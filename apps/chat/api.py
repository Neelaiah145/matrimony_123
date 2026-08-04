from django.shortcuts import get_object_or_404
from django.db.models import Q
from ninja import Router, File, Form
from ninja.files import UploadedFile
from ninja.security import django_auth
from ninja_jwt.authentication import JWTAuth
from typing import Optional

from .schemas import (
    SuccessSchema,
    SendMessageSchema,
    CallInitiateSchema,
    CallRespondSchema,
    CallSignalSchema,
)
from .services import (
    ChatRoomService,
    MessageService,
    CallService,
)
from .models import Message, CallSession, ChatRoom

router = Router(tags=["Chat"], auth=[JWTAuth(), django_auth])

@router.get("/conversations",)
def get_chat_rooms(request):

    from apps.matching.models import Interest
    accepted_interests = Interest.objects.filter(
        Q(from_user=request.user) | Q(to_user=request.user),
        status=Interest.Status.ACCEPTED
    )
    
    for interest in accepted_interests:
        try:
            ChatRoomService.get_or_create_room(interest.from_user, interest.to_user)
        except Exception:
            pass

    rooms = ChatRoomService.get_user_rooms(
        request.user
    )

   
    Message.objects.filter(
        room__in=rooms,
        is_delivered=False
    ).exclude(sender=request.user).update(is_delivered=True)

    data = []

    for room in rooms:

        other = room.get_other_participant(
            request.user
        )
        
        profile = getattr(other, 'profile', None)
        photo_url = None
        if profile and profile.profile_photo:
            photo_url = profile.profile_photo.url

        last_msg_obj = room.messages.last()
        last_msg_text = None
        last_msg_time = None
        
        if last_msg_obj:
            if last_msg_obj.is_deleted:
                last_msg_text = "This message was deleted"
            else:
                last_msg_text = last_msg_obj.message or f"[{last_msg_obj.message_type.title()}]"
            last_msg_time = last_msg_obj.created_at
        else:
            last_msg_time = room.updated_at

        unread_count = room.messages.filter(
            is_seen=False
        ).exclude(sender=request.user).count()

       
        status_obj = getattr(other, 'online_status', None)
        is_online = status_obj.is_online if status_obj else False

        data.append(
            {
                "id": room.id,
                "participant_id": other.id,
                "participant_name": other.get_full_name() or other.email or other.phone or f"User #{other.id}",
                "participant_photo": photo_url,
                "last_message": last_msg_text,
                "last_message_time": last_msg_time,
                "unread_count": unread_count,
                "is_online": is_online,
            }
        )

    return data

@router.get("/conversations/{room_id}")
def chat_history(
    request,
    room_id: int,
):

    room = ChatRoomService.get_room(
        room_id,
        request.user,
    )

    if not room:
        return {
            "success": False,
            "message": "Room not found.",
        }

    messages = MessageService.get_chat_history(
        room,
        request.user,
    )

    
    MessageService.mark_messages_as_seen(room, request.user)

    result = []

    for msg in messages:
        attachments_data = []
        for attachment in msg.attachments.all():
            attachments_data.append({
                "id": attachment.id,
                "file_url": attachment.file.url,
                "file_name": attachment.file_name,
                "file_size": attachment.file_size,
                "mime_type": attachment.mime_type,
            })

        message_text = msg.message
        if msg.is_deleted:
            message_text = "This message was deleted"

        result.append(
            {
                "id": msg.id,
                "sender_id": msg.sender.id,
                "sender": msg.sender.get_full_name() or msg.sender.email or msg.sender.phone or f"User #{msg.sender.id}",
                "message": message_text,
                "type": msg.message_type,
                "seen": msg.is_seen,
                "is_delivered": msg.is_delivered,
                "is_deleted": msg.is_deleted,
                "is_me": msg.sender == request.user,
                "created_at": msg.created_at,
                "attachments": attachments_data,
            }
        )

    return result

