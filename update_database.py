# update_database.py
import sqlite3
import os

def update_database_schema():
    """Update the existing database schema to add location and class columns"""
    conn = sqlite3.connect("faculty_account.db")
    cursor = conn.cursor()
    
    try:
        # Check if location column exists
        cursor.execute("PRAGMA table_info(equipment)")
        columns = [column[1] for column in cursor.fetchall()]
        
        # Add location column if it doesn't exist
        if 'location' not in columns:
            print("Adding location column...")
            cursor.execute("""
                ALTER TABLE equipment ADD COLUMN location TEXT 
                CHECK(location IN ('central supply room', 'anatomy laboratory', 'nutrition laboratory', 'skills laboratory', 'or-dr complex'))
            """)
        
        # Add class column if it doesn't exist
        if 'class' not in columns:
            print("Adding class column...")
            cursor.execute("""
                ALTER TABLE equipment ADD COLUMN class TEXT 
                CHECK(class IN ('consumable', 'plastic', 'apparatus', 'wooden', 'glass', 'metal'))
            """)
        
        # Fix any column name inconsistencies
        cursor.execute("PRAGMA table_info(equipment)")
        current_columns = cursor.fetchall()
        print("Current columns in equipment table:")
        for col in current_columns:
            print(f"  {col[1]} ({col[2]})")
        
        conn.commit()
        print("Database schema updated successfully!")
        
    except Exception as e:
        print(f"Error updating database: {e}")
        conn.rollback()
    finally:
        conn.close()

def fix_column_names():
    """Fix any column name inconsistencies"""
    conn = sqlite3.connect("faculty_account.db")
    cursor = conn.cursor()
    
    try:
        # Check current column names
        cursor.execute("PRAGMA table_info(equipment)")
        columns = cursor.fetchall()
        
        # Fix common column name issues
        column_mapping = {
            'usage_instructors': 'usage_instruction',
            'ls_borrowable': 'is_borrowable',
            'ls_archived': 'is_archived'
        }
        
        for old_name, new_name in column_mapping.items():
            if old_name in [col[1] for col in columns] and new_name not in [col[1] for col in columns]:
                print(f"Renaming {old_name} to {new_name}...")
                # SQLite doesn't support direct column rename, so we need to recreate the table
                recreate_table_with_correct_columns()
                break
        
    except Exception as e:
        print(f"Error fixing column names: {e}")
    finally:
        conn.close()

def recreate_table_with_correct_columns():
    """Recreate the table with correct column names"""
    conn = sqlite3.connect("faculty_account.db")
    cursor = conn.cursor()
    
    try:
        # Create a temporary table with correct schema
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS equipment_temp (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                barcode TEXT UNIQUE NOT NULL,
                name TEXT NOT NULL,
                description TEXT NOT NULL,
                image_path TEXT,
                availability_status TEXT NOT NULL DEFAULT 'Available',
                category TEXT NOT NULL,
                usage_instruction TEXT NOT NULL,
                manufacturer TEXT,
                model TEXT,
                serial_number TEXT,
                purchase_date TEXT,
                warranty_info TEXT,
                location TEXT CHECK(location IN ('central supply room', 'anatomy laboratory', 'nutrition laboratory', 'skills laboratory', 'or-dr complex')),
                additional_notes TEXT,
                tracking_type TEXT NOT NULL DEFAULT 'individual' CHECK(tracking_type IN ('individual', 'quantity')),
                total_quantity INTEGER DEFAULT 1,
                available_quantity INTEGER DEFAULT 1,
                min_stock_level INTEGER DEFAULT 5,
                is_borrowable INTEGER DEFAULT 1,
                class TEXT CHECK(class IN ('consumable', 'plastic', 'apparatus', 'wooden', 'glass', 'metal')),
                variant TEXT,
                is_archived INTEGER DEFAULT 0,
                archived_date TEXT
            )
        """)
        
        # Copy data from old table to new table
        cursor.execute("""
            INSERT INTO equipment_temp (
                id, barcode, name, description, image_path, availability_status, 
                category, usage_instruction, manufacturer, model, serial_number,
                purchase_date, warranty_info, additional_notes, tracking_type,
                total_quantity, available_quantity, min_stock_level, is_borrowable,
                variant, is_archived, archived_date
            )
            SELECT 
                id, barcode, name, description, image_path, availability_status,
                category, COALESCE(usage_instructors, usage_instruction, '') as usage_instruction,
                manufacturer, model, serial_number, purchase_date, warranty_info,
                additional_notes, tracking_type, total_quantity, available_quantity,
                min_stock_level, COALESCE(ls_borrowable, is_borrowable, 1) as is_borrowable,
                variant, COALESCE(ls_archived, is_archived, 0) as is_archived,
                archived_date
            FROM equipment
        """)
        
        # Drop old table and rename new table
        cursor.execute("DROP TABLE equipment")
        cursor.execute("ALTER TABLE equipment_temp RENAME TO equipment")
        
        conn.commit()
        print("Table recreated with correct column names!")
        
    except Exception as e:
        print(f"Error recreating table: {e}")
        conn.rollback()
    finally:
        conn.close()

if __name__ == "__main__":
    print("Updating database schema...")
    update_database_schema()
    fix_column_names()
    print("Database update complete!")