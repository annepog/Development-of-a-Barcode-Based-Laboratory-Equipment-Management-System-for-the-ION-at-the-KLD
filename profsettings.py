import tkinter as tk
from tkinter import messagebox, simpledialog
from PIL import Image, ImageTk
import pymysql
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

def show_profile_settings(root, user_email, back_callback=None):
    """Render the Profile Settings page with modern design.

    Args:
        root: the window or frame to populate.
        user_email: email of the logged-in user
        back_callback: called when the user presses the back arrow.
    """
    # Store back_callback in a way that child functions can access it
    root._profile_back_callback = back_callback
    
    # Load profile data from database
    profile = load_profile_data(user_email)
    
    if profile is None:
        messagebox.showerror("Error", "Could not load profile data")
        return

    # Clear the window and set background
    for widget in root.winfo_children():
        widget.destroy()
    root.configure(bg="#f5f5f5")

    # Top bar matching homepage design
    top_bar = tk.Frame(root, bg="#005c3c", height=80)
    top_bar.pack(fill="x", side="top")

    # Try to load the logo
    try:
        logo_path = resource_path("ion_logo.png")
        logo_img = Image.open(logo_path).resize((50, 50))
        logo_photo = ImageTk.PhotoImage(logo_img)
        logo_lbl = tk.Label(top_bar, image=logo_photo, bg="#005c3c")
        logo_lbl.image = logo_photo
    except Exception:
        logo_lbl = tk.Label(top_bar, text="ION", fg="white", bg="#005c3c", 
                           font=("Arial", 24, "bold"))
    logo_lbl.pack(side="left", padx=(30, 0), pady=15)

    # System name
    tk.Label(top_bar, text="Laboratory Equipment System", bg="#005c3c", 
             font=("Arial", 16), fg="white").pack(side="left", padx=20)

    # Main content area
    main_container = tk.Frame(root, bg="#f5f5f5")
    main_container.pack(expand=True, fill="both", padx=60, pady=40)

    # Header section with back button
    header_frame = tk.Frame(main_container, bg="#f5f5f5")
    header_frame.pack(fill="x", pady=(0, 30))

    def on_back(event=None):
        if callable(back_callback):
            back_callback()

    # Back button with modern styling
    back_btn_frame = tk.Frame(header_frame, bg="#f5f5f5")
    back_btn_frame.pack(side="left")
    
    back_btn = tk.Button(back_btn_frame, text="← Back", font=("Arial", 11), 
                        bg="#005c3c", fg="white", relief="flat",
                        padx=20, pady=8, cursor="hand2",
                        activebackground="#004d32", activeforeground="white",
                        command=on_back)
    back_btn.pack()

    # Page title
    title_frame = tk.Frame(header_frame, bg="#f5f5f5")
    title_frame.pack(side="left", padx=20)
    
    tk.Label(title_frame, text="Profile Settings", font=("Arial", 28, "bold"), 
             bg="#f5f5f5", fg="#005c3c").pack(anchor="w")
    tk.Label(title_frame, text="Manage your account information and settings", 
             font=("Arial", 11), bg="#f5f5f5", fg="#666").pack(anchor="w")

    # Main content card with shadow effect
    card_shadow = tk.Frame(main_container, bg="#d0d0d0")
    card_shadow.pack(fill="both", expand=True)
    
    info_card = tk.Frame(card_shadow, bg="white")
    info_card.place(x=-3, y=-3, relwidth=1, relheight=1)

    # Create scrollable canvas
    canvas = tk.Canvas(info_card, bg="white", highlightthickness=0)
    scrollbar = tk.Scrollbar(info_card, orient="vertical", command=canvas.yview)
    scrollable_frame = tk.Frame(canvas, bg="white")

    canvas_window = canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")

    def on_frame_configure(event):
        canvas.configure(scrollregion=canvas.bbox("all"))
        # Update canvas window width to match canvas width
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

    # Profile content
    content_frame = tk.Frame(scrollable_frame, bg="white")
    content_frame.pack(fill="both", expand=True, padx=50, pady=40)

    # Get the stored back_callback
    stored_back_callback = getattr(root, '_profile_back_callback', back_callback)
    
    # Personal Information Section
    create_section_header(content_frame, "👤 Personal Information")
    
    personal_frame = tk.Frame(content_frame, bg="white")
    personal_frame.pack(fill="x", pady=(10, 30))
    
    create_modern_profile_row(personal_frame, 0, "Full Name", profile["full_name"], 
                              True, lambda: edit_full_name(root, user_email, 
                                                          profile["full_name"], 
                                                          stored_back_callback))
    create_modern_profile_row(personal_frame, 1, "Employee ID", profile["employee_id"], False)
    create_modern_profile_row(personal_frame, 2, "Email Address", profile["email"], False)
    
    # Divider
    tk.Frame(content_frame, bg="#e0e0e0", height=1).pack(fill="x", pady=20)
    
    # Work Information Section
    create_section_header(content_frame, "💼 Work Information")
    
    work_frame = tk.Frame(content_frame, bg="white")
    work_frame.pack(fill="x", pady=(10, 30))
    
    create_modern_profile_row(work_frame, 0, "Department", profile["department"], False)
    create_modern_profile_row(work_frame, 1, "Position", profile["position"], False)
    
    # Divider
    tk.Frame(content_frame, bg="#e0e0e0", height=1).pack(fill="x", pady=20)
    
    # Account Status Section
    create_section_header(content_frame, "📊 Account Status")
    
    status_frame = tk.Frame(content_frame, bg="white")
    status_frame.pack(fill="x", pady=(10, 30))
    
    create_status_row(status_frame, 0, "Account Status", profile["account_status"])
    create_status_row(status_frame, 1, "Return Compliance", 
                     profile["return_compliance_status"])
    
    # Divider
    tk.Frame(content_frame, bg="#e0e0e0", height=1).pack(fill="x", pady=20)
    
    # Security Section
    create_section_header(content_frame, "🔒 Security Settings")
    
    security_frame = tk.Frame(content_frame, bg="white")
    security_frame.pack(fill="x", pady=(10, 20))
    
    # Change Password button
    tk.Label(security_frame, text="Update your password to keep your account secure", 
             font=("Arial", 10), bg="white", fg="#666").pack(anchor="w", pady=(5, 15))
    
    change_pwd_btn = tk.Button(security_frame, text="🔑 Change Password", 
                               font=("Arial", 11, "bold"),
                               bg="#005c3c", fg="white", relief="flat",
                               padx=25, pady=10, cursor="hand2",
                               activebackground="#004d32", activeforeground="white",
                               command=lambda: change_password(root, user_email))
    change_pwd_btn.pack(anchor="w")


