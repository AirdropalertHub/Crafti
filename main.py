import asyncio
import json
import os
import logging
from datetime import datetime
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.enums import ParseMode
from aiogram.types import FSInputFile
import aiohttp
import aiofiles
import tempfile

# Telethon imports
from telethon import TelegramClient, events
from telethon.sessions import StringSession

# Logging setup
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

# ============ CONFIGURATION ============
BOT_TOKEN = "8916402393:AAHXSC98Od-FyP9174D3uqgJkLZlX8H16AQ"
GROUP_CHAT_ID = -5460865745  # Your group where messages will be posted

# Your user account session string (from telethon)
SESSION_STRING = "1BJWap1sAULh18SeSR-v7gM3lEGMsI23Lrv0PktasVxLkZWR_75cIBtyRONJ9AWf8AfUdAtKs3tR30lFAkpKx3zd5d9mGtJ5yvkjOEKxRiiGoVxilM2BXsUCcmsKZpTh3h_L4drVRpeAjhmvKjhYjURW2CmEzW6G2KY8MqWPPRHI2mXjimrYEhRnpKeAxG0b7U8Sd_4ZMLlk-SRTktixnn3Rimcrjvx5m3I9jQRzV20n4YLS3Nznpg6hW9XLI9uYvYw-u4uCvgTMxZNp90nOckCLpb5Ca3tNkYehuZaevLsZXAsBlVEwln7rTEAOaHrKcXbL48FKUGK8WZDTe5PG6k8D1gEwWZsk="  # Replace with your session string
API_ID = 34408702  # Replace with your API ID
API_HASH = "0d483149e1395cafd85e509d0b6978c3"  # Replace with your API Hash

# Bot initialize
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

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

# Colorful emojis for channels
CHANNEL_EMOJIS = [
    "🔴", "🟠", "🟡", "🟢", "🔵", "🟣", 
    "⚫", "⚪", "🩵", "🩷", "🤍", "🖤", 
    "💜", "💙", "💚", "💛", "🧡", "⬜", 
    "🔶", "☑️", "🆕", "🟤", "🔴", "🟣"
]

# File to save channels
CHANNELS_FILE = "monitored_channels.json"
LAST_MESSAGE_FILE = "last_messages.json"
CHANNEL_NAMES_FILE = "channel_names.json"
CHANNEL_EMOJI_FILE = "channel_emoji.json"

# Store last message IDs per channel
last_message_ids = {}
channel_names = {}
channel_emojis = {}
# ============ SESSION & FILE HANDLING ============
# Create client with session string
user_client = TelegramClient(StringSession(SESSION_STRING), API_ID, API_HASH)

def load_channels():
    """Load monitored channels from file"""
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
    """Save monitored channels to file"""
    try:
        with open(CHANNELS_FILE, 'w') as f:
            json.dump(MONITORED_CHANNELS, f, indent=2)
        logger.info(f"✅ Saved {len(MONITORED_CHANNELS)} channels")
    except Exception as e:
        logger.error(f"Error saving channels: {e}")

def load_last_messages():
    """Load last message IDs from file"""
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
    """Save last message IDs to file"""
    try:
        with open(LAST_MESSAGE_FILE, 'w') as f:
            json.dump(last_message_ids, f, indent=2)
        logger.info(f"✅ Saved last messages for {len(last_message_ids)} channels")
    except Exception as e:
        logger.error(f"Error saving last messages: {e}")

async def load_channel_names():
    """Load channel names from file"""
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
    """Save channel names to file"""
    try:
        with open(CHANNEL_NAMES_FILE, 'w') as f:
            json.dump(channel_names, f, indent=2)
        logger.info(f"✅ Saved {len(channel_names)} channel names")
    except Exception as e:
        logger.error(f"Error saving channel names: {e}")

async def load_channel_emojis():
    """Load channel emojis from file"""
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
    """Save channel emojis to file"""
    try:
        with open(CHANNEL_EMOJI_FILE, 'w') as f:
            json.dump(channel_emojis, f, indent=2)
        logger.info(f"✅ Saved {len(channel_emojis)} channel emojis")
    except Exception as e:
        logger.error(f"Error saving channel emojis: {e}")

def get_channel_emoji(chat_id):
    """Get emoji for channel"""
    chat_id_str = str(chat_id)
    if chat_id_str in channel_emojis:
        return channel_emojis[chat_id_str]
    
    # Assign new emoji
    available_emojis = [e for e in CHANNEL_EMOJIS if e not in channel_emojis.values()]
    if available_emojis:
        emoji = available_emojis[0]
    else:
        emoji = "🔴"
    
    channel_emojis[chat_id_str] = emoji
    asyncio.create_task(save_channel_emojis())
    return emoji

