# test_build.py
from database_init import init_database, verify_database

print("=== Testing Database Setup ===")
init_database()
success = verify_database()
print(f"Database test: {'PASSED' if success else 'FAILED'}")
