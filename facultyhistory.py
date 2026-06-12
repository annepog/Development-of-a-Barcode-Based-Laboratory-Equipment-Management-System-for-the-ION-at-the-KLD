import tkinter as tk
from tkinter import ttk, messagebox
import pymysql
from datetime import datetime

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

def show_faculty_history(root: tk.Tk, back_callback, user_email):
    # Clear window first
    for w in root.winfo_children():
        w.destroy()
    
    root.geometry("1920x1080")
    root.configure(bg="#f5f5f5")

    # Top bar with consistent styling
    header_frame = tk.Frame(root, bg="#2c5530", height=80)
    header_frame.pack(fill="x")
    header_frame.pack_propagate(False)

    header_content = tk.Frame(header_frame, bg="#2c5530")
    header_content.pack(fill="both", expand=True, padx=20, pady=15)

    left_header = tk.Frame(header_content, bg="#2c5530")
    left_header.pack(side="left", fill="y")

    # Back button
    tk.Button(left_header, text="← Back", font=("Arial", 12), bg="#2c5530", fg="white", 
              border=0, cursor="hand2", relief="flat", width=8,
              command=back_callback).pack(side="left", padx=(0, 20))

    # Title
    tk.Label(left_header, text="📊 My Borrowing History", 
             font=("Helvetica", 18, "bold"), bg="#2c5530", fg="white").pack(side="left")

    right_header = tk.Frame(header_content, bg="#2c5530")
    right_header.pack(side="right")

    # User info
    tk.Label(right_header, text=f"User: {user_email}", font=("Arial", 11), 
             bg="#2c5530", fg="white").pack(side="right", padx=(10, 0))

    # Main content area
    main_content = tk.Frame(root, bg="#f5f5f5")
    main_content.pack(expand=True, fill="both", padx=20, pady=20)

    # Statistics Cards Section
    stats_frame = tk.Frame(main_content, bg="#f5f5f5")
    stats_frame.pack(fill="x", pady=(0, 25))

    try:
        conn = get_db_connection()
        if conn is None:
            raise Exception("Could not connect to database")
            
        cursor = conn.cursor()
        
        # Get accurate statistics
        cursor.execute("""
            SELECT 
                COUNT(*) as total_transactions,
                SUM(CASE WHEN action = 'Borrowed' THEN 1 ELSE 0 END) as total_borrowed,
                SUM(CASE WHEN action = 'Returned' THEN 1 ELSE 0 END) as total_returned,
                SUM(CASE WHEN status = 'Ongoing' THEN 1 ELSE 0 END) as ongoing
            FROM transactions 
            WHERE borrower_email = %s
        """, (user_email,))
        
        stats = cursor.fetchone()
        conn.close()
        
        if stats:
            total = stats['total_transactions'] or 0
            borrowed = stats['total_borrowed'] or 0
            returned = stats['total_returned'] or 0
            ongoing = stats['ongoing'] or 0
        else:
            total, borrowed, returned, ongoing = 0, 0, 0, 0
        
        # Create stat cards matching admin dashboard style
        stat_cards_data = [
            ("Total Transactions", total, "#2c5530", "All your activities"),
            ("Items Borrowed", borrowed, "#007bff", "Equipment you've borrowed"),
            ("Items Returned", returned, "#28a745", "Successfully returned"), 
            ("Currently Borrowed", ongoing, "#ff6b35", "Items with you now")
        ]
        
        for i, (label, value, color, subtitle) in enumerate(stat_cards_data):
            # Card with shadow effect
            shadow = tk.Frame(stats_frame, bg="#d0d0d0")
            shadow.pack(side="left", fill="both", expand=True, padx=(0, 10 if i < 3 else 0), pady=5)
            
            card = tk.Frame(shadow, bg="white", relief="flat")
            card.pack(fill="both", expand=True, padx=2, py=2)
            
            # Card content
            tk.Label(card, text=str(value), font=("Helvetica", 28, "bold"),
                    bg="white", fg=color).pack(pady=(20, 5))
            
            tk.Label(card, text=label, font=("Helvetica", 11, "bold"),
                    bg="white", fg="#333").pack(pady=(0, 2))
            
            tk.Label(card, text=subtitle, font=("Helvetica", 9),
                    bg="white", fg="#999").pack(pady=(0, 15))
                    
    except Exception as e:
        print(f"Stats error: {e}")
        # REMOVED: Error card display for statistics

    # Search and Filter Section with shadow
    search_shadow = tk.Frame(main_content, bg="#d0d0d0")
    search_shadow.pack(fill="x", pady=(0, 25))
    
    search_section = tk.Frame(search_shadow, bg="white", relief="flat")
    search_section.pack(fill="x", padx=2, pady=2)
    
    # Search header
    search_header = tk.Frame(search_section, bg="#e8f5e9", height=50)
    search_header.pack(fill="x")
    search_header.pack_propagate(False)
    
    tk.Label(search_header, text="Search & Filter Transactions", font=("Arial", 13, "bold"),
             bg="#e8f5e9", fg="#2c5530").pack(anchor="w", padx=30, pady=15)
    
    # Search content
    search_content = tk.Frame(search_section, bg="white")
    search_content.pack(fill="x", padx=40, pady=25)

    # Search row
    search_row = tk.Frame(search_content, bg="white")
    search_row.pack(fill="x", pady=(0, 15))

    tk.Label(search_row, text="🔍 Search:", font=("Arial", 11, "bold"),
             bg="white", fg="#333").pack(side="left", padx=(0, 15))

    search_var = tk.StringVar()
    search_entry = tk.Entry(search_row, textvariable=search_var, font=("Arial", 11),
                           width=30, relief="solid", bd=1, bg="white")
    search_entry.pack(side="left", padx=(0, 15), ipady=4)

    def search_transactions():
        search_term = search_var.get().lower()
        if not search_term:
            refresh_table()
            return
            
        for item in tree.get_children():
            values = tree.item(item)['values']
            # Search in equipment name and barcode
            if (search_term in values[1].lower() or  # equipment
                search_term in values[2].lower()):   # barcode
                tree.selection_set(item)
                tree.focus(item)
            else:
                tree.delete(item)

    search_btn = tk.Button(search_row, text="Search", font=("Arial", 10, "bold"),
                          bg="#005c3c", fg="white", relief="flat", cursor="hand2",
                          padx=20, pady=6, command=search_transactions)
    search_btn.pack(side="left", padx=(0, 10))

    clear_btn = tk.Button(search_row, text="Clear", font=("Arial", 10, "bold"),
                         bg="#999", fg="white", relief="flat", cursor="hand2",
                         padx=20, pady=6, command=lambda: [search_var.set(""), refresh_table()])
    clear_btn.pack(side="left", padx=(0, 20))

    # Export button
    def export_history():
        try:
            conn = get_db_connection()
            if conn is None:
                raise Exception("Could not connect to database")
                
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT datetime, equipment_name, barcode, action, status, handled_by
                FROM transactions 
                WHERE borrower_email = %s
                ORDER BY datetime DESC
            """, (user_email,))
            
            transactions = cursor.fetchall()
            conn.close()
            
            # Simple export to text file
            filename = f"borrowing_history_{user_email.split('@')[0]}.txt"
            with open(filename, 'w', encoding='utf-8') as f:
                f.write(f"Borrowing History for {user_email}\n")
                f.write("=" * 50 + "\n\n")
                
                for trans in transactions:
                    f.write(f"Date: {trans['datetime']}\n")
                    f.write(f"Equipment: {trans['equipment_name']}\n")
                    f.write(f"Barcode: {trans['barcode']}\n")
                    f.write(f"Action: {trans['action']}\n")
                    f.write(f"Status: {trans['status']}\n")
                    f.write(f"Handled By: {trans['handled_by']}\n")
                    f.write("-" * 30 + "\n")
            
            messagebox.showinfo("Export Successful", 
                              f"Your borrowing history has been exported to:\n{filename}")
            
        except Exception as e:
            print(f"Export error: {e}")
            messagebox.showerror("Export Failed", "Could not export history")

    export_btn = tk.Button(search_row, text="📥 Export History", font=("Arial", 10, "bold"),
                          bg="#17a2b8", fg="white", relief="flat", cursor="hand2",
                          padx=20, pady=6, command=export_history)
    export_btn.pack(side="right")

    # Filter row
    filter_row = tk.Frame(search_content, bg="white")
    filter_row.pack(fill="x")

    tk.Label(filter_row, text="Filter by Status:", font=("Arial", 11, "bold"),
             bg="white", fg="#333").pack(side="left", padx=(0, 15))

    filter_var = tk.StringVar(value="all")

    def apply_filter():
        refresh_table()

    filter_options = [
        ("All Transactions", "all"),
        ("Borrowed Items", "borrowed"), 
        ("Returned Items", "returned"),
        ("Ongoing", "ongoing"),
        ("Completed", "completed")
    ]

    for text, value in filter_options:
        tk.Radiobutton(filter_row, text=text, variable=filter_var, value=value,
                      bg="white", font=("Arial", 10), command=apply_filter).pack(side="left", padx=10)

    # Table Section with shadow
    table_shadow = tk.Frame(main_content, bg="#d0d0d0")
    table_shadow.pack(fill="both", expand=True)
    
    table_section = tk.Frame(table_shadow, bg="white", relief="flat")
    table_section.pack(fill="both", expand=True, padx=2, pady=2)
    
    # Table header
    table_header = tk.Frame(table_section, bg="#e3f2fd", height=50)
    table_header.pack(fill="x")
    table_header.pack_propagate(False)
    
    tk.Label(table_header, text="Transaction History", font=("Arial", 13, "bold"),
             bg="#e3f2fd", fg="#2c5530").pack(side="left", padx=30, pady=15)

    # Refresh button in header
    def refresh_history():
        refresh_table()

    refresh_btn = tk.Button(table_header, text="🔄 Refresh", font=("Arial", 10, "bold"),
                           bg="#28a745", fg="white", relief="flat", cursor="hand2",
                           padx=15, pady=5, command=refresh_history)
    refresh_btn.pack(side="right", padx=30)

    # Count label in header
    count_label = tk.Label(table_header, text="Total: 0", font=("Arial", 11),
                          bg="#e3f2fd", fg="#2c5530")
    count_label.pack(side="right", padx=30)

    # Table frame with scrollbar
    table_frame = tk.Frame(table_section, bg="white")
    table_frame.pack(fill="both", expand=True, padx=20, pady=20)

    # Scrollbars
    vsb = ttk.Scrollbar(table_frame, orient="vertical")
    vsb.pack(side="right", fill="y")
    
    hsb = ttk.Scrollbar(table_frame, orient="horizontal")
    hsb.pack(side="bottom", fill="x")

    # Treeview with modern styling
    columns = ("datetime", "equipment", "barcode", "action", "status", "handled_by")
    
    tree = ttk.Treeview(table_frame, columns=columns, show="headings", height=15,
                       yscrollcommand=vsb.set, xscrollcommand=hsb.set)
    tree.pack(fill="both", expand=True)
    
    vsb.config(command=tree.yview)
    hsb.config(command=tree.xview)

    # Configure columns
    column_configs = [
        ("datetime", "Date & Time", 180),
        ("equipment", "Equipment", 250),
        ("barcode", "Barcode", 140),
        ("action", "Action", 100),
        ("status", "Status", 120),
        ("handled_by", "Handled By", 150)
    ]

    for col_id, heading, width in column_configs:
        tree.heading(col_id, text=heading)
        tree.column(col_id, width=width, anchor="center")

    # Enhanced style for table
    style = ttk.Style()
    style.configure("Treeview", 
                   background="white",
                   foreground="#333",
                   fieldbackground="white",
                   rowheight=30,
                   font=("Arial", 10))
    style.configure("Treeview.Heading",
                   font=("Arial", 10, "bold"),
                   background="#f0f0f0",
                   foreground="#2c5530")
    style.map("Treeview", background=[("selected", "#2c5530")])
    
    # Tag configurations for alternating rows and status colors
    tree.tag_configure('oddrow', background='#f9f9f9')
    tree.tag_configure('evenrow', background='white')
    tree.tag_configure('ongoing', background='#fff3cd')
    tree.tag_configure('completed', background='#d4edda')
    tree.tag_configure('borrowed', background='#e7f3ff')
    tree.tag_configure('returned', background='#f8f9fa')

    # Load data function
    def refresh_table():
        # Clear existing data
        for item in tree.get_children():
            tree.delete(item)
        
        try:
            conn = get_db_connection()
            if conn is None:
                raise Exception("Could not connect to database")
                
            cursor = conn.cursor()
            
            # Base query
            query = """
                SELECT datetime, equipment_name, barcode, action, status, handled_by 
                FROM transactions 
                WHERE borrower_email = %s
            """
            params = [user_email]
            
            # Apply filter
            filter_type = filter_var.get()
            if filter_type == "borrowed":
                query += " AND action = 'Borrowed'"
            elif filter_type == "returned":
                query += " AND action = 'Returned'"
            elif filter_type == "ongoing":
                query += " AND status = 'Ongoing'"
            elif filter_type == "completed":
                query += " AND status = 'Completed'"
            
            query += " ORDER BY datetime DESC"
            
            cursor.execute(query, params)
            transactions = cursor.fetchall()
            conn.close()
            
            # Populate treeview
            for idx, trans in enumerate(transactions):
                datetime_str = trans['datetime']
                equipment = trans['equipment_name']
                barcode = trans['barcode']
                action = trans['action']
                status = trans['status']
                handled_by = trans['handled_by']
                
                # Format datetime for better display
                if len(datetime_str) >= 16:
                    try:
                        dt = datetime.strptime(datetime_str[:16], "%Y-%m-%d %H:%M")
                        formatted_date = dt.strftime("%b %d, %Y at %I:%M %p")
                    except:
                        formatted_date = datetime_str[:16]
                else:
                    formatted_date = datetime_str
                
                # Determine row tag based on status and alternating rows
                base_tag = 'evenrow' if idx % 2 == 0 else 'oddrow'
                status_tag = ''
                
                if status == "Ongoing":
                    status_tag = 'ongoing'
                elif status == "Completed":
                    status_tag = 'completed'
                elif action == "Borrowed":
                    status_tag = 'borrowed'
                elif action == "Returned":
                    status_tag = 'returned'
                
                # Combine tags
                tags = (base_tag, status_tag) if status_tag else (base_tag,)
                
                # Insert with status-based coloring
                item_id = tree.insert("", "end", values=(
                    formatted_date, equipment, barcode, action, status, handled_by
                ), tags=tags)
                
            # Update count
            count_label.config(text=f"Total: {len(transactions)}")
            
            # Show message if no data
            if not transactions:
                no_data_frame = tk.Frame(table_frame, bg="white")
                no_data_frame.place(relx=0.5, rely=0.5, anchor="center")
                tk.Label(no_data_frame, text="📭\nNo transactions found for the selected filter", 
                        font=("Arial", 14), bg="white", fg="#999").pack(pady=20)
                
        except Exception as e:
            print(f"Database error: {e}")
            error_frame = tk.Frame(table_frame, bg="white")
            error_frame.place(relx=0.5, rely=0.5, anchor="center")
            tk.Label(error_frame, text="❌\nError loading transactions", 
                    font=("Arial", 14), bg="white", fg="#dc3545").pack(pady=20)

    # Double-click to view details
    def on_item_double_click(event):
        selection = tree.selection()
        if not selection:
            return
            
        item = selection[0]
        values = tree.item(item)['values']
        
        # Show details in a messagebox
        details = f"""
Equipment: {values[1]}
Barcode: {values[2]}
Action: {values[3]}
Status: {values[4]}
Date & Time: {values[0]}
Handled By: {values[5]}
        """.strip()
        
        messagebox.showinfo("Transaction Details", details)

    tree.bind("<Double-1>", on_item_double_click)

    # Bind Enter key to search
    search_entry.bind("<Return>", lambda e: search_transactions())

    # Initial load
    refresh_table()

    # Auto-refresh every 30 seconds
    def auto_refresh():
        refresh_table()
        root.after(30000, auto_refresh)

    root.after(30000, auto_refresh)