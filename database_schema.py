# database_schema.py
import sqlite3
import os

def init_database():
    """Initialize the database with the equipment table schema"""
    conn = sqlite3.connect("faculty_account.db")
    cursor = conn.cursor()
    
    # Create equipment table with all required fields
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS equipment (
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
    
    # Create equipment_images directory if it doesn't exist
    if not os.path.exists("equipment_images"):
        os.makedirs("equipment_images")
    
    conn.commit()
    conn.close()
    print("Database initialized successfully")

def get_db_connection():
    """Get a database connection"""
    return sqlite3.connect("faculty_account.db")

if __name__ == "__main__":
    init_database()