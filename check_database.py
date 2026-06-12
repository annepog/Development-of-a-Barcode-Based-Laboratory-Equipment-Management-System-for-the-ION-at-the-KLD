import sqlite3

conn = sqlite3.connect("faculty_account.db")
cursor = conn.cursor()

print("=" * 60)
print("DATABASE CONTENTS CHECK")
print("=" * 60)

# Check equipment table structure
print("\n EQUIPMENT TABLE COLUMNS:")
cursor.execute("PRAGMA table_info(equipment)")
columns = cursor.fetchall()
for col in columns:
    print(f"  - {col[1]} ({col[2]})")

# Check equipment count
cursor.execute("SELECT COUNT(*) FROM equipment")
count = cursor.fetchone()[0]
print(f"\n TOTAL EQUIPMENT ITEMS: {count}")

# Show all equipment
print("\n EQUIPMENT LIST:")
print("-" * 60)
cursor.execute("""
    SELECT barcode, name, tracking_type, total_quantity, 
           available_quantity, availability_status
    FROM equipment
""")
equipment = cursor.fetchall()

if equipment:
    for item in equipment:
        barcode, name, tracking_type, total_qty, avail_qty, avail_status = item
        print(f"\n  Barcode: {barcode}")
        print(f"  Name: {name}")
        print(f"  Type: {tracking_type}")
        print(f"  Quantity: {avail_qty}/{total_qty}")
        print(f"  Status: {avail_status}")
        print("-" * 60)
else:
    print("   No equipment found in database!")

conn.close()

print("\n Check complete!")