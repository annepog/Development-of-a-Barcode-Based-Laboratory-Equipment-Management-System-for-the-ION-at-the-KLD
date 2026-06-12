# Updated database.py - Complete version without contact numbers
import sqlite3
from datetime import datetime

def init_database():
    conn = sqlite3.connect("faculty_account.db")
    cursor = conn.cursor()

    # Users table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        email TEXT UNIQUE NOT NULL, 
        password TEXT NOT NULL,
        role TEXT NOT NULL CHECK(role IN ('admin', 'faculty'))
    )
    """)

    # User profiles table - NO CONTACT NUMBER
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS user_profiles (
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

    # Equipment table with quantity tracking AND is_borrowable
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS equipment (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        barcode TEXT UNIQUE NOT NULL,
        name TEXT NOT NULL,
        description TEXT NOT NULL,
        image_path TEXT,
        category TEXT NOT NULL,
        usage_instruction TEXT NOT NULL,
        manufacturer TEXT,
        model TEXT,
        serial_number TEXT,
        purchase_date TEXT,
        warranty_info TEXT,
        location TEXT,
        additional_notes TEXT,
        
        -- FIELDS FOR QUANTITY TRACKING
        tracking_type TEXT NOT NULL DEFAULT 'individual' CHECK(tracking_type IN ('individual', 'quantity')),
        total_quantity INTEGER DEFAULT 1,
        available_quantity INTEGER DEFAULT 1,
        min_stock_level INTEGER DEFAULT 5,
        
        -- NEW: Borrowable flag (1=borrowable, 0=not borrowable)
        is_borrowable INTEGER DEFAULT 1,
        
        -- Keep availability_status for individual items only
        availability_status TEXT DEFAULT 'Available'
    )
    """)

    # Check if is_borrowable column exists, if not add it
    try:
        cursor.execute("SELECT is_borrowable FROM equipment LIMIT 1")
    except sqlite3.OperationalError:
        print("Adding is_borrowable column to existing equipment table...")
        cursor.execute("ALTER TABLE equipment ADD COLUMN is_borrowable INTEGER DEFAULT 1")
        conn.commit()
        print("Column added successfully!")

    # Borrow table (updated to handle quantities)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS borrow (
        borrow_id INTEGER PRIMARY KEY AUTOINCREMENT,
        equipment_id INTEGER NOT NULL,
        barcode TEXT NOT NULL,
        borrow_time TEXT NOT NULL,
        return_time TEXT,
        quantity_borrowed INTEGER DEFAULT 1,
        FOREIGN KEY (equipment_id) REFERENCES equipment(id)
    )
    """)

    # Transactions table (updated to handle quantities)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS transactions (
        transaction_id INTEGER PRIMARY KEY AUTOINCREMENT,
        datetime TEXT NOT NULL,
        borrower_name TEXT NOT NULL,
        borrower_email TEXT NOT NULL,
        equipment_name TEXT NOT NULL,
        barcode TEXT NOT NULL,
        action TEXT NOT NULL CHECK(action IN ('Borrowed','Returned')),
        status TEXT NOT NULL,
        handled_by TEXT NOT NULL,
        remarks TEXT,
        quantity INTEGER DEFAULT 1
    )
    """)

    # Reservations table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS reservations (
        reservation_id INTEGER PRIMARY KEY AUTOINCREMENT,
        equipment_id INTEGER NOT NULL,
        user_email TEXT NOT NULL,
        quantity INTEGER NOT NULL,
        date_needed TEXT NOT NULL,
        purpose TEXT NOT NULL,
        duration TEXT NOT NULL,
        notes TEXT,
        status TEXT NOT NULL DEFAULT 'Pending',
        created_at TEXT NOT NULL DEFAULT (datetime('now')),
        updated_at TEXT,
        FOREIGN KEY (equipment_id) REFERENCES equipment(id),
        FOREIGN KEY (user_email) REFERENCES users(email)
    )
    """)

    # Notifications table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS notifications (
        notification_id INTEGER PRIMARY KEY AUTOINCREMENT,
        recipient_email TEXT NOT NULL,
        message TEXT NOT NULL,
        notification_type TEXT NOT NULL,
        related_id INTEGER,
        created_at TEXT NOT NULL,
        is_read INTEGER NOT NULL DEFAULT 0,
        FOREIGN KEY (recipient_email) REFERENCES users(email)
    )
    """)

    # Equipment issues table with reporter tracking
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS equipment_issues (
        issue_id INTEGER PRIMARY KEY AUTOINCREMENT,
        barcode TEXT NOT NULL,
        equipment_name TEXT NOT NULL,
        issue_type TEXT NOT NULL,
        description TEXT NOT NULL,
        priority TEXT NOT NULL,
        status TEXT NOT NULL DEFAULT 'Pending',
        reported_date TEXT NOT NULL,
        resolved_date TEXT,
        reported_by_user_id INTEGER NOT NULL,
        reported_by_name TEXT NOT NULL,
        reported_by_email TEXT NOT NULL,
        FOREIGN KEY (barcode) REFERENCES equipment(barcode),
        FOREIGN KEY (reported_by_user_id) REFERENCES users(id)
    )
    """)

    # Insert sample accounts
    cursor.execute("INSERT OR IGNORE INTO users (email, password, role) VALUES (?, ?, ?)",
                   ("admin@nursing.com", "admin123", "admin"))
    cursor.execute("INSERT OR IGNORE INTO users (email, password, role) VALUES (?, ?, ?)",
                   ("faculty@nursing.com", "faculty123", "faculty"))

    # Insert sample profiles - NO CONTACT NUMBERS
    cursor.execute("""
        INSERT OR IGNORE INTO user_profiles 
        (user_id, full_name, employee_id, department, position, account_status, return_compliance_status)
        SELECT id, 'Dr. Jane Smith', 'EID-001', 'Nursing', 'Professor', 'Active', 'Good Standing'
        FROM users WHERE email = 'faculty@nursing.com'
    """)

    cursor.execute("""
        INSERT OR IGNORE INTO user_profiles 
        (user_id, full_name, employee_id, department, position, account_status, return_compliance_status)
        SELECT id, 'Admin User', 'EID-000', 'Administration', 'System Administrator', 'Active', 'Good Standing'
        FROM users WHERE email = 'admin@nursing.com'
    """)

    # Sample equipment with MIXED tracking types and borrowable flags
    sample_equipment = [
        # BORROWABLE - INDIVIDUAL TRACKING (high-value items)
        ("MICRO-001", "Microscope Unit 1", "Advanced laboratory microscope", "microscope.jpg", 
         "Laboratory Equipment", "Place slide and adjust focus", "Olympus", "CX23", "SN123456", 
         "2023-01-15", "2 years", "Lab Room 101", None, 
         "individual", 1, 1, 0, "Available", 1),  # is_borrowable = 1
        
        ("MICRO-002", "Microscope Unit 2", "Advanced laboratory microscope", "microscope.jpg", 
         "Laboratory Equipment", "Place slide and adjust focus", "Olympus", "CX23", "SN123457", 
         "2023-01-15", "2 years", "Lab Room 101", None, 
         "individual", 1, 1, 0, "Available", 1),  # is_borrowable = 1
        
        ("APPARATUS-001", "Medical Apparatus A", "Diagnostic equipment", "apparatus.jpg", 
         "Medical Equipment", "Follow standard procedures", "Medline", "MA-2000", "SN123458", 
         "2023-03-10", "3 years", "Medical Lab", None, 
         "individual", 1, 1, 0, "Available", 1),  # is_borrowable = 1
        
        # NOT BORROWABLE - QUANTITY TRACKING (consumables/bulk items)
        ("TEST-TUBE-STD", "Test Tubes (Standard)", "Small glass containers for mixing", "testtubes.jpg", 
         "Laboratory Equipment", "Mix or heat chemicals with care", "Pyrex", "Standard", None, 
         "2023-02-20", "1 year", "Lab Storage", "Box of 50 units", 
         "quantity", 50, 50, 10, "Available", 0),  # is_borrowable = 0 (consumable)
        
        ("BEAKER-250ML", "Beakers (250ml)", "Glass beakers for measurements", "beaker.jpg", 
         "Laboratory Equipment", "Handle with care, heat-resistant", "Pyrex", "250ml", None, 
         "2023-04-05", "1 year", "Lab Storage", "Standard laboratory beakers", 
         "quantity", 30, 30, 5, "Available", 0),  # is_borrowable = 0 (consumable)
        
        ("FUNNEL-STD", "Funnels (Standard)", "Pour liquids into small openings", "funnel.jpg", 
         "Laboratory Equipment", "Pour slowly to avoid spills", "Generic", "Standard", None, 
         "2023-04-05", "6 months", "Lab Storage", None, 
         "quantity", 20, 20, 5, "Available", 0),  # is_borrowable = 0 (consumable)
        
        ("GAUZE-WIRE", "Wire Gauzes", "Heat-resistant mesh", "gauze.jpg", 
         "Laboratory Equipment", "Place under beakers when heating", "Generic", "Heat Resistant", None, 
         "2023-05-12", "1 year", "Lab Storage", None, 
         "quantity", 40, 40, 10, "Available", 0),  # is_borrowable = 0 (consumable)
        
        # NOT BORROWABLE - INDIVIDUAL TRACKING (fixed location equipment)
        ("REFRIG-001", "Lab Refrigerator", "Medical-grade refrigerator", "refrigerator.jpg", 
         "Medical Equipment", "Store temperature-sensitive items", "Samsung", "MR-450", "SN789012", 
         "2023-06-01", "5 years", "Lab Room 102", "Fixed installation", 
         "individual", 1, 1, 0, "Available", 0),  # is_borrowable = 0 (fixed location)
    ]

    # Insert equipment only if not exists
    for equipment in sample_equipment:
        cursor.execute("SELECT barcode FROM equipment WHERE barcode = ?", (equipment[0],))
        if not cursor.fetchone():
            cursor.execute("""
                INSERT INTO equipment 
                (barcode, name, description, image_path, category, usage_instruction,
                 manufacturer, model, serial_number, purchase_date, warranty_info, 
                 location, additional_notes,
                 tracking_type, total_quantity, available_quantity, min_stock_level, 
                 availability_status, is_borrowable)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, equipment)

    conn.commit()
    conn.close()

    print(" Database setup complete!")
    print(" Contact numbers removed from user profiles")
    print(" is_borrowable field added to equipment")
    print("\n Sample Users:")
    print("   - Admin User (admin@nursing.com)")
    print("   - Dr. Jane Smith (faculty@nursing.com)")
    print("\n Equipment Types:")
    print("   - Borrowable: Microscopes, Medical Apparatus")
    print("   - Non-Borrowable: Test Tubes, Beakers, Funnels, Refrigerator")

if __name__ == "__main__":
    init_database()