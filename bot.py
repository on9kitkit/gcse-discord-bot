from database import add_xp, get_leaderboard, update_stats, get_user_stats
import time
last_used = {}
import os
import discord
from openai import OpenAI

# 🔑 Environment variables
DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# 🧠 OpenAI client
client_ai = OpenAI(api_key=OPENAI_API_KEY)

# ⚙️ Discord setup
intents = discord.Intents.default()
intents.message_content = True
client = discord.Client(intents=intents)

# 🤖 AI function

# 🤖 AI function
def ask_ai(prompt, system_prompt=None, model="gpt-5.1"):
    if system_prompt is None:
        system_prompt = """You are an expert AQA GCSE tutor AND examiner.

ALWAYS:
- Use bullet points
- Include key terms
- Give clear explanations
- Add an example
- Include exam tips
WHEN USING EQUATIONS:
- Do NOT use LaTeX (no \cdot, \sin, etc.)
- Use simple GCSE notation (e.g. F = BIL, v = fλ)
- Keep equations clean and readable in plain text
- Use standard symbols like θ instead of \theta

Keep answers concise but high quality."""

    response = client_ai.chat.completions.create(
        model=model,
        max_tokens=2000,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": prompt}
        ]
    )

    return response.choices[0].message.content


# 🎨 Embed UI
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


async def get_context(message, limit=5):
    messages = []

    async for msg in message.channel.history(limit=limit):
        if (
            msg.author != client.user
            and msg.content.strip()
            and not msg.content.startswith("!")
        ):
            messages.append(msg.content)

    messages.reverse()
    return "\n".join(messages)

async def send_embed(message, title, content, color=0x00ffcc):
    embed = create_embed(title, content, color, message)
    await message.channel.send(embed=embed)

