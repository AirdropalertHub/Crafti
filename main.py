from telethon import TelegramClient, events
import requests
import os
import asyncio

# Telegram API credentials
api_id = 7823667
api_hash = '178e54c6c8dbe5d8543fb06ead54da45'
bot_token = '7575884578:AAF7wSq4d7SIX0AHgYj9uJPG4vhue2J8GTk'

# Create client
bot = TelegramClient('tiktok_bot', api_id, api_hash)

async def main():
    await bot.start(bot_token=bot_token)
    print("Bot is running...")

    @bot.on(events.NewMessage(pattern='/start'))
    async def start(event):
        await event.respond("Hi! Send me a TikTok link and I'll download the video for you.")

    @bot.on(events.NewMessage)
    async def download_tiktok(event):
        url = event.message.message.strip()
        
        if "tiktok.com" not in url:
            await event.respond("Please send a valid TikTok URL.")
            return

        await event.respond("Processing your request... ⏳")

        api_url = f"https://tikwm.com/api/?url={requests.utils.quote(url)}"
        headers = {"user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}

        try:
            response = requests.get(api_url, headers=headers).json()
            if response.get("code") == 0:
                video_url = response["data"]["play"]
                video_data = requests.get(video_url).content

                file_name = f"tiktok_{event.message.id}.mp4"
                with open(file_name, "wb") as f:
                    f.write(video_data)

                await event.respond(file=file_name)
                os.remove(file_name)
            else:
                await event.respond("Failed to fetch video. Please check the TikTok link.")
        except Exception as e:
            await event.respond(f"An error occurred: {e}")

    await bot.run_until_disconnected()

# Run the bot
asyncio.run(main())
