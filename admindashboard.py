import tkinter as tk
from tkinter import Label, Frame, Button, messagebox
import pymysql
from PIL import Image, ImageTk
from datetime import datetime
from admin_reservations import show_admin_reservations
from ereportsmanagement import show_equipment_reports_management
from reports import show_reports_dashboard
from compliance_tracker import show_compliance_dashboard
from notification_manager import NotificationManager
from returnequipment import show_return_screen
import os
import sys

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

def resource_path(relative_path):
    """Get absolute path to resource, works for dev and for PyInstaller"""
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

def show_admin_dashboard(root, admin_email, main_app=None):
    """Display admin dashboard with equipment management features"""
    # Clear window first
    for widget in root.winfo_children():
        widget.destroy()
    
    root.geometry("1920x1080")
    root.configure(bg="#f5f5f5")
    
    # Header frame
    header_frame = Frame(root, bg="#2c5530", height=80)
    header_frame.pack(fill="x")
    header_frame.pack_propagate(False)
    
    # Header content
    header_content = Frame(header_frame, bg="#2c5530")
    header_content.pack(fill="both", expand=True, padx=20, pady=15)
    
    # Left side - logo and title
    left_header = Frame(header_content, bg="#2c5530")
    left_header.pack(side="left", fill="y")
    
    # Logo
    try:
        logo_img = Image.open(resource_path("ion_logo.png")).resize((50, 50))
        logo_photo = ImageTk.PhotoImage(logo_img)
        logo_label = Label(left_header, image=logo_photo, bg="#2c5530")
        logo_label.image = logo_photo
        logo_label.pack(side="left", padx=(0, 15))
    except:
        Label(left_header, text="HOSPITAL", font=("Arial", 12, "bold"), 
              bg="white", fg="#2c5530", width=8, height=1).pack(side="left", padx=(0, 15))
    
    # Title
    Label(left_header, text="Admin Dashboard", 
          font=("Helvetica", 18, "bold"), bg="#2c5530", fg="white").pack(side="left")
    
    # Right side - user info and logout
    right_header = Frame(header_content, bg="#2c5530")
    right_header.pack(side="right")
    
    Label(right_header, text="Welcome, " + admin_email, 
          font=("Helvetica", 10), bg="#2c5530", fg="white").pack(side="left", padx=(0, 15))
    
    # Fixed logout function
    def perform_logout():
        """Logout the user and return to main login page"""
        if messagebox.askyesno("Confirm Logout", "Are you sure you want to logout?"):
            if main_app:
                # Use main_app's logout method
                main_app.logout()
            else:
                # Fallback: direct logout for standalone execution
                root.destroy()
                # Show login window again
                from loginform import LoginForm
                login_root = tk.Tk()
                login_root.title("ION - Laboratory Equipment Management System")
                login_root.geometry("1920x1080")
                login_root.configure(bg='#f8f9fa')
                
                def login_callback(user_data):
                    # Handle login success
                    login_root.destroy()
                    # Restart admin dashboard
                    admin_root = tk.Tk()
                    admin_root.title("Admin Dashboard")
                    admin_root.geometry("1920x1080")
                    show_admin_dashboard(admin_root, user_data.get('email', ''))
                    admin_root.mainloop()
                
                LoginForm(login_root, login_callback)
                login_root.mainloop()
    
    # Logout button
    Button(right_header, text="🚪 Logout", font=("Helvetica", 10),
           bg="white", fg="#2c5530", relief="flat", width=8,
           command=perform_logout).pack(side="right")

    # Main content area
    main_content = Frame(root, bg="#f5f5f5")
    main_content.pack(fill="both", expand=True, padx=20, pady=20)
    
    # Dashboard title
    Label(main_content, text="Dashboard Overview", font=("Helvetica", 16, "bold"),
          bg="#f5f5f5", fg="#333").pack(anchor="w", pady=(0, 20))
    
    # Stats cards frame
    stats_frame = Frame(main_content, bg="#f5f5f5")
    stats_frame.pack(fill="x", pady=(0, 20))
    
    # Get dashboard statistics
    stats = get_dashboard_stats()
    
    # Create stat cards with updated data
    stat_cards_data = [
        ("Total Equipment", stats['total_equipment'], "#2c5530", "All items in inventory"),
        ("Currently Borrowed", stats['borrowed'], "#ff6b35", "Items checked out"),
        ("Available Items", stats['available'], "#28a745", "Ready to borrow"),
        ("Active Users", stats['active_users'], "#007bff", "Registered faculty")
    ]
    
    for i, (label, value, color, subtitle) in enumerate(stat_cards_data):
        card = Frame(stats_frame, bg="white", relief="solid", borderwidth=1)
        card.pack(side="left", fill="both", expand=True, padx=(0, 10 if i < 3 else 0), pady=5)
        
        Label(card, text=str(value), font=("Helvetica", 28, "bold"),
              bg="white", fg=color).pack(pady=(20, 5))
        
        Label(card, text=label, font=("Helvetica", 11, "bold"),
              bg="white", fg="#333").pack(pady=(0, 2))
        
        Label(card, text=subtitle, font=("Helvetica", 9),
              bg="white", fg="#999").pack(pady=(0, 15))
    
    # Content sections
    content_frame = Frame(main_content, bg="#f5f5f5")
    content_frame.pack(fill="both", expand=True)
    
    # Left section - Recent Transactions
    left_section = Frame(content_frame, bg="#f5f5f5")
    left_section.pack(side="left", fill="both", expand=True, padx=(0, 10))
    
    create_transactions_section(left_section)
    
    # Middle section - Reservation Notifications
    middle_section = Frame(content_frame, bg="#f5f5f5")
    middle_section.pack(side="left", fill="both", expand=True, padx=10)
    
    create_reservations_section(middle_section, root, admin_email)
    
    # Right section - Quick Actions
    right_section = Frame(content_frame, bg="#f5f5f5", width=300)
    right_section.pack(side="right", fill="y")
    right_section.pack_propagate(False)
    
    create_quick_actions_section(right_section, root, admin_email)

