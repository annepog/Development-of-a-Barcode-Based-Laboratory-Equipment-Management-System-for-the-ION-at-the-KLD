# issuereport.py - MySQL Version
import tkinter as tk
from tkinter import messagebox, ttk
from datetime import datetime
import pymysql
import time

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
def show_issue_report_popup(parent, user_email=None):
    """Display a popup window for reporting equipment issues"""
    
    if user_email is None:
        messagebox.showerror("Error", "User email is required to report an issue")
        return
    
    popup = tk.Toplevel(parent)
    popup.title("Report Equipment Issue")
    popup.geometry("500x600")
    popup.configure(bg="#f5f5f5")
    popup.resizable(False, False)
    
    popup.transient(parent)
    popup.grab_set()
    
    header = tk.Frame(popup, bg="#005c3c", height=60)
    header.pack(fill="x")
    header.pack_propagate(False)
    
    tk.Label(header, text="Report Equipment Issue", font=("Arial", 14, "bold"),
             bg="#005c3c", fg="white").pack(pady=15)
    
    content = tk.Frame(popup, bg="white")
    content.pack(fill="both", expand=True, padx=20, pady=20)
    
    tk.Label(content, text="Equipment Barcode:", font=("Arial", 11, "bold"),
             bg="white", fg="#333").pack(anchor="w", pady=(10, 5))
    
    barcode_entry = tk.Entry(content, font=("Arial", 11), width=40, relief="solid", bd=1)
    barcode_entry.pack(fill="x", ipady=8, pady=(0, 15))
    
    tk.Label(content, text="Issue Type:", font=("Arial", 11, "bold"),
             bg="white", fg="#333").pack(anchor="w", pady=(10, 5))
    
    issue_types = [
        "Equipment Damaged",
        "Equipment Malfunction",
        "Missing Parts",
        "Safety Concern",
        "Other"
    ]
    
    issue_var = tk.StringVar(value=issue_types[0])
    issue_dropdown = ttk.Combobox(content, textvariable=issue_var, values=issue_types,
                                 font=("Arial", 11), state="readonly", width=38)
    issue_dropdown.pack(fill="x", ipady=8, pady=(0, 15))
    
    tk.Label(content, text="Description:", font=("Arial", 11, "bold"),
             bg="white", fg="#333").pack(anchor="w", pady=(10, 5))
    
    tk.Label(content, text="Please provide detailed information about the issue:",
             font=("Arial", 9), bg="white", fg="#666").pack(anchor="w")
    
    description_text = tk.Text(content, font=("Arial", 10), height=8, width=40,
                              relief="solid", bd=1, wrap="word")
    description_text.pack(fill="both", expand=True, pady=(5, 15))
    
    tk.Label(content, text="Priority Level:", font=("Arial", 11, "bold"),
             bg="white", fg="#333").pack(anchor="w", pady=(10, 5))
    
    priority_var = tk.StringVar(value="Medium")
    priority_frame = tk.Frame(content, bg="white")
    priority_frame.pack(anchor="w", pady=(0, 15))
    
    for priority in ["Low", "Medium", "High", "Critical"]:
        tk.Radiobutton(priority_frame, text=priority, variable=priority_var,
                      value=priority, font=("Arial", 10), bg="white",
                      activebackground="white").pack(side="left", padx=(0, 15))
    
    def submit_issue():
        barcode = barcode_entry.get().strip()
        issue_type = issue_var.get()
        description = description_text.get("1.0", "end-1c").strip()
        priority = priority_var.get()
    
        if not barcode:
            messagebox.showwarning("Validation Error", "Please enter equipment barcode")
            barcode_entry.focus_set()
            return
        
        if not description:
            messagebox.showwarning("Validation Error", "Please provide a description")
            description_text.focus_set()
            return
        
        # Retry logic for database operations
        max_retries = 3
        for attempt in range(max_retries):
            try:
                conn = get_db_connection()
                if conn is None:
                    messagebox.showerror("Database Error", "Cannot connect to database")
                    return
                    
                cursor = conn.cursor()
                
                # Create equipment_issues table if it doesn't exist
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS equipment_issues (
                        issue_id INT AUTO_INCREMENT PRIMARY KEY,
                        barcode VARCHAR(255) NOT NULL,
                        equipment_name TEXT NOT NULL,
                        issue_type TEXT NOT NULL,
                        description TEXT NOT NULL,
                        priority TEXT NOT NULL,
                        status TEXT NOT NULL DEFAULT 'Pending',
                        reported_date TEXT NOT NULL,
                        resolved_date TEXT,
                        reported_by_user_id INT NOT NULL,
                        reported_by_name TEXT NOT NULL,
                        reported_by_email TEXT NOT NULL,
                        FOREIGN KEY (barcode) REFERENCES equipment(barcode),
                        FOREIGN KEY (reported_by_user_id) REFERENCES users(id)
                    )
                """)
                
                # Check if equipment exists
                cursor.execute("SELECT name FROM equipment WHERE barcode = %s", (barcode,))
                equipment = cursor.fetchone()
                
                if not equipment:
                    messagebox.showerror("Error", f"Equipment with barcode '{barcode}' not found")
                    conn.close()
                    return
                
                equipment_name = equipment['name']
                
                # Get user information
                cursor.execute("""
                    SELECT id, email, role FROM users WHERE email = %s
                """, (user_email,))
                
                user_info = cursor.fetchone()
                
                if not user_info:
                    messagebox.showerror("Error", "User information not found")
                    conn.close()
                    return
                
                user_id = user_info['id']
                email = user_info['email']
                role = user_info['role']
                
                # Get faculty name - try to get from user_profiles, fallback to email
                faculty_name = email  # Default to email
                try:
                    cursor.execute("SELECT full_name FROM user_profiles WHERE user_id = %s", (user_id,))
                    profile = cursor.fetchone()
                    if profile and profile['full_name']:
                        faculty_name = profile['full_name']
                except:
                    pass  # If user_profiles table doesn't exist or no profile, use email
                
                # Get current borrower information if equipment is borrowed
                current_borrower = "Unknown"
                try:
                    cursor.execute("""
                        SELECT borrower_name FROM borrow 
                        WHERE barcode = %s AND return_time IS NULL 
                        ORDER BY borrow_time DESC LIMIT 1
                    """, (barcode,))
                    borrow_info = cursor.fetchone()
                    if borrow_info:
                        current_borrower = borrow_info['borrower_name']
                except:
                    pass  # If borrow table doesn't exist or no current borrower
                
                timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                
                # Insert the issue report
                cursor.execute("""
                    INSERT INTO equipment_issues 
                    (barcode, equipment_name, issue_type, description, priority, reported_date, 
                    reported_by_user_id, reported_by_name, reported_by_email)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                """, (barcode, equipment_name, issue_type, description, priority, timestamp, 
                    user_id, faculty_name, email))
                
                # Also create a maintenance record to track equipment status
                try:
                    cursor.execute("""
                        CREATE TABLE IF NOT EXISTS maintenance_records (
                            record_id INT AUTO_INCREMENT PRIMARY KEY,
                            barcode VARCHAR(255) NOT NULL,
                            equipment_name TEXT NOT NULL,
                            issue_description TEXT NOT NULL,
                            reported_by TEXT NOT NULL,
                            reported_date TEXT NOT NULL,
                            status TEXT DEFAULT 'Reported',
                            current_borrower TEXT,
                            FOREIGN KEY (barcode) REFERENCES equipment(barcode)
                        )
                    """)
                    
                    cursor.execute("""
                        INSERT INTO maintenance_records 
                        (barcode, equipment_name, issue_description, reported_by, reported_date, current_borrower)
                        VALUES (%s, %s, %s, %s, %s, %s)
                    """, (barcode, equipment_name, f"{issue_type}: {description}", faculty_name, timestamp, current_borrower))
                    
                    # Update equipment status to "Under Maintenance" if it's damaged
                    if issue_type in ["Equipment Damaged", "Equipment Malfunction", "Safety Concern"]:
                        cursor.execute("""
                            UPDATE equipment SET availability_status = 'Under Maintenance' 
                            WHERE barcode = %s
                        """, (barcode,))
                        
                except Exception as e:
                    print(f"Note: Maintenance record not created: {e}")
                    # Continue even if maintenance records fail
                
                conn.commit()
                conn.close()
                
                # Success message with all tracking information
                success_msg = f"""
