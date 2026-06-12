# equipmentmanagement.py - MySQL Version
import tkinter as tk
from tkinter import Label, Frame, Button, Entry, StringVar, OptionMenu, messagebox, Toplevel, Text, IntVar, filedialog, Checkbutton, Radiobutton, Scrollbar
from tkinter import ttk
import pymysql
import urllib.request
import urllib.parse
from PIL import Image, ImageTk, ImageEnhance
import os
import shutil
from datetime import datetime
import barcode
from barcode.writer import ImageWriter
import pandas as pd
from reportlab.lib.pagesizes import letter, A4
from reportlab.pdfgen import canvas
from reportlab.lib.units import inch
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
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
def init_database():
    """Initialize the database tables if they don't exist"""
    conn = get_db_connection()
    if conn is None:
        return
    
    try:
        cursor = conn.cursor()
        
        # Equipment table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS equipment (
                id INT AUTO_INCREMENT PRIMARY KEY,
                barcode VARCHAR(255) UNIQUE NOT NULL,
                name TEXT NOT NULL,
                variant TEXT,
                description TEXT,
                category TEXT NOT NULL,
                usage_instruction TEXT,
                image_path TEXT,
                tracking_type VARCHAR(50) DEFAULT 'individual',
                total_quantity INT DEFAULT 1,
                available_quantity INT DEFAULT 1,
                min_stock_level INT DEFAULT 1,
                availability_status VARCHAR(100) DEFAULT 'Available',
                is_borrowable BOOLEAN DEFAULT TRUE,
                location TEXT DEFAULT 'central supply room',
                class VARCHAR(100) DEFAULT 'consumable',
                is_archived BOOLEAN DEFAULT FALSE,
                archived_date TEXT,
                created_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        conn.commit()
        print("Database initialized successfully")
        
    except Exception as e:
        print(f"Database initialization error: {str(e)}")
    finally:
        conn.close()

def generate_next_barcode(class_name, category, tracking_type):
    """Generate next available barcode based on class, category, and type"""
    
    # Convert class to code
    class_codes = {
        'consumable': '10',
        'plastic': '20', 
        'apparatus': '30',
        'wooden': '40',
        'glass': '50',
        'metal': '60'
    }
    
    # Convert category to code  
    category_codes = {
        'Laboratory Equipment': '01',
        'Medical Equipment': '02'
    }
    
    # Convert type to code
    type_codes = {
        'individual': '01',
        'quantity': '02'
    }
    
    # Get codes
    class_code = class_codes.get(class_name.lower(), '99')
    category_code = category_codes.get(category, '99')
    type_code = type_codes.get(tracking_type.lower(), '99')
    
    # Base barcode prefix
    prefix = f"{class_code}{category_code}{type_code}"
    
    try:
        conn = get_db_connection()
        if conn is None:
            return f"{prefix}000001"
            
        cursor = conn.cursor()
        
        # Find the highest sequence for this class-category-type combination
        cursor.execute("""
            SELECT barcode FROM equipment 
            WHERE barcode LIKE %s AND COALESCE(is_archived, 0) = 0
            ORDER BY barcode DESC LIMIT 1
        """, (f"{prefix}%",))
        
        result = cursor.fetchone()
        conn.close()
        
        if result:
            # Extract sequence from existing barcode and increment
            last_sequence = int(result['barcode'][6:])  # Get last 6 digits
            new_sequence = last_sequence + 1
        else:
            # Start from 1 for new combination
            new_sequence = 1
            
        # Format with leading zeros
        sequence_str = f"{new_sequence:06d}"
        
        return f"{prefix}{sequence_str}"
        
    except Exception as e:
        print(f"Error generating barcode: {str(e)}")
        # Fallback: return a simple sequential barcode
        return f"99{category_codes.get(category, '99')}{type_codes.get(tracking_type, '99')}000001"

def generate_barcode_pdf(equipment_list, output_file=None):
    """
    Generate a PDF with barcode labels using TEC-IT online barcode generator
    Uses Code128 format which is widely compatible with scanners
    """
    if not equipment_list:
        messagebox.showwarning("Warning", "No equipment selected for barcode generation")
        return False
    
    if output_file is None:
        output_file = filedialog.asksaveasfilename(
            defaultextension=".pdf",
            filetypes=[("PDF files", "*.pdf")],
            title="Save Barcode Labels PDF"
        )
        if not output_file:
            return False
    
    try:
        # Create PDF
        c = canvas.Canvas(output_file, pagesize=letter)
        page_width, page_height = letter
        
        # Label dimensions for standard 30-label sheets (3x10)
        label_width = 2.5 * inch
        label_height = 1.5 * inch
        labels_per_row = 3
        labels_per_column = 10
        margin_left = 0.5 * inch
        margin_top = 0.5 * inch
        
        current_row = 0
        current_col = 0
        
        temp_dir = tempfile.mkdtemp()
        
        for idx, equipment in enumerate(equipment_list):
            equip_id = equipment['id']
            barcode_text = equipment['barcode']
            name = equipment['name']
            variant = equipment.get('variant', '')
            category = equipment['category']
            
            # Generate barcode using TEC-IT online API
            try:
                # Use TEC-IT barcode generator API with Code128 format
                barcode_url = f"https://barcode.tec-it.com/barcode.ashx?data={barcode_text}&code=Code128&translate-esc=on&dpi=300"
                
                # Create safe filename
                safe_barcode = "".join(c for c in barcode_text if c.isalnum() or c in "_-")
                temp_barcode_path = os.path.join(temp_dir, f"barcode_{safe_barcode}.png")
                
                # Download the barcode image
                headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
                req = urllib.request.Request(barcode_url, headers=headers)
                
                with urllib.request.urlopen(req) as response:
                    with open(temp_barcode_path, 'wb') as out_file:
                        out_file.write(response.read())
                
                # Calculate position for current label
                x = margin_left + (current_col * label_width)
                y = page_height - margin_top - ((current_row + 1) * label_height)
                
                # Draw label border (helps with cutting)
                c.setStrokeColorRGB(0.8, 0.8, 0.8)  # Light gray border
                c.setLineWidth(0.5)
                c.rect(x, y, label_width, label_height)
                
                # Add barcode image - larger for better scanning
                barcode_img_width = 2.2 * inch
                barcode_img_height = 0.8 * inch
                barcode_x = x + (label_width - barcode_img_width) / 2
                barcode_y = y + label_height - barcode_img_height - 0.1 * inch
                
                # Add the downloaded barcode image to PDF
                if os.path.exists(temp_barcode_path):
                    c.drawImage(temp_barcode_path, barcode_x, barcode_y, 
                              width=barcode_img_width, height=barcode_img_height)
                    
                    # Add barcode number below barcode (human readable)
                    c.setFont("Helvetica-Bold", 10)
                    c.setFillColorRGB(0, 0, 0)  # Black text
                    text_width = c.stringWidth(barcode_text, "Helvetica-Bold", 10)
                    text_x = x + (label_width - text_width) / 2
                    c.drawString(text_x, barcode_y - 0.2 * inch, barcode_text)
                    
                    # Add equipment name
                    c.setFont("Helvetica-Bold", 9)
                    display_name = f"{name}"
                    if variant and variant.strip():
                        display_name += f" ({variant})"
                    
                    # Truncate name if too long
                    if len(display_name) > 25:
                        display_name = display_name[:22] + "..."
                    
                    name_width = c.stringWidth(display_name, "Helvetica-Bold", 9)
                    name_x = x + (label_width - name_width) / 2
                    c.drawString(name_x, barcode_y - 0.4 * inch, display_name)
                    
                    # Add category
                    c.setFont("Helvetica", 8)
                    category_text = f"Category: {category}"
                    cat_width = c.stringWidth(category_text, "Helvetica", 8)
                    cat_x = x + (label_width - cat_width) / 2
                    c.drawString(cat_x, barcode_y - 0.55 * inch, category_text)
                    
                    # Add small print for scanning compatibility
                    c.setFont("Helvetica", 6)
                    c.setFillColorRGB(0.5, 0.5, 0.5)  # Gray text
                    compat_text = "Code128 - YHDAA Compatible"
                    compat_width = c.stringWidth(compat_text, "Helvetica", 6)
                    compat_x = x + (label_width - compat_width) / 2
                    c.drawString(compat_x, y + 0.1 * inch, compat_text)
                
                # Move to next position
                current_col += 1
                if current_col >= labels_per_row:
                    current_col = 0
                    current_row += 1
                
                # Create new page if needed
                if current_row >= labels_per_column:
                    c.showPage()
                    current_row = 0
                    current_col = 0
                    
            except Exception as e:
                print(f"Error generating barcode for {barcode_text}: {str(e)}")
                # Fallback: Create a simple text representation
                try:
                    # Calculate position for current label
                    x = margin_left + (current_col * label_width)
                    y = page_height - margin_top - ((current_row + 1) * label_height)
                    
                    # Draw label border
                    c.setStrokeColorRGB(0.8, 0.8, 0.8)
                    c.setLineWidth(0.5)
                    c.rect(x, y, label_width, label_height)
                    
                    # Add barcode text as fallback
                    c.setFont("Helvetica-Bold", 12)
                    c.setFillColorRGB(0, 0, 0)
                    text_width = c.stringWidth(barcode_text, "Helvetica-Bold", 12)
                    text_x = x + (label_width - text_width) / 2
                    text_y = y + label_height / 2
                    c.drawString(text_x, text_y, barcode_text)
                    
                    # Add equipment name
                    c.setFont("Helvetica", 10)
                    display_name = f"{name}"
                    if variant and variant.strip():
                        display_name += f" ({variant})"
                    
                    if len(display_name) > 25:
                        display_name = display_name[:22] + "..."
                    
                    name_width = c.stringWidth(display_name, "Helvetica", 10)
                    name_x = x + (label_width - name_width) / 2
                    c.drawString(name_x, text_y - 0.3 * inch, display_name)
                    
                    # Move to next position
                    current_col += 1
                    if current_col >= labels_per_row:
                        current_col = 0
                        current_row += 1
                    
                    if current_row >= labels_per_column:
                        c.showPage()
                        current_row = 0
                        current_col = 0
                        
                except Exception as fallback_error:
                    print(f"Fallback also failed for {barcode_text}: {str(fallback_error)}")
                continue
        
        c.save()
        
        # Clean up temporary files
        try:
            shutil.rmtree(temp_dir)
        except:
            pass
        
        messagebox.showinfo("Success", f"PDF generated successfully with {len(equipment_list)} barcode labels!\n\nFile saved to: {output_file}")
        return True
        
    except Exception as e:
        messagebox.showerror("Error", f"Failed to generate PDF: {str(e)}")
        # Try to clean up temp directory
        try:
            shutil.rmtree(temp_dir)
        except:
            pass
        return False

def generate_barcode_csv(equipment_list, output_file=None):
    """
    Generate a CSV file with barcode information for external printing systems
    """
    if not equipment_list:
        messagebox.showwarning("Warning", "No equipment selected for CSV generation")
        return False
    
    if output_file is None:
        output_file = filedialog.asksaveasfilename(
            defaultextension=".csv",
            filetypes=[("CSV files", "*.csv")],
            title="Save Barcode Data CSV"
        )
        if not output_file:
            return False
    
    try:
        # Prepare data for CSV
        data = []
        for equipment in equipment_list:
            barcode_text = equipment['barcode']
            name = equipment['name']
            variant = equipment.get('variant', '')
            category = equipment['category']
            
            data.append({
                'Barcode': barcode_text,
                'Name': name,
                'Variant': variant if variant else '',
                'Category': category,
                'Full_Name': f"{name} ({variant})" if variant else name,
                'Barcode_Type': 'Code128',  # Specify barcode type
                'Scanner_Compatibility': 'YHDAA Compatible'
            })
        
        # Create DataFrame and save as CSV
        df = pd.DataFrame(data)
        df.to_csv(output_file, index=False)
        
        messagebox.showinfo("Success", f"CSV generated successfully for {len(equipment_list)} items!")
        return True
        
    except Exception as e:
        messagebox.showerror("Error", f"Failed to generate CSV: {str(e)}")
        return False

