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
        system_prompt = """You are an expert AQA GCSE tutor and examiner.

Give:
- Clear explanations
- Bullet points
- Examples
- Exam tips (Grade 7-9 focus)

Be precise. Avoid waffle."""

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
            reply = ask_ai(question)

            for i in range(0, len(reply), 1900):
                await message.channel.send(reply[i:i+1900])

        # ❓ QUIZ
        elif content.startswith("!quiz"):
            topic = content[6:]
            reply = ask_ai(f"Create a GCSE quiz (3 questions + answers) on: {topic}")

            for i in range(0, len(reply), 1900):
                await message.channel.send(reply[i:i+1900])

        # 🧪 MARK ANSWER
        elif content.startswith("!mark"):
            answer = content[6:]
            reply = ask_ai(
                f"Mark this GCSE answer. Give a grade (1-9), feedback, and how to improve:\n{answer}"
            )

            for i in range(0, len(reply), 1900):
                await message.channel.send(reply[i:i+1900])

        # ✍️ IMPROVE WRITING
        elif content.startswith("!improve"):
            text = content[9:]
            reply = ask_ai(
                f"Improve this to Grade 9 GCSE standard:\n{text}"
            )

            for i in range(0, len(reply), 1900):
                await message.channel.send(reply[i:i+1900])

        # 🧬 BIOLOGY MODE
        elif content.startswith("!bio"):
            topic = content[4:]
            reply = ask_ai(
                topic,
                system_prompt="You are a GCSE Biology expert. Explain clearly with examples and exam tips."
            )

            for i in range(0, len(reply), 1900):
                await message.channel.send(reply[i:i+1900])

        # ⚡ PHYSICS MODE
        elif content.startswith("!phy"):
            topic = content[4:]
            reply = ask_ai(
                topic,
                system_prompt="You are a GCSE Physics expert. Explain step-by-step with formulas and examples."
            )

            for i in range(0, len(reply), 1900):
                await message.channel.send(reply[i:i+1900])

        # 📖 ENGLISH MODE
        elif content.startswith("!eng"):
            topic = content[4:]
            reply = ask_ai(
                topic,
                system_prompt="You are an AQA English examiner. Give analysis, techniques, and Grade 9 insights."
            )

            for i in range(0, len(reply), 1900):
                await message.channel.send(reply[i:i+1900])

        # 💬 CHAT MODE (@bot)
        elif client.user in message.mentions:
            question = content
            reply = ask_ai(question)

            for i in range(0, len(reply), 1900):
                await message.channel.send(reply[i:i+1900])

    except Exception as e:
        print("ERROR:", e)


# 🚀 Run bot
client.run(DISCORD_TOKEN)




