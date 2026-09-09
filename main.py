# ============================================
# PART 1 - IMPORTS & CONFIGURATION
# ============================================

import asyncio
import json
import os
import logging
import html
from datetime import datetime
from typing import Dict, List
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.enums import ParseMode
from aiogram.types import FSInputFile
from telethon import TelegramClient, events
from telethon.sessions import StringSession
from telethon.errors import FloodWaitError

# Logging setup
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

# ============ ENVIRONMENT VARIABLES ============
BOT_TOKEN = os.getenv("BOT_TOKEN", "8916402393:AAHXSC98Od-FyP9174D3uqgJkLZlX8H16AQ")
GROUP_CHAT_ID = int(os.getenv("GROUP_CHAT_ID", "-1003918092839"))
SESSION_STRING = os.getenv("SESSION_STRING", "1BJWap1sAULh18SeSR-v7gM3lEGMsI23Lrv0PktasVxLkZWR_75cIBtyRONJ9AWf8AfUdAtKs3tR30lFAkpKx3zd5d9mGtJ5yvkjOEKxRiiGoVxilM2BXsUCcmsKZpTh3h_L4drVRpeAjhmvKjhYjURW2CmEzW6G2KY8MqWPPRHI2mXjimrYEhRnpKeAxG0b7U8Sd_4ZMLlk-SRTktixnn3Rimcrjvx5m3I9jQRzV20n4YLS3Nznpg6hW9XLI9uYvYw-u4uCvgTMxZNp90nOckCLpb5Ca3tNkYehuZaevLsZXAsBlVEwln7rTEAOaHrKcXbL48FKUGK8WZDTe5PG6k8D1gEwWZsk=")
API_ID = int(os.getenv("API_ID", "34408702"))
API_HASH = os.getenv("API_HASH", "0d483149e1395cafd85e509d0b6978c3")

# Validate required variables
if not BOT_TOKEN:
    raise ValueError("BOT_TOKEN environment variable is required")
if not SESSION_STRING:
    raise ValueError("SESSION_STRING environment variable is required")
if not API_ID:
    raise ValueError("API_ID environment variable is required")
if not API_HASH:
    raise ValueError("API_HASH environment variable is required")

# ============ CONSTANTS ============
TELEGRAM_MAX_CAPTION_LENGTH = 1024
TELEGRAM_MAX_MESSAGE_LENGTH = 4096
CATCHUP_BATCH_SIZE = 50
MAX_RETRY_ATTEMPTS = 3

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

# ============ ADMIN ID ============
ADMIN_IDS = [8497620413]

# ============ MONITORED CHANNELS ============
MONITORED_CHANNELS = [
    -1003493566737,
    -1002928942881,
    -1003174711871,
    -1002843941054,
    -1002563415514,
    -1002394625189,
    -1002242996231,
    -1003656142433
]

CHANNEL_EMOJIS = ["🔴", "🟠", "🟡", "🟢", "🔵", "🟣", "⚫", "⚪", "🩵", "🩷", "🤍", "🖤", "💜", "💙", "💚", "💛", "🧡", "⬜", "🔶", "☑️", "🆕", "🟤", "🔴", "🟣"]

# ============ FILE PATHS ============
CHANNELS_FILE = "monitored_channels.json"
LAST_MESSAGE_FILE = "last_messages.json"
CHANNEL_NAMES_FILE = "channel_names.json"
CHANNEL_EMOJI_FILE = "channel_emoji.json"
MEDIA_CACHE_DIR = "media_cache"

# ============ STATE ============
last_message_ids: Dict[str, int] = {}
channel_names: Dict[str, str] = {}
channel_emojis: Dict[str, str] = {}
channel_locks: Dict[str, asyncio.Lock] = {}
channel_queues: Dict[str, asyncio.Queue] = {}
channel_processors: Dict[str, asyncio.Task] = {}
is_catchup_complete: Dict[str, bool] = {}

user_client = TelegramClient(StringSession(SESSION_STRING), API_ID, API_HASH)
# ============================================
# PART 2 - FILE HANDLING & HELPER FUNCTIONS
# ============================================

def atomic_write_json(filepath: str, data):
    temp_path = f"{filepath}.tmp"
    try:
        with open(temp_path, 'w') as f:
            json.dump(data, f, indent=2)
        os.replace(temp_path, filepath)
        return True
    except Exception as e:
        logger.error(f"Atomic write failed for {filepath}: {e}")
        if os.path.exists(temp_path):
            try:
                os.remove(temp_path)
            except:
                pass
        return False

def safe_load_json(filepath: str, default=None):
    if not os.path.exists(filepath):
        return default if default is not None else {}
    try:
        with open(filepath, 'r') as f:
            return json.load(f)
    except Exception as e:
        logger.error(f"Error loading {filepath}: {e}")
        return default if default is not None else {}

