# update_database_variant.py - Run this ONCE to add variant field
import sqlite3

def update_database():
    """Add variant field to equipment table"""
    try:
        conn = sqlite3.connect("faculty_account.db")
        cursor = conn.cursor()
        
        # Check if variant column already exists
        cursor.execute("PRAGMA table_info(equipment)")
        columns = [column[1] for column in cursor.fetchall()]
        
        if 'variant' not in columns:
            print("Adding variant column to equipment table...")
            cursor.execute("ALTER TABLE equipment ADD COLUMN variant TEXT")
            conn.commit()
            print("SUCCESS: variant column added!")
            print("Note: All existing equipment have variant = NULL (no variant)")
        else:
            print("INFO: variant column already exists. No changes needed.")
        
        # Show some examples
        print("\nExample usage:")
        print("- Test Tubes (5ml)")
        print("- Test Tubes (10ml)")
        print("- Beakers (250ml)")
        print("- Gloves (Small)")
        print("- Gloves (Medium)")
        print("- Gloves (Large)")
        
        conn.close()
        print("\nDatabase update complete!")
        
    except Exception as e:
        print("ERROR: Failed to update database - {}".format(str(e)))

if __name__ == "__main__":
    print("=== Database Variant Field Update ===\n")
    update_database()
    print("\n=== Update Complete ===")
    print("\nYou can now add size/variant information when creating equipment!")