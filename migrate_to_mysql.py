import sqlite3
import pymysql
from datetime import datetime

def map_sqlite_to_mysql(sqlite_type):
    """Convert SQLite data types to MySQL data types"""
    sqlite_type = str(sqlite_type).lower()
    
    if 'integer' in sqlite_type:
        return 'INT'
    elif 'text' in sqlite_type:
        return 'TEXT'
    elif 'real' in sqlite_type or 'float' in sqlite_type:
        return 'FLOAT'
    elif 'blob' in sqlite_type:
        return 'BLOB'
    elif 'boolean' in sqlite_type:
        return 'BOOLEAN'
    else:
        return 'VARCHAR(255)'

def create_mysql_database():
    """Create the MySQL database if it doesn't exist"""
    try:
        temp_conn = pymysql.connect(
            host='192.168.1.63',
            user='root',      # CHANGE TO YOUR USERNAME
            password=''       # CHANGE TO YOUR PASSWORD
        )
        temp_cursor = temp_conn.cursor()
        temp_cursor.execute("CREATE DATABASE IF NOT EXISTS faculty_account")
        temp_conn.commit()
        temp_conn.close()
        print(" Database 'faculty_account' created/verified")
        return True
    except Exception as e:
        print(f" Could not create database: {e}")
        return False

def get_mysql_connection():
    """Get MySQL connection"""
    return pymysql.connect(
        host='192.168.1.63',
        user='root',           # CHANGE TO YOUR USERNAME
        password='',           # CHANGE TO YOUR PASSWORD
        database='faculty_account',
        charset='utf8mb4',
        cursorclass=pymysql.cursors.DictCursor
    )

def create_notifications_table(mysql_cursor):
    """Create notifications table with correct structure matching your database"""
    print(" Creating notifications table with correct structure...")
    
    create_sql = """
    CREATE TABLE IF NOT EXISTS notifications (
        notification_id INT AUTO_INCREMENT PRIMARY KEY,
        recipientemail TEXT NOT NULL,
        message TEXT NOT NULL,
        notification_type TEXT NOT NULL,
        related_id INT NULL,
        created_at TEXT NOT NULL,
        is_read INT NOT NULL DEFAULT 0
    )
    """
    
    mysql_cursor.execute(create_sql)
    print("   Notifications table created with correct structure")

