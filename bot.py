import discord
from openai import OpenAI

# 🔑 PUT YOUR KEYS HERE
DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# 🧠 OpenAI client
client_ai = OpenAI(api_key=OPENAI_API_KEY)

# ⚙️ Discord setup
intents = discord.Intents.default()
intents.message_content = True
client = discord.Client(intents=intents)

# 🤖 AI function
def ask_ai(prompt):
    response = client_ai.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {
                "role": "system",
                "content": "You are an expert AQA GCSE tutor. Give accurate, exam-focused answers. Be clear, structured, and helpful for students aiming for Grade 7-9."
            },
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
        # AI explanation
        if message.content.startswith("!ai"):
            question = message.content[4:]
            reply = ask_ai(question)

            # Split long messages
            for i in range(0, len(reply), 1900):
                await message.channel.send(reply[i:i+1900])

        # Quiz command
        if message.content.startswith("!quiz"):
            topic = message.content[6:]
            reply = ask_ai(f"Create a GCSE-level quiz with 3 questions on: {topic}")

            for i in range(0, len(reply), 1900):
                await message.channel.send(reply[i:i+1900])

    except Exception as e:
        print("ERROR:", e)


# 🚀 Run bot
client.run(DISCORD_TOKEN)




