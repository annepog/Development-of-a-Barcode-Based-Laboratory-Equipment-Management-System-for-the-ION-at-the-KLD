import sqlite3

def update_database():
    """Add 'Consumed' action to transactions table constraint"""
    
    conn = sqlite3.connect("faculty_account.db")
    cursor = conn.cursor()
    
    try:
        # Create backup
        cursor.execute("CREATE TABLE transactions_backup AS SELECT * FROM transactions")
        print(" Backup created")
        
        # Drop old table
        cursor.execute("DROP TABLE transactions")
        print(" Old table dropped")
        
        # Recreate with new constraint
        cursor.execute("""
            CREATE TABLE transactions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                datetime TEXT NOT NULL,
                borrower_name TEXT NOT NULL,
                borrower_email TEXT NOT NULL,
                equipment_name TEXT NOT NULL,
                barcode TEXT NOT NULL,
                action TEXT NOT NULL CHECK (action IN ('Borrowed', 'Returned', 'Consumed')),
                status TEXT NOT NULL,
                handled_by TEXT,
                remarks TEXT,
                quantity INTEGER DEFAULT 1
            )
        """)
        print(" New table created with 'Consumed' action")
        
        # Restore data
        cursor.execute("INSERT INTO transactions SELECT * FROM transactions_backup")
        print(" Data restored")
        
        # Drop backup
        cursor.execute("DROP TABLE transactions_backup")
        print(" Backup removed")
        
        conn.commit()
        print("\n Database updated successfully!")
        print("You can now use 'Consumed' action in your transactions.")
        
    except Exception as e:
        conn.rollback()
        print(f" Error: {e}")
        print("Database changes rolled back.")
    
    finally:
        conn.close()

if __name__ == "__main__":
    update_database()