async def get_channel_name_from_telethon(chat_id):
    """Get channel name using Telethon"""
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
    """Update all channel names"""
    for chat_id in MONITORED_CHANNELS:
        try:
            name = await get_channel_name_from_telethon(chat_id)
            channel_names[str(chat_id)] = name
            logger.info(f"📛 Channel {chat_id}: {name}")
            # Assign emoji
            get_channel_emoji(chat_id)
        except Exception as e:
            logger.error(f"Failed to get name for {chat_id}: {e}")
    
    await save_channel_names()
    await save_channel_emojis()

def get_channel_name(chat_id):
    """Get channel name from cache"""
    chat_id_str = str(chat_id)
    if chat_id_str in channel_names:
        return channel_names[chat_id_str]
    return f"Channel {abs(chat_id)}"
    # ============ MEDIA DOWNLOAD & FORMATTING ============
async def download_media(message):
    """Download media from message and return file path"""
    try:
        os.makedirs('media_cache', exist_ok=True)
        
        file_path = None
        file_name = None
        
        if message.photo:
            photo = message.photo[-1]
            file_name = f"media_cache/photo_{message.id}_{datetime.now().timestamp()}.jpg"
            file_path = await user_client.download_media(photo, file=file_name)
            
        elif message.document:
            file_name = f"media_cache/doc_{message.id}_{datetime.now().timestamp()}_{message.document.file_name or 'document'}"
            file_path = await user_client.download_media(message.document, file=file_name)
            
        elif message.voice:
            file_name = f"media_cache/voice_{message.id}_{datetime.now().timestamp()}.ogg"
            file_path = await user_client.download_media(message.voice, file=file_name)
            
        elif message.video:
            file_name = f"media_cache/video_{message.id}_{datetime.now().timestamp()}.mp4"
            file_path = await user_client.download_media(message.video, file=file_name)
            
        elif message.audio:
            file_name = f"media_cache/audio_{message.id}_{datetime.now().timestamp()}.mp3"
            file_path = await user_client.download_media(message.audio, file=file_name)
            
        elif message.sticker:
            file_name = f"media_cache/sticker_{message.id}_{datetime.now().timestamp()}.webp"
            file_path = await user_client.download_media(message.sticker, file=file_name)
            
        elif message.animation:
            file_name = f"media_cache/gif_{message.id}_{datetime.now().timestamp()}.mp4"
            file_path = await user_client.download_media(message.animation, file=file_name)
            
        return file_path, file_name
        
    except Exception as e:
        logger.error(f"Error downloading media: {e}")
        return None, None

def get_message_type(message):
    """Get the type of message"""
    if message.voice:
        return "voice"
    elif message.photo:
        return "photo"
    elif message.video:
        return "video"
    elif message.document:
        return "document"
    elif message.sticker:
        return "sticker"
    elif message.animation:
        return "gif"
    elif message.audio:
        return "audio"
    elif message.text:
        return "text"
    else:
        return "unknown"

def get_media_emoji(message_type):
    """Get emoji for media type"""
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

def format_channel_message(chat_id, message_text, message_id, message_type="text", username=None):
    """Format message with channel name, emoji and timestamp - COLLAPSIBLE"""
    channel_name = get_channel_name(chat_id)
    emoji = get_channel_emoji(chat_id)
    timestamp = datetime.now().strftime("%d %b %Y • %I:%M %p")
    media_emoji = get_media_emoji(message_type)
    
    if message_text and len(message_text) > 1000:
        message_text = message_text[:997] + "..."
    
    # Main content (collapsible)
    main_content = f"""{emoji} <b>{channel_name}</b>
{media_emoji} <b>{message_type.upper()}</b>
🕒 {timestamp}"""

    # Message content
    if message_text:
        msg_content = f"\n━━━━━━━━━━━━━━━━━━━━\n{message_text}"
    else:
        msg_content = f"\n━━━━━━━━━━━━━━━━━━━━\n<em>📷 {message_type.upper()} message</em>"
    
    # 🔥 COLLAPSIBLE BLOCKQUOTE
    formatted_msg = f"""<blockquote expandable>
<b>{main_content}{msg_content}</b>
</blockquote>"""
    
    return formatted_msg

def format_combined_message(channels_data):
    """Format combined message from all channels - COLLAPSIBLE"""
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
        message = data.get('message', 'No message')
        
        msg += f"""<blockquote expandable>
<b>{emoji} {channel_name}</b>
{media_emoji} {msg_type.upper()}
━━━━━━━━━━━━━━━━━━━━
{message}
</blockquote>
"""
    
    return msg