Issue reported successfully!

Equipment: {equipment_name}
Barcode: {barcode}
Issue Type: {issue_type}
Priority: {priority}

Reported by: {faculty_name} ({role})
Report Date: {timestamp}

Current Borrower: {current_borrower}

The maintenance team will be notified and equipment status has been updated.
"""
                messagebox.showinfo("Success", success_msg)
                popup.destroy()
                break  # Success, break out of retry loop
                
            except pymysql.OperationalError as e:
                if "locked" in str(e) and attempt < max_retries - 1:
                    if 'conn' in locals():
                        conn.close()
                    time.sleep(0.5 * (attempt + 1))  # Exponential backoff
                    continue
                else:
                    messagebox.showerror("Database Error", f"Failed to submit issue: {e}")
                    break
            except Exception as e:
                messagebox.showerror("Error", f"An unexpected error occurred: {e}")
                if 'conn' in locals():
                    conn.close()
                break
    
    button_frame = tk.Frame(content, bg="white")
    button_frame.pack(fill="x", pady=(15, 0))
    
    tk.Button(button_frame, text="Cancel", font=("Arial", 11, "bold"),
              bg="#999", fg="white", relief="flat", cursor="hand2",
              padx=30, pady=10, command=popup.destroy).pack(side="right", padx=5)
    
    tk.Button(button_frame, text="Submit Report", font=("Arial", 11, "bold"),
              bg="#005c3c", fg="white", relief="flat", cursor="hand2",
              padx=30, pady=10, command=submit_issue).pack(side="right", padx=5)
    
    barcode_entry.focus_set()
    
    popup.update_idletasks()
    x = parent.winfo_x() + (parent.winfo_width() // 2) - (popup.winfo_width() // 2)
    y = parent.winfo_y() + (parent.winfo_height() // 2) - (popup.winfo_height() // 2)
    popup.geometry(f"+{x}+{y}")

# Additional function to view reported issues (for admin)
def show_issue_tracker(parent, admin_email):
    """Show a window to track all reported equipment issues"""
    tracker = tk.Toplevel(parent)
    tracker.title("Equipment Issue Tracker")
    tracker.geometry("800x600")
    tracker.configure(bg="#f5f5f5")
    
    header = tk.Frame(tracker, bg="#005c3c", height=60)
    header.pack(fill="x")
    header.pack_propagate(False)
    
    tk.Label(header, text="Equipment Issue Tracker", font=("Arial", 16, "bold"),
             bg="#005c3c", fg="white").pack(pady=15)
    
    # Refresh button
    def refresh_issues():
        for widget in issues_frame.winfo_children():
            widget.destroy()
        load_issues()
    
    refresh_btn = tk.Button(header, text="Refresh", font=("Arial", 10),
                           bg="white", fg="#005c3c", relief="flat",
                           command=refresh_issues)
    refresh_btn.pack(side="right", padx=20)
    
    content = tk.Frame(tracker, bg="#f5f5f5")
    content.pack(fill="both", expand=True, padx=20, pady=20)
    
    # Create a scrollable frame for issues
    canvas = tk.Canvas(content, bg="#f5f5f5", highlightthickness=0)
    scrollbar = tk.Scrollbar(content, orient="vertical", command=canvas.yview)
    issues_frame = tk.Frame(canvas, bg="#f5f5f5")
    
    issues_frame.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
    canvas.create_window((0, 0), window=issues_frame, anchor="nw")
    canvas.configure(yscrollcommand=scrollbar.set)
    
    canvas.pack(side="left", fill="both", expand=True)
    scrollbar.pack(side="right", fill="y")
    
    def load_issues():
        try:
            conn = get_db_connection()
            if conn is None:
                tk.Label(issues_frame, text="Cannot connect to database", 
                        font=("Arial", 10), bg="#f5f5f5", fg="#dc3545").pack(pady=20)
                return
                
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT ei.issue_id, ei.equipment_name, ei.barcode, ei.issue_type, 
                       ei.priority, ei.status, ei.reported_date, ei.reported_by_name,
                       COALESCE(mr.current_borrower, 'Not Borrowed') as current_borrower
                FROM equipment_issues ei
                LEFT JOIN maintenance_records mr ON ei.barcode = mr.barcode 
                    AND mr.reported_date = ei.reported_date
                ORDER BY ei.reported_date DESC
            """)
            
            issues = cursor.fetchall()
            conn.close()
            
            if not issues:
                tk.Label(issues_frame, text="No issues reported yet", 
                        font=("Arial", 12), bg="#f5f5f5", fg="#666").pack(pady=50)
                return
            
            for issue in issues:
                issue_id = issue['issue_id']
                equipment_name = issue['equipment_name']
                barcode = issue['barcode']
                issue_type = issue['issue_type']
                priority = issue['priority']
                status = issue['status']
                reported_date = issue['reported_date']
                reported_by = issue['reported_by_name']
                current_borrower = issue['current_borrower']
                
                # Create issue card
                card = tk.Frame(issues_frame, bg="white", relief="solid", bd=1)
                card.pack(fill="x", pady=5, padx=10)
                
                # Priority color coding
                priority_colors = {
                    "Low": "#28a745",
                    "Medium": "#ffc107", 
                    "High": "#fd7e14",
                    "Critical": "#dc3545"
                }
                
                status_colors = {
                    "Pending": "#ffc107",
                    "In Progress": "#17a2b8",
                    "Resolved": "#28a745"
                }
                
                header_frame = tk.Frame(card, bg="white")
                header_frame.pack(fill="x", padx=15, pady=10)
                
                # Equipment info
                tk.Label(header_frame, text=f"{equipment_name} ({barcode})", 
                        font=("Arial", 12, "bold"), bg="white").pack(anchor="w")
                
                # Priority and status badges
                badge_frame = tk.Frame(header_frame, bg="white")
                badge_frame.pack(anchor="w", pady=(5, 0))
                
                tk.Label(badge_frame, text=priority, font=("Arial", 8, "bold"),
                        bg=priority_colors.get(priority, "#6c757d"), fg="white",
                        padx=8, pady=2).pack(side="left", padx=(0, 5))
                
                tk.Label(badge_frame, text=status, font=("Arial", 8, "bold"),
                        bg=status_colors.get(status, "#6c757d"), fg="white",
                        padx=8, pady=2).pack(side="left")
                
                # Details frame
                details_frame = tk.Frame(card, bg="white")
                details_frame.pack(fill="x", padx=15, pady=(0, 10))
                
                # Issue type and reporter
                tk.Label(details_frame, text=f"Issue: {issue_type}", 
                        font=("Arial", 9), bg="white").pack(anchor="w")
                tk.Label(details_frame, text=f"Reported by: {reported_by}", 
                        font=("Arial", 9), bg="white").pack(anchor="w")
                tk.Label(details_frame, text=f"Current Borrower: {current_borrower}", 
                        font=("Arial", 9), bg="white").pack(anchor="w")
                tk.Label(details_frame, text=f"Reported: {reported_date}", 
                        font=("Arial", 8), bg="white", fg="#666").pack(anchor="w")
                
        except Exception as e:
            tk.Label(issues_frame, text=f"Error loading issues: {e}", 
                    font=("Arial", 10), bg="#f5f5f5", fg="#dc3545").pack(pady=20)
    
    load_issues()
    
    tracker.update_idletasks()
    x = parent.winfo_x() + (parent.winfo_width() // 2) - (tracker.winfo_width() // 2)
    y = parent.winfo_y() + (parent.winfo_height() // 2) - (tracker.winfo_height() // 2)
    tracker.geometry(f"+{x}+{y}")