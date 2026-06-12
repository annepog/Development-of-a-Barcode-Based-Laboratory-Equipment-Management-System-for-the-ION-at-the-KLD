# borrow.py - Enhanced with proper borrower tracking
import tkinter as tk
from tkinter import Frame, Label, Entry, Button, messagebox, Spinbox
from datetime import datetime
import pymysql
from PIL import Image, ImageTk
from tkinter import ttk
import os
import sys

def resource_path(relative_path):
    """Get absolute path to resource, works for dev and for PyInstaller"""
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

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

def show_borrow_screen(root, back_callback, user_email):
    
    def test_database_connection():
        """Test function to check database contents directly"""
        try:
            conn = get_db_connection()
            if conn is None:
                print("TEST: Cannot connect to database")
                return
                
            cursor = conn.cursor()
            
            # Test 1: Check all quantity items
            cursor.execute("""
                SELECT id, name, variant, available_quantity, total_quantity, 
                       is_borrowable, tracking_type, barcode
                FROM equipment 
                WHERE tracking_type = 'quantity'
                AND (is_archived = 0 OR is_archived IS NULL)
                ORDER BY name, variant
            """)
            all_items = cursor.fetchall()
            
            print("TEST: ALL QUANTITY ITEMS IN DATABASE:")
            for item in all_items:
                print(f"  - {item['name']} ({item['variant']}) - "
                      f"Stock: {item['available_quantity']}/{item['total_quantity']} - "
                      f"is_borrowable: {item['is_borrowable']} - Barcode: {item['barcode']}")
            
            # Test 2: Specifically look for the items you mentioned
            target_items = ['Syringe', 'Colostomy Bag', 'Blood Bag']
            for target in target_items:
                cursor.execute("""
                    SELECT name, variant, is_borrowable 
                    FROM equipment 
                    WHERE name LIKE %s 
                    AND tracking_type = 'quantity'
                    AND (is_archived = 0 OR is_archived IS NULL)
                """, (f'%{target}%',))
                matches = cursor.fetchall()
                print(f"TEST: Searching for '{target}': Found {len(matches)} matches")
                for match in matches:
                    print(f"     - {match['name']} ({match['variant']}) - is_borrowable: {match['is_borrowable']}")
            
            conn.close()
        except Exception as e:
            print(f"TEST ERROR: {e}")

    def record_borrow(barcode, quantity=1):
        """Handle borrowing for both individual and quantity-tracked items"""
        if not barcode:
            show_message("Please enter a barcode", "error")
            return
            
        conn = get_db_connection()
        if conn is None:
            return

        cursor = conn.cursor()

        try:
            # Get equipment info including tracking type AND is_borrowable
            cursor.execute("""
                SELECT id, name, tracking_type, available_quantity, total_quantity, 
                    availability_status, is_borrowable
                FROM equipment WHERE barcode = %s AND COALESCE(is_archived, 0) = 0
            """, (barcode,))
            result = cursor.fetchone()
            
            if not result:
                show_message("Equipment not found", "error")
                conn.close()
                return
            
            # Safety check - ensure item is borrowable
            is_borrowable = result['is_borrowable']
            if is_borrowable == 0:
                show_message("This item is a consumable and cannot be borrowed", "error")
                conn.close()
                return
            
            equipment_id = result['id']
            item_name = result['name']
            tracking_type = result['tracking_type']
            avail_qty = result['available_quantity']
            total_qty = result['total_quantity']
            avail_status = result['availability_status']

            # Get borrower info
            cursor.execute("""
                SELECT up.full_name 
                FROM user_profiles up
                JOIN users u ON up.user_id = u.id
                WHERE u.email = %s
            """, (user_email,))
            
            profile_result = cursor.fetchone()
            borrower_name = profile_result['full_name'] if profile_result else user_email

            # Handle based on tracking type
            if tracking_type == "individual":
                if avail_status and avail_status.lower() != 'available':
                    show_message(f"'{item_name}' is currently {avail_status}", "error")
                    conn.close()
                    return
                
                quantity = 1
                
            elif tracking_type == "quantity":
                if avail_qty < quantity:
                    show_message(f"Insufficient stock. Only {avail_qty} available", "error")
                    conn.close()
                    return
                
                if avail_qty == 0:
                    show_message(f"'{item_name}' is out of stock", "error")
                    conn.close()
                    return
            
            # Get borrow timestamp
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

            # Update equipment based on tracking type
            if tracking_type == "individual":
                cursor.execute("""
                    UPDATE equipment SET availability_status = 'Borrowed' 
                    WHERE barcode = %s
                """, (barcode,))
            else:
                new_available = avail_qty - quantity
                cursor.execute("""
                    UPDATE equipment SET available_quantity = %s 
                    WHERE barcode = %s
                """, (new_available, barcode))

            # Insert into borrow table
            cursor.execute("""
                INSERT INTO borrow (equipment_id, barcode, borrow_time, quantity_borrowed, borrower_email, borrower_name, return_status)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
            """, (equipment_id, barcode, timestamp, quantity, user_email, borrower_name, 'Borrowed'))

            # Log transaction based on tracking type
            if tracking_type == "individual":
                action = "Borrowed"
                status = "Ongoing"
                remarks = "Equipment borrowed"
            else:
                action = "Borrowed"
                status = "Ongoing"
                remarks = "Quantity borrowed"

            cursor.execute("""
                INSERT INTO transactions (
                    datetime, borrower_name, borrower_email, equipment_name, barcode,
                    action, status, handled_by, remarks, quantity
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, (timestamp, borrower_name, user_email, item_name, barcode,
                action, status, "System", remarks, quantity))

            conn.commit()
            conn.close()
            
            # Show success
            if tracking_type == "quantity":
                remaining = avail_qty - quantity
                show_message(f"Borrowed {quantity}x {item_name} ({remaining} remaining)", "success")
                messagebox.showinfo("Success", 
                    f"Successfully borrowed {quantity} {item_name}!\n\n"
                    f"Barcode: {barcode}\n"
                    f"Time: {timestamp}\n"
                    f"Remaining stock: {remaining}/{total_qty}")
            else:
                show_message(f"Successfully borrowed: {item_name}", "success")
                messagebox.showinfo("Success", 
                    f"Equipment '{item_name}' successfully borrowed!\n\n"
                    f"Barcode: {barcode}\n"
                    f"Time: {timestamp}")
            
            add_to_session_list(item_name, barcode, quantity, timestamp, "Borrowed")
                
        except Exception as e:
            show_message(f"Error: {e}", "error")
            messagebox.showerror("Error", str(e))
        finally:
            if conn:
                conn.close()

    def record_consumable_usage(equipment_id, item_name, quantity):
        """Handle consumable usage (non-borrowable items)"""
        conn = get_db_connection()
        if conn is None:
            return
            
        cursor = conn.cursor()
        
        try:
            # Get current stock and verify it's a consumable
            cursor.execute("""
                SELECT available_quantity, total_quantity, is_borrowable, tracking_type
                FROM equipment WHERE id = %s
            """, (equipment_id,))
            result = cursor.fetchone()
            
            if not result:
                show_consumable_message("Consumable not found", "error")
                conn.close()
                return
            
            avail_qty = result['available_quantity']
            total_qty = result['total_quantity']
            is_borrowable = result['is_borrowable']
            tracking_type = result['tracking_type']
            
            # Additional validation - ensure it's a quantity item and not borrowable
            if tracking_type != 'quantity' or is_borrowable != 0:
                show_consumable_message("Selected item is not a consumable", "error")
                conn.close()
                return
            
            # Check stock
            if avail_qty < quantity:
                show_consumable_message(f"Insufficient stock. Only {avail_qty} available", "error")
                conn.close()
                return
            
            if avail_qty == 0:
                show_consumable_message(f"'{item_name}' is out of stock", "error")
                conn.close()
                return
            
            # Get user info
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            
            cursor.execute("""
                SELECT up.full_name 
                FROM user_profiles up
                JOIN users u ON up.user_id = u.id
                WHERE u.email = %s
            """, (user_email,))
            
            profile_result = cursor.fetchone()
            user_name = profile_result['full_name'] if profile_result else user_email
            
            # Update stock
            new_available = avail_qty - quantity
            cursor.execute("""
                UPDATE equipment SET available_quantity = %s 
                WHERE id = %s
            """, (new_available, equipment_id))
            
            # Get barcode for transaction
            cursor.execute("SELECT barcode FROM equipment WHERE id = %s", (equipment_id,))
            barcode_result = cursor.fetchone()
            barcode = barcode_result['barcode'] if barcode_result else "N/A"
            
            # Log transaction
            cursor.execute("""
                INSERT INTO transactions (
                    datetime, borrower_name, borrower_email, equipment_name, barcode,
                    action, status, handled_by, remarks, quantity
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, (timestamp, user_name, user_email, item_name, barcode,
                "Consumed", "Completed", "System", "Consumable usage", quantity))
            
            conn.commit()
            conn.close()
            
            # Show success
            remaining = avail_qty - quantity
            show_consumable_message(f"Used {quantity}x {item_name} ({remaining} remaining)", "success")
            messagebox.showinfo("Success", 
                f"Successfully recorded usage of {quantity} {item_name}!\n\n"
                f"Time: {timestamp}\n"
                f"Remaining stock: {remaining}/{total_qty}")
            
            add_to_session_list(item_name, barcode, quantity, timestamp, "Consumed")
            
        except Exception as e:
            show_consumable_message(f"Error: {e}", "error")
            messagebox.showerror("Error", str(e))
        finally:
            if conn:
                conn.close()

    def add_to_session_list(item_name, barcode, quantity, timestamp, action):
        """Add to current session display"""
        session_list.insert(0, f"{action}: {quantity}x {item_name} ({barcode}) - {timestamp}")
        update_session_count()

    def update_session_count():
        """Update session counter"""
        count = session_list.size()
        session_count_label.config(text=f"Items processed this session: {count}")

    def show_message(message, msg_type):
        """Show inline message for equipment"""
        message_label.config(text=message)
        if msg_type == "success":
            message_label.config(fg="#28a745")
        else:
            message_label.config(fg="#dc3545")
        root.after(3000, lambda: message_label.config(text=""))

    def show_consumable_message(message, msg_type):
        """Show inline message for consumables"""
        consumable_message_label.config(text=message)
        if msg_type == "success":
            consumable_message_label.config(fg="#28a745")
        else:
            consumable_message_label.config(fg="#dc3545")
        root.after(3000, lambda: consumable_message_label.config(text=""))

    def process_barcode():
        """Process barcode scan for borrowable items only"""
        barcode = scan_entry.get().strip()
        if not barcode:
            messagebox.showwarning("Input Required", "Please enter a barcode")
            return
        
        # Check if item exists and is borrowable
        conn = get_db_connection()
        if conn is None:
            return
            
        cursor = conn.cursor()
        cursor.execute("""
            SELECT tracking_type, name, is_borrowable 
            FROM equipment 
            WHERE barcode = %s AND COALESCE(is_archived, 0) = 0
        """, (barcode,))
        result = cursor.fetchone()
        conn.close()
        
        if not result:
            show_message("Equipment not found", "error")
            scan_entry.delete(0, tk.END)
            return
        
        tracking_type = result['tracking_type']
        name = result['name']
        is_borrowable = result['is_borrowable']
        
        # Check if item is borrowable
        if is_borrowable == 0:
            show_message(f"'{name}' is a consumable - use the consumables section", "error")
            scan_entry.delete(0, tk.END)
            return
        
        if tracking_type == "quantity":
            show_quantity_dialog(barcode, name)
        else:
            record_borrow(barcode, 1)
            scan_entry.delete(0, tk.END)
            scan_entry.focus_set()

    def show_quantity_dialog(barcode, name):
        """Show dialog to select quantity for batch items"""
        dialog = tk.Toplevel(root)
        dialog.title("Select Quantity")
        dialog.geometry("400x250")
        dialog.configure(bg="white")
        dialog.transient(root)
        dialog.grab_set()
        
        # Center dialog
        dialog.update_idletasks()
        x = root.winfo_x() + (root.winfo_width() // 2) - (dialog.winfo_width() // 2)
        y = root.winfo_y() + (root.winfo_height() // 2) - (dialog.winfo_height() // 2)
        dialog.geometry(f"+{x}+{y}")
        
        Label(dialog, text=f"How many {name}?", font=("Arial", 14, "bold"),
              bg="white", fg="#333").pack(pady=(30, 20))
        
        Label(dialog, text="Select quantity to borrow:", font=("Arial", 11),
              bg="white", fg="#666").pack(pady=(0, 15))
        
        quantity_var = tk.IntVar(value=1)
        
        spinbox = Spinbox(dialog, from_=1, to=100, textvariable=quantity_var,
                         font=("Arial", 16), width=10, justify="center")
        spinbox.pack(pady=15)
        
        button_frame = Frame(dialog, bg="white")
        button_frame.pack(pady=20)
        
        def confirm():
            qty = quantity_var.get()
            dialog.destroy()
            record_borrow(barcode, qty)
            scan_entry.delete(0, tk.END)
            scan_entry.focus_set()
        
        Button(button_frame, text="Cancel", font=("Arial", 11),
               bg="#999", fg="white", relief="flat", padx=20, pady=8,
               command=dialog.destroy).pack(side="left", padx=5)
        
        Button(button_frame, text="Confirm Borrow", font=("Arial", 11, "bold"),
               bg="#005c3c", fg="white", relief="flat", padx=20, pady=8,
               command=confirm).pack(side="left", padx=5)
        
        spinbox.focus_set()
        dialog.bind("<Return>", lambda e: confirm())

    def load_consumables():
        """Load consumables from database - non-borrowable quantity items"""
        try:
            conn = get_db_connection()
            if conn is None:
                return []
                
            cursor = conn.cursor()
            
            print("DEBUG: Loading consumables (is_borrowable = 0)...")
            
            # First, let's check what's actually in the database
            cursor.execute("""
                SELECT COUNT(*) as total_count 
                FROM equipment 
                WHERE tracking_type = 'quantity'
                AND (is_archived = 0 OR is_archived IS NULL)
            """)
            total_quantity_items = cursor.fetchone()['total_count']
            print(f"DEBUG: Total quantity items in DB: {total_quantity_items}")
            
            # Check borrowable vs consumable distribution
            cursor.execute("""
                SELECT is_borrowable, COUNT(*) as count 
                FROM equipment 
                WHERE tracking_type = 'quantity'
                AND (is_archived = 0 OR is_archived IS NULL)
                GROUP BY is_borrowable
            """)
            distribution = cursor.fetchall()
            print("DEBUG: Quantity items distribution by is_borrowable:")
            for dist in distribution:
                status = "borrowable" if dist['is_borrowable'] == 1 else "consumable"
                print(f"DEBUG:   {status} (is_borrowable={dist['is_borrowable']}): {dist['count']} items")
            
            # Get only consumables (is_borrowable = 0) that are quantity-tracked
            query = """
                SELECT id, name, variant, available_quantity, total_quantity, barcode,
                    is_borrowable, tracking_type
                FROM equipment 
                WHERE tracking_type = 'quantity'
                AND is_borrowable = 0
                AND (is_archived = 0 OR is_archived IS NULL)
                ORDER BY name, variant
            """
            
            print(f"DEBUG: Executing query: {query}")
            cursor.execute(query)
            consumable_items = cursor.fetchall()
            
            print(f"DEBUG: Found {len(consumable_items)} consumable items")
            
            # Print detailed info about each found item
            for item in consumable_items:
                print(f"DEBUG: Consumable Item - ID: {item['id']}, Name: {item['name']}, Variant: {item['variant']}, "
                      f"Available: {item['available_quantity']}, Total: {item['total_quantity']}, "
                      f"is_borrowable: {item['is_borrowable']}")
            
            consumables = []
            
            for item in consumable_items:
                item_id = item['id']
                name = item['name']
                variant = item['variant']
                avail_qty = item['available_quantity']
                total_qty = item['total_quantity']
                barcode = item['barcode']
                is_borrowable = item['is_borrowable']
                tracking_type = item['tracking_type']
                
                display_name = f"{name} ({variant})" if variant else name
                consumables.append((item_id, name, variant, avail_qty, total_qty, barcode, display_name))
                print(f"ADDED TO CONSUMABLES: {display_name}")
            
            conn.close()
            
            print(f"FINAL: Returning {len(consumables)} consumables")
            return consumables
            
        except Exception as e:
            print(f"Error loading consumables: {e}")
            import traceback
            traceback.print_exc()
            return []

    def refresh_consumable_dropdown():
        """Refresh the consumable dropdown list"""
        # First run the test to see what's in the database
        test_database_connection()
        
        consumables = load_consumables()
        
        # Update the combobox values
        if not consumables:
            print("DEBUG: No consumables found, setting dropdown to empty")
            consumable_menu['values'] = ["No consumables available"]
            consumable_var.set("No consumables available")
            consumable_data.clear()
            consumable_spinbox.config(state="disabled")
            record_button.config(state="disabled")
        else:
            print(f"DEBUG: Found {len(consumables)} consumables, populating dropdown")
            display_items = []
            consumable_data.clear()
            for consumable in consumables:
                equip_id = consumable[0]
                name = consumable[1]
                variant = consumable[2]
                avail_qty = consumable[3]
                total_qty = consumable[4]
                barcode = consumable[5]
                display_name = consumable[6]
                
                display_text = f"{display_name} - Stock: {avail_qty}/{total_qty}"
                display_items.append(display_text)
                
                consumable_data[display_text] = {
                    'id': equip_id,
                    'name': display_name,
                    'available': avail_qty,
                    'total': total_qty,
                    'barcode': barcode
                }
            
            consumable_menu['values'] = display_items
            
            if display_items:
                consumable_var.set(display_items[0])
                consumable_spinbox.config(state="normal")
                record_button.config(state="normal")
                print(f"DEBUG: Dropdown populated with {len(display_items)} items")
            else:
                consumable_var.set("No consumables available")
                consumable_spinbox.config(state="disabled")
                record_button.config(state="disabled")

    def process_consumable():
        """Process consumable usage"""
        selected = consumable_var.get()
        
        if selected == "No consumables available" or selected == "Select consumable...":
            messagebox.showwarning("Selection Required", "Please select a consumable")
            return
        
        if selected not in consumable_data:
            messagebox.showerror("Error", "Invalid consumable selection")
            return
        
        try:
            quantity = int(consumable_quantity_var.get())
            if quantity < 1:
                messagebox.showerror("Error", "Quantity must be at least 1")
                return
        except ValueError:
            messagebox.showerror("Error", "Please enter a valid quantity")
            return
        
        data = consumable_data[selected]
        record_consumable_usage(data['id'], data['name'], quantity)
        
        consumable_quantity_var.set(1)
        refresh_consumable_dropdown()

    # --- UI Setup ---
    for w in root.winfo_children():
        w.destroy()
    
    root.configure(bg="#f5f5f5")

    # Top bar
    top = Frame(root, bg="#005c3c", height=70)
    top.pack(fill="x")
    top.pack_propagate(False)
    
    Button(top, text="Back", font=("Arial", 12), bg="#005c3c", fg="white", border=0,
           cursor="hand2", relief="flat", command=back_callback).pack(side="left", padx=30, pady=20)
    
    Label(top, text="Borrow Equipment & Use Consumables", font=("Arial", 16, "bold"),
          fg="white", bg="#005c3c").pack(side="left", padx=10, pady=20)

    # Main content
    main = Frame(root, bg="#f5f5f5")
    main.pack(expand=True, fill="both")
    
    try:
        bg_path = resource_path("background.jpg")
        bg_image = Image.open(bg_path)
        screen_width = root.winfo_screenwidth()
        screen_height = root.winfo_screenheight()
        bg_image = bg_image.resize((screen_width, screen_height - 70))
        bg_photo = ImageTk.PhotoImage(bg_image)
        bg_label = Label(main, image=bg_photo)
        bg_label.image = bg_photo
        bg_label.place(x=0, y=0, relwidth=1, relheight=1)
    except Exception as e:
        print(f"Background image not found: {e}")

    content_container = Frame(main, bg="#f5f5f5")
    content_container.pack(expand=True, fill="both", padx=60, pady=40)

    # Two-column layout
    columns_frame = Frame(content_container, bg="#f5f5f5")
    columns_frame.pack(fill="x", pady=(0, 25))
    
    # LEFT COLUMN - Equipment Borrowing
    left_column = Frame(columns_frame, bg="#f5f5f5")
    left_column.pack(side="left", fill="both", expand=True, padx=(0, 12))
    
    shadow1 = Frame(left_column, bg="#d0d0d0")
    shadow1.pack(fill="both", expand=True)
    
    input_section = Frame(shadow1, bg="white", relief="flat")
    input_section.pack(fill="both", expand=True, padx=2, pady=2)
    
    input_header = Frame(input_section, bg="#e8f5e9", height=60)
    input_header.pack(fill="x")
    input_header.pack_propagate(False)
    
    Label(input_header, text="Borrow Equipment", font=("Arial", 15, "bold"),
          bg="#e8f5e9", fg="#005c3c").pack(expand=True)
    
    input_content = Frame(input_section, bg="white")
    input_content.pack(fill="both", expand=True, padx=40, pady=30)
    
    # Message label
    message_label = Label(input_content, text="", font=("Arial", 10, "bold"),
                         bg="white", height=1)
    message_label.pack(pady=(0, 10))
    
    Label(input_content, text="Scan equipment barcode or enter manually:",
          font=("Arial", 11), bg="white", fg="#666").pack(pady=(0, 15))
    
    # Info box
    info_frame = Frame(input_content, bg="#e3f2fd", relief="solid", borderwidth=1)
    info_frame.pack(fill="x", pady=(0, 25))
    
    Label(info_frame, text="Individual items borrow instantly. Quantity items will prompt for amount.",
          font=("Arial", 9), bg="#e3f2fd", fg="#1976d2", wraplength=480, justify="center").pack(padx=15, pady=12)
    
    scan_frame = Frame(input_content, bg="white")
    scan_frame.pack(pady=(0, 10))
    
    scan_entry = Entry(scan_frame, font=("Arial", 14), width=22, justify="center",
                      relief="solid", borderwidth=2, bg="white")  # REMOVED green background
    scan_entry.pack(side="left", ipady=12, padx=(0, 15))
    
    Button(scan_frame, text="Process", font=("Arial", 12, "bold"),
           bg="#005c3c", fg="white", relief="flat", width=14, cursor="hand2",
           command=process_barcode).pack(side="left", ipady=10)
    
    scan_entry.bind("<Return>", lambda e: process_barcode())
    scan_entry.focus_set()
    
    # RIGHT COLUMN - Consumables
    right_column = Frame(columns_frame, bg="#f5f5f5")
    right_column.pack(side="left", fill="both", expand=True, padx=(12, 0))
    
    shadow2 = Frame(right_column, bg="#d0d0d0")
    shadow2.pack(fill="both", expand=True)
    
    consumable_section = Frame(shadow2, bg="white", relief="flat")
    consumable_section.pack(fill="both", expand=True, padx=2, pady=2)
    
    consumable_header = Frame(consumable_section, bg="#fff3e0", height=60)
    consumable_header.pack(fill="x")
    consumable_header.pack_propagate(False)
    
    Label(consumable_header, text="Use Consumables", font=("Arial", 15, "bold"),
          bg="#fff3e0", fg="#e65100").pack(expand=True)
    
    consumable_content = Frame(consumable_section, bg="white")
    consumable_content.pack(fill="both", expand=True, padx=40, pady=30)
    
    # Message label
    consumable_message_label = Label(consumable_content, text="", font=("Arial", 10, "bold"),
                                     bg="white", height=1)
    consumable_message_label.pack(pady=(0, 10))
    
    Label(consumable_content, text="Select consumable to use:",
          font=("Arial", 11), bg="white", fg="#666").pack(pady=(0, 15))
    
    # Info box
    consumable_info_frame = Frame(consumable_content, bg="#fff3e0", relief="solid", borderwidth=1)
    consumable_info_frame.pack(fill="x", pady=(0, 25))
    
    Label(consumable_info_frame, text="Consumables are tracked but not returned. Usage is logged immediately.",
          font=("Arial", 9), bg="#fff3e0", fg="#e65100", wraplength=480, justify="center").pack(padx=15, pady=12)
    
    # Dropdown
    consumable_var = tk.StringVar(value="Select consumable...")
    consumable_data = {}
    
    dropdown_frame = Frame(consumable_content, bg="white")
    dropdown_frame.pack(pady=(0, 20))
    
    consumable_menu = ttk.Combobox(dropdown_frame, textvariable=consumable_var,
                                   font=("Arial", 11), state="readonly", width=32)
    consumable_menu.pack()
    
    # Quantity - REMOVED green background
    quantity_frame = Frame(consumable_content, bg="white")
    quantity_frame.pack(pady=(0, 25))
    
    Label(quantity_frame, text="Quantity:", font=("Arial", 11, "bold"), 
          bg="white", fg="#333").pack(side="left", padx=(0, 15))
    
    consumable_quantity_var = tk.IntVar(value=1)
    consumable_spinbox = Spinbox(quantity_frame, from_=1, to=100, 
                                 textvariable=consumable_quantity_var,
                                 font=("Arial", 13), width=12, justify="center",
                                 relief="solid", borderwidth=1, bg="white")  # REMOVED green background
    consumable_spinbox.pack(side="left")
    
    record_button = Button(consumable_content, text="Record Usage", font=("Arial", 12, "bold"),
        bg="#ff9800", fg="white", relief="flat", width=20, cursor="hand2",
        command=process_consumable)
    record_button.pack(ipady=12)
        
    # Load consumables
    refresh_consumable_dropdown()
    
    # Session List (full width below) - REMOVED green background
    shadow3 = Frame(content_container, bg="#d0d0d0")
    shadow3.pack(fill="both", expand=True)
    
    session_section = Frame(shadow3, bg="white", relief="flat")  # REMOVED green background
    session_section.pack(fill="both", expand=True, padx=2, pady=2)
    
    session_header = Frame(session_section, bg="#e3f2fd", height=50)
    session_header.pack(fill="x")
    session_header.pack_propagate(False)
    
    Label(session_header, text="Current Session", font=("Arial", 13, "bold"),
          bg="#e3f2fd", fg="#005c3c").pack(side="left", padx=30, pady=15)
    
    session_count_label = Label(session_header, text="Items processed this session: 0",
                                font=("Arial", 11), bg="#e3f2fd", fg="#005c3c")
    session_count_label.pack(side="right", padx=30)
    
    session_frame = Frame(session_section, bg="white")  # REMOVED green background
    session_frame.pack(fill="both", expand=True, padx=20, pady=20)
    
    scrollbar = tk.Scrollbar(session_frame)
    scrollbar.pack(side="right", fill="y")
    
    session_list = tk.Listbox(session_frame, font=("Arial", 10), height=8,
                              yscrollcommand=scrollbar.set, relief="solid", borderwidth=1,
                              bg="white")  # REMOVED green background
    session_list.pack(fill="both", expand=True)
    scrollbar.config(command=session_list.yview)