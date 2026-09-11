# ============================================
# PART 1 - IMPORTS & CONFIGURATION
# ============================================

import asyncio
import json
import os
import logging
import re
import html
from datetime import datetime
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.enums import ParseMode
from aiogram.types import FSInputFile, InputMediaPhoto
from telethon import TelegramClient, events
from telethon.sessions import StringSession
from telethon.tl.types import MessageEntityCustomEmoji, MessageEntityTextUrl

# Logging setup
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

# ============ CONFIGURATION ============
BOT_TOKEN = "8916402393:AAHXSC98Od-FyP9174D3uqgJkLZlX8H16AQ"
GROUP_CHAT_ID = -1003918092839
SESSION_STRING = "1BJWap1sAUJPcXL59f8W2BlJzRQabJl_0H4NYfrYLnth9ZxZiEdh_t3L5MxYZd7KjqeROyMiQwcoo64s9ijr8ll44nmfiTRR5gqxHKG2-DCI-FtxuRWiorswXZ4XhF0fcV9EDxJDr-5vfqBmJnc1bU45thEIfFxXQD_wHZW32RCPzO-j6pofDFfhkNHeIoD_kQDIYJ4S2MtYH4UQUib_so3EmWCO9SHSzndNlX2QKbuf2o6fVqIhcM7860zFpbaoLQUh5tYSSvg4k_vrNc4UOpciv5259jZzEUUV1bEyYziNJUi0Apv4amPWEWIWD97efUq_-VyJO_fFVzxd9kQy0Zj4e5XYikxg="
API_ID = 34408702
API_HASH = "0d483149e1395cafd85e509d0b6978c3"

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

CHANNELS_FILE = "monitored_channels.json"
LAST_MESSAGE_FILE = "last_messages.json"
CHANNEL_NAMES_FILE = "channel_names.json"
CHANNEL_EMOJI_FILE = "channel_emoji.json"

last_message_ids = {}
channel_names = {}
channel_emojis = {}
user_client = TelegramClient(StringSession(SESSION_STRING), API_ID, API_HASH)
# ============================================
# PART 2 - FILE HANDLING & HELPER FUNCTIONS
# ============================================

def load_channels():
    global MONITORED_CHANNELS
    try:
        if os.path.exists(CHANNELS_FILE):
            with open(CHANNELS_FILE, 'r') as f:
                MONITORED_CHANNELS = json.load(f)
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

def save_channels():
    try:
        with open(CHANNELS_FILE, 'w') as f:
            json.dump(MONITORED_CHANNELS, f, indent=2)
        logger.info(f"✅ Saved {len(MONITORED_CHANNELS)} channels")
    except Exception as e:
        logger.error(f"Error saving channels: {e}")

def load_last_messages():
    global last_message_ids
    try:
        if os.path.exists(LAST_MESSAGE_FILE):
            with open(LAST_MESSAGE_FILE, 'r') as f:
                last_message_ids = json.load(f)
                logger.info(f"✅ Loaded last messages for {len(last_message_ids)} channels")
                return last_message_ids
    except Exception as e:
        logger.error(f"Error loading last messages: {e}")
    last_message_ids = {}
    return last_message_ids

def save_last_messages():
    try:
        with open(LAST_MESSAGE_FILE, 'w') as f:
            json.dump(last_message_ids, f, indent=2)
        logger.info(f"✅ Saved last messages for {len(last_message_ids)} channels")
    except Exception as e:
        logger.error(f"Error saving last messages: {e}")

async def load_channel_names():
    global channel_names
    try:
        if os.path.exists(CHANNEL_NAMES_FILE):
            with open(CHANNEL_NAMES_FILE, 'r') as f:
                channel_names = json.load(f)
                logger.info(f"✅ Loaded {len(channel_names)} channel names")
                return channel_names
    except Exception as e:
        logger.error(f"Error loading channel names: {e}")
    channel_names = {}
    return channel_names

async def save_channel_names():
    try:
        with open(CHANNEL_NAMES_FILE, 'w') as f:
            json.dump(channel_names, f, indent=2)
        logger.info(f"✅ Saved {len(channel_names)} channel names")
    except Exception as e:
        logger.error(f"Error saving channel names: {e}")

