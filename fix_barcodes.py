import sqlite3

conn = sqlite3.connect("faculty_account.db")
cursor = conn.cursor()

print(" Updating barcodes to numeric format...")

# Update the old text-based barcodes to numeric ones
barcode_updates = [
    ("TEST-TUBE-STD", "4801002457826"),
    ("BEAKER-250ML", "4801002457827"),
    ("FUNNEL-STD", "4801002457828"),
    ("GAUZE-WIRE", "4801002457829"),
]

for old_barcode, new_barcode in barcode_updates:
    cursor.execute("SELECT barcode FROM equipment WHERE barcode = ?", (old_barcode,))
    if cursor.fetchone():
        cursor.execute("UPDATE equipment SET barcode = ? WHERE barcode = ?", 
                      (new_barcode, old_barcode))
        print(f"   Updated: {old_barcode} {new_barcode}")
    else:
        print(f"    Skipped: {old_barcode} (not found)")

conn.commit()
conn.close()

print("\n Barcode update complete!")