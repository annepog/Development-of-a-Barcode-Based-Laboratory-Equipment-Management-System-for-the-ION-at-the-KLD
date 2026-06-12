# admin_reservations.py
import tkinter as tk
from tkinter import messagebox
from datetime import datetime
from notification_manager import NotificationManager
from PIL import Image, ImageTk, ImageEnhance
import pymysql  # Changed from sqlite3 to pymysql
import time


# MySQL connection function
def get_db_connection():
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

# Simple retry function for database operations
def execute_with_retry(query, params=(), max_retries=3):
    for attempt in range(max_retries):
        try:
            conn = get_db_connection()
            if conn is None:
                return None
                
            cursor = conn.cursor()
            cursor.execute(query, params)
            
            if query.strip().upper().startswith('SELECT'):
                result = cursor.fetchall()
                conn.close()
                return result
            else:
                conn.commit()
                conn.close()
                return True
                
        except pymysql.OperationalError as e:  # Changed: sqlite3.OperationalError to pymysql.OperationalError
            if "locked" in str(e) and attempt < max_retries - 1:
                time.sleep(0.5)  # Wait half second before retry
                continue
            else:
                raise e
        except Exception as e:
            raise e

def auto_reject_conflicting_reservations(approved_reservation_id, equipment_id, date_needed):
    """Automatically reject other reservations for the same equipment on the same date"""
    try:
        conn = get_db_connection()
        if conn is None:
            return
            
        cursor = conn.cursor()
        
        # Get the approved reservation details
        cursor.execute("""
            SELECT user_email, date_needed, duration 
            FROM reservations 
            WHERE reservation_id = %s
        """, (approved_reservation_id,))  # CHANGED: ? to %s
        approved_res = cursor.fetchone()
        
        if not approved_res:
            return
        
        approved_user = approved_res['user_email']  # CHANGED: Access by column name
        approved_date = approved_res['date_needed']
        approved_duration = approved_res['duration']
        
        # Find conflicting reservations (same equipment, same date, different user, pending status)
        cursor.execute("""
            SELECT reservation_id, user_email 
            FROM reservations 
            WHERE equipment_id = %s 
            AND date_needed = %s 
            AND reservation_id != %s 
            AND status = 'Pending'
        """, (equipment_id, approved_date, approved_reservation_id))  # CHANGED: ? to %s
        
        conflicting_reservations = cursor.fetchall()
        
        notif_manager = NotificationManager()
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        for res in conflicting_reservations:
            res_id = res['reservation_id']  # CHANGED: Access by column name
            user_email = res['user_email']
            
            # Reject the conflicting reservation
            cursor.execute("""
                UPDATE reservations 
                SET status = 'Rejected', updated_at = %s
                WHERE reservation_id = %s
            """, (timestamp, res_id))  # CHANGED: ? to %s
            
            # Send notification to the user
            cursor.execute("SELECT name FROM equipment WHERE id = %s", (equipment_id,))  # CHANGED: ? to %s
            equipment_result = cursor.fetchone()
            equipment_name = equipment_result['name'] if equipment_result else "Equipment"
            
            notif_manager.create_notification(
                recipient_email=user_email,
                message=f"Your reservation for {equipment_name} on {approved_date} has been automatically rejected because another reservation was approved for the same date.",
                notification_type="reservation_auto_rejected",
                related_id=res_id
            )
            
            print(f"Auto-rejected reservation #{res_id} for {user_email}")
        
        conn.commit()
        conn.close()
        
    except Exception as e:
        print(f"Error in auto_reject_conflicting_reservations: {e}")

def update_equipment_status(equipment_id, status):
    """Update equipment status in the catalog"""
    try:
        conn = get_db_connection()
        if conn is None:
            return
            
        cursor = conn.cursor()
        
        cursor.execute("""
            UPDATE equipment 
            SET availability_status = %s 
            WHERE id = %s
        """, (status, equipment_id))  # CHANGED: ? to %s
        
        conn.commit()
        conn.close()
        print(f"Updated equipment #{equipment_id} status to '{status}'")
        
    except Exception as e:
        print(f"Error updating equipment status: {e}")