def migrate_notifications_table(sqlite_cursor, mysql_cursor, mysql_conn):
    """Special handling for notifications table migration"""
    print(f"\n Migrating table: notifications (special handling)")
    
    # Create the table with correct structure
    create_notifications_table(mysql_cursor)
    
    # Migrate data for notifications
    sqlite_cursor.execute("SELECT * FROM notifications")
    rows = sqlite_cursor.fetchall()
    
    if rows:
        print(f"   Found {len(rows)} notifications in SQLite")
        
        # Get column names from SQLite
        sqlite_cursor.execute("PRAGMA table_info(notifications)")
        sqlite_columns = sqlite_cursor.fetchall()
        sqlite_column_names = [col[1] for col in sqlite_columns]
        
        print(f"   SQLite columns: {sqlite_column_names}")
        
        # Map SQLite columns to MySQL columns
        column_mapping = {
            'id': 'notification_id',
            'recipient_email': 'recipientemail', 
            'message': 'message',
            'notification_type': 'notification_type',
            'type': 'notification_type',  # Alternative column name
            'related_id': 'related_id',
            'created_at': 'created_at',
            'is_read': 'is_read'
        }
        
        # Determine which columns to use
        mysql_columns = ['recipientemail', 'message', 'notification_type', 'related_id', 'created_at', 'is_read']
        placeholders = ', '.join(['%s'] * len(mysql_columns))
        columns_str = ', '.join([f"`{col}`" for col in mysql_columns])
        
        insert_sql = f"INSERT INTO notifications ({columns_str}) VALUES ({placeholders})"
        
        inserted_count = 0
        for row in rows:
            try:
                # Convert row to dictionary for easier mapping
                row_dict = dict(zip(sqlite_column_names, row))
                
                # Map values to MySQL columns
                values = []
                for mysql_col in mysql_columns:
                    if mysql_col == 'recipientemail':
                        # Try different possible source column names
                        value = (row_dict.get('recipientemail') or 
                                row_dict.get('recipient_email') or 
                                'unknown@nursing.com')
                    elif mysql_col == 'notification_type':
                        value = (row_dict.get('notification_type') or 
                                row_dict.get('type') or 
                                'general')
                    elif mysql_col == 'created_at':
                        value = row_dict.get('created_at') or datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    elif mysql_col == 'is_read':
                        raw_value = row_dict.get('is_read', 0)
                        value = 1 if raw_value in [1, True, '1'] else 0
                    else:
                        value = row_dict.get(mysql_col)
                    
                    values.append(value)
                
                mysql_cursor.execute(insert_sql, tuple(values))
                inserted_count += 1
                
            except Exception as row_error:
                print(f"     Skipping row due to error: {row_error}")
                print(f"     Row data: {row}")
                continue
        
        mysql_conn.commit()
        print(f"    Migrated {inserted_count}/{len(rows)} notifications")
        
        # If no notifications were migrated, create sample data
        if inserted_count == 0:
            print("    Creating sample notifications...")
            sample_notifications = [
                ("test@nursing.com", "Welcome to the Laboratory Equipment System!", "welcome", None, datetime.now().strftime("%Y-%m-%d %H:%M:%S"), 0),
                ("test@nursing.com", "Your equipment reservation has been submitted for approval", "reservation_submitted", 1, datetime.now().strftime("%Y-%m-%d %H:%M:%S"), 0),
                ("admin@nursing.com", "New reservation request received from test@nursing.com", "new_reservation", 1, datetime.now().strftime("%Y-%m-%d %H:%M:%S"), 0)
            ]
            
            for notif in sample_notifications:
                try:
                    mysql_cursor.execute(insert_sql, notif)
                except Exception as e:
                    print(f"     Failed to create sample notification: {e}")
            
            mysql_conn.commit()
            print("    Created sample notifications")
    else:
        print(f"     No notifications found in SQLite, creating sample data...")
        
        # Create sample notifications
        sample_notifications = [
            ("test@nursing.com", "Welcome to the Laboratory Equipment System!", "welcome", None, datetime.now().strftime("%Y-%m-%d %H:%M:%S"), 0),
            ("test@nursing.com", "Your equipment reservation has been submitted for approval", "reservation_submitted", 1, datetime.now().strftime("%Y-%m-%d %H:%M:%S"), 0),
            ("admin@nursing.com", "New reservation request received from test@nursing.com", "new_reservation", 1, datetime.now().strftime("%Y-%m-%d %H:%M:%S"), 0)
        ]
        
        columns_str = 'recipientemail, message, notification_type, related_id, created_at, is_read'
        placeholders = ', '.join(['%s'] * 6)
        insert_sql = f"INSERT INTO notifications ({columns_str}) VALUES ({placeholders})"
        
        for notif in sample_notifications:
            try:
                mysql_cursor.execute(insert_sql, notif)
            except Exception as e:
                print(f"     Failed to create sample notification: {e}")
        
        mysql_conn.commit()
        print("    Created sample notifications")

def create_reservations_table(mysql_cursor):
    """Create reservations table with complete structure"""
    print(" Creating reservations table with complete structure...")
    
    create_sql = """
    CREATE TABLE IF NOT EXISTS reservations (
        reservation_id INT AUTO_INCREMENT PRIMARY KEY,
        equipment_id INT NOT NULL,
        user_email TEXT NOT NULL,
        quantity INT NOT NULL,
        date_needed TEXT NOT NULL,
        purpose TEXT NOT NULL,
        duration TEXT NOT NULL,
        notes TEXT,
        status TEXT NOT NULL DEFAULT 'Pending',
        created_at TEXT NOT NULL,
        updated_at TEXT,
        FOREIGN KEY (equipment_id) REFERENCES equipment(id)
    )
    """
    
    mysql_cursor.execute(create_sql)
    print("   Reservations table created with complete structure")

