#loginform.py
import tkinter as tk
from tkinter import ttk, messagebox
import pymysql
from PIL import Image, ImageTk
import re
from forgotpass import show_forgot_password
import os
import sys

def resource_path(relative_path):
    """Get absolute path to resource, works for dev and for PyInstaller"""
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

class LoginForm:
    def __init__(self, root, on_login_success):
        self.root = root
        self.on_login_success = on_login_success
        self.setup_ui()

    def setup_ui(self):
        # Clear any existing widgets
        for widget in self.root.winfo_children():
            widget.destroy()

        # Configure root window with modern gradient
        self.root.configure(bg='#2c5530')
        
        # Create modern gradient background
        self.create_modern_gradient()
        
        # Main container using grid for split screen
        main_container = tk.Frame(self.root, bg='#2c5530')
        main_container.pack(expand=True, fill='both', padx=0, pady=0)
        
        # Configure grid weights for split screen (40% left, 60% right)
        main_container.grid_columnconfigure(0, weight=4)
        main_container.grid_columnconfigure(1, weight=6)
        main_container.grid_rowconfigure(0, weight=1)
        
        # LEFT SIDE - Logo and Branding (Pink Background)
        left_frame = tk.Frame(main_container, bg='#f9bec0')
        left_frame.grid(row=0, column=0, sticky='nsew', padx=(0, 0))
        
        # RIGHT SIDE - Login Form (White Background)
        right_frame = tk.Frame(main_container, bg='white')
        right_frame.grid(row=0, column=1, sticky='nsew', padx=(0, 0))
        
        # Setup left side content
        self.setup_left_side(left_frame)
        
        # Setup right side content
        self.setup_right_side(right_frame)

    def setup_left_side(self, parent):
        """Setup the left side with logo and branding"""
        # Center container for left side content
        center_frame = tk.Frame(parent, bg='#f9bec0')
        center_frame.place(relx=0.5, rely=0.5, anchor='center')
        
        # Larger logo
        try: 
            logo_path = resource_path("ion_logo.png")
            logo_img = Image.open(logo_path).resize((180, 180))  # Bigger logo
            logo_photo = ImageTk.PhotoImage(logo_img)
            logo_label = tk.Label(center_frame, image=logo_photo, bg='#f9bec0')
            logo_label.image = logo_photo
            logo_label.pack(pady=(0, 20))
        except Exception as e:
            print(f"Logo loading error: {e}")
            # Fallback to text logo
            logo_label = tk.Label(center_frame, text="🏥", font=("Arial", 48), 
                                bg='#f9bec0', fg='white')
            logo_label.pack(pady=(0, 20))
        
        # Institute name with larger font
        title_label = tk.Label(center_frame, 
                             text="INSTITUTE OF NURSING", 
                             font=("Helvetica", 26, "bold"), 
                             bg='#f9bec0', fg='white')
        title_label.pack(pady=(0, 10))
        
        # System description
        system_label = tk.Label(center_frame,
                              text="Laboratory Equipment\nManagement System",
                              font=("Helvetica", 20),
                              bg='#f9bec0', fg='white',
                              justify='center')
        system_label.pack(pady=(0, 30))
        
        # Decorative elements
        self.create_decorative_elements(parent)

    def setup_right_side(self, parent):
        """Setup the right side with login form"""
        # Center container for login form
        center_frame = tk.Frame(parent, bg='white')
        center_frame.place(relx=0.5, rely=0.5, anchor='center')
        
        # Login form container with shadow
        form_container = tk.Frame(center_frame, bg='white', relief='flat', bd=0)
        form_container.pack(padx=40, pady=40)
        
        # Add subtle shadow
        self.create_shadow(form_container)
        
        # Form content
        content_frame = tk.Frame(form_container, bg='white', width=400)
        content_frame.pack(fill='both', expand=True, padx=30, pady=40)
        
        # Welcome section
        welcome_label = tk.Label(content_frame, 
                               text="Welcome Back",
                               font=("Helvetica", 24, "bold"),
                               bg='white', fg='#2c5530')
        welcome_label.pack(pady=(0, 8))
        
        signin_label = tk.Label(content_frame,
                              text="Sign in to your account",
                              font=("Helvetica", 12),
                              bg='white', fg='#666666')
        signin_label.pack(pady=(0, 40))
        
        # Email field with modern styling
        email_frame = tk.Frame(content_frame, bg='white')
        email_frame.pack(fill='x', pady=(0, 20))
        
        email_label = tk.Label(email_frame, text="EMAIL ADDRESS",
                             font=("Helvetica", 10, "bold"),
                             bg='white', fg='#2c5530', anchor='w')
        email_label.pack(fill='x', pady=(0, 8))
        
        self.email_entry = ttk.Entry(email_frame, font=("Helvetica", 12))
        self.email_entry.pack(fill='x', ipady=10)
        self.style_modern_entry(self.email_entry)
        self.email_entry.bind('<Return>', lambda e: self.password_entry.focus())
        
        # Password field
        password_frame = tk.Frame(content_frame, bg='white')
        password_frame.pack(fill='x', pady=(0, 20))
        
        password_label = tk.Label(password_frame, text="PASSWORD",
                                font=("Helvetica", 10, "bold"),
                                bg='white', fg='#2c5530', anchor='w')
        password_label.pack(fill='x', pady=(0, 8))
        
        self.password_entry = ttk.Entry(password_frame, show="•", 
                                      font=("Helvetica", 12))
        self.password_entry.pack(fill='x', ipady=10)
        self.style_modern_entry(self.password_entry)
        self.password_entry.bind('<Return>', lambda e: self.login())
        
        # Show password checkbox with pink accent
        self.show_password_var = tk.BooleanVar()
        show_password_check = tk.Checkbutton(content_frame, 
                                           text="Show Password",
                                           variable=self.show_password_var,
                                           font=("Helvetica", 10),
                                           bg='white', fg='#2c5530',
                                           selectcolor='#f9bec0',
                                           activebackground='white',
                                           activeforeground='#2c5530',
                                           command=self.toggle_password_visibility)
        show_password_check.pack(anchor='w', pady=(10, 0))
        
        # Forgot password with pink color
        forgot_frame = tk.Frame(content_frame, bg='white')
        forgot_frame.pack(fill='x', pady=(25, 30))
        
        forgot_btn = tk.Button(forgot_frame, 
                             text="Forgot Password?",
                             font=("Helvetica", 10, "underline"),
                             bg='white', fg="#2c5530",
                             relief='flat', border=0,
                             cursor='hand2',
                             command=self.show_forgot_password)
        forgot_btn.pack(side='right')
        
        # Modern login button with pink color
        self.login_button = tk.Button(content_frame,
                                    text="SIGN IN",
                                    font=("Helvetica", 13, "bold"),
                                    bg='#f9bec0',
                                    fg='white',
                                    relief='flat',
                                    cursor='hand2',
                                    command=self.login)
        self.login_button.pack(fill='x', ipady=14, pady=(0, 20))
        
        # Add modern hover effects
        def on_enter(e):
            self.login_button.config(bg='#f9bec0')  # Darker pink on hover
        def on_leave(e):
            self.login_button.config(bg='#f9bec0')  # Normal pink
        
        self.login_button.bind("<Enter>", on_enter)
        self.login_button.bind("<Leave>", on_leave)
        
        # Modern footer
        footer_frame = tk.Frame(content_frame, bg='white')
        footer_frame.pack(fill='x')
        
        footer_label = tk.Label(footer_frame,
                              text="Secure Access • Faculty Management • 2025",
                              font=("Helvetica", 9),
                              bg='white', fg='#2c5530')
        footer_label.pack(pady=(20, 0))
        
        # Focus on email entry
        self.email_entry.focus()
        
        # Bind Enter key to login
        self.root.bind('<Return>', lambda e: self.login())

    def create_decorative_elements(self, parent):
        """Add decorative elements to the left side"""
        # Top decorative circle
        top_circle = tk.Frame(parent, bg='#f9bec0', width=100, height=100)
        top_circle.place(relx=0.8, rely=0.1)
        top_circle.pack_propagate(False)
        
        # Bottom decorative circle
        bottom_circle = tk.Frame(parent, bg='#f9bec0', width=80, height=80)
        bottom_circle.place(relx=0.1, rely=0.8)
        bottom_circle.pack_propagate(False)

    def create_modern_gradient(self):
        """Create a modern gradient background"""
        try:
            gradient_frame = tk.Frame(self.root)
            gradient_frame.place(x=0, y=0, relwidth=1, relheight=1)
            
            # Modern gradient with more pink tones
            colors = [
                '#2c5530', '#3a6b3d', '#f9bec0', "#f198bc", 
                '#ff80b3', '#ff99c2', '#ffb3d1', '#ffcce0'
            ]
            steps = 120
            
            for i in range(steps):
                # More pink in the gradient
                if i < steps * 0.3:
                    # Green to pink transition
                    color_index = min(int(i / (steps * 0.3) * 3), 2)
                    color = colors[color_index]
                else:
                    # Pink shades
                    color_index = 2 + min(int((i - steps * 0.3) / (steps * 0.7) * 5), 5)
                    color = colors[color_index]
                
                # Create gradient strip
                strip = tk.Frame(gradient_frame, bg=color, height=1)
                strip.place(x=0, y=i * (900/steps), relwidth=1, height=(900/steps) + 1)
                
        except Exception as e:
            print(f"Gradient background failed: {e}")

    def create_shadow(self, widget):
        """Create a subtle shadow effect around widget"""
        # Use a light gray color instead of RGBA
        shadow = tk.Frame(self.root, bg='#e0e0e0', relief='flat')
        shadow.place(relx=0.7, rely=0.5, anchor='center', 
                    width=widget.winfo_reqwidth() + 8, 
                    height=widget.winfo_reqheight() + 8)
        shadow.lower(widget)

    def style_modern_entry(self, entry):
        """Apply modern styling to entry widgets"""
        style = ttk.Style()
        style.configure('Modern.TEntry', 
                       fieldbackground='#f8f9fa',
                       bordercolor='#ddd',
                       focuscolor='#f9bec0',
                       padding=(12, 10))

    def toggle_password_visibility(self):
        """Toggle password visibility using checkbox"""
        if self.show_password_var.get():
            self.password_entry.config(show="")
        else:
            self.password_entry.config(show="•")

    def show_forgot_password(self):
        """Show forgot password screen"""
        def return_to_login(root):
            # Return to login form
            self.setup_ui()
        
        show_forgot_password(self.root, return_to_login)

    def get_db_connection(self):
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

    def validate_email(self, email):
        """Validate email format"""
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return re.match(pattern, email) is not None

    def login(self):
        """Handle login process with proper connection handling"""
        email = self.email_entry.get().strip()
        password = self.password_entry.get()
        
        # Validation
        if not email or not password:
            messagebox.showerror("Error", "Please fill in all fields")
            return
            
        if not self.validate_email(email):
            messagebox.showerror("Error", "Please enter a valid email address")
            return
        
        # Disable login button during attempt
        self.login_button.config(state='disabled', text="SIGNING IN...", bg='#cccccc')
        self.root.update()
        
        conn = None
        try:
            conn = self.get_db_connection()
            if conn is None:
                self.login_button.config(state='normal', text="SIGN IN", bg='#f9bec0')
                return
                
            cursor = conn.cursor()
            
            # Query users table for authentication
            cursor.execute("""
                SELECT email, password, role
                FROM users 
                WHERE email = %s
            """, (email,))
            
            user = cursor.fetchone()
            
            if user and user['password'] == password:
                # Get additional info from user_profiles
                first_name = ""
                last_name = ""

                try:
                    cursor.execute("""
                        SELECT first_name, last_name 
                        FROM user_profiles 
                        WHERE email = %s
                    """, (email,))
                    profile = cursor.fetchone()
                    
                    if profile:
                        first_name = profile.get('first_name', '')
                        last_name = profile.get('last_name', '')
                except Exception as profile_error:
                    print(f"Profile fetch error (non-critical): {profile_error}")
                
                user_data = {
                    'email': user['email'],
                    'role': user['role'],
                    'first_name': first_name,
                    'last_name': last_name
                }
                
                # SUCCESSFUL LOGIN
                cursor.close()
                
                # Call the success callback
                self.on_login_success(user_data)
                
            else:
                messagebox.showerror("Login Failed", 
                                "Invalid email or password. Please try again.")
                self.password_entry.delete(0, tk.END)
                self.email_entry.focus()
                
        except Exception as e:
            messagebox.showerror("Error", f"Login failed: {str(e)}")
            print(f"Full error: {e}")
        
        finally:
            # Always ensure login button is re-enabled and connection is properly closed
            self.login_button.config(state='normal', text="SIGN IN", bg='#ff66a3')
            if conn:
                conn.close()

    def clear_form(self):
        """Clear the login form"""
        self.email_entry.delete(0, tk.END)
        self.password_entry.delete(0, tk.END)
        # Reset password visibility
        self.show_password_var.set(False)
        self.toggle_password_visibility()
        self.email_entry.focus()

# Demo function to test the login form
if __name__ == "__main__":
    
    root = tk.Tk()
    root.title("Institute of Nursing - Laboratory System")
    root.geometry("1000x700")
    
    login_form = LoginForm(root)
    root.mainloop()