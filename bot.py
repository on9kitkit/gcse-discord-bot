import time
last_used = {}
import os
import discord
from openai import OpenAI
user_xp = {}

#XP system
def add_xp(user_id, amount):
    if user_id not in user_xp:
        user_xp[user_id] = 0

    user_xp[user_id] += amount
    return user_xp[user_id]

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
    user_id = message.author.id
    now = time.time()

    if user_id in last_used and now - last_used[user_id] < 3:
        await message.channel.send("⏳ Slow down bro...")
        return

    last_used[user_id] = now
    if message.author == client.user:
        return

    try:
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

        # 🧠 AI EXPLAIN
        elif content.startswith("!ai"):
            question = content[4:]
            if not question.strip():
                await message.channel.send("❗ Please enter a question.")
                return
            async with message.channel.typing():
                reply = ask_ai(question)

            for i in range(0, len(reply), 1900):
                await message.channel.send(reply[i:i+1900])

        # ❓ QUIZ
        elif content.startswith("!quiz"):
            topic = content[6:]
            async with message.channel.typing():
                reply = ask_ai(f"Create a GCSE quiz (3 questions + answers) on: {topic}")
            xp = add_xp(message.author.id, 5)
            level = xp // 100
            await message.channel.send(f"✨ +5 XP | Total: {xp} | Level: {level}")

            for i in range(0, len(reply), 1900):
                await message.channel.send(reply[i:i+1900])

        # 🧪 MARK ANSWER
        elif content.startswith("!mark"):
            answer = content[6:]
            async with message.channel.typing():
                reply = ask_ai(f"Mark this GCSE answer. Give a grade (1-9), feedback, and how to improve:\n{answer}")
            xp = add_xp(message.author.id, 20)
            level = xp // 100
            await message.channel.send(f"✨ +20 XP | Total: {xp} | Level: {level}")

            for i in range(0, len(reply), 1900):
                await message.channel.send(reply[i:i+1900])

        # ✍️ IMPROVE WRITING
        elif content.startswith("!improve"):
            text = content[9:]
            async with message.channel.typing():
                reply = ask_ai(f"Improve this to Grade 9 GCSE standard:\n{text}")
            xp = add_xp(message.author.id, 15)
            level = xp // 100
            await message.channel.send(f"✨ +15 XP | Total: {xp}")

            for i in range(0, len(reply), 1900):
                await message.channel.send(reply[i:i+1900])

        # 🧬 BIOLOGY MODE
        elif content.startswith("!bio"):
            topic = content[4:]
            async with message.channel.typing():
                reply = ask_ai(topic,
                system_prompt="You are a GCSE Biology expert. Explain clearly with examples and exam tips."
            )

            for i in range(0, len(reply), 1900):
                await message.channel.send(reply[i:i+1900])

        # ⚡ PHYSICS MODE
        elif content.startswith("!phy"):
            topic = content[4:]
            async with message.channel.typing():
                reply = ask_ai( topic,
                system_prompt="You are a GCSE Physics expert. Explain step-by-step with formulas and examples.")

            for i in range(0, len(reply), 1900):
                await message.channel.send(reply[i:i+1900])

        # 📖 ENGLISH MODE
        elif content.startswith("!eng"):
            topic = content[4:]
            async with message.channel.typing():
                reply = ask_ai(topic,
                system_prompt="You are an AQA English examiner. Give analysis, techniques, and Grade 9 insights.")

            for i in range(0, len(reply), 1900):
                await message.channel.send(reply[i:i+1900])

        # 💬 CHAT MODE (@bot)
        elif client.user in message.mentions:
            question = content
            reply = ask_ai(question)

            for i in range(0, len(reply), 1900):
                await message.channel.send(reply[i:i+1900])

        elif content.startswith("!leaderboard"):
            sorted_users = sorted(user_xp.items(), key=lambda x: x[1], reverse=True)

            leaderboard = "🏆 **Leaderboard**\n"
            for i, (user, xp) in enumerate(sorted_users[:5]):
                leaderboard += f"{i+1}. <@{user}> — {xp} XP\n"

            await message.channel.send(leaderboard)

    except Exception as e:
        print("ERROR:", e)


# 🚀 Run bot
client.run(DISCORD_TOKEN)