def load_channels() -> List[int]:
    global MONITORED_CHANNELS
    try:
        data = safe_load_json(CHANNELS_FILE)
        if data:
            MONITORED_CHANNELS = data
            logger.info(f"✅ Loaded {len(MONITORED_CHANNELS)} channels")
            return MONITORED_CHANNELS
    except Exception as e:
        logger.error(f"Error loading channels: {e}")
    
    MONITORED_CHANNELS = [
        -1003493566737,
        -1002928942881,
        -1003174711871,
        -1002843941054,
        -1002563415514,
        -1002394625189,
        -1002242996231,
        -1003656142433
    ]
    save_channels()
    return MONITORED_CHANNELS

def save_channels() -> bool:
    try:
        return atomic_write_json(CHANNELS_FILE, MONITORED_CHANNELS)
    except Exception as e:
        logger.error(f"Error saving channels: {e}")
        return False

def load_last_messages() -> Dict[str, int]:
    global last_message_ids
    try:
        data = safe_load_json(LAST_MESSAGE_FILE, {})
        if data:
            last_message_ids = {str(k): v for k, v in data.items()}
            logger.info(f"✅ Loaded last messages for {len(last_message_ids)} channels")
            return last_message_ids
    except Exception as e:
        logger.error(f"Error loading last messages: {e}")
    
    last_message_ids = {}
    return last_message_ids

def save_last_messages() -> bool:
    try:
        return atomic_write_json(LAST_MESSAGE_FILE, last_message_ids)
    except Exception as e:
        logger.error(f"Error saving last messages: {e}")
        return False

async def load_channel_names() -> Dict[str, str]:
    global channel_names
    try:
        data = safe_load_json(CHANNEL_NAMES_FILE, {})
        if data:
            channel_names = data
            logger.info(f"✅ Loaded {len(channel_names)} channel names")
            return channel_names
    except Exception as e:
        logger.error(f"Error loading channel names: {e}")
    
    channel_names = {}
    return channel_names

async def save_channel_names() -> bool:
    try:
        return atomic_write_json(CHANNEL_NAMES_FILE, channel_names)
    except Exception as e:
        logger.error(f"Error saving channel names: {e}")
        return False

async def load_channel_emojis() -> Dict[str, str]:
    global channel_emojis
    try:
        data = safe_load_json(CHANNEL_EMOJI_FILE, {})
        if data:
            channel_emojis = data
            logger.info(f"✅ Loaded {len(channel_emojis)} channel emojis")
            return channel_emojis
    except Exception as e:
        logger.error(f"Error loading channel emojis: {e}")
    
    channel_emojis = {}
    return channel_emojis

async def save_channel_emojis() -> bool:
    try:
        return atomic_write_json(CHANNEL_EMOJI_FILE, channel_emojis)
    except Exception as e:
        logger.error(f"Error saving channel emojis: {e}")
        return False

def get_channel_lock(chat_id: int) -> asyncio.Lock:
    chat_id_str = str(chat_id)
    if chat_id_str not in channel_locks:
        channel_locks[chat_id_str] = asyncio.Lock()
    return channel_locks[chat_id_str]

def get_channel_queue(chat_id: int) -> asyncio.Queue:
    chat_id_str = str(chat_id)
    if chat_id_str not in channel_queues:
        channel_queues[chat_id_str] = asyncio.Queue()
    return channel_queues[chat_id_str]

def get_channel_emoji(chat_id: int) -> str:
    chat_id_str = str(chat_id)
    if chat_id_str in channel_emojis:
        return channel_emojis[chat_id_str]
    
    available_emojis = [e for e in CHANNEL_EMOJIS if e not in channel_emojis.values()]
    emoji = available_emojis[0] if available_emojis else "🔴"
    channel_emojis[chat_id_str] = emoji
    asyncio.create_task(save_channel_emojis())
    return emoji

async def get_channel_name_from_telethon(chat_id: int) -> str:
    try:
        entity = await user_client.get_entity(chat_id)
        if hasattr(entity, 'title'):
            return entity.title
        elif hasattr(entity, 'first_name'):
            return entity.first_name
        else:
            return f"Channel {abs(chat_id)}"
    except Exception as e:
        logger.error(f"Error getting channel name for {chat_id}: {e}")
        return f"Channel {abs(chat_id)}"

async def update_channel_names():
    for chat_id in MONITORED_CHANNELS:
        try:
            name = await get_channel_name_from_telethon(chat_id)
            channel_names[str(chat_id)] = name
            logger.info(f"📛 Channel {chat_id}: {name}")
            get_channel_emoji(chat_id)
        except Exception as e:
            logger.error(f"Failed to get name for {chat_id}: {e}")
    await save_channel_names()
    await save_channel_emojis()

def get_channel_name(chat_id: int) -> str:
    chat_id_str = str(chat_id)
    if chat_id_str in channel_names:
        return channel_names[chat_id_str]
    return f"Channel {abs(chat_id)}"

# ============ MEDIA DOWNLOAD ============

