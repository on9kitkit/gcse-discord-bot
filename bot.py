import discord
import os
import time
from openai import OpenAI
from database import add_xp, update_topic
print("🚀 VERSION 1.0 CLEAN BUILD")

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
quiz_sessions = {}

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

        print("FULL RESPONSE:", response)

        # SAFE extraction
        if hasattr(response, "output_text") and response.output_text:
            return response.output_text

        # fallback (VERY IMPORTANT)
        if response.output and len(response.output) > 0:
            for item in response.output:
                if hasattr(item, "content"):
                    for content in item.content:
                        if hasattr(content, "text"):
                            return content.text

        return "⚠️ AI returned no readable text."

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
    # =========================
    # QUIZ ANSWERING (PRIORITY)
    # =========================
    if user_id in quiz_sessions:
        session = quiz_sessions[user_id]

        current_q = session["questions"][session["current"]]

        async with message.channel.typing():
            feedback = ask_ai(f"""
Question:
{current_q}

Student answer:
{content}

Mark this answer briefly and give feedback.
""")

        await send_embed(message, "📝 Feedback", feedback)

        session["current"] += 1

        if session["current"] >= len(session["questions"]):
            del quiz_sessions[user_id]
            await message.channel.send("🎉 Quiz complete!")
        else:
            next_q = session["questions"][session["current"]]
            await send_embed(message, "➡️ Next Question", next_q)

        return

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
                quiz_text = ask_ai(f"""
        Create a GCSE quiz.

        Topic: {topic}

        Rules:
        - 5 questions
        - Mix of difficulty (1–6 markers)
        - Do NOT include answers
        - Number them clearly (Q1, Q2, ...)
        """)

            # split into questions
            # improved parsing (robust)
            lines = quiz_text.split("\n")
            questions = []
            current_q = ""

            for line in lines:
                line = line.strip()

                if line.lower().startswith("q") and ":" in line:
                    if current_q:
                        questions.append(current_q.strip())
                    current_q = line
                else:
                    current_q += "\n" + line

            if current_q:
                questions.append(current_q.strip())

            quiz_sessions[user_id] = {
                "questions": questions,
                "current": 0,
                "topic": topic
            }

            await send_embed(message, "❓ Quiz Started", questions[0])
            xp = add_xp(user_id, 5)
            await message.channel.send(f"✨ +5 XP | Total: {xp}")
            return
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

Also include:
Topic: ...
""")
            # extract topic from AI response
            topic_name = None
            for line in reply.split("\n"):
                if line.lower().startswith("topic:"):
                    topic_name = line.split(":")[-1].strip()

            if topic_name:
                update_topic(user_id, topic_name)
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
