# notifications_page.py
import tkinter as tk
from tkinter import ttk
from notification_manager import NotificationManager
import pymysql

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


def show_notifications_page(root: tk.Tk, user_email, back_callback):
    """Display full notifications page"""
    
    # Clear window
    for w in root.winfo_children():
        w.destroy()
    root.configure(bg="#f5f5f5")
    
    # Initialize notification manager
    notif_manager = NotificationManager()
    
    # Top bar
    top = tk.Frame(root, bg="#005c3c", height=80)
    top.pack(fill="x", side="top")
    
    # Back button
    back_btn = tk.Button(top, text="← Back", bg="#005c3c", fg="white",
                        font=("Arial", 12, "bold"), relief="flat",
                        cursor="hand2", activebackground="#004d32",
                        command=back_callback)
    back_btn.pack(side="left", padx=30, pady=20)
    
    # Title
    tk.Label(top, text="🔔 All Notifications", bg="#005c3c", 
             font=("Arial", 18, "bold"), fg="white").pack(side="left", padx=20)
    
    # Mark all as read button
    def mark_all_read():
        notif_manager.mark_all_as_read(user_email)
        refresh_notifications()
    
    mark_read_btn = tk.Button(top, text="✓ Mark All as Read", bg="#28a745", fg="white",
                             font=("Arial", 10, "bold"), relief="flat",
                             cursor="hand2", activebackground="#218838",
                             padx=15, pady=8, command=mark_all_read)
    mark_read_btn.pack(side="right", padx=30)
    
    # Main content
    main = tk.Frame(root, bg="#f5f5f5")
    main.pack(expand=True, fill="both", padx=60, pady=30)
    
    # Filter tabs
    filter_frame = tk.Frame(main, bg="#f5f5f5")
    filter_frame.pack(fill="x", pady=(0, 20))
    
    selected_filter = tk.StringVar(value="all")
    
    def apply_filter(filter_type):
        selected_filter.set(filter_type)
        refresh_notifications()
    
    # Filter buttons
    filters = [("All", "all"), ("Unread", "unread"), ("Approvals", "approved"), 
               ("Violations", "violation"), ("Pending", "submitted")]
    
    for i, (label, filter_type) in enumerate(filters):
        btn = tk.Button(filter_frame, text=label, bg="white", fg="#005c3c",
                       font=("Arial", 10, "bold"), relief="flat",
                       cursor="hand2", padx=20, pady=8, bd=1,
                       command=lambda ft=filter_type: apply_filter(ft))
        btn.pack(side="left", padx=5)
    
    # Notifications container with scrollbar
    container = tk.Frame(main, bg="white", bd=1, relief="solid")
    container.pack(fill="both", expand=True)
    
    canvas = tk.Canvas(container, bg="white", highlightthickness=0)
    scrollbar = tk.Scrollbar(container, orient="vertical", command=canvas.yview)
    notif_content = tk.Frame(canvas, bg="white")
    
    canvas_window = canvas.create_window((0, 0), window=notif_content, anchor="nw")
    
    def on_frame_configure(event):
        canvas.configure(scrollregion=canvas.bbox("all"))
    
    def on_canvas_configure(event):
        canvas.itemconfig(canvas_window, width=event.width)
    
    notif_content.bind("<Configure>", on_frame_configure)
    canvas.bind("<Configure>", on_canvas_configure)
    canvas.configure(yscrollcommand=scrollbar.set)
    
    # Mousewheel scrolling
    def on_mousewheel(event):
        canvas.yview_scroll(int(-1*(event.delta/120)), "units")
    
    canvas.bind_all("<MouseWheel>", on_mousewheel)
    
    canvas.pack(side="left", fill="both", expand=True)
    scrollbar.pack(side="right", fill="y")
    
    def refresh_notifications():
        """Refresh notification list based on filter"""
        # Clear current notifications
        for widget in notif_content.winfo_children():
            widget.destroy()
        
        # Get notifications
        all_notifications = notif_manager.get_all_notifications(user_email)
        
        # Apply filter
        filter_type = selected_filter.get()
        if filter_type == "unread":
            notifications = [n for n in all_notifications if not n[5]]
        elif filter_type == "all":
            notifications = all_notifications
        else:
            notifications = [n for n in all_notifications if filter_type in n[2].lower()]
        
        if not notifications:
            tk.Label(notif_content, text="📭\nNo notifications found", 
                    font=("Arial", 14), bg="white", fg="#999").pack(pady=100)
            return
        
        # Display notifications
        for notif_id, message, notif_type, related_id, created_at, is_read in notifications:
            # Notification card
            bg_color = "#fafafa" if is_read else "#fff9e6"
            
            card = tk.Frame(notif_content, bg=bg_color, bd=0,
                          highlightbackground="#e0e0e0", highlightthickness=1)
            card.pack(fill="x", padx=20, pady=10)
            
            # Icon and styling based on type
            if "violation" in notif_type.lower():
                icon = "⚠️"
                accent_color = "#ff6b6b"
                bg_color = "#fff3cd" if not is_read else "#fafafa"
            elif "approved" in notif_type.lower():
                icon = "✅"
                accent_color = "#4CAF50"
            elif "rejected" in notif_type.lower():
                icon = "❌"
                accent_color = "#f44336"
            else:
                icon = "ℹ️"
                accent_color = "#2196F3"
            
            card.config(bg=bg_color)
            
            # Accent bar
            bar_width = 6 if "violation" in notif_type.lower() else 4
            tk.Frame(card, bg=accent_color, width=bar_width).pack(side="left", fill="y")
            
            # Content
            content = tk.Frame(card, bg=bg_color)
            content.pack(fill="both", expand=True, padx=20, pady=15)
            
            # Header row (icon, title, timestamp, actions)
            header = tk.Frame(content, bg=bg_color)
            header.pack(fill="x")
            
            # Icon
            tk.Label(header, text=icon, font=("Arial", 24), 
                    bg=bg_color).pack(side="left", padx=(0, 15))
            
            # Title section
            title_section = tk.Frame(header, bg=bg_color)
            title_section.pack(side="left", fill="x", expand=True)
            
            if "violation" in notif_type.lower():
                tk.Label(title_section, text="VIOLATION NOTICE", 
                        font=("Arial", 11, "bold"), bg=bg_color, 
                        fg="#dc3545").pack(anchor="w")
            else:
                type_text = notif_type.replace("_", " ").title()
                tk.Label(title_section, text=type_text, 
                        font=("Arial", 11, "bold"), bg=bg_color, 
                        fg=accent_color).pack(anchor="w")
            
            tk.Label(title_section, text=created_at, font=("Arial", 9), 
                    bg=bg_color, fg="#888").pack(anchor="w")
            
            # Mark as read button
            if not is_read:
                def mark_read(nid=notif_id):
                    notif_manager.mark_as_read(nid)
                    refresh_notifications()
                
                read_btn = tk.Button(header, text="Mark as Read", bg=accent_color, 
                                   fg="white", font=("Arial", 9, "bold"),
                                   relief="flat", cursor="hand2", padx=10, pady=5,
                                   command=mark_read)
                read_btn.pack(side="right", padx=10)
            
            # Message
            msg_frame = tk.Frame(content, bg=bg_color)
            msg_frame.pack(fill="x", pady=(10, 0))
            
            tk.Label(msg_frame, text=message, font=("Arial", 11), 
                    bg=bg_color, wraplength=900, justify="left").pack(anchor="w")
            
            # Related ID if available
            if related_id:
                tk.Label(msg_frame, text=f"Reference ID: {related_id}", 
                        font=("Arial", 9, "italic"), bg=bg_color, 
                        fg="#666").pack(anchor="w", pady=(5, 0))
    
    # Initial load
    refresh_notifications()
    
    # Stats section at bottom
    stats_frame = tk.Frame(main, bg="#f5f5f5")
    stats_frame.pack(fill="x", pady=(20, 0))
    
    total_count = len(notif_manager.get_all_notifications(user_email))
    unread_count = notif_manager.get_unread_count(user_email)
    
    tk.Label(stats_frame, text=f"Total: {total_count} notifications  |  Unread: {unread_count}", 
            font=("Arial", 10), bg="#f5f5f5", fg="#666").pack()