async def download_media_with_retry(message, max_retries: int = MAX_RETRY_ATTEMPTS):
    os.makedirs(MEDIA_CACHE_DIR, exist_ok=True)
    
    for attempt in range(max_retries):
        try:
            file_path = None
            file_name = None
            
            if message.photo:
                file_name = f"{MEDIA_CACHE_DIR}/photo_{message.id}_{datetime.now().timestamp()}.jpg"
                file_path = await user_client.download_media(message.photo, file=file_name)
            elif message.video:
                file_name = f"{MEDIA_CACHE_DIR}/video_{message.id}_{datetime.now().timestamp()}.mp4"
                file_path = await user_client.download_media(message.video, file=file_name)
            elif message.voice:
                file_name = f"{MEDIA_CACHE_DIR}/voice_{message.id}_{datetime.now().timestamp()}.ogg"
                file_path = await user_client.download_media(message.voice, file=file_name)
            elif message.audio:
                file_name = f"{MEDIA_CACHE_DIR}/audio_{message.id}_{datetime.now().timestamp()}.mp3"
                file_path = await user_client.download_media(message.audio, file=file_name)
            elif message.sticker:
                file_name = f"{MEDIA_CACHE_DIR}/sticker_{message.id}_{datetime.now().timestamp()}.webp"
                file_path = await user_client.download_media(message.sticker, file=file_name)
            elif message.document:
                doc_name = getattr(message.document, "file_name", f"document_{message.id}")
                file_name = f"{MEDIA_CACHE_DIR}/doc_{message.id}_{datetime.now().timestamp()}_{doc_name}"
                file_path = await user_client.download_media(message.document, file=file_name)
            
            if file_path and os.path.exists(file_path):
                return file_path, file_name
            
            if attempt < max_retries - 1:
                await asyncio.sleep(2 ** attempt)
                
        except FloodWaitError as e:
            logger.warning(f"Flood wait {e.seconds}s, waiting...")
            await asyncio.sleep(e.seconds + 1)
        except Exception as e:
            logger.error(f"Download attempt {attempt+1} failed: {e}")
            if attempt < max_retries - 1:
                await asyncio.sleep(2 ** attempt)
    
    return None, None

# ============ MESSAGE TYPE DETECTION ============

def get_message_type(message):
    if message.voice:
        return "voice"
    elif message.photo:
        return "photo"
    elif message.video:
        return "video"
    elif message.sticker:
        return "sticker"
    elif message.audio:
        return "audio"
    elif message.document:
        try:
            mime_type = getattr(message.document, "mime_type", "") or ""
            attributes = getattr(message.document, "attributes", []) or []
            for attr in attributes:
                if attr.__class__.__name__ == "DocumentAttributeAnimated":
                    return "gif"
            if mime_type == "image/gif":
                return "gif"
            if mime_type.startswith("video/"):
                return "video"
        except Exception:
            pass
        return "document"
    elif message.text:
        return "text"
    else:
        return "unknown"

def get_media_emoji(message_type: str) -> str:
    emojis = {
        "voice": "🎙️",
        "photo": "📸",
        "video": "🎬",
        "document": "📄",
        "sticker": "🎨",
        "gif": "🎞️",
        "audio": "🎵",
        "text": "📝"
    }
    return emojis.get(message_type, "📩")

# ============ FORMATTING ============

def safe_html_escape(text: str) -> str:
    if not text:
        return text
    return html.escape(text)

def split_long_message(text: str, max_length: int = TELEGRAM_MAX_MESSAGE_LENGTH) -> List[str]:
    if len(text) <= max_length:
        return [text]
    
    parts = []
    while text:
        split_point = max_length
        if split_point < len(text):
            last_newline = text.rfind('\n', 0, split_point)
            last_space = text.rfind(' ', 0, split_point)
            split_point = max(last_newline, last_space)
            if split_point <= 0:
                split_point = max_length
        
        parts.append(text[:split_point])
        text = text[split_point:].lstrip()
    
    return parts

def format_channel_message(chat_id: int, message_text: str, message_id: int, 
                          message_type: str = "text") -> str:
    channel_name = get_channel_name(chat_id)
    emoji = get_channel_emoji(chat_id)
    timestamp = datetime.now().strftime("%d %b %Y • %I:%M %p")
    media_emoji = get_media_emoji(message_type)
    
    channel_name_escaped = safe_html_escape(channel_name)
    
    main_content = f"""{emoji} <b>{channel_name_escaped}</b>
{media_emoji} <b>{message_type.upper()}</b>
🕒 {timestamp}"""
    
    if message_text:
        message_text_escaped = safe_html_escape(message_text)
        msg_content = f"\n━━━━━━━━━━━━━━━━━━━━\n<b>{message_text_escaped}</b>"
    else:
        msg_content = f"\n━━━━━━━━━━━━━━━━━━━━\n<em>📷 {message_type.upper()} message</em>"
    
    # NO expandable - direct visible
    formatted_msg = f"""<blockquote>
{main_content}{msg_content}
</blockquote>"""
    return formatted_msg