def create_quick_actions_section(parent, root, admin_email):
    """Create quick actions section with functional buttons"""
    actions_frame = Frame(parent, bg="white", relief="solid", borderwidth=1)
    actions_frame.pack(fill="x", pady=(0, 10))
    
    # Header
    header = Frame(actions_frame, bg="#f8f9fa", height=50)
    header.pack(fill="x")
    header.pack_propagate(False)
    
    Label(header, text="Quick Actions", font=("Helvetica", 13, "bold"),
          bg="#f8f9fa", fg="#333").pack(anchor="w", padx=20, pady=15)
    
    # Actions
    actions_content = Frame(actions_frame, bg="white")
    actions_content.pack(fill="x", padx=20, pady=15)
    
    # Define action button functions
    def manage_equipment():
        try:
            from equipmentmanagement import show_equipment_management
            show_equipment_management(root, admin_email)
        except ImportError as e:
            messagebox.showerror("Error", f"Equipment management module not found: {str(e)}")
    
    def manage_users():
        try:
            from usermanagement import show_user_management
            show_user_management(root, admin_email)
        except ImportError as e:
            messagebox.showerror("Error", f"User management module not found: {str(e)}")
    
    def generate_reports():
        show_reports_dashboard(root)
    
    def equipment_report_management():
        show_equipment_reports_management(root, admin_email)
        
    def show_compliance():
        show_compliance_dashboard(root, admin_email)
    
    def return_equipment():
        """Navigate to return equipment screen"""
        show_return_screen(root, lambda: show_admin_dashboard(root, admin_email), admin_email)
    
    def manage_reservations():
        """Navigate to reservation management"""
        show_admin_reservations(root, lambda: show_admin_dashboard(root, admin_email), admin_email)
    
    # Action buttons with functionality
    actions = [
        ("Manage Equipment", "#007bff", manage_equipment, "Add, edit, or remove equipment"),
        ("Manage Users", "#28a745", manage_users, "User accounts and permissions"),
        ("Manage Reservations", "#9b59b6", manage_reservations, "Approve or reject reservations"),
        ("Return Equipment", "#e74c3c", return_equipment, "Process equipment returns"),
        ("View Analytics", "#ffc107", generate_reports, "View system reports and analytics"),
        ("Equipment Reports", "#dc3545", equipment_report_management, "Damage and replacement reports"),
        ("Compliance Dashboard", "#2c5530", show_compliance, "Track faculty compliance and replacements")
    ]
    
    for action_text, color, command, subtitle in actions:
        btn_container = Frame(actions_content, bg="white")
        btn_container.pack(fill="x", pady=4)
        
        btn = Button(btn_container, text=action_text, font=("Helvetica", 10, "bold"),
                    bg=color, fg="white", relief="flat", anchor="w",
                    pady=10, command=command)
        btn.pack(fill="x", side="top")
        
        Label(btn_container, text=subtitle, font=("Helvetica", 8),
              bg="white", fg="#999", anchor="w").pack(fill="x", padx=5)

