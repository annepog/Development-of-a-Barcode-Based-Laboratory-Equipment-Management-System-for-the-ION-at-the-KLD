import tkinter as tk
from tkinter import Label, Frame, Button, messagebox, Toplevel, Entry, StringVar, Text, filedialog
from tkinter import ttk
import pymysql
from PIL import Image, ImageTk, ImageEnhance
from datetime import datetime
import traceback
from reportlab.pdfgen import canvas
from notification_manager import NotificationManager 
from compliance_tracker import ComplianceTracker
import tempfile 

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
def check_equipment():
    """Placeholder for the check_equipment command"""
    messagebox.showinfo("Check Equipment", "Functionality to check equipment status in the database would go here.")

def verify_replacement(report_id, parent, admin_email):
    """
    Open a new window for the admin to enter the barcode 
    of the replacement equipment and confirm.
    """
    
    # 1. Fetch original equipment name and barcode
    try:
        conn = get_db_connection()
        if conn is None:
            return
            
        cursor = conn.cursor()
        cursor.execute("""
            SELECT equipment_name, barcode, reported_by_email 
            FROM equipment_issues 
            WHERE issue_id = %s
        """, (report_id,))
        result = cursor.fetchone()
        conn.close()
        
        if not result:
            messagebox.showerror("Error", "Report not found for verification!")
            return
            
        original_equipment_name = result['equipment_name']
        original_barcode = result['barcode']
        reported_by_email = result['reported_by_email']
        
    except Exception as e:
        messagebox.showerror("Database Error", f"Failed to fetch report details: {str(e)}")
        return

    # Create Toplevel window
    verify_window = Toplevel()
    verify_window.title(f"Verify Replacement for #{report_id}")
    verify_window.geometry("500x350")
    verify_window.configure(bg="white")
    verify_window.transient(parent.winfo_toplevel())
    verify_window.grab_set()
    
    # Header
    header = Frame(verify_window, bg="#28a745", height=50)
    header.pack(fill="x")
    Label(header, text="Verify Replacement", font=("Helvetica", 14, "bold"), 
          bg="#28a745", fg="white").pack(pady=10)
    
    # Content frame
    content = Frame(verify_window, bg="white", padx=30, pady=20)
    content.pack(fill="both", expand=True)

    Label(content, text=f"Report ID: #{report_id}", font=("Helvetica", 11, "bold"), bg="white", fg="#333").pack(anchor="w")
    Label(content, text=f"Original Equipment: {original_equipment_name}", font=("Helvetica", 11), bg="white", fg="#666").pack(anchor="w", pady=(0, 10))

    Label(content, text="Enter Barcode of Replacement Equipment:", font=("Helvetica", 10, "bold"), 
          bg="white", fg="#333").pack(anchor="w", pady=(10, 5))
    
    barcode_var = StringVar()
    barcode_entry = Entry(content, textvariable=barcode_var, font=("Helvetica", 12), width=30)
    barcode_entry.pack(anchor="w", pady=(0, 15))
    
    status_label = Label(content, text="Status: Enter barcode and check.", font=("Helvetica", 10), bg="white", fg="#6c757d")
    status_label.pack(anchor="w", pady=(5, 10))
    
    def confirm_replacement():
        """Confirm the replacement after checking"""
        barcode = barcode_var.get().strip()
        if not barcode:
            messagebox.showwarning("Missing Barcode", "Please enter a barcode!")
            return
        
        try:
            conn = get_db_connection()
            if conn is None:
                return
                
            cursor = conn.cursor()
            
            cursor.execute("SELECT id, name FROM equipment WHERE barcode = %s", (barcode,))
            result = cursor.fetchone()
            
            if not result:
                messagebox.showerror("Error", "Equipment not found in main inventory!")
                conn.close()
                return
            
            equipment_id = result['id']
            new_equipment_name = result['name']
            
            if original_equipment_name.split()[0] != new_equipment_name.split()[0]:
                if not messagebox.askyesno("Model Mismatch", 
                    f"Original was '{original_equipment_name}', new is '{new_equipment_name}'. Are you sure this is the correct replacement model?"):
                    conn.close()
                    return
            
            # UPDATE: Set the original equipment back to Available
            cursor.execute("""
                UPDATE equipment 
                SET availability_status = 'Available'
                WHERE barcode = %s
            """, (original_barcode,))
            
            # Update the report
            cursor.execute("""
                UPDATE equipment_issues 
                SET replacement_status = 'Verified',
                    replacement_equipment_id = %s,
                    status = 'Resolved',
                    resolved_date = %s
                WHERE issue_id = %s
            """, (equipment_id, datetime.today().date().isoformat(), report_id))
            
            conn.commit()
            conn.close()
            
             # ADD COMPLIANCE UPDATE HERE
            try:
                tracker = ComplianceTracker()
                success, status, data = tracker.update_user_compliance(reported_by_email)
                if success:
                    print(f"Compliance updated after replacement: {status}")
                else:
                    print(f"Failed to update compliance: {status}")
            except Exception as comp_error:
                print(f"Error updating compliance: {str(comp_error)}")
            
            messagebox.showinfo("Success", 
                                f"Replacement verified! Report #{report_id} has been resolved.\n\n"
                                f"New Equipment ID: {equipment_id}\n"
                                f"Original equipment is now back to Available status.")
            verify_window.destroy()
            show_equipment_reports_management(root, admin_email)
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to confirm replacement: {str(e)}")

    button_frame = Frame(content, bg="white")
    button_frame.pack(fill="x", pady=(15, 0))
    
    confirm_btn = Button(button_frame, text="Confirm Replacement", 
                         font=("Helvetica", 10, "bold"),
                         bg="#28a745", fg="white", relief="flat", padx=15, pady=6,
                         command=confirm_replacement)
    confirm_btn.pack(side="left", padx=(0, 10))
    
    Button(button_frame, text="Check Equipment", font=("Helvetica", 10),
           bg="#007bff", fg="white", relief="flat", padx=15, pady=6,
           command=check_equipment).pack(side="left", padx=5)
    
    Button(button_frame, text="Cancel", font=("Helvetica", 10),
           bg="#dc3545", fg="white", relief="flat", padx=15, pady=6,
           command=verify_window.destroy).pack(side="right")
    
    barcode_entry.focus_set()


