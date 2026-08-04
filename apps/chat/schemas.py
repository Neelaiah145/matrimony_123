from datetime import datetime
from typing import List, Optional
from ninja import Schema
from typing import Optional


# Send Message Request

class SendMessageSchema(Schema):
    room_id: int
    message: Optional[str] = None



# Upload Attachment Request

class UploadAttachmentSchema(Schema):
    room_id: int



# Chat Room Response

class ChatRoomSchema(Schema):
    id: int
    participant_id: int
    participant_name: str
    participant_photo: Optional[str] = None
    last_message: Optional[str] = None
    last_message_time: Optional[datetime] = None
    unread_count: int



# Message Response

class MessageSchema(Schema):
    id: int
    sender_id: int
    sender_name: str
    message_type: str
    message: Optional[str] = None
    is_seen: bool
    created_at: datetime



# Attachment Response

class AttachmentSchema(Schema):
    id: int
    file: str
    file_name: str
    file_size: int
    mime_type: str



# Message Details

class MessageDetailSchema(Schema):
    id: int
    sender_id: int
    sender_name: str
    message_type: str
    message: Optional[str] = None
    attachments: List[AttachmentSchema] = []
    is_seen: bool
    created_at: datetime



# Chat History Response

class ChatHistorySchema(Schema):
    room_id: int
    messages: List[MessageDetailSchema]



# Success Response

class SuccessSchema(Schema):
    success: bool
    message: str
    
    


# Voice message upload request.
class VoiceMessageUploadSchema(Schema):
    room_id: int


# Voice message upload response.
class VoiceMessageResponseSchema(Schema):
    success: bool
    message: str
    message_id: Optional[int] = None
    attachment_id: Optional[int] = None
    audio_url: Optional[str] = None
    duration: Optional[float] = None


class CallInitiateSchema(Schema):
    room_id: int
    call_type: str


class CallRespondSchema(Schema):
    status: str


class CallSignalSchema(Schema):
    sdp_offer: Optional[str] = None
    sdp_answer: Optional[str] = None
    caller_candidates: Optional[str] = None
    receiver_candidates: Optional[str] = None