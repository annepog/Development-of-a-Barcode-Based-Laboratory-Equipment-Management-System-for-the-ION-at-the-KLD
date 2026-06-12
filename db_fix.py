# db_fix.py
import sqlite3

# Enable WAL mode on the database
conn = sqlite3.connect("faculty_account.db")
conn.execute("PRAGMA journal_mode=WAL")
conn.execute("PRAGMA synchronous=NORMAL") 
conn.execute("PRAGMA busy_timeout=5000")  # Wait 5 seconds if locked
conn.close()
print("Database fixed for concurrent access!")