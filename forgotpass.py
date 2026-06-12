# forgotpass.py - MySQL Version
import tkinter as tk
from tkinter import Entry, Label, Frame, Button, messagebox
import random
import string
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
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
# Email Configuration
SMTP_SERVER = 'smtp.gmail.com'
SMTP_PORT = 587
SENDER_EMAIL = 'kld.nursing.lems@gmail.com'
SENDER_PASSWORD = 'uphzottyfoprbbbu'
SYSTEM_NAME = "KLD Nursing Lab Equipment Management System"


def generate_reset_code():
    """Generate a 6-digit verification code"""
    return ''.join(random.choices(string.digits, k=6))

def send_reset_email(recipient_email, recipient_name, reset_code):
    """Send password reset code via email"""
    msg = MIMEMultipart('alternative')
    msg['Subject'] = f"Password Reset Code - {SYSTEM_NAME}"
    msg['From'] = SENDER_EMAIL
    msg['To'] = recipient_email
    
    html = f"""
    <html>
      <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
        <div style="max-width: 600px; margin: 0 auto; padding: 20px; border: 2px solid #e84e89; border-radius: 10px;">
          <div style="background-color: #e84e89; color: white; padding: 15px; border-radius: 5px; text-align: center;">
            <h2 style="margin: 0;">Password Reset Request</h2>
          </div>
          
          <div style="padding: 20px;">
            <p><strong>Dear {recipient_name},</strong></p>
            <p>We received a request to reset your password for the {SYSTEM_NAME}.</p>
            
            <div style="background-color: #f8f9fa; padding: 20px; border-radius: 5px; text-align: center; margin: 20px 0;">
              <p style="margin: 0; font-size: 14px; color: #666;">Your verification code is:</p>
              <h1 style="margin: 10px 0; color: #e84e89; font-size: 36px; letter-spacing: 5px;">{reset_code}</h1>
              <p style="margin: 0; font-size: 12px; color: #666;">This code will expire in 15 minutes</p>
            </div>
            
            <div style="padding: 15px; background-color: #fff3cd; border-left: 4px solid #ffc107; margin: 20px 0;">
              <p style="margin: 0; font-weight: bold; color: #856404;">
                Security Notice: If you did not request this password reset, please ignore this email or contact the administrator immediately.
              </p>
            </div>
            
            <p>Enter this code in the password reset window to continue.</p>
          </div>
          
          <div style="padding: 20px; text-align: center; color: #666; border-top: 1px solid #ddd;">
            <p style="font-size: 12px; margin-top: 20px;">
              This is an automated message from the {SYSTEM_NAME}.<br>
              KLD Institute of Nursing - Equipment Custodian Office
            </p>
          </div>
        </div>
      </body>
    </html>
    """
    
    text = f"""
    Password Reset Request
    
    Dear {recipient_name},
    
    We received a request to reset your password for the {SYSTEM_NAME}.
    
    Your verification code is: {reset_code}
    
    This code will expire in 15 minutes.
    
    Security Notice: If you did not request this password reset, please ignore this email or contact the administrator immediately.
    
    ---
    KLD Institute of Nursing - LEMS
    Equipment Custodian Office
    """
    
    part1 = MIMEText(text, 'plain')
    part2 = MIMEText(html, 'html')
    msg.attach(part1)
    msg.attach(part2)
    
    try:
        server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
        server.starttls()
        server.login(SENDER_EMAIL, SENDER_PASSWORD)
        server.send_message(msg)
        server.quit()
        return True
    except Exception as e:
        print(f"Failed to send email: {e}")
        return False