def auto_reject_all_pending_individual(equipment_id, approved_reservation_id):
    """Automatically reject ALL other pending reservations for individual items"""
    try:
        conn = get_db_connection()
        if conn is None:
            return
            
        cursor = conn.cursor()
        
        # Get the approved reservation details for notification
        cursor.execute("""
            SELECT user_email, equipment_id 
            FROM reservations 
            WHERE reservation_id = %s
        """, (approved_reservation_id,))  # CHANGED: ? to %s
        approved_res = cursor.fetchone()
        
        if not approved_res:
            return
        
        approved_user = approved_res['user_email']  # CHANGED: Access by column name
        approved_equipment_id = approved_res['equipment_id']
        
        # Find ALL other pending reservations for this individual equipment
        cursor.execute("""
            SELECT reservation_id, user_email 
            FROM reservations 
            WHERE equipment_id = %s 
            AND reservation_id != %s 
            AND status = 'Pending'
        """, (equipment_id, approved_reservation_id))  # CHANGED: ? to %s
        
        conflicting_reservations = cursor.fetchall()
        
        notif_manager = NotificationManager()
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        # Get equipment name for notifications
        cursor.execute("SELECT name FROM equipment WHERE id = %s", (equipment_id,))  # CHANGED: ? to %s
        equipment_result = cursor.fetchone()
        equipment_name = equipment_result['name'] if equipment_result else "Equipment"
        
        for res in conflicting_reservations:
            res_id = res['reservation_id']  # CHANGED: Access by column name
            user_email = res['user_email']
            
            # Reject the conflicting reservation
            cursor.execute("""
                UPDATE reservations 
                SET status = 'Rejected', updated_at = %s
                WHERE reservation_id = %s
            """, (timestamp, res_id))  # CHANGED: ? to %s
            
            # Send notification to the user
            notif_manager.create_notification(
                recipient_email=user_email,
                message=f"Your reservation for {equipment_name} has been automatically rejected because it is an individual item and another reservation was approved.",
                notification_type="reservation_auto_rejected",
                related_id=res_id
            )
            
            print(f"Auto-rejected individual item reservation #{res_id} for {user_email}")
        
        conn.commit()
        conn.close()
        
    except Exception as e:
        print(f"Error in auto_reject_all_pending_individual: {e}")

def update_equipment_after_reservation_completion(reservation_id):
    """Update equipment status when reservation is completed/returned"""
    try:
        conn = get_db_connection()
        if conn is None:
            return
            
        cursor = conn.cursor()
        
        # Get equipment ID and tracking type
        cursor.execute("""
            SELECT r.equipment_id, e.tracking_type 
            FROM reservations r 
            JOIN equipment e ON r.equipment_id = e.id 
            WHERE r.reservation_id = %s
        """, (reservation_id,))  # CHANGED: ? to %s
        
        result = cursor.fetchone()
        if not result:
            return
            
        equipment_id = result['equipment_id']  # CHANGED: Access by column name
        tracking_type = result['tracking_type']
        
        # For individual items, set status back to Available
        if tracking_type == "individual":
            cursor.execute("""
                UPDATE equipment 
                SET availability_status = 'Available' 
                WHERE id = %s
            """, (equipment_id,))  # CHANGED: ? to %s
            conn.commit()
            print(f"Set individual equipment #{equipment_id} back to Available")
        
        conn.close()
        
    except Exception as e:
        print(f"Error updating equipment after reservation completion: {e}")

