import pymysql

def test_mysql():
    """Test MySQL connection and data"""
    try:
        conn = pymysql.connect(
            host='localhost',
            user='root',      # CHANGE THIS
            password='',      # CHANGE THIS
            database='faculty_account'
        )
        cursor = conn.cursor()
        
        print(" MySQL Connection Successful!")
        
        # Show tables
        cursor.execute("SHOW TABLES")
        tables = cursor.fetchall()
        print(f" Tables found: {len(tables)}")
        for table in tables:
            print(f"   - {table[0]}")
        
        # Test data
        print("\n Sample Users:")
        cursor.execute("SELECT email, role FROM users LIMIT 5")
        users = cursor.fetchall()
        for user in users:
            print(f"   - {user[0]} ({user[1]})")
        
        print("\n Sample Equipment:")
        cursor.execute("SELECT barcode, name, tracking_type FROM equipment LIMIT 5")
        equipment = cursor.fetchall()
        for item in equipment:
            print(f"   - {item[0]}: {item[1]} ({item[2]})")
        
        conn.close()
        
    except Exception as e:
        print(f" MySQL Test Failed: {e}")

if __name__ == "__main__":
    test_mysql()