async def load_channel_emojis():
    global channel_emojis
    try:
        if os.path.exists(CHANNEL_EMOJI_FILE):
            with open(CHANNEL_EMOJI_FILE, 'r') as f:
                channel_emojis = json.load(f)
                logger.info(f"✅ Loaded {len(channel_emojis)} channel emojis")
                return channel_emojis
    except Exception as e:
        logger.error(f"Error loading channel emojis: {e}")
    channel_emojis = {}
    return channel_emojis

async def save_channel_emojis():
    try:
        with open(CHANNEL_EMOJI_FILE, 'w') as f:
            json.dump(channel_emojis, f, indent=2)
        logger.info(f"✅ Saved {len(channel_emojis)} channel emojis")
    except Exception as e:
        logger.error(f"Error saving channel emojis: {e}")

def get_channel_emoji(chat_id):
    chat_id_str = str(chat_id)
    if chat_id_str in channel_emojis:
        return channel_emojis[chat_id_str]
    
    available_emojis = [e for e in CHANNEL_EMOJIS if e not in channel_emojis.values()]
    emoji = available_emojis[0] if available_emojis else "🔴"
    channel_emojis[chat_id_str] = emoji
    asyncio.create_task(save_channel_emojis())
    return emoji

async def get_channel_name_from_telethon(chat_id):
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

def get_channel_name(chat_id):
    chat_id_str = str(chat_id)
    if chat_id_str in channel_names:
        return channel_names[chat_id_str]
    return f"Channel {abs(chat_id)}"

# ============ MEDIA DOWNLOAD & FORMATTING ============

async def download_media(message):
    try:
        os.makedirs("media_cache", exist_ok=True)

        file_path = None
        file_name = None

        if message.photo:
            file_name = f"media_cache/photo_{message.id}_{datetime.now().timestamp()}.jpg"
            file_path = await user_client.download_media(
                message.photo,
                file=file_name
            )

        elif message.video:
            file_name = f"media_cache/video_{message.id}_{datetime.now().timestamp()}.mp4"
            file_path = await user_client.download_media(
                message.video,
                file=file_name
            )

        elif message.voice:
            file_name = f"media_cache/voice_{message.id}_{datetime.now().timestamp()}.ogg"
            file_path = await user_client.download_media(
                message.voice,
                file=file_name
            )

        elif message.audio:
            file_name = f"media_cache/audio_{message.id}_{datetime.now().timestamp()}.mp3"
            file_path = await user_client.download_media(
                message.audio,
                file=file_name
            )

        elif message.sticker:
            file_name = f"media_cache/sticker_{message.id}_{datetime.now().timestamp()}.webp"
            file_path = await user_client.download_media(
                message.sticker,
                file=file_name
            )

        elif message.document:
            document_name = getattr(message.document, "file_name", None)

            if not document_name:
                document_name = f"document_{message.id}"

            file_name = (
                f"media_cache/doc_{message.id}_"
                f"{datetime.now().timestamp()}_{document_name}"
            )

            file_path = await user_client.download_media(
                message.document,
                file=file_name
            )

        return file_path, file_name

    except Exception as e:
        logger.error(
            f"Error downloading media from message "
            f"{getattr(message, 'id', 'unknown')}: {e}"
        )
        return None, None


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

            attributes = getattr(
                message.document,
                "attributes",
                []
            ) or []

            for attr in attributes:
                attr_name = attr.__class__.__name__

                if attr_name == "DocumentAttributeAnimated":
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


def get_media_emoji(message_type):
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


# ============ UPDATED FORMAT FUNCTIONS ============

def format_channel_message(chat_id, message_text, message_id, message_type="text", username=None):
    channel_name = get_channel_name(chat_id)
    emoji = get_channel_emoji(chat_id)
    timestamp = datetime.now().strftime("%d %b %Y • %I:%M %p")
    media_emoji = get_media_emoji(message_type)
    
    # Escape HTML special characters
    channel_name_escaped = html.escape(channel_name)
    
    if message_text:
        message_text = html.escape(message_text)
        # Full text bold
        message_text = f"<b>{message_text}</b>"
    
    main_content = f"""{emoji} <b>{channel_name_escaped}</b>
{media_emoji} <b>{message_type.upper()}</b>
🕒 {timestamp}"""

    if message_text:
        msg_content = f"\n━━━━━━━━━━━━━━━━━━━━\n{message_text}"
    else:
        msg_content = f"\n━━━━━━━━━━━━━━━━━━━━\n<em>📷 {message_type.upper()} message</em>"
    
    # NO expandable - direct visible
    formatted_msg = f"""<blockquote>
{main_content}{msg_content}
</blockquote>"""
    return formatted_msg