def get_equipment_id_from_reservation(reservation_id):
    """Get equipment ID from reservation"""
    try:
        conn = get_db_connection()
        if conn is None:
            return None
            
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT equipment_id FROM reservations WHERE reservation_id = %s
        """, (reservation_id,))  # CHANGED: ? to %s
        
        result = cursor.fetchone()
        conn.close()
        
        return result['equipment_id'] if result else None  # CHANGED: Access by column name
        
    except Exception as e:
        print(f"Error getting equipment ID: {e}")
        return None

def approve_reservation(reservation_id, user_email, equipment_name, equipment_id, date_needed):
    """Approve reservation with automatic conflict handling"""
    try:
        # Get equipment tracking type
        result = execute_with_retry("""
            SELECT e.tracking_type, r.quantity 
            FROM equipment e 
            JOIN reservations r ON e.id = r.equipment_id 
            WHERE r.reservation_id = %s
        """, (reservation_id,))  # CHANGED: ? to %s
        
        if not result:
            messagebox.showerror("Error", "Equipment data not found!")
            return
            
        tracking_type = result[0]['tracking_type']  # CHANGED: Access by column name
        reserved_quantity = result[0]['quantity']
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        # Update reservation status
        execute_with_retry("""
            UPDATE reservations 
            SET status = 'Approved', updated_at = %s
            WHERE reservation_id = %s
        """, (timestamp, reservation_id))  # CHANGED: ? to %s
        
        # Handle individual items
        if tracking_type == "individual":
            # Auto-reject other pending reservations
            execute_with_retry("""
                UPDATE reservations 
                SET status = 'Rejected', updated_at = %s
                WHERE equipment_id = %s AND reservation_id != %s AND status = 'Pending'
            """, (timestamp, equipment_id, reservation_id))  # CHANGED: ? to %s
            
            # Update equipment status
            execute_with_retry("""
                UPDATE equipment 
                SET availability_status = 'Reserved' 
                WHERE id = %s
            """, (equipment_id,))  # CHANGED: ? to %s
        
        # Send notification
        notif_manager = NotificationManager()
        notif_manager.create_notification(
            recipient_email=user_email,
            message=f"Your reservation for {equipment_name} has been APPROVED by the custodian.",
            notification_type="reservation_approved",
            related_id=reservation_id
        )
        
        messagebox.showinfo("Success", f"Reservation #{reservation_id} approved!")
        
    except Exception as e:
        messagebox.showerror("Error", f"Failed to approve reservation: {str(e)}")

def complete_reservation(reservation_id, user_email, equipment_name):
    """Mark a reservation as completed and update equipment status"""
    try:
        conn = get_db_connection()
        if conn is None:
            return
            
        cursor = conn.cursor()
        
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        cursor.execute("""
            UPDATE reservations 
            SET status = 'Completed', updated_at = %s
            WHERE reservation_id = %s
        """, (timestamp, reservation_id))  # CHANGED: ? to %s
        
        conn.commit()
        conn.close()
        
        # Update equipment status (set back to Available for individual items)
        update_equipment_after_reservation_completion(reservation_id)
        
        # Send notification
        notif_manager = NotificationManager()
        notif_manager.create_notification(
            recipient_email=user_email,
            message=f"Your reservation for {equipment_name} has been marked as COMPLETED.",
            notification_type="reservation_completed",
            related_id=reservation_id
        )
        
        messagebox.showinfo("Success", f"Reservation #{reservation_id} marked as completed!")
        
    except Exception as e:
        messagebox.showerror("Error", f"Failed to complete reservation: {str(e)}")

def check_and_update_equipment_status(equipment_id):
    """Check if equipment should be set back to Available after reservation period"""
    try:
        conn = get_db_connection()
        if conn is None:
            return
            
        cursor = conn.cursor()
        
        # Check if there are any active reservations for this equipment
        cursor.execute("""
            SELECT COUNT(*) as count FROM reservations 
            WHERE equipment_id = %s AND status = 'Approved'
        """, (equipment_id,))  # CHANGED: ? to %s
        
        result = cursor.fetchone()
        active_reservations = result['count'] if result else 0  # CHANGED: Access by column name
        
        if active_reservations == 0:
            # No active reservations, set status back to Available
            cursor.execute("""
                UPDATE equipment 
                SET availability_status = 'Available' 
                WHERE id = %s AND availability_status = 'Reserved'
            """, (equipment_id,))  # CHANGED: ? to %s
            conn.commit()
            print(f"Reset equipment #{equipment_id} status to 'Available'")
        
        conn.close()
        
    except Exception as e:
        print(f"Error checking equipment status: {e}")

def show_admin_notifications(root, admin_email, back_callback):
    """Display notifications page for admin"""
    for w in root.winfo_children():
        w.destroy()
    
    root.geometry("1920x1080")
    root.configure(bg="#f5f5f5")
    
    # Header with consistent styling
    header_frame = tk.Frame(root, bg="#2c5530", height=80)
    header_frame.pack(fill="x")
    header_frame.pack_propagate(False)
    
    header_content = tk.Frame(header_frame, bg="#2c5530")
    header_content.pack(fill="both", expand=True, padx=20, pady=15)
    
    left_header = tk.Frame(header_content, bg="#2c5530")
    left_header.pack(side="left", fill="y")
    
    try:
        logo_img = Image.open("ion_logo.png").resize((50, 50))
        logo_photo = ImageTk.PhotoImage(logo_img)
        logo_label = tk.Label(left_header, image=logo_photo, bg="#2c5530")
        logo_label.image = logo_photo
        logo_label.pack(side="left", padx=(0, 15))
    except:
        tk.Label(left_header, text="HOSPITAL", font=("Arial", 12, "bold"), 
              bg="white", fg="#2c5530", width=8, height=1).pack(side="left", padx=(0, 15))
    
    tk.Label(left_header, text="Notifications", 
          font=("Helvetica", 18, "bold"), bg="#2c5530", fg="white").pack(side="left")
    
    right_header = tk.Frame(header_content, bg="#2c5530")
    right_header.pack(side="right")
    
    tk.Button(right_header, text="Back", font=("Helvetica", 10),
           bg="white", fg="#2c5530", relief="flat", width=8,
           command=back_callback).pack(side="left", padx=(0, 10))
    
    # Main content with proper layout
    main_content = tk.Frame(root, bg="#f5f5f5")
    main_content.pack(fill="both", expand=True, padx=20, pady=20)
    
    # Content container with scrollbar
    container = tk.Frame(main_content, bg="#f5f5f5")
    container.pack(fill="both", expand=True)
    
    canvas = tk.Canvas(container, bg="#f5f5f5", highlightthickness=0)
    scrollbar = tk.Scrollbar(container, orient="vertical", command=canvas.yview)
    scrollable_frame = tk.Frame(canvas, bg="#f5f5f5")
    
    scrollable_frame.bind(
        "<Configure>",
        lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
    )
    
    canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
    canvas.configure(yscrollcommand=scrollbar.set)
    
    canvas.pack(side="left", fill="both", expand=True)
    scrollbar.pack(side="right", fill="y")
    
    notif_manager = NotificationManager()
    notifications = notif_manager.get_all_notifications(admin_email)

    if not notifications:
        tk.Label(scrollable_frame, text="📭", font=("Arial", 48), bg="#f5f5f5").pack(pady=50)
        tk.Label(scrollable_frame, text="No notifications yet", 
                font=("Arial", 14), bg="#f5f5f5", fg="#666").pack()
    else:
        for notif in notifications:
            notif_id = notif['notification_id']  # CHANGED: Access by column name
            message = notif['message']
            notif_type = notif['notification_type']
            related_id = notif['related_id']
            created_at = notif['created_at']
            is_read = notif['is_read']
            
            # Notification card
            card_frame = tk.Frame(scrollable_frame, bg="#f5f5f5")
            card_frame.pack(fill="x", padx=20, pady=10)
            
            card = tk.Frame(card_frame, bg="white" if is_read else "#fff3cd", 
                           relief="solid", bd=1)
            card.pack(fill="x", padx=10, pady=10)
            
            # Notification content
            content_frame = tk.Frame(card, bg=card["bg"])
            content_frame.pack(fill="x", padx=15, pady=10)
            
            if "approved" in notif_type:
                icon = "✅"
            elif "rejected" in notif_type:
                icon = "❌"
            else:
                icon = "📬"
            
            tk.Label(content_frame, text=icon, font=("Arial", 16), 
                    bg=card["bg"]).pack(side="left", padx=(0, 10))
            
            text_frame = tk.Frame(content_frame, bg=card["bg"])
            text_frame.pack(side="left", fill="x", expand=True)
            
            tk.Label(text_frame, text=message, font=("Arial", 11), 
                    bg=card["bg"], wraplength=600, justify="left").pack(anchor="w")
            tk.Label(text_frame, text=created_at, font=("Arial", 9), 
                    bg=card["bg"], fg="#666").pack(anchor="w")

            if not is_read:
                notif_manager.mark_as_read(notif_id)

def show_admin_reservations(root, back_callback=None, admin_email="admin@nursing.com"):
    """Admin page to view and manage reservations - WITH AUTO-REJECT FEATURE"""
    for w in root.winfo_children():
        w.destroy()
    
    root.geometry("1920x1080")
    root.configure(bg="#f5f5f5")
    
    if back_callback is None:
        back_callback = root.destroy

    # Header with consistent styling
    header_frame = tk.Frame(root, bg="#2c5530", height=80)
    header_frame.pack(fill="x")
    header_frame.pack_propagate(False)
    
    header_content = tk.Frame(header_frame, bg="#2c5530")
    header_content.pack(fill="both", expand=True, padx=20, pady=15)
    
    left_header = tk.Frame(header_content, bg="#2c5530")
    left_header.pack(side="left", fill="y")
    
    try:
        logo_img = Image.open("ion_logo.png").resize((50, 50))
        logo_photo = ImageTk.PhotoImage(logo_img)
        logo_label = tk.Label(left_header, image=logo_photo, bg="#2c5530")
        logo_label.image = logo_photo
        logo_label.pack(side="left", padx=(0, 15))
    except:
        tk.Label(left_header, text="HOSPITAL", font=("Arial", 12, "bold"), 
              bg="white", fg="#2c5530", width=8, height=1).pack(side="left", padx=(0, 15))
    
    tk.Label(left_header, text="Reservation Management", 
          font=("Helvetica", 18, "bold"), bg="#2c5530", fg="white").pack(side="left")
    
    right_header = tk.Frame(header_content, bg="#2c5530")
    right_header.pack(side="right")
    
    def back_to_dashboard():
        from admindashboard import show_admin_dashboard
        show_admin_dashboard(root, admin_email)
    
    tk.Button(right_header, text="Back", font=("Helvetica", 10),
           bg="white", fg="#2c5530", relief="flat", width=8,
           command=back_callback).pack(side="left", padx=(0, 10))
    
    def logout():
        from loginform import show_login_form
        show_login_form(root)
        root.geometry("800x600")
    
    tk.Button(right_header, text="Logout", font=("Helvetica", 10),
           bg="white", fg="#2c5530", relief="flat", width=8,
           command=logout).pack(side="right")

    # Main content area
    main_content = tk.Frame(root, bg="#f5f5f5")
    main_content.pack(fill="both", expand=True, padx=20, pady=20)
    
    # Create a main container that will hold everything
    main_container = tk.Frame(main_content, bg="#f5f5f5")
    main_container.pack(fill="both", expand=True)
    
    # Tabs section
    tabs_section = tk.Frame(main_container, bg="#f5f5f5")
    tabs_section.pack(fill="x", pady=(0, 15))
    
    selected_tab = tk.StringVar(value="Pending")

    def switch_tab(tab_name):
        selected_tab.set(tab_name)
        refresh_reservations()

    # Tab buttons - Added Completed tab
    tabs = ["Pending", "Approved", "Completed", "Rejected"]
    tab_buttons = []
    
    for tab in tabs:
        btn = tk.Button(tabs_section, text=tab, 
                      bg="#005c3c" if selected_tab.get() == tab else "#6c757d",
                      fg="white", font=("Arial", 12, "bold"), 
                      relief="flat", padx=25, pady=12, cursor="hand2",
                      command=lambda t=tab: switch_tab(t))
        btn.pack(side="left", padx=5)
        tab_buttons.append(btn)

    # Stats summary
    stats_frame = tk.Frame(main_container, bg="#e8f5e9", relief="flat", bd=1)
    stats_frame.pack(fill="x", pady=(0, 15))
    
    def update_stats():
        conn = get_db_connection()
        if conn is None:
            return
            
        cursor = conn.cursor()
        
        cursor.execute("SELECT COUNT(*) as count FROM reservations WHERE status = 'Pending'")
        pending_result = cursor.fetchone()
        pending_count = pending_result['count'] if pending_result else 0  # CHANGED: Access by column name
        
        cursor.execute("SELECT COUNT(*) as count FROM reservations WHERE status = 'Approved'")
        approved_result = cursor.fetchone()
        approved_count = approved_result['count'] if approved_result else 0
        
        cursor.execute("SELECT COUNT(*) as count FROM reservations WHERE status = 'Completed'")
        completed_result = cursor.fetchone()
        completed_count = completed_result['count'] if completed_result else 0
        
        cursor.execute("SELECT COUNT(*) as count FROM reservations WHERE status = 'Rejected'")
        rejected_result = cursor.fetchone()
        rejected_count = rejected_result['count'] if rejected_result else 0
        
        conn.close()
        
        stats_text = f"📊 Reservation Summary: {pending_count} Pending • {approved_count} Approved • {completed_count} Completed • {rejected_count} Rejected"
        stats_label.config(text=stats_text)
    
    stats_label = tk.Label(stats_frame, text="", font=("Arial", 11, "bold"), 
                          bg="#e8f5e9", fg="#005c3c", pady=8)
    stats_label.pack()
    update_stats()

    # Scrollable reservations area
    scroll_container = tk.Frame(main_container, bg="#f5f5f5")
    scroll_container.pack(fill="both", expand=True)
    
    # Create canvas and scrollbar
    canvas = tk.Canvas(scroll_container, bg="#f5f5f5", highlightthickness=0)
    scrollbar = tk.Scrollbar(scroll_container, orient="vertical", command=canvas.yview)
    
    # Create scrollable frame
    reservations_frame = tk.Frame(canvas, bg="#f5f5f5")
    
    # Configure canvas scrolling
    reservations_frame.bind(
        "<Configure>",
        lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
    )
    
    canvas.create_window((0, 0), window=reservations_frame, anchor="nw")
    canvas.configure(yscrollcommand=scrollbar.set)
    
    # Pack canvas and scrollbar
    canvas.pack(side="left", fill="both", expand=True, padx=(0, 5))
    scrollbar.pack(side="right", fill="y")
    
    notif_manager = NotificationManager()

    # Notification Bell in header
    notif_frame = tk.Frame(header_content, bg="#2c5530")
    notif_frame.pack(side="right", padx=20)
    
    unread_count = notif_manager.get_unread_count(admin_email)
    
    notif_btn = tk.Button(notif_frame, text="🔔", font=("Arial", 20), 
                          bg="#2c5530", fg="white", border=0, cursor="hand2",
                          command=lambda: show_admin_notifications(root, admin_email, 
                                                                  lambda: show_admin_reservations(root, back_callback, admin_email)))
    notif_btn.pack(side="left")
    
    if unread_count > 0:
        badge = tk.Label(notif_frame, text=str(unread_count), 
                        font=("Arial", 8, "bold"), bg="red", fg="white",
                        width=2, height=1)
        badge.place(x=25, y=0)

    def refresh_reservations():
        # Update tab button colors
        for btn in tab_buttons:
            if btn.cget("text") == selected_tab.get():
                btn.configure(bg="#005c3c")
            else:
                btn.configure(bg="#6c757d")
        
        # Update stats
        update_stats()

        # Clear existing widgets from reservations frame
        for widget in reservations_frame.winfo_children():
            widget.destroy()

        # Get reservations from database - ORDER BY created_at ASC (oldest first)
        conn = get_db_connection()
        if conn is None:
            return
            
        cursor = conn.cursor()
        cursor.execute("""
            SELECT r.reservation_id, r.user_email, e.name, r.quantity, 
                   r.date_needed, r.purpose, r.duration, r.notes, r.status,
                   r.created_at, r.updated_at, r.equipment_id
            FROM reservations r
            JOIN equipment e ON r.equipment_id = e.id
            WHERE r.status = %s
            ORDER BY r.created_at ASC
        """, (selected_tab.get(),))  # CHANGED: ? to %s
        reservations = cursor.fetchall()
        conn.close()

        if not reservations:
            # Empty state
            empty_container = tk.Frame(reservations_frame, bg="#f5f5f5", height=300)
            empty_container.pack(fill="both", expand=True, pady=50)
            empty_container.pack_propagate(False)
            
            tk.Label(empty_container, text="📭", font=("Arial", 48), bg="#f5f5f5").pack(expand=True)
            tk.Label(empty_container, text=f"No {selected_tab.get().lower()} reservations", 
                    font=("Arial", 14), bg="#f5f5f5", fg="#666").pack(pady=10)
            tk.Label(empty_container, text="When new reservations come in, they will appear here", 
                    font=("Arial", 11), bg="#f5f5f5", fg="#999").pack()
        else:
            for res in reservations:
                # CHANGED: Access all values by column name
                res_id = res['reservation_id']
                user_email = res['user_email']
                equip_name = res['name']
                qty = res['quantity']
                date = res['date_needed']
                purpose = res['purpose']
                duration = res['duration']
                notes = res['notes']
                status = res['status']
                created_at = res['created_at']
                updated_at = res['updated_at']
                equipment_id = res['equipment_id']
                
                # Create reservation card
                card_container = tk.Frame(reservations_frame, bg="#f5f5f5")
                card_container.pack(fill="x", padx=10, pady=8)
                
                card = tk.Frame(card_container, bg="white", relief="solid", bd=1)
                card.pack(fill="x", padx=5, pady=5)
                
                # Card content
                content_frame = tk.Frame(card, bg="white")
                content_frame.pack(fill="x", padx=20, pady=15)
                
                # Left side - reservation details
                left_frame = tk.Frame(content_frame, bg="white")
                left_frame.pack(side="left", fill="both", expand=True)
                
                # Equipment name and status
                header_frame = tk.Frame(left_frame, bg="white")
                header_frame.pack(fill="x", pady=(0, 10))
                
                tk.Label(header_frame, text=equip_name, font=("Arial", 14, "bold"), 
                        bg="white", fg="#333").pack(side="left")
                
                # Status badge
                status_color = {
                    "Pending": "#ffc107",
                    "Approved": "#28a745", 
                    "Completed": "#17a2b8",
                    "Rejected": "#dc3545"
                }.get(status, "#6c757d")
                
                status_badge = tk.Label(header_frame, text=status.upper(), 
                                      font=("Arial", 10, "bold"), bg=status_color, fg="white",
                                      padx=12, pady=4)
                status_badge.pack(side="right")
                
                # Reservation details
                details_text = f"• Requested by: {user_email}\n"
                details_text += f"• Date Needed: {date}\n"
                details_text += f"• Duration: {duration}\n"
                details_text += f"• Quantity: {qty}\n"
                details_text += f"• Purpose: {purpose}"
                
                if notes and notes.strip():
                    details_text += f"\n• Notes: {notes}"
                
                tk.Label(left_frame, text=details_text, font=("Arial", 10), 
                        bg="white", fg="#555", justify="left", anchor="w").pack(fill="x")
                
                # Timestamps
                timestamp_frame = tk.Frame(left_frame, bg="white")
                timestamp_frame.pack(fill="x", pady=(10, 0))
                
                timestamp_text = f"Created: {created_at}"
                if updated_at and updated_at != created_at:
                    timestamp_text += f" | Updated: {updated_at}"
                
                tk.Label(timestamp_frame, text=timestamp_text, font=("Arial", 8), 
                        bg="white", fg="#999").pack(anchor="w")
                
                # Right side - action buttons
                right_frame = tk.Frame(content_frame, bg="white")
                right_frame.pack(side="right", padx=(20, 0))
                
                if status == "Pending":
                    def approve(r_id=res_id, email=user_email, eq_name=equip_name, eq_id=equipment_id, need_date=date):
                        approve_reservation(r_id, email, eq_name, eq_id, need_date)
                        refresh_reservations()
                    
                    def reject(r_id=res_id, email=user_email, eq_name=equip_name):
                        try:
                            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                            execute_with_retry("""
                                UPDATE reservations SET status = 'Rejected', updated_at = %s
                                WHERE reservation_id = %s
                            """, (timestamp, r_id))  # CHANGED: ? to %s
                            
                            # Update equipment status if needed
                            update_equipment_after_reservation_completion(r_id)
                            
                            # Send notification
                            notif_manager.create_notification(
                                recipient_email=email,
                                message=f"Your reservation for {eq_name} has been REJECTED by the custodian.",
                                notification_type="reservation_rejected",
                                related_id=r_id
                            )
                            
                            messagebox.showinfo("Success", f"Reservation #{r_id} rejected!")
                            refresh_reservations()
                        except Exception as e:
                            messagebox.showerror("Error", f"Failed to reject reservation: {str(e)}")

                    # Action buttons for Pending
                    tk.Button(right_frame, text="✓ Approve", bg="#28a745", fg="white", 
                             font=("Arial", 11, "bold"), relief="flat", padx=20, pady=8,
                             cursor="hand2", command=approve).pack(pady=5, fill="x")
                    tk.Button(right_frame, text="✗ Reject", bg="#dc3545", fg="white", 
                             font=("Arial", 11, "bold"), relief="flat", padx=20, pady=8,
                             cursor="hand2", command=reject).pack(pady=5, fill="x")
                
                elif status == "Approved":
                    def complete(r_id=res_id, email=user_email, eq_name=equip_name):
                        complete_reservation(r_id, email, eq_name)
                        refresh_reservations()
                    
                    # Complete button for Approved reservations
                    tk.Button(right_frame, text="✓ Complete", bg="#17a2b8", fg="white", 
                             font=("Arial", 11, "bold"), relief="flat", padx=20, pady=8,
                             cursor="hand2", command=complete).pack(pady=5, fill="x")

        # Update the canvas scrollregion
        canvas.update_idletasks()
        canvas.configure(scrollregion=canvas.bbox("all"))

    # Initial load
    refresh_reservations()

# Run directly
def run_admin_reservations_directly():
    """Run the admin reservations page directly without login"""
    root = tk.Tk()
    root.title("Admin Reservations Management")
    root.geometry("1920x1080")
    root.configure(bg="#f5f5f5")
    
    show_admin_reservations(root, back_callback=root.destroy)
    
    root.mainloop()

if __name__ == "__main__":
    run_admin_reservations_directly()