def create_section_header(parent, text):
    """Create a section header"""
    tk.Label(parent, text=text, font=("Arial", 16, "bold"), 
             bg="white", fg="#005c3c").pack(anchor="w", pady=(0, 5))


def create_modern_profile_row(parent, row, label_text, value_text, 
                               editable=False, edit_callback=None):
    """Create a modern row in the profile display"""
    row_frame = tk.Frame(parent, bg="#f8f9fa", bd=0)
    row_frame.pack(fill="x", pady=8)
    
    # Inner padding frame
    inner_frame = tk.Frame(row_frame, bg="#f8f9fa")
    inner_frame.pack(fill="x", padx=20, pady=15)
    
    # Left side - Label and Value
    left_frame = tk.Frame(inner_frame, bg="#f8f9fa")
    left_frame.pack(side="left", fill="x", expand=True)
    
    tk.Label(left_frame, text=label_text, anchor="w", 
             font=("Arial", 10, "bold"), bg="#f8f9fa", 
             fg="#666").pack(anchor="w")
    
    tk.Label(left_frame, text=value_text or "Not set", anchor="w", 
             font=("Arial", 12), bg="#f8f9fa", 
             fg="#333").pack(anchor="w", pady=(3, 0))
    
    # Right side - Edit button if editable
    if editable and edit_callback:
        edit_btn = tk.Button(inner_frame, text="✏️ Edit", font=("Arial", 10, "bold"),
                            bg="#28a745", fg="white", relief="flat",
                            padx=20, pady=8, cursor="hand2",
                            activebackground="#218838", activeforeground="white",
                            command=edit_callback)
        edit_btn.pack(side="right")