# 💬 Discord message handler
@client.event
async def on_message(message):
    if message.author == client.user:
        return

    content = message.content

    # 📘 HELP COMMAND
    if content.startswith("!help"):
        await message.channel.send("""
🤖 **GCSE AI Bot Commands**

!ai <question> → explain anything  
!quiz <topic> → GCSE quiz  
!mark <answer> → get graded (1–9)  
!improve <text> → upgrade to Grade 9  
!bio / !phy / !eng → subject modes  
@bot → chat naturally  

🔥 Tip: Be specific for better answers!
""")
        return

    # ⏳ COOLDOWN (must stay inside function)
    user_id = message.author.id
    now = time.time()

    if user_id in last_used and now - last_used[user_id] < 3:
        await message.channel.send("⏳ Slow down bro...")
        return

    last_used[user_id] = now

    try:
        reply = None
        title = "🤖 AI Response"
        # 🧠 AI EXPLAIN
        if content.startswith("!ai"):
            question = content[4:].strip()
            if not question:
                await message.channel.send("❗ Please enter a question.")
                return

            async with message.channel.typing():
                context = await get_context(message)

                reply = ask_ai(f"""
                Recent conversation:
                {context}

                User request:
                {question}
                
                Explain clearly.
                """)

        # ❓ QUIZ
        elif content.startswith("!quiz"):
            title = "❓ Quiz Time"
            topic = content[6:].strip()
            weak_topics = get_weak_topics(message.author.id)

            memory = ""
            if weak_topics:
                weakest_topic = weak_topics[0][0]
                memory = f"This student struggles with {weakest_topic}. Focus the quiz on this topic."
            if not topic:
                await message.channel.send("❗ Please enter a topic.")
                return

            async with message.channel.typing():
                reply = ask_ai(f"""
                {memory}
                The student asked: {topic}

                Create a GCSE quiz based on their request.

                Rules:
                - Adapt to their request (e.g. MC, long questions, number of questions)
                - If unclear, default to mixed questions
                - Do not show the answers
                """)

            xp = add_xp(message.author.id, 5)
            level = xp // 100
            await message.channel.send(f"✨ +5 XP | Total: {xp} | Level: {level}")

        # 🧪 MARK
        elif content.startswith("!mark"):
            title = "📝 Exam Feedback"
            answer = content[6:].strip()
            if not answer:
                await message.channel.send("❗ Please enter an answer.")
                return

            async with message.channel.typing():
                context = await get_context(message)

                reply = ask_ai(f"""
                Recent conversation:
                {context}

                Mark this GCSE answer:
                {answer}

                - Give a grade (1–9)
                - Give an estimated mark
                - Explain why
                - Show how to improve
                Also:
                - Identify the topic this answer is about (e.g. forces, EM waves, structure in English)
                - Identify ONE weakness in the answer
                Format:
                Topic: ...
                Weakness: ...
                Grade: ...
                Feedback: ...
                """)
                lines = reply.split("\n")

                topic_line = next((l for l in lines if "Topic:" in l), None)

                if topic_line:
                    topic_name = topic_line.replace("Topic:", "").strip()

            xp = add_xp(message.author.id, 20)
            level = xp // 100
            await message.channel.send(f"✨ +20 XP | Total: {xp} | Level: {level}")

        # ✍️ IMPROVE
        elif content.startswith("!improve"):
            title = "📝 Improvement"
            text = content[9:].strip()
            if not text:
                await message.channel.send("❗ Please enter text.")
                return

            async with message.channel.typing():
                reply = ask_ai(f"Improve this to Grade 9:\n{text}")

            xp = add_xp(message.author.id, 5)
            level = xp // 100
            await message.channel.send(f"✨ +5 XP | Total: {xp} | Level: {level}")

        # 🧬 BIO
        elif content.startswith("!bio"):
            title = "🧬 Biology Help"
            update_stats(message.author.id, "bio")
            topic = content[4:].strip()

            if not topic:
                await message.channel.send("❗ Please enter a topic.")
                return

            data = get_user_stats(message.author.id)

            memory = ""
            if data:
                bio_count = data[2]
                phy_count = data[3]
                eng_count = data[4]

                weakest = min(
                    [("Biology", bio_count), ("Physics", phy_count), ("English", eng_count)],
                    key=lambda x: x[1]
                )[0]

                memory = f"This student struggles most with {weakest}. Explain more clearly and simply."

            async with message.channel.typing():
                reply = ask_ai(
                    f"{memory}\n\nExplain this topic:\n{topic}",
                    system_prompt="You are a GCSE Biology expert."
                )

        # ⚡ PHY
        elif content.startswith("!phy"):
            title = "⚡️ Physics Help"
            update_stats(message.author.id, "phy")
            topic = content[4:].strip()
            async with message.channel.typing():
                reply = ask_ai(topic, system_prompt="You are a GCSE Physics expert.")

        # 📖 ENG
        elif content.startswith("!eng"):
            title = "📚 English Help"
            update_stats(message.author.id, "eng")
            topic = content[4:].strip()
            async with message.channel.typing():
                reply = ask_ai(topic, system_prompt="You are an AQA English examiner.")

        elif content.startswith("!his"):
            title = "🦖 History Help"
            topic = content[4:].strip()
            async with message.channel.typing():
                reply = ask_ai(topic, system_prompt="You are an AQA Histroy expert.")

        # 💬 CHAT
        elif client.user in message.mentions:
            async with message.channel.typing():
                reply = ask_ai(content)

        # 🏆 LEADERBOARD
        elif content.startswith("!leaderboard"):
            top_users = get_leaderboard()

            leaderboard = "🏆 **Top Students**\n\n"
            for i, (user, xp) in enumerate(top_users):
                leaderboard += f"{i+1}. <@{user}> — {xp} XP\n"

            await message.channel.send(leaderboard)
            return

        elif content.startswith("!profile"):
            data = get_user_stats(message.author.id)

            if data is None:
                await message.channel.send("📊 No data yet. Start studying!")
                return

            total = data[1]
            bio = data[2]
            phy = data[3]
            eng = data[4]

            await message.channel.send(f"""
        📊 **Your Study Profile**

        Total answers: {total}

        🧬 Biology: {bio}
        ⚡ Physics: {phy}
        📖 English: {eng}
        """)
        else:
            return

        # 📤 SEND RESPONSE (shared logic)
        if not reply:
            return
        await send_embed(message, title, reply)

    except Exception as e:
        import traceback
        traceback.print_exc()


# 🚀 Run bot
client.run(DISCORD_TOKEN)