def format_combined_message(channels_data: Dict) -> str:
    if not channels_data:
        return "<b>📭 No messages found</b>"
    
    timestamp = datetime.now().strftime("%d %b %Y • %I:%M %p")
    
    msg = f"""<blockquote>
<b>🌅 ALL CHANNELS - LATEST UPDATES</b>
🕒 {timestamp}
</blockquote>
"""
    
    for chat_id, data in channels_data.items():
        channel_name = get_channel_name(int(chat_id))
        emoji = get_channel_emoji(int(chat_id))
        msg_type = data.get('type', 'text')
        media_emoji = get_media_emoji(msg_type)
        message_text = data.get('message', 'No message')
        
        channel_name_escaped = safe_html_escape(channel_name)
        
        if message_text and message_text != '📭 No messages yet':
            message_text_escaped = safe_html_escape(message_text)
            message_text = f"<b>{message_text_escaped}</b>"
        elif msg_type != 'text' and not message_text:
            message_text = f"📷 {msg_type.upper()} message"
        
        msg += f"""<blockquote>
{emoji} <b>{channel_name_escaped}</b>
{media_emoji} {msg_type.upper()}
🕒 {data.get('date', timestamp)}
━━━━━━━━━━━━━━━━━━━━
{message_text}
</blockquote>
"""
    return msg

def format_channel_list() -> str:
    if not MONITORED_CHANNELS:
        return "<b>📭 No channels being monitored</b>"
    
    msg = "<b>📡 MONITORED CHANNELS</b>\n\n"
    for idx, chat_id in enumerate(MONITORED_CHANNELS, 1):
        name = get_channel_name(chat_id)
        emoji = get_channel_emoji(chat_id)
        msg += f"{idx}. {emoji} <b>{safe_html_escape(name)}</b>\n"
        msg += f"   📌 ID: <code>{chat_id}</code>\n"
    return msg
    # ============================================
# PART 3 - QUEUE, PROCESSING & SENDING
# ============================================

# ============ SEND MESSAGE WITH MEDIA ============

