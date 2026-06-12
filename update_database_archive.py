# update_database_archive.py - Run this ONCE to add is_archived column
import sqlite3

def update_database():
    """Add is_archived column to user_profiles table"""
    try:
        conn = sqlite3.connect("faculty_account.db")
        cursor = conn.cursor()
        
        # Check if is_archived column already exists
        cursor.execute("PRAGMA table_info(user_profiles)")
        columns = [column[1] for column in cursor.fetchall()]
        
        if 'is_archived' not in columns:
            print("Adding is_archived column to user_profiles table...")
            cursor.execute("ALTER TABLE user_profiles ADD COLUMN is_archived INTEGER DEFAULT 0")
            conn.commit()
            print("SUCCESS: is_archived column added!")
            print("Note: All existing users are set to is_archived = 0 (active)")
        else:
            print("INFO: is_archived column already exists. No changes needed.")
        
        # Verify the column
        cursor.execute("SELECT COUNT(*) FROM user_profiles WHERE is_archived = 0")
        active_count = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM user_profiles WHERE is_archived = 1")
        archived_count = cursor.fetchone()[0]
        
        print("\nCurrent Status:")
        print("- Active users: {}".format(active_count))
        print("- Archived users: {}".format(archived_count))
        
        conn.close()
        print("\nDatabase update complete!")
        
    except Exception as e:
        print("ERROR: Failed to update database - {}".format(str(e)))

if __name__ == "__main__":
    print("=== Database Archive Feature Update ===\n")
    update_database()
    print("\n=== Update Complete ===")
    print("\nYou can now run usermanagement.py to use the archive feature!")