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
def ask_ai(prompt, system_prompt=None):
    if system_prompt is None:
        system_prompt = """You are an expert AQA GCSE tutor AND examiner.

ALWAYS:
- Use bullet points
- Include key terms (important for marks)
- Give clear explanations
- Add an example when possible
- Include exam tips (how to get Grade 7-9)

IF marking:
- Give a grade (1-9)
- Explain WHY
- Show how to improve to next grade

Keep answers concise but high quality. No waffle."""

    response = client_ai.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": prompt}
        ]
    )
    return response.choices[0].message.content


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
        # 🧠 AI EXPLAIN
        if content.startswith("!ai"):
            question = content[4:]
            if not question.strip():
                await message.channel.send("❗ Please enter a question.")
                return

            async with message.channel.typing():
                reply = ask_ai(question)

        # ❓ QUIZ
        elif content.startswith("!quiz"):
            topic = content[6:]
            if not topic.strip():
                await message.channel.send("❗ Please enter a topic.")
                return

            async with message.channel.typing():
                reply = ask_ai(f"Create a GCSE quiz (3 questions + answers) on: {topic}")

            xp = add_xp(message.author.id, 5)
            level = xp // 100
            await message.channel.send(f"✨ +5 XP | Total: {xp} | Level: {level}")

        # 🧪 MARK
        elif content.startswith("!mark"):
            answer = content[6:]
            if not answer.strip():
                await message.channel.send("❗ Please enter an answer.")
                return

            async with message.channel.typing():
                reply = ask_ai(f"Mark this GCSE answer:\n{answer}")

            xp = add_xp(message.author.id, 20)
            level = xp // 100
            await message.channel.send(f"✨ +20 XP | Total: {xp} | Level: {level}")

        # ✍️ IMPROVE
        elif content.startswith("!improve"):
            text = content[9:]
            if not text.strip():
                await message.channel.send("❗ Please enter text.")
                return

            async with message.channel.typing():
                reply = ask_ai(f"Improve this to Grade 9:\n{text}")

            xp = add_xp(message.author.id, 15)
            level = xp // 100
            await message.channel.send(f"✨ +15 XP | Total: {xp} | Level: {level}")

        # 🧬 BIO
        elif content.startswith("!bio"):
            update_stats(message.author.id, "bio")
            topic = content[4:]
            async with message.channel.typing():
                data = get_user_stats(message.author.id)

                memory = ""
                if data:
                bio_count = data[2]
                phy_count = data[3]
                eng_count = data[4]

    # detect weakest subject
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
            update_stats(message.author.id, "phy")
            topic = content[4:]
            async with message.channel.typing():
                reply = ask_ai(topic, system_prompt="You are a GCSE Physics expert.")

        # 📖 ENG
        elif content.startswith("!eng"):
            update_stats(message.author.id, "eng")
            topic = content[4:]
            async with message.channel.typing():
                reply = ask_ai(topic, system_prompt="You are an AQA English examiner.")

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
            cursor.execute("SELECT * FROM user_stats WHERE user_id=?", (message.author.id,))
            data = cursor.fetchone()

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
        for i in range(0, len(reply), 1900):
            await message.channel.send(reply[i:i+1900])

    except Exception as e:
        import traceback
        traceback.print_exc()


# 🚀 Run bot
client.run(DISCORD_TOKEN)