def create_reservations_section(parent, root, admin_email):
    """Create reservations section showing pending reservations"""
    reservations_frame = Frame(parent, bg="white", relief="solid", borderwidth=1)
    reservations_frame.pack(fill="both", expand=True)
    
    # Header
    header = Frame(reservations_frame, bg="#f8f9fa", height=50)
    header.pack(fill="x")
    header.pack_propagate(False)
    
    Label(header, text="📋 Pending Reservations", font=("Helvetica", 13, "bold"),
          bg="#f8f9fa", fg="#333").pack(side="left", anchor="w", padx=20, pady=15)
    
    # Header buttons frame
    header_buttons = Frame(header, bg="#f8f9fa")
    header_buttons.pack(side="right", padx=20, pady=15)
    
    def view_all_reservations():
        show_admin_reservations(root, lambda: show_admin_dashboard(root, admin_email), admin_email)
    
    # View All button
    Button(header_buttons, text="View All", font=("Helvetica", 9),
           bg="#9b59b6", fg="white", relief="flat", padx=12, pady=5,
           command=view_all_reservations).pack(side="left", padx=5)
    
    # Refresh button
    def refresh_reservations():
        for widget in parent.winfo_children():
            widget.destroy()
        create_reservations_section(parent, root, admin_email)
    
    Button(header_buttons, text="Refresh", font=("Helvetica", 9),
           bg="#007bff", fg="white", relief="flat", padx=12, pady=5,
           command=refresh_reservations).pack(side="left", padx=5)
    
    # Content with scrollbar
    content_container = Frame(reservations_frame, bg="white")
    content_container.pack(fill="both", expand=True)
    
    canvas = tk.Canvas(content_container, bg="white", highlightthickness=0)
    scrollbar = tk.Scrollbar(content_container, orient="vertical", command=canvas.yview)
    content = Frame(canvas, bg="white")
    
    content.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
    canvas.create_window((0, 0), window=content, anchor="nw")
    canvas.configure(yscrollcommand=scrollbar.set)
    
    canvas.pack(side="left", fill="both", expand=True)
    scrollbar.pack(side="right", fill="y")
    
    # Mousewheel scrolling
    def on_mousewheel(event):
        canvas.yview_scroll(int(-1*(event.delta/120)), "units")
    
    canvas.bind("<Enter>", lambda e: canvas.bind_all("<MouseWheel>", on_mousewheel))
    canvas.bind("<Leave>", lambda e: canvas.unbind_all("<MouseWheel>"))
    
    # Get pending reservations
    try:
        conn = get_db_connection()
        if conn is None:
            return
            
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT r.reservation_id, r.user_email, e.name, r.quantity, 
                   r.date_needed, r.purpose, r.duration, r.created_at
            FROM reservations r
            JOIN equipment e ON r.equipment_id = e.id
            WHERE r.status = 'Pending'
            ORDER BY r.created_at ASC
            LIMIT 5
        """)
        reservations = cursor.fetchall()
        conn.close()
        
        if not reservations:
            Label(content, text="No pending reservations", font=("Helvetica", 11),
                  bg="white", fg="#999").pack(pady=50)
        else:
            for res in reservations:
                res_id = res['reservation_id']
                user_email = res['user_email']
                equip_name = res['name']
                qty = res['quantity']
                date_needed = res['date_needed']
                purpose = res['purpose']
                duration = res['duration']
                created_at = res['created_at']
                
                # Reservation card
                res_card = Frame(content, bg="white", relief="solid", borderwidth=1)
                res_card.pack(fill="x", padx=15, pady=5)
                
                card_content = Frame(res_card, bg="white")
                card_content.pack(fill="x", padx=12, pady=10)
                
                # Left side - Reservation info
                left_side = Frame(card_content, bg="white")
                left_side.pack(side="left", fill="x", expand=True)
                
                # Top row - Equipment and user
                info_row = Frame(left_side, bg="white")
                info_row.pack(fill="x", anchor="w")
                
                Label(info_row, text=equip_name, font=("Helvetica", 10, "bold"),
                      bg="white", fg="#212529").pack(side="left")
                
                Label(info_row, text=" • ", font=("Helvetica", 10),
                      bg="white", fg="#adb5bd").pack(side="left")
                
                Label(info_row, text=f"Qty: {qty}", font=("Helvetica", 10),
                      bg="white", fg="#495057").pack(side="left")
                
                # Middle row - User and purpose
                Label(left_side, text=f"By: {user_email}", font=("Helvetica", 9),
                      bg="white", fg="#666").pack(anchor="w", pady=(2, 0))
                
                Label(left_side, text=f"For: {purpose}", font=("Helvetica", 9),
                      bg="white", fg="#666", wraplength=200).pack(anchor="w", pady=(0, 2))
                
                # Bottom row - Date needed
                Label(left_side, text=f"Needed: {date_needed}", font=("Helvetica", 8),
                      bg="white", fg="#6c757d").pack(anchor="w", pady=(3, 0))
                
                # Right side - Quick action buttons
                right_side = Frame(card_content, bg="white")
                right_side.pack(side="right", padx=(10, 0))
                
                notif_manager = NotificationManager()
                
                def approve_reservation():
                    from admin_reservations import approve_reservation, get_equipment_id_from_reservation
                    equipment_id = get_equipment_id_from_reservation(res_id)
                    if equipment_id:
                        approve_reservation(res_id, user_email, equip_name, equipment_id, date_needed)
                        refresh_reservations()
                
                def reject_reservation():
                    conn = get_db_connection()
                    if conn is None:
                        return
                        
                    cursor = conn.cursor()
                    
                    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    cursor.execute("""
                        UPDATE reservations SET status = 'Rejected', updated_at = %s
                        WHERE reservation_id = %s
                    """, (timestamp, res_id))
                    
                    conn.commit()
                    conn.close()
                    
                    # Send notification
                    notif_manager.create_notification(
                        recipient_email=user_email,
                        message=f"Your reservation for {equip_name} has been REJECTED by the custodian.",
                        notification_type="reservation_rejected",
                        related_id=res_id
                    )
                    
                    messagebox.showinfo("Success", f"Reservation #{res_id} rejected!")
                    refresh_reservations()
                
                # Quick action buttons
                Button(right_side, text="✓", font=("Helvetica", 10, "bold"),
                       bg="#28a745", fg="white", relief="flat", width=3, height=1,
                       command=approve_reservation).pack(side="left", padx=2)
                
                Button(right_side, text="✗", font=("Helvetica", 10, "bold"),
                       bg="#dc3545", fg="white", relief="flat", width=3, height=1,
                       command=reject_reservation).pack(side="left", padx=2)
                  
    except pymysql.Error as e:
        print(f"Reservations error: {e}")
        Label(content, text="Error loading reservations", font=("Helvetica", 11),
              bg="white", fg="#dc3545").pack(pady=50)

def get_dashboard_stats():
    """Get accurate dashboard statistics from database based on equipment table"""
    try:
        conn = get_db_connection()
        if conn is None:
            return {
                'total_equipment': 0, 
                'borrowed': 0, 
                'available': 0, 
                'active_users': 0,
                'pending_reservations': 0
            }
            
        cursor = conn.cursor()
        
        # Total equipment (count all non-archived equipment items)
        cursor.execute("SELECT COUNT(*) as count FROM equipment WHERE COALESCE(is_archived, 0) = 0")
        total_result = cursor.fetchone()
        total_equipment = total_result['count'] if total_result else 0
        
        # Currently borrowed - count equipment where availability_status = 'Borrowed'
        cursor.execute("""
            SELECT COUNT(*) as count FROM equipment 
            WHERE availability_status = 'Borrowed' 
            AND COALESCE(is_archived, 0) = 0
        """)
        borrowed_result = cursor.fetchone()
        borrowed = borrowed_result['count'] if borrowed_result else 0
        
        # Available equipment - count equipment where availability_status = 'Available'
        cursor.execute("""
            SELECT COUNT(*) as count FROM equipment 
            WHERE availability_status = 'Available' 
            AND COALESCE(is_archived, 0) = 0
        """)
        available_result = cursor.fetchone()
        available = available_result['count'] if available_result else 0
        
        # Active users (not archived)
        cursor.execute("""
            SELECT COUNT(*) as count FROM user_profiles 
            WHERE COALESCE(is_archived, 0) = 0
        """)
        users_result = cursor.fetchone()
        active_users = users_result['count'] if users_result else 0
        
        # Pending reservations
        cursor.execute("SELECT COUNT(*) as count FROM reservations WHERE status = 'Pending'")
        pending_result = cursor.fetchone()
        pending_reservations = pending_result['count'] if pending_result else 0
        
        conn.close()
        
        print(f"DEBUG STATS: Total={total_equipment}, Borrowed={borrowed}, Available={available}")
        
        return {
            'total_equipment': total_equipment,
            'borrowed': borrowed,
            'available': available,
            'active_users': active_users,
            'pending_reservations': pending_reservations
        }
        
    except pymysql.Error as e:
        print(f"Database error: {e}")
        return {
            'total_equipment': 0, 
            'borrowed': 0, 
            'available': 0, 
            'active_users': 0,
            'pending_reservations': 0
        }

def create_transactions_section(parent):
    """Create recent transactions section with compact card design"""
    trans_frame = Frame(parent, bg="white", relief="solid", borderwidth=1)
    trans_frame.pack(fill="both", expand=True)
    
    # Header
    header = Frame(trans_frame, bg="#f8f9fa", height=50)
    header.pack(fill="x")
    header.pack_propagate(False)
    
    Label(header, text="🔄 Recent Logs", font=("Helvetica", 13, "bold"),
          bg="#f8f9fa", fg="#333").pack(side="left", anchor="w", padx=20, pady=15)
    
    # Refresh button
    def refresh_transactions():
        for widget in parent.winfo_children():
            widget.destroy()
        create_transactions_section(parent)
    
    Button(header, text="Refresh", font=("Helvetica", 9),
           bg="#007bff", fg="white", relief="flat", padx=12, pady=5,
           command=refresh_transactions).pack(side="right", padx=20, pady=15)
    
    # Content with scrollbar
    content_container = Frame(trans_frame, bg="white")
    content_container.pack(fill="both", expand=True)
    
    canvas = tk.Canvas(content_container, bg="white", highlightthickness=0)
    scrollbar = tk.Scrollbar(content_container, orient="vertical", command=canvas.yview)
    content = Frame(canvas, bg="white")
    
    content.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
    canvas.create_window((0, 0), window=content, anchor="nw")
    canvas.configure(yscrollcommand=scrollbar.set)
    
    canvas.pack(side="left", fill="both", expand=True)
    scrollbar.pack(side="right", fill="y")
    
    # Mousewheel scrolling
    def on_mousewheel(event):
        canvas.yview_scroll(int(-1*(event.delta/120)), "units")
    
    canvas.bind("<Enter>", lambda e: canvas.bind_all("<MouseWheel>", on_mousewheel))
    canvas.bind("<Leave>", lambda e: canvas.unbind_all("<MouseWheel>"))
    
    # Get recent transactions
    try:
        conn = get_db_connection()
        if conn is None:
            return
            
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT 
                datetime, 
                borrower_name, 
                equipment_name, 
                action, 
                status,
                COALESCE(quantity, 1) as quantity,
                handled_by
            FROM transactions 
            ORDER BY datetime DESC 
            LIMIT 15
        """)
        transactions = cursor.fetchall()
        conn.close()
        
        if transactions:
            for trans in transactions:
                datetime_str = trans['datetime']
                borrower_name = trans['borrower_name']
                equipment_name = trans['equipment_name']
                action = trans['action']
                status = trans['status']
                quantity = trans['quantity']
                handled_by = trans['handled_by']
                
                # Compact card with horizontal layout
                trans_card = Frame(content, bg="white", relief="solid", borderwidth=1)
                trans_card.pack(fill="x", padx=15, pady=5)
                
                card_content = Frame(trans_card, bg="white")
                card_content.pack(fill="x", padx=12, pady=10)
                
                # Left side - Main info
                left_side = Frame(card_content, bg="white")
                left_side.pack(side="left", fill="x", expand=True)
                
                # Top row - Borrower name and equipment
                info_row = Frame(left_side, bg="white")
                info_row.pack(fill="x", anchor="w")
                
                Label(info_row, text=borrower_name, font=("Helvetica", 10, "bold"),
                      bg="white", fg="#212529").pack(side="left")
                
                Label(info_row, text=" • ", font=("Helvetica", 10),
                      bg="white", fg="#adb5bd").pack(side="left")
                
                equipment_text = equipment_name
                if quantity > 1:
                    equipment_text += f" (×{quantity})"
                
                Label(info_row, text=equipment_text, font=("Helvetica", 10),
                      bg="white", fg="#495057").pack(side="left")
                
                # Middle row - Date/time
                if len(datetime_str) >= 16:
                    try:
                        dt = datetime.strptime(datetime_str[:16], "%Y-%m-%d %H:%M")
                        formatted_date = dt.strftime("%b %d, %Y at %I:%M %p")
                    except:
                        formatted_date = datetime_str[:16]
                else:
                    formatted_date = datetime_str
                
                Label(left_side, text=formatted_date, font=("Helvetica", 8),
                      bg="white", fg="#6c757d").pack(anchor="w", pady=(3, 0))
                
                # Bottom row - Handled by (if available)
                if handled_by and handled_by != "System":
                    Label(left_side, text=f"By: {handled_by}", font=("Helvetica", 8),
                          bg="white", fg="#6c757d").pack(anchor="w", pady=(1, 0))
                
                # Right side - Badges
                right_side = Frame(card_content, bg="white")
                right_side.pack(side="right", padx=(10, 0))
                
                # Action badge
                action_text = action
                if action_text == "Borrowed":
                    action_color = "#007bff"
                elif action_text == "Returned":
                    action_color = "#28a745"
                else:
                    action_color = "#6c757d"
                
                Label(right_side, text=action_text, font=("Helvetica", 9, "bold"),
                      bg=action_color, fg="white", padx=12, pady=5).pack(side="left", padx=3)
        
        else:
            Label(content, text="No recent transactions", font=("Helvetica", 11),
                  bg="white", fg="#999").pack(pady=50)
                  
    except pymysql.Error as e:
        print(f"Transaction error: {e}")
        Label(content, text="Error loading transactions", font=("Helvetica", 11),
              bg="white", fg="#dc3545").pack(pady=50)

# Remove the standalone execution to force using MainApp
# if __name__ == "__main__":
#     root = tk.Tk()
#     root.title("Admin Dashboard")
#     root.geometry("1920x1080")
#     show_admin_dashboard(root, "admin@nursing.com")
#     root.mainloop()