def show_barcode_generation_dialog(parent, admin_email):
    """
    Show dialog for selecting equipment and generating barcodes
    """
    dialog = Toplevel(parent)
    dialog.title("Generate Barcode Labels - YHDAA Compatible")
    dialog.geometry("1920x1080")
    dialog.configure(bg="white")
    dialog.transient(parent)
    dialog.grab_set()
    dialog.resizable(True, True)
    
    main_frame = Frame(dialog, bg="white")
    main_frame.pack(fill="both", expand=True, padx=20, pady=20)
    
    # Header with scanner compatibility info
    header_frame = Frame(main_frame, bg="white")
    header_frame.pack(fill="x", pady=(0, 10))
    
    tk.Label(header_frame, text="Generate Barcode Labels", font=("Arial", 16, "bold"), 
             bg="white", fg="#2c5530").pack(side="left")
    
    # Scanner compatibility badge
    compat_frame = Frame(header_frame, bg="#e8f5e9", relief="solid", borderwidth=1)
    compat_frame.pack(side="right", padx=10)
    tk.Label(compat_frame, text="✓ YHDAA Scanner Compatible", font=("Arial", 10, "bold"), 
             bg="#e8f5e9", fg="#2c5530", padx=10, pady=5).pack()
    
    # Instructions with enhanced formatting
    instructions_frame = Frame(main_frame, bg="#f8f9fa", relief="solid", borderwidth=1)
    instructions_frame.pack(fill="x", pady=10)
    
    instructions_text = """SELECT equipment items and choose your output format:

• PDF FORMAT: Best for direct printing on standard sticker sheets (30 labels per page)
• CSV FORMAT: For use with external label printing systems

BARCODE SPECIFICATIONS:
• Format: Code128 (Industry standard)
• Compatibility: YHDAA and most barcode scanners
• Resolution: 300 DPI for crisp printing
• Size: Optimized for scanning reliability

After generation, print the PDF on adhesive label paper and attach to equipment."""
    
    instructions = tk.Text(instructions_frame, height=8, width=85, font=("Arial", 10), 
                          bg="#f8f9fa", relief="flat", wrap="word")
    instructions.pack(padx=15, pady=10, fill="both")
    instructions.insert("1.0", instructions_text)
    instructions.config(state="disabled")
    
    # Equipment selection frame
    selection_frame = Frame(main_frame, bg="white")
    selection_frame.pack(fill="both", expand=True, pady=10)
    
    # Selection controls
    controls_frame = Frame(selection_frame, bg="white")
    controls_frame.pack(fill="x", pady=(0, 10))
    
    tk.Label(controls_frame, text="Select Equipment:", font=("Arial", 11, "bold"),
             bg="white", fg="#333").pack(side="left")
    
    Button(controls_frame, text="Select All", font=("Arial", 9), 
           bg="#28a745", fg="white", relief="flat", padx=12, pady=3,
           command=lambda: toggle_select_all(True)).pack(side="left", padx=5)
    
    Button(controls_frame, text="Clear All", font=("Arial", 9), 
           bg="#dc3545", fg="white", relief="flat", padx=12, pady=3,
           command=lambda: toggle_select_all(False)).pack(side="left", padx=5)
    
    # Count label
    count_label = tk.Label(controls_frame, text="Selected: 0", font=("Arial", 10),
                          bg="white", fg="#666")
    count_label.pack(side="right", padx=10)
    
    # Treeview for equipment selection
    tree_frame = Frame(selection_frame, bg="white")
    tree_frame.pack(fill="both", expand=True)
    
    columns = ("Select", "Barcode", "Name", "Variant", "Category", "Location")
    tree = ttk.Treeview(tree_frame, columns=columns, show="headings", height=12)
    
    # Scrollbars
    vsb = ttk.Scrollbar(tree_frame, orient="vertical", command=tree.yview)
    hsb = ttk.Scrollbar(tree_frame, orient="horizontal", command=tree.xview)
    tree.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)
    
    # Configure columns
    column_widths = {
        "Select": 60,
        "Barcode": 140,
        "Name": 180,
        "Variant": 120,
        "Category": 140,
        "Location": 120
    }
    
    for col in columns:
        tree.heading(col, text=col)
        tree.column(col, width=column_widths.get(col, 100), anchor="center")
    
    tree.pack(side="left", fill="both", expand=True)
    vsb.pack(side="right", fill="y")
    hsb.pack(side="bottom", fill="x")
    
    # Checkboxes for selection
    selection_vars = {}
    
    def load_equipment_for_barcodes():
        """Load non-archived equipment for barcode generation"""
        try:
            conn = get_db_connection()
            if conn is None:
                return
                
            cursor = conn.cursor()
            cursor.execute("""
                SELECT id, barcode, name, COALESCE(variant, '') as variant, 
                       category, COALESCE(location, 'central supply room') as location
                FROM equipment 
                WHERE COALESCE(is_archived, 0) = 0
                ORDER BY category, name, variant
            """)
            equipment_list = cursor.fetchall()
            conn.close()
            
            # Clear existing items
            for item in tree.get_children():
                tree.delete(item)
            
            selection_vars.clear()
            
            for idx, equipment in enumerate(equipment_list):
                equip_id = equipment['id']
                barcode_text = equipment['barcode']
                name = equipment['name']
                variant = equipment['variant']
                category = equipment['category']
                location = equipment['location']
                
                var = IntVar(value=0)
                selection_vars[equip_id] = var
                
                tree.insert("", "end", values=(
                    "□",  # Will be updated by checkbox
                    barcode_text,
                    name,
                    variant,
                    category,
                    location
                ), tags=(equip_id,))
                
            update_selection_count()
                
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load equipment: {str(e)}")
    
    def toggle_select_all(select):
        """Toggle selection of all items"""
        for var in selection_vars.values():
            var.set(1 if select else 0)
        update_checkbox_display()
        update_selection_count()
    
    def update_checkbox_display():
        """Update the display of checkboxes in the treeview"""
        for item in tree.get_children():
            equip_id = tree.item(item)['tags'][0]
            var = selection_vars.get(int(equip_id))
            if var:
                display_text = "✓" if var.get() else "□"
                tree.set(item, "Select", display_text)
    
    def update_selection_count():
        """Update the selected items count"""
        selected_count = sum(1 for var in selection_vars.values() if var.get() == 1)
        count_label.config(text=f"Selected: {selected_count}")
    
    def on_tree_click(event):
        """Handle clicks on the selection column"""
        item = tree.identify_row(event.y)
        column = tree.identify_column(event.x)
        
        if item and column == "#1":  # Selection column
            equip_id = int(tree.item(item)['tags'][0])
            var = selection_vars.get(equip_id)
            if var:
                var.set(1 if var.get() == 0 else 0)
                update_checkbox_display()
                update_selection_count()
    
    tree.bind("<Button-1>", on_tree_click)
    
    # ACTION BUTTONS FRAME
    button_frame = Frame(main_frame, bg="white")
    button_frame.pack(fill="x", pady=20)
    
    def generate_selected_pdf():
        """Generate PDF for selected items"""
        selected_equipment = get_selected_equipment()
        
        if not selected_equipment:
            messagebox.showwarning("Warning", "Please select at least one equipment item")
            return
        
        if generate_barcode_pdf(selected_equipment):
            messagebox.showinfo("Success", 
                               f"PDF generated successfully for {len(selected_equipment)} items!\n\n"
                               "✓ Code128 format compatible with YHDAA scanners\n"
                               "✓ Optimized for standard label sheets\n"
                               "✓ Ready for printing on adhesive paper")
            dialog.destroy()
    
    def generate_selected_csv():
        """Generate CSV for selected items"""
        selected_equipment = get_selected_equipment()
        
        if not selected_equipment:
            messagebox.showwarning("Warning", "Please select at least one equipment item")
            return
        
        if generate_barcode_csv(selected_equipment):
            messagebox.showinfo("Success", 
                               f"CSV generated successfully for {len(selected_equipment)} items!\n\n"
                               "The CSV file can be used with external label printing systems.")
            dialog.destroy()
    
    def get_selected_equipment():
        """Get list of selected equipment"""
        selected_equipment = []
        for equip_id, var in selection_vars.items():
            if var.get() == 1:
                # Get equipment details
                try:
                    conn = get_db_connection()
                    if conn is None:
                        continue
                        
                    cursor = conn.cursor()
                    cursor.execute("""
                        SELECT id, barcode, name, COALESCE(variant, '') as variant, category
                        FROM equipment WHERE id = %s
                    """, (equip_id,))
                    equipment = cursor.fetchone()
                    conn.close()
                    
                    if equipment:
                        selected_equipment.append(equipment)
                except:
                    continue
        return selected_equipment
    
    # Generate buttons
    generate_frame = Frame(button_frame, bg="white")
    generate_frame.pack(side="left", padx=10)
    
    tk.Label(generate_frame, text="Generate Labels:", font=("Arial", 11, "bold"),
             bg="white", fg="#333").pack(anchor="w")
    
    btn_subframe = Frame(generate_frame, bg="white")
    btn_subframe.pack(pady=5)
    
    Button(btn_subframe, text="📄 Generate PDF Labels", font=("Arial", 11, "bold"), 
           bg="#28a745", fg="white", relief="flat", padx=20, pady=10,
           command=generate_selected_pdf).pack(side="left", padx=5)
    
    Button(btn_subframe, text="📊 Generate CSV Data", font=("Arial", 11), 
           bg="#17a2b8", fg="white", relief="flat", padx=20, pady=10,
           command=generate_selected_csv).pack(side="left", padx=5)
    
    Button(button_frame, text="Cancel", font=("Arial", 11), 
           bg="#6c757d", fg="white", relief="flat", padx=25, pady=10,
           command=dialog.destroy).pack(side="right", padx=10)
    
    # Load equipment data
    load_equipment_for_barcodes()
    update_checkbox_display()