def format_combined_message(channels_data):
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
        
        # Escape HTML special characters
        channel_name_escaped = html.escape(channel_name)
        
        if message_text and message_text != '📭 No messages yet':
            message_text = html.escape(message_text)
            message_text = f"<b>{message_text}</b>"
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


def format_channel_list():
    if not MONITORED_CHANNELS:
        return "<b>📭 No channels being monitored</b>"
    
    msg = "<b>📡 MONITORED CHANNELS</b>\n\n"
    for idx, chat_id in enumerate(MONITORED_CHANNELS, 1):
        name = get_channel_name(chat_id)
        emoji = get_channel_emoji(chat_id)
        msg += f"{idx}. {emoji} <b>{html.escape(name)}</b>\n"
        msg += f"   📌 ID: <code>{chat_id}</code>\n"
    return msg


def extract_entities(text, entities):
    """Extract custom emoji and text URL entities"""
    if not entities:
        return text
    
    for entity in sorted(entities, key=lambda e: e.offset, reverse=True):
        entity_text = text[entity.offset:entity.offset + entity.length]
        
        if isinstance(entity, MessageEntityCustomEmoji):
            pass
        elif isinstance(entity, MessageEntityTextUrl):
            url = entity.url
            replacement = f'<a href="{url}">{entity_text}</a>'
            text = text[:entity.offset] + replacement + text[entity.offset + entity.length:]
    
    return text
    # ============================================
# PART 3 - CHANNEL MONITORING, COMMANDS & MAIN
# ============================================

async def process_message(message):
    try:
        chat_id = message.chat_id
        msg_id = message.id
        
        # Check if already processed
        last_id = last_message_ids.get(str(chat_id), 0)
        if msg_id <= last_id:
            return
        
        msg_type = get_message_type(message)
        
        # FIX: Use message.text only (Telethon doesn't have caption)
        msg_text = message.text or None
        
        formatted_msg = format_channel_message(chat_id, msg_text, msg_id, msg_type)
        
        sent_successfully = False
        
        # VOICE
        if message.voice:
            file_path, file_name = await download_media(message)
            if file_path and os.path.exists(file_path):
                await bot.send_voice(GROUP_CHAT_ID, FSInputFile(file_path), caption=formatted_msg, parse_mode=ParseMode.HTML)
                os.remove(file_path)
                sent_successfully = True
            else:
                await bot.send_message(GROUP_CHAT_ID, formatted_msg, parse_mode=ParseMode.HTML)
                sent_successfully = True
        
        # VIDEO
        elif message.video:
            file_path, file_name = await download_media(message)
            if file_path and os.path.exists(file_path):
                await bot.send_video(GROUP_CHAT_ID, FSInputFile(file_path), caption=formatted_msg, parse_mode=ParseMode.HTML)
                os.remove(file_path)
                sent_successfully = True
            else:
                await bot.send_message(GROUP_CHAT_ID, formatted_msg, parse_mode=ParseMode.HTML)
                sent_successfully = True
        
        # STICKER
        elif message.sticker:
            file_path, file_name = await download_media(message)
            if file_path and os.path.exists(file_path):
                await bot.send_sticker(GROUP_CHAT_ID, FSInputFile(file_path))
                await bot.send_message(GROUP_CHAT_ID, formatted_msg, parse_mode=ParseMode.HTML)
                os.remove(file_path)
                sent_successfully = True
            else:
                await bot.send_message(GROUP_CHAT_ID, formatted_msg, parse_mode=ParseMode.HTML)
                sent_successfully = True
        
        # AUDIO
        elif message.audio:
            file_path, file_name = await download_media(message)
            if file_path and os.path.exists(file_path):
                await bot.send_audio(GROUP_CHAT_ID, FSInputFile(file_path), caption=formatted_msg, parse_mode=ParseMode.HTML)
                os.remove(file_path)
                sent_successfully = True
            else:
                await bot.send_message(GROUP_CHAT_ID, formatted_msg, parse_mode=ParseMode.HTML)
                sent_successfully = True
        
        # DOCUMENT / GIF
        elif message.document:
            file_path, file_name = await download_media(message)
            if file_path and os.path.exists(file_path):
                if msg_type == "gif":
                    await bot.send_animation(GROUP_CHAT_ID, FSInputFile(file_path), caption=formatted_msg, parse_mode=ParseMode.HTML)
                else:
                    await bot.send_document(GROUP_CHAT_ID, FSInputFile(file_path), caption=formatted_msg, parse_mode=ParseMode.HTML)
                os.remove(file_path)
                sent_successfully = True
            else:
                await bot.send_message(GROUP_CHAT_ID, formatted_msg, parse_mode=ParseMode.HTML)
                sent_successfully = True
        
        # PHOTO
        elif message.photo:
            file_path, file_name = await download_media(message)
            if file_path and os.path.exists(file_path):
                await bot.send_photo(GROUP_CHAT_ID, FSInputFile(file_path), caption=formatted_msg, parse_mode=ParseMode.HTML)
                os.remove(file_path)
                sent_successfully = True
            else:
                await bot.send_message(GROUP_CHAT_ID, formatted_msg, parse_mode=ParseMode.HTML)
                sent_successfully = True
        
        # TEXT ONLY
        else:
            await bot.send_message(GROUP_CHAT_ID, formatted_msg, parse_mode=ParseMode.HTML)
            sent_successfully = True
        
        # IMPORTANT: Save ID ONLY after successful send
        if sent_successfully:
            last_message_ids[str(chat_id)] = msg_id
            save_last_messages()
            logger.info(f"📨 Sent {msg_type} from channel {chat_id}: {msg_id}")
        
    except Exception as e:
        logger.error(f"❌ Error processing message channel={getattr(message, 'chat_id', 'unknown')} message={getattr(message, 'id', 'unknown')}: {e}")
        # ID NOT saved on error - will retry on next message


