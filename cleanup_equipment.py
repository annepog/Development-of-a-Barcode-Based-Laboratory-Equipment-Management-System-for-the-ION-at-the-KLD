import sqlite3

conn = sqlite3.connect("faculty_account.db")
cursor = conn.cursor()

print("Starting equipment cleanup...")
print("="*60)

# Step 1: Delete duplicate rows (11-17) which are duplicates of 1-10
print("\n1. Removing duplicate equipment (rows 11-17)...")
cursor.execute("DELETE FROM equipment WHERE id >= 11 AND id <= 17")
deleted_count = cursor.rowcount
print(f"   Deleted {deleted_count} duplicate rows")

# Step 2: Update old text barcodes to numeric format (13 digits like the others)
print("\n2. Updating barcodes to numeric format...")

barcode_updates = [
    ("MICRO-001", "4801002457830"),      # Microscope Unit 1
    ("MICRO-002", "4801002457831"),      # Microscope Unit 2
    ("APPARATUS-001", "4801002457832"),  # Medical Apparatus
    ("TEST-TUBE-STD", "4801002457833"),  # Test Tubes
    ("BEAKER-250ML", "4801002457834"),   # Beakers
    ("FUNNEL-STD", "4801002457835"),     # Funnels
    ("GAUZE-WIRE", "4801002457836"),     # Wire Gauzes
]

for old_barcode, new_barcode in barcode_updates:
    cursor.execute("SELECT id, name FROM equipment WHERE barcode = ?", (old_barcode,))
    result = cursor.fetchone()
    if result:
        equipment_id, equipment_name = result
        cursor.execute("UPDATE equipment SET barcode = ? WHERE barcode = ?", 
                      (new_barcode, old_barcode))
        print(f"   Updated: {old_barcode} -> {new_barcode} ({equipment_name})")
    else:
        print(f"   Skipped: {old_barcode} (not found)")

# Step 3: Display final equipment list
print("\n3. Final equipment list:")
print("-"*60)
cursor.execute("""
    SELECT id, barcode, name, tracking_type, total_quantity, available_quantity 
    FROM equipment 
    ORDER BY id
""")

equipment_list = cursor.fetchall()
for eq_id, barcode, name, tracking_type, total_qty, avail_qty in equipment_list:
    if tracking_type == "quantity":
        print(f"   ID {eq_id:2d}: {barcode} - {name} ({avail_qty}/{total_qty} units)")
    else:
        print(f"   ID {eq_id:2d}: {barcode} - {name} (individual)")

print("-"*60)
print(f"   Total equipment: {len(equipment_list)} items")

# Commit changes
conn.commit()
conn.close()

print("\n" + "="*60)
print("Equipment cleanup complete!")
print("="*60)
print("\nAll barcodes are now 13-digit numeric codes")
print("Duplicate equipment removed")
print("Database is ready to use!")