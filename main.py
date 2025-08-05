import asyncio
import re
from telethon import TelegramClient, events, Button
from telethon.sessions import StringSession

# --- Credentials ---
api_id = 7823667
api_hash = '178e54c6c8dbe5d8543fb06ead54da45'
string_session = '1BJWap1sAUB4q5Sp93KohDvZYIm6094k8YZ0JQtv1YbOwHQGv_d95d5MUZwbsLclJZt_OvlP5plHCy5tCAG4WueWHFazVCHxOTKe_PODdHruV6vNvQn79tEOrEH__fX6b62IpVxADIZy4LtdK0e1nedLiesgsj04W6AJEWUDUSARLzoQULNe5plMMvcpwtbLX0Rszc0jSSNE8e068nhdgJb4fCOKbNwxdRlUyr5HdnVJAu7L4HNAAHyFvgDDP7Pq8Q9u5hrRVcFXFvlPFZDFx0FofMpud8Dccxf53nrO73ZM3TwjrmkjhA7p4p7tESdb51FV9RwbvE718-C2UrJVrE8HQFLqsoMg='
bot_token = '7358660128:AAEP7rsba7zM_0JMikXVxVXAcFCxoOy0KLQ'

# --- Channel IDs ---
omer_channel = -1002840030132  # Umair Channel
fun_group = -1002684616105     # Fun Token Group
my_channel = -1002654246828    # Your Channel

# --- Clients ---
user_client = TelegramClient(StringSession(string_session), api_id, api_hash)
bot_client = TelegramClient('bot_session', api_id, api_hash)

@user_client.on(events.NewMessage(chats=omer_channel))
async def gpt_answer_handler(event):
    text = event.raw_text

    if "Our Answer (GPT):" in text:
        print("✅ GPT answer detected in Umair's message!")

        # Extract GPT Answer
        lines = text.splitlines()
        answer_line = next((line for line in lines if line.startswith("✅ Our Answer (GPT):")), None)
        correct_answer = lines[lines.index(answer_line) + 1].strip() if answer_line else "Unknown"

        print(f"🎯 Extracted Answer: {correct_answer}")

        # Find latest quiz message in Fun Token Group
        quiz_link = None
        async for message in user_client.iter_messages(fun_group, limit=20):
            if message.buttons:
                quiz_link = f"https://t.me/c/{str(fun_group)[4:]}/{message.id}"
                print(f"🔗 Quiz link found: {quiz_link}")
                break

        # Compose Styled Message
        message_text = (
            f"🧠 **Quick Quiz Update!**\n\n"
            f"✨ **Correct Answer:** {correct_answer}\n\n"
            f"⚡ *Powered by CRAZY!* 😎🔥\n"
            f"💟 FUN TOKEN 🧩"
        )

        # Send to Your Channel with Inline Button (link)
        if quiz_link:
            await bot_client.send_message(
                my_channel,
                message_text,
                buttons=[Button.url("🧠 Solve Quiz Now", quiz_link)],
                link_preview=False
            )
        else:
            # If no quiz link found, send plain message
            await bot_client.send_message(
                my_channel,
                message_text,
                link_preview=False
            )

        print("🚀 Quiz posted in your channel with styled text & button!")

async def main():
    await user_client.start()
    await bot_client.start(bot_token=bot_token)
    print("🚀 Bot is running... Watching Umair's channel...")
    await asyncio.gather(user_client.run_until_disconnected(), bot_client.run_until_disconnected())

asyncio.run(main())
