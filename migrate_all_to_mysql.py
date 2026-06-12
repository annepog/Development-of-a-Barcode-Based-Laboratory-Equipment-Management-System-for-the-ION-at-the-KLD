import sqlite3
import pymysql
from datetime import datetime
import pymysql.cursors


# For MAIN SERVER configuration
DB_CONFIG = {
    'host': 'localhost',
    'user': 'root',           # or your MySQL username
    'password': '',           # no password
    'database': 'faculty_account',
    'charset': 'utf8mb4',
}

def get_mysql_connection():
    """Get MySQL database connection using main server config"""
    try:
        conn = pymysql.connect(**DB_CONFIG)
        return conn
    except Exception as e:
        print(f"MySQL connection failed: {e}")
        return None

def create_mysql_database():
    """Create database if it doesn't exist"""
    try:
        # Create connection without database specified
        temp_config = DB_CONFIG.copy()
        temp_config.pop('database', None)  # Remove database from config
        
        temp_conn = pymysql.connect(**temp_config)
        temp_cursor = temp_conn.cursor()
        temp_cursor.execute("CREATE DATABASE IF NOT EXISTS faculty_account")
        temp_conn.commit()
        temp_conn.close()
        print("✅ Database 'faculty_account' created/verified")
        return True
    except Exception as e:
        print(f"❌ Could not create database: {e}")
        return False

def create_tables(mysql_cursor):
    """Create all tables with correct schema"""
    
    print("\n🗃️ Creating tables...")
    
    # Users table
    users_table = """
    CREATE TABLE IF NOT EXISTS users (
        id INT AUTO_INCREMENT PRIMARY KEY,
        email VARCHAR(255) NOT NULL UNIQUE,
        password VARCHAR(255) NOT NULL,
        role VARCHAR(50) NOT NULL DEFAULT 'faculty',
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """
    
    # User profiles table
    user_profiles_table = """
    CREATE TABLE IF NOT EXISTS user_profiles (
        id INT AUTO_INCREMENT PRIMARY KEY,
        email VARCHAR(255) NOT NULL UNIQUE,
        first_name VARCHAR(100),
        last_name VARCHAR(100),
        department VARCHAR(100),
        contact_number VARCHAR(20),
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (email) REFERENCES users(email) ON DELETE CASCADE
    )
    """
    
    # Equipment table
    equipment_table = """
    CREATE TABLE IF NOT EXISTS equipment (
        id INT AUTO_INCREMENT PRIMARY KEY,
        name VARCHAR(255) NOT NULL,
        variant VARCHAR(255),
        barcode VARCHAR(255) UNIQUE,
        description TEXT,
        tracking_type VARCHAR(50) DEFAULT 'individual',
        available_quantity INT DEFAULT 0,
        total_quantity INT DEFAULT 0,
        availability_status VARCHAR(50) DEFAULT 'Available',
        is_borrowable TINYINT(1) DEFAULT 1,
        is_archived TINYINT(1) DEFAULT 0,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """
    
    # Borrow table
    borrow_table = """
    CREATE TABLE IF NOT EXISTS borrow (
        id INT AUTO_INCREMENT PRIMARY KEY,
        equipment_id INT NOT NULL,
        user_email VARCHAR(255) NOT NULL,
        quantity INT NOT NULL,
        borrow_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        return_date TIMESTAMP NULL,
        status VARCHAR(50) DEFAULT 'Borrowed',
        notes TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (equipment_id) REFERENCES equipment(id),
        FOREIGN KEY (user_email) REFERENCES users(email)
    )
    """
    
    # Reservations table
    reservations_table = """
    CREATE TABLE IF NOT EXISTS reservations (
        reservation_id INT AUTO_INCREMENT PRIMARY KEY,
        equipment_id INT NOT NULL,
        user_email VARCHAR(255) NOT NULL,
        quantity INT NOT NULL,
        date_needed DATE NOT NULL,
        purpose TEXT NOT NULL,
        duration VARCHAR(100) NOT NULL,
        notes TEXT,
        status VARCHAR(50) NOT NULL DEFAULT 'Pending',
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (equipment_id) REFERENCES equipment(id),
        FOREIGN KEY (user_email) REFERENCES users(email)
    )
    """
    
    # Transactions table
    transactions_table = """
    CREATE TABLE IF NOT EXISTS transactions (
        id INT AUTO_INCREMENT PRIMARY KEY,
        equipment_id INT NOT NULL,
        user_email VARCHAR(255) NOT NULL,
        transaction_type VARCHAR(50) NOT NULL,
        quantity INT NOT NULL,
        transaction_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        notes TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (equipment_id) REFERENCES equipment(id),
        FOREIGN KEY (user_email) REFERENCES users(email)
    )
    """
    
    # Execute table creation
    tables = [
        ("users", users_table),
        ("user_profiles", user_profiles_table),
        ("equipment", equipment_table),
        ("borrow", borrow_table),
        ("reservations", reservations_table),
        ("transactions", transactions_table)
    ]
    
    for table_name, table_sql in tables:
        try:
            mysql_cursor.execute(f"DROP TABLE IF EXISTS {table_name}")
            mysql_cursor.execute(table_sql)
            print(f"✅ Created table: {table_name}")
        except Exception as e:
            print(f"❌ Error creating {table_name}: {e}")