async def send_message_with_media(message, msg_type: str, msg_text: str, chat_id: int, msg_id: int, target_chat_id: int = None) -> bool:
    """Send message with media, handling caption limits - reusable function"""
    if target_chat_id is None:
        target_chat_id = GROUP_CHAT_ID
    
    formatted_msg = format_channel_message(chat_id, msg_text, msg_id, msg_type)
    
    # VOICE
    if message.voice:
        file_path, _ = await download_media_with_retry(message)
        if file_path and os.path.exists(file_path):
            if len(formatted_msg) > TELEGRAM_MAX_CAPTION_LENGTH:
                await bot.send_voice(target_chat_id, FSInputFile(file_path))
                for part in split_long_message(formatted_msg):
                    await bot.send_message(target_chat_id, part, parse_mode=ParseMode.HTML)
            else:
                await bot.send_voice(target_chat_id, FSInputFile(file_path), 
                                    caption=formatted_msg, parse_mode=ParseMode.HTML)
            os.remove(file_path)
            return True
        else:
            for part in split_long_message(formatted_msg):
                await bot.send_message(target_chat_id, part, parse_mode=ParseMode.HTML)
            return True
    
    # VIDEO
    elif message.video:
        file_path, _ = await download_media_with_retry(message)
        if file_path and os.path.exists(file_path):
            if len(formatted_msg) > TELEGRAM_MAX_CAPTION_LENGTH:
                await bot.send_video(target_chat_id, FSInputFile(file_path))
                for part in split_long_message(formatted_msg):
                    await bot.send_message(target_chat_id, part, parse_mode=ParseMode.HTML)
            else:
                await bot.send_video(target_chat_id, FSInputFile(file_path),
                                    caption=formatted_msg, parse_mode=ParseMode.HTML)
            os.remove(file_path)
            return True
        else:
            for part in split_long_message(formatted_msg):
                await bot.send_message(target_chat_id, part, parse_mode=ParseMode.HTML)
            return True
    
    # STICKER
    elif message.sticker:
        file_path, _ = await download_media_with_retry(message)
        if file_path and os.path.exists(file_path):
            await bot.send_sticker(target_chat_id, FSInputFile(file_path))
            for part in split_long_message(formatted_msg):
                await bot.send_message(target_chat_id, part, parse_mode=ParseMode.HTML)
            os.remove(file_path)
            return True
        else:
            for part in split_long_message(formatted_msg):
                await bot.send_message(target_chat_id, part, parse_mode=ParseMode.HTML)
            return True
    
    # AUDIO
    elif message.audio:
        file_path, _ = await download_media_with_retry(message)
        if file_path and os.path.exists(file_path):
            if len(formatted_msg) > TELEGRAM_MAX_CAPTION_LENGTH:
                await bot.send_audio(target_chat_id, FSInputFile(file_path))
                for part in split_long_message(formatted_msg):
                    await bot.send_message(target_chat_id, part, parse_mode=ParseMode.HTML)
            else:
                await bot.send_audio(target_chat_id, FSInputFile(file_path),
                                    caption=formatted_msg, parse_mode=ParseMode.HTML)
            os.remove(file_path)
            return True
        else:
            for part in split_long_message(formatted_msg):
                await bot.send_message(target_chat_id, part, parse_mode=ParseMode.HTML)
            return True
    
    # DOCUMENT / GIF
    elif message.document:
        file_path, _ = await download_media_with_retry(message)
        if file_path and os.path.exists(file_path):
            if msg_type == "gif":
                if len(formatted_msg) > TELEGRAM_MAX_CAPTION_LENGTH:
                    await bot.send_animation(target_chat_id, FSInputFile(file_path))
                    for part in split_long_message(formatted_msg):
                        await bot.send_message(target_chat_id, part, parse_mode=ParseMode.HTML)
                else:
                    await bot.send_animation(target_chat_id, FSInputFile(file_path),
                                            caption=formatted_msg, parse_mode=ParseMode.HTML)
            else:
                if len(formatted_msg) > TELEGRAM_MAX_CAPTION_LENGTH:
                    await bot.send_document(target_chat_id, FSInputFile(file_path))
                    for part in split_long_message(formatted_msg):
                        await bot.send_message(target_chat_id, part, parse_mode=ParseMode.HTML)
                else:
                    await bot.send_document(target_chat_id, FSInputFile(file_path),
                                           caption=formatted_msg, parse_mode=ParseMode.HTML)
            os.remove(file_path)
            return True
        else:
            for part in split_long_message(formatted_msg):
                await bot.send_message(target_chat_id, part, parse_mode=ParseMode.HTML)
            return True
    
    # PHOTO
    elif message.photo:
        file_path, _ = await download_media_with_retry(message)
        if file_path and os.path.exists(file_path):
            if len(formatted_msg) > TELEGRAM_MAX_CAPTION_LENGTH:
                await bot.send_photo(target_chat_id, FSInputFile(file_path))
                for part in split_long_message(formatted_msg):
                    await bot.send_message(target_chat_id, part, parse_mode=ParseMode.HTML)
            else:
                await bot.send_photo(target_chat_id, FSInputFile(file_path),
                                    caption=formatted_msg, parse_mode=ParseMode.HTML)
            os.remove(file_path)
            return True
        else:
            for part in split_long_message(formatted_msg):
                await bot.send_message(target_chat_id, part, parse_mode=ParseMode.HTML)
            return True
    
    # TEXT ONLY
    else:
        for part in split_long_message(formatted_msg):
            await bot.send_message(target_chat_id, part, parse_mode=ParseMode.HTML)
        return True

# ============ PROCESS MESSAGE ============

async def process_message_safe(message):
    """Process message with comprehensive error handling and retry"""
    chat_id = message.chat_id
    msg_id = message.id
    
    chat_id_str = str(chat_id)
    last_id = last_message_ids.get(chat_id_str, 0)
    
    # Check if already processed
    if msg_id <= last_id:
        logger.debug(f"⏭️ Skipping already processed {chat_id}:{msg_id}")
        return
    
    msg_type = get_message_type(message)
    # IMPORTANT: Use message.text, NOT message.caption
    msg_text = message.text or None
    
    # Try to send with retry
    for attempt in range(MAX_RETRY_ATTEMPTS):
        try:
            sent = await send_message_with_media(message, msg_type, msg_text, chat_id, msg_id)
            
            if sent:
                # Only save ID after successful send
                last_message_ids[chat_id_str] = msg_id
                save_last_messages()
                logger.info(f"✅ Sent {msg_type} from {chat_id}:{msg_id}")
                return
            else:
                logger.warning(f"⚠️ Send failed for {chat_id}:{msg_id}, attempt {attempt+1}")
                
        except FloodWaitError as e:
            logger.warning(f"Flood wait {e.seconds}s, waiting...")
            await asyncio.sleep(e.seconds + 1)
        except Exception as e:
            logger.error(f"Error sending {chat_id}:{msg_id}, attempt {attempt+1}: {e}")
            if attempt < MAX_RETRY_ATTEMPTS - 1:
                await asyncio.sleep(2 ** attempt)
    
    # If all retries failed, log but don't save ID
    logger.error(f"❌ Failed to send {chat_id}:{msg_id} after {MAX_RETRY_ATTEMPTS} attempts")

# ============ QUEUE PROCESSOR ============

