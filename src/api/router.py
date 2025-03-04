"""
API routes for accessing parsed data.
"""

from datetime import datetime
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from src.database.database import get_db
from src.database.models import Channel, DangerInfo, Location, Message
from src.api.schemas import (
    ChannelSchema,
    DangerInfoSchema,
    LocationSchema,
    MessageSchema,
    StatsSchema,
)


router = APIRouter()


@router.get("/channels", response_model=List[ChannelSchema])
async def get_channels(
    db: AsyncSession = Depends(get_db),
):
    """Get all monitored channels."""
    query = select(Channel).order_by(Channel.title)
    result = await db.execute(query)
    channels = result.scalars().all()
    return channels


@router.get("/channels/{channel_id}", response_model=ChannelSchema)
async def get_channel(
    channel_id: int,
    db: AsyncSession = Depends(get_db),
):
    """Get a specific channel by ID."""
    channel = await db.get(Channel, channel_id)
    if not channel:
        raise HTTPException(status_code=404, detail="Channel not found")
    return channel


@router.get("/messages", response_model=List[MessageSchema])
async def get_messages(
    channel_id: Optional[int] = None,
    has_location: Optional[bool] = None,
    has_danger_info: Optional[bool] = None,
    date_from: Optional[datetime] = None,
    date_to: Optional[datetime] = None,
    limit: int = Query(50, le=100),
    offset: int = 0,
    db: AsyncSession = Depends(get_db),
):
    """Get messages with optional filtering."""
    query = select(Message).options(
        joinedload(Message.locations),
        joinedload(Message.danger_infos),
    )
    
    # Apply filters
    if channel_id is not None:
        query = query.where(Message.channel_id == channel_id)
    
    if has_location is not None:
        query = query.where(Message.has_location == has_location)
    
    if has_danger_info is not None:
        query = query.where(Message.has_danger_info == has_danger_info)
    
    if date_from is not None:
        query = query.where(Message.date >= date_from)
    
    if date_to is not None:
        query = query.where(Message.date <= date_to)
    
    # Apply pagination
    query = query.order_by(Message.date.desc()).offset(offset).limit(limit)
    
    result = await db.execute(query)
    messages = result.scalars().all()
    return messages


@router.get("/messages/{message_id}", response_model=MessageSchema)
async def get_message(
    message_id: int,
    db: AsyncSession = Depends(get_db),
):
    """Get a specific message by ID."""
    query = select(Message).where(Message.id == message_id).options(
        joinedload(Message.locations),
        joinedload(Message.danger_infos),
    )
    result = await db.execute(query)
    message = result.scalar_one_or_none()
    
    if not message:
        raise HTTPException(status_code=404, detail="Message not found")
    
    return message


@router.get("/locations", response_model=List[LocationSchema])
async def get_locations(
    message_id: Optional[int] = None,
    limit: int = Query(50, le=100),
    offset: int = 0,
    db: AsyncSession = Depends(get_db),
):
    """Get locations with optional filtering."""
    query = select(Location)
    
    # Apply filters
    if message_id is not None:
        query = query.where(Location.message_id == message_id)
    
    # Apply pagination
    query = query.order_by(Location.created_at.desc()).offset(offset).limit(limit)
    
    result = await db.execute(query)
    locations = result.scalars().all()
    return locations


@router.get("/danger-info", response_model=List[DangerInfoSchema])
async def get_danger_info(
    message_id: Optional[int] = None,
    min_severity: Optional[int] = None,
    limit: int = Query(50, le=100),
    offset: int = 0,
    db: AsyncSession = Depends(get_db),
):
    """Get danger information with optional filtering."""
    query = select(DangerInfo)
    
    # Apply filters
    if message_id is not None:
        query = query.where(DangerInfo.message_id == message_id)
    
    if min_severity is not None:
        query = query.where(DangerInfo.severity >= min_severity)
    
    # Apply pagination
    query = query.order_by(DangerInfo.severity.desc()).offset(offset).limit(limit)
    
    result = await db.execute(query)
    danger_info = result.scalars().all()
    return danger_info


@router.get("/stats", response_model=StatsSchema)
async def get_stats(
    channel_id: Optional[int] = None,
    date_from: Optional[datetime] = None,
    date_to: Optional[datetime] = None,
    db: AsyncSession = Depends(get_db),
):
    """Get statistics about parsed data."""
    from sqlalchemy import func
    
    # Base query for messages
    message_query = select(Message)
    
    # Apply filters
    if channel_id is not None:
        message_query = message_query.where(Message.channel_id == channel_id)
    
    if date_from is not None:
        message_query = message_query.where(Message.date >= date_from)
    
    if date_to is not None:
        message_query = message_query.where(Message.date <= date_to)
    
    # Count total messages
    total_messages = await db.execute(
        select(func.count()).select_from(message_query.subquery())
    )
    total_messages_count = total_messages.scalar_one()
    
    # Count messages with locations
    messages_with_locations = await db.execute(
        select(func.count()).select_from(
            message_query.where(Message.has_location).subquery()
        )
    )
    messages_with_locations_count = messages_with_locations.scalar_one()
    
    # Count messages with danger info
    messages_with_danger = await db.execute(
        select(func.count()).select_from(
            message_query.where(Message.has_danger_info).subquery()
        )
    )
    messages_with_danger_count = messages_with_danger.scalar_one()
    
    # Count total locations
    total_locations = await db.execute(
        select(func.count(Location.id)).where(
            Location.message_id.in_(
                select(Message.id).select_from(message_query.subquery())
            )
        )
    )
    total_locations_count = total_locations.scalar_one()
    
    # Count total danger infos
    total_danger_infos = await db.execute(
        select(func.count(DangerInfo.id)).where(
            DangerInfo.message_id.in_(
                select(Message.id).select_from(message_query.subquery())
            )
        )
    )
    total_danger_infos_count = total_danger_infos.scalar_one()
    
    return {
        "total_messages": total_messages_count,
        "messages_with_locations": messages_with_locations_count,
        "messages_with_danger_info": messages_with_danger_count,
        "total_locations": total_locations_count,
        "total_danger_infos": total_danger_infos_count,
    }