@router.post("/send",response=SuccessSchema,)
def send_message(
    request,
    payload: SendMessageSchema,
):

    room = ChatRoomService.get_room(
        payload.room_id,
        request.user,
    )

    if not room:
        return {
            "success": False,
            "message": "Room not found.",
        }

    MessageService.send_message(
        room,
        request.user,
        payload.message,
    )

    return {
        "success": True,
        "message": "Message sent successfully.",
    }


@router.post("/send-with-attachment",response=SuccessSchema,)
def send_message_with_attachment_api(
    request,
    room_id: int = Form(...),
    message: Optional[str] = Form(None),
    file: Optional[UploadedFile] = File(None),
):
    room = ChatRoomService.get_room(
        room_id,
        request.user,
    )

    if not room:
        return {
            "success": False,
            "message": "Room not found.",
        }

    MessageService.send_message_with_attachment(
        room,
        request.user,
        message_text=message,
        file=file,
    )

    return {
        "success": True,
        "message": "Message sent successfully.",
    }


@router.put("/conversations/{room_id}/seen",response=SuccessSchema,)
def mark_seen(
    request,
    room_id: int,
):

    room = ChatRoomService.get_room(
        room_id,
        request.user,
    )

    if not room:
        return {
            "success": False,
            "message": "Room not found.",
        }

    MessageService.mark_messages_as_seen(
        room,
        request.user,
    )

    return {
        "success": True,
        "message": "Messages marked as seen.",
    }


@router.delete("/message/{message_id}",response=SuccessSchema,)
def delete_message_for_me(
    request,
    message_id: int,
):
    MessageService.delete_message_for_me(
        message_id,
        request.user,
    )
    return {
        "success": True,
        "message": "Message deleted for you.",
    }


@router.delete("/message/{message_id}/everyone",response=SuccessSchema,)
def delete_message_for_everyone(
    request,
    message_id: int,
):
    MessageService.delete_message_for_everyone(
        message_id,
        request.user,
    )
    return {
        "success": True,
        "message": "Message deleted for everyone.",
    }


@router.post("/heartbeat",response=SuccessSchema,)
def heartbeat(request):
    from django.utils import timezone
    from .models import UserOnlineStatus
    status, created = UserOnlineStatus.objects.get_or_create(user=request.user)
    status.last_active = timezone.now()
    status.save()
    return {
        "success": True,
        "message": "Heartbeat registered.",
    }
    
    
    
@router.post("/send-voice",response=SuccessSchema,)
def send_voice_message(
    request,
    room_id: int = Form(...),
    voice: UploadedFile = File(...),
):

    room = ChatRoomService.get_room(
        room_id,
        request.user,
    )

    if not room:
        return {
            "success": False,
            "message": "Room not found.",
        }

    MessageService.send_voice_message(
        room=room,
        sender=request.user,
        voice_file=voice,
    )

    return {
        "success": True,
        "message": "Voice message sent successfully.",
    }
    


@router.post("/send-image",response=SuccessSchema,)
def send_image_message(
    request,
    room_id: int = Form(...),
    image: UploadedFile = File(...),
    caption: Optional[str] = Form(None),
):

    room = ChatRoomService.get_room(
        room_id,
        request.user,
    )

    if not room:
        return {
            "success": False,
            "message": "Room not found.",
        }

    MessageService.send_image_message(
        room=room,
        sender=request.user,
        image_file=image,
        caption=caption or "",
    )

    return {
        "success": True,
        "message": "Image sent successfully.",
    }
    

@router.post( "/send-video",response=SuccessSchema,)
def send_video_message(
    request,
    room_id: int = Form(...),
    video: UploadedFile = File(...),
    caption: Optional[str] = Form(None),
):

    room = ChatRoomService.get_room(
        room_id,
        request.user,
    )

    if not room:
        return {
            "success": False,
            "message": "Room not found.",
        }

    MessageService.send_video_message(
        room=room,
        sender=request.user,
        video_file=video,
        caption=caption or "",
    )

    return {
        "success": True,
        "message": "Video sent successfully.",
    }
    
    
