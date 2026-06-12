# remove_contacts.py
import sqlite3
import os

def remove_contact_numbers():
    """Remove contact_number column from user_profiles table - NO CONFIRMATIONS"""
    
    print(" Removing contact numbers from database...")
    
    try:
        # Connect to database
        conn = sqlite3.connect("faculty_account.db")
        cursor = conn.cursor()
        
        # Check if contact_number column exists
        cursor.execute("PRAGMA table_info(user_profiles)")
        columns = [column[1] for column in cursor.fetchall()]
        
        if 'contact_number' not in columns:
            print(" contact_number column already removed!")
            conn.close()
            return True
        
        print(" Current columns in user_profiles:", columns)
        
        # Create backup
        backup_file = "faculty_account_backup.db"
        if not os.path.exists(backup_file):
            print(" Creating database backup...")
            backup_conn = sqlite3.connect(backup_file)
            conn.backup(backup_conn)
            backup_conn.close()
            print(" Backup created: faculty_account_backup.db")
        
        # Step 1: Create new table without contact_number
        print(" Creating new table structure...")
        cursor.execute("""
            CREATE TABLE user_profiles_new (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                full_name TEXT NOT NULL,
                employee_id TEXT UNIQUE NOT NULL,
                department TEXT NOT NULL,
                position TEXT NOT NULL,
                account_status TEXT NOT NULL DEFAULT 'Active',
                return_compliance_status TEXT NOT NULL DEFAULT 'Good Standing',
                is_archived INTEGER DEFAULT 0,
                FOREIGN KEY (user_id) REFERENCES users (id)
            )
        """)
        
        # Step 2: Copy data excluding contact_number
        print(" Copying data to new table...")
        cursor.execute("""
            INSERT INTO user_profiles_new 
            (id, user_id, full_name, employee_id, department, position, 
             account_status, return_compliance_status, is_archived)
            SELECT 
                id, user_id, full_name, employee_id, department, position,
                account_status, return_compliance_status, is_archived
            FROM user_profiles
        """)
        
        # Step 3: Drop old table
        print(" Removing old table...")
        cursor.execute("DROP TABLE user_profiles")
        
        # Step 4: Rename new table
        print(" Renaming new table...")
        cursor.execute("ALTER TABLE user_profiles_new RENAME TO user_profiles")
        
        # Step 5: Verify the changes
        cursor.execute("PRAGMA table_info(user_profiles)")
        new_columns = [column[1] for column in cursor.fetchall()]
        print(" New columns in user_profiles:", new_columns)
        
        # Count records to verify data integrity
        cursor.execute("SELECT COUNT(*) FROM user_profiles")
        count = cursor.fetchone()[0]
        print(f" Data verification: {count} records migrated successfully")
        
        conn.commit()
        conn.close()
        
        print(" SUCCESS: contact_number column completely removed!")
        
        return True
        
    except Exception as e:
        print(f" ERROR: {str(e)}")
        if 'conn' in locals():
            conn.rollback()
            conn.close()
        return False

if __name__ == "__main__":
    # Check if database exists
    if not os.path.exists("faculty_account.db"):
        print(" Database file not found!")
        exit()
    
    # Perform removal immediately
    remove_contact_numbers()