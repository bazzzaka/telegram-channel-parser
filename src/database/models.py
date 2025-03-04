"""
Database models for the application.
"""

import datetime
from typing import Optional

from sqlalchemy import Boolean, Column, DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import relationship

from src.database.database import Base


class Channel(Base):
    """Model for Telegram channels."""
    
    __tablename__ = "channels"
    
    id = Column(Integer, primary_key=True)
    tg_id = Column(Integer, unique=True, nullable=False)
    title = Column(String(255), nullable=False)
    username = Column(String(255), nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(
        DateTime, 
        default=datetime.datetime.utcnow, 
        onupdate=datetime.datetime.utcnow
    )
    
    # Relationships
    messages = relationship("Message", back_populates="channel", cascade="all, delete-orphan")


class Message(Base):
    """Model for Telegram messages."""
    
    __tablename__ = "messages"
    
    id = Column(Integer, primary_key=True)
    tg_id = Column(Integer, nullable=False)
    channel_id = Column(Integer, ForeignKey("channels.id"), nullable=False)
    text = Column(Text, nullable=True)
    date = Column(DateTime, nullable=False)
    has_location = Column(Boolean, default=False)
    has_danger_info = Column(Boolean, default=False)
    processed = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    
    # Relationships
    channel = relationship("Channel", back_populates="messages")
    locations = relationship("Location", back_populates="message", cascade="all, delete-orphan")
    danger_infos = relationship("DangerInfo", back_populates="message", cascade="all, delete-orphan")


class Location(Base):
    """Model for extracted locations."""
    
    __tablename__ = "locations"
    
    id = Column(Integer, primary_key=True)
    message_id = Column(Integer, ForeignKey("messages.id"), nullable=False)
    original_text = Column(Text, nullable=False)
    latitude = Column(Float, nullable=True)
    longitude = Column(Float, nullable=True)
    address = Column(Text, nullable=True)
    map_url = Column(String(2048), nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    
    # Relationships
    message = relationship("Message", back_populates="locations")


class DangerInfo(Base):
    """Model for extracted danger information."""
    
    __tablename__ = "danger_infos"
    
    id = Column(Integer, primary_key=True)
    message_id = Column(Integer, ForeignKey("messages.id"), nullable=False)
    text = Column(Text, nullable=False)
    severity = Column(Integer, nullable=True)  # 1-10 scale
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    
    # Relationships
    message = relationship("Message", back_populates="danger_infos")