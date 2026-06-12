# compliance_tracker.py - Enhanced Compliance Tracking with Equipment Issues Integration
import pymysql  # Changed from sqlite3 to pymysql
from datetime import datetime, timedelta
import tkinter as tk
from tkinter import ttk, Frame, Label, Button, messagebox, Toplevel

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
class ComplianceTracker:
    def __init__(self):
        # No db_path needed for MySQL
        pass
    
    def get_overdue_replacements(self, borrower_email=None):
        """Get all overdue replacements (past deadline and not replaced)"""
        conn = get_db_connection()
        if conn is None:
            return []
            
        cursor = conn.cursor()
        
        query = """
            SELECT 
                ei.issue_id,
                ei.equipment_name,
                ei.barcode,
                ei.reported_by_email,
                ei.reported_by_name,
                ei.reported_date,
                ei.replacement_deadline,
                ei.replacement_status,
                ei.description,
                DATEDIFF(NOW(), ei.replacement_deadline) as days_overdue
            FROM equipment_issues ei
            WHERE ei.replacement_required = 1 
            AND (ei.replacement_status = 'Pending' OR ei.replacement_status IS NULL)
            AND ei.replacement_deadline < NOW()
        """  # CHANGED: julianday to DATEDIFF for MySQL
        
        if borrower_email:
            query += " AND ei.reported_by_email = %s"
            cursor.execute(query, (borrower_email,))
        else:
            cursor.execute(query)
        
        results = cursor.fetchall()
        conn.close()
        
        return results
    
    def get_pending_replacements(self, borrower_email=None):
        """Get pending replacements within deadline"""
        conn = get_db_connection()
        if conn is None:
            return []
            
        cursor = conn.cursor()
        
        query = """
            SELECT 
                ei.issue_id,
                ei.equipment_name,
                ei.barcode,
                ei.reported_by_email,
                ei.reported_by_name,
                ei.reported_date,
                ei.replacement_deadline,
                ei.replacement_status,
                ei.description,
                DATEDIFF(ei.replacement_deadline, NOW()) as days_remaining
            FROM equipment_issues ei
            WHERE ei.replacement_required = 1 
            AND (ei.replacement_status = 'Pending' OR ei.replacement_status IS NULL)
            AND ei.replacement_deadline >= NOW()
        """  # CHANGED: julianday to DATEDIFF for MySQL
        
        if borrower_email:
            query += " AND ei.reported_by_email = %s"
            cursor.execute(query, (borrower_email,))
        else:
            cursor.execute(query)
        
        results = cursor.fetchall()
        conn.close()
        
        return results
    
    def get_user_damage_history(self, borrower_email):
        """Get complete damage history for a user"""
        conn = get_db_connection()
        if conn is None:
            return []
            
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT 
                ei.issue_id,
                ei.equipment_name,
                ei.barcode,
                ei.reported_date,
                ei.replacement_deadline,
                ei.replacement_status,
                ei.resolved_date,
                ei.description,
                ei.status,
                ei.priority,
                ei.estimated_cost,
                CASE 
                    WHEN ei.replacement_status = 'Verified' THEN 'Replaced'
                    WHEN ei.replacement_status = 'Purchased' THEN 'Purchased'
                    WHEN ei.replacement_status = 'Closed' THEN 'Closed'
                    WHEN ei.replacement_deadline < NOW() THEN 'Overdue'
                    ELSE 'Pending'
                END as compliance_status
            FROM equipment_issues ei
            WHERE ei.reported_by_email = %s
            AND ei.replacement_required = 1
            ORDER BY ei.reported_date DESC
        """, (borrower_email,))  # CHANGED: ? to %s
        
        results = cursor.fetchall()
        conn.close()
        
        return results
    
    def calculate_compliance_score(self, borrower_email):
        """
        Calculate compliance score based on:
        - Overdue replacements (major penalty)
        - Pending replacements within deadline (minor penalty)
        - Total damage history
        - Return compliance (from existing borrow system)
        """
        conn = get_db_connection()
        if conn is None:
            return {
                'score': 0,
                'overdue_replacements': 0,
                'pending_replacements': 0,
                'total_damages': 0,
                'unresolved_issues': 0,
                'total_borrows': 0,
                'returned_count': 0
            }
            
        cursor = conn.cursor()
        
        # Get overdue replacements
        cursor.execute("""
            SELECT COUNT(*) as count FROM equipment_issues
            WHERE reported_by_email = %s 
            AND replacement_required = 1
            AND (replacement_status = 'Pending' OR replacement_status IS NULL)
            AND replacement_deadline < NOW()
        """, (borrower_email,))  # CHANGED: ? to %s
        overdue_result = cursor.fetchone()
        overdue_count = overdue_result['count'] if overdue_result else 0  # CHANGED: Access by column name
        
        # Get pending replacements (not overdue yet)
        cursor.execute("""
            SELECT COUNT(*) as count FROM equipment_issues
            WHERE reported_by_email = %s 
            AND replacement_required = 1
            AND (replacement_status = 'Pending' OR replacement_status IS NULL)
            AND replacement_deadline >= NOW()
        """, (borrower_email,))  # CHANGED: ? to %s
        pending_result = cursor.fetchone()
        pending_count = pending_result['count'] if pending_result else 0
        
        # Get total damage history (all equipment issues)
        cursor.execute("""
            SELECT COUNT(*) as count FROM equipment_issues
            WHERE reported_by_email = %s
        """, (borrower_email,))  # CHANGED: ? to %s
        total_result = cursor.fetchone()
        total_damages = total_result['count'] if total_result else 0
        
        # Get unresolved issues
        cursor.execute("""
            SELECT COUNT(*) as count FROM equipment_issues
            WHERE reported_by_email = %s
            AND status != 'Resolved'
        """, (borrower_email,))  # CHANGED: ? to %s
        unresolved_result = cursor.fetchone()
        unresolved_issues = unresolved_result['count'] if unresolved_result else 0
        
        # Get return compliance from borrow history
        cursor.execute("""
            SELECT 
                COUNT(*) as total_borrows,
                SUM(CASE WHEN return_time IS NOT NULL THEN 1 ELSE 0 END) as returned_count
            FROM borrow
            WHERE borrower_email = %s
        """, (borrower_email,))  # CHANGED: ? to %s
        borrow_stats = cursor.fetchone()
        total_borrows = borrow_stats['total_borrows'] if borrow_stats else 0  # CHANGED: Access by column name
        returned_count = borrow_stats['returned_count'] if borrow_stats else 0
        
        conn.close()
        
        # Calculate score (100 point scale)
        score = 100
        
        # CRITICAL PENALTY: Overdue replacements (-25 points each)
        # This is the most serious violation
        score -= (overdue_count * 25)
        
        # MODERATE PENALTY: Pending replacements (-10 points each)
        score -= (pending_count * 10)
        
        # MINOR PENALTY: Unresolved issues (-5 points each)
        score -= (unresolved_issues * 5)
        
        # HISTORY PENALTY: Total damages (-3 points per incident)
        score -= (total_damages * 3)
        
        # Return compliance factor
        if total_borrows > 0:
            return_rate = (returned_count / total_borrows) * 100
            # If return rate is below 80%, additional penalty
            if return_rate < 80:
                score -= (80 - return_rate) / 2
        
        # Ensure score stays between 0-100
        score = max(0, min(100, score))
        
        return {
            'score': round(score, 1),
            'overdue_replacements': overdue_count,
            'pending_replacements': pending_count,
            'total_damages': total_damages,
            'unresolved_issues': unresolved_issues,
            'total_borrows': total_borrows,
            'returned_count': returned_count
        }
    
    def get_compliance_status(self, score):
        """Convert score to status string"""
        if score >= 90:
            return "Excellent Standing"
        elif score >= 75:
            return "Good Standing"
        elif score >= 60:
            return "Fair Standing"
        elif score >= 40:
            return "Poor Standing"
        else:
            return "Critical - Restricted"
    
    def get_compliance_color(self, status):
        """Get color for compliance status"""
        colors = {
            "Excellent Standing": "#28a745",
            "Good Standing": "#28a745",
            "Fair Standing": "#ffc107",
            "Poor Standing": "#ff9800",
            "Critical - Restricted": "#dc3545"
        }
        return colors.get(status, "#6c757d")
    
    def update_user_compliance(self, borrower_email):
        """Update user's compliance status in database"""
        conn = get_db_connection()
        if conn is None:
            return False, "Database connection failed", None
            
        cursor = conn.cursor()
        
        try:
            # Calculate compliance
            compliance_data = self.calculate_compliance_score(borrower_email)
            status = self.get_compliance_status(compliance_data['score'])
            
            # Update user_profiles
            cursor.execute("""
                UPDATE user_profiles
                SET return_compliance_status = %s
                WHERE user_id = (SELECT id FROM users WHERE email = %s)
            """, (status, borrower_email))  # CHANGED: ? to %s
            
            conn.commit()
            return True, status, compliance_data
            
        except Exception as e:
            conn.rollback()
            return False, f"Error: {str(e)}", None
        finally:
            conn.close()
    
    def update_all_compliance_statuses(self):
        """Update compliance status for all users (run periodically)"""
        conn = get_db_connection()
        if conn is None:
            return 0, []
            
        cursor = conn.cursor()
        
        # Get all faculty users
        cursor.execute("SELECT email FROM users WHERE role = 'faculty'")
        users = cursor.fetchall()
        conn.close()
        
        updated_count = 0
        results = []
        
        for user in users:
            email = user['email']  # CHANGED: Access by column name
            success, status, data = self.update_user_compliance(email)
            if success:
                updated_count += 1
                results.append({
                    'email': email,
                    'status': status,
                    'score': data['score'] if data else 0
                })
        
        return updated_count, results
    
    def get_compliance_summary(self):
        """Get overall compliance summary for all users"""
        conn = get_db_connection()
        if conn is None:
            return []
            
        cursor = conn.cursor()
        
        # Get all faculty with their compliance
        cursor.execute("""
            SELECT 
                u.email,
                up.full_name,
                up.return_compliance_status,
                COUNT(DISTINCT ei.issue_id) as total_issues,
                SUM(CASE WHEN ei.replacement_required = 1 
                    AND (ei.replacement_status = 'Pending' OR ei.replacement_status IS NULL)
                    AND ei.replacement_deadline < NOW() THEN 1 ELSE 0 END) as overdue_replacements
            FROM users u
            LEFT JOIN user_profiles up ON u.id = up.user_id
            LEFT JOIN equipment_issues ei ON u.email = ei.reported_by_email
            WHERE u.role = 'faculty'
            GROUP BY u.email, up.full_name, up.return_compliance_status
            ORDER BY overdue_replacements DESC, total_issues DESC
        """)  # CHANGED: datetime to NOW() for MySQL
        
        results = cursor.fetchall()
        conn.close()
        
        return results
    
    def check_deadline_approaching(self, days_before=3):
        """Check for replacements with approaching deadlines and return list"""
        conn = get_db_connection()
        if conn is None:
            return []
            
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT 
                ei.issue_id,
                ei.equipment_name,
                ei.reported_by_email,
                ei.reported_by_name,
                ei.replacement_deadline,
                DATEDIFF(ei.replacement_deadline, NOW()) as days_remaining
            FROM equipment_issues ei
            WHERE ei.replacement_required = 1
            AND (ei.replacement_status = 'Pending' OR ei.replacement_status IS NULL)
            AND ei.replacement_deadline > NOW()
            AND ei.replacement_deadline <= DATE_ADD(NOW(), INTERVAL %s DAY)
            ORDER BY ei.replacement_deadline ASC
        """, (days_before,))  # CHANGED: datetime to DATE_ADD for MySQL
        
        results = cursor.fetchall()
        conn.close()
        
        return results

    def get_compliance_table_data(self, search_term="", status_filter=""):
        """Get data for the compliance table with filtering"""
        conn = get_db_connection()
        if conn is None:
            return []
            
        cursor = conn.cursor()
        
        query = """
            SELECT 
                u.email,
                up.full_name,
                up.department,
                up.position,
                up.return_compliance_status,
                COUNT(DISTINCT ei.issue_id) as total_issues,
                SUM(CASE WHEN ei.replacement_required = 1 
                    AND (ei.replacement_status = 'Pending' OR ei.replacement_status IS NULL)
                    AND ei.replacement_deadline < NOW() THEN 1 ELSE 0 END) as overdue_replacements,
                SUM(CASE WHEN ei.replacement_required = 1 
                    AND (ei.replacement_status = 'Pending' OR ei.replacement_status IS NULL)
                    AND ei.replacement_deadline >= NOW() THEN 1 ELSE 0 END) as pending_replacements
            FROM users u
            LEFT JOIN user_profiles up ON u.id = up.user_id
            LEFT JOIN equipment_issues ei ON u.email = ei.reported_by_email
            WHERE u.role = 'faculty'
        """  # CHANGED: datetime to NOW() for MySQL
        
        params = []
        
        # Add search filter
        if search_term:
            query += " AND (LOWER(u.email) LIKE %s OR LOWER(up.full_name) LIKE %s OR LOWER(up.department) LIKE %s)"
            search_pattern = f"%{search_term.lower()}%"
            params.extend([search_pattern, search_pattern, search_pattern])
        
        # Add status filter
        if status_filter:
            query += " AND up.return_compliance_status = %s"
            params.append(status_filter)
        
        query += """
            GROUP BY u.email, up.full_name, up.department, up.position, up.return_compliance_status
            ORDER BY overdue_replacements DESC, total_issues DESC
        """
        
        cursor.execute(query, params)
        results = cursor.fetchall()
        conn.close()
        
        # Calculate scores for each user
        table_data = []
        for row in results:
            email = row['email']  # CHANGED: Access by column name
            compliance_data = self.calculate_compliance_score(email)
            
            table_data.append({
                'email': email,
                'full_name': row['full_name'],
                'department': row['department'],
                'position': row['position'],
                'compliance_status': row['return_compliance_status'],
                'total_issues': row['total_issues'],
                'overdue_replacements': row['overdue_replacements'],
                'pending_replacements': row['pending_replacements'],
                'compliance_score': compliance_data['score'],
                'unresolved_issues': compliance_data['unresolved_issues'],
                'total_damages': compliance_data['total_damages']
            })
        
        return table_data


def show_compliance_dashboard(root, admin_email=None):
    """Show comprehensive compliance dashboard with enhanced table"""
    window = Toplevel(root) if admin_email else root
    window.title("Compliance Dashboard")
    window.geometry("1400x900")
    window.configure(bg="#f5f5f5")
    
    # Header
    header = Frame(window, bg="#2c5530", height=70)
    header.pack(fill="x")
    header.pack_propagate(False)
    
    Label(header, text="📊 Faculty Compliance Dashboard", 
          font=("Arial", 16, "bold"), bg="#2c5530", fg="white").pack(expand=True)
    
    # Main content
    content = Frame(window, bg="#f5f5f5")
    content.pack(fill="both", expand=True, padx=20, pady=20)
    
    # Search and filter section
    search_frame = Frame(content, bg="white", relief="solid", bd=1)
    search_frame.pack(fill="x", pady=(0, 15))
    
    search_content = Frame(search_frame, bg="white")
    search_content.pack(fill="x", padx=20, pady=15)
    
    # Search input
    Label(search_content, text="Search:", font=("Arial", 10, "bold"), 
          bg="white").grid(row=0, column=0, padx=(0, 10), pady=5)
    
    search_var = tk.StringVar()
    search_entry = tk.Entry(search_content, textvariable=search_var, font=("Arial", 10), width=30)
    search_entry.grid(row=0, column=1, padx=(0, 20), pady=5)
    
    # Status filter
    Label(search_content, text="Status Filter:", font=("Arial", 10, "bold"), 
          bg="white").grid(row=0, column=2, padx=(0, 10), pady=5)
    
    status_var = tk.StringVar()
    status_combo = ttk.Combobox(search_content, textvariable=status_var, font=("Arial", 10), width=15)
    status_combo['values'] = ("", "Excellent Standing", "Good Standing", "Fair Standing", "Poor Standing", "Critical - Restricted")
    status_combo.grid(row=0, column=3, padx=(0, 20), pady=5)
    
    # Action buttons
    button_frame = Frame(search_content, bg="white")
    button_frame.grid(row=0, column=4, padx=10, pady=5)
    
    tracker = ComplianceTracker()
    
    def refresh_table():
        """Refresh the table with current filters"""
        search_term = search_var.get().strip()
        status_filter = status_var.get()
        table_data = tracker.get_compliance_table_data(search_term, status_filter)
        update_compliance_table(table_data)
    
    def update_all_compliance():
        """Update all compliance statuses"""
        count, results = tracker.update_all_compliance_statuses()
        messagebox.showinfo("Success", f"Updated compliance status for {count} users")
        refresh_table()
    
    search_btn = Button(button_frame, text="Search", font=("Arial", 10),
                       bg="#007bff", fg="white", relief="flat", padx=15, pady=5,
                       command=refresh_table)
    search_btn.pack(side="left", padx=5)
    
    clear_btn = Button(button_frame, text="Clear", font=("Arial", 10),
                      bg="#6c757d", fg="white", relief="flat", padx=15, pady=5,
                      command=lambda: [search_var.set(""), status_var.set(""), refresh_table()])
    clear_btn.pack(side="left", padx=5)
    
    update_btn = Button(button_frame, text="Update All", font=("Arial", 10),
                       bg="#28a745", fg="white", relief="flat", padx=15, pady=5,
                       command=update_all_compliance)
    update_btn.pack(side="left", padx=5)
    
    # Table section
    table_frame = Frame(content, bg="white", relief="solid", bd=1)
    table_frame.pack(fill="both", expand=True)
    
    # Create table
    columns = ("Name", "Email", "Department", "Position", "Status", "Score", "Total Issues", "Overdue", "Pending", "Unresolved", "Actions")
    tree = ttk.Treeview(table_frame, columns=columns, show="headings", height=20)
    
    # Configure columns
    column_widths = {
        "Name": 150,
        "Email": 200,
        "Department": 120,
        "Position": 120,
        "Status": 140,
        "Score": 80,
        "Total Issues": 100,
        "Overdue": 80,
        "Pending": 80,
        "Unresolved": 100,
        "Actions": 120
    }
    
    for col in columns:
        tree.heading(col, text=col)
        tree.column(col, width=column_widths.get(col, 100), anchor="center")
    
    # Style the treeview
    style = ttk.Style()
    style.configure("Treeview", 
                   background="white",
                   foreground="#333",
                   fieldbackground="white",
                   rowheight=30,
                   font=("Arial", 9))
    style.configure("Treeview.Heading",
                   font=("Arial", 9, "bold"),
                   background="#f0f0f0",
                   foreground="#2c5530")
    style.map("Treeview", background=[("selected", "#2c5530")])
    
    # Scrollbars
    vsb = ttk.Scrollbar(table_frame, orient="vertical", command=tree.yview)
    hsb = ttk.Scrollbar(table_frame, orient="horizontal", command=tree.xview)
    tree.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)
    
    tree.pack(side="left", fill="both", expand=True, padx=10, pady=10)
    vsb.pack(side="right", fill="y", pady=10)
    hsb.pack(side="bottom", fill="x", padx=10)
    
    def update_compliance_table(table_data):
        """Update the table with new data"""
        # Clear existing items
        for item in tree.get_children():
            tree.delete(item)
        
        # Insert new data
        for idx, user_data in enumerate(table_data):
            # Determine row background
            tags = ('evenrow',) if idx % 2 == 0 else ('oddrow',)
            
            # Get status color
            status_color = tracker.get_compliance_color(user_data['compliance_status'])
            
            # Insert row
            tree.insert("", "end", values=(
                user_data['full_name'] or "N/A",
                user_data['email'],
                user_data['department'] or "N/A",
                user_data['position'] or "N/A",
                user_data['compliance_status'] or "Good Standing",
                f"{user_data['compliance_score']:.0f}",
                user_data['total_issues'],
                user_data['overdue_replacements'],
                user_data['pending_replacements'],
                user_data['unresolved_issues'],
                "View Details"
            ), tags=tags)
        
        # Update row count
        count_label.config(text=f"Total Faculty: {len(table_data)}")
    
    # Configure row tags for alternating colors
    tree.tag_configure('evenrow', background='white')
    tree.tag_configure('oddrow', background='#f9f9f9')
    
    # Count label
    count_frame = Frame(content, bg="#f5f5f5")
    count_frame.pack(fill="x", pady=(10, 0))
    
    count_label = Label(count_frame, text="Total Faculty: 0", font=("Arial", 10, "bold"),
                       bg="#f5f5f5", fg="#2c5530")
    count_label.pack(anchor="w")
    
    # Handle row clicks
    def on_tree_click(event):
        item = tree.identify_row(event.y)
        column = tree.identify_column(event.x)
        
        if item and column:
            col_name = tree.heading(column)["text"]
            if col_name == "Actions":
                user_email = tree.item(item)['values'][1]  # Email is in second column
                show_user_compliance_details(window, user_email)
    
    tree.bind("<Double-1>", on_tree_click)
    
    # Context menu
    context_menu = tk.Menu(tree, tearoff=0)
    context_menu.add_command(label="View Details", 
                            command=lambda: show_selected_user_details())
    
    def show_context_menu(event):
        item = tree.identify_row(event.y)
        if item:
            tree.selection_set(item)
            context_menu.post(event.x_root, event.y_root)
    
    tree.bind("<Button-3>", show_context_menu)
    
    def show_selected_user_details():
        selection = tree.selection()
        if selection:
            user_email = tree.item(selection[0])['values'][1]
            show_user_compliance_details(window, user_email)
        else:
            messagebox.showwarning("Warning", "Please select a user to view details")
    
    # Load initial data
    refresh_table()
    
    # Bind search on Enter key
    search_entry.bind("<Return>", lambda e: refresh_table())
    
    # Close button
    close_frame = Frame(window, bg="#f5f5f5")
    close_frame.pack(fill="x", padx=20, pady=(10, 20))
    
    Button(close_frame, text="Close", font=("Arial", 10),
           bg="#6c757d", fg="white", relief="flat", padx=20, pady=10,
           command=window.destroy).pack(side="right", padx=5)


def show_user_compliance_details(parent, user_email):
    """Show detailed compliance information for a specific user"""
    window = Toplevel(parent)
    window.title(f"Compliance Details - {user_email}")
    window.geometry("1000x700")
    window.configure(bg="#f5f5f5")
    
    tracker = ComplianceTracker()
    
    # Get user info
    conn = get_db_connection()
    if conn is None:
        return
        
    cursor = conn.cursor()
    cursor.execute("""
        SELECT up.full_name, up.department, up.position
        FROM users u
        JOIN user_profiles up ON u.id = up.user_id
        WHERE u.email = %s
    """, (user_email,))  # CHANGED: ? to %s
    user_info = cursor.fetchone()
    conn.close()
    
    full_name = user_info['full_name'] if user_info else "Unknown"  # CHANGED: Access by column name
    department = user_info['department'] if user_info else "N/A"
    position = user_info['position'] if user_info else "N/A"
    
    # Header
    header = Frame(window, bg="#007bff", height=80)
    header.pack(fill="x")
    header.pack_propagate(False)
    
    Label(header, text=f"Compliance Report: {full_name}", 
          font=("Arial", 14, "bold"), bg="#007bff", fg="white").pack(pady=10)
    Label(header, text=f"{department} | {position}", 
          font=("Arial", 10), bg="#007bff", fg="white").pack()
    
    # Get compliance data
    compliance_data = tracker.calculate_compliance_score(user_email)
    status = tracker.get_compliance_status(compliance_data['score'])
    history = tracker.get_user_damage_history(user_email)
    overdue = tracker.get_overdue_replacements(user_email)
    pending = tracker.get_pending_replacements(user_email)
    
    # Content
    content = Frame(window, bg="#f5f5f5")
    content.pack(fill="both", expand=True, padx=20, pady=20)
    
    # Score card
    score_frame = Frame(content, bg="white", relief="solid", bd=1)
    score_frame.pack(fill="x", pady=(0, 15))
    
    score_grid = Frame(score_frame, bg="white")
    score_grid.pack(fill="x", padx=20, pady=20)
    
    # Main score
    status_color = tracker.get_compliance_color(status)
    main_score = Frame(score_grid, bg=status_color, relief="solid", bd=2)
    main_score.grid(row=0, column=0, columnspan=2, sticky="ew", pady=(0, 15))
    
    Label(main_score, text=f"{compliance_data['score']:.0f}/100", 
          font=("Arial", 32, "bold"), bg=status_color, fg="white").pack(pady=(15, 5))
    Label(main_score, text=status, 
          font=("Arial", 14), bg=status_color, fg="white").pack(pady=(0, 15))
    
    # Detailed metrics
    metrics = [
        ("Overdue Replacements", compliance_data['overdue_replacements'], "#dc3545"),
        ("Pending Replacements", compliance_data['pending_replacements'], "#ffc107"),
        ("Total Damages", compliance_data['total_damages'], "#ff9800"),
        ("Unresolved Issues", compliance_data['unresolved_issues'], "#6c757d")
    ]
    
    for i, (label, value, color) in enumerate(metrics):
        metric_card = Frame(score_grid, bg="white", relief="solid", bd=1)
        metric_card.grid(row=1, column=i, padx=5, sticky="ew")
        
        Label(metric_card, text=str(value), font=("Arial", 20, "bold"),
              bg="white", fg=color).pack(pady=(10, 5))
        Label(metric_card, text=label, font=("Arial", 9),
              bg="white", fg="#666", wraplength=100).pack(pady=(0, 10))
        
        score_grid.grid_columnconfigure(i, weight=1)
    
    # Tabs for different views
    notebook = ttk.Notebook(content)
    notebook.pack(fill="both", expand=True)
    
    # Tab 1: Overdue Replacements
    overdue_frame = Frame(notebook, bg="white")
    notebook.add(overdue_frame, text=f"Overdue ({len(overdue)})")
    
    if overdue:
        tree1 = create_issues_tree(overdue_frame, "overdue")
        for issue in overdue:
            tree1.insert("", "end", values=(
                issue['issue_id'],  # CHANGED: Access by column name
                issue['equipment_name'],
                issue['barcode'],
                issue['replacement_deadline'].split()[0] if issue['replacement_deadline'] else "N/A",
                f"{issue['days_overdue']} days" if issue['days_overdue'] else "N/A"
            ))
    else:
        Label(overdue_frame, text="No overdue replacements", 
              font=("Arial", 12), bg="white", fg="#28a745").pack(expand=True)
    
    # Tab 2: Pending Replacements
    pending_frame = Frame(notebook, bg="white")
    notebook.add(pending_frame, text=f"Pending ({len(pending)})")
    
    if pending:
        tree2 = create_issues_tree(pending_frame, "pending")
        for issue in pending:
            tree2.insert("", "end", values=(
                issue['issue_id'],  # CHANGED: Access by column name
                issue['equipment_name'],
                issue['barcode'],
                issue['replacement_deadline'].split()[0] if issue['replacement_deadline'] else "N/A",
                f"{issue['days_remaining']} days" if issue['days_remaining'] else "N/A"
            ))
    else:
        Label(pending_frame, text="No pending replacements", 
              font=("Arial", 12), bg="white", fg="#28a745").pack(expand=True)
    
    # Tab 3: All History
    history_frame = Frame(notebook, bg="white")
    notebook.add(history_frame, text=f"All History ({len(history)})")
    
    if history:
        columns = ("ID", "Equipment", "Reported", "Deadline", "Status", "Priority")
        tree3 = ttk.Treeview(history_frame, columns=columns, show="headings", height=15)
        
        for col in columns:
            tree3.heading(col, text=col)
            tree3.column(col, width=120, anchor="center")
        
        for issue in history:
            tree3.insert("", "end", values=(
                issue['issue_id'],  # CHANGED: Access by column name
                issue['equipment_name'],
                issue['reported_date'].split()[0] if issue['reported_date'] else "N/A",
                issue['replacement_deadline'].split()[0] if issue['replacement_deadline'] else "N/A",
                issue['compliance_status'],
                issue['priority']
            ))
        
        scrollbar = ttk.Scrollbar(history_frame, orient="vertical", command=tree3.yview)
        tree3.configure(yscrollcommand=scrollbar.set)
        tree3.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
    else:
        Label(history_frame, text="No damage history", 
              font=("Arial", 12), bg="white", fg="#28a745").pack(expand=True)
    
    # Close button
    Button(window, text="Close", font=("Arial", 10),
           bg="#6c757d", fg="white", relief="flat", padx=20, pady=10,
           command=window.destroy).pack(pady=15)


def create_issues_tree(parent, tree_type):
    """Helper function to create issue treeview"""
    columns = ("ID", "Equipment", "Barcode", "Deadline", "Days")
    tree = ttk.Treeview(parent, columns=columns, show="headings", height=15)
    
    widths = [60, 200, 120, 100, 80]
    for col, width in zip(columns, widths):
        tree.heading(col, text=col)
        tree.column(col, width=width, anchor="center")
    
    scrollbar = ttk.Scrollbar(parent, orient="vertical", command=tree.yview)
    tree.configure(yscrollcommand=scrollbar.set)
    
    tree.pack(side="left", fill="both", expand=True, padx=10, pady=10)
    scrollbar.pack(side="right", fill="y", pady=10)
    
    return tree


# Utility function to run daily compliance update
def run_daily_compliance_update():
    """Run this function daily (e.g., via scheduler) to update all compliance statuses"""
    tracker = ComplianceTracker()
    count, results = tracker.update_all_compliance_statuses()
    print(f"Updated compliance status for {count} users")
    
    # Print summary
    for result in results:
        print(f"  {result['email']}: {result['status']} (Score: {result['score']})")
    
    return count, results


if __name__ == "__main__":
    root = tk.Tk()
    root.title("Compliance Dashboard Test")
    
    show_compliance_dashboard(root)
    
    root.mainloop()