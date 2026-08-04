from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.validators import FileExtensionValidator
from django.db import models
from django.utils import timezone


class ChatRoom(models.Model):
    """
    One chat room between two users.
    Created only after interest is accepted.
    """

    participant1 = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="chat_rooms_as_user1"
    )

    participant2 = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="chat_rooms_as_user2"
    )

    is_active = models.BooleanField(default=True)

    created_at = models.DateTimeField(auto_now_add=True)

    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "chat_rooms"
        ordering = ["-created_at"]

        indexes = [
            models.Index(fields=["participant1"]),
            models.Index(fields=["participant2"]),
        ]

    def clean(self):
        if self.participant1 == self.participant2:
            raise ValidationError(
                "A user cannot create a chat with themselves."
            )

    def get_other_participant(self, user):
        if self.participant1 == user:
            return self.participant2
        return self.participant1

    def __str__(self):
        return f"{self.participant1} ↔ {self.participant2}"


class MessageType(models.TextChoices):
    TEXT = "TEXT", "Text"
    IMAGE = "IMAGE", "Image"
    VIDEO = "VIDEO", "Video"
    VOICE = "VOICE", "Voice"
    DOCUMENT = "DOCUMENT", "Document"
    SYSTEM = "SYSTEM", "System"


class Message(models.Model):
    """
    Stores chat messages.
    """

    room = models.ForeignKey(
        ChatRoom,
        on_delete=models.CASCADE,
        related_name="messages"
    )

    sender = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="sent_messages"
    )

    message_type = models.CharField(
        max_length=20,
        choices=MessageType.choices,
        default=MessageType.TEXT
    )

    message = models.TextField(
        blank=True,
        null=True
    )

    is_delivered = models.BooleanField(default=False)

    is_seen = models.BooleanField(default=False)

    seen_at = models.DateTimeField(
        blank=True,
        null=True
    )

    is_deleted = models.BooleanField(default=False)

    deleted_at = models.DateTimeField(
        blank=True,
        null=True
    )

    deleted_by_p1 = models.BooleanField(default=False)
    deleted_by_p2 = models.BooleanField(default=False)

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    updated_at = models.DateTimeField(
        auto_now=True
    )

    class Meta:
        db_table = "chat_messages"
        ordering = ["created_at"]

        indexes = [
            models.Index(fields=["room"]),
            models.Index(fields=["sender"]),
            models.Index(fields=["created_at"]),
            models.Index(fields=["is_seen"]),
        ]

    @property
    def has_attachment(self):
        return self.attachments.exists()

    def __str__(self):
        return f"{self.sender} - {self.message_type}"


class MessageAttachment(models.Model):
    """
    Stores files attached to a message.
    """

    message = models.ForeignKey(
        Message,
        on_delete=models.CASCADE,
        related_name="attachments"
    )

    file = models.FileField(
        upload_to="chat/",
        validators=[
            FileExtensionValidator(
                allowed_extensions=["jpg","jpeg","png","gif","webp","mp4","mov","avi","mp3","wav","ogg","pdf","doc","docx",
                                    "xls","xlsx","ppt","pptx","txt","zip"
                ]
            )
        ]
    )

    file_name = models.CharField(
        max_length=255
    )

    file_size = models.PositiveBigIntegerField()

    mime_type = models.CharField(
        max_length=100
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    class Meta:
        db_table = "chat_message_attachments"
        ordering = ["created_at"]

    def __str__(self):
        return self.file_name


class CallSession(models.Model):
    class CallType(models.TextChoices):
        VOICE = "VOICE", "Voice"
        VIDEO = "VIDEO", "Video"

    class CallStatus(models.TextChoices):
        RINGING = "RINGING", "Ringing"
        ACCEPTED = "ACCEPTED", "Accepted"
        REJECTED = "REJECTED", "Rejected"
        ENDED = "ENDED", "Ended"

    room = models.ForeignKey(ChatRoom, on_delete=models.CASCADE, related_name="calls")
    caller = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="outgoing_calls")
    receiver = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="incoming_calls")
    call_type = models.CharField(max_length=10, choices=CallType.choices)
    status = models.CharField(max_length=20, choices=CallStatus.choices, default=CallStatus.RINGING)
    
    sdp_offer = models.TextField(null=True, blank=True)
    sdp_answer = models.TextField(null=True, blank=True)
    caller_candidates = models.TextField(default="[]")
    receiver_candidates = models.TextField(default="[]")
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "chat_call_sessions"
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.call_type} call: {self.caller} -> {self.receiver} ({self.status})"


class UserOnlineStatus(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="online_status"
    )
    last_active = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "chat_user_online_statuses"

    @property
    def is_online(self):
        if not self.last_active:
            return False
        return (timezone.now() - self.last_active).total_seconds() < 15

    def __str__(self):
        return f"{self.user} - {'Online' if self.is_online else 'Offline'}"