import tkinter as tk
import pymysql  # Changed from sqlite3 to pymysql
from PIL import Image, ImageTk, ImageEnhance
from reservationform import show_reserve_form
from equipment_details import show_equipment_details
from notification_manager import NotificationManager
from borrow import show_borrow_screen  # ADDED: Import borrow screen
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

def show_faculty_notifications(root, user_email, back_callback):
    for w in root.winfo_children():
        w.destroy()
    root.configure(bg="#f8fafc")  # Light gray background

    notif_manager = NotificationManager()

    top = tk.Frame(root, bg="#005c3c", height=80)
    top.pack(fill="x")
    top.pack_propagate(False)
    
    tk.Button(top, text="← Back", font=("Arial", 12, "bold"), bg="#005c3c", fg="white", 
              border=0, cursor="hand2", command=back_callback,
              activebackground="#004a30", activeforeground="white").pack(side="left", padx=30, pady=25)
    
    tk.Label(top, text="All Notifications", font=("Arial", 18, "bold"), 
             bg="#005c3c", fg="white").pack(side="left", padx=10, pady=25)

    main = tk.Frame(root, bg="#f8fafc")  # Light gray background
    main.pack(fill="both", expand=True)
    
    canvas = tk.Canvas(main, bg="#f8fafc", highlightthickness=0)  # Light gray background
    scrollbar = tk.Scrollbar(main, orient="vertical", command=canvas.yview)
    notif_frame = tk.Frame(canvas, bg="#f8fafc")  # Light gray background

    notif_frame.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
    canvas_window = canvas.create_window((0, 0), window=notif_frame, anchor="nw")
    canvas.configure(yscrollcommand=scrollbar.set)

    def on_mousewheel(event):
        canvas.yview_scroll(int(-1*(event.delta/120)), "units")
    canvas.bind_all("<MouseWheel>", on_mousewheel)

    canvas.pack(side="left", fill="both", expand=True, padx=60, pady=30)
    scrollbar.pack(side="right", fill="y", pady=30, padx=(0, 60))

    notifications = notif_manager.get_all_notifications(user_email)

    if not notifications:
        empty_frame = tk.Frame(notif_frame, bg="#f8fafc", height=200)  # Light gray background
        empty_frame.pack(fill="x", pady=100)
        tk.Label(empty_frame, text="📭 No notifications yet", 
                font=("Arial", 16), bg="#f8fafc", fg="#64748b").pack(expand=True)
    else:
        for notif in notifications:
            # CHANGED: Access by column name
            notif_id = notif['notification_id']
            message = notif['message']
            notif_type = notif['notification_type']
            related_id = notif['related_id']
            created_at = notif['created_at']
            is_read = notif['is_read']
            
            # Modern card with light gray theme
            card_bg = "white" if is_read else "#f0f9ff"  # White cards with light blue for unread
            card = tk.Frame(notif_frame, bg=card_bg, relief="flat", bd=0)
            card.pack(fill="x", pady=8, padx=10, ipadx=0, ipady=0)
            
            # Create subtle shadow effect
            shadow = tk.Frame(card, bg="#e2e8f0", height=4)
            shadow.pack(side="bottom", fill="x")
            
            # Card content
            content_frame = tk.Frame(card, bg=card_bg)
            content_frame.pack(fill="x", padx=20, pady=20)

            if "approved" in notif_type.lower():
                icon = "✅"
                accent_color = "#10b981"
                title = "Reservation Approved"
            elif "rejected" in notif_type.lower():
                icon = "❌"
                accent_color = "#ef4444"
                title = "Reservation Rejected"
            else:
                icon = "ℹ️"
                accent_color = "#3b82f6"
                title = "Reservation Submitted"
            
            # Icon and title
            header_frame = tk.Frame(content_frame, bg=card_bg)
            header_frame.pack(fill="x", pady=(0, 10))
            
            tk.Label(header_frame, text=icon, font=("Arial", 16), 
                    bg=card_bg).pack(side="left", padx=(0, 10))
            
            title_frame = tk.Frame(header_frame, bg=card_bg)
            title_frame.pack(side="left", fill="x", expand=True)
            
            tk.Label(title_frame, text=title, font=("Arial", 14, "bold"), 
                    bg=card_bg, fg="#1e293b").pack(anchor="w")  # Dark text
            tk.Label(title_frame, text=created_at, font=("Arial", 11), 
                    bg=card_bg, fg="#64748b").pack(anchor="w", pady=(2, 0))  # Gray text
            
            # Message
            tk.Label(content_frame, text=message, font=("Arial", 12), 
                    bg=card_bg, wraplength=600, justify="left", fg="#475569").pack(anchor="w", pady=(0, 15))  # Dark gray text

            # Action buttons
            if not is_read:
                action_frame = tk.Frame(content_frame, bg=card_bg)
                action_frame.pack(anchor="e")
                
                mark_read_btn = tk.Button(action_frame, text="Mark as Read", bg="#3b82f6", fg="white",
                         font=("Arial", 10, "bold"), relief="flat", cursor="hand2",
                         padx=20, pady=8, bd=0, borderwidth=0,
                         activebackground="#2563eb", activeforeground="white",
                         command=lambda nid=notif_id: [notif_manager.mark_as_read(nid), 
                                                       show_faculty_notifications(root, user_email, back_callback)])
                mark_read_btn.pack(side="right")


