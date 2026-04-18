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
def ask_ai(user_id, prompt):
    try:
        response = client_ai.responses.create(
            model="gpt-5.4",
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

        # ensure quiz continues only in same channel
        if message.channel.id != session["channel_id"]:
            return

        current_q = session["questions"][session["current"]]

        async with message.channel.typing():
            feedback = ask_ai(user_id, f"""
Question:
{current_q}

Student answer:
{content}

Mark this answer.

Give:
- Score: x/1
- Brief feedback

Be strict like an examiner.
""")

        await send_embed(message, "📝 Feedback", feedback)
        # extract score
        for line in feedback.split("\n"):
            if "score" in line.lower():
                try:
                    score = int(line.split(":")[1].split("/")[0].strip())
                    session["score"] += score
                except:
                    pass
        session["current"] += 1

        if session["current"] >= len(session["questions"]):
            del quiz_sessions[user_id]
            score = session["score"]
            total = session["total"]

            await message.channel.send(
                f"🎉 Quiz complete!\n\nScore: {score}/{total}"
            )
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
                reply = ask_ai(user_id, f"""
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
                quiz_text = ask_ai(user_id, f"""
                Create a GCSE quiz.

                Topic: {topic}

                Rules:
                - EXACTLY 5 questions
                - Format EXACTLY like this:

                Q1: ...
                Q2: ...
                Q3: ...
                Q4: ...
                Q5: ...

                - Do NOT include answers
                - No extra text
                """)

            # split into questions
            # improved parsing (robust)
            lines = quiz_text.split("\n")
            questions = []
            current_q = ""

            for line in lines:
                line = line.strip()

                # detect new question (more flexible)
                if line.lower().startswith("q"):
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
                "topic": topic,
                "channel_id": message.channel.id,
                "score": 0,
                "total": len(questions)
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
                reply = ask_ai(user_id, f"""
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

        elif content.startswith("!eng"):
            title = "📖 English Help"
            topic = content[4:].strip()
            async with message.channel.typing():
                reply = ask_ai(user_id, f"""
You are an AQA GCSE English Language examiner.

Explain clearly using:
- terminology (e.g. structure, language devices)
- short examples
- exam-style advice

Topic:
{topic}
""")

        elif content.startswith("!lit"):
            title = "📚 Literature Help"
            topic = content[4:].strip()
            async with message.channel.typing():
                reply = ask_ai(user_id, f"""
You are an AQA GCSE English Literature examiner.

Explain with:
- key quotes
- analysis (AO1, AO2 style)
- context if relevant

Topic:
{topic}
""")

        elif content.startswith("!phy"):
            title = "⚡ Physics Help"
            topic = content[4:].strip()
            async with message.channel.typing():
                reply = ask_ai(user_id, f"""
You are a GCSE Physics expert.

Explain using:
- bullet points
- equations (plain text)
- real-world examples

Topic:
{topic}
""")

        elif content.startswith("!chem"):
            title = "🧪 Chemistry Help"
            topic = content[5:].strip()
            async with message.channel.typing():
                reply = ask_ai(user_id, f"""
You are a GCSE Chemistry expert.

Explain using:
- key terms
- equations (plain text)
- step-by-step processes

Topic:
{topic}
""")

        elif content.startswith("!bio"):
            title = "🧬 Biology Help"
            topic = content[4:].strip()
            async with message.channel.typing():
                reply = ask_ai(user_id, f"""
You are a GCSE Biology expert.

Explain using:
- key terminology
- processes clearly
- examples

Topic:
{topic}
""")

        elif content.startswith("!math"):
            title = "➗ Maths Help"
            topic = content[5:].strip()
            async with message.channel.typing():
                reply = ask_ai(user_id, f"""
You are a GCSE Maths tutor.

Explain step-by-step:
- show working
- explain each step
- keep it simple

Question:
{topic}
""")

        elif content.startswith("!his"):
            title = "🏛️ History Help"
            topic = content[4:].strip()
            async with message.channel.typing():
                reply = ask_ai(user_id, f"""
You are an AQA GCSE History examiner.

Explain using:
- key events
- causes and consequences
- clear timeline

Topic:
{topic}
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
