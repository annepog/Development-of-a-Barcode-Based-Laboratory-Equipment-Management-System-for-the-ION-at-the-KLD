# notification_manager.py - CLEAN VERSION
import pymysql
from datetime import datetime


class NotificationManager:
    """Manages all notification operations with MySQL backend"""
    
    def __init__(self):
        pass
    
    def get_connection(self):
        """Get MySQL database connection - SERVER SIDE"""
        try:
            conn = pymysql.connect(
                host='localhost',
                user='root',           # or your MySQL username
                password='',           # no password
                database='faculty_account',
                charset='utf8mb4',
                cursorclass=pymysql.cursors.DictCursor
            )
            return conn
        except Exception as e:
            print(f"Database connection failed: {e}")
            return None
    
    def create_notification(self, recipient_email, message, notification_type, related_id=None):
        """Create a new notification"""
        conn = self.get_connection()
        if conn is None:
            print("Failed to create notification: Database connection failed")
            return None
            
        cursor = conn.cursor()
        
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        try:
            cursor.execute("""
                INSERT INTO notifications (recipient_email, message, notification_type, related_id, created_at, is_read)
                VALUES (%s, %s, %s, %s, %s, 0)
            """, (recipient_email, message, notification_type, related_id, timestamp))
            
            conn.commit()
            notification_id = cursor.lastrowid
            print(f"Notification created (ID: {notification_id}) for {recipient_email}")
            return notification_id
            
        except Exception as e:
            print(f"Error creating notification: {e}")
            conn.rollback()
            return None
        finally:
            conn.close()
    
    def get_unread_count(self, recipient_email):
        """Get count of unread notifications"""
        conn = self.get_connection()
        if conn is None:
            return 0
            
        cursor = conn.cursor()
        
        try:
            cursor.execute("""
                SELECT COUNT(*) as count FROM notifications
                WHERE recipient_email = %s AND is_read = 0
            """, (recipient_email,))
            
            result = cursor.fetchone()
            count = result['count'] if result else 0
            return count
            
        except Exception as e:
            print(f"Error getting unread count: {e}")
            return 0
        finally:
            conn.close()
    
    def get_all_notifications(self, recipient_email, limit=None):
        """Get all notifications for a user (with optional limit) - RETURNS TUPLES"""
        conn = self.get_connection()
        if conn is None:
            return []
            
        cursor = conn.cursor()
        
        try:
            query = """
                SELECT notification_id, message, notification_type, related_id, created_at, is_read
                FROM notifications
                WHERE recipient_email = %s
                ORDER BY created_at DESC
            """
            
            params = [recipient_email]
            
            if limit:
                query += " LIMIT %s"
                params.append(limit)
            
            cursor.execute(query, params)
            notifications = cursor.fetchall()
            
            # Convert to list of tuples for compatibility with existing code
            formatted_notifications = []
            for notif in notifications:
                # Access as dictionary and convert to tuple
                formatted_notifications.append((
                    notif['notification_id'],      # index 0
                    notif['message'],              # index 1
                    notif['notification_type'],    # index 2
                    notif['related_id'],           # index 3
                    notif['created_at'],           # index 4
                    bool(notif['is_read'])         # index 5
                ))
            
            return formatted_notifications
            
        except Exception as e:
            print(f"Error getting notifications: {e}")
            return []
        finally:
            conn.close()
    
    def get_all_notifications_as_dicts(self, recipient_email, limit=None):
        """Alternative method that returns dictionaries instead of tuples"""
        conn = self.get_connection()
        if conn is None:
            return []
            
        cursor = conn.cursor()
        
        try:
            query = """
                SELECT notification_id, message, notification_type, related_id, created_at, is_read
                FROM notifications
                WHERE recipient_email = %s
                ORDER BY created_at DESC
            """
            
            params = [recipient_email]
            
            if limit:
                query += " LIMIT %s"
                params.append(limit)
            
            cursor.execute(query, params)
            notifications = cursor.fetchall()
            
            # Return as list of dictionaries
            return notifications
            
        except Exception as e:
            print(f"Error getting notifications: {e}")
            return []
        finally:
            conn.close()
    
    def mark_as_read(self, notification_id):
        """Mark notification as read"""
        conn = self.get_connection()
        if conn is None:
            return False
            
        cursor = conn.cursor()
        
        try:
            cursor.execute("""
                UPDATE notifications SET is_read = 1 WHERE notification_id = %s
            """, (notification_id,))
            
            conn.commit()
            success = cursor.rowcount > 0
            
            if success:
                print(f"Notification {notification_id} marked as read")
            else:
                print(f"Notification {notification_id} not found")
                
            return success
            
        except Exception as e:
            print(f"Error marking notification as read: {e}")
            conn.rollback()
            return False
        finally:
            conn.close()
    
    def mark_all_as_read(self, recipient_email):
        """Mark all notifications as read for a user"""
        conn = self.get_connection()
        if conn is None:
            return 0
            
        cursor = conn.cursor()
        
        try:
            cursor.execute("""
                UPDATE notifications SET is_read = 1 
                WHERE recipient_email = %s AND is_read = 0
            """, (recipient_email,))
            
            conn.commit()
            updated_count = cursor.rowcount
            print(f"Marked {updated_count} notifications as read for {recipient_email}")
            return updated_count
            
        except Exception as e:
            print(f"Error marking all notifications as read: {e}")
            conn.rollback()
            return 0
        finally:
            conn.close()
    
    def delete_notification(self, notification_id):
        """Delete a specific notification"""
        conn = self.get_connection()
        if conn is None:
            return False
            
        cursor = conn.cursor()
        
        try:
            cursor.execute("DELETE FROM notifications WHERE notification_id = %s", (notification_id,))
            conn.commit()
            success = cursor.rowcount > 0
            
            if success:
                print(f"Notification {notification_id} deleted")
            else:
                print(f"Notification {notification_id} not found")
                
            return success
            
        except Exception as e:
            print(f"Error deleting notification: {e}")
            conn.rollback()
            return False
        finally:
            conn.close()
    
    def clear_all_notifications(self, recipient_email):
        """Clear all notifications for a user"""
        conn = self.get_connection()
        if conn is None:
            return 0
            
        cursor = conn.cursor()
        
        try:
            cursor.execute("DELETE FROM notifications WHERE recipient_email = %s", (recipient_email,))
            conn.commit()
            deleted_count = cursor.rowcount
            print(f"Cleared {deleted_count} notifications for {recipient_email}")
            return deleted_count
            
        except Exception as e:
            print(f"Error clearing notifications: {e}")
            conn.rollback()
            return 0
        finally:
            conn.close()
    
    def notify_reservation_created(self, reservation_id, equipment_name, faculty_email):
        """Send notifications when reservation is created"""
        # Notify faculty
        faculty_notif_id = self.create_notification(
            recipient_email=faculty_email,
            message=f"Your reservation for {equipment_name} has been submitted. Waiting for custodian approval.",
            notification_type="reservation_submitted",
            related_id=reservation_id
        )
        
        # Notify admin
        admin_notif_id = self.create_notification(
            recipient_email="admin@nursing.com",
            message=f"New reservation request for {equipment_name} from {faculty_email}",
            notification_type="new_reservation",
            related_id=reservation_id
        )
        
        return faculty_notif_id, admin_notif_id
    
    def notify_reservation_approved(self, reservation_id, equipment_name, faculty_email):
        """Send notification when reservation is approved"""
        return self.create_notification(
            recipient_email=faculty_email,
            message=f"Great news! Your reservation for {equipment_name} has been approved. You can now collect the equipment.",
            notification_type="reservation_approved",
            related_id=reservation_id
        )
    
    def notify_reservation_rejected(self, reservation_id, equipment_name, faculty_email, reason=None):
        """Send notification when reservation is rejected"""
        message = f"Your reservation for {equipment_name} has been rejected."
        if reason:
            message += f" Reason: {reason}"
        
        return self.create_notification(
            recipient_email=faculty_email,
            message=message,
            notification_type="reservation_rejected",
            related_id=reservation_id
        )
    
    def notify_borrow_approved(self, borrow_id, equipment_name, faculty_email):
        """Send notification when borrow request is approved"""
        return self.create_notification(
            recipient_email=faculty_email,
            message=f"Your borrow request for {equipment_name} has been approved. Equipment is ready for pickup.",
            notification_type="borrow_approved",
            related_id=borrow_id
        )
    
    def notify_borrow_rejected(self, borrow_id, equipment_name, faculty_email, reason=None):
        """Send notification when borrow request is rejected"""
        message = f"Your borrow request for {equipment_name} has been rejected."
        if reason:
            message += f" Reason: {reason}"
        
        return self.create_notification(
            recipient_email=faculty_email,
            message=message,
            notification_type="borrow_rejected",
            related_id=borrow_id
        )
    
    def notify_return_processed(self, return_id, equipment_name, faculty_email):
        """Send notification when equipment return is processed"""
        return self.create_notification(
            recipient_email=faculty_email,
            message=f"Return of {equipment_name} has been processed successfully. Thank you!",
            notification_type="return_processed",
            related_id=return_id
        )
    
    def notify_violation(self, report_id, equipment_name, faculty_email, deadline):
        """Send violation notice notification"""
        return self.create_notification(
            recipient_email=faculty_email,
            message=f"VIOLATION NOTICE: You must replace {equipment_name} by {deadline}. Failure to comply may result in disciplinary action.",
            notification_type="violation_notice",
            related_id=report_id
        )
    
    def notify_equipment_low_stock(self, equipment_name, current_quantity, minimum_quantity):
        """Send notification when equipment stock is low"""
        return self.create_notification(
            recipient_email="admin@nursing.com",
            message=f"LOW STOCK ALERT: {equipment_name} has only {current_quantity} units left (minimum: {minimum_quantity}).",
            notification_type="low_stock",
            related_id=None
        )
    
    def notify_equipment_out_of_stock(self, equipment_name):
        """Send notification when equipment is out of stock"""
        return self.create_notification(
            recipient_email="admin@nursing.com",
            message=f"OUT OF STOCK: {equipment_name} is now out of stock. Please restock immediately.",
            notification_type="out_of_stock",
            related_id=None
        )
    
    def notify_maintenance_due(self, equipment_name, maintenance_date):
        """Send notification when equipment maintenance is due"""
        return self.create_notification(
            recipient_email="admin@nursing.com",
            message=f"MAINTENANCE DUE: {equipment_name} requires maintenance on {maintenance_date}.",
            notification_type="maintenance_due",
            related_id=None
        )
    
    def get_notification_stats(self, recipient_email):
        """Get notification statistics for a user"""
        conn = self.get_connection()
        if conn is None:
            return {"total": 0, "unread": 0, "read": 0}
            
        cursor = conn.cursor()
        
        try:
            # Get total notifications
            cursor.execute("""
                SELECT COUNT(*) as total FROM notifications 
                WHERE recipient_email = %s
            """, (recipient_email,))
            total = cursor.fetchone()['total']
            
            # Get unread notifications
            cursor.execute("""
                SELECT COUNT(*) as unread FROM notifications 
                WHERE recipient_email = %s AND is_read = 0
            """, (recipient_email,))
            unread = cursor.fetchone()['unread']
            
            # Get read notifications
            read_count = total - unread
            
            return {
                "total": total,
                "unread": unread,
                "read": read_count
            }
            
        except Exception as e:
            print(f"Error getting notification stats: {e}")
            return {"total": 0, "unread": 0, "read": 0}
        finally:
            conn.close()
    
    def create_sample_notifications(self, recipient_email):
        """Create sample notifications for testing"""
        sample_notifications = [
            (recipient_email, "Welcome to the Laboratory Equipment System!", "welcome", None),
            (recipient_email, "Your equipment reservation has been submitted for approval", "reservation_submitted", 1),
            (recipient_email, "Your borrow request for Microscope has been approved", "borrow_approved", 2),
            (recipient_email, "Reminder: Equipment return due tomorrow", "reminder", 3),
        ]
        
        created_ids = []
        for notif_data in sample_notifications:
            notif_id = self.create_notification(*notif_data)
            if notif_id:
                created_ids.append(notif_id)
        
        print(f"Created {len(created_ids)} sample notifications for {recipient_email}")
        return created_ids

