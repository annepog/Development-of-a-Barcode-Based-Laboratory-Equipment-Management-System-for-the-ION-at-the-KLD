# fix_borrower_tracking.py
import sqlite3
import os
import shutil
import datetime

def fix_borrower_tracking():
    """Fix the borrower tracking issues in the database"""
    
    db_path = "faculty_account.db"
    
    if not os.path.exists(db_path):
        print(f"ERROR: Database file '{db_path}' not found!")
        return False
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        print("Starting borrower tracking fix...")
        
        # Step 1: Check current borrow table structure
        print("\nChecking current borrow table structure...")
        cursor.execute("PRAGMA table_info(borrow)")
        current_columns = [column[1] for column in cursor.fetchall()]
        print(f"Current columns: {current_columns}")
        
        # Step 2: Create a temporary table with the correct schema
        print("\nCreating temporary table with correct schema...")
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS borrow_new (
                borrow_id INTEGER PRIMARY KEY AUTOINCREMENT,
                equipment_id INTEGER NOT NULL,
                barcode TEXT NOT NULL,
                borrow_time TEXT NOT NULL,
                quantity_borrowed INTEGER DEFAULT 1,
                return_time TEXT,
                borrower_email TEXT,
                borrower_name TEXT,
                return_status TEXT DEFAULT 'Borrowed'
            )
        """)
        
        # Step 3: Copy data from old borrow table to new one
        print("Copying data to new table...")
        cursor.execute("""
            INSERT INTO borrow_new (
                borrow_id, equipment_id, barcode, borrow_time, quantity_borrowed, return_time
            )
            SELECT 
                borrow_id, equipment_id, barcode, borrow_time, quantity_borrowed, return_time
            FROM borrow
        """)
        
        # Step 4: Update borrower information from transactions table
        print("Updating borrower information from transactions...")
        cursor.execute("""
            UPDATE borrow_new 
            SET borrower_email = (
                SELECT borrower_email 
                FROM transactions 
                WHERE transactions.barcode = borrow_new.barcode 
                AND transactions.action = 'Borrowed'
                AND transactions.datetime LIKE substr(borrow_new.borrow_time, 1, 10) || '%'
                LIMIT 1
            )
            WHERE borrower_email IS NULL
        """)
        
        cursor.execute("""
            UPDATE borrow_new 
            SET borrower_name = (
                SELECT borrower_name 
                FROM transactions 
                WHERE transactions.barcode = borrow_new.barcode 
                AND transactions.action = 'Borrowed'
                AND transactions.datetime LIKE substr(borrow_new.borrow_time, 1, 10) || '%'
                LIMIT 1
            )
            WHERE borrower_name IS NULL
        """)
        
        # Step 5: Set return_status based on return_time
        print("Setting return status...")
        cursor.execute("""
            UPDATE borrow_new 
            SET return_status = 
                CASE 
                    WHEN return_time IS NULL THEN 'Borrowed'
                    WHEN quantity_borrowed > 0 AND return_time IS NOT NULL THEN 'Returned'
                    ELSE 'Borrowed'
                END
        """)
        
        # Step 6: Count records before drop
        cursor.execute("SELECT COUNT(*) FROM borrow")
        old_count = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM borrow_new")
        new_count = cursor.fetchone()[0]
        
        print(f"Records in old table: {old_count}")
        print(f"Records in new table: {new_count}")
        
        # Step 7: Drop the old table and rename new one
        print("Replacing old table with new one...")
        cursor.execute("DROP TABLE IF EXISTS borrow_old")
        cursor.execute("ALTER TABLE borrow RENAME TO borrow_old")
        cursor.execute("ALTER TABLE borrow_new RENAME TO borrow")
        
        # Step 8: Create indexes for better performance
        print("Creating indexes...")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_borrow_barcode ON borrow(barcode)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_borrow_borrower_email ON borrow(borrower_email)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_borrow_return_status ON borrow(return_status)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_borrow_return_time ON borrow(return_time)")
        
        # Commit all changes
        conn.commit()
        
        # Step 9: Verify the changes
        print("\nVerification:")
        
        # Check new schema
        cursor.execute("PRAGMA table_info(borrow)")
        new_columns = [column[1] for column in cursor.fetchall()]
        print(f"New columns: {new_columns}")
        
        # Show sample data with borrower info
        print("\nSample data with borrower info:")
        cursor.execute("""
            SELECT borrow_id, barcode, borrower_name, borrower_email, borrow_time, return_time, return_status 
            FROM borrow 
            LIMIT 5
        """)
        sample_data = cursor.fetchall()
        for row in sample_data:
            print(f"  ID: {row[0]}, Barcode: {row[1]}, Borrower: {row[2]}, Email: {row[3]}, Status: {row[6]}")
        
        # Show borrower trends sample
        print("\nBorrower trends sample:")
        cursor.execute("""
            SELECT 
                borrower_name,
                borrower_email,
                COUNT(*) as total_borrowed,
                SUM(CASE WHEN return_time IS NOT NULL THEN 1 ELSE 0 END) as total_returned,
                SUM(CASE WHEN return_time IS NULL THEN 1 ELSE 0 END) as currently_borrowed,
                ROUND(AVG(CASE WHEN return_time IS NOT NULL 
                    THEN (julianday(return_time) - julianday(borrow_time)) 
                    ELSE NULL END), 2) as avg_return_days
            FROM borrow
            WHERE borrower_name IS NOT NULL
            GROUP BY borrower_email, borrower_name
            ORDER BY total_borrowed DESC
            LIMIT 5
        """)
        trends_data = cursor.fetchall()
        
        if trends_data:
            for row in trends_data:
                print(f"  {row[0]}: {row[2]} borrowed, {row[3]} returned, {row[4]} ongoing, {row[5]} avg days")
        else:
            print("  No borrower trends data yet - start borrowing equipment to see trends!")
        
        # Count records with borrower info
        cursor.execute("SELECT COUNT(*) FROM borrow WHERE borrower_email IS NOT NULL")
        with_borrower_info = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM borrow")
        total_records = cursor.fetchone()[0]
        
        print(f"\nSummary:")
        print(f"  Total borrow records: {total_records}")
        print(f"  Records with borrower info: {with_borrower_info}")
        if total_records > 0:
            print(f"  Success rate: {(with_borrower_info/total_records)*100:.1f}%")
        else:
            print("  Success rate: N/A")
        
        conn.close()
        
        print(f"\nBorrower tracking fix completed successfully!")
        print("Your 'borrower trends and return compliance' reports should now show data.")
        
        return True
        
    except Exception as e:
        print(f"Error during fix: {e}")
        import traceback
        traceback.print_exc()
        return False

def backup_database():
    """Create a backup of the database before making changes"""
    db_path = "faculty_account.db"
    backup_path = f"faculty_account_backup_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.db"
    
    if os.path.exists(db_path):
        shutil.copy2(db_path, backup_path)
        print(f"Database backed up to: {backup_path}")
        return backup_path
    else:
        print("No database file found to backup")
        return None

def restore_backup(backup_path):
    """Restore database from backup"""
    if os.path.exists(backup_path):
        shutil.copy2(backup_path, "faculty_account.db")
        print(f"Database restored from: {backup_path}")
        return True
    else:
        print("Backup file not found")
        return False

if __name__ == "__main__":
    print("=" * 60)
    print("BORROWER TRACKING FIX TOOL")
    print("=" * 60)
    
    # No confirmation needed - just run the fix
    print("\nRunning database fix automatically...")
    
    # Create backup
    backup_file = backup_database()
    
    # Run the fix
    success = fix_borrower_tracking()
    
    if not success and backup_file:
        print("\nAttempting to restore from backup due to errors...")
        restore_backup(backup_file)