def create_status_row(parent, row, label_text, value_text):
    """Create a status row with colored indicator"""
    row_frame = tk.Frame(parent, bg="#f8f9fa", bd=0)
    row_frame.pack(fill="x", pady=8)
    
    # Inner padding frame
    inner_frame = tk.Frame(row_frame, bg="#f8f9fa")
    inner_frame.pack(fill="x", padx=20, pady=15)
    
    # Left side - Label
    tk.Label(inner_frame, text=label_text, anchor="w", 
             font=("Arial", 10, "bold"), bg="#f8f9fa", 
             fg="#666").pack(side="left")
    
    # Right side - Status with color
    status_frame = tk.Frame(inner_frame, bg="#f8f9fa")
    status_frame.pack(side="right")
    
    # Color based on status
    if "active" in value_text.lower() or "good" in value_text.lower():
        bg_color = "#d4edda"
        fg_color = "#155724"
        indicator = "●"
    elif "compliant" in value_text.lower():
        bg_color = "#d4edda"
        fg_color = "#155724"
        indicator = "●"
    else:
        bg_color = "#f8d7da"
        fg_color = "#721c24"
        indicator = "●"
    
    status_label = tk.Label(status_frame, text=f"{indicator} {value_text}", 
                           font=("Arial", 11, "bold"),
                           bg=bg_color, fg=fg_color, padx=15, pady=6)
    status_label.pack()

def load_profile_data(user_email):
    """Load profile data from MySQL database"""
    conn = get_db_connection()
    if not conn:
        print(" Database connection failed")
        return None
        
    try:
        with conn.cursor() as cursor:
            # First, let's check what columns actually exist in user_profiles
            cursor.execute("DESCRIBE user_profiles")
            columns = cursor.fetchall()
            print(" Available columns in user_profiles:")
            for col in columns:
                print(f"   - {col['Field']}")
            
            # Build query based on available columns
            query = """
                SELECT u.email
            """
            
            # Check which profile columns exist and add them to query
            available_columns = [col['Field'] for col in columns]
            
            if 'full_name' in available_columns:
                query += ", p.full_name"
            else:
                query += ", '' as full_name"
                
            if 'employee_id' in available_columns:
                query += ", p.employee_id"
            else:
                query += ", '' as employee_id"
                
            if 'department' in available_columns:
                query += ", p.department"
            else:
                query += ", '' as department"
                
            if 'position' in available_columns:
                query += ", p.position"
            else:
                query += ", '' as position"
                
            if 'account_status' in available_columns:
                query += ", p.account_status"
            else:
                query += ", 'Active' as account_status"
                
            if 'return_compliance_status' in available_columns:
                query += ", p.return_compliance_status"
            else:
                query += ", 'Compliant' as return_compliance_status"
            
            query += """
                FROM user_profiles p
                JOIN users u ON p.user_id = u.id
                WHERE u.email = %s
            """
            
            print(f" Executing query: {query}")
            cursor.execute(query, (user_email,))
            
            result = cursor.fetchone()
            
            print(f" Query result for {user_email}: {result}")
            
            if result:
                profile_data = {
                    "email": result['email'],
                    "full_name": result.get('full_name', 'Not set'),
                    "employee_id": result.get('employee_id', 'Not set'),
                    "department": result.get('department', 'Not set'),
                    "position": result.get('position', 'Not set'),
                    "account_status": result.get('account_status', 'Active'),
                    "return_compliance_status": result.get('return_compliance_status', 'Compliant'),
                    "contact_number": "Not available"  # Hardcoded since column doesn't exist
                }
                print(f" Profile data loaded: {profile_data}")
                return profile_data
            else:
                print(f" No profile found for email: {user_email}")
                return None
            
    except Exception as e:
        print(f" Database error in load_profile_data: {e}")
        return None
    finally:
        conn.close()