def migrate_data(sqlite_cursor, mysql_cursor, mysql_conn):
    """Migrate data from SQLite to MySQL"""
    
    print("\n📦 Migrating data...")
    
    # Define the migration order
    migration_order = ['users', 'user_profiles', 'equipment', 'borrow', 'reservations', 'transactions']
    
    for table_name in migration_order:
        print(f"\n🔄 Migrating {table_name}...")
        
        try:
            # Get data from SQLite
            sqlite_cursor.execute(f"SELECT * FROM {table_name}")
            rows = sqlite_cursor.fetchall()
            column_names = [description[0] for description in sqlite_cursor.description]
            
            if not rows:
                print(f"   No data in {table_name}")
                continue
            
            # Special handling for each table
            if table_name == 'equipment':
                migrate_equipment_data(rows, column_names, mysql_cursor)
            elif table_name == 'reservations':
                migrate_reservations_data(rows, column_names, mysql_cursor)
            else:
                migrate_generic_table(table_name, rows, column_names, mysql_cursor)
                
            mysql_conn.commit()
            print(f"✅ Successfully migrated {table_name}")
            
        except Exception as e:
            print(f"❌ Error migrating {table_name}: {e}")
            continue

def migrate_equipment_data(rows, column_names, mysql_cursor):
    """Migrate equipment data with proper type conversion"""
    
    insert_sql = """
    INSERT INTO equipment (id, name, variant, barcode, description, tracking_type, 
                          available_quantity, total_quantity, availability_status, 
                          is_borrowable, is_archived, created_at)
    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
    """
    
    for row in rows:
        try:
            # Convert row to dictionary for easier access
            row_dict = dict(zip(column_names, row))
            
            # Handle is_borrowable conversion
            is_borrowable = 1  # Default to borrowable
            if 'is_borrowable' in row_dict and row_dict['is_borrowable'] is not None:
                if isinstance(row_dict['is_borrowable'], bool):
                    is_borrowable = 1 if row_dict['is_borrowable'] else 0
                elif isinstance(row_dict['is_borrowable'], int):
                    is_borrowable = 1 if row_dict['is_borrowable'] != 0 else 0
                elif isinstance(row_dict['is_borrowable'], str):
                    is_borrowable = 1 if row_dict['is_borrowable'].lower() in ['true', '1', 'yes'] else 0
            
            # Handle is_archived
            is_archived = 0
            if 'is_archived' in row_dict and row_dict['is_archived'] is not None:
                if isinstance(row_dict['is_archived'], bool):
                    is_archived = 1 if row_dict['is_archived'] else 0
                elif isinstance(row_dict['is_archived'], int):
                    is_archived = 1 if row_dict['is_archived'] != 0 else 0
            
            # Prepare values
            values = (
                row_dict.get('id'),
                row_dict.get('name', ''),
                row_dict.get('variant', ''),
                row_dict.get('barcode', ''),
                row_dict.get('description', ''),
                row_dict.get('tracking_type', 'individual'),
                row_dict.get('available_quantity', 0),
                row_dict.get('total_quantity', 0),
                row_dict.get('availability_status', 'Available'),
                is_borrowable,
                is_archived,
                row_dict.get('created_at', datetime.now())
            )
            
            mysql_cursor.execute(insert_sql, values)
            
        except Exception as e:
            print(f"   Skipping equipment row due to error: {e}")
            continue

