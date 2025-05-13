from pydantic import BaseModel, EmailStr, Field
from typing import Optional, List, Dict, Any


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


# WhatsApp Schema Models
class WhatsAppSetupRequest(BaseModel):
    """Request model for setting up WhatsApp integration"""
    auth_token: str
    phone_number_id: str
    entity_id: Optional[str] = "default"
    
    class Config:
        schema_extra = {
            "example": {
                "auth_token": "your-whatsapp-business-api-token",
                "phone_number_id": "your-whatsapp-phone-number-id",
                "entity_id": "user123"
            }
        }


class WhatsAppMessageRequest(BaseModel):
    """Request model for sending WhatsApp text messages"""
    content_prompt: str
    phone_number: str
    api_key: Optional[str] = None
    entity_id: Optional[str] = "default"
    
    class Config:
        schema_extra = {
            "example": {
                "content_prompt": "Notify the customer that their order #12345 has been shipped and will arrive on Friday",
                "phone_number": "+1234567890",
                "api_key": "your-api-key",
                "entity_id": "user123"
            }
        }


class WhatsAppMediaRequest(BaseModel):
    """Request model for sending WhatsApp media messages"""
    media_url: str
    caption: str
    phone_number: str
    api_key: Optional[str] = None
    entity_id: Optional[str] = "default"
    
    class Config:
        schema_extra = {
            "example": {
                "media_url": "https://example.com/image.jpg",
                "caption": "Here's your product image",
                "phone_number": "+1234567890",
                "api_key": "your-api-key",
                "entity_id": "user123"
            }
        }


class WhatsAppTemplateRequest(BaseModel):
    """Request model for sending WhatsApp template messages"""
    template_name: str
    template_params: Dict[str, Any]
    phone_number: str
    api_key: Optional[str] = None
    entity_id: Optional[str] = "default"
    
    class Config:
        schema_extra = {
            "example": {
                "template_name": "order_confirmation",
                "template_params": {
                    "order_number": "12345",
                    "delivery_date": "May 15, 2025"
                },
                "phone_number": "+1234567890",
                "api_key": "your-api-key",
                "entity_id": "user123"
            }
        }


class WhatsAppMessageResponse(BaseModel):
    """Response model for WhatsApp message operations"""
    success: bool
    message: str
    phone_number: Optional[str] = None
    message_content: Optional[str] = None
    error: Optional[str] = None
