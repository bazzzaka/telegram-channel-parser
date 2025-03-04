"""
Telegram client implementation using Telethon and Pyrogram libraries.
"""

import asyncio
import os
from enum import Enum, auto
from typing import Any, Dict, List, Optional, Union

from loguru import logger
import telethon
from telethon.tl import types as tl_types
from telethon.sessions import StringSession
import pyrogram
from pyrogram import types as pg_types

from src.config import settings


class TelegramClientMode(Enum):
    """Mode for Telegram client connection."""
    
    USER = auto()  # Connect as user
    BOT = auto()   # Connect as bot


class TelegramClient:
    """Client for interacting with Telegram API."""
    
    def __init__(self, mode: TelegramClientMode = TelegramClientMode.USER):
        """Initialize the Telegram client.
        
        Args:
            mode: Mode to connect to Telegram (user or bot)
        """
        self.mode = mode
        self.client = None
        self._session_string = os.environ.get("TG_SESSION_STRING", "")
        
        if mode == TelegramClientMode.USER:
            # Initialize Telethon client for user account
            if not settings.TG_PHONE:
                raise ValueError("TG_PHONE is required for USER mode")
            
            self.client = telethon.TelegramClient(
                StringSession(self._session_string),
                settings.TG_API_ID,
                settings.TG_API_HASH,
            )
        else:
            # Initialize Pyrogram client for bot
            if not settings.TG_BOT_TOKEN:
                raise ValueError("TG_BOT_TOKEN is required for BOT mode")
            
            self.client = pyrogram.Client(
                "tg_parser_bot",
                api_id=settings.TG_API_ID,
                api_hash=settings.TG_API_HASH,
                bot_token=settings.TG_BOT_TOKEN,
                in_memory=True,
            )
    
    async def connect(self) -> None:
        """Connect to Telegram API."""
        logger.info(f"Connecting to Telegram using {self.mode.name} mode")
        
        if self.mode == TelegramClientMode.USER:
            await self.client.start(phone=settings.TG_PHONE, password=settings.TG_PASSWORD)
            
            # Save session string for reuse
            if not self._session_string:
                self._session_string = self.client.session.save()
                logger.info("Generated new session string")
            
            # Get account info
            me = await self.client.get_me()
            logger.info(f"Connected as user: {me.first_name} (ID: {me.id})")
        else:
            await self.client.start()
            
            # Get bot info
            me = await self.client.get_me()
            logger.info(f"Connected as bot: {me.first_name} (ID: {me.id})")
    
    async def disconnect(self) -> None:
        """Disconnect from Telegram API."""
        if self.client:
            logger.info("Disconnecting from Telegram")
            await self.client.disconnect()
    
    async def join_channel(self, channel_username: str) -> bool:
        """Join a Telegram channel.
        
        Args:
            channel_username: Username of the channel to join
        
        Returns:
            True if joined successfully, False otherwise
        """
        logger.info(f"Attempting to join channel: {channel_username}")
        
        try:
            if self.mode == TelegramClientMode.USER:
                await self.client(telethon.functions.channels.JoinChannelRequest(
                    channel=channel_username
                ))
            else:
                # Bots can't join channels on their own
                logger.warning("Bots cannot join channels without an invite link")
                return False
            
            logger.info(f"Successfully joined channel: {channel_username}")
            return True
        except Exception as e:
            logger.error(f"Failed to join channel {channel_username}: {e}")
            return False
    
    async def get_channel_entity(self, channel_identifier: str) -> Optional[Any]:
        """Get channel entity by username or ID.
        
        Args:
            channel_identifier: Channel username or ID
        
        Returns:
            Channel entity or None if not found
        """
        try:
            if self.mode == TelegramClientMode.USER:
                return await self.client.get_entity(channel_identifier)
            else:
                # For bot, convert string IDs to int
                if channel_identifier.startswith("-100") and channel_identifier[4:].isdigit():
                    channel_identifier = int(channel_identifier[4:])
                return await self.client.get_chat(channel_identifier)
        except Exception as e:
            logger.error(f"Failed to get channel entity {channel_identifier}: {e}")
            return None
    
    async def get_messages(
        self, 
        channel: Any, 
        limit: int = 100, 
        offset_id: int = 0
    ) -> List[Any]:
        """Get messages from a channel.
        
        Args:
            channel: Channel entity
            limit: Maximum number of messages to retrieve
            offset_id: Message ID to start from
        
        Returns:
            List of message objects
        """
        try:
            if self.mode == TelegramClientMode.USER:
                return await self.client.get_messages(
                    channel, 
                    limit=limit, 
                    offset_id=offset_id
                )
            else:
                return await self.client.get_chat_history(
                    channel.id, 
                    limit=limit, 
                    offset_id=offset_id
                )
        except Exception as e:
            logger.error(f"Failed to get messages: {e}")
            return []

    def message_to_dict(self, message: Any) -> Dict[str, Any]:
        """Convert message object to dictionary.
        
        Args:
            message: Telethon or Pyrogram message object
        
        Returns:
            Dictionary with message data
        """
        if self.mode == TelegramClientMode.USER:
            # Telethon message
            return {
                "id": message.id,
                "text": message.text if hasattr(message, "text") else "",
                "date": message.date,
                "channel_id": message.chat_id,
            }
        else:
            # Pyrogram message
            return {
                "id": message.id,
                "text": message.text if hasattr(message, "text") else "",
                "date": message.date,
                "channel_id": message.chat.id,
            }