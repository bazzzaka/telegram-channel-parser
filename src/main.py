"""
Main entry point for the Telegram Channel Parser application.
"""

import asyncio
import os
from typing import Optional

from fastapi import FastAPI
from loguru import logger

from src.config import settings
from src.database.database import init_db
from src.telegram.client import TelegramClient, TelegramClientMode
from src.telegram.listener import TelegramMessageListener
from src.api.router import router as api_router


app = FastAPI(
    title="Telegram Channel Parser",
    description="Application for parsing Telegram channels to extract location data",
    version="0.1.0",
)

app.include_router(api_router, prefix="/api")

# Initialize Telegram client
telegram_client: Optional[TelegramClient] = None


@app.on_event("startup")
async def startup_event() -> None:
    """Initialize services on application startup."""
    logger.info("Starting Telegram Channel Parser application")
    
    # Initialize database
    await init_db()
    
    # Initialize Telegram client
    global telegram_client
    try:
        # Try to connect using user account first
        telegram_client = TelegramClient(mode=TelegramClientMode.USER)
        await telegram_client.connect()
    except Exception as e:
        logger.warning(f"Failed to connect using user account: {e}")
        logger.info("Falling back to bot mode")
        # Fallback to bot mode
        telegram_client = TelegramClient(mode=TelegramClientMode.BOT)
        await telegram_client.connect()
    
    # Initialize message listener
    listener = TelegramMessageListener(client=telegram_client)
    asyncio.create_task(listener.start_listening())


@app.on_event("shutdown")
async def shutdown_event() -> None:
    """Clean up resources on application shutdown."""
    logger.info("Shutting down Telegram Channel Parser application")
    if telegram_client:
        await telegram_client.disconnect()


if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "src.main:app",
        host=settings.APP_HOST,
        port=settings.APP_PORT,
        reload=settings.APP_DEBUG,
    )