def edit_full_name(root, user_email, current_name, back_callback):
    """Edit full name with modern dialog"""
    dialog = tk.Toplevel(root)
    dialog.title("Edit Full Name")
    dialog.geometry("450x250")
    dialog.configure(bg="white")
    dialog.transient(root)
    dialog.grab_set()
    
    # Center the dialog
    dialog.update_idletasks()
    x = (dialog.winfo_screenwidth() // 2) - (450 // 2)
    y = (dialog.winfo_screenheight() // 2) - (250 // 2)
    dialog.geometry(f"450x250+{x}+{y}")
    
    # Header
    header = tk.Frame(dialog, bg="#005c3c", height=60)
    header.pack(fill="x")
    header.pack_propagate(False)
    
    tk.Label(header, text="✏️ Edit Full Name", font=("Arial", 16, "bold"),
             bg="#005c3c", fg="white").pack(pady=15)
    
    # Content
    content = tk.Frame(dialog, bg="white")
    content.pack(fill="both", expand=True, padx=30, pady=20)
    
    tk.Label(content, text="Enter your full name:", font=("Arial", 11),
             bg="white", fg="#666").pack(anchor="w", pady=(0, 8))
    
    entry = tk.Entry(content, font=("Arial", 12), width=35, relief="solid", bd=1)
    entry.insert(0, current_name)
    entry.pack(pady=(0, 20), ipady=8)
    entry.focus()
    
    def save_changes():
        new_name = entry.get().strip()
        if not new_name:
            messagebox.showerror("Error", "Full name cannot be empty")
            return
        
        conn = get_db_connection()
        if not conn:
            messagebox.showerror("Database Error", "Could not connect to database")
            return
            
        try:
            with conn.cursor() as cursor:
                cursor.execute("""
                    UPDATE user_profiles 
                    SET full_name = %s
                    WHERE user_id = (SELECT id FROM users WHERE email = %s)
                """, (new_name, user_email))
                
                conn.commit()
                dialog.destroy()
                messagebox.showinfo("Success", "Full name updated successfully!")
                show_profile_settings(root, user_email, back_callback)
                
        except Exception as e:
            messagebox.showerror("Database Error", f"Error updating full name: {str(e)}")
        finally:
            conn.close()
    
    # Buttons
    button_frame = tk.Frame(content, bg="white")
    button_frame.pack(fill="x")
    
    tk.Button(button_frame, text="Cancel", font=("Arial", 11),
              bg="#6c757d", fg="white", relief="flat",
              padx=25, pady=10, cursor="hand2",
              activebackground="#5a6268", activeforeground="white",
              command=dialog.destroy).pack(side="left", padx=(0, 10))
    
    tk.Button(button_frame, text="Save Changes", font=("Arial", 11, "bold"),
              bg="#005c3c", fg="white", relief="flat",
              padx=25, pady=10, cursor="hand2",
              activebackground="#004d32", activeforeground="white",
              command=save_changes).pack(side="left")


def change_password(root, user_email):
    """Change password with modern dialog"""
    dialog = tk.Toplevel(root)
    dialog.title("Change Password")
    dialog.geometry("500x450")
    dialog.configure(bg="white")
    dialog.transient(root)
    dialog.grab_set()
    
    # Center the dialog
    dialog.update_idletasks()
    x = (dialog.winfo_screenwidth() // 2) - (500 // 2)
    y = (dialog.winfo_screenheight() // 2) - (450 // 2)
    dialog.geometry(f"500x450+{x}+{y}")
    
    # Header
    header = tk.Frame(dialog, bg="#005c3c", height=60)
    header.pack(fill="x")
    header.pack_propagate(False)
    
    tk.Label(header, text="🔑 Change Password", font=("Arial", 16, "bold"),
             bg="#005c3c", fg="white").pack(pady=15)
    
    # Content
    content = tk.Frame(dialog, bg="white")
    content.pack(fill="both", expand=True, padx=40, pady=30)
    
    # Current password
    tk.Label(content, text="Current Password", font=("Arial", 11, "bold"),
             bg="white", fg="#333").pack(anchor="w", pady=(0, 5))
    current_pwd = tk.Entry(content, font=("Arial", 12), show="●", width=40, 
                          relief="solid", bd=1)
    current_pwd.pack(pady=(0, 20), ipady=8)
    current_pwd.focus()
    
    # New password
    tk.Label(content, text="New Password", font=("Arial", 11, "bold"),
             bg="white", fg="#333").pack(anchor="w", pady=(0, 5))
    new_pwd = tk.Entry(content, font=("Arial", 12), show="●", width=40, 
                      relief="solid", bd=1)
    new_pwd.pack(pady=(0, 20), ipady=8)
    
    # Confirm new password
    tk.Label(content, text="Confirm New Password", font=("Arial", 11, "bold"),
             bg="white", fg="#333").pack(anchor="w", pady=(0, 5))
    confirm_pwd = tk.Entry(content, font=("Arial", 12), show="●", width=40, 
                          relief="solid", bd=1)
    confirm_pwd.pack(pady=(0, 5), ipady=8)
    
    # Password requirements
    req_frame = tk.Frame(content, bg="#f8f9fa", bd=1, relief="solid")
    req_frame.pack(fill="x", pady=15)
    
    tk.Label(req_frame, text="ℹ️ Password must be at least 6 characters long", 
             font=("Arial", 9), bg="#f8f9fa", fg="#666").pack(anchor="w", 
                                                               padx=10, pady=8)
    
    def save_password():
        current = current_pwd.get()
        new = new_pwd.get()
        confirm = confirm_pwd.get()
        
        if not current or not new or not confirm:
            messagebox.showerror("Error", "All fields are required")
            return
        
        if new != confirm:
            messagebox.showerror("Error", "New passwords do not match")
            return
        
        if len(new) < 6:
            messagebox.showerror("Error", "Password must be at least 6 characters long")
            return
        
        conn = get_db_connection()
        if not conn:
            messagebox.showerror("Database Error", "Could not connect to database")
            return
            
        try:
            with conn.cursor() as cursor:
                # Verify current password
                cursor.execute("SELECT password FROM users WHERE email = %s", (user_email,))
                result = cursor.fetchone()
                
                if not result or result['password'] != current:
                    messagebox.showerror("Error", "Current password is incorrect")
                    conn.close()
                    return
                
                # Update password
                cursor.execute("""
                    UPDATE users 
                    SET password = %s
                    WHERE email = %s
                """, (new, user_email))
                
                conn.commit()
                messagebox.showinfo("Success", "Password changed successfully!")
                dialog.destroy()
                
        except Exception as e:
            messagebox.showerror("Database Error", f"Error changing password: {str(e)}")
        finally:
            conn.close()
    
    # Buttons
    button_frame = tk.Frame(content, bg="white")
    button_frame.pack(fill="x", pady=(10, 0))
    
    tk.Button(button_frame, text="Cancel", font=("Arial", 11),
              bg="#6c757d", fg="white", relief="flat",
              padx=25, pady=10, cursor="hand2",
              activebackground="#5a6268", activeforeground="white",
              command=dialog.destroy).pack(side="left", padx=(0, 10))
    
    tk.Button(button_frame, text="Change Password", font=("Arial", 11, "bold"),
              bg="#005c3c", fg="white", relief="flat",
              padx=25, pady=10, cursor="hand2",
              activebackground="#004d32", activeforeground="white",
              command=save_password).pack(side="left")


# Simple test
if __name__ == "__main__":
    root = tk.Tk()
    root.title("Profile Settings Demo")
    root.geometry("1000x700")
    show_profile_settings(root, "faculty@nursing.com")
    root.mainloop()