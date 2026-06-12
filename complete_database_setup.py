# complete_database_setup.py - RUN THIS ONCE TO SET UP EVERYTHING
import sqlite3
from datetime import datetime

print(" Setting up faculty_account.db...")

# Create connection
conn = sqlite3.connect("faculty_account.db")
cursor = conn.cursor()

# 1. Users table
print(" Creating users table...")
cursor.execute("""
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    email TEXT UNIQUE NOT NULL, 
    password TEXT NOT NULL,
    role TEXT NOT NULL CHECK(role IN ('admin', 'faculty'))
)
""")

# 2. User profiles table
print(" Creating user_profiles table...")
cursor.execute("""
CREATE TABLE IF NOT EXISTS user_profiles (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    full_name TEXT NOT NULL,
    employee_id TEXT UNIQUE NOT NULL,
    contact_number TEXT,
    department TEXT NOT NULL,
    position TEXT NOT NULL,
    account_status TEXT NOT NULL DEFAULT 'Active',
    return_compliance_status TEXT NOT NULL DEFAULT 'Good Standing',
    FOREIGN KEY (user_id) REFERENCES users (id)
)
""")

# 3. Equipment table - DROP AND RECREATE to ensure clean state
print(" Creating equipment table...")
cursor.execute("DROP TABLE IF EXISTS equipment")
cursor.execute("""
CREATE TABLE equipment (
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
    location TEXT,
    additional_notes TEXT
)
""")

# 4. Reservations table
print(" Creating reservations table...")
cursor.execute("DROP TABLE IF EXISTS reservations")
cursor.execute("""
CREATE TABLE reservations (
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

# 5. Notifications table
print(" Creating notifications table...")
cursor.execute("DROP TABLE IF EXISTS notifications")
cursor.execute("""
CREATE TABLE notifications (
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

# 6. Borrow table
print(" Creating borrow table...")
cursor.execute("DROP TABLE IF EXISTS borrow")
cursor.execute("""
CREATE TABLE borrow (
    borrow_id INTEGER PRIMARY KEY AUTOINCREMENT,
    equipment_id INTEGER NOT NULL,
    barcode TEXT NOT NULL,
    borrow_time TEXT NOT NULL,
    FOREIGN KEY (equipment_id) REFERENCES equipment(id)
)
""")

# 7. Transactions table
print(" Creating transactions table...")
cursor.execute("DROP TABLE IF EXISTS transactions")
cursor.execute("""
CREATE TABLE transactions (
    transaction_id INTEGER PRIMARY KEY AUTOINCREMENT,
    datetime TEXT NOT NULL,
    borrower_name TEXT NOT NULL,
    borrower_email TEXT NOT NULL,
    equipment_name TEXT NOT NULL,
    barcode TEXT NOT NULL,
    action TEXT NOT NULL CHECK(action IN ('Borrowed','Returned')),
    status TEXT NOT NULL,
    handled_by TEXT NOT NULL,
    remarks TEXT
)
""")

# INSERT SAMPLE DATA
print("\n Inserting sample data...")

# Sample users
print("   Adding users...")
cursor.execute("INSERT OR IGNORE INTO users (email, password, role) VALUES (?, ?, ?)",
               ("admin@nursing.com", "admin123", "admin"))
cursor.execute("INSERT OR IGNORE INTO users (email, password, role) VALUES (?, ?, ?)",
               ("faculty@nursing.com", "faculty123", "faculty"))

# Sample user profile for faculty
print("   Adding user profiles...")
cursor.execute("""
    INSERT OR IGNORE INTO user_profiles 
    (user_id, full_name, employee_id, contact_number, department, position, account_status, return_compliance_status)
    SELECT id, 'Faculty User', 'EID-001', '123-456-7890', 'Nursing', 'Professor', 'Active', 'Good Standing'
    FROM users WHERE email = 'faculty@nursing.com'
""")

# Sample equipment - THIS IS CRITICAL!
print("   Adding equipment...")
sample_equipment = [
    ("4801002457825", "Microscopes", "Capture and display specimen images.", "capstone/microscope.jpg", "Available", "Laboratory Equipment", "Place the slide and adjust the focus knobs.", None, None, None, None, None, None, None),
    ("4801002457824", "Test tubes", "Small glass containers for mixing chemicals.", "capstone/testtube.jpeg", "Available", "Laboratory Equipment", "Mix or heat chemicals with care.", None, None, None, None, None, None, None),
    ("4801002457823", "Medical apparatus", "Used to diagnose or treat.", "capstone/apparatus.jpeg", "Available", "Medical Equipment", "Follow standard procedures for use.", None, None, None, None, None, None, None),
    ("4801002457822", "Funnels", "Pour liquids into small openings.", "capstone/funnel.jpeg", "Available", "Laboratory Equipment", "Pour liquids slowly to avoid spills.", None, None, None, None, None, None, None),
    ("4801002457821", "Wire gauzes", "Heat-resistant mesh for experiments.", "capstone/gauze.jpeg", "Available", "Laboratory Equipment", "Place under beakers when heating.", None, None, None, None, None, None, None),
    ("6970122841710", "Test tube holders", "Hold test tubes over flames.", "capstone/holder.jpeg", "Available", "Laboratory Equipment", "Grip test tubes firmly over heat.", None, None, None, None, None, None, None)
]

for equipment in sample_equipment:
    cursor.execute("""
        INSERT INTO equipment (barcode, name, description, image_path, availability_status, category, usage_instruction,
                              manufacturer, model, serial_number, purchase_date, warranty_info, location, additional_notes)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, equipment)

# Sample reservation
print("   Adding sample reservation...")
cursor.execute("""
    INSERT INTO reservations (equipment_id, user_email, quantity, date_needed, purpose, duration, notes, status)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
""", (1, "faculty@nursing.com", 2, "2025-10-05", "Class demonstration", "2 hours", "Need for lab", "Pending"))

# Sample transaction
print("   Adding sample transaction...")
borrower_email = "faculty@nursing.com"
cursor.execute("""
    INSERT INTO transactions (
        datetime, borrower_name, borrower_email, equipment_name, barcode,
        action, status, handled_by, remarks
    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
""", (
    datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    borrower_email,
    borrower_email,
    "Microscopes",
    "4801002457825",
    "Borrowed",
    "Ongoing",
    "Custodian 1",
    None
))

# Commit and verify
conn.commit()

# Verify equipment was inserted
cursor.execute("SELECT COUNT(*) FROM equipment")
equipment_count = cursor.fetchone()[0]

cursor.execute("SELECT COUNT(*) FROM users")
user_count = cursor.fetchone()[0]

conn.close()

print("\n Database setup complete!")
print(f"    Equipment items: {equipment_count}")
print(f"    Users: {user_count}")
print("\n You can now run your application!")

if equipment_count == 0:
    print("\n  WARNING: No equipment found! Check if the INSERT statements ran correctly.")
else:
    print("\n Successfully created {equipment_count} equipment items")