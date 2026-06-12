#loginpage.py
import tkinter as tk
from tkinter import messagebox
from loginform import LoginForm

class MainApp:
    def __init__(self, root):
        self.root = root
        self.root.title("ION - Laboratory Equipment Management System")
        self.root.configure(bg='#2c5530')  # Green background
        
        # Start in fullscreen mode
        self.root.attributes('-fullscreen', True)
        
        # Add modern styling
        self.setup_modern_styling()
        
        # Store reference to current dashboard window
        self.current_dashboard = None
        
        # Create login form
        self.login_form = LoginForm(root, self.on_login_success)
        
    def setup_modern_styling(self):
        """Setup modern styling for the application"""
        # Configure modern color scheme
        self.root.option_add('*Background', '#2c5530')
        self.root.option_add('*Foreground', '#333333')
        self.root.option_add('*Font', 'Helvetica 10')
        
    def on_login_success(self, user_data):
        """Handle successful login - redirect based on user role"""
        user_role = user_data.get('role', 'faculty').lower()
        user_email = user_data.get('email', '')
        
        # Hide the login window
        self.root.withdraw()
        
        try:
            # Check if user is admin
            if user_role == 'admin':
                from admindashboard import show_admin_dashboard
                
                admin_window = tk.Toplevel(self.root)
                admin_window.title("Admin Dashboard - Faculty Equipment Management")
                admin_window.attributes('-fullscreen', True)
                admin_window.configure(bg='#f8f9fa')
                
                # Store reference to current dashboard
                self.current_dashboard = admin_window
                
                show_admin_dashboard(admin_window, user_email, self)
                
                def on_admin_close():
                    admin_window.destroy()
                    self.current_dashboard = None
                    self.root.deiconify()
                    self.login_form.clear_form()
                
                admin_window.protocol("WM_DELETE_WINDOW", on_admin_close)
                
            else:
                from home import show_homepage
                
                home_window = tk.Toplevel(self.root)
                home_window.title("Faculty Equipment Management System")
                home_window.attributes('-fullscreen', True)
                home_window.configure(bg='#f8f9fa')
                
                # Store reference to current dashboard
                self.current_dashboard = home_window
                
                show_homepage(home_window, user_email, self)
                
                def on_home_close():
                    home_window.destroy()
                    self.current_dashboard = None
                    self.root.deiconify()
                    self.login_form.clear_form()
                
                home_window.protocol("WM_DELETE_WINDOW", on_home_close)
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load dashboard: {str(e)}")
            self.root.deiconify()
    
    def logout(self):
        """Logout and show login screen"""
        print("DEBUG: Logout initiated")  # Debug line
        
        # Destroy current dashboard window
        if self.current_dashboard:
            self.current_dashboard.destroy()
            self.current_dashboard = None
        
        # Clear any session data or cached roles
        if hasattr(self, 'cached_role'):
            delattr(self, 'cached_role')
        
        # Show the main login window and clear form
        self.root.deiconify()
        self.login_form.clear_form()
        
        # Force focus back to login window
        self.root.focus_force()

def main():
    root = tk.Tk()
    app = MainApp(root)
    root.mainloop()

if __name__ == "__main__":
    main()