from pydantic import BaseModel, EmailStr, Field
from typing import Optional, List, Dict


class GmailSetupRequest(BaseModel):
    """Request model for setting up Gmail integration"""
    entity_id: Optional[str] = "default"
    
    class Config:
        schema_extra = {
            "example": {
                "entity_id": "user123"
            }
        }


class EmailSendRequest(BaseModel):
    """Request model for sending emails with auto-generated subject"""
    recipient_email: EmailStr
    content_prompt: str
    recipient_name: Optional[str] = None
    sender_name: Optional[str] = None
    sender_designation: Optional[str] = None
    is_formal: bool = True
    entity_id: Optional[str] = "default"
    
    class Config:
        schema_extra = {
            "example": {
                "recipient_email": "recipient@example.com",
                "recipient_name": "John Smith",
                "sender_name": "Jane Doe",
                "sender_designation": "Product Manager",
                "content_prompt": "Invite the team to a project kickoff meeting on Friday at 2pm",
                "is_formal": True,
                "entity_id": "user123"
            }
        }


class EmailRequest(BaseModel):
    recipient_email: EmailStr
    content_prompt: str
    recipient_name: Optional[str] = None
    sender_name: Optional[str] = None
    sender_designation: Optional[str] = None
    subject: Optional[str] = None  # Now optional, will be auto-generated if not provided
    is_formal: bool = True
    entity_id: Optional[str] = "default"
    
    class Config:
        schema_extra = {
            "example": {
                "recipient_email": "recipient@example.com",
                "recipient_name": "John Smith",
                "sender_name": "Jane Doe",
                "sender_designation": "Product Manager",
                "content_prompt": "Invite the team to a project kickoff meeting on Friday at 2pm",
                "is_formal": True,
                "entity_id": "user123"
            }
        }


class EmailResponse(BaseModel):
    success: bool
    message: str
    email_content: Optional[str] = None
    error: Optional[str] = None


class SlackChannelInfo(BaseModel):
    id: str
    name: str


class SlackMessageRequest(BaseModel):
    content_prompt: str
    channel_id: str
    channel_name: str
    bot_token: Optional[str] = None
    
    class Config:
        schema_extra = {
            "example": {
                "content_prompt": "Announce the new product release scheduled for next week",
                "channel_id": "C08QPUC28UA",
                "channel_name": "general",
                "bot_token": "xoxb-your-bot-token"
            }
        }


class SlackMessageResponse(BaseModel):
    success: bool
    message: str
    channel_name: Optional[str] = None
    message_content: Optional[str] = None
    error: Optional[str] = None


class ChannelListResponse(BaseModel):
    channels: List[SlackChannelInfo]