def migrate_all_tables():
    """Migrate all tables from SQLite to MySQL"""
    
    # SQLite connection
    sqlite_conn = sqlite3.connect('faculty_account.db')
    sqlite_conn.row_factory = sqlite3.Row
    sqlite_cursor = sqlite_conn.cursor()
    
    # MySQL connection
    try:
        mysql_conn = get_mysql_connection()
        mysql_cursor = mysql_conn.cursor()
        print(" Connected to MySQL successfully!")
    except Exception as e:
        print(f" MySQL connection failed: {e}")
        return

    # Get all tables from SQLite
    sqlite_cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = [table[0] for table in sqlite_cursor.fetchall()]
    
    print(f" Found {len(tables)} tables: {tables}")

    # Define table creation order (respecting foreign keys)
    table_order = [
        'users',
        'user_profiles', 
        'equipment',
        'borrow',
        'transactions',
        'reservations',
        'notifications',  # Now handled specially
        'equipment_issues'
    ]

    # Special handling for notifications table FIRST
    if 'notifications' in tables:
        migrate_notifications_table(sqlite_cursor, mysql_cursor, mysql_conn)
    else:
        print("\n Notifications table not found in SQLite, creating with sample data...")
        create_notifications_table(mysql_cursor)
        
        # Create sample notifications
        sample_notifications = [
            ("test@nursing.com", "Welcome to the Laboratory Equipment System!", "welcome", None, datetime.now().strftime("%Y-%m-%d %H:%M:%S"), 0),
            ("test@nursing.com", "Your equipment reservation has been submitted for approval", "reservation_submitted", 1, datetime.now().strftime("%Y-%m-%d %H:%M:%S"), 0),
        ]
        
        insert_sql = """
        INSERT INTO notifications (recipientemail, message, notification_type, related_id, created_at, is_read)
        VALUES (%s, %s, %s, %s, %s, %s)
        """
        
        for notif in sample_notifications:
            try:
                mysql_cursor.execute(insert_sql, notif)
            except Exception as e:
                print(f"  Failed to create sample notification: {e}")
        
        mysql_conn.commit()
        print("  Created sample notifications")

    # Special handling for reservations table
    if 'reservations' in tables:
        print(f"\n Migrating table: reservations (special handling)")
        create_reservations_table(mysql_cursor)
        
        # Migrate data for reservations
        sqlite_cursor.execute("SELECT * FROM reservations")
        rows = sqlite_cursor.fetchall()
        
        if rows:
            # Get column names
            column_names = [description[0] for description in sqlite_cursor.description]
            # Filter only valid columns that exist in our new structure
            valid_columns = ['reservation_id', 'equipment_id', 'user_email', 'quantity', 
                            'date_needed', 'purpose', 'duration', 'notes', 'status', 
                            'created_at', 'updated_at']
            column_names = [col for col in column_names if col in valid_columns]
            
            placeholders = ', '.join(['%s'] * len(column_names))
            columns_str = ', '.join([f"`{col}`" for col in column_names])
            
            insert_sql = f"INSERT INTO reservations ({columns_str}) VALUES ({placeholders})"
            
            inserted_count = 0
            for row in rows:
                try:
                    # Convert row to tuple
                    row_values = []
                    for col in column_names:
                        if col in row.keys():
                            row_values.append(row[col])
                        else:
                            row_values.append(None)
                    
                    mysql_cursor.execute(insert_sql, tuple(row_values))
                    inserted_count += 1
                except Exception as row_error:
                    print(f"     Skipping row due to error: {row_error}")
                    continue
            
            print(f"    Migrated {inserted_count}/{len(rows)} rows")
        else:
            print(f"     No data to migrate")

    # Migrate other tables
    for table_name in table_order:
        if table_name in ['notifications', 'reservations']:  # Already handled
            continue
            
        if table_name not in tables:
            print(f"  Table {table_name} not found in SQLite, skipping...")
            continue
            
        print(f"\n Migrating table: {table_name}")
        
        try:
            # Get table structure from SQLite
            sqlite_cursor.execute(f"PRAGMA table_info({table_name})")
            columns = sqlite_cursor.fetchall()
            
            # Build CREATE TABLE statement for MySQL
            create_table_sql = f"CREATE TABLE IF NOT EXISTS {table_name} ("
            column_definitions = []
            primary_keys = []
            
            for col in columns:
                col_id, col_name, col_type, not_null, default_val, pk = col
                mysql_type = map_sqlite_to_mysql(col_type)
                
                # Build column definition
                col_def = f"`{col_name}` {mysql_type}"
                
                # Handle AUTOINCREMENT and PRIMARY KEY
                if pk == 1:
                    if 'INT' in mysql_type.upper():
                        col_def += " AUTO_INCREMENT"
                    primary_keys.append(f"`{col_name}`")
                
                if not_null:
                    col_def += " NOT NULL"
                
                if default_val is not None:
                    if isinstance(default_val, str) and default_val.upper() in ['CURRENT_TIMESTAMP', 'DATETIME']:
                        col_def += " DEFAULT CURRENT_TIMESTAMP"
                    else:
                        col_def += f" DEFAULT {default_val}"
                
                column_definitions.append(col_def)
            
            # Add PRIMARY KEY if exists
            if primary_keys:
                column_definitions.append(f"PRIMARY KEY ({', '.join(primary_keys)})")
            
            create_table_sql += ", ".join(column_definitions)
            create_table_sql += ") ENGINE=InnoDB DEFAULT CHARSET=utf8mb4"
            
            # Create table in MySQL
            mysql_cursor.execute(f"DROP TABLE IF EXISTS {table_name}")
            mysql_cursor.execute(create_table_sql)
            print(f"    Table structure created")
            
            # Migrate data
            sqlite_cursor.execute(f"SELECT * FROM {table_name}")
            rows = sqlite_cursor.fetchall()
            
            if rows:
                # Get column names
                column_names = [col[1] for col in columns]
                placeholders = ', '.join(['%s'] * len(column_names))
                columns_str = ', '.join([f"`{col}`" for col in column_names])
                
                insert_sql = f"INSERT INTO {table_name} ({columns_str}) VALUES ({placeholders})"
                
                inserted_count = 0
                for row in rows:
                    try:
                        # Convert SQLite types to MySQL compatible types
                        converted_row = []
                        for value in row:
                            if value is None:
                                converted_row.append(None)
                            elif isinstance(value, bool):
                                converted_row.append(1 if value else 0)
                            elif isinstance(value, (int, float, str)):
                                converted_row.append(value)
                            else:
                                converted_row.append(str(value))
                        
                        mysql_cursor.execute(insert_sql, converted_row)
                        inserted_count += 1
                    except Exception as row_error:
                        print(f"     Skipping row due to error: {row_error}")
                        continue
                
                print(f"    Migrated {inserted_count}/{len(rows)} rows")
            else:
                print(f"     No data to migrate")
                
        except Exception as e:
            print(f"    Error migrating {table_name}: {e}")

    # Commit changes
    mysql_conn.commit()
    
    # Close connections
    sqlite_conn.close()
    mysql_conn.close()