def show_equipment_management(root, admin_email):
    # Clear window
    for widget in root.winfo_children():
        widget.destroy()
    
    root.geometry("1920x1080")
    root.configure(bg="#f5f5f5")

    # Top bar with consistent styling
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

    tk.Label(left_header, text="Equipment Management", 
        font=("Helvetica", 18, "bold"), bg="#2c5530", fg="white").pack(side="left")

    right_header = tk.Frame(header_content, bg="#2c5530")
    right_header.pack(side="right")

    # Back button
    def back_to_dashboard():
        try:
            from admindashboard import show_admin_dashboard
            show_admin_dashboard(root, admin_email)
        except ImportError:
            messagebox.showerror("Error", "Admin dashboard module not found")

    tk.Button(right_header, text="Back", font=("Helvetica", 10),
        bg="white", fg="#2c5530", relief="flat", width=8,
        command=back_to_dashboard).pack(side="left", padx=(0, 10))

    # Admin info
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

    # Search section with shadow
    shadow1 = tk.Frame(content_container, bg="#d0d0d0")
    shadow1.pack(fill="x", pady=(0, 25))
    
    search_section = tk.Frame(shadow1, bg="white", relief="flat")
    search_section.pack(fill="x", padx=2, pady=2)
    
    # Search header
    search_header = tk.Frame(search_section, bg="#e8f5e9", height=50)
    search_header.pack(fill="x")
    search_header.pack_propagate(False)
    
    tk.Label(search_header, text="Search Equipment", font=("Arial", 13, "bold"),
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
        load_equipment_into_table(search_term)
    
    search_btn = tk.Button(search_frame, text="Search", font=("Arial", 10, "bold"),
              bg="#2c5530", fg="white", relief="flat", cursor="hand2",
              padx=20, pady=6, command=perform_search)
    search_btn.pack(side="left", padx=5)
    
    clear_btn = tk.Button(search_frame, text="Clear", font=("Arial", 10, "bold"),
              bg="#999", fg="white", relief="flat", cursor="hand2",
              padx=20, pady=6,
              command=lambda: [search_var.set(""), load_equipment_into_table("")])
    clear_btn.pack(side="left", padx=5)

    # Action buttons frame
    action_frame = tk.Frame(search_content, bg="white")
    action_frame.pack(fill="x", pady=(15, 0))
    
    def open_new_equipment_dialog():
        show_new_equipment_dialog(root, admin_email)
    
    add_btn = tk.Button(action_frame, text="➕ Add New Equipment", font=("Arial", 10, "bold"),
              bg="#007bff", fg="white", relief="flat", cursor="hand2",
              padx=20, pady=6, command=open_new_equipment_dialog)
    add_btn.pack(side="left", padx=5)
    
    def open_archive():
        show_archived_equipment(root, admin_email)
    
    archive_btn = tk.Button(action_frame, text="📁 View Archive", font=("Arial", 10, "bold"),
              bg="#6c757d", fg="white", relief="flat", cursor="hand2",
              padx=20, pady=6, command=open_archive)
    archive_btn.pack(side="left", padx=5)
    
    # Barcode generation button
    def open_barcode_generator():
        show_barcode_generation_dialog(root, admin_email)

    barcode_btn = tk.Button(action_frame, text="📊 Generate Barcodes", font=("Arial", 10, "bold"),
            bg="#28a745", fg="white", relief="flat", cursor="hand2",
            padx=20, pady=6, command=open_barcode_generator)
    barcode_btn.pack(side="left", padx=5)
    
    # Print report button
    def generate_report():
        generate_equipment_pdf_report()

    print_btn = tk.Button(action_frame, text="📄 Print Report", font=("Arial", 10, "bold"),
        bg="#6f42c1", fg="white", relief="flat", cursor="hand2",
        padx=20, pady=6, command=generate_report)
    print_btn.pack(side="left", padx=5)
    
    # Filter options frame
    filter_frame = tk.Frame(search_content, bg="white")
    filter_frame.pack(fill="x", pady=(15, 0))

    tk.Label(filter_frame, text="Filter by Status:", font=("Arial", 10, "bold"),
            bg="white", fg="#333").pack(side="left", padx=(0, 10))

    # Status filter
    status_var = tk.StringVar(value="All")

    status_options = ["All", "Available", "Low Stock", "Out of Stock", "Unavailable", "Borrowed", "Reserved"]

    for status in status_options:
        tk.Radiobutton(filter_frame, text=status, variable=status_var, 
                    value=status, font=("Arial", 9), bg="white", fg="#333", 
                    command=lambda: load_equipment_into_table(search_var.get())).pack(side="left", padx=10)

    # Table section with shadow
    shadow2 = tk.Frame(content_container, bg="#d0d0d0")
    shadow2.pack(fill="both", expand=True)
    
    table_section = tk.Frame(shadow2, bg="white", relief="flat")
    table_section.pack(fill="both", expand=True, padx=2, pady=2)
    
    # Table header
    table_header = tk.Frame(table_section, bg="#e3f2fd", height=50)
    table_header.pack(fill="x")
    table_header.pack_propagate(False)
    
    tk.Label(table_header, text="Equipment Inventory", font=("Arial", 13, "bold"),
             bg="#e3f2fd", fg="#2c5530").pack(side="left", padx=30, pady=15)
    
    # Count label in header
    count_label = tk.Label(table_header, text="Total: 0", font=("Arial", 11),
                          bg="#e3f2fd", fg="#2c5530")
    count_label.pack(side="right", padx=30)

    # Table frame with scrollbar
    table_frame = tk.Frame(table_section, bg="white")
    table_frame.pack(fill="both", expand=True, padx=20, pady=20)

    # Scrollbars
    vsb = ttk.Scrollbar(table_frame, orient="vertical")
    vsb.pack(side="right", fill="y")
    
    hsb = ttk.Scrollbar(table_frame, orient="horizontal")
    hsb.pack(side="bottom", fill="x")

    # Table columns - equipment specific fields
    columns = ("ID", "BARCODE", "NAME", "CATEGORY", "CLASS", "LOCATION", 
           "TYPE", "TOTAL", "AVAIL", "STATUS", "BORROW", "EDIT", "ARCHIVE")
    
    tree = ttk.Treeview(table_frame, columns=columns, show="headings", height=15,
                       yscrollcommand=vsb.set, xscrollcommand=hsb.set)
    tree.pack(fill="both", expand=True)
    
    vsb.config(command=tree.yview)
    hsb.config(command=tree.xview)

    # Configure columns
    column_widths = {
    "ID": 60,
    "BARCODE": 120,
    "NAME": 200,
    "CATEGORY": 150,
    "CLASS": 100,
    "LOCATION": 150,
    "TYPE": 80,
    "TOTAL": 70,
    "AVAIL": 70,
    "STATUS": 100,
    "BORROW": 80,
    "EDIT": 80,
    "ARCHIVE": 80
    }
    
    for col in columns:
        tree.heading(col, text=col)
        tree.column(col, width=column_widths.get(col, 100), anchor="center")
        
    # Click function for treeview
    def on_tree_click(event):
        item = tree.identify_row(event.y)
        column = tree.identify_column(event.x)
        
        if item and column:
            col_name = tree.heading(column)["text"]
            if col_name == "EDIT":
                edit_selected_equipment()
            elif col_name == "ARCHIVE":
                archive_selected_equipment()

    tree.bind("<Button-1>", on_tree_click)

    # Enhanced style for table
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
    tree.tag_configure('lowstock', background='#fff3cd')
    tree.tag_configure('outofstock', background='#f8d7da')
    tree.tag_configure('borrowed', background='#e7f3ff')
    tree.tag_configure('reserved', background='#fff0f0')

    def load_equipment_into_table(search_term=""):
        """Load equipment data into the table with search and filter"""
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
                    id, barcode, name, category,
                    COALESCE(class, 'consumable') as class,
                    COALESCE(location, 'central supply room') as location,
                    COALESCE(tracking_type, 'individual') as tracking_type,
                    COALESCE(total_quantity, 1) as total_quantity,
                    COALESCE(available_quantity, 1) as available_quantity,
                    COALESCE(min_stock_level, 1) as min_stock_level,
                    COALESCE(availability_status, 'Available') as availability_status,
                    COALESCE(is_borrowable, 1) as is_borrowable,
                    COALESCE(variant, '') as variant
                FROM equipment 
                WHERE COALESCE(is_archived, 0) = 0
            """
            params = []
            
            # Add search filter
            if search_term:
                query += " AND (LOWER(name) LIKE %s OR LOWER(barcode) LIKE %s OR LOWER(category) LIKE %s OR LOWER(variant) LIKE %s)"
                search_pattern = f"%{search_term}%"
                params.extend([search_pattern, search_pattern, search_pattern, search_pattern])
            
            query += " ORDER BY name ASC, variant ASC"
            
            cursor.execute(query, params)
            equipment_list = cursor.fetchall()
            conn.close()

            # Apply status filter
            filtered_equipment = []
            current_status_filter = status_var.get()
            
            for equipment in equipment_list:
                equip_id = equipment['id']
                barcode = equipment['barcode']
                name = equipment['name']
                category = equipment['category']
                equip_class = equipment['class']
                location = equipment['location']
                tracking_type = equipment['tracking_type']
                total_qty = equipment['total_quantity']
                avail_qty = equipment['available_quantity']
                min_stock = equipment['min_stock_level']
                avail_status = equipment['availability_status']
                is_borrowable = equipment['is_borrowable']
                variant = equipment['variant']
                
                # Determine status for filtering
                if tracking_type == "quantity":
                    if avail_qty == 0:
                        equipment_status = "Out of Stock"
                    elif avail_qty <= min_stock:
                        equipment_status = "Low Stock"
                    else:
                        equipment_status = "Available"
                else:
                    # For individual items, check various statuses
                    if avail_status == "Reserved":
                        equipment_status = "Reserved"
                    elif avail_qty < total_qty and is_borrowable:
                        equipment_status = "Borrowed"
                    else:
                        equipment_status = avail_status
                
                # Apply status filter
                if current_status_filter == "All" or current_status_filter == equipment_status:
                    filtered_equipment.append(equipment)

            # Insert into table
            for idx, equipment in enumerate(filtered_equipment):
                equip_id = equipment['id']
                barcode = equipment['barcode']
                name = equipment['name']
                category = equipment['category']
                equip_class = equipment['class']
                location = equipment['location']
                tracking_type = equipment['tracking_type']
                total_qty = equipment['total_quantity']
                avail_qty = equipment['available_quantity']
                min_stock = equipment['min_stock_level']
                avail_status = equipment['availability_status']
                is_borrowable = equipment['is_borrowable']
                variant = equipment['variant']
                
                # Determine row tag based on stock status
                tag = 'evenrow' if idx % 2 == 0 else 'oddrow'
                if tracking_type == "quantity":
                    if avail_qty == 0:
                        tag = 'outofstock'
                    elif avail_qty <= min_stock:
                        tag = 'lowstock'
                else:
                    # For individual items, check status
                    if avail_status == "Reserved":
                        tag = 'reserved'
                    elif avail_qty < total_qty and is_borrowable:
                        tag = 'borrowed'
                
                # Prepare display values
                display_name = f"{name} ({variant})" if variant else name
                if len(display_name) > 35:
                    display_name = display_name[:32] + "..."
                    
                type_text = "Qty" if tracking_type == "quantity" else "Indiv"
                borrow_text = "Yes" if is_borrowable else "No"
                
                # Status display
                if tracking_type == "quantity":
                    if avail_qty == 0:
                        status_text = "Out of Stock"
                    elif avail_qty <= min_stock:
                        status_text = "Low Stock"
                    else:
                        status_text = "Available"
                else:
                    # For individual items, check status
                    if avail_status == "Reserved":
                        status_text = "Reserved"
                    elif avail_qty < total_qty and is_borrowable:
                        status_text = "Borrowed"
                    else:
                        status_text = avail_status
                
                row_values = (
                equip_id,
                barcode,
                display_name,
                category,
                equip_class.title(),
                location.title(),
                type_text,
                total_qty,
                avail_qty,
                status_text,
                borrow_text,
                " Edit",
                " Archive"
            )
                
                tree.insert("", "end", values=row_values, tags=(tag,))

            # Update count
            count_label.config(text=f"Total: {len(filtered_equipment)}")

        except Exception as e:
            error_msg = f"Database error: {str(e)}"
            print(error_msg)
            tree.insert("", "end", values=("Error", "Loading equipment", error_msg[:50], "", "", "", "", "", "", "", "", "", ""))

    # Context menu for actions
    context_menu = tk.Menu(tree, tearoff=0)
    context_menu.add_command(label="Edit Equipment", command=lambda: edit_selected_equipment())
    context_menu.add_command(label="Archive Equipment", command=lambda: archive_selected_equipment())
    context_menu.add_separator()
    context_menu.add_command(label="Generate Barcode Label", command=lambda: generate_single_barcode())
    
    def show_context_menu(event):
        item = tree.identify_row(event.y)
        if item:
            tree.selection_set(item)
            context_menu.post(event.x_root, event.y_root)
    
    tree.bind("<Button-3>", show_context_menu)  # Right-click
    
    def edit_selected_equipment():
        selection = tree.selection()
        if not selection:
            messagebox.showwarning("Warning", "Please select an equipment item to edit")
            return
        
        try:
            item = tree.item(selection[0])
            equip_id = item['values'][0]  # ID is in first column
            edit_equipment((equip_id,), root, admin_email)
        except Exception as e:
            messagebox.showerror("Error", f"Failed to edit equipment: {str(e)}")
    
    def archive_selected_equipment():
        selection = tree.selection()
        if not selection:
            messagebox.showwarning("Warning", "Please select an equipment item to archive")
            return
        
        try:
            item = tree.item(selection[0])
            equip_id = item['values'][0]
            equip_name = item['values'][2]
            equip_barcode = item['values'][1]
            confirm_archive_equipment((equip_id, equip_barcode, equip_name), root, admin_email)
        except Exception as e:
            messagebox.showerror("Error", f"Failed to archive equipment: {str(e)}")
    
    def generate_single_barcode():
        selection = tree.selection()
        if not selection:
            messagebox.showwarning("Warning", "Please select an equipment item")
            return
        
        try:
            item = tree.item(selection[0])
            equip_id = item['values'][0]
            
            conn = get_db_connection()
            if conn is None:
                return
                
            cursor = conn.cursor()
            cursor.execute("""
                SELECT id, barcode, name, COALESCE(variant, '') as variant, category
                FROM equipment WHERE id = %s
            """, (equip_id,))
            equipment = cursor.fetchone()
            conn.close()
            
            if equipment:
                if generate_barcode_pdf([equipment]):
                    messagebox.showinfo("Success", 
                                       "Barcode label generated successfully!\n\n"
                                       "✓ Code128 format compatible with YHDAA scanners\n"
                                       "✓ Ready for printing on adhesive paper")
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to generate barcode: {str(e)}")
    
    # Double-click to edit
    tree.bind("<Double-1>", lambda e: edit_selected_equipment())
    
    # Load initial data
    load_equipment_into_table()
    
    # Bind search on Enter key
    search_entry.bind("<Return>", lambda e: perform_search())

def edit_equipment(equipment, root, admin_email):
    equip_id = equipment[0]
    
    try:
        conn = get_db_connection()
        if conn is None:
            return
            
        cursor = conn.cursor()
        cursor.execute("""
            SELECT barcode, name, description, category, usage_instruction, 
                   image_path, tracking_type, total_quantity, available_quantity, 
                   min_stock_level, availability_status, COALESCE(is_borrowable, 1) as is_borrowable,
                   COALESCE(variant, '') as variant, COALESCE(location, 'central supply room') as location,
                   COALESCE(class, 'consumable') as class
            FROM equipment WHERE id = %s
        """, (equip_id,))
        equip_data = cursor.fetchone()
        conn.close()
        
        if not equip_data:
            messagebox.showerror("Error", "Equipment not found")
            return
            
        show_edit_equipment_dialog(root, admin_email, equip_id, equip_data)
        
    except Exception as e:
        messagebox.showerror("Error", "Failed to load equipment: {}".format(str(e)))

def confirm_archive_equipment(equipment, root, admin_email):
    equip_id, barcode, name = equipment[0], equipment[1], equipment[2]
    
    if messagebox.askyesno("Archive", "Archive {} ({})?\n\nThis will hide it from the catalog but preserve all data.".format(name, barcode)):
        try:
            conn = get_db_connection()
            if conn is None:
                return
                
            cursor = conn.cursor()
            
            archived_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            
            cursor.execute("UPDATE equipment SET is_archived = 1, archived_date = %s WHERE id = %s", (archived_date, equip_id))
            conn.commit()
            conn.close()
            
            messagebox.showinfo("Success", "{} has been archived!".format(name))
            show_equipment_management(root, admin_email)
        except Exception as e:
            messagebox.showerror("Error", "Failed to archive: {}".format(str(e)))

def show_archived_equipment(root, admin_email):
    """Display archived equipment with option to restore"""
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
              command=lambda: show_equipment_management(root, admin_email)).pack(side="left", padx=30, pady=20)

    tk.Label(top, text="Archived Equipment", bg="#6c757d", fg="white",
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
    
    tk.Label(table_header, text="Archived Equipment", font=("Arial", 13, "bold"),
             bg="#e3f2fd", fg="#6c757d").pack(side="left", padx=30, pady=15)

    # Table frame
    table_frame = tk.Frame(table_section, bg="white")
    table_frame.pack(fill="both", expand=True, padx=20, pady=20)

    # Scrollbars
    vsb = ttk.Scrollbar(table_frame, orient="vertical")
    vsb.pack(side="right", fill="y")
    
    hsb = ttk.Scrollbar(table_frame, orient="horizontal")
    hsb.pack(side="bottom", fill="x")

    # Table columns
    columns = ("ID", "BARCODE", "NAME", "CATEGORY", "CLASS", "LOCATION", "ARCHIVED DATE", "ACTIONS")
    
    tree = ttk.Treeview(table_frame, columns=columns, show="headings", height=15,
                       yscrollcommand=vsb.set, xscrollcommand=hsb.set)
    tree.pack(fill="both", expand=True)
    
    vsb.config(command=tree.yview)
    hsb.config(command=tree.xview)

    # Configure columns
    column_widths = {
        "ID": 60,
        "BARCODE": 120,
        "NAME": 200,
        "CATEGORY": 150,
        "CLASS": 100,
        "LOCATION": 150,
        "ARCHIVED DATE": 150,
        "ACTIONS": 120
    }
    
    for col in columns:
        tree.heading(col, text=col)
        tree.column(col, width=column_widths.get(col, 100), anchor="center")

    # Style
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

    def load_archived_equipment():
        for item in tree.get_children():
            tree.delete(item)
        
        try:
            conn = get_db_connection()
            if conn is None:
                return
                
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT id, barcode, name, category, COALESCE(class, 'consumable') as class,
                       COALESCE(location, 'central supply room') as location,
                       COALESCE(archived_date, 'N/A') as archived_date
                FROM equipment 
                WHERE COALESCE(is_archived, 0) = 1
                ORDER BY archived_date DESC
            """)
            
            archived_list = cursor.fetchall()
            conn.close()
            
            for idx, equipment in enumerate(archived_list):
                equip_id = equipment['id']
                barcode = equipment['barcode']
                name = equipment['name']
                category = equipment['category']
                equip_class = equipment['class']
                location = equipment['location']
                archived_date = equipment['archived_date']
                
                tag = 'evenrow' if idx % 2 == 0 else 'oddrow'
                
                row_values = (
                    equip_id,
                    barcode,
                    name,
                    category,
                    equip_class.title(),
                    location.title(),
                    archived_date,
                    "Restore | Delete"
                )
                
                tree.insert("", "end", values=row_values, tags=(tag,))

        except Exception as e:
            tree.insert("", "end", values=("Error", "Loading archived", str(e)[:50], "", "", "", "", ""))

    # Context menu for archived items
    context_menu = tk.Menu(tree, tearoff=0)
    context_menu.add_command(label="Restore Equipment", command=lambda: restore_selected_equipment())
    context_menu.add_command(label="Delete Permanently", command=lambda: delete_selected_equipment())
    
    def show_context_menu(event):
        item = tree.identify_row(event.y)
        if item:
            tree.selection_set(item)
            context_menu.post(event.x_root, event.y_root)
    
    tree.bind("<Button-3>", show_context_menu)
    
    def restore_selected_equipment():
        selection = tree.selection()
        if not selection:
            messagebox.showwarning("Warning", "Please select an equipment item to restore")
            return
        
        try:
            item = tree.item(selection[0])
            equip_id = item['values'][0]
            equip_name = item['values'][2]
            restore_equipment(equip_id, equip_name, root, admin_email)
        except Exception as e:
            messagebox.showerror("Error", f"Failed to restore equipment: {str(e)}")
    
    def delete_selected_equipment():
        selection = tree.selection()
        if not selection:
            messagebox.showwarning("Warning", "Please select an equipment item to delete")
            return
        
        try:
            item = tree.item(selection[0])
            equip_id = item['values'][0]
            equip_name = item['values'][2]
            delete_archived_equipment(equip_id, equip_name, root, admin_email)
        except Exception as e:
            messagebox.showerror("Error", f"Failed to delete equipment: {str(e)}")
    
    # Load archived data
    load_archived_equipment()

