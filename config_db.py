# config_db.py - FOR MAIN SERVER
import pymysql.cursors

# MAIN SERVER configuration - localhost, no password
DB_CONFIG = {
    'host': 'localhost',
    'user': 'root',           # Change if your MySQL username is different
    'password': '',           # Empty password
    'database': 'faculty_account',
    'charset': 'utf8mb4'
    # Remove cursorclass from here
}