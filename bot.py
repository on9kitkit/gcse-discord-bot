import discord
import os
import time
from openai import OpenAI

# =========================
# ENV VARIABLES
# =========================
DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

if not DISCORD_TOKEN:
    raise ValueError("❌ DISCORD_TOKEN missing")

if not OPENAI_API_KEY:
    raise ValueError("❌ OPENAI_API_KEY missing")

print("✅ Keys loaded")

# =========================
# CLIENTS
# =========================
client_ai = OpenAI(api_key=OPENAI_API_KEY)

intents = discord.Intents.default()
intents.message_content = True
client = discord.Client(intents=intents)

# cooldown
last_used = {}

# =========================
# AI FUNCTION (SAFE)
# =========================
def ask_ai(prompt):
    try:
        response = client_ai.responses.create(
            model="gpt-4o-mini",
            input=prompt,
            max_output_tokens=500
        )

        return response.output_text or "⚠️ Empty AI response."

    except Exception as e:
        print("AI ERROR:", e)
        return "❌ AI failed. Check logs."

# =========================
# EMBED
# =========================
def create_embed(title, text, message):
    embed = discord.Embed(
        title=title,
        description=text[:4000],
        color=0x00ffcc
    )
    embed.set_footer(text=f"Requested by {message.author.name}")
    return embed

async def send_embed(message, title, text):
    await message.channel.send(embed=create_embed(title, text, message))

# =========================
# EVENTS
# =========================
@client.event
async def on_ready():
    print(f"✅ Logged in as {client.user}")

@client.event
async def on_message(message):
    if message.author == client.user:
        return

    content = message.content.strip()

    # HELP
    if content.startswith("!help"):
        await message.channel.send("""
🤖 GCSE Bot

!ai <question>
!quiz <topic>
!mark <answer>
""")
        return

    # COOLDOWN
    user_id = message.author.id
    now = time.time()

    if user_id in last_used and now - last_used[user_id] < 2:
        await message.channel.send("⏳ Slow down...")
        return

    last_used[user_id] = now

    try:
        reply = None
        title = "🤖 AI Response"

        # =========================
        # AI
        # =========================
        if content.startswith("!ai"):
            question = content[4:].strip()

            if not question:
                await message.channel.send("❗ Enter a question.")
                return

            async with message.channel.typing():
                reply = ask_ai(f"""
You are a GCSE tutor.

Explain clearly using:
- bullet points
- key terms
- simple examples

Question:
{question}
""")

        # =========================
        # QUIZ
        # =========================
        elif content.startswith("!quiz"):
            title = "❓ Quiz Time"
            topic = content[6:].strip()

            if not topic:
                await message.channel.send("❗ Enter a topic.")
                return

            async with message.channel.typing():
                reply = ask_ai(f"""
Create a GCSE quiz.

Topic: {topic}

Rules:
- Mix of 1–6 mark questions
- Exam-style questions
- NO answers included
""")

        # =========================
        # MARK
        # =========================
        elif content.startswith("!mark"):
            title = "📝 Feedback"
            answer = content[6:].strip()

            if not answer:
                await message.channel.send("❗ Enter an answer.")
                return

            async with message.channel.typing():
                reply = ask_ai(f"""
Mark this GCSE answer:

{answer}

Give:
- Grade (1–9)
- Feedback
- How to improve
""")

        else:
            return

        # SEND
        if not reply:
            reply = "⚠️ No response."

        print("DEBUG:", reply[:100])
        await send_embed(message, title, reply)

    except Exception as e:
        import traceback
        traceback.print_exc()

# =========================
# RUN
# =========================
client.run(DISCORD_TOKEN)