def format_channel_list():
    """Format list of monitored channels with emojis"""
    if not MONITORED_CHANNELS:
        return "<b>📭 No channels being monitored</b>"
    
    msg = "<b>📡 MONITORED CHANNELS</b>\n\n"
    for idx, chat_id in enumerate(MONITORED_CHANNELS, 1):
        name = get_channel_name(chat_id)
        emoji = get_channel_emoji(chat_id)
        msg += f"{idx}. {emoji} <b>{name}</b>\n"
        msg += f"   📌 ID: <code>{chat_id}</code>\n"
    
    return msg
    # ============ CHANNEL MONITORING ============
async def process_message(message):
    """Process a message from monitored channel"""
    try:
        chat_id = message.chat_id
        msg_id = message.id
        
        # Check if already processed
        last_id = last_message_ids.get(str(chat_id), 0)
        if msg_id <= last_id:
            return
        
        # Update last message ID
        last_message_ids[str(chat_id)] = msg_id
        save_last_messages()
        
        # Get message type and text
        msg_type = get_message_type(message)
        msg_text = message.text or message.caption or None
        
        # Format message
        formatted_msg = format_channel_message(
            chat_id,
            msg_text,
            msg_id,
            msg_type
        )
        
        # Send based on media type
        if message.voice:
            file_path, file_name = await download_media(message)
            if file_path and os.path.exists(file_path):
                await bot.send_voice(
                    GROUP_CHAT_ID,
                    FSInputFile(file_path),
                    caption=formatted_msg,
                    parse_mode=ParseMode.HTML
                )
                os.remove(file_path)
            else:
                await bot.send_message(GROUP_CHAT_ID, formatted_msg, parse_mode=ParseMode.HTML)
                
        elif message.photo:
            file_path, file_name = await download_media(message)
            if file_path and os.path.exists(file_path):
                await bot.send_photo(
                    GROUP_CHAT_ID,
                    FSInputFile(file_path),
                    caption=formatted_msg,
                    parse_mode=ParseMode.HTML
                )
                os.remove(file_path)
            else:
                await bot.send_message(GROUP_CHAT_ID, formatted_msg, parse_mode=ParseMode.HTML)
                
        elif message.video:
            file_path, file_name = await download_media(message)
            if file_path and os.path.exists(file_path):
                await bot.send_video(
                    GROUP_CHAT_ID,
                    FSInputFile(file_path),
                    caption=formatted_msg,
                    parse_mode=ParseMode.HTML
                )
                os.remove(file_path)
            else:
                await bot.send_message(GROUP_CHAT_ID, formatted_msg, parse_mode=ParseMode.HTML)
                
        elif message.document:
            file_path, file_name = await download_media(message)
            if file_path and os.path.exists(file_path):
                await bot.send_document(
                    GROUP_CHAT_ID,
                    FSInputFile(file_path),
                    caption=formatted_msg,
                    parse_mode=ParseMode.HTML
                )
                os.remove(file_path)
            else:
                await bot.send_message(GROUP_CHAT_ID, formatted_msg, parse_mode=ParseMode.HTML)
                
        elif message.sticker:
            file_path, file_name = await download_media(message)
            if file_path and os.path.exists(file_path):
                await bot.send_sticker(GROUP_CHAT_ID, FSInputFile(file_path))
                await bot.send_message(GROUP_CHAT_ID, formatted_msg, parse_mode=ParseMode.HTML)
                os.remove(file_path)
            else:
                await bot.send_message(GROUP_CHAT_ID, formatted_msg, parse_mode=ParseMode.HTML)
                
        elif message.animation:
            file_path, file_name = await download_media(message)
            if file_path and os.path.exists(file_path):
                await bot.send_animation(
                    GROUP_CHAT_ID,
                    FSInputFile(file_path),
                    caption=formatted_msg,
                    parse_mode=ParseMode.HTML
                )
                os.remove(file_path)
            else:
                await bot.send_message(GROUP_CHAT_ID, formatted_msg, parse_mode=ParseMode.HTML)
                
        else:
            await bot.send_message(GROUP_CHAT_ID, formatted_msg, parse_mode=ParseMode.HTML)
        
        logger.info(f"📨 Sent {msg_type} from channel {chat_id}: {msg_id}")
        
    except Exception as e:
        logger.error(f"Error processing message: {e}")

async def monitor_channels():
    """Monitor all channels for new messages"""
    logger.info("🚀 Starting channel monitor...")
    
    @user_client.on(events.NewMessage(chats=MONITORED_CHANNELS))
    async def handler(event):
        await process_message(event.message)
    
    await user_client.run_until_disconnected()

