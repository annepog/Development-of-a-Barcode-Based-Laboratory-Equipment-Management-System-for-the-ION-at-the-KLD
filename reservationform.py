# reservationform.py - Updated with hours duration (MySQL Version)
import tkinter as tk
from tkinter import messagebox, Spinbox
from tkcalendar import DateEntry
import pymysql
from datetime import datetime, timedelta
from notification_manager import NotificationManager
from PIL import Image, ImageTk, ImageEnhance

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

def show_reserve_form(root, equipment_name, equipment_id, user_email, back_callback):
    for w in root.winfo_children():
        w.destroy()
    root.configure(bg="#f5f5f5")

    # Get equipment stock information
    conn = get_db_connection()
    if not conn:
        messagebox.showerror("Database Error", "Could not connect to database!")
        back_callback()
        return
    
    try:
        with conn.cursor() as cursor:
            cursor.execute("""
                SELECT total_quantity, available_quantity, tracking_type, variant, availability_status
                FROM equipment WHERE id = %s
            """, (equipment_id,))
            equipment_data = cursor.fetchone()
    except Exception as e:
        messagebox.showerror("Database Error", f"Error fetching equipment data: {str(e)}")
        conn.close()
        back_callback()
        return
    finally:
        conn.close()
    
    if not equipment_data:
        messagebox.showerror("Error", "Equipment not found!")
        back_callback()
        return
    
    total_quantity = equipment_data['total_quantity']
    available_quantity = equipment_data['available_quantity']
    tracking_type = equipment_data['tracking_type']
    variant = equipment_data['variant']
    availability_status = equipment_data['availability_status']
    
    # Check if equipment is already reserved
    if availability_status == "Reserved":
        messagebox.showwarning("Already Reserved", 
                             "This equipment is already reserved and cannot be reserved again until the current reservation is completed.")
        back_callback()
        return
    
    # Determine max quantity based on tracking type
    if tracking_type == "individual":
        max_quantity = 1  # Individual items can only reserve 1
        available_display = "1 (Individual Item)"
    else:
        max_quantity = available_quantity  # Quantity items can reserve up to available stock
        available_display = f"{available_quantity}/{total_quantity}"
    
    # Top bar with consistent styling
    top = tk.Frame(root, bg="#005c3c", height=70)
    top.pack(fill="x")
    top.pack_propagate(False)
    
    tk.Button(top, text="← Back", font=("Arial", 12), bg="#005c3c", fg="white", border=0,
              cursor="hand2", command=back_callback).pack(side="left", padx=30, pady=20)
    tk.Label(top, text="Reserve Equipment", font=("Arial", 16, "bold"), 
             bg="#005c3c", fg="white").pack(side="left", padx=10, pady=20)

    # Main content area with background
    main = tk.Frame(root, bg="#f5f5f5")
    main.pack(expand=True, fill="both")
    
    # Try to load and set background image
    try:
        bg_image = Image.open("background.jpg")
        screen_width = root.winfo_screenwidth()
        screen_height = root.winfo_screenheight()
        bg_image = bg_image.resize((screen_width, screen_height - 70))
        enhancer = ImageEnhance.Brightness(bg_image)
        bg_image = enhancer.enhance(1.3)
        bg_photo = ImageTk.PhotoImage(bg_image)
        bg_label = tk.Label(main, image=bg_photo)
        bg_label.image = bg_photo
        bg_label.place(x=0, y=0, relwidth=1, relheight=1)
    except Exception as e:
        print(f"Background image not found: {e}")

    # Create scrollable frame
    canvas = tk.Canvas(main, bg="#f5f5f5", highlightthickness=0)
    scrollbar = tk.Scrollbar(main, orient="vertical", command=canvas.yview)
    scrollable_frame = tk.Frame(canvas, bg="#f5f5f5")

    scrollable_frame.bind(
        "<Configure>",
        lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
    )

    canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
    canvas.configure(yscrollcommand=scrollbar.set)

    # Mouse wheel scrolling
    def _on_mousewheel(event):
        canvas.yview_scroll(int(-1*(event.delta/120)), "units")
    
    canvas.bind_all("<MouseWheel>", _on_mousewheel)

    canvas.pack(side="left", fill="both", expand=True, padx=20, pady=20)
    scrollbar.pack(side="right", fill="y", pady=20)

    # Content container with padding
    content_container = tk.Frame(scrollable_frame, bg="#f5f5f5")
    content_container.pack(expand=True, fill="both", padx=40, pady=40)

    # Center frame for the form
    center_frame = tk.Frame(content_container, bg="#f5f5f5")
    center_frame.pack(expand=True)

    # Logo section
    logo_frame = tk.Frame(center_frame, bg="#f5f5f5")
    logo_frame.pack(pady=(0, 20))
    
    try:
        logo_img = Image.open("ion_logo.png")
        logo_img = logo_img.resize((70, 70), Image.Resampling.LANCZOS)
        logo_photo = ImageTk.PhotoImage(logo_img)
        logo_label = tk.Label(logo_frame, image=logo_photo, bg="#f5f5f5")
        logo_label.image = logo_photo
        logo_label.pack()
    except:
        tk.Label(logo_frame, text="🏥", font=("Arial", 48), bg="#f5f5f5").pack()

    # Title
    tk.Label(center_frame, text="Equipment Reservation Form", 
             font=("Arial", 20, "bold"), bg="#f5f5f5", fg="#005c3c").pack(pady=(0, 10))
    tk.Label(center_frame, text="Fill out the form below to request equipment", 
             font=("Arial", 11), bg="#f5f5f5", fg="#666").pack(pady=(0, 25))

    # Form container with shadow
    shadow = tk.Frame(center_frame, bg="#d0d0d0")
    shadow.pack()
    
    form_container = tk.Frame(shadow, bg="white", bd=0)
    form_container.pack(padx=2, pady=2)
    
    form = tk.Frame(form_container, bg="white", padx=50, pady=40)
    form.pack()

    def add_field(label_text, row, widget, is_text=False, help_text=None):
        label_frame = tk.Frame(form, bg="white")
        label_frame.grid(row=row, column=0, sticky="nw" if is_text else "w", 
                        pady=15, padx=(0, 40))
        
        tk.Label(label_frame, text=label_text, bg="white", 
                font=("Arial", 11, "bold"), fg="#333").pack(anchor="w")
        
        if help_text:
            tk.Label(label_frame, text=help_text, bg="white", 
                    font=("Arial", 9), fg="#666").pack(anchor="w")
        
        widget.grid(row=row, column=1, pady=15, sticky="w")
        return widget

    # Equipment Name (readonly) with variant - KEEP green styling for equipment name only
    display_name = f"{equipment_name} ({variant})" if variant else equipment_name
    equipment_entry = tk.Entry(form, width=40, font=("Arial", 11), 
                              relief="solid", bd=1)
    equipment_entry.insert(0, display_name)
    equipment_entry.config(state="readonly", bg="#f8f8f8", fg="#005c3c", 
                          font=("Arial", 11, "bold"))
    add_field("Equipment Name", 0, equipment_entry)

    # Stock information
    stock_frame = tk.Frame(form, bg="white")
    stock_frame.grid(row=1, column=0, columnspan=2, sticky="w", pady=10)
    
    stock_info = f"Available Stock: {available_display}"
    if tracking_type == "individual":
        stock_info += " (Individual Item)"
    else:
        stock_info += " (Quantity Tracked)"
    
    tk.Label(stock_frame, text=stock_info, font=("Arial", 10, "bold"), 
             bg="white", fg="#005c3c").pack(anchor="w")

    # Quantity (Spinbox) with limits - REMOVED green background
    quantity_var = tk.StringVar(value="1")
    
    if max_quantity == 0:
        # No stock available
        quantity_entry = tk.Entry(form, width=40, font=("Arial", 11), 
                                 relief="solid", bd=1, state="disabled")
        quantity_entry.insert(0, "Out of Stock")
        add_field("Quantity", 2, quantity_entry, help_text="No items available for reservation")
    else:
        quantity_entry = Spinbox(form, from_=1, to=max_quantity, width=38, font=("Arial", 11), 
                                textvariable=quantity_var, relief="solid", bd=1)
        help_text = f"Maximum: {max_quantity} item(s) available"
        add_field("Quantity", 2, quantity_entry, help_text=help_text)

    # Date Needed (Calendar) - set minimum date to tomorrow
    min_date = datetime.now() + timedelta(days=1)
    date_entry = DateEntry(form, width=37, background="#005c3c", foreground="white", 
                          borderwidth=1, font=("Arial", 11), relief="solid",
                          mindate=min_date)
    add_field("Date Needed", 3, date_entry, help_text="Select a future date")

    # Purpose of Use - REMOVED green background
    purpose_entry = tk.Entry(form, width=40, font=("Arial", 11), relief="solid", bd=1)
    add_field("Purpose of Use", 4, purpose_entry, help_text="Required - describe what you need this for")

    # Duration of Use (Dropdown) - NOW IN HOURS
    duration_var = tk.StringVar(value="1 Hour")
    duration_options = ["1 Hour", "2 Hours", "3 Hours", "4 Hours", "6 Hours", "8 Hours", "12 Hours", "24 Hours", "48 Hours", "72 Hours"]
    duration_menu = tk.OptionMenu(form, duration_var, *duration_options)
    duration_menu.config(width=35, font=("Arial", 11), bg="white", relief="solid", bd=1)
    add_field("Duration of Use", 5, duration_menu, help_text="Select how many hours you need the equipment")

    # Additional Notes - REMOVED green background
    notes_label_frame = tk.Frame(form, bg="white")
    notes_label_frame.grid(row=6, column=0, sticky="nw", pady=15, padx=(0, 40))
    tk.Label(notes_label_frame, text="Additional Notes", bg="white", 
            font=("Arial", 11, "bold"), fg="#333").pack(anchor="w")
    tk.Label(notes_label_frame, text="(optional)", bg="white", 
            font=("Arial", 9), fg="#888").pack(anchor="w")
    
    notes_entry = tk.Text(form, width=40, height=4, font=("Arial", 11), 
                         wrap="word", relief="solid", bd=1)
    notes_entry.grid(row=6, column=1, pady=15)

    # Buttons
    button_frame = tk.Frame(form, bg="white")
    button_frame.grid(row=7, columnspan=2, pady=30)

    tk.Button(button_frame, text="Cancel", bg="#999", fg="white", width=18,
              font=("Arial", 11, "bold"), relief="flat", cursor="hand2",
              activebackground="#777", pady=8,
              command=back_callback).pack(side="left", padx=10)

    def confirm():
        # Check if item is out of stock
        if max_quantity == 0:
            messagebox.showerror("Out of Stock", 
                               "This item is currently out of stock and cannot be reserved.")
            return
        
        quantity = quantity_var.get()
        date_needed = date_entry.get()
        purpose = purpose_entry.get().strip()
        duration = duration_var.get()
        notes = notes_entry.get("1.0", "end-1c").strip()

        # Validation
        if not quantity or not date_needed or not purpose:
            messagebox.showwarning("Incomplete Form", 
                                 "Please fill out all required fields.")
            return

        try:
            quantity = int(quantity)
            if quantity < 1 or quantity > max_quantity:
                messagebox.showerror("Invalid Quantity", 
                                   f"Quantity must be between 1 and {max_quantity}")
                return
        except ValueError:
            messagebox.showerror("Invalid Quantity", "Please enter a valid number for quantity.")
            return

        # Check if selected date is in the past
        selected_date = datetime.strptime(date_needed, "%m/%d/%y")
        if selected_date < datetime.now().replace(hour=0, minute=0, second=0, microsecond=0):
            messagebox.showerror("Invalid Date", "Please select a future date.")
            return

        conn = get_db_connection()
        if not conn:
            messagebox.showerror("Database Error", "Could not connect to database!")
            return

        try:
            with conn.cursor() as cursor:
                # Insert reservation with Pending status
                cursor.execute("""
                    INSERT INTO reservations (equipment_id, user_email, quantity, date_needed, 
                                            purpose, duration, notes, status, created_at)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, 'Pending', %s)
                """, (equipment_id, user_email, quantity, date_needed, 
                      purpose, duration, notes, datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
                
                reservation_id = cursor.lastrowid
                conn.commit()

                print(f"\n{'='*60}")
                print(f"RESERVATION SUBMITTED SUCCESSFULLY")
                print(f"{'='*60}")
                print(f"Reservation ID: {reservation_id}")
                print(f"Equipment: {display_name} (ID: {equipment_id})")
                print(f"User: {user_email}")
                print(f"Quantity: {quantity}")
                print(f"Date Needed: {date_needed}")
                print(f"Duration: {duration}")
                print(f"Status: Pending (Waiting for admin approval)")
                print(f"{'='*60}\n")

                # Create notification for the user
                notif_manager = NotificationManager()
                notif_id = notif_manager.create_notification(
                    user_email=user_email,
                    message=f"Your reservation for {display_name} has been submitted and is pending approval.",
                    notif_type="reservation_submitted",
                    related_id=reservation_id
                )
                
                if notif_id:
                    print(f" User notification created (ID: {notif_id})")
                else:
                    print(" Warning: User notification creation failed")

                # Create notification for admin
                admin_notif_id = notif_manager.create_notification(
                    user_email="admin@nursing.com",
                    message=f"New reservation request for {display_name} from {user_email}",
                    notif_type="new_reservation",
                    related_id=reservation_id
                )
                
                if admin_notif_id:
                    print(f" Admin notification created (ID: {admin_notif_id})")

                # Success message
                success_message = (
                    f"Reservation Request Submitted Successfully!\n\n"
                    f"Equipment: {display_name}\n"
                    f"Quantity: {quantity}\n"
                    f"Date Needed: {date_needed}\n"
                    f"Duration: {duration}\n\n"
                    f"Status: ⏳ Pending Approval\n\n"
                    f"Your request has been sent to the administrator for approval.\n"
                    f"You will be notified when it's approved or rejected.\n\n"
                    f"Reservation ID: #{reservation_id}"
                )
                
                messagebox.showinfo("Reservation Submitted", success_message)
                
                print(f" Returning to catalog...\n")
                back_callback()

        except Exception as e:
            error_msg = f"Failed to submit reservation: {str(e)}"
            messagebox.showerror("Error", error_msg)
            print(f"\n RESERVATION ERROR:")
            print(f"   {error_msg}")
            import traceback
            traceback.print_exc()
            print()
            conn.rollback()
        finally:
            conn.close()

    # Enable/disable confirm button based on availability
    if max_quantity == 0:
        confirm_btn = tk.Button(button_frame, text="Out of Stock", bg="#dc3545", fg="white",
                              width=22, font=("Arial", 11, "bold"), relief="flat",
                              state="disabled", pady=8)
        confirm_btn.pack(side="left", padx=10)
    else:
        confirm_btn = tk.Button(button_frame, text="Submit Reservation", bg="#005c3c", fg="white",
                              width=22, font=("Arial", 11, "bold"), relief="flat", 
                              cursor="hand2", activebackground="#004d32", pady=8,
                              command=confirm)
        confirm_btn.pack(side="left", padx=10)

    # Update scroll region after everything is loaded
    def update_scroll_region():
        canvas.configure(scrollregion=canvas.bbox("all"))
    
    canvas.after(100, update_scroll_region)