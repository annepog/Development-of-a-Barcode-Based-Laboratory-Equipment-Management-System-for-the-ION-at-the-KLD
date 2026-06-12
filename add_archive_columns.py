"""
Database migration script to add archive functionality to equipment table
Run this script to add the necessary columns - runs automatically
"""

import sqlite3
from datetime import datetime

def add_archive_columns():
    try:
        conn = sqlite3.connect("faculty_account.db")
        cursor = conn.cursor()
        
        print("Checking equipment table structure...")
        
        # Check if columns already exist
        cursor.execute("PRAGMA table_info(equipment)")
        columns = [column[1] for column in cursor.fetchall()]
        
        changes_made = False
        
        # Add is_archived column if it doesn't exist
        if 'is_archived' not in columns:
            print("Adding 'is_archived' column...")
            cursor.execute("""
                ALTER TABLE equipment 
                ADD COLUMN is_archived INTEGER DEFAULT 0
            """)
            print(" Added 'is_archived' column")
            changes_made = True
        else:
            print(" 'is_archived' column already exists")
        
        # Add archived_date column if it doesn't exist
        if 'archived_date' not in columns:
            print("Adding 'archived_date' column...")
            cursor.execute("""
                ALTER TABLE equipment 
                ADD COLUMN archived_date TEXT
            """)
            print(" Added 'archived_date' column")
            changes_made = True
        else:
            print(" 'archived_date' column already exists")
        
        if changes_made:
            conn.commit()
            print("\n" + "="*50)
            print(" DATABASE MIGRATION COMPLETED SUCCESSFULLY!")
            print("="*50)
            print("\nArchive functionality is now available.")
            print("All existing equipment is set as active (not archived).")
        else:
            print("\n" + "="*50)
            print(" DATABASE ALREADY UP TO DATE")
            print("="*50)
            print("\nNo changes needed. Archive columns already exist.")
        
        conn.close()
        return True
        
    except sqlite3.Error as e:
        print(f"\n DATABASE ERROR: {str(e)}")
        return False
    except Exception as e:
        print(f"\n ERROR: {str(e)}")
        return False

if __name__ == "__main__":
    print("="*50)
    print("EQUIPMENT ARCHIVE MIGRATION")
    print("="*50)
    print("\nThis will add archive columns to your equipment table.")
    print("Your existing data will NOT be affected.\n")
    
    # Run automatically without asking for confirmation
    add_archive_columns()
    
    print("\n" + "="*50)
    print("You can now use the archive features!")
    print("="*50)