# debug_notifications.py
import pymysql
from datetime import datetime

def debug_notifications():
    """Debug notifications for specific accounts"""
    
    print("=== NOTIFICATIONS DEBUG ===")
    
    # Test accounts
    test_accounts = [
        "anneclarissegarces30@gmail.com",
        "bleysico@gmail.com"
    ]
    
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
        
        print("Database connection successful")
        
        # Check if notifications table exists
        cursor.execute("SHOW TABLES LIKE 'notifications'")
        table_exists = cursor.fetchone()
        
        if not table_exists:
            print("ERROR: Notifications table does not exist!")
            return
        
        print("Notifications table exists")
        
        # Check table structure
        cursor.execute("DESCRIBE notifications")
        columns = cursor.fetchall()
        print("Table structure:")
        for col in columns:
            print(f"  {col['Field']} ({col['Type']})")
        
        # Check total notifications count
        cursor.execute("SELECT COUNT(*) as total FROM notifications")
        total_count = cursor.fetchone()['total']
        print(f"Total notifications in database: {total_count}")
        
        # Check for each test account
        for account in test_accounts:
            print(f"\n--- Checking account: {account} ---")
            
            # Check if account exists in users table
            cursor.execute("SELECT COUNT(*) as count FROM users WHERE email = %s", (account,))
            user_exists = cursor.fetchone()['count']
            print(f"User exists in database: {user_exists > 0}")
            
            # Check notifications for this account
            cursor.execute("""
                SELECT COUNT(*) as count FROM notifications 
                WHERE recipient_email = %s
            """, (account,))
            notif_count = cursor.fetchone()['count']
            print(f"Total notifications for user: {notif_count}")
            
            # Check unread notifications
            cursor.execute("""
                SELECT COUNT(*) as count FROM notifications 
                WHERE recipient_email = %s AND is_read = 0
            """, (account,))
            unread_count = cursor.fetchone()['count']
            print(f"Unread notifications: {unread_count}")
            
            # Show actual notifications
            if notif_count > 0:
                cursor.execute("""
                    SELECT notification_id, message, notification_type, created_at, is_read
                    FROM notifications 
                    WHERE recipient_email = %s
                    ORDER BY created_at DESC
                """, (account,))
                notifications = cursor.fetchall()
                
                print("Actual notifications:")
                for notif in notifications:
                    status = "UNREAD" if not notif['is_read'] else "READ"
                    print(f"  - ID: {notif['notification_id']}, Type: {notif['notification_type']}, Status: {status}")
                    print(f"    Message: {notif['message']}")
                    print(f"    Date: {notif['created_at']}")
            else:
                print("  No notifications found for this user")
                
                # Create a test notification to see if it works
                print("  Creating test notification...")
                timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                try:
                    cursor.execute("""
                        INSERT INTO notifications (recipient_email, message, notification_type, created_at, is_read)
                        VALUES (%s, %s, %s, %s, %s)
                    """, (account, "TEST: Debug notification", "debug", timestamp, 0))
                    conn.commit()
                    print("  Test notification created successfully")
                except Exception as e:
                    print(f"  ERROR creating test notification: {e}")
                    conn.rollback()
        
        # Check if there are any notifications at all
        print(f"\n--- All notifications in database ---")
        cursor.execute("""
            SELECT recipient_email, COUNT(*) as count 
            FROM notifications 
            GROUP BY recipient_email
        """)
        all_notifs = cursor.fetchall()
        
        if all_notifs:
            print("Notifications by user:")
            for notif in all_notifs:
                print(f"  {notif['recipient_email']}: {notif['count']} notifications")
        else:
            print("  No notifications found in entire database")
            
        # Check if there are any system-generated notifications
        print(f"\n--- System notifications ---")
        cursor.execute("""
            SELECT * FROM notifications 
            WHERE recipient_email IN ('admin@nursing.com', 'system@nursing.com')
            OR notification_type LIKE '%system%'
            OR notification_type LIKE '%admin%'
        """)
        system_notifs = cursor.fetchall()
        print(f"System notifications found: {len(system_notifs)}")
        
        conn.close()
        
    except Exception as e:
        print(f"Database error: {e}")

def test_notification_manager():
    """Test the notification manager with specific accounts"""
    print("\n=== TESTING NOTIFICATION MANAGER ===")
    
    from notification_manager import NotificationManager
    nm = NotificationManager()
    
    test_accounts = [
        "anneclarissegarces30@gmail.com",
        "bleysico@gmail.com"
    ]
    
    for account in test_accounts:
        print(f"\n--- Testing NotificationManager for: {account} ---")
        
        # Test get_unread_count
        try:
            unread_count = nm.get_unread_count(account)
            print(f"get_unread_count result: {unread_count}")
        except Exception as e:
            print(f"get_unread_count ERROR: {e}")
        
        # Test get_all_notifications
        try:
            notifications = nm.get_all_notifications(account)
            print(f"get_all_notifications result: {len(notifications)} notifications")
            
            if notifications:
                for i, notif in enumerate(notifications):
                    print(f"  Notification {i+1}: ID={notif[0]}, Message='{notif[1][:50]}...', Read={notif[5]}")
        except Exception as e:
            print(f"get_all_notifications ERROR: {e}")
        
        # Test creating a notification
        try:
            test_id = nm.create_notification(
                recipient_email=account,
                message=f"Debug test notification for {account}",
                notification_type="debug_test"
            )
            if test_id:
                print(f"Successfully created notification ID: {test_id}")
            else:
                print("Failed to create notification")
        except Exception as e:
            print(f"create_notification ERROR: {e}")

def check_recent_activity():
    """Check if there's any recent activity that should generate notifications"""
    print("\n=== CHECKING RECENT ACTIVITY ===")
    
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
        
        # Check reservations
        cursor.execute("SELECT COUNT(*) as count FROM reservations")
        reserv_count = cursor.fetchone()['count']
        print(f"Total reservations: {reserv_count}")
        
        if reserv_count > 0:
            cursor.execute("SELECT * FROM reservations ORDER BY created_at DESC LIMIT 3")
            recent_reserv = cursor.fetchall()
            print("Recent reservations:")
            for reserv in recent_reserv:
                print(f"  - ID: {reserv['reservation_id']}, User: {reserv['user_email']}, Status: {reserv['status']}")
        
        # Check borrow requests
        cursor.execute("SELECT COUNT(*) as count FROM borrow")
        borrow_count = cursor.fetchone()['count']
        print(f"Total borrow requests: {borrow_count}")
        
        if borrow_count > 0:
            cursor.execute("SELECT * FROM borrow ORDER BY created_at DESC LIMIT 3")
            recent_borrow = cursor.fetchall()
            print("Recent borrow requests:")
            for borrow in recent_borrow:
                print(f"  - ID: {borrow['borrow_id']}, User: {borrow['user_email']}, Status: {borrow['status']}")
        
        conn.close()
        
    except Exception as e:
        print(f"Activity check error: {e}")

if __name__ == "__main__":
    debug_notifications()
    test_notification_manager()
    check_recent_activity()
    print("\n=== DEBUG COMPLETE ===")