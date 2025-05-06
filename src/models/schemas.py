from pydantic import BaseModel, EmailStr, Field
from typing import Optional, List, Dict


class EmailRequest(BaseModel):
    recipient_email: EmailStr
    subject: str
    content_prompt: str
    is_formal: bool = True
    
    class Config:
        schema_extra = {
            "example": {
                "recipient_email": "recipient@example.com",
                "subject": "Meeting Invitation",
                "content_prompt": "Invite the team to a project kickoff meeting on Friday at 2pm",
                "is_formal": True
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
    
    class Config:
        schema_extra = {
            "example": {
                "content_prompt": "Announce the new product release scheduled for next week",
                "channel_id": "C08QPUC28UA"
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
