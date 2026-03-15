import discord
import os
import psycopg2
import asyncio

# Configuration from Environment Variables
DISCORD_BOT_TOKEN = os.getenv("DISCORD_BOT_TOKEN")
# The ID of the channel you want the bot to listen to
ALLOWED_CHANNEL_ID = int(os.getenv("DISCORD_CHANNEL_ID", 0))
DB_URL = os.getenv("DATABASE_URL", "postgresql://postgres:postgres@localhost:5432/homelab")

intents = discord.Intents.default()
intents.message_content = True

client = discord.Client(intents=intents)

async def check_for_agent_replies(channel):
    print("Started background polling for agent replies...")
    last_processed_id = 0
    
    try:
        conn = psycopg2.connect(DB_URL)
        cur = conn.cursor()
        cur.execute("SELECT MAX(message_id) FROM agent_chat")
        last_processed_id = cur.fetchone()[0] or 0
        cur.close()
        conn.close()
    except Exception as e:
        print(f"DB Init Error: {e}")

    while True:
        try:
            conn = psycopg2.connect(DB_URL)
            cur = conn.cursor()
            cur.execute("SELECT message_id, content FROM agent_chat WHERE role = %s AND message_id > %s ORDER BY message_id ASC", ("agent", last_processed_id))
            new_msgs = cur.fetchall()
            
            for m_id, content in new_msgs:
                await channel.send(f"🤖 **BestFam Agent:**\n{content}")
                last_processed_id = m_id
                
            cur.close()
            conn.close()
        except Exception as e:
            pass
            
        await asyncio.sleep(3)

@client.event
async def on_ready():
    print(f"✅ Logged in as {client.user}")
    
    if ALLOWED_CHANNEL_ID != 0:
        channel = client.get_channel(ALLOWED_CHANNEL_ID)
        if channel:
            print(f"Listening to channel: {channel.name}")
            client.loop.create_task(check_for_agent_replies(channel))
        else:
            print("⚠️ WARNING: Could not find the specified Discord Channel ID.")

@client.event
async def on_message(message):
    if message.author == client.user:
        return

    if ALLOWED_CHANNEL_ID != 0 and message.channel.id != ALLOWED_CHANNEL_ID:
        return

    print(f"Discord Input: {message.content}")

    try:
        conn = psycopg2.connect(DB_URL)
        cur = conn.cursor()
        cur.execute("INSERT INTO agent_chat (role, content) VALUES (%s, %s)", ("user", message.content))
        conn.commit()
        cur.close()
        conn.close()
        
        await message.add_reaction("✅")
        
    except Exception as e:
        print(f"Database error: {e}")
        await message.add_reaction("❌")

if __name__ == "__main__":
    if not DISCORD_BOT_TOKEN:
        print("❌ ERROR: DISCORD_BOT_TOKEN environment variable is not set.")
    else:
        client.run(DISCORD_BOT_TOKEN)
