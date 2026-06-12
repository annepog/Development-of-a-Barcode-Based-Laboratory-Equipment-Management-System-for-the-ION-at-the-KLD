# database_setup.py
import sqlite3

def setup_notification_system():
    """Setup notification system - adds to your existing database"""
    conn = sqlite3.connect("faculty_account.db")
    cursor = conn.cursor()
    
    # The notifications table already exists in your schema, so we just verify it
    cursor.execute("""
        SELECT name FROM sqlite_master 
        WHERE type='table' AND name='notifications'
    """)
    
    if cursor.fetchone():
        print(" Notifications table already exists!")
    else:
        # Create if it doesn't exist (fallback)
        cursor.execute("""
            CREATE TABLE notifications (
                notification_id INTEGER PRIMARY KEY AUTOINCREMENT,
                recipient_email TEXT NOT NULL,
                message TEXT NOT NULL,
                notification_type TEXT NOT NULL,
                related_id INTEGER,
                created_at TEXT NOT NULL,
                is_read INTEGER NOT NULL DEFAULT 0,
                FOREIGN KEY (recipient_email) REFERENCES users(email)
            )
        """)
        print(" Notifications table created!")
    
    conn.commit()
    conn.close()
    print(" Notification system ready!")

if __name__ == "__main__":
    setup_notification_system()