def show_equipment_reports_management(root, admin_email):
    """Display equipment damage reports management interface with user management style"""
    for widget in root.winfo_children():
        widget.destroy()
    
    root.geometry("1920x1080")
    root.configure(bg="#f5f5f5")

    # Top header with same styling as return screen
    header_frame = tk.Frame(root, bg="#2c5530", height=80)
    header_frame.pack(fill="x")
    header_frame.pack_propagate(False)

    header_content = tk.Frame(header_frame, bg="#2c5530")
    header_content.pack(fill="both", expand=True, padx=20, pady=15)

    left_header = tk.Frame(header_content, bg="#2c5530")
    left_header.pack(side="left", fill="y")

    # Logo (same as return screen)
    try:
        logo_img = Image.open("ion_logo.png").resize((50, 50))
        logo_photo = ImageTk.PhotoImage(logo_img)
        logo_label = tk.Label(left_header, image=logo_photo, bg="#2c5530")
        logo_label.image = logo_photo
        logo_label.pack(side="left", padx=(0, 15))
    except:
        tk.Label(left_header, text="HOSPITAL", font=("Arial", 12, "bold"), 
            bg="white", fg="#2c5530", width=8, height=1).pack(side="left", padx=(0, 15))

    # Title
    tk.Label(left_header, text="Equipment Reports Management", 
        font=("Helvetica", 18, "bold"), bg="#2c5530", fg="white").pack(side="left")

    right_header = tk.Frame(header_content, bg="#2c5530")
    right_header.pack(side="right")

    # Back button (same styling as return screen)
    def back_to_dashboard():
        try:
            from admindashboard import show_admin_dashboard
            show_admin_dashboard(root, admin_email)
        except ImportError:
            messagebox.showerror("Error", "Admin dashboard module not found")
    
    tk.Button(right_header, text="Back", font=("Helvetica", 10),
        bg="white", fg="#2c5530", relief="flat", width=8,
        command=back_to_dashboard).pack(side="left", padx=(0, 10))

    # Admin info (same as return screen)
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

    # Search section with shadow - like user management
    shadow1 = tk.Frame(content_container, bg="#d0d0d0")
    shadow1.pack(fill="x", pady=(0, 25))
    
    search_section = tk.Frame(shadow1, bg="white", relief="flat")
    search_section.pack(fill="x", padx=2, pady=2)
    
    # Search header
    search_header = tk.Frame(search_section, bg="#e8f5e9", height=50)
    search_header.pack(fill="x")
    search_header.pack_propagate(False)
    
    tk.Label(search_header, text="Search Reports", font=("Arial", 13, "bold"),
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
        load_reports_into_table(search_term)
    
    search_btn = tk.Button(search_frame, text="Search", font=("Arial", 10, "bold"),
              bg="#2c5530", fg="white", relief="flat", cursor="hand2",
              padx=20, pady=6, command=perform_search)
    search_btn.pack(side="left", padx=5)
    
    clear_btn = tk.Button(search_frame, text="Clear", font=("Arial", 10, "bold"),
              bg="#999", fg="white", relief="flat", cursor="hand2",
              padx=20, pady=6,
              command=lambda: [search_var.set(""), load_reports_into_table("")])
    clear_btn.pack(side="left", padx=5)

    # Action buttons frame
    action_frame = tk.Frame(search_content, bg="white")
    action_frame.pack(fill="x", pady=(15, 0))
    
    def refresh_reports():
        load_reports_into_table("")
    
    refresh_btn = tk.Button(action_frame, text="🔄 Refresh", font=("Arial", 10, "bold"),
              bg="#007bff", fg="white", relief="flat", cursor="hand2",
              padx=20, pady=6, command=refresh_reports)
    refresh_btn.pack(side="left", padx=5)

    # PDF Export button - EXACTLY LIKE EQUIPMENT MANAGEMENT
    def generate_reports_pdf():
        """Generate a PDF report of equipment damage reports"""
        try:
            conn = get_db_connection()
            if conn is None:
                return
                
            cursor = conn.cursor()
            
            # Get search term for filtering
            search_term = search_var.get().strip()
            
            # Base query for reports
            query = """
                SELECT 
                    ei.issue_id, ei.equipment_name, ei.barcode, ei.issue_type, ei.priority,
                    ei.reported_by_name, ei.reported_date, ei.status,
                    ei.replacement_status, ei.replacement_deadline, ei.reported_by_email
                FROM equipment_issues ei
                WHERE 1=1
            """
            params = []
            
            # Add search filter if any
            if search_term:
                query += " AND (LOWER(ei.equipment_name) LIKE %s OR LOWER(ei.barcode) LIKE %s OR LOWER(ei.reported_by_name) LIKE %s OR LOWER(ei.issue_type) LIKE %s)"
                search_pattern = f"%{search_term}%"
                params.extend([search_pattern, search_pattern, search_pattern, search_pattern])
            
            query += " ORDER BY ei.reported_date DESC"
            
            cursor.execute(query, params)
            reports_list = cursor.fetchall()
            conn.close()

            if not reports_list:
                messagebox.showinfo("Info", "No equipment reports found to generate report.")
                return
            
            # Ask for save location
            output_file = filedialog.asksaveasfilename(
                defaultextension=".pdf",
                filetypes=[("PDF files", "*.pdf")],
                title="Save Equipment Reports Report As"
            )
            
            if not output_file:
                return
            
            # Create PDF in LANDSCAPE mode
            from reportlab.lib.pagesizes import landscape, letter
            c = canvas.Canvas(output_file, pagesize=landscape(letter))
            width, height = landscape(letter)
            
            # Title and header
            c.setFont("Helvetica-Bold", 14)
            c.drawString(40, height - 40, "Equipment Damage Reports")
            c.setFont("Helvetica", 9)
            c.drawString(40, height - 55, f"Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            c.drawString(40, height - 70, f"Total Reports: {len(reports_list)}")
            
            if search_term:
                c.drawString(40, height - 85, f"Search Filter: {search_term}")
            
            # Table setup - COMPACT COLUMNS
            headers = ["ID", "Equipment", "Barcode", "Issue Type", "Priority", "Reported By", "Date", "Status", "Replacement"]
            col_widths = [50, 120, 80, 80, 50, 100, 80, 70, 80]  # Compact columns
            x_positions = [40]
            for i in range(1, len(col_widths)):
                x_positions.append(x_positions[i-1] + col_widths[i-1])
            
            y_position = height - 100
            
            # Table headers - SMALLER FONT
            c.setFont("Helvetica-Bold", 7)
            for i, header in enumerate(headers):
                c.drawString(x_positions[i], y_position, header)
            
            # Draw line under headers
            c.line(40, y_position - 3, sum(col_widths) + 40, y_position - 3)
            
            # Table data - SMALLER FONT
            c.setFont("Helvetica", 6)
            y_position -= 15
            
            for report in reports_list:
                issue_id = report['issue_id']
                equipment_name = report['equipment_name']
                barcode = report['barcode']
                issue_type = report['issue_type']
                priority = report['priority']
                reported_by = report['reported_by_name']
                reported_date = report['reported_date']
                status = report['status']
                replacement_status = report['replacement_status']
                replacement_deadline = report['replacement_deadline']
                reported_by_email = report['reported_by_email']
                
                # Prepare display values
                display_equipment = equipment_name
                if len(display_equipment) > 20:
                    display_equipment = display_equipment[:17] + "..."
                
                display_reporter = reported_by
                if len(display_reporter) > 15:
                    display_reporter = display_reporter[:12] + "..."
                
                # Date formatting
                date_text = reported_date[:10] if reported_date else "N/A"
                
                # Replacement status display
                if replacement_status == "Verified":
                    repl_text = "Verified"
                elif replacement_status == "Purchased":
                    repl_text = "Purchased"
                elif replacement_status == "Closed":
                    repl_text = "Closed"
                else:
                    repl_text = "Required"
                
                row_data = [
                    str(issue_id),
                    display_equipment,
                    barcode or "N/A",
                    issue_type or "N/A",
                    priority or "Medium",
                    display_reporter,
                    date_text,
                    status or "Pending",
                    repl_text
                ]
                
                # Check if we need a new page
                if y_position < 40:
                    c.showPage()
                    c.setPageSize(landscape(letter))
                    y_position = height - 40
                    
                    # Page header for continuation
                    c.setFont("Helvetica-Bold", 9)
                    c.drawString(40, height - 25, "Equipment Damage Reports (Continued)")
                    
                    # Redraw headers on new page
                    c.setFont("Helvetica-Bold", 7)
                    for i, header in enumerate(headers):
                        c.drawString(x_positions[i], y_position, header)
                    c.line(40, y_position - 3, sum(col_widths) + 40, y_position - 3)
                    y_position -= 15
                    c.setFont("Helvetica", 6)
                
                # Draw row
                for i, data in enumerate(row_data):
                    c.drawString(x_positions[i], y_position, str(data))
                
                y_position -= 12  # Tighter row spacing
            
            # Summary page
            c.showPage()
            c.setPageSize(landscape(letter))
            c.setFont("Helvetica-Bold", 14)
            c.drawString(40, height - 40, "Equipment Reports Summary")
            
            c.setFont("Helvetica", 9)
            y_pos = height - 65
            
            # Basic counts
            c.drawString(40, y_pos, f"Total Reports: {len(reports_list)}")
            y_pos -= 20
            
            # Count by status
            status_count = {}
            priority_count = {}
            issue_type_count = {}
            
            for report in reports_list:
                status = report['status'] or "Pending"
                priority = report['priority'] or "Medium"
                issue_type = report['issue_type'] or "Unknown"
                
                status_count[status] = status_count.get(status, 0) + 1
                priority_count[priority] = priority_count.get(priority, 0) + 1
                issue_type_count[issue_type] = issue_type_count.get(issue_type, 0) + 1
            
            # Two column layout
            c.drawString(40, y_pos, "Reports by Status:")
            y_pos -= 15
            
            col1_x = 50
            col2_x = width / 2 + 20
            current_col = col1_x
            
            for i, (status, count) in enumerate(status_count.items()):
                if i == 6:  # Switch to second column after 6 items
                    current_col = col2_x
                    y_pos = height - 80
                
                c.drawString(current_col, y_pos, f"• {status}: {count}")
                y_pos -= 12
            
            # Priority section
            y_pos = min(y_pos, height - 80)
            y_pos -= 15
            
            c.drawString(40, y_pos, "Reports by Priority:")
            y_pos -= 15
            
            current_col = col1_x
            for i, (priority, count) in enumerate(priority_count.items()):
                if i == 6:
                    current_col = col2_x
                    y_pos = height - 110
                
                c.drawString(current_col, y_pos, f"• {priority}: {count}")
                y_pos -= 12
            
            # Issue type section
            y_pos = min(y_pos, height - 110)
            y_pos -= 15
            
            c.drawString(40, y_pos, "Reports by Issue Type:")
            y_pos -= 15
            
            current_col = col1_x
            for i, (issue_type, count) in enumerate(issue_type_count.items()):
                if i == 6:
                    current_col = col2_x
                    y_pos = height - 140
                
                c.drawString(current_col, y_pos, f"• {issue_type}: {count}")
                y_pos -= 12
            
            # Replacement status summary
            replacement_stats = {}
            for report in reports_list:
                repl_status = report['replacement_status'] or "Required"
                replacement_stats[repl_status] = replacement_stats.get(repl_status, 0) + 1
            
            y_pos = min(y_pos, height - 140)
            y_pos -= 20
            
            c.drawString(40, y_pos, "Replacement Status:")
            y_pos -= 15
            
            current_col = col1_x
            for i, (repl_status, count) in enumerate(replacement_stats.items()):
                if i == 6:
                    current_col = col2_x
                    y_pos = height - 160
                
                c.drawString(current_col, y_pos, f"• {repl_status}: {count}")
                y_pos -= 12
            
            # Footer
            c.setFont("Helvetica", 7)
            c.setFillColorRGB(0.5, 0.5, 0.5)
            c.drawString(40, 25, f"KLD Institute of Nursing - Equipment Reports Management System")
            c.drawString(width - 150, 25, f"Page 1")
            
            c.save()
            messagebox.showinfo("Success", f"PDF report generated successfully!\n\nSaved to: {output_file}")
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to generate PDF report: {str(e)}")
    
    # Add PDF export button to action frame - EXACTLY LIKE EQUIPMENT MANAGEMENT
    pdf_btn = tk.Button(action_frame, text="📄 Print Report", font=("Arial", 10, "bold"),
              bg="#6f42c1", fg="white", relief="flat", cursor="hand2",
              padx=20, pady=6, command=generate_reports_pdf)
    pdf_btn.pack(side="left", padx=5)

    # Table section with shadow - exactly like user management
    shadow2 = tk.Frame(content_container, bg="#d0d0d0")
    shadow2.pack(fill="both", expand=True)
    
    table_section = tk.Frame(shadow2, bg="white", relief="flat")
    table_section.pack(fill="both", expand=True, padx=2, pady=2)
    
    # Table header
    table_header = tk.Frame(table_section, bg="#e3f2fd", height=50)
    table_header.pack(fill="x")
    table_header.pack_propagate(False)
    
    tk.Label(table_header, text="Equipment Damage Reports", font=("Arial", 13, "bold"),
             bg="#e3f2fd", fg="#2c5530").pack(side="left", padx=30, pady=15)
    
    # Count label in header
    count_label = tk.Label(table_header, text="Total: 0", font=("Arial", 11),
                          bg="#e3f2fd", fg="#2c5530")
    count_label.pack(side="right", padx=30)

    # Table frame with scrollbar - exactly like user management
    table_frame = tk.Frame(table_section, bg="white")
    table_frame.pack(fill="both", expand=True, padx=20, pady=20)

    # Scrollbars
    vsb = ttk.Scrollbar(table_frame, orient="vertical")
    vsb.pack(side="right", fill="y")
    
    hsb = ttk.Scrollbar(table_frame, orient="horizontal")
    hsb.pack(side="bottom", fill="x")

    # Table columns - equipment reports specific fields
    columns = ("ID", "EQUIPMENT", "BARCODE", "ISSUE TYPE", "PRIORITY", "REPORTED BY", "DATE", "STATUS", "REPLACEMENT", "DETAILS", "SEND NOTICE", "VERIFY")
    
    tree = ttk.Treeview(table_frame, columns=columns, show="headings", height=15,
                       yscrollcommand=vsb.set, xscrollcommand=hsb.set)
    tree.pack(fill="both", expand=True)
    
    vsb.config(command=tree.yview)
    hsb.config(command=tree.xview)

    # Configure columns
    column_widths = {
        "ID": 60,
        "EQUIPMENT": 180,
        "BARCODE": 100,
        "ISSUE TYPE": 120,
        "PRIORITY": 80,
        "REPORTED BY": 150,
        "DATE": 100,
        "STATUS": 100,
        "REPLACEMENT": 100,
        "DETAILS": 80,
        "SEND NOTICE": 100,
        "VERIFY": 80
    }
    
    for col in columns:
        tree.heading(col, text=col)
        tree.column(col, width=column_widths.get(col, 100), anchor="center")

    # Enhanced style for table matching user management
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
    tree.tag_configure('resolved', background='#e8f5e8')
    tree.tag_configure('high_priority', background='#ffe6e6')

    def load_reports_into_table(search_term=""):
        """Load equipment reports data into the table with search"""
        # Clear existing items
        for item in tree.get_children():
            tree.delete(item)
        
        try:
            conn = get_db_connection()
            if conn is None:
                return
                
            cursor = conn.cursor()
            
            # Base query
            query = """
                SELECT 
                    ei.issue_id, ei.equipment_name, ei.barcode, ei.issue_type, ei.priority,
                    ei.reported_by_name, ei.reported_date, ei.status,
                    ei.replacement_required, ei.replacement_status, ei.replacement_deadline,
                    ei.reported_by_email, ei.violation_sent
                FROM equipment_issues ei
                WHERE 1=1
            """
            params = []
            
            # Add search filter
            if search_term:
                query += " AND (LOWER(ei.equipment_name) LIKE %s OR LOWER(ei.barcode) LIKE %s OR LOWER(ei.reported_by_name) LIKE %s OR LOWER(ei.issue_type) LIKE %s)"
                search_pattern = f"%{search_term}%"
                params.extend([search_pattern, search_pattern, search_pattern, search_pattern])
            
            query += " ORDER BY ei.reported_date DESC"
            
            cursor.execute(query, params)
            reports_list = cursor.fetchall()
            conn.close()

            # Insert into table
            for idx, report in enumerate(reports_list):
                issue_id = report['issue_id']
                equipment_name = report['equipment_name']
                barcode = report['barcode']
                issue_type = report['issue_type']
                priority = report['priority']
                reported_by = report['reported_by_name']
                reported_date = report['reported_date']
                status = report['status']
                replacement_required = report['replacement_required']
                replacement_status = report['replacement_status']
                replacement_deadline = report['replacement_deadline']
                reported_by_email = report['reported_by_email']
                violation_sent = report['violation_sent']
                
                # Determine row tag based on status and priority
                tag = 'evenrow' if idx % 2 == 0 else 'oddrow'
                if status == "Resolved":
                    tag = 'resolved'
                elif priority == "High":
                    tag = 'high_priority'
                
                # Date formatting
                date_text = reported_date[:10] if reported_date else "N/A"
                
                # Replacement status display
                if replacement_status == "Verified":
                    repl_text = "Verified"
                elif replacement_status == "Purchased":
                    repl_text = "Purchased"
                elif replacement_status == "Closed":
                    repl_text = "Closed"
                else:
                    repl_text = "Required"
                
                row_values = (
                    issue_id,
                    equipment_name or "N/A",
                    barcode or "N/A",
                    issue_type or "N/A",
                    priority or "Medium",
                    reported_by or "N/A",
                    date_text,
                    status or "Pending",
                    repl_text,
                    "📋 Details",
                    "📧 Send Notice" if violation_sent == 0 else "✓ Sent",
                    "✅ Verify" if (replacement_status == "Pending" or replacement_status is None) else "✓ Done"
                )
                
                tree.insert("", "end", values=row_values, tags=(tag,))

            # Update count
            count_label.config(text=f"Total: {len(reports_list)}")

        except Exception as e:
            error_msg = f"Database error: {str(e)}"
            print(error_msg)
            tree.insert("", "end", values=("Error", "Loading reports", error_msg[:50], "", "", "", "", "", "", "", "", ""))

    # Context menu for actions
    context_menu = tk.Menu(tree, tearoff=0)
    context_menu.add_command(label="View Details", command=lambda: view_selected_report())
    context_menu.add_command(label="Send Notice", command=lambda: send_notice_selected())
    context_menu.add_command(label="Verify Replacement", command=lambda: verify_selected())
    context_menu.add_separator()
    context_menu.add_command(label="Export to PDF", command=generate_reports_pdf)  # Added PDF export to context menu
    
    def show_context_menu(event):
        item = tree.identify_row(event.y)
        if item:
            tree.selection_set(item)
            context_menu.post(event.x_root, event.y_root)
    
    tree.bind("<Button-3>", show_context_menu)  # Right-click
    
    def view_selected_report():
        selection = tree.selection()
        if not selection:
            messagebox.showwarning("Warning", "Please select a report to view details")
            return
        
        try:
            item = tree.item(selection[0])
            report_id = item['values'][0]  # ID is in first column
            view_report_details(report_id, root, admin_email)  # Added admin_email parameter
        except Exception as e:
            messagebox.showerror("Error", f"Failed to view report details: {str(e)}")
    
    def send_notice_selected():
        selection = tree.selection()
        if not selection:
            messagebox.showwarning("Warning", "Please select a report to send notice")
            return
        
        try:
            item = tree.item(selection[0])
            report_id = item['values'][0]
            # Get the actual data from database
            report_data = get_report_data(report_id)
            if report_data:
                if report_data['violation_sent'] == 1:
                    messagebox.showinfo("Already Sent", "Violation notice has already been sent for this report.")
                    return
                
                send_violation_notice(report_id, report_data['reported_by_email'], report_data['equipment_name'], report_data['barcode'], root, admin_email)
        except Exception as e:
            messagebox.showerror("Error", f"Failed to send notice: {str(e)}")
    
    def verify_selected():
        selection = tree.selection()
        if not selection:
            messagebox.showwarning("Warning", "Please select a report to verify replacement")
            return
        
        try:
            item = tree.item(selection[0])
            report_id = item['values'][0]
            # Get the actual data from database
            report_data = get_report_data(report_id)
            if report_data:
                if report_data['replacement_status'] == "Verified":
                    messagebox.showinfo("Already Verified", "Replacement has already been verified for this report.")
                    return
                
                verify_replacement(report_id, root, admin_email)
        except Exception as e:
            messagebox.showerror("Error", f"Failed to verify replacement: {str(e)}")
    
    def get_report_data(report_id):
        """Get complete report data from database"""
        try:
            conn = get_db_connection()
            if conn is None:
                return None
                
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT 
                    ei.issue_id, ei.equipment_name, ei.barcode, ei.issue_type, ei.priority,
                    ei.reported_by_name, ei.reported_date, ei.status,
                    ei.replacement_required, ei.replacement_status, ei.replacement_deadline,
                    ei.reported_by_email, ei.violation_sent
                FROM equipment_issues ei
                WHERE ei.issue_id = %s
            """, (report_id,))
            report_data = cursor.fetchone()
            conn.close()
            return report_data
        except Exception as e:
            messagebox.showerror("Error", f"Failed to get report data: {str(e)}")
            return None
    
    # Click function for action columns
    def on_tree_click(event):
        item = tree.identify_row(event.y)
        column = tree.identify_column(event.x)
        
        if item and column:
            col_name = tree.heading(column)["text"]
            if col_name == "DETAILS":
                view_selected_report()
            elif col_name == "SEND NOTICE":
                send_notice_selected()
            elif col_name == "VERIFY":
                verify_selected()

    tree.bind("<Button-1>", on_tree_click)
    
    # Double-click to view details
    tree.bind("<Double-1>", lambda e: view_selected_report())
    
    # Load initial data
    load_reports_into_table()
    
    # Bind search on Enter key
    search_entry.bind("<Return>", lambda e: perform_search())

def send_violation_notice(report_id, faculty_email, equipment_name, equipment_barcode, parent, admin_email):
    """Send violation notice to faculty member and update equipment status"""
    try:
        conn = get_db_connection()
        if conn is None:
            return
            
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT violation_sent, replacement_deadline, reported_by_name 
            FROM equipment_issues 
            WHERE issue_id = %s
        """, (report_id,))
        
        result = cursor.fetchone()
        
        if not result:
            messagebox.showerror("Error", "Report not found!")
            conn.close()
            return
        
        violation_sent = result['violation_sent']
        deadline = result['replacement_deadline']
        faculty_name = result['reported_by_name']
        
        if violation_sent == 1:
            messagebox.showinfo("Already Sent", 
                                 "Violation notice has already been sent for this report.")
            conn.close()
            return
        
        deadline_text = deadline if deadline else "within 7 working days"
        
        message = (
            f"EQUIPMENT REPLACEMENT VIOLATION NOTICE\n\n"
            f"Equipment: {equipment_name}\n"
            f"Report ID: #{report_id}\n\n"
            f"You are required to replace the damaged equipment with the SAME MODEL "
            f"by {deadline_text}.\n\n"
            f"Please coordinate with the Equipment Custodian immediately to:\n"
            f"1. Purchase the exact same model of equipment\n"
            f"2. Submit the replacement for verification\n"
            f"3. Provide proof of purchase\n\n"
            f"Failure to comply may result in disciplinary action and salary deductions.\n\n"
            f"For questions, contact the Equipment Office."
        )
        
        # Create notification using NotificationManager
        notif_manager = NotificationManager()
        
        notification_id = notif_manager.create_notification(
            recipient_email=faculty_email,
            message=message,
            notification_type="violation_notice",
            related_id=report_id
        )
        
        print(f"Notification created with ID: {notification_id}")
        
        # Send email notification
        try:
            send_violation_email(faculty_email, faculty_name, equipment_name, deadline_text, report_id)
            email_status = "Email sent successfully"
        except Exception as email_error:
            print(f"Email sending failed: {email_error}")
            email_status = "Email sending failed (notification saved)"
        
        # UPDATE: Set equipment status to Unavailable
        cursor.execute("""
            UPDATE equipment 
            SET availability_status = 'Unavailable'
            WHERE barcode = %s
        """, (equipment_barcode,))
        
        # Mark violation as sent and change status to In Progress
        cursor.execute("""
            UPDATE equipment_issues 
            SET violation_sent = 1, 
                status = 'In Progress'
            WHERE issue_id = %s
        """, (report_id,))
        
        conn.commit()
        conn.close()
        
        # ADD COMPLIANCE UPDATE HERE
        try:
            tracker = ComplianceTracker()
            success, status, data = tracker.update_user_compliance(faculty_email)
            if success:
                print(f"Compliance updated for {faculty_email}: {status}")
            else:
                print(f"Failed to update compliance: {status}")
        except Exception as comp_error:
            print(f"Error updating compliance: {str(comp_error)}")
        
        messagebox.showinfo("Success", 
                              f"Violation notice sent to {faculty_email}!\n\n"
                              f"Notification ID: {notification_id}\n"
                              f"{email_status}\n\n"
                              f"Equipment status updated to 'Unavailable'\n"
                              f"The faculty member has been notified about the equipment replacement requirement.")
        
        # Reload reports
        show_equipment_reports_management(parent, admin_email)
        
    except Exception as e:
        print(f"Error in send_violation_notice: {e}")
        traceback.print_exc()
        messagebox.showerror("Error", f"Failed to send violation notice: {str(e)}")

def send_violation_email(recipient_email, recipient_name, equipment_name, deadline, report_id):
    """Send violation notice via email"""
    import smtplib
    from email.mime.text import MIMEText
    from email.mime.multipart import MIMEMultipart
    
    try:
        from email_config import SENDER_EMAIL, SENDER_PASSWORD, SMTP_SERVER, SMTP_PORT, SYSTEM_NAME, SYSTEM_EMAIL_SIGNATURE
    except ImportError:
        print("email_config.py not found. Email sending disabled.")
        raise Exception("Email configuration not found or invalid.")
    
    msg = MIMEMultipart('alternative')
    msg['Subject'] = f"VIOLATION NOTICE - Equipment Replacement Required (Report #{report_id})"
    msg['From'] = SENDER_EMAIL
    msg['To'] = recipient_email
    
    html = f"""
    <html>
      <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
        <div style="max-width: 600px; margin: 0 auto; padding: 20px; border: 2px solid #dc3545; border-radius: 10px;">
          <div style="background-color: #dc3545; color: white; padding: 15px; border-radius: 5px; text-align: center;">
            <h2 style="margin: 0;">EQUIPMENT REPLACEMENT VIOLATION NOTICE</h2>
          </div>
          
          <div style="padding: 20px; background-color: #fff3cd; margin: 20px 0; border-left: 4px solid #ff6b6b;">
            <p><strong>Dear {recipient_name},</strong></p>
            <p>This is an official notice regarding damaged equipment under your responsibility.</p>
          </div>
          
          <div style="padding: 20px; background-color: #f8f9fa; border-radius: 5px;">
            <h3 style="color: #dc3545; margin-top: 0;">Report Details:</h3>
            <table style="width: 100%; border-collapse: collapse;">
              <tr>
                <td style="padding: 8px; border-bottom: 1px solid #ddd;"><strong>Report ID:</strong></td>
                <td style="padding: 8px; border-bottom: 1px solid #ddd;">#{report_id}</td>
              </tr>
              <tr>
                <td style="padding: 8px; border-bottom: 1px solid #ddd;"><strong>Equipment:</strong></td>
                <td style="padding: 8px; border-bottom: 1px solid #ddd;">{equipment_name}</td>
              </tr>
              <tr>
                <td style="padding: 8px; border-bottom: 1px solid #ddd;"><strong>Deadline:</strong></td>
                <td style="padding: 8px; border-bottom: 1px solid #ddd; color: #dc3545; font-weight: bold;">{deadline}</td>
              </tr>
            </table>
          </div>
          
          <div style="padding: 20px;">
            <h3 style="color: #dc3545;">Required Actions:</h3>
            <ol style="line-height: 2;">
              <li><strong>Purchase</strong> the exact same model of the damaged equipment</li>
              <li><strong>Coordinate</strong> with the Equipment Custodian for verification</li>
              <li><strong>Submit</strong> proof of purchase and the replacement equipment</li>
              <li><strong>Complete</strong> all requirements by <span style="color: #dc3545; font-weight: bold;">{deadline}</span></li>
            </ol>
          </div>
          
          <div style="padding: 15px; background-color: #fff3cd; border-left: 4px solid #ffc107; margin: 20px 0;">
            <p style="margin: 0; font-weight: bold; color: #856404;">
              Important: You must provide the SAME MODEL of equipment. Different models will not be accepted.
            </p>
          </div>
          
          <div style="padding: 20px; background-color: #f8d7da; border-left: 4px solid #dc3545; margin: 20px 0;">
            <p style="margin: 0; color: #721c24; font-weight: bold;">
              Failure to comply may result in:
            </p>
            <ul style="color: #721c24; margin: 10px 0;">
              <li>Suspension of equipment borrowing privileges</li>
            </ul>
          </div>
          
          <div style="padding: 20px; text-align: center; color: #666;">
            <p>For questions or assistance, please contact the Equipment Custodian.</p>
            <p style="font-size: 12px; margin-top: 20px;">
              This is an automated message from the {SYSTEM_NAME}.
            </p>
          </div>
        </div>
      </body>
    </html>
    """
    
    text = f"""
    EQUIPMENT REPLACEMENT VIOLATION NOTICE
    
    Dear {recipient_name},
    
    This is an official notice regarding damaged equipment under your responsibility.
    
    Report Details:
    - Report ID: #{report_id}
    - Equipment: {equipment_name}
    - Deadline: {deadline}
    
    Required Actions:
    1. Purchase the exact same model of the damaged equipment
    2. Coordinate with the Equipment Custodian for verification
    3. Submit proof of purchase and the replacement equipment
    4. Complete all requirements by {deadline}
    
    IMPORTANT: You must provide the SAME MODEL of equipment. Different models will not be accepted.
    
    Failure to comply may result in disciplinary action, salary deductions, and suspension of equipment borrowing privileges.
    
    For questions or assistance, please contact the Equipment Custodian Office.
    
    {SYSTEM_EMAIL_SIGNATURE}
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
        print(f"Email sent successfully to {recipient_email}")
    except Exception as e:
        print(f"Failed to send email: {e}")
        raise

def view_report_details(report_id, parent, admin_email):
    """View detailed information about a report"""
    try:
        conn = get_db_connection()
        if conn is None:
            return
            
        cursor = conn.cursor()
        cursor.execute("""
            SELECT * FROM equipment_issues WHERE issue_id = %s
        """, (report_id,))
        report = cursor.fetchone()
        conn.close()
        
        if not report:
            messagebox.showerror("Error", "Report not found!")
            return
        
        # Create detailed view window
        detail_window = Toplevel()
        detail_window.title(f"Report Details - #{report_id}")
        detail_window.geometry("700x650")
        detail_window.configure(bg="white")
        
        # Header
        header = Frame(detail_window, bg="#007bff", height=60)
        header.pack(fill="x")
        header.pack_propagate(False)
        
        Label(header, text=f"Equipment Damage Report #{report_id}", 
              font=("Helvetica", 16, "bold"), bg="#007bff", fg="white").pack(pady=15)
        
        # Content with scrollbar
        content_frame = Frame(detail_window, bg="white")
        content_frame.pack(fill="both", expand=True)
        
        canvas = tk.Canvas(content_frame, bg="white", highlightthickness=0)
        scrollbar = ttk.Scrollbar(content_frame, orient="vertical", command=canvas.yview)
        content = Frame(canvas, bg="white")
        
        content.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.create_window((0, 0), window=content, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        canvas.pack(side="left", fill="both", expand=True, padx=20, pady=20)
        scrollbar.pack(side="right", fill="y")
        
        # Report details
        details = [
            ("Report ID:", report['issue_id']),
            ("Equipment Barcode:", report['barcode']),
            ("Equipment Name:", report['equipment_name']),
            ("Issue Type:", report['issue_type']),
            ("Priority:", report['priority']),
            ("Status:", report['status']),
            ("Reported Date:", report['reported_date']),
            ("Resolved Date:", report['resolved_date'] if report['resolved_date'] else "Not resolved"),
            ("Reported By:", f"{report['reported_by_name']} ({report['reported_by_email']})")
        ]
        
        for i, (label, value) in enumerate(details):
            Label(content, text=label, font=("Helvetica", 11, "bold"), 
                  bg="white", fg="#333", anchor="w").grid(row=i, column=0, sticky="w", padx=10, pady=8)
            Label(content, text=value, font=("Helvetica", 11), 
                  bg="white", fg="#666", anchor="w").grid(row=i, column=1, sticky="w", padx=10, pady=8)
        
        # Description
        row_num = len(details)
        Label(content, text="Description:", font=("Helvetica", 11, "bold"), 
              bg="white", fg="#333", anchor="w").grid(row=row_num, column=0, sticky="nw", padx=10, pady=8)
        
        desc_text = Text(content, font=("Helvetica", 10), bg="#f8f9fa", 
                         relief="solid", borderwidth=1, height=4, width=40, wrap="word")
        desc_text.insert("1.0", report['description'] if report['description'] else "No description")
        desc_text.config(state="disabled")
        desc_text.grid(row=row_num, column=1, sticky="w", padx=10, pady=8)
        
        # Replacement Information Section
        row_num = len(details)
        
        # Separator
        separator = Frame(content, bg="#dee2e6", height=2)
        separator.grid(row=row_num, column=0, columnspan=2, sticky="ew", padx=10, pady=20)
        row_num += 1
        
        # Replacement header
        Label(content, text="REPLACEMENT REQUIREMENT", 
              font=("Helvetica", 12, "bold"), bg="white", fg="#dc3545").grid(
                      row=row_num, column=0, columnspan=2, sticky="w", padx=10, pady=10)
        row_num += 1
        
        replacement_details = [
            ("Replacement Status:", report['replacement_status'] if report['replacement_status'] else "Pending"),
            ("Deadline:", report['replacement_deadline'] if report['replacement_deadline'] else "Not set"),
            ("Estimated Cost:", f"P{report['estimated_cost']}" if report['estimated_cost'] else "Not specified"),
            ("Replacement Equipment ID:", report['replacement_equipment_id'] if report['replacement_equipment_id'] else "Not yet replaced")
        ]
        
        for label, value in replacement_details:
            Label(content, text=label, font=("Helvetica", 11, "bold"), 
                  bg="white", fg="#333", anchor="w").grid(row=row_num, column=0, sticky="w", padx=10, pady=8)
            
            # Color code the status
            if label == "Replacement Status:":
                if value == "Verified":
                    fg_color = "#28a745"
                elif value == "Purchased":
                    fg_color = "#17a2b8"
                elif value == "Pending":
                    fg_color = "#dc3545"
                else:
                    fg_color = "#666"
            else:
                fg_color = "#666"
            
            Label(content, text=value, font=("Helvetica", 11, "bold" if label == "Replacement Status:" else "normal"), 
                  bg="white", fg=fg_color, anchor="w").grid(row=row_num, column=1, sticky="w", padx=10, pady=8)
            row_num += 1
        
        # Notice box - always show for pending replacements
        if not report['replacement_status'] or report['replacement_status'] == "Pending":
            notice_frame = Frame(content, bg="#fff3cd", relief="solid", borderwidth=1)
            notice_frame.grid(row=row_num, column=0, columnspan=2, sticky="ew", padx=10, pady=15)
            
            Label(notice_frame, text="REPLACEMENT REQUIRED", 
                  font=("Helvetica", 11, "bold"), bg="#fff3cd", fg="#856404").pack(pady=5)
            Label(notice_frame, 
                  text="Faculty must provide the SAME MODEL of equipment\nas a replacement for the damaged item.", 
                  font=("Helvetica", 10), bg="#fff3cd", fg="#856404", justify="center").pack(pady=5)
        
        content.grid_columnconfigure(1, weight=1)
        
        # Action buttons at bottom
        button_frame = Frame(detail_window, bg="white")
        button_frame.pack(fill="x", padx=20, pady=15)
        
        # Show verify replacement button for pending replacements
        if not report['replacement_status'] or report['replacement_status'] == "Pending":
            Button(button_frame, text="Verify Replacement", 
                   font=("Helvetica", 11, "bold"),
                   bg="#28a745", fg="white", relief="flat", padx=20, pady=8,
                   command=lambda: [detail_window.destroy(), verify_replacement(report_id, parent, admin_email)]).pack(side="left", padx=5)
        
        Button(button_frame, text="Close", font=("Helvetica", 11),
               bg="#6c757d", fg="white", relief="flat", padx=20, pady=8,
               command=detail_window.destroy).pack(side="right", padx=5)
            
    except Exception as e:
        messagebox.showerror("Error", f"Failed to load report details: {str(e)}")

if __name__ == "__main__":
    root = tk.Tk()
    root.title("Equipment Reports Management")
    root.geometry("1000x700") 
    
    show_equipment_reports_management(root, "admin@nursing.com")
    root.mainloop()