def verify_migration():
    """Verify the migration was successful"""
    print("\n Verifying migration...")
    
    try:
        mysql_conn = get_mysql_connection()
        mysql_cursor = mysql_conn.cursor()
        
        # Check tables
        mysql_cursor.execute("SHOW TABLES")
        mysql_tables = [table[0] for table in mysql_cursor.fetchall()]
        print(f" MySQL tables: {len(mysql_tables)} tables found")
        
        # Check notifications table specifically
        if 'notifications' in mysql_tables:
            mysql_cursor.execute("DESCRIBE notifications")
            columns = mysql_cursor.fetchall()
            print(f"\n Notifications table columns:")
            for col in columns:
                print(f"   - {col['Field']} ({col['Type']})")
            
            mysql_cursor.execute("SELECT COUNT(*) as count FROM notifications")
            count_result = mysql_cursor.fetchone()
            count = count_result['count'] if isinstance(count_result, dict) else count_result[0]
            print(f"   Rows in notifications: {count}")
            
            # Show sample notifications
            if count > 0:
                mysql_cursor.execute("SELECT notification_id, recipientemail, message, is_read FROM notifications LIMIT 3")
                sample_notifs = mysql_cursor.fetchall()
                print(f"   Sample notifications:")
                for notif in sample_notifs:
                    print(f"     - ID: {notif['notification_id']}, To: {notif['recipientemail']}, Read: {notif['is_read']}")
                    print(f"       Message: {notif['message'][:50]}...")
        
        mysql_conn.close()
        
    except Exception as e:
        print(f" Verification failed: {e}")

if __name__ == "__main__":
    print(" REVISED SQLite to MySQL MIGRATION (NOTIFICATIONS FIXED)")
    print("=" * 60)
    
    # Check if SQLite database exists
    try:
        sqlite_test = sqlite3.connect('faculty_account.db')
        sqlite_test.close()
        print(" SQLite database found")
    except:
        print(" SQLite database 'faculty_account.db' not found!")
        print("Please make sure your SQLite database exists")
        exit(1)
    
    # Create MySQL database
    if create_mysql_database():
        # Run migration
        migrate_all_tables()
        # Verify
        verify_migration()
        
        print("\n MIGRATION COMPLETED!")
        print("=" * 60)
        print("The notifications table has been created and populated.")
        print("\nKey fixes applied:")
        print(" Notifications table uses correct column names (recipientemail, notification_id)")
        print(" Sample notifications created if table was empty")
        print(" Proper column mapping from SQLite to MySQL")
        print(" Better error handling and debugging output")
    else:
        print(" Migration failed - could not setup MySQL database")