# Initialize the notification manager
notification_manager = NotificationManager()

# Test function
def test_notification_manager():
    """Test the notification manager functionality"""
    nm = NotificationManager()
    
    # Test connection
    conn = nm.get_connection()
    if conn:
        print("Database connection successful")
        conn.close()
    else:
        print("Database connection failed")
        return False
    
    # Test creating a notification
    test_notif_id = nm.create_notification(
        recipient_email="test@nursing.com",
        message="Test notification - system is working!",
        notification_type="test"
    )
    
    if test_notif_id:
        print(f"Notification created successfully (ID: {test_notif_id})")
        
        # Test getting notifications as tuples
        notifications = nm.get_all_notifications("test@nursing.com")
        print(f"Retrieved {len(notifications)} notifications as tuples")
        
        # Test getting notifications as dictionaries
        notifications_dict = nm.get_all_notifications_as_dicts("test@nursing.com")
        print(f"Retrieved {len(notifications_dict)} notifications as dictionaries")
        
        # Show how to access tuple data
        if notifications:
            print("Tuple access example:")
            for i, notif in enumerate(notifications):
                print(f"  Notification {i+1}:")
                print(f"    ID: {notif[0]}")
                print(f"    Message: {notif[1]}")
                print(f"    Type: {notif[2]}")
                print(f"    Read: {notif[5]}")
        
        # Test marking as read
        if nm.mark_as_read(test_notif_id):
            print("Notification marked as read")
        else:
            print("Failed to mark notification as read")
            
        # Test unread count
        unread_count = nm.get_unread_count("test@nursing.com")
        print(f"Unread count: {unread_count}")
            
        # Test deleting notification
        if nm.delete_notification(test_notif_id):
            print("Notification deleted successfully")
        else:
            print("Failed to delete notification")
    else:
        print("Failed to create test notification")
        return False
    
    print("All notification manager tests passed!")
    return True

if __name__ == "__main__":
    test_notification_manager()