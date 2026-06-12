import sqlite3

conn = sqlite3.connect("faculty_account.db")
cursor = conn.cursor()

print("Adding return_time column to borrow table...")

try:
    cursor.execute("""
        ALTER TABLE borrow 
        ADD COLUMN return_time TEXT
    """)
    conn.commit()
    print("SUCCESS: return_time column added!")
except Exception as e:
    print(f"ERROR: {e}")

conn.close()