async def monitor_channels():
    logger.info("🚀 Starting channel monitor...")
    
    # Dynamic handler - checks chat_id in MONITORED_CHANNELS
    @user_client.on(events.NewMessage())
    async def handler(event):
        if event.chat_id in MONITORED_CHANNELS:
            await process_message(event.message)
    
    await user_client.run_until_disconnected()


async def get_channel_last_messages(chat_id, limit=1):
    try:
        messages = []
        async for msg in user_client.iter_messages(chat_id, limit=limit):
            msg_type = get_message_type(msg)
            # FIX: Use message.text only
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


async def send_media_message(chat_id, msg_data, formatted_msg):
    """Send media message with proper caption"""
    msg = msg_data['message_obj']
    msg_type = msg_data['type']
    
    if msg.voice:
        file_path, file_name = await download_media(msg)
        if file_path and os.path.exists(file_path):
            await bot.send_voice(chat_id, FSInputFile(file_path), caption=formatted_msg, parse_mode=ParseMode.HTML)
            os.remove(file_path)
            return True
    
    elif msg.video:
        file_path, file_name = await download_media(msg)
        if file_path and os.path.exists(file_path):
            await bot.send_video(chat_id, FSInputFile(file_path), caption=formatted_msg, parse_mode=ParseMode.HTML)
            os.remove(file_path)
            return True
    
    elif msg.sticker:
        file_path, file_name = await download_media(msg)
        if file_path and os.path.exists(file_path):
            await bot.send_sticker(chat_id, FSInputFile(file_path))
            await bot.send_message(chat_id, formatted_msg, parse_mode=ParseMode.HTML)
            os.remove(file_path)
            return True
    
    elif msg.audio:
        file_path, file_name = await download_media(msg)
        if file_path and os.path.exists(file_path):
            await bot.send_audio(chat_id, FSInputFile(file_path), caption=formatted_msg, parse_mode=ParseMode.HTML)
            os.remove(file_path)
            return True
    
    elif msg.document:
        file_path, file_name = await download_media(msg)
        if file_path and os.path.exists(file_path):
            if msg_type == "gif":
                await bot.send_animation(chat_id, FSInputFile(file_path), caption=formatted_msg, parse_mode=ParseMode.HTML)
            else:
                await bot.send_document(chat_id, FSInputFile(file_path), caption=formatted_msg, parse_mode=ParseMode.HTML)
            os.remove(file_path)
            return True
    
    elif msg.photo:
        file_path, file_name = await download_media(msg)
        if file_path and os.path.exists(file_path):
            await bot.send_photo(chat_id, FSInputFile(file_path), caption=formatted_msg, parse_mode=ParseMode.HTML)
            os.remove(file_path)
            return True
    
    return False


