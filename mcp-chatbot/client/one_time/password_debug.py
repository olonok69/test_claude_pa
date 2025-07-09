#!/usr/bin/env python3
"""
Password Debug Script - Debug bcrypt password verification issues

Usage:
    python password_debug.py
"""

import sqlite3
import bcrypt
import os

def debug_password_verification():
    """Debug password verification for existing users."""
    print("🔍 Password Verification Debug")
    print("=" * 40)
    
    db_path = "keys/users.db"
    if not os.path.exists(db_path):
        print("❌ SQLite database not found")
        return
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Get all users with their password hashes
        cursor.execute('SELECT username, password_hash FROM users')
        users = cursor.fetchall()
        
        # Test passwords that should work
        test_passwords = {
            'admin': ['very_Secure_p@ssword_123!', 'admin_password_change_immediately', 'admin'],
            'juan': ['Larisa1000@', 'juan_password'],
            'giovanni_romero': ['MrRomero2024!', 'giovanni_password'],
            'demo_user': ['StrongPassword123!', 'strong_password_123!', 'demo_password'],
            'test_admin': ['test_admin_123!']
        }
        
        for username, stored_hash in users:
            print(f"\n👤 Testing user: {username}")
            print(f"   Stored hash: {stored_hash[:30]}...")
            print(f"   Hash length: {len(stored_hash)}")
            print(f"   Hash prefix: {stored_hash[:4]}")
            
            if username in test_passwords:
                for test_password in test_passwords[username]:
                    try:
                        # Test bcrypt verification
                        is_valid = bcrypt.checkpw(test_password.encode(), stored_hash.encode())
                        print(f"   🔐 '{test_password}': {'✅ VALID' if is_valid else '❌ INVALID'}")
                        
                        if is_valid:
                            print(f"   🎉 WORKING PASSWORD FOUND: {test_password}")
                            break
                            
                    except Exception as e:
                        print(f"   ❌ Error testing '{test_password}': {str(e)}")
            else:
                print(f"   ⚠️  No test passwords defined for {username}")
        
        conn.close()
        
    except Exception as e:
        print(f"❌ Error: {str(e)}")

def create_test_password_hashes():
    """Create test password hashes to compare formats."""
    print("\n🧪 Creating test password hashes for comparison")
    print("=" * 50)
    
    test_passwords = [
        'very_Secure_p@ssword_123!',
        'Larisa1000@',
        'MrRomero2024!',
        'StrongPassword123!',
        'admin_password_change_immediately'
    ]
    
    for password in test_passwords:
        # Create a new hash
        new_hash = bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()
        
        print(f"Password: {password}")
        print(f"New hash: {new_hash}")
        
        # Test verification
        is_valid = bcrypt.checkpw(password.encode(), new_hash.encode())
        print(f"Verification: {'✅ SUCCESS' if is_valid else '❌ FAILED'}")
        print()

def fix_specific_user_password(username, new_password):
    """Fix password for a specific user."""
    print(f"🔧 Fixing password for user: {username}")
    
    try:
        db_path = "keys/users.db"
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Create new hash
        new_hash = bcrypt.hashpw(new_password.encode(), bcrypt.gensalt()).decode()
        
        # Update user
        cursor.execute('UPDATE users SET password_hash = ? WHERE username = ?', 
                      (new_hash, username))
        
        if cursor.rowcount > 0:
            conn.commit()
            print(f"✅ Password updated for {username}")
            print(f"   New password: {new_password}")
            
            # Test the new password
            cursor.execute('SELECT password_hash FROM users WHERE username = ?', (username,))
            stored_hash = cursor.fetchone()[0]
            
            is_valid = bcrypt.checkpw(new_password.encode(), stored_hash.encode())
            print(f"   Verification test: {'✅ SUCCESS' if is_valid else '❌ FAILED'}")
            
        else:
            print(f"❌ User {username} not found")
        
        conn.close()
        
    except Exception as e:
        print(f"❌ Error fixing password: {str(e)}")

def main():
    """Main debug function."""
    print("🔧 Password Verification Debug Tool")
    print("=" * 50)
    
    # Run debug
    debug_password_verification()
    
    # Show test hashes
    create_test_password_hashes()
    
    # Interactive fixing
    print("\n" + "=" * 50)
    print("🔧 INTERACTIVE PASSWORD FIXING")
    print("=" * 50)
    
    while True:
        print("\nOptions:")
        print("1. Fix admin password")
        print("2. Fix custom user password")
        print("3. Exit")
        
        choice = input("Enter choice (1-3): ").strip()
        
        if choice == "1":
            fix_specific_user_password("admin", "very_Secure_p@ssword_123!")
        elif choice == "2":
            username = input("Enter username: ").strip()
            password = input("Enter new password: ").strip()
            if username and password:
                fix_specific_user_password(username, password)
        elif choice == "3":
            break
        else:
            print("Invalid choice")
    
    print("\n✅ Debug session complete!")

if __name__ == "__main__":
    main()