from pydantic import BaseModel, Field, HttpUrl
from typing import Optional, List, Dict, Any


class LinkedInSetupRequest(BaseModel):
    """Request model for setting up LinkedIn integration"""
    entity_id: Optional[str] = "default"
    
    class Config:
        schema_extra = {
            "example": {
                "entity_id": "user123"
            }
        }


class LinkedInProfileInfo(BaseModel):
    """Model for LinkedIn profile information"""
    id: str
    name: str
    headline: Optional[str] = None
    url: Optional[str] = None


class LinkedInConnectionRequest(BaseModel):
    """Request model for sending LinkedIn connection requests"""
    profile_url: str
    message: Optional[str] = None
    access_token: str
    entity_id: Optional[str] = "default"
    
    class Config:
        schema_extra = {
            "example": {
                "profile_url": "https://www.linkedin.com/in/johndoe/",
                "message": "I'd like to connect with you regarding potential collaboration opportunities.",
                "access_token": "your-linkedin-access-token",
                "entity_id": "user123"
            }
        }


class LinkedInMessageRequest(BaseModel):
    """Request model for sending LinkedIn messages"""
    profile_id: str
    content_prompt: str
    access_token: str
    entity_id: Optional[str] = "default"
    
    class Config:
        schema_extra = {
            "example": {
                "profile_id": "linkedinProfileId123",
                "content_prompt": "Follow up on our previous discussion about the project timeline",
                "access_token": "your-linkedin-access-token",
                "entity_id": "user123"
            }
        }


class LinkedInPostRequest(BaseModel):
    """Request model for creating LinkedIn posts"""
    content_prompt: str
    access_token: str
    image_url: Optional[HttpUrl] = None
    article_url: Optional[HttpUrl] = None
    entity_id: Optional[str] = "default"
    
    class Config:
        schema_extra = {
            "example": {
                "content_prompt": "Announce our new product launch with key features and benefits",
                "access_token": "your-linkedin-access-token",
                "image_url": "https://example.com/product-image.jpg",
                "article_url": "https://example.com/product-launch-blog",
                "entity_id": "user123"
            }
        }


class LinkedInProfileSearchRequest(BaseModel):
    """Request model for searching LinkedIn profiles"""
    keywords: str
    access_token: str
    limit: Optional[int] = 10
    entity_id: Optional[str] = "default"
    
    class Config:
        schema_extra = {
            "example": {
                "keywords": "software engineer AI machine learning",
                "access_token": "your-linkedin-access-token",
                "limit": 10,
                "entity_id": "user123"
            }
        }


class LinkedInResponse(BaseModel):
    """Generic response model for LinkedIn operations"""
    success: bool
    message: str
    data: Optional[Any] = None
    error: Optional[str] = None


class LinkedInProfilesResponse(BaseModel):
    """Response model for LinkedIn profile search results"""
    success: bool
    message: str
    profiles: List[LinkedInProfileInfo] = []
    error: Optional[str] = None
