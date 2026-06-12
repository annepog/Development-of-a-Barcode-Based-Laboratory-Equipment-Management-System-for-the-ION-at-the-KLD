# check_notifications.py
import pymysql

def check_notifications_table():
    """Check the actual structure and data in notifications table"""
    try:
        conn = pymysql.connect(
            host='localhost',
            user='root',
            password='',
            database='faculty_account',
            charset='utf8mb4',
            cursorclass=pymysql.cursors.DictCursor
        )
        cursor = conn.cursor()
        
        print("🔍 CHECKING NOTIFICATIONS TABLE")
        print("=" * 50)
        
        # Check table structure
        cursor.execute("DESCRIBE notifications")
        columns = cursor.fetchall()
        print("📋 TABLE STRUCTURE:")
        for col in columns:
            print(f"   - {col['Field']} ({col['Type']})")
        
        # Check row count
        cursor.execute("SELECT COUNT(*) as count FROM notifications")
        count = cursor.fetchone()['count']
        print(f"\n📊 TOTAL ROWS: {count}")
        
        # Check sample data
        if count > 0:
            cursor.execute("SELECT * FROM notifications LIMIT 5")
            notifications = cursor.fetchall()
            print(f"\n📝 SAMPLE DATA (first {len(notifications)} rows):")
            for i, notif in enumerate(notifications):
                print(f"\n   Row {i+1}:")
                for key, value in notif.items():
                    print(f"     {key}: {value}")
        
        # Check if there are notifications for a specific user
        test_email = "test@nursing.com"  # Change this to an actual user email
        cursor.execute("SELECT COUNT(*) as count FROM notifications WHERE recipientemail = %s", (test_email,))
        user_count = cursor.fetchone()['count']
        print(f"\n👤 Notifications for {test_email}: {user_count}")
        
        if user_count > 0:
            cursor.execute("SELECT * FROM notifications WHERE recipientemail = %s LIMIT 3", (test_email,))
            user_notifs = cursor.fetchall()
            print(f"   Sample notifications for {test_email}:")
            for notif in user_notifs:
                print(f"     - ID: {notif['notification_id']}, Type: {notif['notification_type']}, Read: {notif['is_read']}")
        
        conn.close()
        
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    check_notifications_table()