def restore_equipment(equip_id, name, root, admin_email):
    if messagebox.askyesno("Restore", "Restore '{}' back to active inventory?".format(name)):
        try:
            conn = get_db_connection()
            if conn is None:
                return
                
            cursor = conn.cursor()
            
            cursor.execute("UPDATE equipment SET is_archived = 0, archived_date = NULL WHERE id = %s", (equip_id,))
            conn.commit()
            conn.close()
            
            messagebox.showinfo("Success", "'{}' has been restored!".format(name))
            show_archived_equipment(root, admin_email)
        except Exception as e:
            messagebox.showerror("Error", "Failed to restore: {}".format(str(e)))

def delete_archived_equipment(equip_id, name, root, admin_email):
    if messagebox.askyesno("Delete Permanently", "PERMANENTLY delete '{}'?\n\nThis action cannot be undone!".format(name)):
        try:
            conn = get_db_connection()
            if conn is None:
                return
                
            cursor = conn.cursor()
            
            cursor.execute("SELECT image_path FROM equipment WHERE id = %s", (equip_id,))
            result = cursor.fetchone()
            if result and result['image_path']:
                image_path = result['image_path']
                if os.path.exists(image_path):
                    try:
                        os.remove(image_path)
                    except:
                        pass
            
            cursor.execute("DELETE FROM equipment WHERE id = %s", (equip_id,))
            conn.commit()
            conn.close()
            
            messagebox.showinfo("Success", "'{}' has been permanently deleted!".format(name))
            show_archived_equipment(root, admin_email)
        except Exception as e:
            messagebox.showerror("Error", "Failed to delete: {}".format(str(e)))
            
