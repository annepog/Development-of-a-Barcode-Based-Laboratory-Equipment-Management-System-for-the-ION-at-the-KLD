# reports.py - Improved Reporting Module with Enhanced Visual Charts (MySQL Version)
import tkinter as tk
from tkinter import ttk, Frame, Label, Button, messagebox, Scrollbar
from tkcalendar import DateEntry
import pymysql
import pandas as pd
from datetime import datetime, timedelta
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import matplotlib
matplotlib.use('Agg')
from PIL import Image, ImageTk

class ReportManager:
    def __init__(self):
        pass
    
    def get_db_connection(self):
        """Get MySQL database connection - CLIENT SIDE"""
        try:
            conn = pymysql.connect(
                host='192.168.1.63',      # Server IP address
                user='lan_user',          # Client username
                password='secure_password_123',  # Client password
                database='faculty_account',
                charset='utf8mb4',
                cursorclass=pymysql.cursors.DictCursor
            )
            return conn
        except Exception as e:
            print(f"Database connection failed: {e}")
            messagebox.showerror("Database Error", f"Cannot connect to database: {e}")
            return None
    

    def get_equipment_utilization(self, start_date=None, end_date=None):
        """Generate equipment utilization report"""
        conn = self.get_db_connection()
        if not conn:
            return pd.DataFrame()
        
        try:
            with conn.cursor() as cursor:
                query = """
                    SELECT 
                        e.name,
                        e.category,
                        COUNT(DISTINCT r.reservation_id) as total_reservations,
                        COUNT(DISTINCT b.borrow_id) as total_borrows,
                        e.total_quantity,
                        e.available_quantity
                    FROM equipment e
                    LEFT JOIN reservations r ON e.id = r.equipment_id
                    LEFT JOIN borrow b ON e.id = b.equipment_id
                    WHERE 1=1
                """
                
                params = []
                if start_date:
                    query += " AND (r.created_at >= %s OR b.borrow_time >= %s)"
                    params.extend([start_date, start_date])
                if end_date:
                    query += " AND (r.created_at <= %s OR b.borrow_time <= %s)"
                    params.extend([end_date, end_date])
                
                query += " GROUP BY e.id ORDER BY total_reservations DESC, total_borrows DESC"
                
                cursor.execute(query, params)
                results = cursor.fetchall()
                
                df = pd.DataFrame(results)
                
                if not df.empty:
                    total_activity = df['total_reservations'] + df['total_borrows']
                    df['utilization_rate'] = (total_activity / total_activity.max() * 100) if total_activity.max() > 0 else 0
                
                return df
                
        except Exception as e:
            print(f"Error getting equipment utilization: {e}")
            return pd.DataFrame()
        finally:
            conn.close()

    def get_borrower_trends(self, start_date=None, end_date=None):
        """Generate borrower trends report"""
        conn = self.get_db_connection()
        if not conn:
            return pd.DataFrame()
        
        try:
            with conn.cursor() as cursor:
                query = """
                    SELECT 
                        up.full_name,
                        up.department,
                        COUNT(DISTINCT r.reservation_id) as total_reservations,
                        COUNT(DISTINCT b.borrow_id) as total_borrows
                    FROM user_profiles up
                    LEFT JOIN users u ON up.user_id = u.id
                    LEFT JOIN reservations r ON u.email = r.user_email
                    LEFT JOIN borrow b ON u.email = b.borrower_email
                    WHERE u.role = 'faculty'
                """
                
                params = []
                if start_date:
                    query += " AND (r.created_at >= %s OR b.borrow_time >= %s)"
                    params.extend([start_date, start_date])
                if end_date:
                    query += " AND (r.created_at <= %s OR b.borrow_time <= %s)"
                    params.extend([end_date, end_date])
                
                query += " GROUP BY u.id HAVING total_reservations > 0 OR total_borrows > 0"
                
                cursor.execute(query, params)
                results = cursor.fetchall()
                return pd.DataFrame(results)
                
        except Exception as e:
            print(f"Error getting borrower trends: {e}")
            return pd.DataFrame()
        finally:
            conn.close()

    def get_activity_trends(self, start_date=None, end_date=None):
        """Get activity trends over time"""
        conn = self.get_db_connection()
        if not conn:
            return pd.DataFrame()
        
        try:
            with conn.cursor() as cursor:
                query = """
                    SELECT 
                        DATE(r.created_at) as activity_date,
                        COUNT(r.reservation_id) as reservations,
                        0 as borrows
                    FROM reservations r
                    WHERE 1=1
                """
                
                params = []
                if start_date:
                    query += " AND r.created_at >= %s"
                    params.append(start_date)
                if end_date:
                    query += " AND r.created_at <= %s"
                    params.append(end_date)
                    
                query += " GROUP BY activity_date"
                
                query += """
                    UNION ALL
                    
                    SELECT 
                        DATE(b.borrow_time) as activity_date,
                        0 as reservations,
                        COUNT(b.borrow_id) as borrows
                    FROM borrow b
                    WHERE 1=1
                """
                
                if start_date:
                    query += " AND b.borrow_time >= %s"
                    params.append(start_date)
                if end_date:
                    query += " AND b.borrow_time <= %s"
                    params.append(end_date)
                    
                query += " GROUP BY activity_date ORDER BY activity_date"
                
                cursor.execute(query, params)
                results = cursor.fetchall()
                df = pd.DataFrame(results)
                
                # Aggregate by date
                if not df.empty:
                    df = df.groupby('activity_date').sum().reset_index()
                    df['total_activities'] = df['reservations'] + df['borrows']
                
                return df
                
        except Exception as e:
            print(f"Error getting activity trends: {e}")
            return pd.DataFrame()
        finally:
            conn.close()

    def get_current_equipment_status(self, start_date=None, end_date=None):
        """Get equipment status based on date range"""
        conn = self.get_db_connection()
        if not conn:
            return pd.DataFrame()
        
        try:
            with conn.cursor() as cursor:
                # If no date range specified, use current status
                if not start_date and not end_date:
                    query = """
                        SELECT 
                            e.name,
                            e.category,
                            e.tracking_type,
                            e.total_quantity,
                            e.available_quantity,
                            e.availability_status,
                            CASE 
                                WHEN EXISTS (SELECT 1 FROM borrow b WHERE b.equipment_id = e.id AND b.return_time IS NULL) THEN 'Borrowed'
                                WHEN e.availability_status = 'Reserved' THEN 'Reserved' 
                                WHEN e.available_quantity > 0 THEN 'Available'
                                ELSE 'Unavailable'
                            END as current_status
                        FROM equipment e
                        WHERE COALESCE(e.is_archived, 0) = 0
                        ORDER BY e.name
                    """
                    cursor.execute(query)
                else:
                    # Get status based on activity in date range
                    query = """
                        SELECT 
                            e.name,
                            e.category,
                            e.tracking_type,
                            e.total_quantity,
                            e.available_quantity,
                            e.availability_status,
                            CASE 
                                WHEN EXISTS (
                                    SELECT 1 FROM borrow b 
                                    WHERE b.equipment_id = e.id 
                                    AND DATE(b.borrow_time) BETWEEN %s AND %s
                                    AND (b.return_time IS NULL OR DATE(b.return_time) > %s)
                                ) THEN 'Borrowed'
                                WHEN EXISTS (
                                    SELECT 1 FROM reservations r 
                                    WHERE r.equipment_id = e.id 
                                    AND DATE(r.created_at) BETWEEN %s AND %s
                                    AND r.status = 'approved'
                                ) THEN 'Reserved'
                                WHEN e.available_quantity > 0 THEN 'Available'
                                ELSE 'Unavailable'
                            END as current_status
                        FROM equipment e
                        WHERE COALESCE(e.is_archived, 0) = 0
                        ORDER BY e.name
                    """
                    params = [start_date, end_date, end_date, start_date, end_date]
                    cursor.execute(query, params)
                
                results = cursor.fetchall()
                return pd.DataFrame(results)
                
        except Exception as e:
            print(f"Error getting equipment status: {e}")
            return pd.DataFrame()
        finally:
            conn.close()

    def show_reports_dashboard(self, parent):
        """Single window dashboard with charts in separate tabs"""
        dashboard = tk.Toplevel(parent)
        dashboard.title("Analytics Dashboard")
        
        # Make window full screen
        dashboard.attributes('-fullscreen', True)
        
        # Add escape key to exit fullscreen
        dashboard.bind('<Escape>', lambda e: dashboard.attributes('-fullscreen', False))
        
        dashboard.configure(bg="#f5f5f5")
        
        # Header with consistent styling
        header_frame = tk.Frame(dashboard, bg="#2c5530", height=80)
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

        tk.Label(left_header, text="📊 Analytics Dashboard", 
            font=("Helvetica", 18, "bold"), bg="#2c5530", fg="white").pack(side="left")

        right_header = tk.Frame(header_content, bg="#2c5530")
        right_header.pack(side="right")

        # Close button
        Button(right_header, text="✕ Close", command=dashboard.destroy,
               bg="#dc3545", fg="white", font=("Arial", 10), relief="flat",
               width=8).pack(side="left", padx=(0, 10))
        
        # Main container
        main_container = Frame(dashboard, bg="#f5f5f5")
        main_container.pack(fill="both", expand=True, padx=20, pady=10)
        
        # Date selection
        date_frame = Frame(main_container, bg="white", relief="solid", bd=1)
        date_frame.pack(fill="x", pady=(0, 10))
        
        Label(date_frame, text="Date Range:", font=("Arial", 11, "bold"), 
              bg="white").pack(side="left", padx=10, pady=10)
        
        start_date_entry = DateEntry(date_frame, width=12, font=("Arial", 10))
        start_date_entry.pack(side="left", padx=5)
        
        end_date_entry = DateEntry(date_frame, width=12, font=("Arial", 10))
        end_date_entry.pack(side="left", padx=5)
        
        # Set default dates (last 30 days)
        end_date = datetime.now()
        start_date = end_date - timedelta(days=30)
        start_date_entry.set_date(start_date)
        end_date_entry.set_date(end_date)
        
        # Create notebook for tabs
        notebook = ttk.Notebook(main_container)
        notebook.pack(fill="both", expand=True, pady=10)
        
        # Tab 1: Equipment Details
        equipment_frame = Frame(notebook, bg="#f5f5f5")
        notebook.add(equipment_frame, text="🧰 Equipment Analytics")
        
        # Tab 2: Borrower Details
        borrower_frame = Frame(notebook, bg="#f5f5f5")
        notebook.add(borrower_frame, text="👥 User Analytics")
        
        # Store frame references
        self.equipment_frame = equipment_frame
        self.borrower_frame = borrower_frame
        
        # Refresh function
        def refresh_charts():
            start_str = start_date_entry.get_date().strftime("%Y-%m-%d")
            end_str = end_date_entry.get_date().strftime("%Y-%m-%d")
            
            # Clear existing content
            for widget in equipment_frame.winfo_children():
                widget.destroy()
            for widget in borrower_frame.winfo_children():
                widget.destroy()
            
            # Create new content
            self.create_equipment_tab(start_str, end_str)
            self.create_borrower_tab(start_str, end_str)
        
        refresh_btn = Button(date_frame, text="🔄 Refresh", command=refresh_charts,
                           bg="#007bff", fg="white", font=("Arial", 10), relief="flat",
                           padx=15, pady=5)
        refresh_btn.pack(side="left", padx=10)
        
        # Load initial content
        refresh_charts()

    def create_equipment_tab(self, start_date=None, end_date=None):
        """Create equipment utilization tab content with improved charts"""
        # Get data
        equipment_df = self.get_equipment_utilization(start_date, end_date)
        status_df = self.get_current_equipment_status()
        activity_df = self.get_activity_trends(start_date, end_date)
        
        # Main content frame with scrollbar
        scroll_frame = Frame(self.equipment_frame, bg="white", relief="solid", bd=1)
        scroll_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Add scrollbar
        scrollbar = Scrollbar(scroll_frame)
        scrollbar.pack(side="right", fill="y")
        
        # Canvas for scrolling
        canvas = tk.Canvas(scroll_frame, bg="white", yscrollcommand=scrollbar.set)
        canvas.pack(side="left", fill="both", expand=True)
        
        scrollbar.config(command=canvas.yview)
        
        # Scrollable content frame
        content_frame = Frame(canvas, bg="white")
        canvas.create_window((0, 0), window=content_frame, anchor="nw")
        
        Label(content_frame, text="Equipment Analytics", font=("Arial", 18, "bold"),
            bg="white", pady=20).pack()
        
        if not equipment_df.empty or not status_df.empty:
            # Create main sections
            main_frame = Frame(content_frame, bg="white")
            main_frame.pack(fill="both", expand=True, padx=20, pady=20)
            
            # Row 1: Current Status Overview (Pie Chart) + Usage Over Time (Line Chart)
            row1_frame = Frame(main_frame, bg="white")
            row1_frame.pack(fill="both", expand=True, pady=10)
            
            # LEFT: Current Status Overview (Pie Chart)
            left_chart = Frame(row1_frame, bg="white", relief="solid", bd=1)
            left_chart.pack(side="left", fill="both", expand=True, padx=5)
            
            desc_frame1 = Frame(left_chart, bg="#f8f9fa", height=70)
            desc_frame1.pack(fill="x")
            desc_frame1.pack_propagate(False)
            Label(desc_frame1, text="📊 Current Equipment Status", font=("Arial", 12, "bold"), 
                bg="#f8f9fa", fg="#333").pack(pady=2)
            Label(desc_frame1, text="Real-time distribution of all equipment by availability status", 
                font=("Arial", 9), bg="#f8f9fa", fg="#666", wraplength=350).pack(pady=2)
            
            # Create pie chart
            fig1, ax1 = plt.subplots(figsize=(6, 5))
            
            status_counts = status_df['current_status'].value_counts()
            colors = ['#2ecc71', '#e74c3c', '#f39c12', '#95a5a6']
            explode = (0.05, 0.05, 0.05, 0.05)[:len(status_counts)]
            
            wedges, texts, autotexts = ax1.pie(status_counts, labels=status_counts.index, 
                                               autopct='%1.1f%%', startangle=90,
                                               colors=colors[:len(status_counts)],
                                               explode=explode,
                                               textprops={'fontsize': 10, 'fontweight': 'bold'})
            
            ax1.set_title('Equipment Status Distribution', fontsize=12, fontweight='bold', pad=20)
            
            # Add legend with counts
            legend_labels = [f'{status}: {count}' for status, count in status_counts.items()]
            ax1.legend(legend_labels, loc='lower left', fontsize=9, bbox_to_anchor=(0, -0.1))
            
            plt.tight_layout(pad=3.0)
            canvas1 = FigureCanvasTkAgg(fig1, left_chart)
            canvas1.draw()
            canvas1.get_tk_widget().pack(fill="both", expand=True, padx=10, pady=10)
            
            # RIGHT: Usage Over Time (Line Chart)
            right_chart = Frame(row1_frame, bg="white", relief="solid", bd=1)
            right_chart.pack(side="right", fill="both", expand=True, padx=5)
            
            desc_frame2 = Frame(right_chart, bg="#f8f9fa", height=70)
            desc_frame2.pack(fill="x")
            desc_frame2.pack_propagate(False)
            Label(desc_frame2, text="📈 Usage Trends Over Time", font=("Arial", 12, "bold"), 
                bg="#f8f9fa", fg="#333").pack(pady=2)
            Label(desc_frame2, text="Daily trends showing reservations and borrows to identify peak usage periods", 
                font=("Arial", 9), bg="#f8f9fa", fg="#666", wraplength=350).pack(pady=2)
            
            # Create line chart
            fig2, ax2 = plt.subplots(figsize=(6, 5))
            
            if not activity_df.empty:
                dates = pd.to_datetime(activity_df['activity_date'])
                
                ax2.plot(dates, activity_df['reservations'], marker='o', linewidth=2, 
                        markersize=5, color='#3498db', label='Reservations')
                ax2.plot(dates, activity_df['borrows'], marker='s', linewidth=2,
                        markersize=5, color='#2ecc71', label='Borrows')
                ax2.plot(dates, activity_df['total_activities'], marker='', linewidth=2.5,
                        color='#e74c3c', linestyle='--', alpha=0.7, label='Total')
                
                ax2.set_title('Daily Activity Trends', fontsize=12, fontweight='bold', pad=20)
                ax2.set_xlabel('Date', fontsize=10)
                ax2.set_ylabel('Number of Activities', fontsize=10)
                ax2.legend(fontsize=9, loc='upper left')
                ax2.grid(True, alpha=0.3)
                
                # Rotate x-axis labels
                plt.xticks(rotation=45, ha='right', fontsize=9)
                
                # Format date labels
                import matplotlib.dates as mdates
                ax2.xaxis.set_major_formatter(mdates.DateFormatter('%m/%d'))
                ax2.xaxis.set_major_locator(mdates.DayLocator(interval=max(1, len(dates)//7)))
            else:
                ax2.text(0.5, 0.5, 'No activity data available', 
                        ha='center', va='center', fontsize=12, transform=ax2.transAxes)
            
            plt.tight_layout(pad=3.0)
            canvas2 = FigureCanvasTkAgg(fig2, right_chart)
            canvas2.draw()
            canvas2.get_tk_widget().pack(fill="both", expand=True, padx=10, pady=10)
            
            # Row 2: Most Used Equipment (Bar Chart)
            row2_frame = Frame(main_frame, bg="white")
            row2_frame.pack(fill="both", expand=True, pady=10)
            
            chart_frame = Frame(row2_frame, bg="white", relief="solid", bd=1)
            chart_frame.pack(fill="both", expand=True, padx=5)
            
            desc_frame3 = Frame(chart_frame, bg="#f8f9fa", height=70)
            desc_frame3.pack(fill="x")
            desc_frame3.pack_propagate(False)
            Label(desc_frame3, text="🔧 Most Used Equipment", font=("Arial", 12, "bold"), 
                bg="#f8f9fa", fg="#333").pack(pady=2)
            Label(desc_frame3, text="Top equipment ranked by total usage (reservations + borrows) to identify high-demand items", 
                font=("Arial", 9), bg="#f8f9fa", fg="#666", wraplength=800).pack(pady=2)
            
            fig3, ax3 = plt.subplots(figsize=(12, 5))
            top_equipment = equipment_df.head(10)
            
            # Gradient colors from blue to green
            colors = ['#3498db', '#45a5db', '#56b2db', '#67bfdb', '#78ccdb', 
                     '#89d9db', '#9ae6db', '#2ecc71', '#27ae60', '#229954']
            
            total_activities = top_equipment['total_reservations'] + top_equipment['total_borrows']
            bars = ax3.bar(range(len(top_equipment)), total_activities, 
                        color=colors[:len(top_equipment)], alpha=0.85, edgecolor='white', linewidth=1.5)
            
            ax3.set_title('Top 10 Equipment by Total Usage', fontsize=14, fontweight='bold', pad=20)
            ax3.set_xlabel('Equipment', fontsize=11)
            ax3.set_ylabel('Total Activities (Reservations + Borrows)', fontsize=11)
            
            ax3.set_xticks(range(len(top_equipment)))
            ax3.set_xticklabels(top_equipment['name'], rotation=45, ha='right', fontsize=10)
            
            # Add value labels on bars - NO LEGEND
            for i, bar in enumerate(bars):
                height = bar.get_height()
                ax3.text(bar.get_x() + bar.get_width()/2., height,
                        f'{int(height)}', ha='center', va='bottom', fontsize=10, fontweight='bold')
            
            ax3.grid(True, alpha=0.3, axis='y', linestyle='--')
            ax3.spines['top'].set_visible(False)
            ax3.spines['right'].set_visible(False)
            
            plt.tight_layout(pad=3.0)
            canvas3 = FigureCanvasTkAgg(fig3, chart_frame)
            canvas3.draw()
            canvas3.get_tk_widget().pack(fill="both", expand=True, padx=10, pady=10)
            
            # Row 3: Equipment Status Lists
            row3_frame = Frame(main_frame, bg="white")
            row3_frame.pack(fill="both", expand=True, pady=10)
            
            status_lists_frame = Frame(row3_frame, bg="white", relief="solid", bd=1)
            status_lists_frame.pack(fill="both", expand=True, padx=5)
            
            desc_frame4 = Frame(status_lists_frame, bg="#f8f9fa", height=70)
            desc_frame4.pack(fill="x")
            desc_frame4.pack_propagate(False)
            Label(desc_frame4, text="📋 Detailed Equipment Status", font=("Arial", 12, "bold"), 
                bg="#f8f9fa", fg="#333").pack(pady=2)
            Label(desc_frame4, text="Complete list of all equipment organized by current status with stock information", 
                font=("Arial", 9), bg="#f8f9fa", fg="#666", wraplength=800).pack(pady=2)
            
            # Create notebook for status tabs
            status_notebook = ttk.Notebook(status_lists_frame)
            status_notebook.pack(fill="both", expand=True, padx=10, pady=10)
            
            status_colors = {
                'Available': '#d4edda',
                'Borrowed': '#f8d7da',
                'Reserved': '#fff3cd',
                'Unavailable': '#f8f9fa'
            }
            
            status_text_colors = {
                'Available': '#155724',
                'Borrowed': '#721c24',
                'Reserved': '#856404',
                'Unavailable': '#6c757d'
            }
            
            # Create tabs for each status
            for status in ['Available', 'Borrowed', 'Reserved', 'Unavailable']:
                status_tab = Frame(status_notebook, bg="white")
                status_notebook.add(status_tab, text=f"{status} ({len(status_df[status_df['current_status'] == status])})")
                
                scroll_frame_tab = Frame(status_tab, bg="white")
                scroll_frame_tab.pack(fill="both", expand=True)
                
                scrollbar_tab = Scrollbar(scroll_frame_tab)
                scrollbar_tab.pack(side="right", fill="y")
                
                canvas_tab = tk.Canvas(scroll_frame_tab, bg="white", yscrollcommand=scrollbar_tab.set)
                canvas_tab.pack(side="left", fill="both", expand=True)
                
                scrollbar_tab.config(command=canvas_tab.yview)
                
                content_frame_tab = Frame(canvas_tab, bg="white")
                canvas_tab.create_window((0, 0), window=content_frame_tab, anchor="nw")
                
                status_equipment = status_df[status_df['current_status'] == status]
                
                if not status_equipment.empty:
                    for idx, equipment in status_equipment.iterrows():
                        card_frame = Frame(content_frame_tab, bg=status_colors[status], 
                                        relief="solid", bd=1, padx=15, pady=10)
                        card_frame.pack(fill="x", padx=10, pady=5)
                        
                        name_frame = Frame(card_frame, bg=status_colors[status])
                        name_frame.pack(fill="x", pady=(0, 5))
                        
                        Label(name_frame, text=equipment['name'], 
                            font=("Arial", 12, "bold"), bg=status_colors[status], 
                            fg=status_text_colors[status], anchor="w").pack(side="left")
                        
                        Label(name_frame, text=equipment['category'], 
                            font=("Arial", 10), bg=status_colors[status], 
                            fg=status_text_colors[status], anchor="w").pack(side="right")
                        
                        details_frame = Frame(card_frame, bg=status_colors[status])
                        details_frame.pack(fill="x")
                        
                        type_qty_frame = Frame(details_frame, bg=status_colors[status])
                        type_qty_frame.pack(fill="x", pady=2)
                        
                        Label(type_qty_frame, text=f"Type: {equipment['tracking_type'].title()}", 
                            font=("Arial", 9), bg=status_colors[status], 
                            fg=status_text_colors[status]).pack(side="left")
                        
                        Label(type_qty_frame, 
                            text=f"Stock: {equipment['available_quantity']}/{equipment['total_quantity']}", 
                            font=("Arial", 9), bg=status_colors[status], 
                            fg=status_text_colors[status]).pack(side="right")
                else:
                    empty_frame = Frame(content_frame_tab, bg="white", height=100)
                    empty_frame.pack(fill="both", expand=True, pady=50)
                    empty_frame.pack_propagate(False)
                    
                    Label(empty_frame, text="📭", font=("Arial", 24), bg="white").pack(expand=True)
                    Label(empty_frame, text=f"No equipment is {status.lower()}", 
                        font=("Arial", 11), bg="white", fg="#666").pack()
                
                def configure_scroll_region_tab(event, c=canvas_tab):
                    c.configure(scrollregion=c.bbox("all"))
                
                content_frame_tab.bind("<Configure>", configure_scroll_region_tab)
                
                def on_mousewheel_tab(event, c=canvas_tab):
                    c.yview_scroll(int(-1*(event.delta/120)), "units")
                
                canvas_tab.bind("<MouseWheel>", on_mousewheel_tab)
                content_frame_tab.bind("<MouseWheel>", on_mousewheel_tab)
                
        else:
            Label(content_frame, text="No equipment data available", 
                font=("Arial", 14), bg="white", fg="#666", pady=50).pack(expand=True)
        
        # Configure scroll region
        def configure_scroll_region(event):
            canvas.configure(scrollregion=canvas.bbox("all"))
        
        content_frame.bind("<Configure>", configure_scroll_region)
        
        def on_mousewheel(event):
            canvas.yview_scroll(int(-1*(event.delta/120)), "units")
        
        canvas.bind("<MouseWheel>", on_mousewheel)
        content_frame.bind("<MouseWheel>", on_mousewheel)

    def create_borrower_tab(self, start_date=None, end_date=None):
        """Create borrower activity tab content"""
        borrower_df = self.get_borrower_trends(start_date, end_date)
        
        scroll_frame = Frame(self.borrower_frame, bg="white", relief="solid", bd=1)
        scroll_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        scrollbar = Scrollbar(scroll_frame)
        scrollbar.pack(side="right", fill="y")
        
        canvas = tk.Canvas(scroll_frame, bg="white", yscrollcommand=scrollbar.set)
        canvas.pack(side="left", fill="both", expand=True)
        
        scrollbar.config(command=canvas.yview)
        
        content_frame = Frame(canvas, bg="white")
        canvas.create_window((0, 0), window=content_frame, anchor="nw")
        
        Label(content_frame, text="User Activity Analytics", font=("Arial", 18, "bold"),
              bg="white", pady=20).pack()
        
        if not borrower_df.empty:
            charts_frame = Frame(content_frame, bg="white")
            charts_frame.pack(fill="both", expand=True, padx=20, pady=20)
            
            # Row 1: Top Active Users
            row1_frame = Frame(charts_frame, bg="white")
            row1_frame.pack(fill="both", expand=True, pady=10)
            
            left_frame = Frame(row1_frame, bg="white", relief="solid", bd=1)
            left_frame.pack(side="left", fill="both", expand=True, padx=5)
            
            desc_frame1 = Frame(left_frame, bg="#f8f9fa", height=70)
            desc_frame1.pack(fill="x")
            desc_frame1.pack_propagate(False)
            Label(desc_frame1, text="👤 Top Active Users", font=("Arial", 12, "bold"), 
                  bg="#f8f9fa", fg="#333").pack(pady=2)
            Label(desc_frame1, text="Users with highest total activities broken down by reservations and borrows", 
                  font=("Arial", 9), bg="#f8f9fa", fg="#666", wraplength=400).pack(pady=2)
            
            fig1, ax1 = plt.subplots(figsize=(6, 4.5))
            top_borrowers = borrower_df.nlargest(8, 'total_reservations')
            
            bar_width = 0.6
            indices = range(len(top_borrowers))
            
            bars1 = ax1.bar(indices, top_borrowers['total_reservations'], bar_width, 
                           label='Reservations', color='#3498db', alpha=0.8)
            bars2 = ax1.bar(indices, top_borrowers['total_borrows'], bar_width,
                           bottom=top_borrowers['total_reservations'], 
                           label='Borrows', color='#2ecc71', alpha=0.8)
            
            ax1.set_title('Top Users by Activity Type', fontsize=12, fontweight='bold', pad=15)
            ax1.set_xlabel('Users', fontsize=10)
            ax1.set_ylabel('Number of Activities', fontsize=10)
            
            ax1.set_xticks(indices)
            ax1.set_xticklabels(top_borrowers['full_name'].fillna('Unknown'), 
                               rotation=45, ha='right', fontsize=9)
            
            ax1.legend(fontsize=9)
            ax1.grid(True, alpha=0.3, axis='y')
            
            for i, (res, bor) in enumerate(zip(top_borrowers['total_reservations'], top_borrowers['total_borrows'])):
                total = res + bor
                if total > 0:
                    ax1.text(i, total + 0.1, f'{total}', ha='center', va='bottom', fontsize=9, fontweight='bold')
            
            plt.tight_layout(pad=3.0)
            canvas1 = FigureCanvasTkAgg(fig1, left_frame)
            canvas1.draw()
            canvas1.get_tk_widget().pack(fill="both", expand=True, padx=10, pady=10)
            
            # Right: User Activity Levels
            right_frame = Frame(row1_frame, bg="white", relief="solid", bd=1)
            right_frame.pack(side="right", fill="both", expand=True, padx=5)
            
            desc_frame2 = Frame(right_frame, bg="#f8f9fa", height=70)
            desc_frame2.pack(fill="x")
            desc_frame2.pack_propagate(False)
            Label(desc_frame2, text="📊 User Activity Distribution", font=("Arial", 12, "bold"), 
                  bg="#f8f9fa", fg="#333").pack(pady=2)
            Label(desc_frame2, text="Distribution of users by activity level to understand engagement patterns", 
                  font=("Arial", 9), bg="#f8f9fa", fg="#666", wraplength=400).pack(pady=2)
            
            fig2, ax2 = plt.subplots(figsize=(6, 4.5))
            
            borrower_df['total_activities'] = borrower_df['total_reservations'] + borrower_df['total_borrows']
            
            high_activity = len(borrower_df[borrower_df['total_activities'] > 5])
            medium_activity = len(borrower_df[(borrower_df['total_activities'] > 2) & (borrower_df['total_activities'] <= 5)])
            low_activity = len(borrower_df[borrower_df['total_activities'] <= 2])
            
            activity_levels = ['High\n(>5)', 'Medium\n(3-5)', 'Low\n(1-2)']
            activity_counts = [high_activity, medium_activity, low_activity]
            colors = ['#2ecc71', '#f39c12', '#e74c3c']
            
            bars = ax2.bar(activity_levels, activity_counts, color=colors, alpha=0.8, edgecolor='white', linewidth=2)
            ax2.set_title('User Activity Levels', fontsize=12, fontweight='bold', pad=15)
            ax2.set_xlabel('Activity Level', fontsize=10)
            ax2.set_ylabel('Number of Users', fontsize=10)
            
            for bar in bars:
                height = bar.get_height()
                ax2.text(bar.get_x() + bar.get_width()/2., height,
                        f'{int(height)}', ha='center', va='bottom', fontsize=10, fontweight='bold')
            
            ax2.grid(True, alpha=0.3, axis='y', linestyle='--')
            ax2.spines['top'].set_visible(False)
            ax2.spines['right'].set_visible(False)
            
            plt.tight_layout(pad=3.0)
            canvas2 = FigureCanvasTkAgg(fig2, right_frame)
            canvas2.draw()
            canvas2.get_tk_widget().pack(fill="both", expand=True, padx=10, pady=10)
            
        else:
            Label(content_frame, text="No user data available for the selected date range", 
                  font=("Arial", 14), bg="white", fg="#666", pady=50).pack(expand=True)
        
        def configure_scroll_region(event):
            canvas.configure(scrollregion=canvas.bbox("all"))
        
        content_frame.bind("<Configure>", configure_scroll_region)
        
        def on_mousewheel(event):
            canvas.yview_scroll(int(-1*(event.delta/120)), "units")
        
        canvas.bind("<MouseWheel>", on_mousewheel)
        content_frame.bind("<MouseWheel>", on_mousewheel)

# Utility function
def show_reports_dashboard(parent):
    ReportManager().show_reports_dashboard(parent)

# Test
if __name__ == "__main__":
    root = tk.Tk()
    root.title("Analytics Dashboard Test")
    root.geometry("400x200")
    root.configure(bg="#f5f5f5")
    
    Button(root, text="📊 Open Analytics Dashboard", command=lambda: show_reports_dashboard(root),
           font=("Arial", 14, "bold"), bg="#2c5530", fg="white", 
           relief="flat", pady=15).pack(expand=True, padx=50, pady=50)
    
    root.mainloop()