def show_browse_catalog(root, back_callback, user_email="faculty@nursing.com", 
                        search_term="", category_filter="All Categories", 
                        status_filter="All Status", class_filter="All Classes",
                        location_filter="All Locations"):
    print(f"\nLOADING BROWSE CATALOG for {user_email}")
    print(f"Filters: search='{search_term}', category='{category_filter}', status='{status_filter}', class='{class_filter}', location='{location_filter}'")
    
    for w in root.winfo_children():
        w.destroy()
    root.configure(bg="#f8fafc")  # Light gray background

    notif_manager = NotificationManager()

    # Modern header with improved styling
    top = tk.Frame(root, bg="#005c3c", height=80)
    top.pack(fill="x", side="top")
    top.pack_propagate(False)

    tk.Button(top, text="← Back", font=("Arial", 12, "bold"), bg="#005c3c", fg="white", border=0,
              cursor="hand2", command=back_callback,
              activebackground="#004a30", activeforeground="white").pack(side="left", padx=30, pady=25)
    
    tk.Label(top, text="Browse Equipment", font=("Arial", 18, "bold"), bg="#005c3c", 
             fg="white").pack(side="left", padx=10, pady=25)

    notif_frame = tk.Frame(top, bg="#005c3c")
    notif_frame.pack(side="right", padx=30)

    unread_count = notif_manager.get_unread_count(user_email)
    
    notif_btn = tk.Button(notif_frame, text="🔔", font=("Arial", 24), 
                         bg="#005c3c", fg="white", border=0, cursor="hand2",
                         activebackground="#005c3c", activeforeground="white",
                         padx=10, pady=0,
                         command=lambda: show_faculty_notifications(root, user_email, 
                                                           lambda: show_browse_catalog(root, back_callback, user_email)))
    notif_btn.pack()

    if unread_count > 0:
        badge = tk.Frame(notif_frame, bg="#ef4444", height=20, width=20)
        badge.place(x=28, y=2)
        badge.pack_propagate(False)
        tk.Label(badge, text=str(unread_count), 
                        font=("Arial", 9, "bold"), bg="#ef4444", fg="white").pack(expand=True)

    main = tk.Frame(root, bg="#f8fafc")  # Light gray background
    main.pack(expand=True, fill="both")
    
    # Create a light gray background
    light_bg = tk.Frame(main, bg="#f8fafc")
    light_bg.place(x=0, y=0, relwidth=1, relheight=1)

    content_container = tk.Frame(main, bg="#f8fafc")  # Light gray background
    content_container.place(relx=0.5, rely=0.5, anchor="center", relwidth=0.95, relheight=0.9)  # More centered

    # Modern search area with light theme
    search_area = tk.Frame(content_container, bg="white", relief="flat", bd=0)  # White card
    search_area.pack(fill="x", pady=(0, 25))
    
    # Create subtle shadow effect
    search_shadow = tk.Frame(search_area, bg="#e2e8f0", height=4)  # Light shadow
    search_shadow.pack(side="bottom", fill="x")
    
    search_inner = tk.Frame(search_area, bg="white")  # White card
    search_inner.pack(padx=25, pady=20, fill="x")
    
    # Search field with light theme styling
    search_var = tk.StringVar(value=search_term)
    tk.Label(search_inner, text="🔍 Search", font=("Arial", 11, "bold"), bg="white", fg="#374151").pack(side="left", padx=(0, 10))  # Dark text
    search_entry = tk.Entry(search_inner, width=25, font=("Arial", 11), textvariable=search_var,
                           relief="flat", bd=1, bg="#f8fafc", fg="#1e293b", insertbackground="#1e293b")  # Light input
    search_entry.pack(side="left", padx=(0, 15), ipady=8, ipadx=10)
    
    # Modern filter dropdowns with light theme
    filter_frame = tk.Frame(search_inner, bg="white")
    filter_frame.pack(side="left", fill="x", expand=True)
    
    # Category filter
    category_var = tk.StringVar(value=category_filter)
    category_frame = tk.Frame(filter_frame, bg="white")
    category_frame.pack(side="left", padx=5)
    tk.Label(category_frame, text="Category", font=("Arial", 9, "bold"), bg="white", fg="#64748b").pack(anchor="w")
    category_menu = tk.OptionMenu(category_frame, category_var, "All Categories", 
                                  "Laboratory Equipment", "Medical Equipment")
    category_menu.config(bg="white", font=("Arial", 9), width=14, relief="flat", bd=1, 
                        highlightthickness=1, highlightbackground="#cbd5e1", highlightcolor="#3b82f6",
                        fg="#1e293b", activebackground="#f8fafc")  # Light dropdown
    category_menu.pack(pady=(2, 0))
    
    # Status filter
    status_var = tk.StringVar(value=status_filter)
    status_frame = tk.Frame(filter_frame, bg="white")
    status_frame.pack(side="left", padx=5)
    tk.Label(status_frame, text="Status", font=("Arial", 9, "bold"), bg="white", fg="#64748b").pack(anchor="w")
    status_menu = tk.OptionMenu(status_frame, status_var, "All Status", "Available", "In Use", "Unavailable")
    status_menu.config(bg="white", font=("Arial", 9), width=12, relief="flat", bd=1,
                      highlightthickness=1, highlightbackground="#cbd5e1", highlightcolor="#3b82f6",
                      fg="#1e293b", activebackground="#f8fafc")  # Light dropdown
    status_menu.pack(pady=(2, 0))
    
    # Class filter
    class_var = tk.StringVar(value=class_filter)
    class_frame = tk.Frame(filter_frame, bg="white")
    class_frame.pack(side="left", padx=5)
    tk.Label(class_frame, text="Class", font=("Arial", 9, "bold"), bg="white", fg="#64748b").pack(anchor="w")
    class_menu = tk.OptionMenu(class_frame, class_var, "All Classes", 
                               "consumable", "plastic", "apparatus", "wooden", "glass", "metal")
    class_menu.config(bg="white", font=("Arial", 9), width=12, relief="flat", bd=1,
                     highlightthickness=1, highlightbackground="#cbd5e1", highlightcolor="#3b82f6",
                     fg="#1e293b", activebackground="#f8fafc")  # Light dropdown
    class_menu.pack(pady=(2, 0))
    
    # Location filter
    location_var = tk.StringVar(value=location_filter)
    location_frame = tk.Frame(filter_frame, bg="white")
    location_frame.pack(side="left", padx=5)
    tk.Label(location_frame, text="Location", font=("Arial", 9, "bold"), bg="white", fg="#64748b").pack(anchor="w")
    location_menu = tk.OptionMenu(location_frame, location_var, "All Locations",
                                  "central supply room", "anatomy laboratory", 
                                  "nutrition laboratory", "skills laboratory", "or-dr complex")
    location_menu.config(bg="white", font=("Arial", 9), width=14, relief="flat", bd=1,
                        highlightthickness=1, highlightbackground="#cbd5e1", highlightcolor="#3b82f6",
                        fg="#1e293b", activebackground="#f8fafc")  # Light dropdown
    location_menu.pack(pady=(2, 0))

    def create_modern_button(parent, text, command, bg_color, is_primary=False, state="normal", width=14):
        """Create modern buttons with consistent styling"""
        if state == "disabled":
            bg_color = "#cbd5e1"
            fg_color = "#64748b"
        else:
            fg_color = "white"
            
        btn = tk.Button(parent, 
                      text=text, 
                      font=("Arial", 10, "bold"),
                      bg=bg_color, 
                      fg=fg_color, 
                      relief="flat",
                      width=width,
                      height=1,
                      cursor="hand2" if state == "normal" else "arrow",
                      state=state,
                      activebackground=bg_color,
                      activeforeground=fg_color,
                      bd=0,
                      padx=15,
                      pady=10,
                      command=command if state == "normal" else None)
        return btn

    def apply_filters():
        new_search = search_var.get().strip()
        new_category = category_var.get()
        new_status = status_var.get()
        new_class = class_var.get()
        new_location = location_var.get()
        
        print(f"Applying filters: search='{new_search}', category='{new_category}', status='{new_status}', class='{new_class}', location='{new_location}'")
        
        show_browse_catalog(root, back_callback, user_email, 
                          search_term=new_search,
                          category_filter=new_category,
                          status_filter=new_status,
                          class_filter=new_class,
                          location_filter=new_location)

    def clear_filters():
        show_browse_catalog(root, back_callback, user_email, 
                          search_term="",
                          category_filter="All Categories",
                          status_filter="All Status",
                          class_filter="All Classes",
                          location_filter="All Locations")

    # Modern action buttons
    button_frame = tk.Frame(search_inner, bg="white")
    button_frame.pack(side="right", padx=(20, 0))
    
    search_btn = create_modern_button(button_frame, "🔍 Search", apply_filters, "#005c3c", is_primary=True, width=12)
    search_btn.pack(side="left", padx=5)
    
    clear_btn = create_modern_button(button_frame, "🗑️ Clear", clear_filters, "#64748b", width=12)
    clear_btn.pack(side="left", padx=5)
    
    search_entry.bind('<Return>', lambda e: apply_filters())

    catalog_frame = tk.Frame(content_container, bg="#f8fafc")  # Light gray background
    catalog_frame.pack(fill="both", expand=True)

    canvas = tk.Canvas(catalog_frame, highlightthickness=0, bg="#f8fafc")  # Light gray background
    scrollbar = tk.Scrollbar(catalog_frame, orient="vertical", command=canvas.yview)
    scrollable_frame = tk.Frame(canvas, bg="#f8fafc")  # Light gray background

    scrollable_frame.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
    canvas_window = canvas.create_window((0, 0), window=scrollable_frame, anchor="nw", width=canvas.winfo_reqwidth())
    canvas.configure(yscrollcommand=scrollbar.set)

    def center_window(event):
        canvas.itemconfig(canvas_window, width=event.width)
    
    canvas.bind('<Configure>', center_window)

    canvas.pack(side="left", fill="both", expand=True)
    scrollbar.pack(side="right", fill="y")

    def _on_mousewheel(event):
        canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")
    canvas.bind_all("<MouseWheel>", _on_mousewheel)

    equipment = []
    try:
        conn = get_db_connection()
        if conn is None:
            raise Exception("Could not connect to database")
            
        cursor = conn.cursor()
        
        # Count only non-archived equipment
        cursor.execute("SELECT COUNT(*) as count FROM equipment WHERE COALESCE(is_archived, 0) = 0")
        total_result = cursor.fetchone()
        total_count = total_result['count'] if total_result else 0  # CHANGED: Access by column name
        
        if total_count == 0:
            conn.close()
            no_data_frame = tk.Frame(scrollable_frame, bg="white", relief="flat", bd=0)  # White card
            no_data_frame.pack(pady=100, padx=100, fill="both", expand=True)
            
            # Subtle shadow effect
            shadow = tk.Frame(no_data_frame, bg="#e2e8f0", height=4)  # Light shadow
            shadow.pack(side="bottom", fill="x")
            
            content = tk.Frame(no_data_frame, bg="white")  # White card
            content.pack(fill="both", expand=True, padx=20, pady=40)
            
            tk.Label(content, text="📋 No Equipment Data Found", 
                    font=("Arial", 16, "bold"), bg="white", fg="#64748b",
                    justify="center").pack(pady=20)
            
            tk.Label(content, text="The equipment database is currently empty", 
                    font=("Arial", 12), bg="white", fg="#94a3b8",
                    justify="center").pack(pady=(0, 20))
            return
        
        # Modified query to exclude archived equipment and include new filters
        query = """SELECT id, name, description, availability_status, image_path, category, 
                   COALESCE(is_borrowable, 1) as is_borrowable,
                   COALESCE(variant, '') as variant,
                   COALESCE(class, 'consumable') as class,
                   COALESCE(location, 'central supply room') as location,
                   barcode  # ADDED: Get barcode for borrow functionality
                   FROM equipment WHERE COALESCE(is_archived, 0) = 0"""
        params = []
        
        if search_term:
            query += " AND (LOWER(name) LIKE LOWER(%s) OR LOWER(description) LIKE LOWER(%s) OR LOWER(variant) LIKE LOWER(%s))"
            search_pattern = f"%{search_term}%"
            params.extend([search_pattern, search_pattern, search_pattern])
            print(f"Search filter applied: {search_pattern}")
        
        if category_filter != "All Categories":
            query += " AND category = %s"
            params.append(category_filter)
            print(f"Category filter applied: {category_filter}")
        
        if status_filter != "All Status":
            query += " AND availability_status = %s"
            params.append(status_filter)
            print(f"Status filter applied: {status_filter}")
            
        if class_filter != "All Classes":
            query += " AND class = %s"
            params.append(class_filter)
            print(f"Class filter applied: {class_filter}")
            
        if location_filter != "All Locations":
            query += " AND location = %s"
            params.append(location_filter)
            print(f"Location filter applied: {location_filter}")
        
        query += " ORDER BY name, variant"
        
        print(f"Executing query: {query}")
        print(f"With params: {params}")
        
        cursor.execute(query, params)
        equipment = cursor.fetchall()
        conn.close()
        
        print(f"Found {len(equipment)} active items matching filters")
            
    except Exception as e:
        print(f"ERROR: Database error - {e}")

    if not equipment:
        no_data_frame = tk.Frame(scrollable_frame, bg="white", relief="flat", bd=0)  # White card
        no_data_frame.pack(pady=100, padx=100, fill="both", expand=True)
        
        # Subtle shadow effect
        shadow = tk.Frame(no_data_frame, bg="#e2e8f0", height=4)  # Light shadow
        shadow.pack(side="bottom", fill="x")
        
        content = tk.Frame(no_data_frame, bg="white")  # White card
        content.pack(fill="both", expand=True, padx=20, pady=40)
        
        tk.Label(content, 
                text="🔍 No equipment found matching your filters", 
                font=("Arial", 16, "bold"), bg="white", fg="#64748b",
                justify="center").pack(pady=20)
        
        tk.Label(content, 
                text="Try adjusting your search criteria or clear filters", 
                font=("Arial", 12), bg="white", fg="#94a3b8",
                justify="center").pack(pady=(0, 20))
                
        clear_btn = create_modern_button(content, "🗑️ Clear Filters", clear_filters, "#64748b", width=16)
        clear_btn.pack(pady=10)
    else:
        has_filters = search_term or category_filter != "All Categories" or status_filter != "All Status" or class_filter != "All Classes" or location_filter != "All Locations"
        
        # Results header with light theme styling
        results_bg = "#d1fae5" if has_filters else "#dbeafe"  # Light greens/blues
        results_fg = "#065f46" if has_filters else "#1e40af"  # Dark text
        
        results_frame = tk.Frame(scrollable_frame, bg=results_bg, relief="flat", bd=0)
        results_frame.pack(fill="x", pady=(10, 25))
        
        # Subtle shadow effect
        shadow = tk.Frame(results_frame, bg="#cbd5e1", height=4)  # Light shadow
        shadow.pack(side="bottom", fill="x")
        
        content = tk.Frame(results_frame, bg=results_bg)
        content.pack(fill="x", padx=20, pady=15)
        
        if has_filters:
            result_text = f"🎯 Found {len(equipment)} equipment item(s) matching your criteria"
        else:
            result_text = f"📊 Total Active Equipment: {len(equipment)} item(s)"
            
        tk.Label(content, 
                text=result_text, 
                font=("Arial", 12, "bold"), bg=results_bg, fg=results_fg,
                justify="center").pack()
        
        # Modern card layout with light theme
        cards_container = tk.Frame(scrollable_frame, bg="#f8fafc")  # Light gray background
        cards_container.pack(anchor="center", pady=20, fill="both", expand=True)

        for idx, equipment_data in enumerate(equipment):
            # CHANGED: Access by column name
            eid = equipment_data['id']
            name = equipment_data['name']
            desc = equipment_data['description']
            status = equipment_data['availability_status']
            img_path = equipment_data['image_path']
            category = equipment_data['category']
            is_borrowable = equipment_data['is_borrowable']
            variant = equipment_data['variant']
            equip_class = equipment_data['class']
            location = equipment_data['location']
            barcode = equipment_data['barcode']  # ADDED: Get barcode
            
            row = idx // 2
            col = idx % 2
            
            # Modern card with light theme
            card_outer = tk.Frame(cards_container, bg="#f8fafc", width=420, height=520)  # INCREASED: Height to accommodate borrow button
            card_outer.grid(row=row, column=col, padx=20, pady=20)
            card_outer.grid_propagate(False)
            
            # Subtle shadow effect
            shadow = tk.Frame(card_outer, bg="#e2e8f0", height=6)  # Light shadow
            shadow.place(x=0, y=514, width=420, height=6)
            
            # Main card - light theme
            card = tk.Frame(card_outer, bg="white", width=420, height=514)  # White card
            card.place(x=0, y=0)
            card.pack_propagate(False)

            content = tk.Frame(card, bg="white")  # White card
            content.pack(padx=20, pady=20, fill="both", expand=True)

            # Image container with light border - centered content
            img_container = tk.Frame(content, bg="#f1f5f9", width=380, height=200, relief="flat", bd=0)  # Light gray container
            img_container.pack(pady=(0, 15))
            img_container.pack_propagate(False)
            
            try:
                if img_path and os.path.exists(img_path):
                    # Try resource_path first, then original path
                    try:
                        actual_path = resource_path(img_path)
                    except:
                        actual_path = img_path
                    
                    img = Image.open(actual_path)
                    img = img.resize((380, 200), Image.Resampling.LANCZOS)
                    photo = ImageTk.PhotoImage(img)
                    img_label = tk.Label(img_container, image=photo, bg="#f1f5f9")
                    img_label.image = photo
                    img_label.pack(expand=True)
                else:
                    # Centered "No Image" text
                    no_img_frame = tk.Frame(img_container, bg="#f1f5f9")
                    no_img_frame.pack(expand=True, fill="both")
                    tk.Label(no_img_frame, text="🖼️ No Image", font=("Arial", 14), 
                            bg="#f1f5f9", fg="#94a3b8").pack(expand=True)  # Centered
            except Exception as e:
                # Centered error message
                error_frame = tk.Frame(img_container, bg="#f1f5f9")
                error_frame.pack(expand=True, fill="both")
                tk.Label(error_frame, text="❌ Image Error", font=("Arial", 14), 
                        bg="#f1f5f9", fg="#94a3b8").pack(expand=True)  # Centered
            
            # Equipment name - centered
            display_name = f"{name} ({variant})" if variant else name
            name_label = tk.Label(content, text=display_name, font=("Arial", 14, "bold"), bg="white", 
                    fg="#005c3c", wraplength=380, justify="center")  # Green text, centered
            name_label.pack(pady=(0, 10))
            
            # Info frame with class and location - centered content
            info_frame = tk.Frame(content, bg="white")
            info_frame.pack(fill="x", pady=(0, 10))
            
            tk.Label(info_frame, text=f"📦 Class: {equip_class.title()}", font=("Arial", 10), 
                    bg="white", fg="#64748b", anchor="w").pack(side="left", fill="x", expand=True)  # Gray text
            
            # Abbreviate location for display
            location_abbr = {
                'central supply room': 'Central Supply',
                'anatomy laboratory': 'Anatomy Lab',
                'nutrition laboratory': 'Nutrition Lab', 
                'skills laboratory': 'Skills Lab',
                'or-dr complex': 'OR-DR Complex'
            }
            location_display = location_abbr.get(location, location.title())
            
            tk.Label(info_frame, text=f"📍 {location_display}", font=("Arial", 10), 
                    bg="white", fg="#64748b", anchor="e").pack(side="right")  # Gray text
            
            # Description - centered
            desc_text = desc if desc else "No description available"
            desc_label = tk.Label(content, text=desc_text, 
                    font=("Arial", 10), bg="white", wraplength=380, 
                    justify="center", fg="#475569", height=2)  # Dark gray text
            desc_label.pack(pady=(0, 12))
            
            # Status badge with modern styling - centered
            status_color = {
                "Available": "#10b981",
                "In Use": "#ef4444", 
                "Unavailable": "#f59e0b"
            }.get(status, "#6b7280")
            
            status_badge = tk.Label(content, text=status, font=("Arial", 10, "bold"), 
                    bg=status_color, fg="white", padx=15, pady=6, bd=0)
            status_badge.pack(pady=(0, 15))
            
            # Action buttons - centered in their container
            button_frame = tk.Frame(content, bg="white")
            button_frame.pack(fill="x", pady=(0, 5))
            
            # Details button
            details_btn = create_modern_button(
                button_frame, 
                "📋 Details", 
                lambda eid=eid: show_equipment_details(
                    root, eid, 
                    lambda: show_browse_catalog(root, back_callback, user_email, 
                                               search_term, category_filter, status_filter,
                                               class_filter, location_filter),
                    user_email
                ),
                "#6b7280",  # Gray
                width=10
            )
            details_btn.pack(side="left", padx=(0, 5), fill="x", expand=True)
            
            # ADDED: Borrow button - only show for borrowable items
            if is_borrowable and status == "Available":
                borrow_btn = create_modern_button(
                    button_frame,
                    "📥 Borrow",
                    lambda eid=eid, barcode=barcode, name=display_name: show_borrow_screen(
                        root,
                        lambda: show_browse_catalog(root, back_callback, user_email,
                                                   search_term, category_filter, status_filter,
                                                   class_filter, location_filter),
                        user_email
                    ),
                    "#007bff",  # Blue color for borrow
                    width=10
                )
                borrow_btn.pack(side="left", padx=5, fill="x", expand=True)
            else:
                # Disabled borrow button for non-borrowable or unavailable items
                borrow_btn = create_modern_button(
                    button_frame,
                    "📥 Borrow",
                    None,
                    "#cbd5e1",
                    state="disabled",
                    width=10
                )
                borrow_btn.pack(side="left", padx=5, fill="x", expand=True)
            
            # Reserve/Inventory button
            if is_borrowable:
                btn_state = "normal" if status == "Available" else "disabled"
                btn_bg = "#005c3c" if status == "Available" else "#cbd5e1"
                btn_text = "📅 Reserve"
                
                reserve_btn = create_modern_button(
                    button_frame,
                    btn_text,
                    lambda eid=eid, dname=display_name: show_reserve_form(
                        root,
                        equipment_name=dname,
                        equipment_id=eid,
                        user_email=user_email,
                        back_callback=lambda: show_browse_catalog(root, back_callback, user_email,
                                                                 search_term, category_filter, status_filter,
                                                                 class_filter, location_filter)
                    ),
                    btn_bg,
                    state=btn_state,
                    width=10
                )
                reserve_btn.pack(side="right", padx=(5, 0), fill="x", expand=True)
            else:
                # Inventory only button (styled as disabled)
                inventory_btn = create_modern_button(
                    button_frame,
                    "📦 Inventory",
                    None,
                    "#cbd5e1",
                    state="disabled",
                    width=10
                )
                inventory_btn.pack(side="right", padx=(5, 0), fill="x", expand=True)
        
        # Configure grid columns for proper alignment and centering
        cards_container.grid_columnconfigure(0, weight=1)
        cards_container.grid_columnconfigure(1, weight=1)
        
        scrollable_frame.update_idletasks()
        canvas.update_idletasks()
        canvas.configure(scrollregion=canvas.bbox("all"))