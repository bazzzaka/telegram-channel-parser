"""
Module for listening to Telegram messages.
"""

import asyncio
import datetime
from typing import Any, Dict, List, Optional, Tuple, Union

from loguru import logger
from sqlalchemy.ext.asyncio import AsyncSession

from src.config import settings
from src.database.database import async_session
from src.database.models import Channel, DangerInfo, Location, Message
from src.location.extractor import LocationExtractor
from src.location.map_service import get_map_url
from src.telegram.client import TelegramClient, TelegramClientMode


class TelegramMessageListener:
    """Listener for Telegram messages."""
    
    def __init__(self, client: TelegramClient):
        """Initialize the message listener.
        
        Args:
            client: Telegram client instance
        """
        self.client = client
        self.location_extractor = LocationExtractor()
        self.channels: Dict[str, Any] = {}
        self.is_running = False
    
    async def start_listening(self) -> None:
        """Start listening for messages from configured channels."""
        if self.is_running:
            logger.warning("Message listener is already running")
            return
        
        self.is_running = True
        logger.info("Starting message listener")
        
        # Load channels from configuration
        await self._load_channels()
        
        while self.is_running:
            try:
                # Process messages from all channels
                for channel_id, channel_entity in self.channels.items():
                    await self._process_channel_messages(channel_entity)
                
                # Wait before next polling cycle
                await asyncio.sleep(60)  # Poll every minute
            except Exception as e:
                logger.error(f"Error in message listener: {e}")
                await asyncio.sleep(10)  # Wait before retry
    
    async def stop_listening(self) -> None:
        """Stop listening for messages."""
        logger.info("Stopping message listener")
        self.is_running = False
    
    async def _load_channels(self) -> None:
        """Load channel entities from configuration."""
        logger.info("Loading channels from configuration")
        
        for channel_identifier in settings.tg_channels_list:
            try:
                # Get channel entity
                channel_entity = await self.client.get_channel_entity(channel_identifier)
                if channel_entity:
                    # Store channel entity
                    if self.client.mode == TelegramClientMode.USER:
                        # Telethon entity
                        self.channels[str(channel_entity.id)] = channel_entity
                        logger.info(f"Loaded channel: {channel_entity.title} ({channel_entity.id})")
                    else:
                        # Pyrogram entity
                        self.channels[str(channel_entity.id)] = channel_entity
                        logger.info(f"Loaded channel: {channel_entity.title} ({channel_entity.id})")
                    
                    # Store channel in database
                    await self._store_channel(channel_entity)
            except Exception as e:
                logger.error(f"Failed to load channel {channel_identifier}: {e}")
    
    async def _store_channel(self, channel_entity: Any) -> None:
        """Store channel in database.
        
        Args:
            channel_entity: Telegram channel entity
        """
        async with async_session() as session:
            try:
                # Extract channel info
                if self.client.mode == TelegramClientMode.USER:
                    # Telethon entity
                    channel_id = channel_entity.id
                    title = channel_entity.title
                    username = getattr(channel_entity, "username", None)
                else:
                    # Pyrogram entity
                    channel_id = channel_entity.id
                    title = channel_entity.title
                    username = getattr(channel_entity, "username", None)
                
                # Check if channel exists
                channel = await session.get(Channel, channel_id)
                if not channel:
                    # Create new channel
                    channel = Channel(
                        tg_id=channel_id,
                        title=title,
                        username=username,
                    )
                    session.add(channel)
                    await session.commit()
                    logger.info(f"Stored channel in database: {title} ({channel_id})")
                else:
                    # Update existing channel
                    channel.title = title
                    channel.username = username
                    channel.updated_at = datetime.datetime.utcnow()
                    await session.commit()
                    logger.info(f"Updated channel in database: {title} ({channel_id})")
            except Exception as e:
                await session.rollback()
                logger.error(f"Failed to store channel in database: {e}")
    
    async def _process_channel_messages(self, channel_entity: Any) -> None:
        """Process messages from a channel.
        
        Args:
            channel_entity: Telegram channel entity
        """
        logger.info(f"Processing messages from channel: {channel_entity.title}")
        
        # Get latest messages
        messages = await self.client.get_messages(channel_entity, limit=50)
        if not messages:
            logger.info(f"No new messages in channel: {channel_entity.title}")
            return
        
        # Process each message
        processed_count = 0
        for message in messages:
            # Convert message to dictionary
            message_dict = self.client.message_to_dict(message)
            
            # Process message
            async with async_session() as session:
                try:
                    # Check if message exists
                    existing_message = await self._get_message_by_tg_id(
                        session, 
                        message_dict["id"], 
                        message_dict["channel_id"]
                    )
                    
                    if not existing_message:
                        # Store and process new message
                        await self._store_and_process_message(session, message_dict)
                        processed_count += 1
                except Exception as e:
                    await session.rollback()
                    logger.error(f"Failed to process message {message_dict['id']}: {e}")
        
        logger.info(f"Processed {processed_count} new messages from channel: {channel_entity.title}")
    
    async def _get_message_by_tg_id(
        self, 
        session: AsyncSession, 
        tg_id: int, 
        channel_tg_id: int
    ) -> Optional[Message]:
        """Get message by Telegram ID.
        
        Args:
            session: Database session
            tg_id: Telegram message ID
            channel_tg_id: Telegram channel ID
        
        Returns:
            Message object or None if not found
        """
        from sqlalchemy import select
        
        # Get channel by Telegram ID
        channel_stmt = select(Channel).where(Channel.tg_id == channel_tg_id)
        channel_result = await session.execute(channel_stmt)
        channel = channel_result.scalar_one_or_none()
        
        if not channel:
            return None
        
        # Get message by Telegram ID and channel ID
        message_stmt = select(Message).where(
            Message.tg_id == tg_id,
            Message.channel_id == channel.id
        )
        message_result = await session.execute(message_stmt)
        return message_result.scalar_one_or_none()
    
    async def _store_and_process_message(
        self, 
        session: AsyncSession, 
        message_dict: Dict[str, Any]
    ) -> None:
        """Store and process a new message.
        
        Args:
            session: Database session
            message_dict: Message data dictionary
        """
        from sqlalchemy import select
        
        # Get channel by Telegram ID
        channel_stmt = select(Channel).where(Channel.tg_id == message_dict["channel_id"])
        channel_result = await session.execute(channel_stmt)
        channel = channel_result.scalar_one_or_none()
        
        if not channel:
            logger.warning(f"Channel not found: {message_dict['channel_id']}")
            return
        
        # Extract text from message
        text = message_dict.get("text", "")
        if not text:
            logger.debug(f"Skipping message without text: {message_dict['id']}")
            return
        
        # Extract locations and danger info
        locations = self.location_extractor.extract_locations(text)
        danger_info = self.location_extractor.extract_danger_info(text)
        
        # Create message
        message = Message(
            tg_id=message_dict["id"],
            channel_id=channel.id,
            text=text,
            date=message_dict["date"],
            has_location=bool(locations),
            has_danger_info=bool(danger_info),
            processed=True,
        )
        session.add(message)
        await session.flush()  # Flush to get message ID
        
        # Store locations
        for loc_text, lat, lng in locations:
            # Generate map URL
            map_url = get_map_url(lat, lng, settings.MAP_SERVICE)
            
            # Create location
            location = Location(
                message_id=message.id,
                original_text=loc_text,
                latitude=lat,
                longitude=lng,
                map_url=map_url,
            )
            session.add(location)
        
        # Store danger info
        for danger_text, severity in danger_info:
            danger = DangerInfo(
                message_id=message.id,
                text=danger_text,
                severity=severity,
            )
            session.add(danger)
        
        # Commit changes
        await session.commit()
        logger.info(f"Stored and processed message {message.tg_id}: {len(locations)} locations, {len(danger_info)} danger info")