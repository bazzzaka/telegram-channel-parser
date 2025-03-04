"""
Pydantic schemas for API requests and responses.
"""

from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, Field


class ChannelSchema(BaseModel):
    """Schema for channel information."""
    
    id: int
    tg_id: int
    title: str
    username: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class LocationSchema(BaseModel):
    """Schema for location information."""
    
    id: int
    message_id: int
    original_text: str
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    address: Optional[str] = None
    map_url: Optional[str] = None
    created_at: datetime
    
    class Config:
        from_attributes = True


class DangerInfoSchema(BaseModel):
    """Schema for danger information."""
    
    id: int
    message_id: int
    text: str
    severity: Optional[int] = None
    created_at: datetime
    
    class Config:
        from_attributes = True


class MessageSchema(BaseModel):
    """Schema for message information."""
    
    id: int
    tg_id: int
    channel_id: int
    text: Optional[str] = None
    date: datetime
    has_location: bool
    has_danger_info: bool
    processed: bool
    created_at: datetime
    locations: List[LocationSchema] = []
    danger_infos: List[DangerInfoSchema] = []
    
    class Config:
        from_attributes = True


class StatsSchema(BaseModel):
    """Schema for statistics."""
    
    total_messages: int
    messages_with_locations: int
    messages_with_danger_info: int
    total_locations: int
    total_danger_infos: int