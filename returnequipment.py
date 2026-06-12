# return.py - Admin-only return functionality with Report Issue button (MySQL Version)
import tkinter as tk
from tkinter import Frame, Label, Entry, Button, Spinbox, messagebox
from datetime import datetime
import pymysql
from PIL import Image, ImageTk, ImageEnhance
from issuereport import show_issue_report_popup  # Import the issue report function

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
def show_return_screen(root, back_callback, admin_email):
    
    def report_issue():
        """Open the issue report popup for admin"""
        show_issue_report_popup(root, admin_email)
    
    def record_return(barcode, quantity=1):
        print(f"DEBUG: record_return called with barcode={barcode}, quantity={quantity}")
        
        conn = get_db_connection()
        if not conn:
            messagebox.showerror("Database Error", "Could not connect to database!")
            return

        try:
            with conn.cursor() as cursor:
                cursor.execute("""
                    SELECT id, name, tracking_type, available_quantity, total_quantity
                    FROM equipment
                    WHERE barcode = %s
                """, (barcode,))
                
                equipment_result = cursor.fetchone()
                print(f"DEBUG: Equipment result: {equipment_result}")
                
                if not equipment_result:
                    show_return_details("", barcode, "", "", "", False, 
                                      "Equipment not found in system")
                    return
                
                equipment_id = equipment_result['id']
                item_name = equipment_result['name']
                tracking_type = equipment_result['tracking_type']
                avail_qty = equipment_result['available_quantity']
                total_qty = equipment_result['total_quantity']
                print(f"DEBUG: Equipment {item_name}, Type: {tracking_type}, Available: {avail_qty}/{total_qty}")
                
                # Get borrow record WITH BORROWER INFO
                cursor.execute("""
                    SELECT borrow_id, borrow_time, quantity_borrowed, borrower_email, borrower_name
                    FROM borrow
                    WHERE barcode = %s AND return_time IS NULL
                    ORDER BY borrow_time DESC
                    LIMIT 1
                """, (barcode,))
                
                borrow_result = cursor.fetchone()
                print(f"DEBUG: Borrow result: {borrow_result}")
                
                if not borrow_result:
                    show_return_details(item_name, barcode, "", "", "", False, 
                                      "Equipment is not currently borrowed")
                    return
                
                borrow_id = borrow_result['borrow_id']
                borrow_time = borrow_result['borrow_time']
                quantity_borrowed = borrow_result['quantity_borrowed']
                borrower_email = borrow_result['borrower_email']
                borrower_name = borrow_result['borrower_name']
                print(f"DEBUG: Borrow ID: {borrow_id}, Borrowed qty: {quantity_borrowed}, Borrower: {borrower_name}")
                
                if tracking_type == "quantity":
                    if quantity > quantity_borrowed:
                        show_return_details(item_name, barcode, "", "", "", False, 
                                          f"Cannot return {quantity} items. Only {quantity_borrowed} were borrowed.")
                        return
                else:
                    quantity = 1
                
                timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                print(f"DEBUG: Returning {quantity} items at {timestamp}")
                
                # Update equipment availability
                if tracking_type == "individual":
                    cursor.execute("""
                        UPDATE equipment SET availability_status = 'Available' 
                        WHERE barcode = %s
                    """, (barcode,))
                    print("DEBUG: Updated individual item to Available")
                else:
                    new_available = avail_qty + quantity
                    cursor.execute("""
                        UPDATE equipment SET available_quantity = %s 
                        WHERE barcode = %s
                    """, (new_available, barcode))
                    print(f"DEBUG: Updated quantity from {avail_qty} to {new_available}")
                
                # Update borrow record
                if tracking_type == "quantity" and quantity < quantity_borrowed:
                    new_borrowed = quantity_borrowed - quantity
                    cursor.execute("""
                        UPDATE borrow SET quantity_borrowed = %s, return_status = 'Partially Returned'
                        WHERE borrow_id = %s
                    """, (new_borrowed, borrow_id))
                    print(f"DEBUG: Partial return - updated borrowed qty to {new_borrowed}")
                else:
                    cursor.execute("""
                        UPDATE borrow SET return_time = %s, return_status = 'Returned'
                        WHERE borrow_id = %s
                    """, (timestamp, borrow_id))
                    print("DEBUG: Full return - set return_time and return_status")
                
                # Update transaction status
                if tracking_type == "individual" or quantity >= quantity_borrowed:
                    cursor.execute("""
                        UPDATE transactions SET status = 'Returned' 
                        WHERE barcode = %s AND status = 'Ongoing' AND borrower_email = %s
                    """, (barcode, borrower_email))
                    print("DEBUG: Updated transaction status to Returned")
                
                # Record return transaction with admin verification info
                cursor.execute("""
                    INSERT INTO transactions (
                        datetime, borrower_name, borrower_email, equipment_name, barcode,
                        action, status, handled_by, remarks, quantity
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                """, (
                    timestamp, borrower_name, borrower_email, item_name, barcode,
                    "Returned", "Returned", admin_email,  # Admin email as handled_by
                    f"Returned {quantity} of {quantity_borrowed} borrowed (Admin Verified)", 
                    quantity
                ))
                print("DEBUG: Inserted return transaction with admin verification")

                conn.commit()
                print("DEBUG: Database committed")
                
                borrow_dt = datetime.strptime(borrow_time, "%Y-%m-%d %H:%M:%S")
                return_dt = datetime.strptime(timestamp, "%Y-%m-%d %H:%M:%S")
                duration = return_dt - borrow_dt
                print(f"DEBUG: Duration: {duration}")
                
                if tracking_type == "quantity":
                    remaining_borrowed = quantity_borrowed - quantity
                    new_available = avail_qty + quantity
                    print(f"DEBUG: Showing success - remaining: {remaining_borrowed}, new available: {new_available}")
                    show_return_details(item_name, barcode, borrower_name, duration, timestamp, True,
                                      tracking_type=tracking_type, quantity=quantity,
                                      remaining_borrowed=remaining_borrowed,
                                      new_available=new_available, total_qty=total_qty,
                                      handled_by=admin_email)
                else:
                    print("DEBUG: Showing success for individual item")
                    show_return_details(item_name, barcode, borrower_name, duration, timestamp, True,
                                      handled_by=admin_email)
                
                if tracking_type == "quantity":
                    remaining = quantity_borrowed - quantity
                    msg = f"Successfully returned {quantity} {item_name}!\n\n"
                    msg += f"Faculty: {borrower_name}\n"
                    msg += f"Remaining borrowed: {remaining}\n"
                    msg += f"Stock now: {avail_qty + quantity}/{total_qty}\n"
                    msg += f"Verified by: {admin_email}"
                    messagebox.showinfo("Return Successful", msg)
                else:
                    msg = f"Successfully returned {item_name}!\n\n"
                    msg += f"Faculty: {borrower_name}\n"
                    msg += f"Barcode: {barcode}\nTime: {timestamp}\n"
                    msg += f"Verified by: {admin_email}"
                    messagebox.showinfo("Return Successful", msg)
                
        except Exception as e:
            print(f"DEBUG ERROR in record_return: {e}")
            import traceback
            traceback.print_exc()
            show_return_details("", barcode, "", "", "", False, f"Database error: {e}")
            conn.rollback()
        finally:
            conn.close()
            print("DEBUG: Connection closed")

    def show_return_details(item_name, barcode, borrower_name, duration, timestamp, success, 
                          error_msg="", tracking_type="individual", quantity=1, 
                          remaining_borrowed=0, new_available=0, total_qty=0, handled_by=""):
        for widget in details_frame.winfo_children():
            widget.destroy()
        
        if success:
            shadow = Frame(details_frame, bg="#d0d0d0")
            shadow.pack(fill="x", pady=20, padx=40)
            
            success_card = Frame(shadow, bg="#d4edda", relief="flat")
            success_card.pack(fill="x", padx=2, pady=2)
            
            Frame(success_card, bg="#28a745", width=5).pack(side="left", fill="y")
            
            content = Frame(success_card, bg="#d4edda")
            content.pack(fill="both", expand=True, padx=25, pady=20)
            
            header_frame = Frame(content, bg="#d4edda")
            header_frame.pack(fill="x", pady=(0, 15))
            
            Label(header_frame, text="Return Successful", font=("Arial", 16, "bold"),
                  bg="#d4edda", fg="#155724").pack(side="left")
            
            Label(header_frame, text=timestamp, font=("Arial", 10),
                  bg="#d4edda", fg="#155724").pack(side="right")
            
            details_grid = Frame(content, bg="#d4edda")
            details_grid.pack(fill="x")
            
            # Equipment info
            row1 = Frame(details_grid, bg="#d4edda")
            row1.pack(fill="x", pady=8)
            
            Label(row1, text="Equipment:", font=("Arial", 11, "bold"),
                  bg="#d4edda", fg="#155724").pack(side="left")
            Label(row1, text=f"{item_name} ({barcode})", font=("Arial", 11),
                  bg="#d4edda", fg="#155724").pack(side="left", padx=(10, 0))
            
            # Faculty info
            row_faculty = Frame(details_grid, bg="#d4edda")
            row_faculty.pack(fill="x", pady=8)
            
            Label(row_faculty, text="Faculty:", font=("Arial", 11, "bold"),
                  bg="#d4edda", fg="#155724").pack(side="left")
            Label(row_faculty, text=borrower_name, font=("Arial", 11),
                  bg="#d4edda", fg="#155724").pack(side="left", padx=(10, 0))
            
            # Admin info
            row_admin = Frame(details_grid, bg="#d4edda")
            row_admin.pack(fill="x", pady=8)
            
            Label(row_admin, text="Verified by:", font=("Arial", 11, "bold"),
                  bg="#d4edda", fg="#155724").pack(side="left")
            Label(row_admin, text=handled_by, font=("Arial", 11),
                  bg="#d4edda", fg="#155724").pack(side="left", padx=(10, 0))
            
            if tracking_type == "quantity":
                # Quantity info
                row_qty = Frame(details_grid, bg="#d4edda")
                row_qty.pack(fill="x", pady=8)
                
                Label(row_qty, text="Quantity Returned:", font=("Arial", 11, "bold"),
                      bg="#d4edda", fg="#155724").pack(side="left")
                Label(row_qty, text=f"{quantity} items", font=("Arial", 11),
                      bg="#d4edda", fg="#155724").pack(side="left", padx=(10, 0))
                
                # Stock info
                row_stock = Frame(details_grid, bg="#d4edda")
                row_stock.pack(fill="x", pady=8)
                
                Label(row_stock, text="Current Stock:", font=("Arial", 11, "bold"),
                      bg="#d4edda", fg="#155724").pack(side="left")
                Label(row_stock, text=f"{new_available}/{total_qty} available", font=("Arial", 11),
                      bg="#d4edda", fg="#155724").pack(side="left", padx=(10, 0))
                
                if remaining_borrowed > 0:
                    row_remain = Frame(details_grid, bg="#d4edda")
                    row_remain.pack(fill="x", pady=8)
                    
                    Label(row_remain, text="Still Borrowed:", font=("Arial", 11, "bold"),
                          bg="#d4edda", fg="#155724").pack(side="left")
                    Label(row_remain, text=f"{remaining_borrowed} items", font=("Arial", 11),
                          bg="#d4edda", fg="#155724").pack(side="left", padx=(10, 0))
            
            # Duration info
            row3 = Frame(details_grid, bg="#d4edda")
            row3.pack(fill="x", pady=8)
            
            Label(row3, text="Borrow Duration:", font=("Arial", 11, "bold"),
                  bg="#d4edda", fg="#155724").pack(side="left")
            Label(row3, text=str(duration), font=("Arial", 11),
                  bg="#d4edda", fg="#155724").pack(side="left", padx=(10, 0))
            
        else:
            # Error display
            shadow = Frame(details_frame, bg="#d0d0d0")
            shadow.pack(fill="x", pady=20, padx=40)
            
            error_card = Frame(shadow, bg="#f8d7da", relief="flat")
            error_card.pack(fill="x", padx=2, pady=2)
            
            Frame(error_card, bg="#dc3545", width=5).pack(side="left", fill="y")
            
            content = Frame(error_card, bg="#f8d7da")
            content.pack(fill="both", expand=True, padx=25, pady=20)
            
            header_frame = Frame(content, bg="#f8d7da")
            header_frame.pack(fill="x", pady=(0, 15))
            
            Label(header_frame, text="Return Failed", font=("Arial", 16, "bold"),
                  bg="#f8d7da", fg="#721c24").pack(side="left")
            
            error_details = Frame(content, bg="#f8d7da")
            error_details.pack(fill="x")
            
            Label(error_details, text=f"Barcode: {barcode}", font=("Arial", 11, "bold"),
                  bg="#f8d7da", fg="#721c24").pack(anchor="w", pady=5)
            
            if item_name:
                Label(error_details, text=f"Equipment: {item_name}", font=("Arial", 11),
                      bg="#f8d7da", fg="#721c24").pack(anchor="w", pady=5)
            
            Label(error_details, text=f"Error: {error_msg}", font=("Arial", 11),
                  bg="#f8d7da", fg="#721c24").pack(anchor="w", pady=5)

    def process_barcode():
        print("DEBUG: Process barcode called")
        
        barcode = scan_entry.get().strip()
        print(f"DEBUG: Barcode entered: '{barcode}'")
        
        if not barcode:
            print("DEBUG: No barcode entered")
            messagebox.showwarning("Input Required", "Please enter or scan a barcode")
            scan_entry.configure(bg="#ffebee")
            root.after(1000, lambda: scan_entry.configure(bg="white"))
            return
        
        conn = get_db_connection()
        if not conn:
            messagebox.showerror("Database Error", "Could not connect to database!")
            return

        try:
            with conn.cursor() as cursor:
                print(f"DEBUG: Checking equipment for barcode: {barcode}")
                
                cursor.execute("""
                    SELECT tracking_type, name
                    FROM equipment
                    WHERE barcode = %s
                """, (barcode,))
                
                equipment_result = cursor.fetchone()
                
                if not equipment_result:
                    print("DEBUG: Equipment not found")
                    messagebox.showerror("Error", "Equipment not found")
                    scan_entry.delete(0, tk.END)
                    return
                
                tracking_type = equipment_result['tracking_type']
                name = equipment_result['name']
                
                cursor.execute("""
                    SELECT borrow_id, quantity_borrowed, borrower_name, borrower_email
                    FROM borrow
                    WHERE barcode = %s AND return_time IS NULL
                    ORDER BY borrow_time DESC
                    LIMIT 1
                """, (barcode,))
                
                borrow_result = cursor.fetchone()
                
                if not borrow_result:
                    print(f"DEBUG: {name} is not borrowed")
                    messagebox.showerror("Error", f"{name} is not currently borrowed")
                    scan_entry.delete(0, tk.END)
                    return
                
                borrow_id = borrow_result['borrow_id']
                quantity_borrowed = borrow_result['quantity_borrowed']
                borrower_name = borrow_result['borrower_name']
                borrower_email = borrow_result['borrower_email']
                print(f"DEBUG: Found: {name}, Type: {tracking_type}, Borrowed: {quantity_borrowed}, Faculty: {borrower_name}")
                
                if tracking_type == "quantity" and quantity_borrowed > 1:
                    print(f"DEBUG: Opening quantity dialog for {quantity_borrowed} items")
                    show_quantity_dialog(barcode, name, quantity_borrowed, borrower_name)
                else:
                    print("DEBUG: Processing immediate return")
                    record_return(barcode, 1)
                    scan_entry.delete(0, tk.END)
                    scan_entry.focus_set()
                    
        except Exception as e:
            print(f"DEBUG ERROR in process_barcode: {e}")
            import traceback
            traceback.print_exc()
            messagebox.showerror("Error", f"An error occurred: {str(e)}")
        finally:
            conn.close()

    def show_quantity_dialog(barcode, name, max_quantity, borrower_name):
        dialog = tk.Toplevel(root)
        dialog.title("Admin Return - Select Quantity")
        dialog.geometry("400x250")
        dialog.configure(bg="white")
        dialog.transient(root)
        dialog.grab_set()
        
        dialog.update_idletasks()
        x = root.winfo_x() + (root.winfo_width() // 2) - (dialog.winfo_width() // 2)
        y = root.winfo_y() + (root.winfo_height() // 2) - (dialog.winfo_height() // 2)
        dialog.geometry(f"+{x}+{y}")
        
        Label(dialog, text=f"Return {name}", font=("Arial", 14, "bold"),
              bg="white", fg="#333").pack(pady=(20, 5))
        
        Label(dialog, text=f"Faculty: {borrower_name}", font=("Arial", 11),
              bg="white", fg="#666").pack(pady=(0, 5))
        
        Label(dialog, text=f"Currently borrowed: {max_quantity}", font=("Arial", 10),
              bg="white", fg="#666").pack(pady=(0, 15))
        
        Label(dialog, text="How many to return?", font=("Arial", 11),
              bg="white", fg="#666").pack(pady=(0, 15))
        
        quantity_var = tk.IntVar(value=max_quantity)
        
        spinbox = Spinbox(dialog, from_=1, to=max_quantity, textvariable=quantity_var,
                         font=("Arial", 16), width=10, justify="center")
        spinbox.pack(pady=15)
        
        def confirm():
            qty = quantity_var.get()
            dialog.destroy()
            record_return(barcode, qty)
            scan_entry.delete(0, tk.END)
            scan_entry.focus_set()
        
        button_frame = Frame(dialog, bg="white")
        button_frame.pack(pady=20)
        
        Button(button_frame, text="Cancel", font=("Arial", 11),
               bg="#999", fg="white", relief="flat", padx=20, pady=8,
               command=dialog.destroy).pack(side="left", padx=5)
        
        Button(button_frame, text="Confirm Return", font=("Arial", 11, "bold"),
               bg="#005c3c", fg="white", relief="flat", padx=20, pady=8,
               command=confirm).pack(side="left", padx=5)
        
        spinbox.focus_set()
        dialog.bind("<Return>", lambda e: confirm())

    # UI Setup
    for w in root.winfo_children():
        w.destroy()
    
    root.configure(bg="#f5f5f5")

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

    tk.Label(left_header, text="Admin - Return Equipment", 
        font=("Helvetica", 18, "bold"), bg="#2c5530", fg="white").pack(side="left")

    right_header = tk.Frame(header_content, bg="#2c5530")
    right_header.pack(side="right")

    tk.Button(right_header, text="Back", font=("Helvetica", 10),
        bg="white", fg="#2c5530", relief="flat", width=8,
        command=back_callback).pack(side="left", padx=(0, 10))

    Button(right_header, text="📝 Report Issue", font=("Arial", 10, "bold"), 
        bg="#dc3545", fg="white", relief="flat", cursor="hand2",
        command=report_issue).pack(side="left", padx=(0, 10))

    admin_label = tk.Label(right_header, text=f"Admin: {admin_email}", font=("Arial", 11), 
                        bg="#2c5530", fg="white")
    admin_label.pack(side="right", padx=(10, 0))

    main = tk.Frame(root, bg="#f5f5f5")
    main.pack(expand=True, fill="both")
    
    try:
        bg_image = Image.open("background.jpg")
        screen_width = root.winfo_screenwidth()
        screen_height = root.winfo_screenheight()
        bg_image = bg_image.resize((screen_width, screen_height - 70))
        enhancer = ImageEnhance.Brightness(bg_image)
        bg_image = enhancer.enhance(1.3)
        bg_photo = ImageTk.PhotoImage(bg_image)
        bg_label = Label(main, image=bg_photo)
        bg_label.image = bg_photo
        bg_label.place(x=0, y=0, relwidth=1, relheight=1)
    except:
        pass

    content_container = Frame(main, bg="#f5f5f5")
    content_container.pack(expand=True, fill="both", padx=60, pady=40)

    shadow1 = Frame(content_container, bg="#d0d0d0")
    shadow1.pack(fill="x", pady=(0, 25))
    
    input_section = Frame(shadow1, bg="white", relief="flat")
    input_section.pack(fill="x", padx=2, pady=2)
    
    input_header = Frame(input_section, bg="#e8f5e9", height=50)
    input_header.pack(fill="x")
    input_header.pack_propagate(False)
    
    Label(input_header, text="Scan or Enter Barcode", font=("Arial", 14, "bold"),
          bg="#e8f5e9", fg="#005c3c").pack(pady=15)
    
    input_content = Frame(input_section, bg="white")
    input_content.pack(fill="x", padx=50, pady=35)
    
    Label(input_content, text="Scan the equipment barcode or enter it manually below:",
          font=("Arial", 11), bg="white", fg="#666").pack(pady=(0, 15))
    
    info_frame = Frame(input_content, bg="#e3f2fd", relief="solid", borderwidth=1)
    info_frame.pack(fill="x", pady=(0, 20))
    
    Label(info_frame, text="Admin Note: Returns will be recorded under the original faculty borrower's account. Verify equipment physically before processing return.",
          font=("Arial", 9), bg="#e3f2fd", fg="#1976d2", wraplength=600).pack(padx=15, pady=10)
    
    input_frame = Frame(input_content, bg="white")
    input_frame.pack()
    
    scan_entry = Entry(input_frame, font=("Arial", 16), width=28, justify="center",
                      relief="solid", borderwidth=2, bg="white")
    scan_entry.pack(side="left", ipady=12, padx=(0, 20))
    
    # CLEANER SINGLE BUTTON LAYOUT - REMOVED THE UGLY SECOND BUTTON
    Button(input_frame, text="Process Return", font=("Arial", 12, "bold"),
           bg="#005c3c", fg="white", relief="flat", width=18, cursor="hand2",
           command=process_barcode).pack(side="left", ipady=10)
    
    scan_entry.bind("<Return>", lambda e: process_barcode())
    scan_entry.focus_set()
    
    shadow2 = Frame(content_container, bg="#d0d0d0")
    shadow2.pack(fill="x", pady=(0, 25))
    
    instructions_panel = Frame(shadow2, bg="white", relief="flat")
    instructions_panel.pack(fill="x", padx=2, pady=2)
    
    inst_header = Frame(instructions_panel, bg="#e3f2fd", height=50)
    inst_header.pack(fill="x")
    inst_header.pack_propagate(False)
    
    Label(inst_header, text="Admin Return Instructions", font=("Arial", 13, "bold"),
          bg="#e3f2fd", fg="#005c3c").pack(anchor="w", padx=30, pady=15)
    
    inst_content = Frame(instructions_panel, bg="white")
    inst_content.pack(fill="x", padx=50, pady=25)
    
    instructions = [
        "Physically verify the equipment condition before processing return",
        "Scan the barcode using a barcode scanner or enter manually",
        "For quantity items, select how many to return (partial returns allowed)",
        "Equipment must be currently borrowed to process return",
        "Return will be recorded under the original faculty borrower's account",
        "System will automatically update stock levels and transaction history",
        "Use 'Report Issue' button in top right to report damaged equipment"
    ]
    
    for instruction in instructions:
        instruction_frame = Frame(inst_content, bg="white")
        instruction_frame.pack(fill="x", pady=5)
        
        Label(instruction_frame, text="•", font=("Arial", 12, "bold"),
              bg="white", fg="#005c3c").pack(side="left", padx=(0, 10))
        Label(instruction_frame, text=instruction, font=("Arial", 11),
              bg="white", fg="#666", anchor="w").pack(side="left", fill="x")
    
    details_frame = Frame(content_container, bg="#f5f5f5")
    details_frame.pack(fill="both", expand=True)