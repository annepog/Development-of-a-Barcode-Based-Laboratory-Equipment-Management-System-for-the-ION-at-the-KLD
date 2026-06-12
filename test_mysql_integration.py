# test_mysql_integration.py
import pymysql
import sys
import os

# Add current directory to path to import modules
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def test_mysql_integration():
    """Comprehensive test for all MySQL-connected modules"""
    print(" Testing MySQL Integration for All Modules")
    print("=" * 60)
    
    # Test Database Connection
    try:
        conn = pymysql.connect(
            host='localhost',
            user='root',           # Change to your MySQL username
            password='',           # Change to your MySQL password
            database='faculty_account',
            charset='utf8mb4',
            cursorclass=pymysql.cursors.DictCursor
        )
        print(" Database Connection: SUCCESS")
    except Exception as e:
        print(f" Database Connection: FAILED - {e}")
        return
    
    results = []
    
    try:
        with conn.cursor() as cursor:
            # Test 1: Check all tables exist
            cursor.execute("SHOW TABLES")
            tables = [list(table.values())[0] for table in cursor.fetchall()]
            required_tables = ['users', 'user_profiles', 'equipment', 'reservations', 'borrow', 'notifications', 'transactions']
            
            missing_tables = [table for table in required_tables if table not in tables]
            if not missing_tables:
                results.append(" All required tables exist")
            else:
                results.append(f" Missing tables: {missing_tables}")
            
            # Test 2: Check table structures
            cursor.execute("SELECT COUNT(*) as count FROM users")
            user_count = cursor.fetchone()['count']
            results.append(f" Users table: {user_count} records")
            
            cursor.execute("SELECT COUNT(*) as count FROM equipment")
            equipment_count = cursor.fetchone()['count']
            results.append(f" Equipment table: {equipment_count} records")
            
            cursor.execute("SELECT COUNT(*) as count FROM reservations")
            reservation_count = cursor.fetchone()['count']
            results.append(f" Reservations table: {reservation_count} records")
            
            cursor.execute("SELECT COUNT(*) as count FROM notifications")
            notification_count = cursor.fetchone()['count']
            results.append(f" Notifications table: {notification_count} records")
            
            # Test 3: Test Notification Manager
            try:
                from notification_manager import NotificationManager
                nm = NotificationManager()
                test_conn = nm.get_connection()
                if test_conn:
                    results.append(" Notification Manager: Connection OK")
                    test_conn.close()
                else:
                    results.append(" Notification Manager: Connection failed")
            except Exception as e:
                results.append(f" Notification Manager: {str(e)}")
            
            # Test 4: Test User Management
            try:
                from usermanagement import get_db_connection
                user_conn = get_db_connection()
                if user_conn:
                    results.append(" User Management: Connection OK")
                    user_conn.close()
                else:
                    results.append(" User Management: Connection failed")
            except Exception as e:
                results.append(f" User Management: {str(e)}")
            
            # Test 5: Test Reports Module
            try:
                from reports import ReportManager
                rm = ReportManager()
                test_df = rm.get_equipment_utilization()
                results.append(f" Reports Module: {len(test_df)} equipment items")
            except Exception as e:
                results.append(f" Reports Module: {str(e)}")
            
            # Test 6: Check sample data integrity
            cursor.execute("""
                SELECT u.email, p.full_name, p.department 
                FROM users u 
                LEFT JOIN user_profiles p ON u.id = p.user_id 
                LIMIT 3
            """)
            sample_users = cursor.fetchall()
            if sample_users:
                results.append(" User data integrity: OK")
            else:
                results.append("  User data: No sample data found")
            
            # Test 7: Check equipment data
            cursor.execute("SELECT name, available_quantity FROM equipment LIMIT 3")
            sample_equipment = cursor.fetchall()
            if sample_equipment:
                results.append(" Equipment data integrity: OK")
            else:
                results.append("  Equipment data: No sample data found")
        
        conn.close()
        
    except Exception as e:
        results.append(f" Database operations failed: {e}")
    
    # Print results
    print("\n TEST RESULTS:")
    print("-" * 40)
    for result in results:
        print(f"  {result}")
    
    print("-" * 40)
    
    # Summary
    success_count = sum(1 for r in results if r.startswith("success"))
    warning_count = sum(1 for r in results if r.startswith("warning"))
    error_count = sum(1 for r in results if r.startswith("error"))
    total_count = len(results)
    
    print(f"\n SUMMARY:")
    print(f"   Successful: {success_count}/{total_count}")
    print(f"   Warnings: {warning_count}")
    print(f"   Errors: {error_count}")
    
    if error_count == 0:
        print(" All MySQL modules are working correctly!")
    else:
        print(" Some modules need attention. Check the errors above.")

if __name__ == "__main__":
    test_mysql_integration()