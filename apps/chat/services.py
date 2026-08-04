from django.db.models import Q
from django.core.exceptions import ValidationError
from django.utils import timezone
from apps.matching.models import Interest
from .models import (
    ChatRoom,
    Message,
    MessageType,
    MessageAttachment,
    CallSession,
)

from .models import Message, MessageType
from .validators import validate_voice_file


class ChatRoomService:
    """ Handles chat room operations. """

    @staticmethod
    def get_or_create_room(user1, user2):

        if user1 == user2:
            raise ValidationError(
                "Users cannot chat with themselves."
            )

        interest_exists = Interest.objects.filter(
            (
                Q(from_user=user1, to_user=user2)
                |
                Q(from_user=user2, to_user=user1)
            ),
            status=Interest.Status.ACCEPTED,
        ).exists()

        if not interest_exists:
            raise ValidationError(
                "Chat is allowed only after interest is accepted."
            )

        if user1.id > user2.id:
            user1, user2 = user2, user1

        room, created = ChatRoom.objects.get_or_create(
            participant1=user1,
            participant2=user2,
            defaults={
                "is_active": True,
            }
        )

        if not room.is_active:
            room.is_active = True
            room.save(update_fields=["is_active"])

        return room

    @staticmethod
    def get_room(room_id, user):
        """
        Returns room only if user belongs to it.
        """

        return (
            ChatRoom.objects.filter(
                id=room_id,
                is_active=True,
            )
            .filter(
                Q(participant1=user)
                |
                Q(participant2=user)
            )
            .first()
        )

    @staticmethod
    def get_user_rooms(user):
        return (
            ChatRoom.objects.filter(
                Q(participant1=user)
                |
                Q(participant2=user),
                is_active=True,
            )
            .prefetch_related(
                "messages"
            )
            .select_related(
                "participant1",
                "participant2",
            )
            .order_by("-updated_at")
        )

    @staticmethod
    def deactivate_room(room):

        room.is_active = False

        room.save(
            update_fields=[
                "is_active",
            ]
        )



