import asyncio
import json
import os
import threading
from flask import Flask
from telethon import TelegramClient, events, Button
from telethon.sessions import StringSession
from telethon.tl.functions.messages import GetBotCallbackAnswerRequest
from openai import OpenAI

# --- BOT CONFIG ---


# --- Flask App for Replit Keepalive ---
app = Flask(__name__)

@app.route('/')
def home():
    return "🤖 Bot is running 24/7 with Flask + Telethon!"

def run_flask():
    app.run(host="0.0.0.0", port=8080)

# --- Load / Save Users ---
def load_users():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r") as f:
            return json.load(f)
    return {}

def save_users(users):
    with open(DATA_FILE, "w") as f:
        json.dump(users, f, indent=2)

users = load_users()

# --- OpenAI Client ---
gpt_client = OpenAI(api_key=OPENAI_KEY)

# --- BOT CLIENT ---
bot = TelegramClient("bot_session", 7823667, "178e54c6c8dbe5d8543fb06ead54da45")

# --- User Clients ---
user_clients = {}

async def get_gpt_answer(question, options):
    try:
        prompt = f"Question: {question}\nOptions:\n" + "\n".join(f"- {o}" for o in options)
        response = gpt_client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "You are a quiz solver. Reply only with the correct option text."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=50
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        return f"Error: {e}"

async def press_correct(event, correct_text, client):
    for row in event.buttons:
        for button in row:
            if getattr(button, "text", "") == correct_text:
                try:
                    await client(GetBotCallbackAnswerRequest(
                        peer=event.chat_id,
                        msg_id=event.id,
                        data=button.data
                    ))
                    print("✅ Button clicked")
                except Exception as e:
                    print("Click error:", e)
                return

# --- User Client Setup ---
async def setup_user_client(uid, api_id, api_hash, string_session):
    if uid in user_clients:  # prevent duplicate
        return

    client = TelegramClient(StringSession(string_session), int(api_id), api_hash)
    await client.start()
    user_clients[uid] = client

    @client.on(events.NewMessage(chats=FUN_GROUP))
    async def quiz_handler(ev):
        if ev.buttons:
            q = ev.raw_text.strip()
            opts = [b.text for row in ev.buttons for b in row if hasattr(b, "text")]
            ans = await get_gpt_answer(q, opts)
            await press_correct(ev, ans, client)

            # ✅ Single clean message
            quiz_link = f"https://t.me/c/{str(FUN_GROUP)[4:]}/{ev.id}"
            msg = (
                f"**🧠 Correct Answer:** {ans}\n\n"
                f"**⚡ Powered by CRAZY! 😎🔥**\n"
                f"**💟 FUN TOKEN 🧩**"
            )
            await bot.send_message(
                MY_CHANNEL,
                msg,
                buttons=[Button.url("🧠 Solve Quiz Now", quiz_link)]
            )

# --- Bot Commands ---
@bot.on(events.NewMessage(pattern="/start"))
async def start_cmd(event):
    await event.reply("👋 Apna `api_id`, `api_hash`, aur `string_session` bhejo is format me:\n\n"
                      "`api_id|api_hash|string_session`")

@bot.on(events.NewMessage(pattern="/check"))
async def check_users(event):
    total = len(users)
    await event.reply(f"👥 Total users connected: **{total}**")

@bot.on(events.NewMessage)
async def collect_user(event):
    if "|" in event.raw_text:
        try:
            api_id, api_hash, string_session = event.raw_text.split("|")
            uid = int(event.sender_id)

            # remove duplicate if already exists
            users[str(uid)] = {"api_id": int(api_id), "api_hash": api_hash, "string": string_session}
            save_users(users)

            await setup_user_client(uid, int(api_id), api_hash, string_session)

            await event.reply("✅ Tumhara account add ho gaya! Ab tumhara client Fun Token group me quiz solve karega.")

        except Exception as e:
            await event.reply(f"❌ Error: {e}")

# --- Auto reconnect users on startup ---
async def reconnect_all_users():
    for uid, data in users.items():
        try:
            await setup_user_client(int(uid), data["api_id"], data["api_hash"], data["string"])
            print(f"♻️ Reconnected user {uid}")
        except Exception as e:
            print(f"Reconnect error {uid}:", e)

async def main():
    await bot.start(bot_token=BOT_TOKEN)
    await reconnect_all_users()
    print("🚀 Bot started and waiting for users...")
    await bot.run_until_disconnected()

# --- Start both Flask & Bot ---
if __name__ == "__main__":
    threading.Thread(target=run_flask).start()  # Flask server in background
    asyncio.run(main())
