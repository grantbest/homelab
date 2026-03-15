import psycopg2
import time
import sys
import os
import json
import ollama
from pathlib import Path

# Config
DB_CONFIG = {
    "dbname": os.getenv("DB_NAME", "homelab"),
    "user": os.getenv("DB_USER", "postgres"),
    "password": os.getenv("DB_PASSWORD", "postgres"),
    "host": os.getenv("DB_HOST", "localhost"),
    "port": os.getenv("DB_PORT", "5432")
}
OLLAMA_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
MODEL = os.getenv("OLLAMA_MODEL", "llama3")

def get_context(conn):
    ctx = {}
    with conn.cursor() as cur:
        try:
            cur.execute("SELECT game_info, system_triggered, stake, result FROM bet_tracking ORDER BY created_at DESC LIMIT 5")
            ctx['recent_bets'] = cur.fetchall()
        except: ctx['recent_bets'] = []
        conn.rollback()
        
        try:
            cur.execute("SELECT name, status, description FROM betting_rules WHERE status = 'ACTIVE'")
            ctx['active_rules'] = cur.fetchall()
        except: ctx['active_rules'] = []
        conn.rollback()
    return ctx

def respond(user_msg, ctx):
    client = ollama.Client(host=OLLAMA_URL)
    system = "You are the BestFam Agent, an expert MLB Analyst. Use the provided context to answer directly."
    prompt = f"CONTEXT: {json.dumps(ctx, default=str)}\n\nUSER: {user_msg}"
    try:
        res = client.chat(model=MODEL, messages=[
            {'role': 'system', 'content': system},
            {'role': 'user', 'content': prompt}
        ])
        return res['message']['content']
    except Exception as e:
        return f"Agent error: {str(e)}"

def main():
    print("🚀 STARTING AGENT V3...")
    sys.stdout.flush()
    
    conn = psycopg2.connect(**DB_CONFIG)
    conn.autocommit = True
    
    with conn.cursor() as cur:
        cur.execute("SELECT COALESCE(MAX(message_id), 0) FROM agent_chat")
        last_id = cur.fetchone()[0]
    
    print(f"📊 Resuming from {last_id}")
    sys.stdout.flush()

    while True:
        try:
            with conn.cursor() as cur:
                cur.execute("SELECT message_id, content FROM agent_chat WHERE role='user' AND message_id > %s ORDER BY message_id ASC", (last_id,))
                rows = cur.fetchall()
                
                for m_id, content in rows:
                    print(f"💭 Thinking about: {content}")
                    sys.stdout.flush()
                    
                    ctx = get_context(conn)
                    reply = respond(content, ctx)
                    
                    cur.execute("INSERT INTO agent_chat (role, content) VALUES ('agent', %s)", (reply,))
                    print(f"✅ Replied to {m_id}")
                    sys.stdout.flush()
                    last_id = m_id
            
            # Heartbeat
            # print(".", end="")
            # sys.stdout.flush()
            
        except Exception as e:
            print(f"ERR: {str(e)}")
            sys.stdout.flush()
            time.sleep(5)
            try:
                conn = psycopg2.connect(**DB_CONFIG)
                conn.autocommit = True
            except: pass
            
        time.sleep(2)

if __name__ == "__main__":
    main()
