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
    UserAlreadyParticipant,
    InviteHashExpired,
    InviteHashInvalid,
    PeerIdInvalid,
    InviteRequestSent
)
from urllib.parse import urlparse
from config import (
    API_ID,
    API_HASH,
    BOT_TOKEN,
    ADMIN_LIMIT,
    ADMIN_IDS,
    DEFAULT_LIMIT
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Bot Client
app = Client(
    "app_session",
    api_id=API_ID,
    api_hash=API_HASH,
    bot_token=BOT_TOKEN,
    workers=1000
)

# User Client (for scraping)
user = Client(
    "session_923294013197",
    api_id=API_ID,
    api_hash=API_HASH,
    phone_number="+923294013197", # Ensure this matches your session
    workers=1000
)

START_MESSAGE = """
『⭐️ 𝐂𝐑𝐄𝐃𝐈𝐓 𝐂𝐀𝐑𝐃 𝐒𝐂𝐑𝐀𝐏𝐄𝐑 ⭐️』

⌾ 𝐒𝐂𝐑𝐀𝐏𝐄 𝐂𝐑𝐄𝐃𝐈𝐓 𝐂𝐀𝐑𝐃𝐒 from Telegram channels

⚡️ 𝐂𝐎𝐌𝐌𝐀𝐍𝐃𝐒:
▬▬▬▬▬▬▬▬▬▬▬▬▬
/scr - Scrape from single channel 📺
/mc - Scrape from multiple channels 📡
/clean - Format card data from file 🧹

<strong>𝐄𝐗𝐀𝐌𝐏𝐋𝐄𝐒:</strong>
❯ /scr @channel 100
❯ /scr @channel 100 515462
❯ /scr @channel 100 BankName

【✯ 𝐇𝐀𝐏𝐏𝐘 𝐒𝐂𝐑𝐀𝐏𝐈𝐍𝐆! ✯】
"""

# --- Cronjob Function ---
async def keep_alive_task():
    logger.info(f"Cronjob: Bot heartbeat check at {datetime.now()}")

# --- Helper Functions ---
async def scrape_messages(client, channel_username, limit, start_number=None, bank_name=None):
    messages = []
    count = 0
    pattern = r'\d{16}\D*\d{2}\D*\d{2,4}\D*\d{3,4}'
    
    async for message in user.search_messages(channel_username):
        if count >= limit:
            break
        text = message.text or message.caption
        if text:
            if bank_name and bank_name.lower() not in text.lower():
                continue
            matched_messages = re.findall(pattern, text)
            if matched_messages:
                for matched_message in matched_messages:
                    extracted_values = re.findall(r'\d+', matched_message)
                    if len(extracted_values) == 4:
                        card_number, mo, year, cvv = extracted_values
                        year = year[-2:]
                        if start_number and not card_number.startswith(start_number[:6]):
                            continue
                        messages.append(f"{card_number}|{mo}|{year}|{cvv}")
                count += len(matched_messages)
    return messages[:limit]

def remove_duplicates(messages):
    unique_messages = list(set(messages))
    return unique_messages, len(messages) - len(unique_messages)

async def get_user_link(message):
    if not message.from_user:
        return 'Scrapper x Cleaner'
    return f'<a href="tg://user?id={message.from_user.id}">{message.from_user.first_name}</a>'

async def join_private_chat(client, invite_link):
    try:
        await client.join_chat(invite_link)
        return True
    except UserAlreadyParticipant:
        return True
    except Exception:
        return False

# --- Handlers ---
@app.on_message(filters.command(["scr"], prefixes=["/"]) & (filters.group | filters.private))
async def scr_cmd(client, message):
    args = message.text.split()[1:]
    if len(args) < 2:
        return await message.reply("<b>⚠️ Provide channel and limit.</b>")
    
    target = args[0]
    limit = int(args[1])
    
    temp = await message.reply("<b>𝐒𝐜𝐫𝐚𝐩𝐢𝐧𝐠 𝐈𝐧 𝐏𝐫𝐨𝐠𝐫𝐞𝐬𝐬...</b>")
    
    # Handle Private Links
    if "t.me/+" in target:
        await join_private_chat(user, target)
        
    results = await scrape_messages(user, target, limit)
    unique, dups = remove_duplicates(results)
    
    if not unique:
        return await temp.edit("<b>❌ No cards found.</b>")
    
    # Send File
    file_path = f"scraped_{message.chat.id}.txt"
    async with aiofiles.open(file_path, 'w') as f:
        await f.write("\n".join(unique))
    
    await message.reply_document(file_path, caption=f"✅ Scraped {len(unique)} cards.")
    os.remove(file_path)
    await temp.delete()

@app.on_message(filters.command("start"))
async def start(client, message):
    await message.reply(START_MESSAGE, reply_markup=InlineKeyboardMarkup([
        [InlineKeyboardButton("Dev", user_id=5541778617)]
    ]))

# --- Execution ---
async def main():
    await user.start()
    await app.start()
    
    # Start Cronjob
    scheduler = AsyncIOScheduler()
    scheduler.add_job(keep_alive_task, "interval", hours=1)
    scheduler.start()
    
    logger.info("Bot is fully running with Cronjob!")
    await idle()

if __name__ == "__main__":
    asyncio.run(main())
    