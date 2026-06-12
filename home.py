#home.py
import tkinter as tk
from PIL import Image, ImageTk
from profsettings import show_profile_settings
from browsecatalog import show_browse_catalog  
from borrow import show_borrow_screen
from returnequipment import show_return_screen
from facultyhistory import show_faculty_history
from notification_manager import NotificationManager
from notifications_page import show_notifications_page
import os
import sys
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
def resource_path(relative_path):
    """Get absolute path to resource, works for dev and for PyInstaller"""
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

def restart_application():
    """Restart the application without circular imports"""
    import subprocess
    import sys
    python = sys.executable
    subprocess.call([python] + sys.argv)

def show_homepage(root: tk.Tk, user_email, main_app=None):
    """
    Show faculty homepage
    main_app is optional for backward compatibility
    """
    # Clear window first
    for w in root.winfo_children():
        w.destroy()
    root.configure(bg="#f5f5f5")

    # Initialize notification manager
    notif_manager = NotificationManager()

    # Top bar with gradient effect
    top = tk.Frame(root, bg="#005c3c", height=80)
    top.pack(fill="x", side="top")

    # Try to load logo, if not loaded show text
    try:
        logo_img = Image.open(resource_path("ion_logo.png")).resize((50, 50))
        logo_photo = ImageTk.PhotoImage(logo_img)
        logo = tk.Label(top, image=logo_photo, bg="#005c3c")
        logo.image = logo_photo 
    except Exception:
        logo = tk.Label(top, text="ION", bg="#005c3c", fg="white", font=("Arial", 24, "bold"))
    logo.pack(side="left", padx=(30, 0), pady=15)

    # System name
    tk.Label(top, text="Laboratory Equipment System", bg="#005c3c", 
             font=("Arial", 16), fg="white").pack(side="left", padx=20)

    # User menu variables
    user_menu = None
    menu_shown = False

    # Logout function - handles both cases (with and without main_app)
    def perform_logout():
        """Logout the user and return to main login page"""
        nonlocal menu_shown
        if user_menu:
            user_menu.destroy()
        
        if main_app:
            # Use main_app's logout method if available
            root.destroy()
            main_app.logout()
        else:
            # Fallback: restart the application using subprocess
            root.destroy()
            restart_application()

    # Function to show or hide the user menu
    def toggle_menu(event=None):
        nonlocal user_menu, menu_shown
        
        if menu_shown and user_menu:
            # Hide menu
            user_menu.destroy()
            user_menu = None
            menu_shown = False
        else:
            # Show menu
            user_menu = tk.Toplevel(root)
            user_menu.overrideredirect(True)
            user_menu.configure(bg="white", bd=1, relief="solid")
            user_menu.attributes('-topmost', True)
            
            # Position menu below user icon
            root.update_idletasks()
            x = user_icon.winfo_rootx() - 120
            y = user_icon.winfo_rooty() + user_icon.winfo_height()
            user_menu.geometry(f"+{x}+{y}")
            
            # Menu buttons
            settings_btn = tk.Button(user_menu, text="⚙ Settings", relief="flat", bg="white", fg="#333",
                      font=("Arial", 10), anchor="w", padx=15, pady=8,
                      activebackground="#f0f0f0",
                      command=lambda: [user_menu.destroy(), show_profile_settings(root, user_email, back_callback=lambda: show_homepage(root, user_email, main_app))])
            settings_btn.pack(fill="x")
            
            logout_btn = tk.Button(user_menu, text="🚪 Logout", relief="flat", bg="white", fg="#333",
                      font=("Arial", 10), anchor="w", padx=15, pady=8,
                      activebackground="#f0f0f0",
                      command=perform_logout)
            logout_btn.pack(fill="x")
            
            menu_shown = True
            
            # Bind focus out to close menu
            def on_focus_out(event):
                nonlocal menu_shown
                if user_menu and menu_shown:
                    user_menu.destroy()
                    menu_shown = False
            
            user_menu.bind("<FocusOut>", on_focus_out)
            
            # Set focus to menu
            user_menu.focus_set()

    # User icon with better styling
    user_icon = tk.Label(top, text="👤", bg="#005c3c", font=("Arial", 24), 
                         fg="white", cursor="hand2")
    user_icon.pack(side="right", padx=(10, 30), pady=10)
    user_icon.bind("<Button-1>", toggle_menu)

    # Hide menu when clicking outside
    def hide_menu(event):
        nonlocal menu_shown, user_menu
        if menu_shown and user_menu:
            # Check if click is outside the menu
            if (event.widget != user_icon and 
                (not user_menu or event.widget not in user_menu.winfo_children())):
                user_menu.destroy()
                user_menu = None
                menu_shown = False
    
    root.bind("<Button-1>", hide_menu, add="+")

    # Main content area with background image
    main = tk.Frame(root, bg="#f5f5f5")
    main.pack(expand=True, fill="both")
    
    # Try to load and set background image
    try:
        bg_image = Image.open(resource_path("background.jpg"))
        screen_width = root.winfo_screenwidth()
        screen_height = root.winfo_screenheight()
        bg_image = bg_image.resize((screen_width, screen_height - 80))
        
        # Remove the enhancement part that's causing error
        # from PIL import ImageEnhance
        # enhancer = ImageEnhance.Brightness(bg_image)
        # bg_image = bg_image.enhance(1.3)
        
        bg_photo = ImageTk.PhotoImage(bg_image)
        bg_label = tk.Label(main, image=bg_photo)
        bg_label.image = bg_photo
        bg_label.place(x=0, y=0, relwidth=1, relheight=1)
    
    except Exception as e:
        print(f"Background image not found: {e}")

    # Container for cards and notifications
    content_container = tk.Frame(main, bg="#f5f5f5")
    content_container.pack(expand=True, fill="both", padx=60, pady=50)

    # Left side - Cards section
    left_section = tk.Frame(content_container, bg="#f5f5f5")
    left_section.pack(side="left", fill="both", expand=True)

    # Heading
    tk.Label(left_section, text="Faculty Equipment Portal",
             font=("Arial", 28, "bold"), bg="#f5f5f5", fg="#005c3c").pack(pady=(20, 5))
    tk.Label(left_section,
             text="Browse, borrow, and manage laboratory equipment for your research and classes",
             font=("Arial", 11), bg="#f5f5f5", fg="#666").pack(pady=(0, 30))

    # Function to create a modern card with icons
    def card(parent, title, desc, icon, btn_text, r, c):
        shadow = tk.Frame(parent, bg="#b0b0b0", width=240, height=200)
        shadow.grid(row=r, column=c, padx=20, pady=20)
        shadow.grid_propagate(False)
        
        frame = tk.Frame(shadow, bg="#ffffff", width=240, height=200)
        frame.place(x=-2, y=-2)
        frame.pack_propagate(False)

        icon_section = tk.Frame(frame, bg="#d4edda", height=80)
        icon_section.pack(fill="x")
        icon_section.pack_propagate(False)
        
        tk.Label(icon_section, text=icon, bg="#d4edda",
                 font=("Arial", 36)).pack(expand=True)

        content = tk.Frame(frame, bg="#ffffff")
        content.pack(fill="both", expand=True, padx=15, pady=10)
        
        tk.Label(content, text=title, font=("Arial", 13, "bold"),
                 bg="#ffffff", fg="#005c3c").pack(pady=(5, 3))
        tk.Label(content, text=desc, wraplength=200, font=("Arial", 9),
                 bg="#ffffff", fg="#666", justify="center").pack(pady=(0, 10))

        # Button actions - pass main_app to all callbacks
        if title == "Browse Equipment":
            action = lambda: show_browse_catalog(root, back_callback=lambda: show_homepage(root, user_email, main_app), user_email=user_email)
        elif title == "Borrow Equipment":
            action = lambda: show_borrow_screen(root, back_callback=lambda: show_homepage(root, user_email, main_app), user_email=user_email)
        elif title == "View History":
            action = lambda: show_faculty_history(root, back_callback=lambda: show_homepage(root, user_email, main_app), user_email=user_email)
        else:
            action = lambda: None
        
        btn = tk.Button(content, text=btn_text, bg="#005c3c", fg="white",
                       relief="flat", font=("Arial", 10, "bold"),
                       width=12, height=1, cursor="hand2",
                       activebackground="#004d32", activeforeground="white",
                       command=action)
        btn.pack(pady=(0, 5))

    # Place cards in a grid layout (3 cards instead of 4)
    grid = tk.Frame(left_section, bg="#f5f5f5")
    grid.pack()
    card(grid, "Browse Equipment", "Search available equipment", "🔍", "Browse", 0, 0)
    card(grid, "Borrow Equipment", "Submit request to borrow equipment", "📦", "Request", 0, 1)
    card(grid, "View History", "View your borrowing history", "📊", "View", 0, 2)  # Moved to first row, third column

    # Right side - Notification Section
    notif_container = tk.Frame(content_container, bg="#f5f5f5")
    notif_container.pack(side="right", padx=(30, 0), fill="y")

    notif_section = tk.Frame(notif_container, bg="white", bd=1, relief="solid", 
                            width=380, height=550)
    notif_section.pack(fill="both", expand=True)
    notif_section.pack_propagate(False)

    # Notification header
    notif_header = tk.Frame(notif_section, bg="#005c3c", height=50, cursor="hand2")
    notif_header.pack(fill="x")
    notif_header.pack_propagate(False)
    
    def go_to_notifications(event=None):
        show_notifications_page(root, user_email, back_callback=lambda: show_homepage(root, user_email, main_app))
    
    notif_header.bind("<Button-1>", go_to_notifications)

    bell_label = tk.Label(notif_header, text="🔔 Notifications", font=("Arial", 14, "bold"),
            bg="#005c3c", fg="white", cursor="hand2")
    bell_label.pack(pady=12, padx=15, side="left")
    bell_label.bind("<Button-1>", go_to_notifications)

    # Get unread count
    unread_count = notif_manager.get_unread_count(user_email)

    if unread_count > 0:
        badge = tk.Label(notif_header, text=str(unread_count), 
                        font=("Arial", 10, "bold"),
                        bg="#ff4444", fg="white", padx=8, pady=3,
                        cursor="hand2")
        badge.pack(side="right", padx=15)
        badge.bind("<Button-1>", go_to_notifications)

    # Scrollable notification area
    canvas = tk.Canvas(notif_section, bg="white", highlightthickness=0, height=450)
    scrollbar = tk.Scrollbar(notif_section, orient="vertical", command=canvas.yview)
    notif_frame = tk.Frame(canvas, bg="white")

    canvas_window = canvas.create_window((0, 0), window=notif_frame, anchor="nw", width=360)

    def on_frame_configure(event):
        canvas.configure(scrollregion=canvas.bbox("all"))

    notif_frame.bind("<Configure>", on_frame_configure)
    canvas.configure(yscrollcommand=scrollbar.set)

    def on_mousewheel(event):
        canvas.yview_scroll(int(-1*(event.delta/120)), "units")

    canvas.bind_all("<MouseWheel>", on_mousewheel)

    canvas.pack(side="left", fill="both", expand=True)
    scrollbar.pack(side="right", fill="y")

    # Get notifications
    all_notifications = notif_manager.get_all_notifications_as_dicts(user_email, limit=50)
    unread_notifications = [notif for notif in all_notifications if not notif['is_read']]

    if not unread_notifications:
        tk.Label(notif_frame, text="📭\nNo unread notifications", 
                font=("Arial", 11), bg="white", fg="#999").pack(pady=50)
    else:
        for notif in unread_notifications:
            bg_color = "#fff3cd"
            
            notif_item = tk.Frame(notif_frame, bg=bg_color, bd=0, 
                                highlightbackground="#e0e0e0", highlightthickness=1)
            notif_item.pack(fill="x", padx=10, pady=6)

            if "violation" in notif['notification_type'].lower():
                icon = "⚠️"
                accent_color = "#ff6b6b"
            elif "approved" in notif['notification_type'].lower():
                icon = "✅"
                accent_color = "#4CAF50"
            elif "rejected" in notif['notification_type'].lower():
                icon = "❌"
                accent_color = "#f44336"
            else:
                icon = "ℹ️"
                accent_color = "#2196F3"
            
            notif_item.config(bg=bg_color)
            
            bar_width = 6 if "violation" in notif['notification_type'].lower() else 4
            tk.Frame(notif_item, bg=accent_color, width=bar_width).pack(side="left", fill="y")
            
            content_frame = tk.Frame(notif_item, bg=bg_color)
            content_frame.pack(fill="x", padx=12, pady=10)

            icon_size = 20 if "violation" in notif['notification_type'].lower() else 18
            tk.Label(content_frame, text=icon, font=("Arial", icon_size), 
                    bg=bg_color).pack(side="left", padx=(0, 10), anchor="n")
            
            text_frame = tk.Frame(content_frame, bg=bg_color)
            text_frame.pack(side="left", fill="x", expand=True)
            
            if "violation" in notif['notification_type'].lower():
                tk.Label(text_frame, text="VIOLATION NOTICE", 
                        font=("Arial", 9, "bold"), bg=bg_color, 
                        fg="#dc3545").pack(anchor="w")
            
            wrap_length = 260 if "violation" in notif['notification_type'].lower() else 270
            font_size = 9 if "violation" in notif['notification_type'].lower() else 10
            
            msg_label = tk.Label(text_frame, text=notif['message'], font=("Arial", font_size), 
                                bg=bg_color, wraplength=wrap_length, justify="left")
            msg_label.pack(anchor="w", pady=(2, 0))
            
            tk.Label(text_frame, text=notif['created_at'], font=("Arial", 8), 
                    bg=bg_color, fg="#888").pack(anchor="w", pady=(3, 0))
            
            tk.Label(content_frame, text="●", font=("Arial", 14), 
                    bg=bg_color, fg=accent_color).pack(side="right", padx=5)

    # Refresh button
    def refresh_notifications():
        show_homepage(root, user_email, main_app)

    refresh_btn = tk.Button(notif_section, text="🔄 Refresh Notifications", 
                            bg="#005c3c", fg="white", font=("Arial", 9, "bold"),
                            relief="flat", cursor="hand2", height=2,
                            activebackground="#004d32", activeforeground="white",
                            command=refresh_notifications)
    refresh_btn.pack(side="bottom", fill="x")

    # "View All" button
    view_all_btn = tk.Button(notif_section, text="View All Notifications →", 
                            bg="#005c3c", fg="white", font=("Arial", 10, "bold"),
                            relief="flat", cursor="hand2", height=2,
                            activebackground="#004d32", activeforeground="white",
                            command=lambda: show_notifications_page(root, user_email, 
                                                                   back_callback=lambda: show_homepage(root, user_email, main_app)))
    view_all_btn.pack(side="bottom", fill="x")