async def process_queue_worker(chat_id: int):
    """Background worker that processes messages from queue in order"""
    chat_id_str = str(chat_id)
    lock = get_channel_lock(chat_id)
    queue = get_channel_queue(chat_id)
    
    while True:
        try:
            # Get message from queue
            message = await queue.get()
            
            # Process with lock to ensure order
            async with lock:
                await process_message_safe(message)
            
            queue.task_done()
            
        except asyncio.CancelledError:
            logger.info(f"Queue worker cancelled for {chat_id}")
            break
        except Exception as e:
            logger.error(f"Queue worker error for {chat_id}: {e}")
            queue.task_done()
            await asyncio.sleep(1)

def ensure_processor_running(chat_id: int):
    """Ensure a queue processor is running for the channel"""
    chat_id_str = str(chat_id)
    if chat_id_str not in channel_processors or channel_processors[chat_id_str].done():
        channel_processors[chat_id_str] = asyncio.create_task(process_queue_worker(chat_id))
        logger.info(f"Started queue processor for {chat_id}")

async def add_to_queue(chat_id: int, message):
    """Add message to channel queue and ensure processor is running"""
    queue = get_channel_queue(chat_id)
    await queue.put(message)
    ensure_processor_running(chat_id)

# ============ CATCH-UP SYSTEM ============

async def catch_up_channel(chat_id: int, last_id: int) -> int:
    """Catch up all missed messages for a channel - reliable pagination"""
    logger.info(f"🔄 Catching up channel {chat_id} from ID {last_id}")
    processed_count = 0
    
    try:
        # Get latest message
        latest_msg = None
        async for msg in user_client.iter_messages(chat_id, limit=1):
            latest_msg = msg
            break
        
        if not latest_msg:
            logger.info(f"ℹ️ No messages in channel {chat_id}")
            return 0
        
        latest_id = latest_msg.id
        
        if latest_id <= last_id:
            logger.info(f"ℹ️ No new messages in channel {chat_id} (latest: {latest_id}, last: {last_id})")
            return 0
        
        logger.info(f"📥 Channel {chat_id}: {latest_id - last_id} messages to catch up")
        
        # RELIABLE PAGINATION: Start from last_id + 1, go to latest_id
        current_start = last_id + 1
        
        while current_start <= latest_id:
            batch_end = min(current_start + CATCHUP_BATCH_SIZE - 1, latest_id)
            
            # Fetch messages in this range
            messages = []
            async for msg in user_client.iter_messages(
                chat_id,
                min_id=current_start,
                max_id=batch_end,
                reverse=True  # Oldest first
            ):
                if msg.id > last_id:
                    messages.append(msg)
            
            if not messages:
                # No messages in this range, move forward
                current_start = batch_end + 1
                continue
            
            # Process each message
            for msg in messages:
                logger.info(f"📥 Catch-up: {chat_id} message {msg.id}")
                # Add to queue for ordered processing
                await add_to_queue(chat_id, msg)
                processed_count += 1
                await asyncio.sleep(0.1)  # Rate limit protection
            
            # Update progress
            current_start = batch_end + 1
            
            # Save progress periodically
            if processed_count % 10 == 0:
                save_last_messages()
                logger.info(f"💾 Progress saved for {chat_id}: {processed_count} messages")
        
        logger.info(f"✅ Channel {chat_id} catch-up complete: {processed_count} messages")
        
    except FloodWaitError as e:
        logger.warning(f"Flood wait {e.seconds}s for channel {chat_id}, waiting...")
        await asyncio.sleep(e.seconds + 1)
        # Retry
        return await catch_up_channel(chat_id, last_id)
    except Exception as e:
        logger.error(f"❌ Catch-up error for {chat_id}: {e}")
    
    return processed_count

async def catch_up_all_channels():
    """Catch up all monitored channels"""
    logger.info("🔄 Starting comprehensive catch-up...")
    total_processed = 0
    
    for chat_id in MONITORED_CHANNELS:
        chat_id_str = str(chat_id)
        last_id = last_message_ids.get(chat_id_str, 0)
        
        try:
            processed = await catch_up_channel(chat_id, last_id)
            total_processed += processed
        except Exception as e:
            logger.error(f"❌ Error catching up channel {chat_id}: {e}")
        
        await asyncio.sleep(0.5)
    
    logger.info(f"✅ Catch-up complete! {total_processed} messages processed")
    return total_processed
    # ============================================
# PART 4 - MONITOR, COMMANDS & MAIN
# ============================================

# ============ MONITOR CHANNELS ============

async def monitor_channels():
    """Monitor channels with dynamic chat_id filtering"""
    logger.info("🚀 Starting channel monitor...")
    
    @user_client.on(events.NewMessage())
    async def handler(event):
        # Dynamic check - works with add/remove channel
        if event.chat_id in MONITORED_CHANNELS:
            # Queue message for ordered processing
            await add_to_queue(event.chat_id, event.message)
    
    await user_client.run_until_disconnected()

# ============ GET LAST MESSAGES ============

