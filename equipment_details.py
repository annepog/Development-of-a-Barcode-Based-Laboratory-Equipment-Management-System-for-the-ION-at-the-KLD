import tkinter as tk
from PIL import Image, ImageTk, ImageEnhance
import pymysql  # Changed from sqlite3 to pymysql

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
def show_equipment_details(root, equipment_id, back_callback, user_email):
    """Display equipment details in a modern card layout"""
    for w in root.winfo_children():
        w.destroy()
    root.configure(bg="#f5f5f5")

    # Fetch equipment from database
    conn = get_db_connection()
    if conn is None:
        tk.Label(root, text="Database connection failed", fg="red", bg="#f5f5f5", 
                font=("Arial", 16)).pack(pady=50)
        return
        
    cursor = conn.cursor()
    cursor.execute("""
        SELECT id, barcode, name, description, image_path, availability_status, 
               category, usage_instruction, manufacturer, model, serial_number,
               tracking_type, available_quantity, total_quantity, min_stock_level,
               COALESCE(variant, '') as variant, COALESCE(is_borrowable, 1) as is_borrowable,
               COALESCE(class, 'consumable') as class,
               COALESCE(location, 'central supply room') as location
        FROM equipment
        WHERE id = %s
    """, (equipment_id,))  # CHANGED: ? to %s
    result = cursor.fetchone()
    conn.close()

    if not result:
        tk.Label(root, text="Equipment not found", fg="red", bg="#f5f5f5", 
                font=("Arial", 16)).pack(pady=50)
        return

    # CHANGED: Access by column name
    eq_id = result['id']
    barcode = result['barcode']
    name = result['name']
    description = result['description']
    image_path = result['image_path']
    status = result['availability_status']
    category = result['category']
    usage = result['usage_instruction']
    manufacturer = result['manufacturer']
    model = result['model']
    serial_number = result['serial_number']
    tracking_type = result['tracking_type']
    available_qty = result['available_quantity']
    total_qty = result['total_quantity']
    min_stock = result['min_stock_level']
    variant = result['variant']
    is_borrowable = result['is_borrowable']
    equip_class = result['class']
    location = result['location']

    # Determine availability display
    if tracking_type == "quantity":
        if available_qty == 0:
            availability_display = "Out of Stock"
            availability_color = "#dc3545"
        elif available_qty <= min_stock:
            availability_display = f"Low Stock ({available_qty} available)"
            availability_color = "#ffc107"
        else:
            availability_display = f"In Stock ({available_qty} available)"
            availability_color = "#28a745"
    else:
        status_colors = {
            "Available": "#28a745",
            "Borrowed": "#ffc107",
            "Maintenance": "#ff6b6b",
            "Reserved": "#ffc107",
            "Unavailable": "#dc3545"
        }
        availability_display = status or "Available"
        availability_color = status_colors.get(status, "#28a745")

    # Top bar matching homepage design
    top_bar = tk.Frame(root, bg="#005c3c", height=80)
    top_bar.pack(fill="x", side="top")
    top_bar.pack_propagate(False)

    # Logo
    try:
        logo_img = Image.open("ion_logo.png").resize((50, 50))
        logo_photo = ImageTk.PhotoImage(logo_img)
        logo_label = tk.Label(top_bar, image=logo_photo, bg="#005c3c")
        logo_label.image = logo_photo
        logo_label.pack(side="left", padx=(30, 0), pady=15)
    except:
        tk.Label(top_bar, text="ION", font=("Arial", 24, "bold"),
                bg="#005c3c", fg="white").pack(side="left", padx=(30, 0), pady=15)

    # System name
    tk.Label(top_bar, text="Laboratory Equipment System", bg="#005c3c", 
             font=("Arial", 16), fg="white").pack(side="left", padx=20)

    # Main container
    main_container = tk.Frame(root, bg="#f5f5f5")
    main_container.pack(expand=True, fill="both", padx=60, pady=40)

    # Header section with back button
    header_frame = tk.Frame(main_container, bg="#f5f5f5")
    header_frame.pack(fill="x", pady=(0, 30))

    # Back button
    back_btn = tk.Button(header_frame, text="← Back", font=("Arial", 11), 
                        bg="#005c3c", fg="white", relief="flat",
                        padx=20, pady=8, cursor="hand2",
                        activebackground="#004d32", activeforeground="white",
                        command=back_callback)
    back_btn.pack(side="left")

    # Page title
    title_frame = tk.Frame(header_frame, bg="#f5f5f5")
    title_frame.pack(side="left", padx=20)
    
    display_name = f"{name} ({variant})" if variant else name
    tk.Label(title_frame, text=display_name, font=("Arial", 24, "bold"), 
             bg="#f5f5f5", fg="#005c3c").pack(anchor="w")
    tk.Label(title_frame, text=f"Category: {category}", 
             font=("Arial", 11), bg="#f5f5f5", fg="#666").pack(anchor="w")

    # Main content card with shadow effect
    card_shadow = tk.Frame(main_container, bg="#d0d0d0")
    card_shadow.pack(fill="both", expand=True)
    
    content_card = tk.Frame(card_shadow, bg="white")
    content_card.place(x=-3, y=-3, relwidth=1, relheight=1)

    # Scrollable canvas
    canvas = tk.Canvas(content_card, bg="white", highlightthickness=0)
    scrollbar = tk.Scrollbar(content_card, orient="vertical", command=canvas.yview)
    scrollable_frame = tk.Frame(canvas, bg="white")

    canvas_window = canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")

    def on_frame_configure(event):
        canvas.configure(scrollregion=canvas.bbox("all"))
        canvas.itemconfig(canvas_window, width=canvas.winfo_width())

    def on_canvas_configure(event):
        canvas.itemconfig(canvas_window, width=event.width)

    scrollable_frame.bind("<Configure>", on_frame_configure)
    canvas.bind("<Configure>", on_canvas_configure)
    canvas.configure(yscrollcommand=scrollbar.set)

    # Enable mousewheel scrolling
    def on_mousewheel(event):
        canvas.yview_scroll(int(-1*(event.delta/120)), "units")
    canvas.bind_all("<MouseWheel>", on_mousewheel)

    canvas.pack(side="left", fill="both", expand=True)
    scrollbar.pack(side="right", fill="y")

    # Content inside scrollable frame
    content_frame = tk.Frame(scrollable_frame, bg="white")
    content_frame.pack(fill="both", expand=True, padx=50, pady=40)

    # Top section - Image and Quick Info side by side
    top_section = tk.Frame(content_frame, bg="white")
    top_section.pack(fill="x", pady=(0, 30))

    # Left - Image
    image_frame = tk.Frame(top_section, bg="#f8f9fa", relief="solid", borderwidth=1)
    image_frame.pack(side="left", padx=(0, 40))

    try:
        img = Image.open(image_path)
        img = img.resize((300, 300))
        photo = ImageTk.PhotoImage(img)
        img_label = tk.Label(image_frame, image=photo, bg="#f8f9fa")
        img_label.image = photo
        img_label.pack(padx=10, pady=10)
    except:
        placeholder = tk.Frame(image_frame, bg="#e0e0e0", width=300, height=300)
        placeholder.pack_propagate(False)
        placeholder.pack(padx=10, pady=10)
        tk.Label(placeholder, text="📷\nNo Image Available", bg="#e0e0e0", 
                fg="#999", font=("Arial", 14)).place(relx=0.5, rely=0.5, anchor="center")

    # Right - Quick Info Cards
    quick_info_frame = tk.Frame(top_section, bg="white")
    quick_info_frame.pack(side="left", fill="both", expand=True)

    def create_info_badge(parent, icon, label, value, bg_color, fg_color="#333"):
        """Create a modern info badge with uniform height and alignment"""
        badge = tk.Frame(parent, bg=bg_color, relief="flat", bd=0, height=70)
        badge.pack(fill="x", pady=6)
        badge.pack_propagate(False)  # Force uniform height
        
        content = tk.Frame(badge, bg=bg_color)
        content.place(relx=0, rely=0, relwidth=1, relheight=1)
        
        # Icon with fixed width for alignment
        icon_frame = tk.Frame(content, bg=bg_color, width=50)
        icon_frame.pack(side="left", padx=(20, 0))
        icon_frame.pack_propagate(False)
        tk.Label(icon_frame, text=icon, font=("Arial", 18), bg=bg_color, 
                fg=fg_color).pack(expand=True)
        
        # Text content with consistent alignment
        text_frame = tk.Frame(content, bg=bg_color)
        text_frame.pack(side="left", fill="both", expand=True, padx=(10, 20))
        
        # Label with consistent styling
        tk.Label(text_frame, text=label.upper(), font=("Arial", 9, "bold"), 
                bg=bg_color, fg="#666", anchor="w").pack(anchor="w", pady=(15, 2))
        
        # Value with consistent styling and wrapping
        tk.Label(text_frame, text=value, font=("Arial", 12), 
                bg=bg_color, fg=fg_color, anchor="w", wraplength=400,
                justify="left").pack(anchor="w", fill="x")

    # Barcode badge
    create_info_badge(quick_info_frame, "🔖", "Equipment ID", barcode, "#e3f2fd", "#1976d2")

    # Status badge
    create_info_badge(quick_info_frame, "📊", "Status", availability_display, 
                     "#f8f9fa", availability_color)

    # Tracking type badge
    tracking_display = "Quantity Item" if tracking_type == "quantity" else "Individual Item"
    tracking_bg = "#fff3e0" if tracking_type == "quantity" else "#e8f5e9"
    tracking_fg = "#e65100" if tracking_type == "quantity" else "#2e7d32"
    create_info_badge(quick_info_frame, "📦", "Tracking Type", tracking_display, 
                     tracking_bg, tracking_fg)

    # Class badge
    class_display = equip_class.title()
    create_info_badge(quick_info_frame, "🏷️", "Class", class_display, "#f3e5f5", "#7b1fa2")

    # Location badge
    location_abbr = {
        'central supply room': 'Central Supply',
        'anatomy laboratory': 'Anatomy Lab',
        'nutrition laboratory': 'Nutrition Lab', 
        'skills laboratory': 'Skills Lab',
        'or-dr complex': 'OR-DR Complex'
    }
    location_display = location_abbr.get(location, location.title())
    create_info_badge(quick_info_frame, "📍", "Location", location_display, "#e8f5e8", "#388e3c")

    # Borrowable badge
    borrowable_text = "Available for Borrowing" if is_borrowable else "Not Borrowable (Fixed/Consumable)"
    borrowable_bg = "#d4edda" if is_borrowable else "#f8d7da"
    borrowable_fg = "#155724" if is_borrowable else "#721c24"
    borrowable_icon = "✅" if is_borrowable else "⛔"
    create_info_badge(quick_info_frame, borrowable_icon, "Borrowing Status", 
                     borrowable_text, borrowable_bg, borrowable_fg)

    # Divider with consistent spacing
    tk.Frame(content_frame, bg="#e0e0e0", height=1).pack(fill="x", pady=30)

    # Quantity Information (if applicable)
    if tracking_type == "quantity":
        qty_section = tk.Frame(content_frame, bg="#f8f9fa", relief="solid", borderwidth=1)
        qty_section.pack(fill="x", pady=(0, 30))
        
        # Section header with consistent padding
        header_content = tk.Frame(qty_section, bg="#f8f9fa")
        header_content.pack(fill="x", padx=30, pady=(20, 15))
        tk.Label(header_content, text="📊 Inventory Information", font=("Arial", 16, "bold"),
                bg="#f8f9fa", fg="#005c3c").pack(anchor="w")
        
        # Quantity grid with uniform card sizes
        qty_grid = tk.Frame(qty_section, bg="#f8f9fa")
        qty_grid.pack(fill="x", padx=30, pady=(0, 20))
        
        # Configure columns with equal weight
        for i in range(3):
            qty_grid.columnconfigure(i, weight=1)
        
        def create_quantity_card(parent, title, value, color="#333", row=0, col=0):
            """Create uniform quantity cards"""
            card = tk.Frame(parent, bg="white", relief="solid", borderwidth=1, height=120)
            card.grid(row=row, column=col, sticky="nsew", padx=10, pady=5)
            card.grid_propagate(False)
            
            # Center content vertically and horizontally
            content = tk.Frame(card, bg="white")
            content.place(relx=0.5, rely=0.5, anchor="center")
            
            tk.Label(content, text=title, font=("Arial", 11, "bold"),
                    bg="white", fg="#666").pack(pady=(0, 8))
            tk.Label(content, text=str(value), font=("Arial", 20, "bold"),
                    bg="white", fg=color).pack()
            
            return card
        
        # Create uniform quantity cards
        create_quantity_card(qty_grid, "Total Quantity", total_qty, "#333", 0, 0)
        
        avail_color = "#dc3545" if available_qty <= min_stock else "#28a745"
        create_quantity_card(qty_grid, "Available", available_qty, avail_color, 0, 1)
        
        create_quantity_card(qty_grid, "Min Stock Level", min_stock, "#ff9800", 0, 2)
        
        # Stock warning with consistent styling
        if available_qty <= min_stock:
            warning_frame = tk.Frame(qty_section, bg="#fff3cd", relief="solid", borderwidth=1)
            warning_frame.pack(fill="x", padx=30, pady=(0, 20))
            warning_content = tk.Frame(warning_frame, bg="#fff3cd")
            warning_content.pack(fill="x", padx=20, pady=12)
            tk.Label(warning_content, text="⚠️ Low stock warning! Please reorder soon.", 
                    font=("Arial", 11, "bold"), bg="#fff3cd", fg="#856404").pack(anchor="w")

    # Description Section with consistent structure
    def create_section(parent, title, content_text, icon="📝"):
        """Create uniform content sections"""
        section = tk.Frame(parent, bg="white")
        section.pack(fill="x", pady=(0, 25))
        
        # Section header
        header = tk.Frame(section, bg="white")
        header.pack(fill="x", pady=(0, 12))
        tk.Label(header, text=f"{icon} {title}", font=("Arial", 16, "bold"),
                bg="white", fg="#005c3c").pack(anchor="w")
        
        # Content box
        content_box = tk.Frame(section, bg="#f8f9fa", relief="solid", borderwidth=1)
        content_box.pack(fill="x")
        
        # Content with consistent padding
        content_label = tk.Label(content_box, text=content_text, font=("Arial", 11),
                               bg="#f8f9fa", fg="#333", anchor="w", wraplength=900, 
                               justify="left")
        content_label.pack(anchor="w", padx=20, pady=18)
        
        return section

    # Create uniform sections
    create_section(content_frame, "Description", description, "📝")
    create_section(content_frame, "Usage Instructions", usage, "📖")

    # Additional Details Section (if any)
    if manufacturer or model or serial_number:
        details_section = tk.Frame(content_frame, bg="white")
        details_section.pack(fill="x", pady=(0, 25))
        
        tk.Label(details_section, text="ℹ️ Additional Information", font=("Arial", 16, "bold"),
                bg="white", fg="#005c3c").pack(anchor="w", pady=(0, 12))
        
        details_box = tk.Frame(details_section, bg="#f8f9fa", relief="solid", borderwidth=1)
        details_box.pack(fill="x")
        
        details_content = tk.Frame(details_box, bg="#f8f9fa")
        details_content.pack(fill="x", padx=20, pady=18)
        
        # Create uniform detail rows
        def create_detail_row(parent, label, value):
            if value:
                row = tk.Frame(parent, bg="#f8f9fa")
                row.pack(fill="x", pady=8)
                
                # Label with fixed width for alignment
                label_frame = tk.Frame(row, bg="#f8f9fa", width=120)
                label_frame.pack(side="left")
                label_frame.pack_propagate(False)
                tk.Label(label_frame, text=label, font=("Arial", 11, "bold"),
                        bg="#f8f9fa", fg="#666", anchor="w").pack(anchor="w")
                
                # Value
                tk.Label(row, text=value, font=("Arial", 11),
                        bg="#f8f9fa", fg="#333", anchor="w").pack(side="left", padx=(10, 0))
        
        create_detail_row(details_content, "Manufacturer:", manufacturer)
        create_detail_row(details_content, "Model:", model)
        create_detail_row(details_content, "Serial Number:", serial_number)

    # Divider before buttons
    tk.Frame(content_frame, bg="#e0e0e0", height=1).pack(fill="x", pady=30)

    # Action Buttons Section
    button_section = tk.Frame(content_frame, bg="white")
    button_section.pack(fill="x", pady=(0, 20))

    # Determine if equipment can be borrowed
    can_borrow = False
    borrow_message = ""
    
    if not is_borrowable:
        borrow_message = "This equipment is not available for borrowing"
    elif tracking_type == "quantity" and available_qty == 0:
        borrow_message = "Out of stock - Cannot borrow at this time"
    elif tracking_type == "individual" and status and status.lower() != "available":
        borrow_message = f"Currently {status} - Cannot borrow at this time"
    else:
        can_borrow = True

    # Info box for borrow status with consistent styling
    if not can_borrow:
        info_box = tk.Frame(button_section, bg="#fff3cd", relief="solid", borderwidth=1)
        info_box.pack(fill="x", pady=(0, 20))
        info_content = tk.Frame(info_box, bg="#fff3cd")
        info_content.pack(fill="x", padx=20, pady=15)
        tk.Label(info_content, text=f"ℹ️ {borrow_message}", 
                font=("Arial", 11, "bold"), bg="#fff3cd", fg="#856404").pack(anchor="w")

    # Buttons with uniform sizing
    button_frame = tk.Frame(button_section, bg="white")
    button_frame.pack()

    def create_action_button(parent, text, command, bg_color, is_primary=False):
        """Create uniform action buttons"""
        btn = tk.Button(parent, text=text, font=("Arial", 11, "bold"),
                      bg=bg_color, fg="white", relief="flat",
                      width=20, height=2, cursor="hand2",
                      activebackground=bg_color, activeforeground="white",
                      command=command)
        if is_primary:
            btn.config(bg="#005c3c", activebackground="#004d32")
        return btn


    # Borrow button (only if borrowable)
    if can_borrow:
        def go_to_borrow():
            from borrow import show_borrow_screen
            show_borrow_screen(root, back_callback=back_callback, user_email=user_email)

        borrow_btn = create_action_button(button_frame, "🛒 Borrow This Equipment", 
                                        go_to_borrow, "#005c3c", is_primary=True)
        borrow_btn.pack(side="left", padx=8)


if __name__ == "__main__":
    root = tk.Tk()
    root.title("Equipment Details")
    root.geometry("1200x800")
    show_equipment_details(root, 1, lambda: print("Back clicked"), "faculty@nursing.com")
    root.mainloop()