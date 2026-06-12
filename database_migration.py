import sqlite3
import datetime

def migrate_database():
    """Add replacement tracking columns to equipment_issues table"""
    try:
        conn = sqlite3.connect("faculty_account.db")
        cursor = conn.cursor()
        
        # Check if columns already exist
        cursor.execute("PRAGMA table_info(equipment_issues)")
        columns = [column[1] for column in cursor.fetchall()]
        
        # Add new columns if they don't exist
        if 'replacement_required' not in columns:
            cursor.execute("""
                ALTER TABLE equipment_issues 
                ADD COLUMN replacement_required INTEGER DEFAULT 0
            """)
            print(" Added column: replacement_required")
        
        if 'replacement_status' not in columns:
            cursor.execute("""
                ALTER TABLE equipment_issues 
                ADD COLUMN replacement_status TEXT DEFAULT 'Pending'
            """)
            print(" Added column: replacement_status")
        
        if 'replacement_deadline' not in columns:
            cursor.execute("""
                ALTER TABLE equipment_issues 
                ADD COLUMN replacement_deadline TEXT
            """)
            print(" Added column: replacement_deadline")
        
        if 'replacement_equipment_id' not in columns:
            cursor.execute("""
                ALTER TABLE equipment_issues 
                ADD COLUMN replacement_equipment_id INTEGER
            """)
            print(" Added column: replacement_equipment_id")
        
        if 'estimated_cost' not in columns:
            cursor.execute("""
                ALTER TABLE equipment_issues 
                ADD COLUMN estimated_cost REAL
            """)
            print(" Added column: estimated_cost")
        
        conn.commit()
        conn.close()
        
        print("\n Database migration completed successfully!")
        print("All replacement tracking columns have been added to equipment_issues table.")
        
    except Exception as e:
        print(f" Error during migration: {str(e)}")

if __name__ == "__main__":
    print("Starting database migration...")
    print("Adding replacement tracking columns to equipment_issues table...\n")
    migrate_database()