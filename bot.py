from database import add_xp, get_leaderboard, update_stats, get_user_stats, get_weak_topics, update_topic
import time
import os
import discord
from openai import OpenAI

# ⏱️ cooldown
last_used = {}

# 🔑 ENV
DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

if not DISCORD_TOKEN:
    raise ValueError("❌ DISCORD_TOKEN missing")

if not OPENAI_API_KEY:
    raise ValueError("❌ OPENAI_API_KEY missing")

print("✅ API KEY LOADED:", OPENAI_API_KEY[:10])

# 🧠 OpenAI client
client_ai = OpenAI(api_key=OPENAI_API_KEY)

# ⚙️ Discord setup
intents = discord.Intents.default()
intents.message_content = True
client = discord.Client(intents=intents)

# 🤖 AI FUNCTION
def ask_ai(prompt, system_prompt=None, model="gpt-4o-mini"):
    if system_prompt is None:
        system_prompt = r"""You are an expert AQA GCSE tutor...

ALWAYS:
- Use bullet points
- Include key terms
- Give clear explanations
- Add an example
- Include exam tips
"""

    response = client_ai.responses.create(
        model=model,
        input=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": prompt}
        ],
        max_output_tokens=2000
    )

    try:
        return response.output[0].content[0].text
    except:
        print("RAW RESPONSE:", response)
        return None

# 🎨 EMBED
def create_embed(title, description, color, message):
    embed = discord.Embed(
        title=title,
        description=description[:4000],
        color=color
    )

    embed.set_footer(text=f"Requested by {message.author.name}")

    if message.author.avatar:
        embed.set_thumbnail(url=message.author.avatar.url)

    return embed


async def send_embed(message, title, content):
    embed = create_embed(title, content, 0x00ffcc, message)
    await message.channel.send(embed=embed)


# 💬 MESSAGE HANDLER
@client.event
async def on_message(message):
    if message.author == client.user:
        return

    content = message.content.strip()

    # HELP
    if content.startswith("!help"):
        await message.channel.send("""
🤖 **GCSE AI Bot**

!ai <question>
!quiz <topic>
!mark <answer>
!improve <text>
!bio / !phy / !eng
""")
        return

    # ⏳ cooldown
    user_id = message.author.id
    now = time.time()

    if user_id in last_used and now - last_used[user_id] < 2:
        await message.channel.send("⏳ Slow down...")
        return

    last_used[user_id] = now

    try:
        reply = None
        title = "🤖 AI Response"

        # 🧠 AI
        if content.startswith("!ai"):
            question = content[4:].strip()
            if not question:
                await message.channel.send("❗ Enter a question.")
                return

            async with message.channel.typing():
                reply = ask_ai(question)

        # ❓ QUIZ
        elif content.startswith("!quiz"):
            title = "❓ Quiz Time"
            topic = content[6:].strip()

            if not topic:
                await message.channel.send("❗ Enter a topic.")
                return

            weak_topics = get_weak_topics(user_id)

            memory = ""
            if weak_topics and ("weak" in topic.lower() or "improve" in topic.lower()):
                memory = f"Focus on weak topic: {weak_topics[0][0]}"

            async with message.channel.typing():
                reply = ask_ai(f"""
{memory}

Create a GCSE quiz.

User request: {topic}

Rules:
- Mix question types (1–6 markers)
- Include exam-style questions
- DO NOT include answers
""")

            xp = add_xp(user_id, 5)
            await message.channel.send(f"✨ +5 XP | Total: {xp}")

        # 🧪 MARK
        elif content.startswith("!mark"):
            title = "📝 Feedback"
            answer = content[6:].strip()

            if not answer:
                await message.channel.send("❗ Enter answer.")
                return

            async with message.channel.typing():
                reply = ask_ai(f"""
Mark this GCSE answer:

{answer}

Give:
- Grade (1–9)
- Feedback
- Topic
- Weakness

Format:
Topic: ...
Weakness: ...
Grade: ...
Feedback: ...
""")

                # store weak topic
                for line in reply.split("\n"):
                    if line.lower().startswith("topic:"):
                        topic_name = line.split(":")[-1].strip()
                        update_topic(user_id, topic_name)

            xp = add_xp(user_id, 20)
            await message.channel.send(f"✨ +20 XP | Total: {xp}")

        # ✍️ IMPROVE
        elif content.startswith("!improve"):
            title = "📝 Improved"
            text = content[9:].strip()

            async with message.channel.typing():
                reply = ask_ai(f"Improve this to Grade 9:\n{text}")

        # SUBJECT MODES
        elif content.startswith("!bio"):
            topic = content[4:].strip()
            async with message.channel.typing():
                reply = ask_ai(topic, "You are a GCSE Biology expert.")

        elif content.startswith("!phy"):
            topic = content[4:].strip()
            async with message.channel.typing():
                reply = ask_ai(topic, "You are a GCSE Physics expert.")

        elif content.startswith("!eng"):
            topic = content[4:].strip()
            async with message.channel.typing():
                reply = ask_ai(topic, "You are an AQA English examiner.")

        # 🏆 leaderboard
        elif content.startswith("!leaderboard"):
            data = get_leaderboard()
            text = "🏆 Top Students\n\n"

            for i, (user, xp) in enumerate(data):
                text += f"{i+1}. <@{user}> — {xp} XP\n"

            await message.channel.send(text)
            return

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


# 🚀 RUN
client.run(DISCORD_TOKEN)
