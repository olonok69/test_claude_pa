#!/usr/bin/env python3
"""
Script to promote a user to admin in SQLite database
Run this to fix the "no admin users" issue
"""

import sqlite3
import os
from datetime import datetime

def promote_user_to_admin():
    """Promote an existing user to admin status."""
    db_path = "keys/users.db"
    
    if not os.path.exists(db_path):
        print("❌ Database file not found!")
        return False
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # First, show all users
        print("📋 Current users in database:")
        cursor.execute('SELECT username, email, full_name, is_admin FROM users')
        users = cursor.fetchall()
        
        for i, (username, email, name, is_admin) in enumerate(users):
            admin_status = "👑 Admin" if is_admin else "👤 User"
            print(f"{i+1}. {username} ({name}) - {admin_status}")
        
        if not users:
            print("❌ No users found in database!")
            return False
        
        # Ask user to choose
        while True:
            try:
                choice = input(f"\nEnter the number (1-{len(users)}) of the user to promote to admin: ")
                choice_idx = int(choice) - 1
                
                if 0 <= choice_idx < len(users):
                    selected_user = users[choice_idx]
                    username = selected_user[0]
                    break
                else:
                    print(f"❌ Please enter a number between 1 and {len(users)}")
            except ValueError:
                print("❌ Please enter a valid number")
        
        # Confirm promotion
        confirm = input(f"\n🔄 Promote '{username}' to admin? (y/N): ").lower()
        if confirm != 'y':
            print("❌ Promotion cancelled")
            return False
        
        # Promote user
        cursor.execute('UPDATE users SET is_admin = TRUE WHERE username = ?', (username,))
        
        # Log the promotion
        cursor.execute('''
            INSERT INTO audit_log (user_id, event_type, event_description)
            SELECT id, 'USER_PROMOTED', ?
            FROM users WHERE username = ?
        ''', (f'User {username} promoted to admin via script', username))
        
        conn.commit()
        conn.close()
        
        print(f"✅ User '{username}' promoted to admin successfully!")
        print("🚀 You can now log in with admin privileges")
        return True
        
    except Exception as e:
        print(f"❌ Error promoting user: {str(e)}")
        return False

def check_admin_status():
    """Check current admin status in database."""
    db_path = "keys/users.db"
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        cursor.execute('SELECT COUNT(*) FROM users WHERE is_admin = TRUE')
        admin_count = cursor.fetchone()[0]
        
        cursor.execute('SELECT COUNT(*) FROM users')
        total_count = cursor.fetchone()[0]
        
        print(f"📊 Database Status:")
        print(f"   Total users: {total_count}")
        print(f"   Admin users: {admin_count}")
        
        if admin_count == 0:
            print("⚠️  No admin users found!")
            return False
        else:
            print("✅ Admin users found")
            return True
            
    except Exception as e:
        print(f"❌ Error checking database: {str(e)}")
        return False

if __name__ == "__main__":
    print("🔐 Admin User Promotion Tool")
    print("=" * 40)
    
    # Check current status
    if check_admin_status():
        print("✅ Admin users already exist!")
        exit(0)
    
    print("\n🔧 No admin users found. Let's promote someone!")
    promote_user_to_admin()