@router.post("/send-document",response=SuccessSchema,)
def send_document_message(
    request,
    room_id: int = Form(...),
    document: UploadedFile = File(...),
    caption: Optional[str] = Form(None),
):

    room = ChatRoomService.get_room(
        room_id,
        request.user,
    )

    if not room:
        return {
            "success": False,
            "message": "Room not found.",
        }

    MessageService.send_document_message(
        room=room,
        sender=request.user,
        document_file=document,
        caption=caption or "",
    )

    return {
        "success": True,
        "message": "Document sent successfully.",
    }


@router.post("/call/initiate")
def initiate_call(request, payload: CallInitiateSchema):
    room = ChatRoomService.get_room(payload.room_id, request.user)
    if not room:
        return {"success": False, "message": "Room not found."}
    
    receiver = room.get_other_participant(request.user)
    session = CallService.initiate_call(room, request.user, receiver, payload.call_type)
    return {
        "success": True,
        "call_id": session.id,
        "caller_name": request.user.get_full_name(),
        "receiver_name": receiver.get_full_name()
    }


@router.get("/call/active")
def get_active_call(request):
    session = CallService.get_active_call(request.user)
    if not session:
        return {"active": False}
    
    return {
        "active": True,
        "call_id": session.id,
        "caller_id": session.caller.id,
        "caller_name": session.caller.get_full_name(),
        "receiver_id": session.receiver.id,
        "receiver_name": session.receiver.get_full_name(),
        "call_type": session.call_type,
        "status": session.status,
        "is_caller": session.caller == request.user
    }


@router.post("/call/{call_id}/respond")
def respond_call(request, call_id: int, payload: CallRespondSchema):
    session = CallService.get_call(call_id, request.user)
    if not session:
        return {"success": False, "message": "Call session not found."}
    
    if payload.status in [CallSession.CallStatus.ACCEPTED, CallSession.CallStatus.REJECTED, CallSession.CallStatus.ENDED]:
        session.status = payload.status
        session.save(update_fields=["status"])
        return {"success": True, "message": f"Call updated to {payload.status}."}
    
    return {"success": False, "message": "Invalid status."}


@router.post("/call/{call_id}/signal")
def post_signal(request, call_id: int, payload: CallSignalSchema):
    session = CallService.get_call(call_id, request.user)
    if not session:
        return {"success": False, "message": "Call session not found."}
    
    update_fields = []
    if payload.sdp_offer is not None:
        session.sdp_offer = payload.sdp_offer
        update_fields.append("sdp_offer")
    if payload.sdp_answer is not None:
        session.sdp_answer = payload.sdp_answer
        update_fields.append("sdp_answer")
    if payload.caller_candidates is not None:
        session.caller_candidates = payload.caller_candidates
        update_fields.append("caller_candidates")
    if payload.receiver_candidates is not None:
        session.receiver_candidates = payload.receiver_candidates
        update_fields.append("receiver_candidates")
        
    if update_fields:
        session.save(update_fields=update_fields)
        
    return {"success": True, "message": "Signal updated successfully."}


@router.get("/call/{call_id}/signal")
def get_signal(request, call_id: int):
    session = CallService.get_call(call_id, request.user)
    if not session:
        return {"success": False, "message": "Call session not found."}
        
    return {
        "success": True,
        "status": session.status,
        "sdp_offer": session.sdp_offer,
        "sdp_answer": session.sdp_answer,
        "caller_candidates": session.caller_candidates,
        "receiver_candidates": session.receiver_candidates,
    }


@router.post("/call/{call_id}/end")
def end_call(request, call_id: int):
    session = CallService.get_call(call_id, request.user)
    if not session:
        return {"success": True, "message": "Call already ended or not found."}
        
    session.status = CallSession.CallStatus.ENDED
    session.save(update_fields=["status"])
    return {"success": True, "message": "Call ended."}