def migrate_reservations_data(rows, column_names, mysql_cursor):
    """Migrate reservations data"""
    
    insert_sql = """
    INSERT INTO reservations (reservation_id, equipment_id, user_email, quantity, 
                            date_needed, purpose, duration, notes, status, created_at)
    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
    """
    
    for row in rows:
        try:
            row_dict = dict(zip(column_names, row))
            
            values = (
                row_dict.get('reservation_id'),
                row_dict.get('equipment_id'),
                row_dict.get('user_email', ''),
                row_dict.get('quantity', 1),
                row_dict.get('date_needed', datetime.now().date()),
                row_dict.get('purpose', ''),
                row_dict.get('duration', ''),
                row_dict.get('notes', ''),
                row_dict.get('status', 'Pending'),
                row_dict.get('created_at', datetime.now())
            )
            
            mysql_cursor.execute(insert_sql, values)
            
        except Exception as e:
            print(f"   Skipping reservation row due to error: {e}")
            continue

def migrate_generic_table(table_name, rows, column_names, mysql_cursor):
    """Migrate generic table data"""
    
    columns_str = ', '.join([f"`{col}`" for col in column_names])
    placeholders = ', '.join(['%s'] * len(column_names))
    insert_sql = f"INSERT INTO {table_name} ({columns_str}) VALUES ({placeholders})"
    
    for row in rows:
        try:
            # Convert any boolean values to integers for MySQL
            converted_row = []
            for value in row:
                if isinstance(value, bool):
                    converted_row.append(1 if value else 0)
                else:
                    converted_row.append(value)
            
            mysql_cursor.execute(insert_sql, converted_row)
            
        except Exception as e:
            print(f"   Skipping row in {table_name} due to error: {e}")
            continue

def verify_migration(mysql_cursor):
    """Verify the migration was successful"""
    
    print("\n🔍 Verifying migration...")
    
    # Check table counts
    tables = ['users', 'user_profiles', 'equipment', 'borrow', 'reservations', 'transactions']
    
    for table in tables:
        try:
            mysql_cursor.execute(f"SELECT COUNT(*) as count FROM {table}")
            result = mysql_cursor.fetchone()
            print(f"✅ {table}: {result['count']} rows")
            
        except Exception as e:
            print(f"❌ {table}: Error - {e}")

def main():
    print("🚀 SQLite to MySQL Migration - MAIN SERVER")
    print("=" * 50)
    
    # Check SQLite database
    try:
        sqlite_conn = sqlite3.connect('faculty_account.db')
        sqlite_conn.row_factory = sqlite3.Row
        sqlite_cursor = sqlite_conn.cursor()
        print("✅ SQLite database found")
    except Exception as e:
        print(f"❌ SQLite database error: {e}")
        return
    
    # Create MySQL database
    if not create_mysql_database():
        return
    
    # Get MySQL connection
    mysql_conn = get_mysql_connection()
    if not mysql_conn:
        print("❌ Failed to connect to MySQL")
        return
    
    mysql_cursor = mysql_conn.cursor()
    
    try:
        # Create tables
        create_tables(mysql_cursor)
        
        # Migrate data
        migrate_data(sqlite_cursor, mysql_cursor, mysql_conn)
        
        # Verify
        verify_migration(mysql_cursor)
        
        print("\n🎉 Migration completed successfully!")
        print("\n📝 Next steps:")
        print("1. Update your config_db.py to use this localhost configuration")
        print("2. Test your application")
        print("3. For clients, create a separate config with server IP")
        
    except Exception as e:
        print(f"❌ Migration failed: {e}")
    finally:
        sqlite_conn.close()
        mysql_conn.close()

if __name__ == "__main__":
    main()