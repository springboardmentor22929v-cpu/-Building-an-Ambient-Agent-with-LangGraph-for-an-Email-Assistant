import sqlite3

# Connect to the memory database
conn = sqlite3.connect("agent_memory.sqlite")
cursor = conn.cursor()

# Query all rows from the user_preferences table
try:
    cursor.execute("SELECT key, value FROM user_preferences")
    rows = cursor.fetchall()
    
    print("\n🔍 SQLite Memory Viewer")
    print("=======================")
    if not rows:
        print("📭 Database is empty.")
    else:
        for row in rows:
            print(f"🔑 Key: {row[0]} | 💾 Value: {row[1]}")
            
except sqlite3.OperationalError:
    print("❌ Could not find table 'user_preferences'. Is the DB initialized?")

conn.close()