async def get_channel_last_messages(chat_id: int, limit: int = 1) -> List[Dict]:
    try:
        messages = []
        async for msg in user_client.iter_messages(chat_id, limit=limit):
            msg_type = get_message_type(msg)
            msg_text = msg.text or None
            if not msg_text and msg_type != 'text':
                msg_text = f"📷 {msg_type.upper()} message"
            elif not msg_text:
                msg_text = "No message text"
            
            messages.append({
                'message_id': msg.id,
                'message': msg_text,
                'type': msg_type,
                'date': msg.date.strftime('%d %b %Y • %I:%M %p'),
                'message_obj': msg
            })
        return messages
    except Exception as e:
        logger.error(f"Error getting messages from {chat_id}: {e}")
        return []

# ============ COMMAND HANDLERS ============

@dp.message(Command("start"))
async def start_command(message: types.Message):
    if message.from_user.id not in ADMIN_IDS:
        await message.reply("🚫")
        return
    
    await message.reply(
        f"""<blockquote>
<b>🤖 Channel Monitor Bot</b>

✅ <b>Bot is online</b>
📡 Monitoring <b>{len(MONITORED_CHANNELS)}</b> channels
🎙️ Voice messages supported
📸 Media messages supported

<b>📋 Commands:</b>
/channels - <b>List monitored channels</b>
/last - <b>Get last message from all channels (COMBINED)</b>
/addchannel - <b>Add channel to monitor</b>
/removechannel - <b>Remove channel from monitoring</b>

<i>New messages from monitored channels are automatically posted here.</i>
</blockquote>""",
        parse_mode=ParseMode.HTML
    )

@dp.message(Command("channels"))
async def channels_command(message: types.Message):
    if message.from_user.id not in ADMIN_IDS:
        await message.reply("🚫")
        return
    await message.reply(format_channel_list(), parse_mode=ParseMode.HTML)

@dp.message(Command("last"))
async def last_command(message: types.Message):
    """Get last message from ALL channels with media"""
    status_msg = await message.reply("🔄 <b>Fetching messages...</b>", parse_mode=ParseMode.HTML)
    
    channels_data = {}
    channel_messages = {}
    
    for chat_id in MONITORED_CHANNELS:
        messages = await get_channel_last_messages(chat_id, limit=1)
        if messages:
            msg = messages[0]
            channels_data[str(chat_id)] = {
                'message': msg['message'],
                'type': msg['type'],
                'date': msg['date']
            }
            channel_messages[str(chat_id)] = msg
        else:
            channels_data[str(chat_id)] = {
                'message': '📭 No messages yet',
                'type': 'text',
                'date': datetime.now().strftime('%d %b %Y • %I:%M %p')
            }
    
    if not channels_data:
        await status_msg.edit_text("📭 <b>No channels found.</b>", parse_mode=ParseMode.HTML)
        return
    
    # Send combined text first
    combined_msg = format_combined_message(channels_data)
    for part in split_long_message(combined_msg):
        await status_msg.reply(part, parse_mode=ParseMode.HTML)
    await status_msg.delete()
    
    # Send media for each channel
    for chat_id_str, msg_data in channel_messages.items():
        chat_id = int(chat_id_str)
        msg_type = msg_data['type']
        
        if msg_type == 'text':
            continue
        
        msg_text = msg_data['message']
        
        try:
            await asyncio.sleep(0.3)
            await send_message_with_media(
                msg_data['message_obj'], 
                msg_type, 
                msg_text, 
                chat_id, 
                msg_data['message_id'],
                message.chat.id  # Target user's chat
            )
        except Exception as e:
            logger.error(f"Error sending media for channel {chat_id}: {e}")

@dp.message(Command("addchannel"))
async def add_channel_command(message: types.Message):
    if message.from_user.id not in ADMIN_IDS:
        await message.reply("🚫")
        return
    
    args = message.text.split()
    if len(args) < 2:
        await message.reply(
            "❌ <b>Usage:</b> <code>/addchannel CHANNEL_ID</code>\n\n"
            "<b>Example:</b> <code>/addchannel -1001234567890</code>\n\n"
            "📌 Make sure your user account is in the channel.",
            parse_mode=ParseMode.HTML
        )
        return
    
    try:
        channel_id = int(args[1])
        
        if channel_id in MONITORED_CHANNELS:
            await message.reply(f"⚠️ Channel <code>{channel_id}</code> is already being monitored.", parse_mode=ParseMode.HTML)
            return
        
        # Verify channel exists and user can access it
        try:
            chat = await user_client.get_entity(channel_id)
            channel_name = chat.title or f"Channel {abs(channel_id)}"
            channel_names[str(channel_id)] = channel_name
            await save_channel_names()
            get_channel_emoji(channel_id)
            await save_channel_emojis()
        except Exception as e:
            await message.reply(
                f"⚠️ <b>Warning:</b> Could not access channel.\n"
                f"Error: {str(e)[:100]}\n\n"
                f"Make sure your user account is in the channel.",
                parse_mode=ParseMode.HTML
            )
            return
        
        # Add to monitored list (immediate effect)
        MONITORED_CHANNELS.append(channel_id)
        save_channels()
        last_message_ids[str(channel_id)] = 0
        save_last_messages()
        
        # Initialize queue and ensure processor is running
        get_channel_queue(channel_id)
        get_channel_lock(channel_id)
        ensure_processor_running(channel_id)
        
        emoji = get_channel_emoji(channel_id)
        
        await message.reply(
            f"✅ <b>Channel Added!</b>\n\n"
            f"{emoji} <b>Name:</b> {channel_name}\n"
            f"📌 <b>ID:</b> <code>{channel_id}</code>\n\n"
            f"🔔 Now monitoring this channel for new messages.\n"
            f"📥 Running catch-up for missed messages...",
            parse_mode=ParseMode.HTML
        )
        
        # Catch up this channel
        asyncio.create_task(catch_up_channel(channel_id, 0))
        
    except ValueError:
        await message.reply("❌ <b>Invalid channel ID.</b> Please provide a numeric ID.", parse_mode=ParseMode.HTML)
    except Exception as e:
        await message.reply(f"❌ <b>Error:</b> {e}", parse_mode=ParseMode.HTML)