def show_forgot_password(root, return_to_login):
    """Display forgot password interface"""
    for widget in root.winfo_children():
        widget.destroy()
    
    root.configure(bg='#fbb3bb')
    
    # Main container
    main_frame = Frame(root, bg='white', relief='flat', bd=0)
    main_frame.place(relx=0.5, rely=0.5, anchor="center", width=500, height=600)
    
    # Shadow effect
    shadow_frame = Frame(main_frame, bg='#e0e0e0', relief='flat', bd=0)
    shadow_frame.place(x=5, y=5, relwidth=1, relheight=1)
    
    # Content card
    content_frame = Frame(main_frame, bg='white', relief='flat', bd=1, 
                         highlightthickness=2, highlightbackground='#f0f0f0')
    content_frame.place(relx=0.5, rely=0.5, anchor="center", width=490, height=590)
    
    # Header
    header_frame = Frame(content_frame, bg='#e84e89')
    header_frame.pack(fill="x", pady=(0, 30))
    
    Label(header_frame, text="Reset Password", font=("Arial", 24, "bold"), 
          bg='#e84e89', fg='white').pack(pady=20)
    
    # Content area
    content_area = Frame(content_frame, bg='white')
    content_area.pack(fill="both", expand=True, padx=40, pady=20)
    
    # Store verification code and user data
    verification_data = {'code': None, 'email': None, 'name': None}
    
    # Step 1: Email Entry
    def show_step1():
        for widget in content_area.winfo_children():
            widget.destroy()
        
        Label(content_area, text="Enter your email address", 
              font=("Arial", 14), bg='white', fg='#495057').pack(pady=(0, 10))
        
        Label(content_area, text="We will send you a verification code", 
              font=("Arial", 11), bg='white', fg='#6c757d').pack(pady=(0, 30))
        
        email_frame = Frame(content_area, bg='white')
        email_frame.pack(fill="x", pady=(0, 20))
        
        Label(email_frame, text="Email Address", font=("Arial", 11, "bold"), 
              bg='white', fg='#495057', anchor="w").pack(fill="x")
        
        email_entry = Entry(email_frame, font=("Arial", 12), relief="solid", bd=1,
                           highlightthickness=1, highlightbackground='#e9ecef')
        email_entry.pack(fill="x", pady=(8, 0), ipady=10)
        email_entry.focus_set()
        
        def send_code():
            email = email_entry.get().strip()
            
            if not email:
                messagebox.showwarning("Missing Information", "Please enter your email address.")
                return
            
            # Check if email exists in database
            conn = get_db_connection()
            if conn is None:
                messagebox.showerror("Database Error", "Cannot connect to database.")
                return
                
            cursor = conn.cursor()
            cursor.execute("""
                SELECT u.email, up.full_name 
                FROM users u
                LEFT JOIN user_profiles up ON u.id = up.user_id
                WHERE u.email = %s
            """, (email,))
            result = cursor.fetchone()
            conn.close()
            
            if not result:
                messagebox.showerror("Email Not Found", 
                                   "No account found with this email address.")
                return
            
            user_email = result['email']
            user_name = result['full_name']
            user_name = user_name or "User"
            
            # Generate and send code
            reset_code = generate_reset_code()
            
            # Show loading message
            send_btn.config(state='disabled', text='Sending...')
            root.update()
            
            if send_reset_email(user_email, user_name, reset_code):
                verification_data['code'] = reset_code
                verification_data['email'] = user_email
                verification_data['name'] = user_name
                
                messagebox.showinfo("Code Sent", 
                                  f"A verification code has been sent to {email}")
                show_step2()
            else:
                messagebox.showerror("Email Error", 
                                   "Failed to send verification code. Please try again.")
                send_btn.config(state='normal', text='Send Verification Code')
        
        send_btn = Button(content_area, text="Send Verification Code", 
                         font=("Arial", 12, "bold"), bg="#e84e89", fg="white",
                         padx=20, pady=12, relief="flat", cursor="hand2",
                         activebackground="#d63d75", command=send_code)
        send_btn.pack(fill="x", pady=(20, 10))
        
        Button(content_area, text="Back to Login", font=("Arial", 11), 
               bg="white", fg="#6c757d", relief="flat", cursor="hand2",
               command=lambda: return_to_login(root)).pack(pady=10)
        
        email_entry.bind("<Return>", lambda e: send_code())
    
    # Step 2: Code Verification
    def show_step2():
        for widget in content_area.winfo_children():
            widget.destroy()
        
        Label(content_area, text="Enter Verification Code", 
              font=("Arial", 14), bg='white', fg='#495057').pack(pady=(0, 10))
        
        Label(content_area, text=f"Code sent to {verification_data['email']}", 
              font=("Arial", 11), bg='white', fg='#6c757d').pack(pady=(0, 30))
        
        code_frame = Frame(content_area, bg='white')
        code_frame.pack(fill="x", pady=(0, 20))
        
        Label(code_frame, text="Verification Code", font=("Arial", 11, "bold"), 
              bg='white', fg='#495057', anchor="w").pack(fill="x")
        
        code_entry = Entry(code_frame, font=("Arial", 16, "bold"), relief="solid", 
                          bd=1, highlightthickness=1, highlightbackground='#e9ecef',
                          justify='center')
        code_entry.pack(fill="x", pady=(8, 0), ipady=10)
        code_entry.focus_set()
        
        def verify_code():
            entered_code = code_entry.get().strip()
            
            if not entered_code:
                messagebox.showwarning("Missing Code", "Please enter the verification code.")
                return
            
            if entered_code == verification_data['code']:
                show_step3()
            else:
                messagebox.showerror("Invalid Code", "The verification code is incorrect.")
        
        Button(content_area, text="Verify Code", font=("Arial", 12, "bold"), 
               bg="#e84e89", fg="white", padx=20, pady=12, relief="flat",
               cursor="hand2", activebackground="#d63d75", 
               command=verify_code).pack(fill="x", pady=(20, 10))
        
        def resend_code():
            new_code = generate_reset_code()
            if send_reset_email(verification_data['email'], 
                              verification_data['name'], new_code):
                verification_data['code'] = new_code
                messagebox.showinfo("Code Resent", "A new verification code has been sent.")
            else:
                messagebox.showerror("Error", "Failed to resend code.")
        
        Button(content_area, text="Resend Code", font=("Arial", 11), 
               bg="white", fg="#e84e89", relief="flat", cursor="hand2",
               command=resend_code).pack(pady=5)
        
        Button(content_area, text="Back", font=("Arial", 11), 
               bg="white", fg="#6c757d", relief="flat", cursor="hand2",
               command=show_step1).pack(pady=5)
        
        code_entry.bind("<Return>", lambda e: verify_code())
    
    # Step 3: New Password
    def show_step3():
        for widget in content_area.winfo_children():
            widget.destroy()
        
        Label(content_area, text="Create New Password", 
              font=("Arial", 14), bg='white', fg='#495057').pack(pady=(0, 30))
        
        # New password
        pass_frame1 = Frame(content_area, bg='white')
        pass_frame1.pack(fill="x", pady=(0, 15))
        
        Label(pass_frame1, text="New Password", font=("Arial", 11, "bold"), 
              bg='white', fg='#495057', anchor="w").pack(fill="x")
        
        new_pass_entry = Entry(pass_frame1, font=("Arial", 12), show="*", 
                              relief="solid", bd=1, highlightthickness=1,
                              highlightbackground='#e9ecef')
        new_pass_entry.pack(fill="x", pady=(8, 0), ipady=10)
        new_pass_entry.focus_set()
        
        # Confirm password
        pass_frame2 = Frame(content_area, bg='white')
        pass_frame2.pack(fill="x", pady=(0, 30))
        
        Label(pass_frame2, text="Confirm Password", font=("Arial", 11, "bold"), 
              bg='white', fg='#495057', anchor="w").pack(fill="x")
        
        confirm_pass_entry = Entry(pass_frame2, font=("Arial", 12), show="*", 
                                  relief="solid", bd=1, highlightthickness=1,
                                  highlightbackground='#e9ecef')
        confirm_pass_entry.pack(fill="x", pady=(8, 0), ipady=10)
        
        def reset_password():
            new_password = new_pass_entry.get()
            confirm_password = confirm_pass_entry.get()
            
            if not new_password or not confirm_password:
                messagebox.showwarning("Missing Information", 
                                     "Please fill in all fields.")
                return
            
            if len(new_password) < 6:
                messagebox.showwarning("Weak Password", 
                                     "Password must be at least 6 characters long.")
                return
            
            if new_password != confirm_password:
                messagebox.showerror("Password Mismatch", 
                                   "Passwords do not match.")
                return
            
            # Update password in database
            conn = get_db_connection()
            if conn is None:
                messagebox.showerror("Database Error", "Cannot connect to database.")
                return
                
            cursor = conn.cursor()
            cursor.execute("UPDATE users SET password = %s WHERE email = %s",
                          (new_password, verification_data['email']))
            conn.commit()
            conn.close()
            
            messagebox.showinfo("Success", 
                              "Your password has been reset successfully!")
            return_to_login(root)
        
        Button(content_area, text="Reset Password", font=("Arial", 12, "bold"), 
               bg="#28a745", fg="white", padx=20, pady=12, relief="flat",
               cursor="hand2", activebackground="#218838",
               command=reset_password).pack(fill="x", pady=(10, 10))
        
        Button(content_area, text="Cancel", font=("Arial", 11), 
               bg="white", fg="#6c757d", relief="flat", cursor="hand2",
               command=lambda: return_to_login(root)).pack(pady=5)
        
        new_pass_entry.bind("<Return>", lambda e: confirm_pass_entry.focus_set())
        confirm_pass_entry.bind("<Return>", lambda e: reset_password())
    
    # Start with step 1
    show_step1()