class MessageService:
    """
    Handles all chat message operations.
    """

    @staticmethod
    def send_message(room, sender, message_text):

        if room is None:
            raise ValidationError(
                "Chat room not found."
            )

        if sender not in (
            room.participant1,
            room.participant2,
        ):
            raise ValidationError(
                "You are not a participant of this chat."
            )

        if not message_text or not message_text.strip():
            raise ValidationError(
                "Message cannot be empty."
            )

        message = Message.objects.create(
            room=room,
            sender=sender,
            message=message_text.strip(),
            message_type=MessageType.TEXT,
        )

        MessageService._check_and_set_delivered(message)

        room.save(
            update_fields=["updated_at"]
        )

        return message

    @staticmethod
    def get_chat_history(room, user):
        query = Message.objects.filter(room=room)
        if room.participant1 == user:
            query = query.exclude(deleted_by_p1=True)
        elif room.participant2 == user:
            query = query.exclude(deleted_by_p2=True)

        return (
            query.select_related(
                "sender",
            )
            .prefetch_related(
                "attachments",
            )
            .order_by(
                "created_at",
            )
        )

    @staticmethod
    def mark_messages_as_seen(room, user):

        (
            Message.objects.filter(
                room=room,
                is_seen=False,
            )
            .exclude(
                sender=user,
            )
            .update(
                is_seen=True,
                is_delivered=True,
                seen_at=timezone.now(),
            )
        )

    @staticmethod
    def _check_and_set_delivered(message):
        recipient = message.room.get_other_participant(message.sender)
        recipient_status = getattr(recipient, 'online_status', None)
        if recipient_status and recipient_status.is_online:
            message.is_delivered = True
            message.save(update_fields=['is_delivered'])

    @staticmethod
    def delete_message_for_me(message_id, user):
        try:
            message = Message.objects.filter(
                Q(room__participant1=user) | Q(room__participant2=user)
            ).get(id=message_id)
        except Message.DoesNotExist:
            raise ValidationError("Message not found.")

        if message.room.participant1 == user:
            message.deleted_by_p1 = True
            message.save(update_fields=["deleted_by_p1"])
        elif message.room.participant2 == user:
            message.deleted_by_p2 = True
            message.save(update_fields=["deleted_by_p2"])

        return message

    @staticmethod
    def delete_message_for_everyone(message_id, user):
        try:
            message = Message.objects.get(
                id=message_id,
                sender=user,
            )
        except Message.DoesNotExist:
            raise ValidationError("Message not found or you are not the sender.")

        message.is_deleted = True
        message.deleted_at = timezone.now()
        message.save(update_fields=["is_deleted", "deleted_at"])

        return message
    
    @staticmethod
    def send_voice_message(room, sender, voice_file):
        if not room:
            raise ValidationError(
                "Chat room not found."
            )

        if sender not in [room.participant1, room.participant2]:
            raise ValidationError(
                "You are not a participant of this chat."
            )

        validate_voice_file(voice_file)

        message = Message.objects.create(
            room=room,
            sender=sender,
            message="",
            message_type=MessageType.VOICE,
        )

        MessageService._check_and_set_delivered(message)

        attachment = MessageAttachment.objects.create(
            message=message,
            file=voice_file,
            file_name=voice_file.name,
            file_size=voice_file.size,
            mime_type=getattr(
                voice_file,
                "content_type",
                "audio/webm",
            ),
        )

        room.save(update_fields=["updated_at"])

        return {
            "message": message,
            "attachment": attachment,
        }


    @staticmethod
    def send_image_message(room, sender, image_file, caption=""):
        if not room:
            raise ValidationError("Chat room not found.")

        if sender not in [room.participant1, room.participant2]:
            raise ValidationError(
                "You are not a participant."
            )

        message = Message.objects.create(
            room=room,
            sender=sender,
            message=caption,
            message_type=MessageType.IMAGE,
        )

        MessageService._check_and_set_delivered(message)

        attachment = MessageAttachment.objects.create(
            message=message,
            file=image_file,
            file_name=image_file.name,
            file_size=image_file.size,
            mime_type=getattr(
                image_file,
                "content_type",
                "image/jpeg",
            ),
        )

        room.save(update_fields=["updated_at"])

        return {
            "message": message,
            "attachment": attachment,
        }


    @staticmethod
    def send_video_message(room, sender, video_file, caption=""):
        if not room:
            raise ValidationError("Chat room not found.")

        if sender not in [room.participant1, room.participant2]:
            raise ValidationError(
                "You are not a participant."
            )

        message = Message.objects.create(
            room=room,
            sender=sender,
            message=caption,
            message_type=MessageType.VIDEO,
        )

        MessageService._check_and_set_delivered(message)

        attachment = MessageAttachment.objects.create(
            message=message,
            file=video_file,
            file_name=video_file.name,
            file_size=video_file.size,
            mime_type=getattr(
                video_file,
                "content_type",
                "video/mp4",
            ),
        )

        room.save(update_fields=["updated_at"])

        return {
            "message": message,
            "attachment": attachment,
        }


    @staticmethod
    def send_document_message(room, sender, document_file, caption=""):

        if not room:
            raise ValidationError("Chat room not found.")

        if sender not in [room.participant1, room.participant2]:
            raise ValidationError(
                "You are not a participant."
            )

        message = Message.objects.create(
            room=room,
            sender=sender,
            message=caption,
            message_type=MessageType.DOCUMENT,
        )

        MessageService._check_and_set_delivered(message)

        attachment = MessageAttachment.objects.create(
            message=message,
            file=document_file,
            file_name=document_file.name,
            file_size=document_file.size,
            mime_type=getattr(
                document_file,
                "content_type",
                "application/octet-stream",
            ),
        )

        room.save(update_fields=["updated_at"])

        return {
            "message": message,
            "attachment": attachment,
        }


class CallService:
    @staticmethod
    def initiate_call(room, caller, receiver, call_type):
        CallSession.objects.filter(
            room=room,
            status__in=[CallSession.CallStatus.RINGING, CallSession.CallStatus.ACCEPTED]
        ).update(status=CallSession.CallStatus.ENDED)

        return CallSession.objects.create(
            room=room,
            caller=caller,
            receiver=receiver,
            call_type=call_type,
            status=CallSession.CallStatus.RINGING
        )

    @staticmethod
    def get_active_call(user):
        return CallSession.objects.filter(
            Q(caller=user) | Q(receiver=user),
            status__in=[CallSession.CallStatus.RINGING, CallSession.CallStatus.ACCEPTED]
        ).first()

    @staticmethod
    def get_call(call_id, user):
        try:
            return CallSession.objects.filter(
                Q(caller=user) | Q(receiver=user)
            ).get(id=call_id)
        except CallSession.DoesNotExist:
            return None
        
    
    
    
    