@dp.message(Command("removechannel"))
async def remove_channel_command(message: types.Message):
    if message.from_user.id not in ADMIN_IDS:
        await message.reply("🚫")
        return
    
    args = message.text.split()
    if len(args) < 2:
        await message.reply(
            "❌ <b>Usage:</b> <code>/removechannel CHANNEL_ID</code>\n\n"
            "<b>Example:</b> <code>/removechannel -1001234567890</code>",
            parse_mode=ParseMode.HTML
        )
        return
    
    try:
        channel_id = int(args[1])
        chat_id_str = str(channel_id)
        
        if channel_id not in MONITORED_CHANNELS:
            await message.reply(f"⚠️ Channel <code>{channel_id}</code> is not being monitored.", parse_mode=ParseMode.HTML)
            return
        
        # Remove immediately
        MONITORED_CHANNELS.remove(channel_id)
        save_channels()
        
        if chat_id_str in last_message_ids:
            del last_message_ids[chat_id_str]
            save_last_messages()
        
        # Don't delete queue/lock immediately - let processor finish
        # Mark channel as inactive by removing from monitored list
        
        await message.reply(
            f"✅ <b>Channel Removed!</b>\n\n"
            f"📌 <b>ID:</b> <code>{channel_id}</code>\n\n"
            f"🔔 No longer monitoring this channel.",
            parse_mode=ParseMode.HTML
        )
    except ValueError:
        await message.reply("❌ <b>Invalid channel ID.</b> Please provide a numeric ID.", parse_mode=ParseMode.HTML)
    except Exception as e:
        await message.reply(f"❌ <b>Error:</b> {e}", parse_mode=ParseMode.HTML)

# ============ BACKGROUND TASK ============

async def background_monitor():
    # Wait for initial setup
    await asyncio.sleep(5)
    
    logger.info("🚀 Starting channel monitor...")
    logger.info(f"📡 Monitoring {len(MONITORED_CHANNELS)} channels")
    logger.info(f"📤 Posting to group: {GROUP_CHAT_ID}")
    
    try:
        await bot.send_message(
            GROUP_CHAT_ID,
            f"""<blockquote>
<b>🤖 Channel Monitor Active</b>

📡 Monitoring <b>{len(MONITORED_CHANNELS)}</b> channels
🎙️ Voice & Media messages supported
📤 New messages will appear here automatically.
</blockquote>""",
            parse_mode=ParseMode.HTML
        )
    except Exception as e:
        logger.error(f"Failed to send startup message: {e}")
    
    await monitor_channels()

# ============ MAIN ============

async def main():
    # Load state
    load_channels()
    load_last_messages()
    await load_channel_names()
    await load_channel_emojis()
    
    # Initialize queues and processors
    for chat_id in MONITORED_CHANNELS:
        get_channel_queue(chat_id)
        get_channel_lock(chat_id)
        ensure_processor_running(chat_id)
    
    # Start user client
    await user_client.start()
    logger.info("✅ User client started successfully")
    
    # Update channel names
    await update_channel_names()
    
    # IMPORTANT: Register NewMessage handler BEFORE catch-up
    # This ensures no live messages are missed during catch-up
    monitor_task = asyncio.create_task(background_monitor())
    
    # Wait a moment for handler to register
    await asyncio.sleep(1)
    
    # Run catch-up AFTER handler is registered
    logger.info("🔄 Running catch-up for missed messages...")
    total_processed = await catch_up_all_channels()
    logger.info(f"✅ Catch-up complete: {total_processed} messages processed")
    
    # Keep bot running
    try:
        await dp.start_polling(bot)
    finally:
        monitor_task.cancel()
        try:
            await monitor_task
        except asyncio.CancelledError:
            pass

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n👋 Bot stopped")
    except Exception as e:
        print(f"❌ Error: {e}")