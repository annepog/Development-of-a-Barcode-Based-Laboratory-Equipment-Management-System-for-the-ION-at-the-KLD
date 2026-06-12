# database_migration_violation.py
import sqlite3

def add_violation_sent_column():
    """Add violation_sent column to equipment_issues table"""
    conn = sqlite3.connect("faculty_account.db")
    cursor = conn.cursor()
    
    try:
        # Check if column already exists
        cursor.execute("PRAGMA table_info(equipment_issues)")
        columns = [column[1] for column in cursor.fetchall()]
        
        if 'violation_sent' in columns:
            print("Column 'violation_sent' already exists in equipment_issues table!")
        else:
            # Add the column
            cursor.execute("""
                ALTER TABLE equipment_issues 
                ADD COLUMN violation_sent INTEGER DEFAULT 0
            """)
            conn.commit()
            print("Successfully added 'violation_sent' column to equipment_issues table!")
            
    except sqlite3.Error as e:
        print(f"Error adding column: {e}")
    finally:
        conn.close()

def verify_database_structure():
    """Verify all required tables and columns exist"""
    conn = sqlite3.connect("faculty_account.db")
    cursor = conn.cursor()
    
    print("\n=== Database Structure Verification ===\n")
    
    # Check equipment_issues table
    cursor.execute("PRAGMA table_info(equipment_issues)")
    columns = cursor.fetchall()
    
    print("equipment_issues table columns:")
    for column in columns:
        print(f"  - {column[1]} ({column[2]})")
    
    print("\n" + "="*40 + "\n")
    
    # Check if notifications table exists
    cursor.execute("""
        SELECT name FROM sqlite_master 
        WHERE type='table' AND name='notifications'
    """)
    
    if cursor.fetchone():
        print("notifications table: EXISTS")
        cursor.execute("PRAGMA table_info(notifications)")
        notif_columns = cursor.fetchall()
        print("notifications table columns:")
        for column in notif_columns:
            print(f"  - {column[1]} ({column[2]})")
    else:
        print("notifications table: NOT FOUND")
        print("Creating notifications table...")
        cursor.execute("""
            CREATE TABLE notifications (
                notification_id INTEGER PRIMARY KEY AUTOINCREMENT,
                recipient_email TEXT NOT NULL,
                message TEXT NOT NULL,
                notification_type TEXT NOT NULL,
                related_id INTEGER,
                created_at TEXT NOT NULL,
                is_read INTEGER NOT NULL DEFAULT 0
            )
        """)
        conn.commit()
        print("notifications table created successfully!")
    
    conn.close()
    print("\n=== Verification Complete ===\n")

if __name__ == "__main__":
    print("Starting database migration...\n")
    add_violation_sent_column()
    print("\nVerifying database structure...\n")
    verify_database_structure()
    print("Migration complete!")