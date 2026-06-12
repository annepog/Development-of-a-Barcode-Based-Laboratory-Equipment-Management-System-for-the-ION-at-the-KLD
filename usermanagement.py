import tkinter as tk
from tkinter import Label, Frame, Button, Entry, StringVar, OptionMenu, messagebox, Toplevel, filedialog
from tkinter import ttk
import pymysql
from PIL import Image, ImageTk, ImageEnhance
import secrets
import string
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from reportlab.lib.units import inch

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

# Email Configuration - CONFIGURED FOR KLD NURSING LEMS
EMAIL_CONFIG = {
    'smtp_server': 'smtp.gmail.com',
    'smtp_port': 587,
    'sender_email': 'kld.nursing.lems@gmail.com',
    'sender_password': 'uphzottyfoprbbbu',
    'sender_name': 'KLD Institute of Nursing - LEMS'
}

ENABLE_EMAIL = True


def generate_user_pdf_report():
    """Generate a PDF report of the user inventory in LANDSCAPE format"""
    conn = get_db_connection()
    if not conn:
        messagebox.showerror("Database Error", "Could not connect to database!")
        return
        
    try:
        with conn.cursor() as cursor:
            # Get all user data
            cursor.execute("""
                SELECT 
                    p.employee_id, p.full_name, p.department, p.position, 
                    u.email, p.account_status, p.return_compliance_status
                FROM user_profiles p
                JOIN users u ON p.user_id = u.id
                WHERE COALESCE(p.is_archived, 0) = 0
                ORDER BY p.department, p.full_name
            """)
            
            users_list = cursor.fetchall()
            
        if not users_list:
            messagebox.showinfo("Info", "No users found to generate report.")
            return
        
        # Ask for save location
        output_file = filedialog.asksaveasfilename(
            defaultextension=".pdf",
            filetypes=[("PDF files", "*.pdf")],
            title="Save User Report As"
        )
        
        if not output_file:
            return
        
        # Create PDF in LANDSCAPE mode
        from reportlab.lib.pagesizes import landscape, letter
        c = canvas.Canvas(output_file, pagesize=landscape(letter))
        width, height = landscape(letter)  # Now width > height
        
        # Title and header
        c.setFont("Helvetica-Bold", 16)
        c.drawString(50, height - 50, "User Management Report")
        c.setFont("Helvetica", 10)
        c.drawString(50, height - 70, f"Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        c.drawString(50, height - 85, f"Total Users: {len(users_list)}")
        
        # Table setup - WIDER COLUMNS FOR LANDSCAPE
        headers = ["Employee ID", "Name", "Department", "Position", "Email", "Status", "Compliance"]
        col_widths = [90, 120, 100, 100, 150, 70, 90]  # Wider columns
        x_positions = [50]
        for i in range(1, len(col_widths)):
            x_positions.append(x_positions[i-1] + col_widths[i-1])
        
        y_position = height - 110
        
        # Table headers
        c.setFont("Helvetica-Bold", 9)
        for i, header in enumerate(headers):
            c.drawString(x_positions[i], y_position, header)
        
        # Draw line under headers
        c.line(50, y_position - 5, sum(col_widths) + 50, y_position - 5)
        
        # Table data
        c.setFont("Helvetica", 8)
        y_position -= 20
        
        for user in users_list:
            employee_id = user['employee_id']
            full_name = user['full_name']
            department = user['department']
            position = user['position']
            email = user['email']
            account_status = user['account_status']
            return_compliance_status = user['return_compliance_status']
            
            # Prepare display values - NO TRUNCATION NEEDED IN LANDSCAPE
            display_name = full_name
            display_department = department
            display_position = position
            display_email = email
            
            status_text = account_status or "Active"
            compliance_text = return_compliance_status or "Good Standing"
            
            row_data = [
                employee_id or "N/A",
                display_name,
                display_department,
                display_position,
                display_email,
                status_text,
                compliance_text
            ]
            
            # Check if we need a new page
            if y_position < 50:
                c.showPage()
                # Set up new page in landscape
                c.setPageSize(landscape(letter))
                y_position = height - 50
                
                # Page header for continuation
                c.setFont("Helvetica-Bold", 10)
                c.drawString(50, height - 30, "User Management Report (Continued)")
                
                # Redraw headers on new page
                c.setFont("Helvetica-Bold", 9)
                for i, header in enumerate(headers):
                    c.drawString(x_positions[i], y_position, header)
                c.line(50, y_position - 5, sum(col_widths) + 50, y_position - 5)
                y_position -= 20
                c.setFont("Helvetica", 8)
            
            # Draw row
            for i, data in enumerate(row_data):
                c.drawString(x_positions[i], y_position, str(data))
            
            y_position -= 15
        
        # Summary page
        c.showPage()
        c.setPageSize(landscape(letter))  # Keep landscape for summary
        c.setFont("Helvetica-Bold", 16)
        c.drawString(50, height - 50, "User Management Summary")
        
        c.setFont("Helvetica", 11)  # Slightly larger font for summary
        y_pos = height - 80
        
        # Basic counts
        c.drawString(50, y_pos, f"Total Active Users: {len(users_list)}")
        y_pos -= 25
        
        # Count by department
        department_count = {}
        status_count = {"Active": 0, "Inactive": 0}
        compliance_count = {}
        
        for user in users_list:
            department = user['department'] or "Unknown"
            status = user['account_status'] or "Active"
            compliance = user['return_compliance_status'] or "Good Standing"
            
            department_count[department] = department_count.get(department, 0) + 1
            status_count[status] = status_count.get(status, 0) + 1
            compliance_count[compliance] = compliance_count.get(compliance, 0) + 1
        
        c.drawString(50, y_pos, "Users by Department:")
        y_pos -= 20
        
        # Two column layout for departments
        col1_x = 65
        col2_x = width / 2 + 20
        current_col = col1_x
        max_per_col = 8
        
        for i, (department, count) in enumerate(department_count.items()):
            if i == max_per_col:
                current_col = col2_x
                y_pos = height - 100  # Reset y position for second column
            
            c.drawString(current_col, y_pos, f"• {department}: {count} users")
            y_pos -= 18
        
        # Status and compliance section
        y_pos = min(y_pos, height - 100)  # Ensure we have space
        y_pos -= 20
        
        c.drawString(50, y_pos, "Users by Status:")
        y_pos -= 20
        c.drawString(65, y_pos, f"• Active: {status_count.get('Active', 0)}")
        y_pos -= 18
        c.drawString(65, y_pos, f"• Inactive: {status_count.get('Inactive', 0)}")
        
        y_pos -= 20
        c.drawString(50, y_pos, "Compliance Status:")
        y_pos -= 20
        
        for compliance, count in compliance_count.items():
            c.drawString(65, y_pos, f"• {compliance}: {count} users")
            y_pos -= 18
        
        # Add a nice border and footer
        c.setStrokeColorRGB(0.8, 0.8, 0.8)
        c.setLineWidth(1)
        c.rect(40, 40, width - 80, height - 80)  # Border around content
        
        # Footer
        c.setFont("Helvetica", 8)
        c.setFillColorRGB(0.5, 0.5, 0.5)
        c.drawString(50, 30, f"KLD Institute of Nursing - Laboratory Equipment Management System")
        c.drawString(width - 200, 30, f"Page 1")
        
        c.save()
        messagebox.showinfo("Success", f"PDF report generated successfully!\n\nSaved to: {output_file}")
        
    except Exception as e:
        messagebox.showerror("Error", f"Failed to generate PDF report: {str(e)}")
    finally:
        conn.close()

def send_credentials_email(recipient_email, full_name, employee_id, password):
    """Send account credentials via email"""
    if not ENABLE_EMAIL:
        return False, "Email sending is disabled in configuration"
    
    if EMAIL_CONFIG['sender_email'] == 'your-email@gmail.com':
        return False, "Email not configured. Please update EMAIL_CONFIG with your SMTP credentials"
    
    try:
        msg = MIMEMultipart('alternative')
        msg['Subject'] = 'Your LEMS Account Credentials - KLD Institute of Nursing'
        msg['From'] = f"{EMAIL_CONFIG['sender_name']} <{EMAIL_CONFIG['sender_email']}>"
        msg['To'] = recipient_email
        
        html_body = f"""
        <html>
          <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
            <div style="max-width: 600px; margin: 0 auto; padding: 20px; border: 1px solid #ddd; border-radius: 5px;">
              <h2 style="color: #2c5530; border-bottom: 2px solid #2c5530; padding-bottom: 10px;">
                Welcome to LEMS
              </h2>
              <p><strong>Kolehiyo ng Lungsod ng Dasmarinas</strong><br>
              Institute of Nursing<br>
              Laboratory Equipment Management System</p>
              <p>Dear <strong>{full_name}</strong>,</p>
              <p>Your LEMS account has been successfully created. Below are your login credentials:</p>
              <div style="background-color: #f5f5f5; padding: 15px; border-radius: 5px; margin: 20px 0;">
                <p style="margin: 5px 0;"><strong>Employee ID:</strong> {employee_id}</p>
                <p style="margin: 5px 0;"><strong>Email:</strong> {recipient_email}</p>
                <p style="margin: 5px 0;"><strong>Temporary Password:</strong> <code style="background-color: #fff; padding: 2px 5px; border: 1px solid #ddd;">{password}</code></p>
              </div>
              <div style="background-color: #fff3cd; border-left: 4px solid #ffc107; padding: 10px; margin: 20px 0;">
                <p style="margin: 0;"><strong>Important Security Notice:</strong></p>
                <p style="margin: 5px 0 0 0;">Please change your password immediately after your first login for security purposes.</p>
              </div>
              <p><strong>Next Steps:</strong></p>
              <ol>
                <li>Login to LEMS using your email and temporary password</li>
                <li>Change your password in your profile settings</li>
                <li>Complete your profile information</li>
              </ol>
              <p>If you have any questions or need assistance, please contact the LEMS administrator.</p>
              <hr style="border: none; border-top: 1px solid #ddd; margin: 20px 0;">
              <p style="font-size: 12px; color: #666;">
                This is an automated message from the Laboratory Equipment Management System.<br>
                Please do not reply to this email.<br>
                If you did not expect this email, please contact the system administrator immediately.
              </p>
            </div>
          </body>
        </html>
        """
        
        text_body = f"""
        Welcome to LEMS
        
        Kolehiyo ng Lungsod ng Dasmarinas
        Institute of Nursing
        Laboratory Equipment Management System
        
        Dear {full_name},
        
        Your LEMS account has been successfully created. Below are your login credentials:
        
        Employee ID: {employee_id}
        Email: {recipient_email}
        Temporary Password: {password}
        
        IMPORTANT: Please change your password immediately after your first login for security purposes.
        
        Next Steps:
        1. Login to LEMS using your email and temporary password
        2. Change your password in your profile settings
        3. Complete your profile information
        
        If you have any questions or need assistance, please contact the LEMS administrator.
        
        ---
        This is an automated message from the Laboratory Equipment Management System.
        Please do not reply to this email.
        If you did not expect this email, please contact the system administrator immediately.
        """
        
        part1 = MIMEText(text_body, 'plain')
        part2 = MIMEText(html_body, 'html')
        msg.attach(part1)
        msg.attach(part2)
        
        with smtplib.SMTP(EMAIL_CONFIG['smtp_server'], EMAIL_CONFIG['smtp_port']) as server:
            server.starttls()
            server.login(EMAIL_CONFIG['sender_email'], EMAIL_CONFIG['sender_password'])
            server.send_message(msg)
        
        return True, "Email sent successfully"
        
    except smtplib.SMTPAuthenticationError:
        return False, "Email authentication failed. Please check your email credentials."
    except smtplib.SMTPException as e:
        return False, f"SMTP error occurred: {str(e)}"
    except Exception as e:
        return False, f"Failed to send email: {str(e)}"

def show_new_account_dialog(root, admin_email):
    """Show dialog to create new account - NO CONTACT NUMBER"""
    dialog = Toplevel(root)
    dialog.title("Add New Account")
    dialog.geometry("500x550")
    dialog.configure(bg="#f5f5f5")
    dialog.transient(root)
    dialog.grab_set()
    
    dialog.update_idletasks()
    x = (dialog.winfo_screenwidth() // 2) - (500 // 2)
    y = (dialog.winfo_screenheight() // 2) - (550 // 2)
    dialog.geometry(f"500x550+{x}+{y}")
    
    Label(dialog, text="Create New Account", font=("Arial", 16, "bold"),
          bg="#f5f5f5", fg="#333").pack(pady=20)
    
    form_frame = Frame(dialog, bg="white", relief="solid", borderwidth=1)
    form_frame.pack(fill="both", expand=True, padx=20, pady=(0, 20))
    
    fields = {}
    field_names = [
        ("Full Name", "full_name"),
        ("Employee ID", "employee_id"),
        ("Email", "email"),
        ("Department", "department"),
        ("Position", "position")
    ]
    
    for label_text, field_name in field_names:
        field_frame = Frame(form_frame, bg="white")
        field_frame.pack(fill="x", padx=20, pady=10)
        
        Label(field_frame, text=label_text, font=("Arial", 10),
              bg="white", fg="#333", anchor="w").pack(fill="x")
        
        entry = Entry(field_frame, font=("Arial", 10), relief="solid", borderwidth=1)
        entry.pack(fill="x", pady=(5, 0), ipady=5)
        fields[field_name] = entry
    
    button_frame = Frame(dialog, bg="#f5f5f5")
    button_frame.pack(fill="x", padx=20, pady=(0, 20))
    
    def create_account():
        for field_name, entry in fields.items():
            if not entry.get().strip():
                messagebox.showerror("Error", f"Please fill in {field_name.replace('_', ' ')}")
                return
        
        password = ''.join(secrets.choice(string.ascii_letters + string.digits) for _ in range(12))
        
        conn = get_db_connection()
        if not conn:
            messagebox.showerror("Database Error", "Could not connect to database!")
            return
            
        try:
            with conn.cursor() as cursor:
                cursor.execute("SELECT id FROM users WHERE email = %s", (fields['email'].get().strip(),))
                if cursor.fetchone():
                    messagebox.showerror("Error", "Email already exists")
                    return
                
                cursor.execute("INSERT INTO users (email, password, role) VALUES (%s, %s, 'faculty')", 
                              (fields['email'].get().strip(), password))
                user_id = cursor.lastrowid
                
                cursor.execute("""
                    INSERT INTO user_profiles (
                        user_id, full_name, employee_id, department, position, 
                        account_status, return_compliance_status, is_archived
                    ) VALUES (%s, %s, %s, %s, %s, 'Active', 'Good Standing', 0)
                """, (
                    user_id,
                    fields['full_name'].get().strip(),
                    fields['employee_id'].get().strip(),
                    fields['department'].get().strip(),
                    fields['position'].get().strip()
                ))
                
                conn.commit()
                
                success, message = send_credentials_email(
                    fields['email'].get().strip(),
                    fields['full_name'].get().strip(),
                    fields['employee_id'].get().strip(),
                    password
                )
                
                if success:
                    messagebox.showinfo("Success", "Account created successfully! Credentials sent via email.")
                else:
                    messagebox.showwarning("Partial Success", 
                        f"Account created but email failed: {message}\nPassword: {password}")
                
                dialog.destroy()
                show_user_management(root, admin_email)
                
        except Exception as e:
            messagebox.showerror("Error", f"Failed to create account: {str(e)}")
            conn.rollback()
        finally:
            conn.close()
    
    Button(button_frame, text="Create Account", font=("Arial", 10, "bold"),
           bg="#007bff", fg="white", relief="flat", padx=20, pady=10,
           command=create_account).pack(side="left", expand=True, fill="x", padx=(0, 5))
    
    Button(button_frame, text="Cancel", font=("Arial", 10),
           bg="#6c757d", fg="white", relief="flat", padx=20, pady=10,
           command=dialog.destroy).pack(side="right", expand=True, fill="x", padx=(5, 0))

def edit_user(user_data, root, admin_email):
    """Edit user information - NO CONTACT NUMBER"""
    user_id = user_data['user_id']
    full_name = user_data['full_name']
    employee_id = user_data['employee_id']
    department = user_data['department']
    position = user_data['position']
    account_status = user_data['account_status']
    email = user_data['email']
    
    dialog = Toplevel(root)
    dialog.title("Edit User")
    dialog.geometry("500x650")
    dialog.configure(bg="#f5f5f5")
    dialog.transient(root)
    dialog.grab_set()
    
    dialog.update_idletasks()
    x = (dialog.winfo_screenwidth() // 2) - (500 // 2)
    y = (dialog.winfo_screenheight() // 2) - (650 // 2)
    dialog.geometry(f"500x650+{x}+{y}")
    
    Label(dialog, text="Edit User Information", font=("Arial", 16, "bold"),
          bg="#f5f5f5", fg="#333").pack(pady=20)
    
    form_frame = Frame(dialog, bg="white", relief="solid", borderwidth=1)
    form_frame.pack(fill="both", expand=True, padx=20, pady=(0, 20))
    
    fields = {}
    field_data = [
        ("Full Name", "full_name", full_name),
        ("Employee ID", "employee_id", employee_id),
        ("Email", "email", email),
        ("Department", "department", department),
        ("Position", "position", position)
    ]
    
    for label_text, field_name, initial_value in field_data:
        field_frame = Frame(form_frame, bg="white")
        field_frame.pack(fill="x", padx=20, pady=10)
        
        Label(field_frame, text=label_text, font=("Arial", 10),
              bg="white", fg="#333", anchor="w").pack(fill="x")
        
        entry = Entry(field_frame, font=("Arial", 10), relief="solid", borderwidth=1)
        entry.pack(fill="x", pady=(5, 0), ipady=5)
        entry.insert(0, initial_value or "")
        fields[field_name] = entry
    
    status_frame = Frame(form_frame, bg="white")
    status_frame.pack(fill="x", padx=20, pady=10)
    
    Label(status_frame, text="Account Status", font=("Arial", 10),
          bg="white", fg="#333", anchor="w").pack(fill="x")
    
    status_var = StringVar(value=account_status or "Active")
    status_menu = OptionMenu(status_frame, status_var, "Active", "Inactive")
    status_menu.config(font=("Arial", 10), relief="solid", borderwidth=1)
    status_menu.pack(fill="x", pady=(5, 0))
    
    button_frame = Frame(dialog, bg="#f5f5f5")
    button_frame.pack(fill="x", padx=20, pady=(0, 20))
    
    def save_changes():
        conn = get_db_connection()
        if not conn:
            messagebox.showerror("Database Error", "Could not connect to database!")
            return
            
        try:
            with conn.cursor() as cursor:
                cursor.execute("""
                    UPDATE user_profiles
                    SET full_name = %s, employee_id = %s, department = %s, 
                        position = %s, account_status = %s
                    WHERE user_id = %s
                """, (
                    fields['full_name'].get().strip(),
                    fields['employee_id'].get().strip(),
                    fields['department'].get().strip(),
                    fields['position'].get().strip(),
                    status_var.get(),
                    user_id
                ))
                
                cursor.execute("UPDATE users SET email = %s WHERE id = %s", 
                              (fields['email'].get().strip(), user_id))
                
                conn.commit()
                messagebox.showinfo("Success", "User information updated successfully!")
                dialog.destroy()
                show_user_management(root, admin_email)
                
        except Exception as e:
            messagebox.showerror("Error", f"Failed to update user: {str(e)}")
            conn.rollback()
        finally:
            conn.close()
    
    Button(button_frame, text="Save Changes", font=("Arial", 10, "bold"),
           bg="#007bff", fg="white", relief="flat", padx=20, pady=10,
           command=save_changes).pack(side="left", expand=True, fill="x", padx=(0, 5))
    
    Button(button_frame, text="Cancel", font=("Arial", 10),
           bg="#6c757d", fg="white", relief="flat", padx=20, pady=10,
           command=dialog.destroy).pack(side="right", expand=True, fill="x", padx=(5, 0))

def confirm_archive_user(user_data, root, admin_email):
    """Confirm before archiving user"""
    user_id = user_data['user_id']
    full_name = user_data['full_name']
    
    result = messagebox.askyesno(
        "Archive User",
        f"Are you sure you want to archive {full_name}?\n\nArchived users can be restored later.",
        icon='warning'
    )
    
    if result:
        conn = get_db_connection()
        if not conn:
            messagebox.showerror("Database Error", "Could not connect to database!")
            return
            
        try:
            with conn.cursor() as cursor:
                cursor.execute("UPDATE user_profiles SET is_archived = 1 WHERE user_id = %s", (user_id,))
                conn.commit()
                messagebox.showinfo("Success", f"{full_name} has been archived successfully!")
                show_user_management(root, admin_email)
                
        except Exception as e:
            messagebox.showerror("Error", f"Failed to archive user: {str(e)}")
            conn.rollback()
        finally:
            conn.close()

def confirm_restore_user(user_data, root, admin_email):
    """Confirm before restoring user"""
    user_id = user_data['user_id']
    full_name = user_data['full_name']
    
    result = messagebox.askyesno(
        "Restore User",
        f"Are you sure you want to restore {full_name}?",
        icon='question'
    )
    
    if result:
        conn = get_db_connection()
        if not conn:
            messagebox.showerror("Database Error", "Could not connect to database!")
            return
            
        try:
            with conn.cursor() as cursor:
                cursor.execute("UPDATE user_profiles SET is_archived = 0 WHERE user_id = %s", (user_id,))
                conn.commit()
                messagebox.showinfo("Success", f"{full_name} has been restored successfully!")
                show_archived_users(root, admin_email)
                
        except Exception as e:
            messagebox.showerror("Error", f"Failed to restore user: {str(e)}")
            conn.rollback()
        finally:
            conn.close()

def confirm_delete_user(user_data, root, admin_email):
    """Confirm before permanently deleting user"""
    user_id = user_data['user_id']
    full_name = user_data['full_name']
    
    result = messagebox.askyesno(
        "Delete User Permanently",
        f"Are you sure you want to PERMANENTLY delete {full_name}?\n\nThis action cannot be undone!",
        icon='warning'
    )
    
    if result:
        result2 = messagebox.askyesno(
            "Final Confirmation",
            "This will permanently delete all user data.\n\nAre you absolutely sure?",
            icon='warning'
        )
        
        if result2:
            conn = get_db_connection()
            if not conn:
                messagebox.showerror("Database Error", "Could not connect to database!")
                return
                
            try:
                with conn.cursor() as cursor:
                    cursor.execute("DELETE FROM user_profiles WHERE user_id = %s", (user_id,))
                    cursor.execute("DELETE FROM users WHERE id = %s", (user_id,))
                    conn.commit()
                    messagebox.showinfo("Success", f"{full_name} has been permanently deleted!")
                    show_archived_users(root, admin_email)
                    
            except Exception as e:
                messagebox.showerror("Error", f"Failed to delete user: {str(e)}")
                conn.rollback()
            finally:
                conn.close()

def show_user_management(root, admin_email):
    """Display user management interface with equipment management style"""
    # Clear window
    for widget in root.winfo_children():
        widget.destroy()
    
    root.geometry("1920x1080")
    root.configure(bg="#f5f5f5")

   # Top bar with consistent styling - MATCHING RESERVATION STYLE
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

    tk.Label(left_header, text="User Management", 
        font=("Helvetica", 18, "bold"), bg="#2c5530", fg="white").pack(side="left")

    right_header = tk.Frame(header_content, bg="#2c5530")
    right_header.pack(side="right")

    # Back button - SAME STYLE AS RESERVATION
    def back_to_dashboard():
        try:
            from admindashboard import show_admin_dashboard
            show_admin_dashboard(root, admin_email)
        except ImportError:
            messagebox.showerror("Error", "Admin dashboard module not found")

    tk.Button(right_header, text="Back", font=("Helvetica", 10),
        bg="white", fg="#2c5530", relief="flat", width=8,
        command=back_to_dashboard).pack(side="left", padx=(0, 10))

    # Admin info - ADJUSTED TO MATCH RESERVATION STYLE
    admin_label = tk.Label(right_header, text=f"Admin: {admin_email}", font=("Arial", 11), 
                        bg="#2c5530", fg="white")
    admin_label.pack(side="right", padx=(10, 0))

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

    # Content container with padding
    content_container = tk.Frame(main, bg="#f5f5f5")
    content_container.pack(expand=True, fill="both", padx=60, pady=40)

    # Search section with shadow - like equipment management
    shadow1 = tk.Frame(content_container, bg="#d0d0d0")
    shadow1.pack(fill="x", pady=(0, 25))
    
    search_section = tk.Frame(shadow1, bg="white", relief="flat")
    search_section.pack(fill="x", padx=2, pady=2)
    
    # Search header
    search_header = tk.Frame(search_section, bg="#e8f5e9", height=50)
    search_header.pack(fill="x")
    search_header.pack_propagate(False)
    
    tk.Label(search_header, text="Search Users", font=("Arial", 13, "bold"),
             bg="#e8f5e9", fg="#2c5530").pack(anchor="w", padx=30, pady=15)
    
    # Search content
    search_content = tk.Frame(search_section, bg="white")
    search_content.pack(fill="x", padx=40, pady=25)
    
    search_var = tk.StringVar()
    
    search_frame = tk.Frame(search_content, bg="white")
    search_frame.pack()
    
    tk.Label(search_frame, text="🔍", font=("Arial", 16), bg="white").pack(side="left", padx=(0, 10))
    
    search_entry = tk.Entry(search_frame, width=40, font=("Arial", 11), 
                            relief="solid", bd=1, textvariable=search_var, bg="white")
    search_entry.pack(side="left", ipady=6, padx=(0, 15))
    
    def perform_search():
        search_term = search_var.get().strip().lower()
        load_users_into_table(search_term)
    
    search_btn = tk.Button(search_frame, text="Search", font=("Arial", 10, "bold"),
              bg="#2c5530", fg="white", relief="flat", cursor="hand2",
              padx=20, pady=6, command=perform_search)
    search_btn.pack(side="left", padx=5)
    
    clear_btn = tk.Button(search_frame, text="Clear", font=("Arial", 10, "bold"),
              bg="#999", fg="white", relief="flat", cursor="hand2",
              padx=20, pady=6,
              command=lambda: [search_var.set(""), load_users_into_table("")])
    clear_btn.pack(side="left", padx=5)

    # Action buttons frame
    action_frame = tk.Frame(search_content, bg="white")
    action_frame.pack(fill="x", pady=(15, 0))
    
    def open_new_account_dialog():
        show_new_account_dialog(root, admin_email)
    
    add_btn = tk.Button(action_frame, text="➕ Add New Account", font=("Arial", 10, "bold"),
              bg="#007bff", fg="white", relief="flat", cursor="hand2",
              padx=20, pady=6, command=open_new_account_dialog)
    add_btn.pack(side="left", padx=5)
    
    def open_archive():
        show_archived_users(root, admin_email)
    
    archive_btn = tk.Button(action_frame, text="📁 View Archive", font=("Arial", 10, "bold"),
              bg="#6c757d", fg="white", relief="flat", cursor="hand2",
              padx=20, pady=6, command=open_archive)
    archive_btn.pack(side="left", padx=5)
    
    # ADD PDF REPORT BUTTON
    def generate_user_report():
        generate_user_pdf_report()

    report_btn = tk.Button(action_frame, text="📄 Print Report", font=("Arial", 10, "bold"),
          bg="#6f42c1", fg="white", relief="flat", cursor="hand2",
          padx=20, pady=6, command=generate_user_report)
    report_btn.pack(side="left", padx=5)

    # Table section with shadow - exactly like equipment management
    shadow2 = tk.Frame(content_container, bg="#d0d0d0")
    shadow2.pack(fill="both", expand=True)
    
    table_section = tk.Frame(shadow2, bg="white", relief="flat")
    table_section.pack(fill="both", expand=True, padx=2, pady=2)
    
    # Table header
    table_header = tk.Frame(table_section, bg="#e3f2fd", height=50)
    table_header.pack(fill="x")
    table_header.pack_propagate(False)
    
    tk.Label(table_header, text="User Management", font=("Arial", 13, "bold"),
             bg="#e3f2fd", fg="#2c5530").pack(side="left", padx=30, pady=15)
    
    # Count label in header
    count_label = tk.Label(table_header, text="Total: 0", font=("Arial", 11),
                          bg="#e3f2fd", fg="#2c5530")
    count_label.pack(side="right", padx=30)

    # Table frame with scrollbar - exactly like equipment management
    table_frame = tk.Frame(table_section, bg="white")
    table_frame.pack(fill="both", expand=True, padx=20, pady=20)

    # Scrollbars
    vsb = ttk.Scrollbar(table_frame, orient="vertical")
    vsb.pack(side="right", fill="y")
    
    hsb = ttk.Scrollbar(table_frame, orient="horizontal")
    hsb.pack(side="bottom", fill="x")

    # Table columns - user specific fields but same style
    columns = ("ID", "EMPLOYEE ID", "NAME", "DEPARTMENT", "POSITION", "EMAIL", "STATUS", "COMPLIANCE", "EDIT", "ARCHIVE")
    
    tree = ttk.Treeview(table_frame, columns=columns, show="headings", height=15,
                       yscrollcommand=vsb.set, xscrollcommand=hsb.set)
    tree.pack(fill="both", expand=True)
    
    vsb.config(command=tree.yview)
    hsb.config(command=tree.xview)

    # Configure columns
    column_widths = {
        "ID": 60,
        "EMPLOYEE ID": 120,
        "NAME": 200,
        "DEPARTMENT": 150,
        "POSITION": 150,
        "EMAIL": 200,
        "STATUS": 100,
        "COMPLIANCE": 120,
        "EDIT": 80,
        "ARCHIVE": 80
    }
    
    for col in columns:
        tree.heading(col, text=col)
        tree.column(col, width=column_widths.get(col, 100), anchor="center")

    # Enhanced style for table matching equipment management
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
    
    # Tag configurations for alternating rows
    tree.tag_configure('oddrow', background='#f9f9f9')
    tree.tag_configure('evenrow', background='white')
    tree.tag_configure('inactive', background='#f8d7da')

    def load_users_into_table(search_term=""):
        """Load users data into the table with search"""
        # Clear existing items
        for item in tree.get_children():
            tree.delete(item)
        
        conn = get_db_connection()
        if not conn:
            messagebox.showerror("Database Error", "Could not connect to database!")
            return
            
        try:
            with conn.cursor() as cursor:
                # Base query
                query = """
                    SELECT p.user_id, p.full_name, p.employee_id, 
                           p.department, p.position, p.account_status, p.return_compliance_status,
                           u.email
                    FROM user_profiles p
                    JOIN users u ON p.user_id = u.id
                    WHERE COALESCE(p.is_archived, 0) = 0
                """
                params = []
                
                # Add search filter
                if search_term:
                    query += " AND (LOWER(p.full_name) LIKE %s OR LOWER(p.employee_id) LIKE %s OR LOWER(u.email) LIKE %s OR LOWER(p.department) LIKE %s)"
                    search_pattern = f"%{search_term}%"
                    params.extend([search_pattern, search_pattern, search_pattern, search_pattern])
                
                query += " ORDER BY p.full_name ASC"
                
                cursor.execute(query, params)
                users_list = cursor.fetchall()

            # Insert into table
            for idx, user in enumerate(users_list):
                user_id = user['user_id']
                full_name = user['full_name']
                employee_id = user['employee_id']
                department = user['department']
                position = user['position']
                account_status = user['account_status']
                return_compliance_status = user['return_compliance_status']
                email = user['email']
                
                # Determine row tag based on status
                tag = 'evenrow' if idx % 2 == 0 else 'oddrow'
                if account_status == "Inactive":
                    tag = 'inactive'
                
                # Status display with color coding
                status_text = account_status or "Active"
                
                # Compliance display
                compliance_text = return_compliance_status or "Good Standing"
                
                row_values = (
                    user_id,
                    employee_id or "N/A",
                    full_name or "N/A",
                    department or "N/A",
                    position or "N/A",
                    email or "N/A",
                    status_text,
                    compliance_text,
                    " Edit",
                    " Archive"
                )
                
                tree.insert("", "end", values=row_values, tags=(tag,))

            # Update count
            count_label.config(text=f"Total: {len(users_list)}")

        except Exception as e:
            error_msg = f"Database error: {str(e)}"
            print(error_msg)
            tree.insert("", "end", values=("Error", "Loading users", error_msg[:50], "", "", "", "", "", "", ""))
        finally:
            conn.close()

    # Context menu for actions
    context_menu = tk.Menu(tree, tearoff=0)
    context_menu.add_command(label="Edit User", command=lambda: edit_selected_user())
    context_menu.add_command(label="Archive User", command=lambda: archive_selected_user())
    
    def show_context_menu(event):
        item = tree.identify_row(event.y)
        if item:
            tree.selection_set(item)
            context_menu.post(event.x_root, event.y_root)
    
    tree.bind("<Button-3>", show_context_menu)  # Right-click
    
    def edit_selected_user():
        selection = tree.selection()
        if not selection:
            messagebox.showwarning("Warning", "Please select a user to edit")
            return
        
        try:
            item = tree.item(selection[0])
            user_id = item['values'][0]  # ID is in first column
            user_data = get_user_data(user_id)
            if user_data:
                edit_user(user_data, root, admin_email)
        except Exception as e:
            messagebox.showerror("Error", f"Failed to edit user: {str(e)}")
    
    def archive_selected_user():
        selection = tree.selection()
        if not selection:
            messagebox.showwarning("Warning", "Please select a user to archive")
            return
        
        try:
            item = tree.item(selection[0])
            user_id = item['values'][0]
            user_name = item['values'][2]
            user_data = get_user_data(user_id)
            if user_data:
                confirm_archive_user(user_data, root, admin_email)
        except Exception as e:
            messagebox.showerror("Error", f"Failed to archive user: {str(e)}")
    
    def get_user_data(user_id):
        """Get complete user data from database"""
        conn = get_db_connection()
        if not conn:
            messagebox.showerror("Database Error", "Could not connect to database!")
            return None
            
        try:
            with conn.cursor() as cursor:
                cursor.execute("""
                    SELECT p.user_id, p.full_name, p.employee_id, 
                           p.department, p.position, p.account_status, p.return_compliance_status,
                           u.email
                    FROM user_profiles p
                    JOIN users u ON p.user_id = u.id
                    WHERE p.user_id = %s
                """, (user_id,))
                user_data = cursor.fetchone()
                return user_data
        except Exception as e:
            messagebox.showerror("Error", f"Failed to get user data: {str(e)}")
            return None
        finally:
            conn.close()
    
    # Click function for edit and archive columns
    def on_tree_click(event):
        item = tree.identify_row(event.y)
        column = tree.identify_column(event.x)
        
        if item and column:
            col_name = tree.heading(column)["text"]
            if col_name == "EDIT":
                edit_selected_user()
            elif col_name == "ARCHIVE":
                archive_selected_user()

    tree.bind("<Button-1>", on_tree_click)
    
    # Double-click to edit
    tree.bind("<Double-1>", lambda e: edit_selected_user())
    
    # Load initial data
    load_users_into_table()
    
    # Bind search on Enter key
    search_entry.bind("<Return>", lambda e: perform_search())

def show_archived_users(root, admin_email):
    """Display archived users with equipment management style"""
    # Clear window
    for widget in root.winfo_children():
        widget.destroy()
    
    root.geometry("1920x1080")
    root.configure(bg="#f5f5f5")

    # Top bar
    top = tk.Frame(root, bg="#6c757d", height=70)
    top.pack(fill="x", side="top")
    top.pack_propagate(False)

    tk.Button(top, text="← Back", font=("Arial", 12), bg="#6c757d", fg="white",
              border=0, cursor="hand2", relief="flat",
              command=lambda: show_user_management(root, admin_email)).pack(side="left", padx=30, pady=20)

    tk.Label(top, text="Archived Users", bg="#6c757d", fg="white",
             font=("Arial", 16, "bold")).pack(side="left", padx=10, pady=20)

    # Main content
    main = tk.Frame(root, bg="#f5f5f5")
    main.pack(expand=True, fill="both")
    
    # Content container
    content_container = tk.Frame(main, bg="#f5f5f5")
    content_container.pack(expand=True, fill="both", padx=60, pady=40)

    # Table section
    shadow = tk.Frame(content_container, bg="#d0d0d0")
    shadow.pack(fill="both", expand=True)
    
    table_section = tk.Frame(shadow, bg="white", relief="flat")
    table_section.pack(fill="both", expand=True, padx=2, pady=2)
    
    # Table header
    table_header = tk.Frame(table_section, bg="#e3f2fd", height=50)
    table_header.pack(fill="x")
    table_header.pack_propagate(False)
    
    tk.Label(table_header, text="Archived Users", font=("Arial", 13, "bold"),
             bg="#e3f2fd", fg="#6c757d").pack(side="left", padx=30, pady=15)

    # Table frame
    table_frame = tk.Frame(table_section, bg="white")
    table_frame.pack(fill="both", expand=True, padx=20, pady=20)

    # Scrollbars
    vsb = ttk.Scrollbar(table_frame, orient="vertical")
    vsb.pack(side="right", fill="y")
    
    hsb = ttk.Scrollbar(table_frame, orient="horizontal")
    hsb.pack(side="bottom", fill="x")

    # Table columns for archived users
    columns = ("ID", "EMPLOYEE ID", "NAME", "DEPARTMENT", "POSITION", "EMAIL", "RESTORE", "DELETE")
    
    tree = ttk.Treeview(table_frame, columns=columns, show="headings", height=15,
                       yscrollcommand=vsb.set, xscrollcommand=hsb.set)
    tree.pack(fill="both", expand=True)
    
    vsb.config(command=tree.yview)
    hsb.config(command=tree.xview)

    # Configure columns
    column_widths = {
        "ID": 60,
        "EMPLOYEE ID": 120,
        "NAME": 200,
        "DEPARTMENT": 150,
        "POSITION": 150,
        "EMAIL": 200,
        "RESTORE": 80,
        "DELETE": 80
    }
    
    for col in columns:
        tree.heading(col, text=col)
        tree.column(col, width=column_widths.get(col, 100), anchor="center")
    
    # Style for archived table
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
                   foreground="#6c757d")
    
    # Tag configurations
    tree.tag_configure('oddrow', background='#f9f9f9')
    tree.tag_configure('evenrow', background='white')

    def load_archived_users_into_table():
        """Load archived users into the table"""
        for item in tree.get_children():
            tree.delete(item)
        
        conn = get_db_connection()
        if not conn:
            messagebox.showerror("Database Error", "Could not connect to database!")
            return
            
        try:
            with conn.cursor() as cursor:
                cursor.execute("""
                    SELECT p.user_id, p.full_name, p.employee_id, 
                           p.department, p.position, u.email
                    FROM user_profiles p
                    JOIN users u ON p.user_id = u.id
                    WHERE p.is_archived = 1
                    ORDER BY p.full_name
                """)
                
                archived_list = cursor.fetchall()
                
            for idx, user in enumerate(archived_list):
                user_id = user['user_id']
                full_name = user['full_name']
                employee_id = user['employee_id']
                department = user['department']
                position = user['position']
                email = user['email']
                
                tag = 'evenrow' if idx % 2 == 0 else 'oddrow'
                
                row_values = (
                    user_id,
                    employee_id or "N/A",
                    full_name or "N/A",
                    department or "N/A",
                    position or "N/A",
                    email or "N/A",
                    "↶ Restore",
                    "🗑️ Delete"
                )
                
                tree.insert("", "end", values=row_values, tags=(tag,))

        except Exception as e:
            tree.insert("", "end", values=("Error", "Loading archived", str(e)[:50], "", "", "", "", ""))
        finally:
            conn.close()

    # Click function for archived table
    def on_archived_tree_click(event):
        item = tree.identify_row(event.y)
        column = tree.identify_column(event.x)
        
        if item and column:
            col_name = tree.heading(column)["text"]
            if col_name == "RESTORE":
                restore_selected_user()
            elif col_name == "DELETE":
                delete_selected_user()

    tree.bind("<Button-1>", on_archived_tree_click)
    
    def restore_selected_user():
        selection = tree.selection()
        if not selection:
            messagebox.showwarning("Warning", "Please select a user to restore")
            return
        
        try:
            item = tree.item(selection[0])
            user_id = item['values'][0]
            user_name = item['values'][2]
            user_data = get_archived_user_data(user_id)
            if user_data:
                confirm_restore_user(user_data, root, admin_email)
        except Exception as e:
            messagebox.showerror("Error", f"Failed to restore user: {str(e)}")
    
    def delete_selected_user():
        selection = tree.selection()
        if not selection:
            messagebox.showwarning("Warning", "Please select a user to delete")
            return
        
        try:
            item = tree.item(selection[0])
            user_id = item['values'][0]
            user_name = item['values'][2]
            user_data = get_archived_user_data(user_id)
            if user_data:
                confirm_delete_user(user_data, root, admin_email)
        except Exception as e:
            messagebox.showerror("Error", f"Failed to delete user: {str(e)}")
    
    def get_archived_user_data(user_id):
        """Get complete archived user data from database"""
        conn = get_db_connection()
        if not conn:
            messagebox.showerror("Database Error", "Could not connect to database!")
            return None
            
        try:
            with conn.cursor() as cursor:
                cursor.execute("""
                    SELECT p.user_id, p.full_name, p.employee_id, 
                           p.department, p.position, p.account_status, p.return_compliance_status,
                           u.email
                    FROM user_profiles p
                    JOIN users u ON p.user_id = u.id
                    WHERE p.user_id = %s AND p.is_archived = 1
                """, (user_id,))
                user_data = cursor.fetchone()
                return user_data
        except Exception as e:
            messagebox.showerror("Error", f"Failed to get user data: {str(e)}")
            return None
        finally:
            conn.close()
    
    # Load archived data
    load_archived_users_into_table()

def init_user_database():
    """Initialize the database for user management testing"""
    conn = get_db_connection()
    if not conn:
        print(" Database initialization failed: Could not connect to database!")
        return
        
    try:
        with conn.cursor() as cursor:
            # Ensure tables exist
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    email VARCHAR(255) UNIQUE NOT NULL, 
                    password VARCHAR(255) NOT NULL,
                    role VARCHAR(50) NOT NULL CHECK(role IN ('admin', 'faculty'))
                )
            """)
            
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS user_profiles (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    user_id INT NOT NULL,
                    full_name VARCHAR(255) NOT NULL,
                    employee_id VARCHAR(100) UNIQUE NOT NULL,
                    department VARCHAR(255) NOT NULL,
                    position VARCHAR(255) NOT NULL,
                    account_status VARCHAR(50) NOT NULL DEFAULT 'Active',
                    return_compliance_status VARCHAR(100) NOT NULL DEFAULT 'Good Standing',
                    is_archived TINYINT DEFAULT 0,
                    FOREIGN KEY (user_id) REFERENCES users (id)
                )
            """)
            
            # Insert test admin account if not exists
            cursor.execute("INSERT IGNORE INTO users (email, password, role) VALUES (%s, %s, %s)",
                          ("admin@nursing.com", "admin123", "admin"))
            
            cursor.execute("""
                INSERT IGNORE INTO user_profiles 
                (user_id, full_name, employee_id, department, position, account_status, return_compliance_status)
                SELECT id, 'Admin User', 'EID-000', 'Administration', 'System Administrator', 'Active', 'Good Standing'
                FROM users WHERE email = 'admin@nursing.com'
            """)
            
            conn.commit()
            print(" User database initialized successfully!")
            
    except Exception as e:
        print(f" Database initialization error: {str(e)}")
        conn.rollback()
    finally:
        conn.close()

if __name__ == "__main__":
    root = tk.Tk()
    root.title("User Management System")
    root.geometry("1920x1080")
    
    # Initialize database first
    init_user_database()
    
    # Test with admin account
    show_user_management(root, "admin@nursing.com")
    
    root.mainloop()