def print_equipment_table():
    """Print equipment table data to console with proper formatting"""
    try:
        conn = get_db_connection()
        if conn is None:
            return
            
        cursor = conn.cursor()
        
        # Get all equipment data
        cursor.execute("""
            SELECT 
                barcode, name, variant, category, class, location,
                tracking_type, total_quantity, available_quantity,
                min_stock_level, availability_status, is_borrowable
            FROM equipment 
            WHERE COALESCE(is_archived, 0) = 0
            ORDER BY category, name, variant
        """)
        
        equipment_list = cursor.fetchall()
        conn.close()
        
        if not equipment_list:
            print("No equipment found in the database.")
            return
        
        # Print header
        print("\n" + "="*130)
        print("EQUIPMENT INVENTORY REPORT")
        print("Generated on: {}".format(datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
        print("="*130)
        
        # Print column headers with better spacing
        headers = ["Barcode", "Name", "Category", "Location", "Type", "Total", "Avail", "Status"]
        
        # Format string with proper column widths
        header_format = "{:<15} {:<25} {:<22} {:<18} {:<8} {:<6} {:<6} {:<12}"
        print(header_format.format(*headers))
        print("-"*130)
        
        # Print each row
        for equipment in equipment_list:
            barcode = equipment['barcode']
            name = equipment['name']
            variant = equipment['variant']
            category = equipment['category']
            equip_class = equipment['class']
            location = equipment['location']
            tracking_type = equipment['tracking_type']
            total_qty = equipment['total_quantity']
            avail_qty = equipment['available_quantity']
            min_stock = equipment['min_stock_level']
            avail_status = equipment['availability_status']
            is_borrowable = equipment['is_borrowable']
            
            # Format the data for display
            display_name = name
            if variant and variant.strip():
                display_name = f"{name} ({variant})"
            
            # Truncate long names
            if len(display_name) > 24:
                display_name = display_name[:21] + "..."
            
            # Truncate category and location
            display_category = category[:20] + "..." if len(category) > 22 else category
            display_location = location[:16] + "..." if len(location) > 18 else location
            
            type_text = "Indiv" if tracking_type == "individual" else "Qty"
            
            # Determine status display
            if tracking_type == "quantity":
                if avail_qty == 0:
                    status_text = "Out of Stock"
                elif avail_qty <= min_stock:
                    status_text = "Low Stock"
                else:
                    status_text = "Available"
            else:
                status_text = "Available" if avail_status == "Available" else "Unavailable"
            
            row_data = [
                barcode,
                display_name,
                display_category,
                display_location.title(),
                type_text,
                str(total_qty),
                str(avail_qty),
                status_text
            ]
            
            print(header_format.format(*row_data))
        
        # Print summary
        print("-"*130)
        print(f"Total Equipment Items: {len(equipment_list)}")
        
        # Count by category and type
        category_count = {}
        type_count = {"Individual": 0, "Quantity": 0}
        
        for equipment in equipment_list:
            category = equipment['category']
            tracking_type = equipment['tracking_type']
            
            category_count[category] = category_count.get(category, 0) + 1
            type_count["Individual" if tracking_type == "individual" else "Quantity"] += 1
        
        print(f"\nEquipment by Category:")
        for category, count in category_count.items():
            print(f"  {category}: {count} items")
        
        print(f"\nEquipment by Type:")
        print(f"  Individual Items: {type_count['Individual']}")
        print(f"  Quantity Items: {type_count['Quantity']}")
        
        # Stock status summary
        low_stock_count = 0
        out_of_stock_count = 0
        for equipment in equipment_list:
            tracking_type = equipment['tracking_type']
            avail_qty = equipment['available_quantity']
            min_stock = equipment['min_stock_level']
            
            if tracking_type == "quantity":
                if avail_qty == 0:
                    out_of_stock_count += 1
                elif avail_qty <= min_stock:
                    low_stock_count += 1
        
        if low_stock_count > 0 or out_of_stock_count > 0:
            print(f"\nStock Alerts:")
            if low_stock_count > 0:
                print(f"  ⚠️  Low Stock Items: {low_stock_count}")
            if out_of_stock_count > 0:
                print(f"  ❌ Out of Stock Items: {out_of_stock_count}")
        
        print("="*130)
        
    except Exception as e:
        print("Error printing equipment table: {}".format(str(e)))

def generate_equipment_pdf_report():
    """Generate a PDF report of the equipment inventory in LANDSCAPE format"""
    try:
        conn = get_db_connection()
        if conn is None:
            return
            
        cursor = conn.cursor()
        
        # Get all equipment data
        cursor.execute("""
            SELECT 
                barcode, name, variant, category, class, location,
                tracking_type, total_quantity, available_quantity,
                min_stock_level, availability_status, is_borrowable
            FROM equipment 
            WHERE COALESCE(is_archived, 0) = 0
            ORDER BY category, name, variant
        """)
        
        equipment_list = cursor.fetchall()
        conn.close()
        
        if not equipment_list:
            messagebox.showinfo("Info", "No equipment found to generate report.")
            return
        
        # Ask for save location
        output_file = filedialog.asksaveasfilename(
            defaultextension=".pdf",
            filetypes=[("PDF files", "*.pdf")],
            title="Save Equipment Report As"
        )
        
        if not output_file:
            return
        
        # Create PDF in LANDSCAPE mode
        from reportlab.lib.pagesizes import landscape, letter
        c = canvas.Canvas(output_file, pagesize=landscape(letter))
        width, height = landscape(letter)
        
        # Title and header
        c.setFont("Helvetica-Bold", 14)  # Slightly smaller title
        c.drawString(40, height - 40, "Equipment Inventory Report")
        c.setFont("Helvetica", 9)  # Smaller header font
        c.drawString(40, height - 55, f"Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        c.drawString(40, height - 70, f"Total Equipment Items: {len(equipment_list)}")
        
        # Table setup - COMPACT COLUMNS
        headers = ["Barcode", "Name", "Category", "Class", "Location", "Type", "Total", "Avail", "Min Stock", "Status"]
        col_widths = [80, 120, 85, 65, 85, 45, 40, 40, 50, 60]  # More compact columns
        x_positions = [40]
        for i in range(1, len(col_widths)):
            x_positions.append(x_positions[i-1] + col_widths[i-1])
        
        y_position = height - 95
        
        # Table headers - SMALLER FONT
        c.setFont("Helvetica-Bold", 7)  # Smaller font for headers
        for i, header in enumerate(headers):
            c.drawString(x_positions[i], y_position, header)
        
        # Draw line under headers
        c.line(40, y_position - 3, sum(col_widths) + 40, y_position - 3)
        
        # Table data - SMALLER FONT
        c.setFont("Helvetica", 6)  # Smaller font for data
        y_position -= 15
        
        for equipment in equipment_list:
            barcode = equipment['barcode']
            name = equipment['name']
            variant = equipment['variant']
            category = equipment['category']
            equip_class = equipment['class']
            location = equipment['location']
            tracking_type = equipment['tracking_type']
            total_qty = equipment['total_quantity']
            avail_qty = equipment['available_quantity']
            min_stock = equipment['min_stock_level']
            avail_status = equipment['availability_status']
            is_borrowable = equipment['is_borrowable']
            
            # Prepare display values
            display_name = name
            if variant and variant.strip():
                display_name = f"{name} ({variant})"
            
            # Truncate very long names if needed
            if len(display_name) > 25:
                display_name = display_name[:22] + "..."
            
            type_text = "Indiv" if tracking_type == "individual" else "Qty"  # Shorter type text
            
            # Determine status with shorter text
            if tracking_type == "quantity":
                if avail_qty == 0:
                    status_text = "Out"
                elif avail_qty <= min_stock:
                    status_text = "Low"
                else:
                    status_text = "Avail"
            else:
                status_text = "Avail" if avail_status == "Available" else "Unavail"  # Shorter status text
            
            row_data = [
                barcode,
                display_name,
                category,
                equip_class.title(),
                location.title(),
                type_text,
                str(total_qty),
                str(avail_qty),
                str(min_stock),
                status_text
            ]
            
            # Check if we need a new page
            if y_position < 40:
                c.showPage()
                c.setPageSize(landscape(letter))
                y_position = height - 40
                
                # Page header for continuation
                c.setFont("Helvetica-Bold", 9)
                c.drawString(40, height - 25, "Equipment Inventory Report (Continued)")
                
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
        c.drawString(40, height - 40, "Equipment Inventory Summary")
        
        c.setFont("Helvetica", 9)  # Smaller font for summary
        y_pos = height - 65
        
        # Basic counts
        c.drawString(40, y_pos, f"Total Equipment Items: {len(equipment_list)}")
        y_pos -= 20
        
        # Count by category
        category_count = {}
        class_count = {}
        type_count = {"Individual": 0, "Quantity": 0}
        location_count = {}
        
        for equipment in equipment_list:
            category = equipment['category'] or "Unknown"
            equip_class = equipment['class'] or "Unknown"
            tracking_type = equipment['tracking_type']
            location = equipment['location'] or "Unknown"
            
            category_count[category] = category_count.get(category, 0) + 1
            class_count[equip_class] = class_count.get(equip_class, 0) + 1
            type_count["Individual" if tracking_type == "individual" else "Quantity"] += 1
            location_count[location] = location_count.get(location, 0) + 1
        
        # Two column layout
        c.drawString(40, y_pos, "Equipment by Category:")
        y_pos -= 15
        
        col1_x = 50
        col2_x = width / 2 + 20
        current_col = col1_x
        
        for i, (category, count) in enumerate(category_count.items()):
            if i == 6:  # Switch to second column after 6 items
                current_col = col2_x
                y_pos = height - 80
            
            c.drawString(current_col, y_pos, f"• {category}: {count}")
            y_pos -= 12
        
        # Class and type section
        y_pos = min(y_pos, height - 80)
        y_pos -= 15
        
        c.drawString(40, y_pos, "Equipment by Class:")
        y_pos -= 15
        
        current_col = col1_x
        for i, (equip_class, count) in enumerate(class_count.items()):
            if i == 6:
                current_col = col2_x
                y_pos = height - 110
            
            c.drawString(current_col, y_pos, f"• {equip_class.title()}: {count}")
            y_pos -= 12
        
        # Tracking type
        y_pos = min(y_pos, height - 110)
        y_pos -= 15
        
        c.drawString(40, y_pos, "Tracking Type:")
        y_pos -= 15
        c.drawString(50, y_pos, f"• Individual: {type_count['Individual']}")
        y_pos -= 12
        c.drawString(50, y_pos, f"• Quantity: {type_count['Quantity']}")
        
        # Stock status summary
        low_stock_count = 0
        out_of_stock_count = 0
        for equipment in equipment_list:
            tracking_type = equipment['tracking_type']
            avail_qty = equipment['available_quantity']
            min_stock = equipment['min_stock_level']
            
            if tracking_type == "quantity":
                if avail_qty == 0:
                    out_of_stock_count += 1
                elif avail_qty <= min_stock:
                    low_stock_count += 1
        
        y_pos = min(y_pos, height - 130)
        y_pos -= 20
        
        if low_stock_count > 0 or out_of_stock_count > 0:
            c.setFont("Helvetica-Bold", 10)
            c.drawString(40, y_pos, "Stock Alerts:")
            y_pos -= 15
            c.setFont("Helvetica", 9)
            
            if low_stock_count > 0:
                c.drawString(50, y_pos, f"⚠️ Low Stock: {low_stock_count}")
                y_pos -= 12
            if out_of_stock_count > 0:
                c.drawString(50, y_pos, f"❌ Out of Stock: {out_of_stock_count}")
        
        # Footer
        c.setFont("Helvetica", 7)
        c.setFillColorRGB(0.5, 0.5, 0.5)
        c.drawString(40, 25, f"KLD Institute of Nursing - Laboratory Equipment Management System")
        c.drawString(width - 150, 25, f"Page 1")
        
        c.save()
        messagebox.showinfo("Success", f"PDF report generated successfully!\n\nSaved to: {output_file}")
        
    except Exception as e:
        messagebox.showerror("Error", f"Failed to generate PDF report: {str(e)}")

def show_print_options_dialog(parent):
    """Show dialog for print options"""
    dialog = Toplevel(parent)
    dialog.title("Print Equipment Report")
    dialog.geometry("400x300")
    dialog.configure(bg="white")
    dialog.transient(parent)
    dialog.grab_set()
    
    main_frame = Frame(dialog, bg="white", padx=20, pady=20)
    main_frame.pack(fill="both", expand=True)
    
    tk.Label(main_frame, text="Print Equipment Report", font=("Arial", 16, "bold"), 
             bg="white", fg="#2c5530").pack(pady=(0, 20))
    
    tk.Label(main_frame, text="Choose output format:", font=("Arial", 12), 
             bg="white", fg="#333").pack(pady=(0, 10))
    
    # Console print button
    console_btn = Button(main_frame, text="📄 Print to Console", font=("Arial", 11, "bold"),
                        bg="#17a2b8", fg="white", relief="flat", padx=20, pady=15,
                        command=lambda: [print_equipment_table(), dialog.destroy()])
    console_btn.pack(fill="x", pady=10)
    
    # PDF report button
    pdf_btn = Button(main_frame, text="📊 Generate PDF Report", font=("Arial", 11, "bold"),
                    bg="#28a745", fg="white", relief="flat", padx=20, pady=15,
                    command=lambda: [generate_equipment_pdf_report(), dialog.destroy()])
    pdf_btn.pack(fill="x", pady=10)
    
    # Cancel button
    cancel_btn = Button(main_frame, text="Cancel", font=("Arial", 11),
                       bg="#6c757d", fg="white", relief="flat", padx=20, pady=10,
                       command=dialog.destroy)
    cancel_btn.pack(fill="x", pady=10)

def show_new_equipment_dialog(parent, admin_email):
    dialog = Toplevel(parent)
    dialog.title("Add New Equipment")
    dialog.geometry("600x750")
    dialog.configure(bg="#f8f9fa")
    dialog.transient(parent)
    dialog.grab_set()
    dialog.resizable(True, True)
    
    # Main container
    main_frame = Frame(dialog, bg="#f8f9fa")
    main_frame.pack(fill="both", expand=True, padx=20, pady=20)
    
    # Header
    header_frame = Frame(main_frame, bg="#f8f9fa", height=80)
    header_frame.pack(fill="x", pady=(0, 20))
    header_frame.pack_propagate(False)
    
    tk.Label(header_frame, text="Add New Equipment", font=("Arial", 18, "bold"), 
             bg="#f8f9fa", fg="#2c5530").pack(expand=True)
    
    tk.Label(header_frame, text="Fill in the equipment details below", 
             font=("Arial", 10), bg="#f8f9fa", fg="#666").pack(pady=(0, 10))
    
    # Create scrollable frame
    canvas_frame = Frame(main_frame, bg="#f8f9fa")
    canvas_frame.pack(fill="both", expand=True)
    
    canvas = tk.Canvas(canvas_frame, bg="#f8f9fa", highlightthickness=0)
    scrollbar = ttk.Scrollbar(canvas_frame, orient="vertical", command=canvas.yview)
    scrollable_frame = Frame(canvas, bg="#f8f9fa")
    
    scrollable_frame.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
    canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
    canvas.configure(yscrollcommand=scrollbar.set)
    
    canvas.pack(side="left", fill="both", expand=True)
    scrollbar.pack(side="right", fill="y")
    
    def on_mousewheel(event):
        canvas.yview_scroll(int(-1*(event.delta/120)), "units")
    canvas.bind_all("<MouseWheel>", on_mousewheel)
    
    # Form fields
    fields = {}
    
    # Basic Information Section - WITH BORDER
    basic_card = Frame(scrollable_frame, bg="white", relief="solid", bd=1)
    basic_card.pack(fill="x", pady=(0, 20))
    
    basic_header = Frame(basic_card, bg="#e8f5e9", height=35)
    basic_header.pack(fill="x")
    basic_header.pack_propagate(False)
    
    tk.Label(basic_header, text="📋 Basic Information", font=("Arial", 11, "bold"), 
             bg="#e8f5e9", fg="#2c5530").pack(side="left", padx=12, pady=8)
    
    basic_content = Frame(basic_card, bg="white")
    basic_content.pack(fill="x", padx=15, pady=15)
    
    # Barcode field - READ ONLY
    barcode_frame = Frame(basic_content, bg="white")
    barcode_frame.pack(fill="x", pady=8)
    
    tk.Label(barcode_frame, text="Barcode *", font=("Arial", 10, "bold"), 
            bg="white", fg="#495057", width=15, anchor="w").pack(side="left")
    
    barcode_entry = Entry(barcode_frame, font=("Arial", 10), width=45, 
                         relief="solid", bd=1, bg="white", state="readonly")
    barcode_entry.pack(side="left", padx=10, fill="x", expand=True)
    fields['barcode'] = barcode_entry
    
    # Generate barcode button
    generate_btn_frame = Frame(basic_content, bg="white")
    generate_btn_frame.pack(fill="x", pady=8)
    
    Button(generate_btn_frame, text="🔄 Generate Barcode", font=("Arial", 9, "bold"), 
           bg="#17a2b8", fg="white", relief="flat", padx=20, pady=6, cursor="hand2",
           command=lambda: auto_generate_barcode()).pack(side="left", padx=(150, 0))
    
    # Other form fields
    form_fields = [
        ("Name *", "name"), 
        ("Variant", "variant"),
        ("Description *", "description"),
        ("Category *", "category"),
        ("Usage Instruction *", "usage"),
    ]

    for label_text, field_name in form_fields:
        field_frame = Frame(basic_content, bg="white")
        field_frame.pack(fill="x", pady=8)
        
        tk.Label(field_frame, text=label_text, font=("Arial", 10, "bold"), 
                bg="white", fg="#495057", width=15, anchor="w").pack(side="left")
        
        if field_name == "category":
            # Create dropdown for category
            category_var = StringVar(dialog)
            category_var.set("Medical Equipment")
            
            category_menu = OptionMenu(field_frame, category_var, "Medical Equipment", "Laboratory Equipment")
            category_menu.config(font=("Arial", 10), width=42, bg="white", relief="solid", bd=1)
            category_menu.pack(side="left", padx=10, fill="x", expand=True)
            fields[field_name] = category_var
        
        elif field_name in ["description", "usage"]:
            # Create larger text area
            text_frame = Frame(field_frame, bg="white")
            text_frame.pack(side="left", padx=10, fill="x", expand=True)
            
            text_widget = Text(text_frame, font=("Arial", 10), width=45, height=4, 
                              wrap="word", relief="solid", bd=1, bg="white")
            
            # Add scrollbar
            scrollbar = ttk.Scrollbar(text_frame, command=text_widget.yview)
            text_widget.config(yscrollcommand=scrollbar.set)
            
            text_widget.pack(side="left", fill="both", expand=True)
            scrollbar.pack(side="right", fill="y")
            
            fields[field_name] = text_widget
        
        else:
            entry = Entry(field_frame, font=("Arial", 10), width=45, 
                         relief="solid", bd=1, bg="white")
            entry.pack(side="left", padx=10, fill="x", expand=True)
            fields[field_name] = entry
    
    # Location and Class
    location_class_frame = Frame(basic_content, bg="white")
    location_class_frame.pack(fill="x", pady=10)
    
    # Location
    location_left = Frame(location_class_frame, bg="white")
    location_left.pack(side="left", padx=(0, 20), fill="x", expand=True)
    
    tk.Label(location_left, text="Location *", font=("Arial", 10, "bold"), 
            bg="white", fg="#495057", anchor="w").pack(anchor="w")
    
    location_var = StringVar(dialog)
    location_var.set("central supply room")
    location_menu = OptionMenu(location_left, location_var, 
                              "central supply room", "anatomy laboratory", 
                              "nutrition laboratory", "skills laboratory", "or-dr complex")
    location_menu.config(font=("Arial", 10), width=25, bg="white", relief="solid", bd=1)
    location_menu.pack(pady=(5, 0), fill="x")
    fields['location'] = location_var
    
    # Class
    class_right = Frame(location_class_frame, bg="white")
    class_right.pack(side="left", fill="x", expand=True)
    
    tk.Label(class_right, text="Class *", font=("Arial", 10, "bold"), 
            bg="white", fg="#495057", anchor="w").pack(anchor="w")
    
    class_var = StringVar(dialog)
    class_var.set("consumable")
    class_menu = OptionMenu(class_right, class_var, 
                           "consumable", "plastic", "apparatus", "wooden", "glass", "metal")
    class_menu.config(font=("Arial", 10), width=25, bg="white", relief="solid", bd=1)
    class_menu.pack(pady=(5, 0), fill="x")
    fields['class'] = class_var
    
    # Inventory Settings Section - WITH BORDER
    inventory_card = Frame(scrollable_frame, bg="white", relief="solid", bd=1)
    inventory_card.pack(fill="x", pady=(0, 20))
    
    inventory_header = Frame(inventory_card, bg="#e3f2fd", height=35)
    inventory_header.pack(fill="x")
    inventory_header.pack_propagate(False)
    
    tk.Label(inventory_header, text="📊 Inventory Settings", font=("Arial", 11, "bold"), 
             bg="#e3f2fd", fg="#1565c0").pack(side="left", padx=12, pady=8)
    
    inventory_content = Frame(inventory_card, bg="white")
    inventory_content.pack(fill="x", padx=15, pady=15)
    
    # Tracking Type
    tracking_frame = Frame(inventory_content, bg="white")
    tracking_frame.pack(fill="x", pady=8)
    
    tk.Label(tracking_frame, text="Tracking Type *", font=("Arial", 10, "bold"), 
            bg="white", fg="#495057", width=15, anchor="w").pack(side="left")
    
    tracking_var = StringVar(value="individual")
    tracking_radio_frame = Frame(tracking_frame, bg="white")
    tracking_radio_frame.pack(side="left", padx=10, fill="x", expand=True)
    
    Radiobutton(tracking_radio_frame, text="Individual (Unique items)", 
                variable=tracking_var, value="individual", bg="white", 
                font=("Arial", 10), selectcolor="#e8f5e9", 
                activebackground="white").pack(anchor="w", pady=2)
    Radiobutton(tracking_radio_frame, text="Quantity (Bulk items)", 
                variable=tracking_var, value="quantity", bg="white", 
                font=("Arial", 10), selectcolor="#e8f5e9",
                activebackground="white").pack(anchor="w", pady=2)
    
    fields['tracking_type'] = tracking_var
    
    # Quantity Fields
    quantity_grid = Frame(inventory_content, bg="white")
    quantity_grid.pack(fill="x", pady=10)
    
    # Total Quantity
    total_qty_frame = Frame(quantity_grid, bg="white")
    total_qty_frame.pack(side="left", padx=(0, 30), fill="x", expand=True)
    
    tk.Label(total_qty_frame, text="Total Quantity *", font=("Arial", 10, "bold"), 
            bg="white", fg="#495057", anchor="w").pack(anchor="w")
    
    total_qty_entry = Entry(total_qty_frame, font=("Arial", 10), width=15,
                           relief="solid", bd=1, bg="white", justify="center")
    total_qty_entry.insert(0, "1")
    total_qty_entry.pack(pady=(5, 0), fill="x")
    fields['total_quantity'] = total_qty_entry
    
    # Available Quantity
    avail_frame = Frame(quantity_grid, bg="white")
    avail_frame.pack(side="left", padx=(0, 30), fill="x", expand=True)
    
    tk.Label(avail_frame, text="Available Quantity *", font=("Arial", 10, "bold"), 
            bg="white", fg="#495057", anchor="w").pack(anchor="w")
    
    avail_qty_entry = Entry(avail_frame, font=("Arial", 10), width=15,
                           relief="solid", bd=1, bg="white", justify="center")
    avail_qty_entry.insert(0, "1")
    avail_qty_entry.pack(pady=(5, 0), fill="x")
    fields['available_quantity'] = avail_qty_entry
    
    # Min Stock Level - CHANGED DEFAULT FROM 5 TO 1
    min_stock_frame = Frame(quantity_grid, bg="white")
    min_stock_frame.pack(side="left", fill="x", expand=True)
    
    tk.Label(min_stock_frame, text="Min Stock Level *", font=("Arial", 10, "bold"), 
            bg="white", fg="#495057", anchor="w").pack(anchor="w")
    
    min_stock_entry = Entry(min_stock_frame, font=("Arial", 10), width=15,
                           relief="solid", bd=1, bg="white", justify="center")
    min_stock_entry.insert(0, "1")  # CHANGED FROM "5" TO "1"
    min_stock_entry.pack(pady=(5, 0), fill="x")
    fields['min_stock_level'] = min_stock_entry
    
    # Status
    status_frame = Frame(inventory_content, bg="white")
    status_frame.pack(fill="x", pady=8)
    
    tk.Label(status_frame, text="Status *", font=("Arial", 10, "bold"), 
            bg="white", fg="#495057", width=15, anchor="w").pack(side="left")
    
    status_var = StringVar(value="Available")
    status_menu = OptionMenu(status_frame, status_var, "Available", "Unavailable", "Reserved")
    status_menu.config(font=("Arial", 10), width=42, bg="white", relief="solid", bd=1)
    status_menu.pack(side="left", padx=10, fill="x", expand=True)
    fields['availability_status'] = status_var
    
    # Borrowing Settings - WITH BORDER
    borrow_card = Frame(scrollable_frame, bg="white", relief="solid", bd=1)
    borrow_card.pack(fill="x", pady=(0, 20))
    
    borrow_header = Frame(borrow_card, bg="#fff3cd", height=35)
    borrow_header.pack(fill="x")
    borrow_header.pack_propagate(False)
    
    tk.Label(borrow_header, text="🔄 Borrowing Settings", font=("Arial", 11, "bold"), 
             bg="#fff3cd", fg="#856404").pack(side="left", padx=12, pady=8)
    
    borrow_content = Frame(borrow_card, bg="white")
    borrow_content.pack(fill="x", padx=15, pady=15)
    
    borrow_var = IntVar(value=1)
    Checkbutton(borrow_content, text="Borrowable by students/faculty", 
                variable=borrow_var, bg="white", font=("Arial", 10),
                activebackground="white", selectcolor="#e8f5e9").pack(anchor="w")
    fields['is_borrowable'] = borrow_var
    
    # Image Upload Section - WITH BORDER
    image_card = Frame(scrollable_frame, bg="white", relief="solid", bd=1)
    image_card.pack(fill="x", pady=(0, 20))
    
    image_header = Frame(image_card, bg="#f8d7da", height=35)
    image_header.pack(fill="x")
    image_header.pack_propagate(False)
    
    tk.Label(image_header, text="🖼️ Equipment Image", font=("Arial", 11, "bold"), 
             bg="#f8d7da", fg="#721c24").pack(side="left", padx=12, pady=8)
    
    image_content = Frame(image_card, bg="white")
    image_content.pack(fill="x", padx=15, pady=15)
    
    # Image preview - with border
    image_preview_frame = Frame(image_content, bg="#e9ecef", width=300, height=200, relief="solid", borderwidth=1)
    image_preview_frame.pack(pady=8)
    image_preview_frame.pack_propagate(False)
    
    preview_label = Label(image_preview_frame, text="No image selected\n\nClick 'Browse Image' to upload", 
                         font=("Arial", 9), bg="#e9ecef", fg="#6c757d", justify="center")
    preview_label.pack(expand=True)
    
    fields['image_preview_label'] = preview_label
    fields['image_path'] = None
    fields['original_image'] = None
    
    def browse_image():
        file_path = filedialog.askopenfilename(
            title="Select Equipment Image",
            filetypes=[
                ("Image files", "*.jpg *.jpeg *.png *.gif *.bmp"),
                ("All files", "*.*")
            ]
        )
        
        if file_path:
            try:
                img = Image.open(file_path)
                fields['original_image'] = img
                
                img_copy = img.copy()
                img_copy.thumbnail((280, 180), Image.Resampling.LANCZOS)
                photo = ImageTk.PhotoImage(img_copy)
                
                preview_label.configure(image=photo, text="")
                preview_label.image = photo
                
                fields['image_path'] = file_path
                
            except Exception as e:
                messagebox.showerror("Error", "Failed to load image: {}".format(str(e)))
    
    image_btn_frame = Frame(image_content, bg="white")
    image_btn_frame.pack(pady=8)
    
    Button(image_btn_frame, text="📁 Browse Image", font=("Arial", 10), 
           bg="#007bff", fg="white", relief="flat", padx=18, pady=6, cursor="hand2",
           command=browse_image).pack(side="left", padx=5)
    
    # AUTO-GENERATE BARCODE FUNCTIONALITY
    def auto_generate_barcode():
        """Auto-generate barcode when form fields change"""
        class_name = class_var.get()
        category = fields['category'].get().strip()
        tracking_type = tracking_var.get()
        
        if class_name and category and tracking_type:
            barcode = generate_next_barcode(class_name, category, tracking_type)
            # Auto-fill the barcode field
            barcode_entry.config(state="normal")  # Temporarily enable to set value
            barcode_entry.delete(0, tk.END)
            barcode_entry.insert(0, barcode)
            barcode_entry.config(state="readonly")  # Set back to readonly
        else:
            messagebox.showwarning("Warning", "Please select Class, Category, and Tracking Type first")

    # Add traces to auto-generate when any of these fields change
    class_var.trace('w', lambda *args: auto_generate_barcode())
    tracking_var.trace('w', lambda *args: auto_generate_barcode())
    
    # For category field (Entry widget), we need to bind to key release
    if 'category' in fields and hasattr(fields['category'], 'bind'):
        fields['category'].bind('<KeyRelease>', lambda e: auto_generate_barcode())
    
    # Action buttons - WITH BORDER
    button_card = Frame(scrollable_frame, bg="white", relief="solid", bd=1)
    button_card.pack(fill="x", pady=(0, 10))
    
    button_content = Frame(button_card, bg="white")
    button_content.pack(fill="x", padx=15, pady=15)
    
    button_frame = Frame(button_content, bg="white")
    button_frame.pack(fill="x")
    
    # Cancel button
    Button(button_frame, text="✕ Cancel", font=("Arial", 11, "bold"), 
           bg="#6c757d", fg="white", relief="flat", padx=25, pady=10, cursor="hand2",
           command=dialog.destroy).pack(side="left", padx=10)
    
    # Save button
    Button(button_frame, text="💾 Save Equipment", font=("Arial", 11, "bold"), 
           bg="#28a745", fg="white", relief="flat", padx=25, pady=10, cursor="hand2",
           command=lambda: save_new_equipment(fields, dialog, parent, admin_email)).pack(side="right", padx=10)

def save_new_equipment(fields, dialog, parent, admin_email):
    # Get field values - temporarily enable barcode field to read value
    barcode_entry = fields["barcode"]
    barcode_entry.config(state="normal")
    barcode = barcode_entry.get().strip()
    barcode_entry.config(state="readonly")
    name = fields["name"].get().strip()
    variant = fields["variant"].get().strip()
    category = fields["category"].get().strip()
    location = fields['location'].get()
    equip_class = fields['class'].get()
    tracking_type = fields['tracking_type'].get()
    is_borrowable = fields['is_borrowable'].get()
    
    # Handle Text widgets for description and usage
    if isinstance(fields["description"], Text):
        description = fields["description"].get("1.0", "end-1c").strip()
    else:
        description = fields["description"].get().strip()

    if isinstance(fields["usage"], Text):
        usage = fields["usage"].get("1.0", "end-1c").strip()
    else:
        usage = fields["usage"].get().strip()
    
    try:
        total_qty = int(fields['total_quantity'].get().strip())
        avail_qty = int(fields['available_quantity'].get().strip())
        min_stock = int(fields['min_stock_level'].get().strip())
    except ValueError:
        messagebox.showerror("Error", "Quantity values must be numbers")
        return
    
    avail_status = fields['availability_status'].get()
    image_path = fields.get('image_path')
    original_image = fields.get('original_image')
    
    # Validation
    if not all([barcode, name, description, category, usage]):
        messagebox.showerror("Error", "Please fill in all required fields (*)")
        return
    
    if avail_qty > total_qty:
        messagebox.showerror("Error", "Available quantity cannot exceed total quantity")
        return
    
    try:
        conn = get_db_connection()
        if conn is None:
            return
            
        cursor = conn.cursor()
        
        # Check for duplicate barcode
        cursor.execute("SELECT id FROM equipment WHERE barcode = %s", (barcode,))
        if cursor.fetchone():
            messagebox.showerror("Error", "Barcode already exists")
            conn.close()
            return
        
        # Handle image upload
        final_image_path = None
        if image_path and original_image:
            try:
                if not os.path.exists("equipment_images"):
                    os.makedirs("equipment_images")
                
                file_extension = os.path.splitext(image_path)[1]
                if not file_extension:
                    file_extension = ".jpg"
                
                safe_barcode = barcode.replace("/", "_").replace("\\", "_").replace(" ", "_")
                safe_barcode = "".join(c for c in safe_barcode if c.isalnum() or c in "_-")
                
                timestamp = str(int(datetime.now().timestamp()))
                new_filename = f"equip_{safe_barcode}_{timestamp}{file_extension}"
                final_image_path = os.path.join("equipment_images", new_filename)
                
                original_image.save(final_image_path)
                print(f"Image saved to: {final_image_path}")
                
            except Exception as e:
                print(f"Error saving image: {str(e)}")
                final_image_path = None
        
        # Insert new equipment
        cursor.execute("""
            INSERT INTO equipment (
                barcode, name, variant, description, category, usage_instruction,
                image_path, tracking_type, total_quantity, available_quantity,
                min_stock_level, availability_status, is_borrowable, location, class
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """, (barcode, name, variant, description, category, usage, final_image_path,
              tracking_type, total_qty, avail_qty, min_stock, avail_status, is_borrowable, 
              location, equip_class))
        
        conn.commit()
        conn.close()
        
        messagebox.showinfo("Success", "Equipment '{}' added successfully!".format(name))
        dialog.destroy()
        show_equipment_management(parent, admin_email)
        
    except Exception as e:
        messagebox.showerror("Error", "Failed to add equipment: {}".format(str(e)))

def show_edit_equipment_dialog(parent, admin_email, equip_id, equip_data):
    dialog = Toplevel(parent)
    dialog.title("Edit Equipment")
    dialog.geometry("600x750")  # Same size as add equipment dialog
    dialog.configure(bg="#f8f9fa")
    dialog.transient(parent)
    dialog.grab_set()
    dialog.resizable(True, True)
    
    barcode = equip_data['barcode']
    name = equip_data['name']
    description = equip_data['description']
    category = equip_data['category']
    usage = equip_data['usage_instruction']
    image_path = equip_data['image_path']
    tracking_type = equip_data['tracking_type']
    total_qty = equip_data['total_quantity']
    avail_qty = equip_data['available_quantity']
    min_stock = equip_data['min_stock_level']
    avail_status = equip_data['availability_status']
    is_borrowable = equip_data['is_borrowable']
    variant = equip_data['variant']
    location = equip_data['location']
    equip_class = equip_data['class']
    
    # Main container
    main_frame = Frame(dialog, bg="#f8f9fa")
    main_frame.pack(fill="both", expand=True, padx=20, pady=20)
    
    # Header
    header_frame = Frame(main_frame, bg="#f8f9fa", height=80)
    header_frame.pack(fill="x", pady=(0, 20))
    header_frame.pack_propagate(False)
    
    title = f"Edit Equipment - {name}" + (f" ({variant})" if variant else "")
    tk.Label(header_frame, text=title, font=("Arial", 16, "bold"), 
             bg="#f8f9fa", fg="#2c5530").pack(expand=True)
    
    tk.Label(header_frame, text="Update the equipment details below", 
             font=("Arial", 10), bg="#f8f9fa", fg="#666").pack(pady=(0, 10))
    
    # Create scrollable frame
    canvas_frame = Frame(main_frame, bg="#f8f9fa")
    canvas_frame.pack(fill="both", expand=True)
    
    canvas = tk.Canvas(canvas_frame, bg="#f8f9fa", highlightthickness=0)
    scrollbar = ttk.Scrollbar(canvas_frame, orient="vertical", command=canvas.yview)
    scrollable_frame = Frame(canvas, bg="#f8f9fa")
    
    scrollable_frame.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
    canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
    canvas.configure(yscrollcommand=scrollbar.set)
    
    canvas.pack(side="left", fill="both", expand=True)
    scrollbar.pack(side="right", fill="y")
    
    def on_mousewheel(event):
        canvas.yview_scroll(int(-1*(event.delta/120)), "units")
    canvas.bind_all("<MouseWheel>", on_mousewheel)
    
    # Form fields
    fields = {}
    
    # Basic Information Section - WITH BORDER
    basic_card = Frame(scrollable_frame, bg="white", relief="solid", bd=1)
    basic_card.pack(fill="x", pady=(0, 20))
    
    basic_header = Frame(basic_card, bg="#e8f5e9", height=35)
    basic_header.pack(fill="x")
    basic_header.pack_propagate(False)
    
    tk.Label(basic_header, text="📋 Basic Information", font=("Arial", 11, "bold"), 
             bg="#e8f5e9", fg="#2c5530").pack(side="left", padx=12, pady=8)
    
    basic_content = Frame(basic_card, bg="white")
    basic_content.pack(fill="x", padx=15, pady=15)
    
    # Barcode (read-only)
    barcode_frame = Frame(basic_content, bg="white")
    barcode_frame.pack(fill="x", pady=8)
    
    tk.Label(barcode_frame, text="Barcode", font=("Arial", 10, "bold"), 
            bg="white", fg="#495057", width=15, anchor="w").pack(side="left")
    
    tk.Label(barcode_frame, text=barcode, font=("Arial", 10), bg="#f8f9fa", 
            fg="#666", width=45, anchor="w", relief="solid", bd=1, padx=10).pack(side="left", padx=10)
    
    # Editable fields
    form_fields = [
        ("Name *", "name", name),
        ("Variant", "variant", variant),
        ("Description *", "description", description),
        ("Category *", "category", category),
        ("Usage Instruction *", "usage", usage),
    ]
    
    for label_text, field_name, default_value in form_fields:
        field_frame = Frame(basic_content, bg="white")
        field_frame.pack(fill="x", pady=8)
        
        tk.Label(field_frame, text=label_text, font=("Arial", 10, "bold"), 
                bg="white", fg="#495057", width=15, anchor="w").pack(side="left")
        
        if field_name == "category":
            # Create dropdown for category
            category_var = StringVar(dialog)
            category_var.set(default_value if default_value else "Medical Equipment")
            
            category_menu = OptionMenu(field_frame, category_var, "Medical Equipment", "Laboratory Equipment")
            category_menu.config(font=("Arial", 10), width=42, bg="white", relief="solid", bd=1)
            category_menu.pack(side="left", padx=10, fill="x", expand=True)
            fields[field_name] = category_var
        
        elif field_name in ["description", "usage"]:
            # Create larger text area for description and usage
            text_frame = Frame(field_frame, bg="white")
            text_frame.pack(side="left", padx=10, fill="x", expand=True)
            
            text_widget = Text(text_frame, font=("Arial", 10), width=45, height=4, 
                              wrap="word", relief="solid", bd=1, bg="white")
            
            # Add scrollbar
            scrollbar = ttk.Scrollbar(text_frame, command=text_widget.yview)
            text_widget.config(yscrollcommand=scrollbar.set)
            
            text_widget.pack(side="left", fill="both", expand=True)
            scrollbar.pack(side="right", fill="y")
            
            # Insert default value for edit dialog
            if default_value:
                text_widget.insert("1.0", default_value)
            
            fields[field_name] = text_widget
        
        else:
            entry = Entry(field_frame, font=("Arial", 10), width=45, 
                         relief="solid", bd=1, bg="white")
            if default_value:
                entry.insert(0, default_value)
            entry.pack(side="left", padx=10, fill="x", expand=True)
            fields[field_name] = entry
    
    # Location and Class
    location_class_frame = Frame(basic_content, bg="white")
    location_class_frame.pack(fill="x", pady=10)
    
    # Location
    location_left = Frame(location_class_frame, bg="white")
    location_left.pack(side="left", padx=(0, 20), fill="x", expand=True)
    
    tk.Label(location_left, text="Location *", font=("Arial", 10, "bold"), 
            bg="white", fg="#495057", anchor="w").pack(anchor="w")
    
    location_var = StringVar(dialog)
    location_var.set(location)
    location_menu = OptionMenu(location_left, location_var, 
                              "central supply room", "anatomy laboratory", 
                              "nutrition laboratory", "skills laboratory", "or-dr complex")
    location_menu.config(font=("Arial", 10), width=25, bg="white", relief="solid", bd=1)
    location_menu.pack(pady=(5, 0), fill="x")
    fields['location'] = location_var
    
    # Class
    class_right = Frame(location_class_frame, bg="white")
    class_right.pack(side="left", fill="x", expand=True)
    
    tk.Label(class_right, text="Class *", font=("Arial", 10, "bold"), 
            bg="white", fg="#495057", anchor="w").pack(anchor="w")
    
    class_var = StringVar(dialog)
    class_var.set(equip_class)
    class_menu = OptionMenu(class_right, class_var, 
                           "consumable", "plastic", "apparatus", "wooden", "glass", "metal")
    class_menu.config(font=("Arial", 10), width=25, bg="white", relief="solid", bd=1)
    class_menu.pack(pady=(5, 0), fill="x")
    fields['class'] = class_var
    
    # Inventory Settings Section - WITH BORDER
    inventory_card = Frame(scrollable_frame, bg="white", relief="solid", bd=1)
    inventory_card.pack(fill="x", pady=(0, 20))
    
    inventory_header = Frame(inventory_card, bg="#e3f2fd", height=35)
    inventory_header.pack(fill="x")
    inventory_header.pack_propagate(False)
    
    tk.Label(inventory_header, text="📊 Inventory Settings", font=("Arial", 11, "bold"), 
             bg="#e3f2fd", fg="#1565c0").pack(side="left", padx=12, pady=8)
    
    inventory_content = Frame(inventory_card, bg="white")
    inventory_content.pack(fill="x", padx=15, pady=15)
    
    # Tracking Type
    tracking_frame = Frame(inventory_content, bg="white")
    tracking_frame.pack(fill="x", pady=8)
    
    tk.Label(tracking_frame, text="Tracking Type *", font=("Arial", 10, "bold"), 
            bg="white", fg="#495057", width=15, anchor="w").pack(side="left")
    
    tracking_var = StringVar(value=tracking_type)
    tracking_radio_frame = Frame(tracking_frame, bg="white")
    tracking_radio_frame.pack(side="left", padx=10, fill="x", expand=True)
    
    Radiobutton(tracking_radio_frame, text="Individual (Unique items)", 
                variable=tracking_var, value="individual", bg="white", 
                font=("Arial", 10), selectcolor="#e8f5e9", 
                activebackground="white").pack(anchor="w", pady=2)
    Radiobutton(tracking_radio_frame, text="Quantity (Bulk items)", 
                variable=tracking_var, value="quantity", bg="white", 
                font=("Arial", 10), selectcolor="#e8f5e9",
                activebackground="white").pack(anchor="w", pady=2)
    fields['tracking_type'] = tracking_var
    
    # Quantity Fields
    quantity_grid = Frame(inventory_content, bg="white")
    quantity_grid.pack(fill="x", pady=10)
    
    # Total Quantity
    total_qty_frame = Frame(quantity_grid, bg="white")
    total_qty_frame.pack(side="left", padx=(0, 30), fill="x", expand=True)
    
    tk.Label(total_qty_frame, text="Total Quantity *", font=("Arial", 10, "bold"), 
            bg="white", fg="#495057", anchor="w").pack(anchor="w")
    
    total_qty_entry = Entry(total_qty_frame, font=("Arial", 10), width=15,
                           relief="solid", bd=1, bg="white", justify="center")
    total_qty_entry.insert(0, str(total_qty))
    total_qty_entry.pack(pady=(5, 0), fill="x")
    fields['total_quantity'] = total_qty_entry
    
    # Available Quantity
    avail_frame = Frame(quantity_grid, bg="white")
    avail_frame.pack(side="left", padx=(0, 30), fill="x", expand=True)
    
    tk.Label(avail_frame, text="Available Quantity *", font=("Arial", 10, "bold"), 
            bg="white", fg="#495057", anchor="w").pack(anchor="w")
    
    avail_qty_entry = Entry(avail_frame, font=("Arial", 10), width=15,
                           relief="solid", bd=1, bg="white", justify="center")
    avail_qty_entry.insert(0, str(avail_qty))
    avail_qty_entry.pack(pady=(5, 0), fill="x")
    fields['available_quantity'] = avail_qty_entry
    
    # Min Stock Level
    min_stock_frame = Frame(quantity_grid, bg="white")
    min_stock_frame.pack(side="left", fill="x", expand=True)
    
    tk.Label(min_stock_frame, text="Min Stock Level *", font=("Arial", 10, "bold"), 
            bg="white", fg="#495057", anchor="w").pack(anchor="w")
    
    min_stock_entry = Entry(min_stock_frame, font=("Arial", 10), width=15,
                           relief="solid", bd=1, bg="white", justify="center")
    min_stock_entry.insert(0, str(min_stock))
    min_stock_entry.pack(pady=(5, 0), fill="x")
    fields['min_stock_level'] = min_stock_entry
    
    # Status
    status_frame = Frame(inventory_content, bg="white")
    status_frame.pack(fill="x", pady=8)
    
    tk.Label(status_frame, text="Status *", font=("Arial", 10, "bold"), 
            bg="white", fg="#495057", width=15, anchor="w").pack(side="left")
    
    status_var = StringVar(value=avail_status)
    status_menu = OptionMenu(status_frame, status_var, "Available", "Unavailable", "Reserved")
    status_menu.config(font=("Arial", 10), width=42, bg="white", relief="solid", bd=1)
    status_menu.pack(side="left", padx=10, fill="x", expand=True)
    fields['availability_status'] = status_var
    
    # Borrowing Settings - WITH BORDER
    borrow_card = Frame(scrollable_frame, bg="white", relief="solid", bd=1)
    borrow_card.pack(fill="x", pady=(0, 20))
    
    borrow_header = Frame(borrow_card, bg="#fff3cd", height=35)
    borrow_header.pack(fill="x")
    borrow_header.pack_propagate(False)
    
    tk.Label(borrow_header, text="🔄 Borrowing Settings", font=("Arial", 11, "bold"), 
             bg="#fff3cd", fg="#856404").pack(side="left", padx=12, pady=8)
    
    borrow_content = Frame(borrow_card, bg="white")
    borrow_content.pack(fill="x", padx=15, pady=15)
    
    borrow_var = IntVar(value=is_borrowable)
    Checkbutton(borrow_content, text="Borrowable by students/faculty", 
                variable=borrow_var, bg="white", font=("Arial", 10),
                activebackground="white", selectcolor="#e8f5e9").pack(anchor="w")
    fields['is_borrowable'] = borrow_var
    
    # Image Upload Section - WITH BORDER
    image_card = Frame(scrollable_frame, bg="white", relief="solid", bd=1)
    image_card.pack(fill="x", pady=(0, 20))
    
    image_header = Frame(image_card, bg="#f8d7da", height=35)
    image_header.pack(fill="x")
    image_header.pack_propagate(False)
    
    tk.Label(image_header, text="🖼️ Equipment Image", font=("Arial", 11, "bold"), 
             bg="#f8d7da", fg="#721c24").pack(side="left", padx=12, pady=8)
    
    image_content = Frame(image_card, bg="white")
    image_content.pack(fill="x", padx=15, pady=15)
    
    # Image preview - with border
    image_preview_frame = Frame(image_content, bg="#e9ecef", width=300, height=200, relief="solid", borderwidth=1)
    image_preview_frame.pack(pady=8)
    image_preview_frame.pack_propagate(False)
    
    preview_label = Label(image_preview_frame, text="No image", font=("Arial", 9), bg="#e9ecef", fg="#6c757d", justify="center")
    preview_label.pack(expand=True)
    
    # Load existing image if available
    if image_path and os.path.exists(image_path):
        try:
            existing_img = Image.open(image_path)
            fields['original_image'] = existing_img
            
            img_copy = existing_img.copy()
            img_copy.thumbnail((280, 180), Image.Resampling.LANCZOS)
            photo = ImageTk.PhotoImage(img_copy)
            
            preview_label.configure(image=photo, text="")
            preview_label.image = photo
        except Exception as e:
            print("Error loading existing image: {}".format(str(e)))
    else:
        fields['original_image'] = None
    
    fields['image_preview_label'] = preview_label
    fields['image_path'] = image_path
    fields['new_image_path'] = None
    
    def browse_image():
        file_path = filedialog.askopenfilename(
            title="Select Equipment Image",
            filetypes=[
                ("Image files", "*.jpg *.jpeg *.png *.gif *.bmp"),
                ("All files", "*.*")
            ]
        )
        
        if file_path:
            try:
                img = Image.open(file_path)
                fields['original_image'] = img
                
                img_copy = img.copy()
                img_copy.thumbnail((280, 180), Image.Resampling.LANCZOS)
                photo = ImageTk.PhotoImage(img_copy)
                
                preview_label.configure(image=photo, text="")
                preview_label.image = photo
                
                fields['new_image_path'] = file_path
                
            except Exception as e:
                messagebox.showerror("Error", "Failed to load image: {}".format(str(e)))
    
    def remove_image():
        preview_label.configure(image="", text="No image")
        preview_label.image = None
        fields['original_image'] = None
        fields['new_image_path'] = "REMOVE"
    
    image_btn_frame = Frame(image_content, bg="white")
    image_btn_frame.pack(pady=8)
    
    Button(image_btn_frame, text="📁 Change Image", font=("Arial", 10), 
           bg="#007bff", fg="white", relief="flat", padx=18, pady=6, cursor="hand2",
           command=browse_image).pack(side="left", padx=5)
    
    if image_path:
        Button(image_btn_frame, text="🗑️ Remove Image", font=("Arial", 10), 
               bg="#dc3545", fg="white", relief="flat", padx=18, pady=6, cursor="hand2",
               command=remove_image).pack(side="left", padx=5)
    
    # Action buttons - WITH BORDER
    button_card = Frame(scrollable_frame, bg="white", relief="solid", bd=1)
    button_card.pack(fill="x", pady=(0, 10))
    
    button_content = Frame(button_card, bg="white")
    button_content.pack(fill="x", padx=15, pady=15)
    
    button_frame = Frame(button_content, bg="white")
    button_frame.pack(fill="x")
    
    # Cancel button
    Button(button_frame, text="✕ Cancel", font=("Arial", 11, "bold"), 
           bg="#6c757d", fg="white", relief="flat", padx=25, pady=10, cursor="hand2",
           command=dialog.destroy).pack(side="left", padx=10)
    
    # Save button
    Button(button_frame, text="💾 Save Changes", font=("Arial", 11, "bold"), 
           bg="#28a745", fg="white", relief="flat", padx=25, pady=10, cursor="hand2",
           command=lambda: save_equipment_changes(equip_id, fields, dialog, parent, admin_email)).pack(side="right", padx=10)

def save_equipment_changes(equip_id, fields, dialog, parent, admin_email):
    # Get field values
    name = fields["name"].get().strip()
    variant = fields["variant"].get().strip()
    category = fields["category"].get().strip()
    location = fields['location'].get()
    equip_class = fields['class'].get()
    tracking_type = fields['tracking_type'].get()
    is_borrowable = fields['is_borrowable'].get()
    
    # Handle Text widgets for description and usage
    if isinstance(fields["description"], Text):
        description = fields["description"].get("1.0", "end-1c").strip()
    else:
        description = fields["description"].get().strip()

    if isinstance(fields["usage"], Text):
        usage = fields["usage"].get("1.0", "end-1c").strip()
    else:
        usage = fields["usage"].get().strip()
    
    try:
        total_qty = int(fields['total_quantity'].get().strip())
        avail_qty = int(fields['available_quantity'].get().strip())
        min_stock = int(fields['min_stock_level'].get().strip())
    except ValueError:
        messagebox.showerror("Error", "Quantity values must be numbers")
        return
    
    avail_status = fields['availability_status'].get()
    new_image_path = fields.get('new_image_path')
    current_image_path = fields['image_path']
    
    # Validation
    if not all([name, description, category, usage]):
        messagebox.showerror("Error", "Please fill in all required fields (*)")
        return
    
    if avail_qty > total_qty:
        messagebox.showerror("Error", "Available quantity cannot exceed total quantity")
        return
    
    try:
        conn = get_db_connection()
        if conn is None:
            return
            
        cursor = conn.cursor()
        
        final_image_path = current_image_path
        
        # Handle image changes
        if new_image_path == "REMOVE":
            if current_image_path and os.path.exists(current_image_path):
                try:
                    os.remove(current_image_path)
                except:
                    pass
            final_image_path = None
            
        elif new_image_path and new_image_path != "REMOVE" and fields.get('original_image'):
            try:
                if not os.path.exists("equipment_images"):
                    os.makedirs("equipment_images")
                
                cursor.execute("SELECT barcode FROM equipment WHERE id = %s", (equip_id,))
                result = cursor.fetchone()
                if not result:
                    messagebox.showerror("Error", "Equipment not found")
                    conn.close()
                    return
                    
                barcode = result['barcode']
                
                file_extension = os.path.splitext(new_image_path)[1]
                if not file_extension:
                    file_extension = ".jpg"
                
                safe_barcode = barcode.replace("/", "_").replace("\\", "_").replace(" ", "_")
                safe_barcode = "".join(c for c in safe_barcode if c.isalnum() or c in "_-")
                
                timestamp = str(int(datetime.now().timestamp()))
                new_filename = f"equip_{safe_barcode}_{timestamp}{file_extension}"
                final_image_path = os.path.join("equipment_images", new_filename)
                
                if current_image_path and os.path.exists(current_image_path) and current_image_path != final_image_path:
                    try:
                        os.remove(current_image_path)
                    except:
                        pass
                
                fields['original_image'].save(final_image_path)
                print(f"Image updated: {final_image_path}")
                
            except Exception as e:
                print(f"Error updating image: {str(e)}")
                final_image_path = current_image_path
        
        # Update equipment
        cursor.execute("""
            UPDATE equipment SET
                name = %s, variant = %s, description = %s, category = %s, usage_instruction = %s,
                image_path = %s, tracking_type = %s, total_quantity = %s, available_quantity = %s,
                min_stock_level = %s, availability_status = %s, is_borrowable = %s, location = %s, class = %s
            WHERE id = %s
        """, (name, variant, description, category, usage, final_image_path,
              tracking_type, total_qty, avail_qty, min_stock, avail_status, is_borrowable, 
              location, equip_class, equip_id))
        
        conn.commit()
        conn.close()
        
        messagebox.showinfo("Success", "Equipment '{}' updated successfully!".format(name))
        dialog.destroy()
        show_equipment_management(parent, admin_email)
        
    except Exception as e:
        messagebox.showerror("Error", "Failed to update equipment: {}".format(str(e)))

if __name__ == "__main__":
    root = tk.Tk()
    root.title("Equipment Management with Barcode Generation - MySQL Version")
    root.geometry("1920x1080")
    # Initialize database first
    init_database()
    show_equipment_management(root, "admin@nursing.com")
    root.mainloop()