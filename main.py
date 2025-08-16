import asyncio
from telethon import TelegramClient, events, Button
from telethon.sessions import StringSession
from telethon.tl.functions.messages import GetBotCallbackAnswerRequest
from openai import OpenAI

# --- Credentials ---
api_id = 7823667
api_hash = '178e54c6c8dbe5d8543fb06ead54da45'
string_session = '1BJWap1sAUBRnyrtDuwg7wwtpw0Z3Cdgro-6xfC3tUXP0EKwR1mnTCCS9c7GkwD-ZwSXM_gka0w5-oi9UngP73BplmQlYqg95fm1ZpmuPxV8qbG8KfOnDhZXM7X6dRCYILuMW2MOITwHh1gqfQqG_EcBvEozb1C1Ro8gkWeJv1LcJwbH_-DtD4CeiZQKEQfaC8h6QcHMKuqRASmWoQSqWUXOEdxLYxVsfJ1-Bamh-iunnjQk8QpHzvWhhy7wQCSCbplUhNzZ9Elrv6kC0Q2Rs1wTnSo0tK5i8cKdK89C4K1eCEVEXHDWaIWmtxnmY1GQLrsqae6LtBUJ9cAeyzJXGdqW8TMuiAzA='
bot_token = '7358660128:AAGlIGzE7_SyI0Uppaed3mnmgG3ytDbq6r0'
openai_api_key = "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"
# --- Channel IDs ---
fun_group = -1002684616105  # Fun Token Group
my_channel = -1002654246828  # Your Channel

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

async def press_correct_button_multiple_times(event, correct_option_text, presses=5):
    button_to_press = None
    for row in event.buttons:
        for button in row:
            if hasattr(button, 'text') and button.text == correct_option_text:
                button_to_press = button
                break
        if button_to_press:
            break

    if not button_to_press or not hasattr(button_to_press, 'data'):
        print("Correct option button not found or no callback data.")
        return

    callback_data = button_to_press.data

    for i in range(presses):
        try:
            await user_client(
                GetBotCallbackAnswerRequest(
                    peer=event.chat_id,
                    msg_id=event.id,
                    data=callback_data
                )
            )
            print(f"Clicked correct option {i+1}/{presses}")
        except Exception as e:
            print(f"Error clicking button: {e}")

        # Delay between 15 to 19 seconds
        await asyncio.sleep(15 + (4 * i) % 5)

@user_client.on(events.NewMessage(chats=fun_group))
async def quiz_listener(event):
    if event.buttons:  # quiz detected
        question = event.raw_text.strip()
        options = []

        # Extract button text
        for row in event.buttons:
            for button in row:
                if hasattr(button, 'text'):
                    options.append(button.text)

        print(f"📝 New Quiz: {question}")
        print(f"📌 Options: {options}")

        # Get GPT answer
        correct_answer = await get_gpt_answer(question, options)
        print(f"✅ GPT Answer: {correct_answer}")

        # Create quiz link
        quiz_link = f"https://t.me/c/{str(fun_group)[4:]}/{event.id}"

        # Styled message
        message_text = (
            f"🧠 **Quick Quiz Update!**\n\n"
            f"✨ **Correct Answer:** {correct_answer}\n\n"
            f"⚡ **Powered by CRAZY!** 😎🔥\n"
            f"**💟 FUN TOKEN 🧩**"
        )

        # Send to your channel
        await bot_client.send_message(
            my_channel,
            message_text,
            buttons=[Button.url("🧠 Solve Quiz Now", quiz_link)],
            link_preview=False
        )

        # Automatically press correct button multiple times
        await press_correct_button_multiple_times(event, correct_answer, presses=5)

async def main():
    await user_client.start()
    await bot_client.start(bot_token=bot_token)
    print("🚀 Bot is running... Watching Fun Token Group directly...")
    await asyncio.gather(user_client.run_until_disconnected(), bot_client.run_until_disconnected())

asyncio.run(main())
