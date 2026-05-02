import re
import os
import asyncio
import logging
import aiofiles
from datetime import datetime
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from pyrogram.enums import ParseMode
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from pyrogram import Client, filters, idle
from pyrogram.errors import (
    UserAlreadyParticipant, InviteHashExpired, InviteHashInvalid, PeerIdInvalid, InviteRequestSent
)
from urllib.parse import urlparse
from config import API_ID, API_HASH, BOT_TOKEN, ADMIN_LIMIT, ADMIN_IDS, DEFAULT_LIMIT

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Clients
app = Client("app_session", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN, workers=1000)
user = Client("session_923294013197", api_id=API_ID, api_hash=API_HASH, phone_number="+923294013197", workers=1000)

# --- INTERNAL CRONJOB ---
async def keep_alive_task():
    logger.info(f"Cronjob Heartbeat: {datetime.now()}")

# [PASTE ALL YOUR REMAINING FUNCTIONS HERE: scrape_messages, remove_duplicates, 
# send_results, join_private_chat, setup_scr_handler, mc_cmd, clean_cmd, etc.]

# --- UPDATED STARTUP LOGIC (Fixes the Runtime Error) ---
async def main():
    setup_scr_handler(app) # Initialize your handlers
    await user.start()
    await app.start()
    
    # Start the internal scheduler (Cronjob)
    scheduler = AsyncIOScheduler()
    scheduler.add_job(keep_alive_task, "interval", hours=1)
    scheduler.start()
    
    logger.info("Bot is Live and Heartbeat is active!")
    await idle() # Keeps the bot running
    await app.stop()
    await user.stop()

if __name__ == "__main__":
    asyncio.run(main()) # Use this instead of app.run()
