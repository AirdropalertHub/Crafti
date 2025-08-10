import asyncio
import nest_asyncio
from telethon import TelegramClient, events, Button
from telethon.sessions import StringSession
from openai import OpenAI
from flask import Flask
from threading import Thread

# --- Flask Webserver (Keep Alive) ---
app = Flask('')

@app.route('/')
def home():
    return "Bot is Running!"

def run():
    app.run(host='0.0.0.0', port=8080)

def keep_alive():
    t = Thread(target=run)
    t.start()

# --- Credentials ---
api_id = 7823667
api_hash = '178e54c6c8dbe5d8543fb06ead54da45'
string_session = '1BJWap1sAUB4q5Sp93KohDvZYIm6094k8YZ0JQtv1YbOwHQGv_d95d5MUZwbsLclJZt_OvlP5plHCy5tCAG4WueWHFazVCHxOTKe_PODdHruV6vNvQn79tEOrEH__fX6b62IpVxADIZy4LtdK0e1nedLiesgsj04W6AJEWUDUSARLzoQULNe5plMMvcpwtbLX0Rszc0jSSNE8e068nhdgJb4fCOKbNwxdRlUyr5HdnVJAu7L4HNAAHyFvgDDP7Pq8Q9u5hrRVcFXFvlPFZDFx0FofMpud8Dccxf53nrO73ZM3TwjrmkjhA7p4p7tESdb51FV9RwbvE718-C2UrJVrE8HQFLqsoMg='
bot_token = '7358660128:AAGlIGzE7_SyI0Uppaed3mnmgG3ytDbq6r0'

# --- Channel IDs ---
fun_group = -1002684616105  # Fun Token Group
my_channel = -1002654246828 # Your Channel

# --- Clients ---
user_client = TelegramClient(StringSession(string_session), api_id, api_hash)
bot_client = TelegramClient('bot_session', api_id, api_hash)

# --- OpenAI Client ---
gpt_client = OpenAI(api_key=openai_api_key)

async def get_gpt_answer(question, options):
    """Send quiz to GPT and return best matching option."""
    try:
        prompt = (
            f"Question: {question}\n"
            "Options:\n" + "\n".join(f"- {opt}" for opt in options) +
            "\nChoose the correct option exactly as it appears."
        )

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

@user_client.on(events.NewMessage(chats=fun_group))
async def quiz_listener(event):
    if event.buttons:  # quiz detected
        question = event.raw_text.strip()
        options = []

        for row in event.buttons:
            for button in row:
                if hasattr(button, 'text'):
                    options.append(button.text)

        print(f"📝 New Quiz: {question}")
        print(f"📌 Options: {options}")

        correct_answer = await get_gpt_answer(question, options)
        print(f"✅ GPT Answer: {correct_answer}")

        quiz_link = f"https://t.me/c/{str(fun_group)[4:]}/{event.id}"

        message_text = (
            f"🧠 **Quick Quiz Update!**\n\n"
            f"✨ **Correct Answer:** {correct_answer}\n\n"
            f"⚡ **Powered by CRAZY!** 😎🔥\n"
            f"**💟 FUN TOKEN 🧩**"
        )

        await bot_client.send_message(
            my_channel,
            message_text,
            buttons=[Button.url("🧠 Solve Quiz Now", quiz_link)],
            link_preview=False
        )

async def main():
    await user_client.start()
    await bot_client.start(bot_token=bot_token)
    print("🚀 Bot is running... Watching Fun Token Group directly...")
    await asyncio.gather(user_client.run_until_disconnected(), bot_client.run_until_disconnected())

# --- Replit Fix ---
nest_asyncio.apply()
keep_alive()
asyncio.get_event_loop().run_until_complete(main())
