# test_borrower_tracking.py
import sqlite3

def test_borrower_tracking():
    """Test if borrower tracking is working"""
    conn = sqlite3.connect("faculty_account.db")
    cursor = conn.cursor()
    
    print("Testing Borrower Tracking Fix")
    print("=" * 40)
    
    # Test 1: Check schema
    cursor.execute("PRAGMA table_info(borrow)")
    columns = [col[1] for col in cursor.fetchall()]
    required_columns = ['borrower_email', 'borrower_name', 'return_status']
    
    print("Schema Check:")
    for req_col in required_columns:
        if req_col in columns:
            print(f"  OK {req_col} - EXISTS")
        else:
            print(f"  ERROR {req_col} - MISSING")
    
    # Test 2: Check data
    print("\nData Check:")
    cursor.execute("SELECT COUNT(*) FROM borrow WHERE borrower_email IS NOT NULL")
    with_borrower = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM borrow")
    total = cursor.fetchone()[0]
    
    print(f"  Total borrow records: {total}")
    print(f"  Records with borrower info: {with_borrower}")
    
    if total > 0:
        print(f"  Success rate: {(with_borrower/total)*100:.1f}%")
    
    # Test 3: Sample borrower trends query
    print("\nBorrower Trends Test:")
    cursor.execute("""
        SELECT 
            borrower_name,
            COUNT(*) as total_borrowed,
            SUM(CASE WHEN return_time IS NOT NULL THEN 1 ELSE 0 END) as returned
        FROM borrow 
        WHERE borrower_name IS NOT NULL
        GROUP BY borrower_name
        LIMIT 5
    """)
    
    results = cursor.fetchall()
    if results:
        for name, borrowed, returned in results:
            print(f"  {name}: {borrowed} borrowed, {returned} returned")
    else:
        print("  No borrower data found - try borrowing some equipment first!")
    
    conn.close()
    
    if all(col in columns for col in required_columns):
        print("\nStatus: FIX WORKING")
    else:
        print("\nStatus: NEEDS FIXING")

if __name__ == "__main__":
    test_borrower_tracking()