# ============ COMMAND HANDLERS ============

@dp.message(Command("start"))
async def start_command(message: types.Message):
    """Hidden - Only admin"""
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
    """Only admin"""
    if message.from_user.id not in ADMIN_IDS:
        await message.reply("🚫")
        return
    await message.reply(format_channel_list(), parse_mode=ParseMode.HTML)


@dp.message(Command("last"))
async def last_command(message: types.Message):
    """✅ EVERYONE can use this - Get last message from ALL channels with media"""
    
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
    await status_msg.edit_text(combined_msg, parse_mode=ParseMode.HTML)
    
    # Then send each channel's media (if any)
    for chat_id_str, msg_data in channel_messages.items():
        chat_id = int(chat_id_str)
        msg_type = msg_data['type']
        
        if msg_type == 'text':
            continue
        
        msg_text = msg_data['message']
        formatted_msg = format_channel_message(
            chat_id, 
            msg_text, 
            msg_data['message_id'], 
            msg_type
        )
        
        try:
            await asyncio.sleep(0.5)
            await send_media_message(message.chat.id, msg_data, formatted_msg)
        except Exception as e:
            logger.error(f"Error sending media for channel {chat_id}: {e}")


@dp.message(Command("addchannel"))
async def add_channel_command(message: types.Message):
    """Only admin"""
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
        
        try:
            chat = await user_client.get_entity(channel_id)
            channel_name = chat.title or f"Channel {abs(channel_id)}"
            channel_names[str(channel_id)] = channel_name
            await save_channel_names()
            get_channel_emoji(channel_id)
            await save_channel_emojis()
        except Exception as e:
            channel_name = f"Channel {abs(channel_id)}"
            logger.error(f"Failed to get channel info: {e}")
        
        MONITORED_CHANNELS.append(channel_id)
        save_channels()
        last_message_ids[str(channel_id)] = 0
        save_last_messages()
        
        emoji = get_channel_emoji(channel_id)
        
        await message.reply(
            f"✅ <b>Channel Added!</b>\n\n"
            f"{emoji} <b>Name:</b> {channel_name}\n"
            f"📌 <b>ID:</b> <code>{channel_id}</code>\n\n"
            f"🔔 Now monitoring this channel for new messages.",
            parse_mode=ParseMode.HTML
        )
    except ValueError:
        await message.reply("❌ <b>Invalid channel ID.</b> Please provide a numeric ID.", parse_mode=ParseMode.HTML)
    except Exception as e:
        await message.reply(f"❌ <b>Error:</b> {e}", parse_mode=ParseMode.HTML)


@dp.message(Command("removechannel"))
async def remove_channel_command(message: types.Message):
    """Only admin"""
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
        
        if channel_id not in MONITORED_CHANNELS:
            await message.reply(f"⚠️ Channel <code>{channel_id}</code> is not being monitored.", parse_mode=ParseMode.HTML)
            return
        
        MONITORED_CHANNELS.remove(channel_id)
        save_channels()
        if str(channel_id) in last_message_ids:
            del last_message_ids[str(channel_id)]
            save_last_messages()
        
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
    await asyncio.sleep(10)
    
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
    load_channels()
    load_last_messages()
    await load_channel_names()
    await load_channel_emojis()
    
    await user_client.start()
    logger.info("✅ User client started successfully")
    
    await update_channel_names()
    
    # 🔥 CATCH-UP REMOVED - Only new messages will be forwarded
    
    logger.info("🚀 Starting Channel Monitor Bot...")
    logger.info(f"📡 Monitoring {len(MONITORED_CHANNELS)} channels")
    logger.info(f"📤 Posting to group: {GROUP_CHAT_ID}")
    
    asyncio.create_task(background_monitor())
    await dp.start_polling(bot)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n👋 Bot stopped")
    except Exception as e:
        print(f"❌ Error: {e}")
