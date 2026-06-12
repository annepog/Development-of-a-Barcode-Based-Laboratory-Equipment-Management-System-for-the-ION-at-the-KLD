# Database migration script - adds quantity tracking columns to existing database
import sqlite3
from datetime import datetime

conn = sqlite3.connect("faculty_account.db")
cursor = conn.cursor()

print(" Starting database migration...")

# Check if tracking_type column already exists
cursor.execute("PRAGMA table_info(equipment)")
columns = [column[1] for column in cursor.fetchall()]

if 'tracking_type' not in columns:
    print(" Adding new columns to equipment table...")
    
    # Add new columns for quantity tracking
    cursor.execute("""
        ALTER TABLE equipment 
        ADD COLUMN tracking_type TEXT NOT NULL DEFAULT 'individual' 
        CHECK(tracking_type IN ('individual', 'quantity'))
    """)
    
    cursor.execute("""
        ALTER TABLE equipment 
        ADD COLUMN total_quantity INTEGER DEFAULT 1
    """)
    
    cursor.execute("""
        ALTER TABLE equipment 
        ADD COLUMN available_quantity INTEGER DEFAULT 1
    """)
    
    cursor.execute("""
        ALTER TABLE equipment 
        ADD COLUMN min_stock_level INTEGER DEFAULT 5
    """)
    
    print(" New columns added successfully!")
    
    # Update existing equipment to have proper default values
    cursor.execute("""
        UPDATE equipment 
        SET tracking_type = 'individual',
            total_quantity = 1,
            available_quantity = CASE 
                WHEN availability_status = 'Available' THEN 1 
                ELSE 0 
            END,
            min_stock_level = 0
        WHERE tracking_type IS NULL OR tracking_type = 'individual'
    """)
    
    print(" Existing equipment updated with default values!")
else:
    print("ℹ  Columns already exist, skipping migration...")

# Check if quantity column exists in borrow table
cursor.execute("PRAGMA table_info(borrow)")
borrow_columns = [column[1] for column in cursor.fetchall()]

if 'quantity_borrowed' not in borrow_columns:
    print(" Adding quantity_borrowed to borrow table...")
    cursor.execute("""
        ALTER TABLE borrow 
        ADD COLUMN quantity_borrowed INTEGER DEFAULT 1
    """)
    print(" Borrow table updated!")
else:
    print("ℹ  Borrow table already has quantity_borrowed column")

# Check if quantity column exists in transactions table
cursor.execute("PRAGMA table_info(transactions)")
transaction_columns = [column[1] for column in cursor.fetchall()]

if 'quantity' not in transaction_columns:
    print(" Adding quantity to transactions table...")
    cursor.execute("""
        ALTER TABLE transactions 
        ADD COLUMN quantity INTEGER DEFAULT 1
    """)
    print(" Transactions table updated!")
else:
    print("  Transactions table already has quantity column")

conn.commit()

# Now insert sample quantity-tracked equipment
print("\n Adding sample quantity-tracked items...")

quantity_items = [
    ("TEST-TUBE-STD", "Test Tubes (Standard)", "Small glass containers for mixing", "capstone/testtube.jpeg", 
     "Laboratory Equipment", "Mix or heat chemicals with care", "Pyrex", "Standard", None, 
     "2023-02-20", "1 year", "Lab Storage", "Box of 50 units", 
     "quantity", 50, 50, 10),
    
    ("BEAKER-250ML", "Beakers (250ml)", "Glass beakers for measurements", None, 
     "Laboratory Equipment", "Handle with care, heat-resistant", "Pyrex", "250ml", None, 
     "2023-04-05", "1 year", "Lab Storage", "Standard laboratory beakers", 
     "quantity", 30, 30, 5),
    
    ("FUNNEL-STD", "Funnels (Standard)", "Pour liquids into small openings", "capstone/funnel.jpeg", 
     "Laboratory Equipment", "Pour slowly to avoid spills", "Generic", "Standard", None, 
     "2023-04-05", "6 months", "Lab Storage", None, 
     "quantity", 20, 20, 5),
    
    ("GAUZE-WIRE", "Wire Gauzes", "Heat-resistant mesh", "capstone/gauze.jpeg", 
     "Laboratory Equipment", "Place under beakers when heating", "Generic", "Heat Resistant", None, 
     "2023-05-12", "1 year", "Lab Storage", None, 
     "quantity", 40, 40, 10),
]

for item in quantity_items:
    cursor.execute("SELECT barcode FROM equipment WHERE barcode = ?", (item[0],))
    if not cursor.fetchone():
        cursor.execute("""
            INSERT INTO equipment 
            (barcode, name, description, image_path, category, usage_instruction,
             manufacturer, model, serial_number, purchase_date, warranty_info, 
             location, additional_notes,
             tracking_type, total_quantity, available_quantity, min_stock_level)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, item)
        print(f"   Added: {item[1]} (Qty: {item[14]})")
    else:
        print(f"    Skipped: {item[1]} (already exists)")

conn.commit()
conn.close()

print("\n Migration complete!")
print(" Your database now supports both individual and quantity tracking!")