async def get_channel_last_messages(chat_id, limit=2):
    """Get last N messages from a specific channel"""
    try:
        messages = []
        async for msg in user_client.iter_messages(chat_id, limit=limit):
            msg_type = get_message_type(msg)
            msg_text = msg.text or msg.caption or f"📷 {msg_type.upper()} message"
            
            messages.append({
                'message_id': msg.id,
                'message': msg_text,
                'type': msg_type,
                'date': msg.date
            })
        return messages
    except Exception as e:
        logger.error(f"Error getting messages from {chat_id}: {e}")
        return []

async def get_all_channels_last_messages(limit=2):
    """Get last N messages from all monitored channels"""
    result = {}
    for chat_id in MONITORED_CHANNELS:
        messages = await get_channel_last_messages(chat_id, limit)
        if messages:
            result[str(chat_id)] = messages
    return result
    # ============ COMMAND HANDLERS ============

@dp.message(Command("start"))
async def start_command(message: types.Message):
    """Start command - show bot info"""
    await message.reply(
        f"""<blockquote>
<b>🤖 Channel Monitor Bot</b>

✅ <b>Bot is online</b>
📡 Monitoring <b>{len(MONITORED_CHANNELS)}</b> channels
🎙️ Voice messages supported
📸 Media messages supported

<b>📋 Commands:</b>
/channels - <b>List monitored channels</b>
/last - <b>Get last 2 messages from all channels</b>
/addchannel - <b>Add channel to monitor</b>
/removechannel - <b>Remove channel from monitoring</b>

<i>New messages from monitored channels are automatically posted here.</i>
</blockquote>""",
        parse_mode=ParseMode.HTML
    )

@dp.message(Command("channels"))
async def channels_command(message: types.Message):
    """List all monitored channels"""
    if message.chat.id != GROUP_CHAT_ID and message.from_user.id not in [8497620413]:
        await message.reply("❌ This command is only available in the main group.")
        return
    
    await message.reply(format_channel_list(), parse_mode=ParseMode.HTML)

@dp.message(Command("addchannel"))
async def add_channel_command(message: types.Message):
    """Add a channel to monitor"""
    if message.chat.id != GROUP_CHAT_ID and message.from_user.id not in [8497620413]:
        await message.reply("❌ This command is only available in the main group.")
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
    """Remove a channel from monitoring"""
    if message.chat.id != GROUP_CHAT_ID and message.from_user.id not in [8497620413]:
        await message.reply("❌ This command is only available in the main group.")
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

@dp.message(Command("last"))
async def last_command(message: types.Message):
    """Get last 2 messages from all channels"""
    if message.chat.id != GROUP_CHAT_ID and message.from_user.id not in [8497620413]:
        await message.reply("❌ This command is only available in the main group.")
        return
    
    status_msg = await message.reply("🔄 <b>Fetching messages...</b>", parse_mode=ParseMode.HTML)
    
    messages_data = await get_all_channels_last_messages(limit=2)
    
    if not messages_data:
        await status_msg.edit_text("📭 <b>No messages found in any channel.</b>", parse_mode=ParseMode.HTML)
        return
    
    # Send each channel's messages
    for chat_id, messages in messages_data.items():
        channel_id = int(chat_id)
        emoji = get_channel_emoji(channel_id)
        channel_name = get_channel_name(channel_id)
        
        for msg in messages:
            msg_type = msg.get('type', 'text')
            media_emoji = get_media_emoji(msg_type)
            timestamp = msg['date'].strftime('%d %b %Y • %I:%M %p')
            
            if msg_type != 'text':
                formatted_msg = f"""<blockquote expandable>
<b>{emoji} {channel_name}</b>
{media_emoji} {msg_type.upper()}
🕒 {timestamp}
━━━━━━━━━━━━━━━━━━━━
<em>📷 {msg_type.upper()} message</em>
</blockquote>"""
            else:
                formatted_msg = f"""<blockquote expandable>
<b>{emoji} {channel_name}</b>
📝 TEXT
🕒 {timestamp}
━━━━━━━━━━━━━━━━━━━━
{msg['message']}
</blockquote>"""
            
            await message.reply(formatted_msg, parse_mode=ParseMode.HTML)
            await asyncio.sleep(0.5)
    
    await status_msg.delete()
    # ============ BACKGROUND TASK ============
async def background_monitor():
    """Background task to monitor channels"""
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
    """Main entry point"""
    load_channels()
    load_last_messages()
    await load_channel_names()
    await load_channel_emojis()
    
    # Start user client
    await user_client.start()
    logger.info("✅ User client started successfully")
    
    # Update channel names and emojis
    await update_channel_names()
    
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