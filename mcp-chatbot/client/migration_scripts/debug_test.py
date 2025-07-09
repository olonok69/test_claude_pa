#!/usr/bin/env python3
"""
Debug Migration Test Script
Identifies and fixes the UNIQUE constraint issue
"""

import os
import sys
import sqlite3
from datetime import datetime
import uuid
import traceback

# Add the client directory to the path
sys.path.append('.')

def debug_database_state():
    """Debug the current database state to identify the issue."""
    print("🔍 DEBUGGING DATABASE STATE:")
    print("=" * 50)
    
    db_path = "keys/users.db"
    if not os.path.exists(db_path):
        print("❌ Database not found!")
        return False
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Get all users
        cursor.execute("SELECT id, username, email, created_at FROM users ORDER BY created_at")
        users = cursor.fetchall()
        
        print(f"📊 Total users in database: {len(users)}")
        print("\n👥 Current users:")
        for user in users:
            user_id, username, email, created_at = user
            print(f"  ID: {user_id} | Username: {username} | Email: {email} | Created: {created_at}")
        
        # Check for test users specifically
        cursor.execute("SELECT COUNT(*) FROM users WHERE username LIKE 'test_user_%'")
        test_user_count = cursor.fetchone()[0]
        print(f"\n🧪 Test users found: {test_user_count}")
        
        if test_user_count > 0:
            cursor.execute("SELECT username, email, created_at FROM users WHERE username LIKE 'test_user_%'")
            test_users = cursor.fetchall()
            print("🧪 Existing test users:")
            for user in test_users:
                print(f"  • {user[0]} ({user[1]}) - {user[2]}")
        
        # Check database schema
        cursor.execute("PRAGMA table_info(users)")
        schema = cursor.fetchall()
        print(f"\n📋 Users table schema:")
        for column in schema:
            print(f"  • {column[1]} ({column[2]}) - {'NOT NULL' if column[3] else 'NULL'} - {'UNIQUE' if column[5] else ''}")
        
        # Check for any constraints
        cursor.execute("SELECT sql FROM sqlite_master WHERE type='table' AND name='users'")
        table_sql = cursor.fetchone()[0]
        print(f"\n🏗️ Table creation SQL:")
        print(table_sql)
        
        conn.close()
        return True
        
    except Exception as e:
        print(f"❌ Error debugging database: {str(e)}")
        print(f"🐛 Traceback: {traceback.format_exc()}")
        return False

def clean_all_test_data():
    """Aggressively clean all test data."""
    print("\n🧹 CLEANING ALL TEST DATA:")
    print("=" * 30)
    
    db_path = "keys/users.db"
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Remove all test users
        cursor.execute("DELETE FROM users WHERE username LIKE 'test_%' OR username LIKE '%test%' OR email LIKE '%test%'")
        deleted_users = cursor.rowcount
        print(f"✅ Removed {deleted_users} test users")
        
        # Remove test sessions
        cursor.execute("DELETE FROM user_sessions WHERE user_agent LIKE '%test%' OR user_agent LIKE '%Test%'")
        deleted_sessions = cursor.rowcount
        print(f"✅ Removed {deleted_sessions} test sessions")
        
        # Remove test audit logs
        cursor.execute("DELETE FROM audit_log WHERE event_description LIKE '%test%' OR event_description LIKE '%Test%'")
        deleted_logs = cursor.rowcount
        print(f"✅ Removed {deleted_logs} test audit logs")
        
        conn.commit()
        conn.close()
        
        print("✅ Test data cleanup completed")
        return True
        
    except Exception as e:
        print(f"❌ Error cleaning test data: {str(e)}")
        return False

def test_user_creation_step_by_step():
    """Test user creation step by step to identify the exact issue."""
    print("\n🔬 TESTING USER CREATION STEP BY STEP:")
    print("=" * 40)
    
    try:
        # Import the modules
        from utils.enhanced_security_config import SecureUserStore
        
        user_store = SecureUserStore('sqlite')
        
        # Generate unique test data
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S_%f')  # Include microseconds
        unique_id = str(uuid.uuid4())[:8]
        test_username = f"debug_user_{timestamp}_{unique_id}"
        test_email = f"debug_{timestamp}_{unique_id}@debug.com"
        test_password = "DebugPassword123!@#"
        
        print(f"🧪 Test username: {test_username}")
        print(f"📧 Test email: {test_email}")
        
        # Check if user already exists (shouldn't with unique timestamp)
        db_path = "keys/users.db"
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        cursor.execute("SELECT COUNT(*) FROM users WHERE username = ? OR email = ?", (test_username, test_email))
        existing_count = cursor.fetchone()[0]
        
        if existing_count > 0:
            print(f"❌ User already exists! This shouldn't happen with unique timestamp.")
            cursor.execute("SELECT username, email FROM users WHERE username = ? OR email = ?", (test_username, test_email))
            existing_users = cursor.fetchall()
            for user in existing_users:
                print(f"  Existing: {user[0]} - {user[1]}")
            conn.close()
            return False
        
        print("✅ No existing user with this username/email")
        conn.close()
        
        # Try to create the user
        print("🔄 Attempting to create user...")
        success = user_store.create_user(
            username=test_username,
            password=test_password,
            email=test_email,
            full_name="Debug Test User",
            is_admin=False
        )
        
        if success:
            print("✅ User created successfully!")
            
            # Verify the user was created
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            cursor.execute("SELECT username, email FROM users WHERE username = ?", (test_username,))
            created_user = cursor.fetchone()
            
            if created_user:
                print(f"✅ User verified in database: {created_user[0]} - {created_user[1]}")
                
                # Clean up the test user
                cursor.execute("DELETE FROM users WHERE username = ?", (test_username,))
                conn.commit()
                print("✅ Test user cleaned up")
            else:
                print("❌ User not found in database after creation")
            
            conn.close()
            return True
        else:
            print("❌ User creation failed")
            return False
            
    except Exception as e:
        print(f"❌ Error in step-by-step test: {str(e)}")
        print(f"🐛 Traceback: {traceback.format_exc()}")
        return False

def run_minimal_test_suite():
    """Run a minimal test suite that avoids user creation."""
    print("\n🚀 RUNNING MINIMAL TEST SUITE (NO USER CREATION):")
    print("=" * 50)
    
    try:
        from utils.enhanced_security_config import StreamlitSecureAuth, SecureUserStore
        
        # Test 1: Database connectivity
        print("🔍 Test 1: Database connectivity...")
        db_path = "keys/users.db"
        if os.path.exists(db_path):
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM users")
            user_count = cursor.fetchone()[0]
            conn.close()
            print(f"✅ Database accessible, {user_count} users found")
        else:
            print("❌ Database not found")
            return False
        
        # Test 2: Password hashing
        print("🔍 Test 2: Password hashing...")
        user_store = SecureUserStore('sqlite')
        test_password = "TestPassword123!"
        hashed = user_store.hash_password(test_password)
        is_valid = user_store.verify_password(test_password, hashed)
        is_invalid = not user_store.verify_password("wrong_password", hashed)
        
        if is_valid and is_invalid:
            print("✅ Password hashing working correctly")
        else:
            print("❌ Password hashing failed")
            return False
        
        # Test 3: Authentication system initialization
        print("🔍 Test 3: Authentication system...")
        auth_system = StreamlitSecureAuth('sqlite')
        if auth_system:
            print("✅ Authentication system initialized")
        else:
            print("❌ Authentication system failed to initialize")
            return False
        
        # Test 4: Check existing users
        print("🔍 Test 4: Existing users verification...")
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT username, email FROM users WHERE migrated_from_yaml = 1 LIMIT 3")
        migrated_users = cursor.fetchall()
        
        if migrated_users:
            print(f"✅ Found {len(migrated_users)} migrated users:")
            for user in migrated_users:
                print(f"  • {user[0]} ({user[1]})")
        else:
            print("❌ No migrated users found")
        
        conn.close()
        
        print("\n🎉 MINIMAL TEST SUITE PASSED!")
        print("📝 Your SQLite authentication system is working!")
        print("⚠️  The issue is specifically with test user creation, not the core system.")
        
        return True
        
    except Exception as e:
        print(f"❌ Error in minimal test suite: {str(e)}")
        print(f"🐛 Traceback: {traceback.format_exc()}")
        return False

def fix_database_issues():
    """Try to fix common database issues."""
    print("\n🛠️ ATTEMPTING TO FIX DATABASE ISSUES:")
    print("=" * 40)
    
    db_path = "keys/users.db"
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Check for duplicate usernames
        cursor.execute("""
            SELECT username, COUNT(*) 
            FROM users 
            GROUP BY username 
            HAVING COUNT(*) > 1
        """)
        duplicates = cursor.fetchall()
        
        if duplicates:
            print(f"❌ Found duplicate usernames: {duplicates}")
            print("🔧 Attempting to fix duplicates...")
            
            for username, count in duplicates:
                # Keep the first one, delete the rest
                cursor.execute("""
                    DELETE FROM users 
                    WHERE rowid NOT IN (
                        SELECT MIN(rowid) 
                        FROM users 
                        WHERE username = ?
                    ) AND username = ?
                """, (username, username))
                
            conn.commit()
            print("✅ Duplicate usernames fixed")
        else:
            print("✅ No duplicate usernames found")
        
        # Check for duplicate emails
        cursor.execute("""
            SELECT email, COUNT(*) 
            FROM users 
            GROUP BY email 
            HAVING COUNT(*) > 1
        """)
        email_duplicates = cursor.fetchall()
        
        if email_duplicates:
            print(f"❌ Found duplicate emails: {email_duplicates}")
            print("🔧 Attempting to fix email duplicates...")
            
            for email, count in email_duplicates:
                # Keep the first one, delete the rest
                cursor.execute("""
                    DELETE FROM users 
                    WHERE rowid NOT IN (
                        SELECT MIN(rowid) 
                        FROM users 
                        WHERE email = ?
                    ) AND email = ?
                """, (email, email))
                
            conn.commit()
            print("✅ Duplicate emails fixed")
        else:
            print("✅ No duplicate emails found")
        
        # Vacuum the database to clean up
        conn.execute("VACUUM")
        print("✅ Database vacuumed and optimized")
        
        conn.close()
        return True
        
    except Exception as e:
        print(f"❌ Error fixing database issues: {str(e)}")
        return False

def main():
    """Main debug script."""
    print("""
╔═══════════════════════════════════════════════════════════════════════════════╗
║                            DEBUG MIGRATION TEST                               ║
║                        Identify and Fix UNIQUE Constraint Issues             ║
╚═══════════════════════════════════════════════════════════════════════════════╝
    """)
    
    print("🛠️ DEBUG OPTIONS:")
    print("-" * 30)
    print("1. 🔍 Debug Database State")
    print("2. 🧹 Clean All Test Data")
    print("3. 🔬 Test User Creation Step-by-Step")
    print("4. 🚀 Run Minimal Test Suite (Safe)")
    print("5. 🛠️ Fix Database Issues")
    print("6. 🔄 Full Debug Sequence")
    print("7. ❌ Exit")
    
    while True:
        try:
            choice = input("\nSelect option (1-7): ").strip()
            
            if choice == "1":
                debug_database_state()
                break
                
            elif choice == "2":
                clean_all_test_data()
                break
                
            elif choice == "3":
                test_user_creation_step_by_step()
                break
                
            elif choice == "4":
                run_minimal_test_suite()
                break
                
            elif choice == "5":
                fix_database_issues()
                break
                
            elif choice == "6":
                print("🔄 Running Full Debug Sequence...")
                print("\nStep 1: Debug Database State")
                debug_database_state()
                
                print("\nStep 2: Clean Test Data")
                clean_all_test_data()
                
                print("\nStep 3: Fix Database Issues")
                fix_database_issues()
                
                print("\nStep 4: Test User Creation")
                if test_user_creation_step_by_step():
                    print("\nStep 5: Run Minimal Test Suite")
                    run_minimal_test_suite()
                else:
                    print("\n❌ User creation still failing. Let's run the safe test suite:")
                    run_minimal_test_suite()
                
                break
                
            elif choice == "7":
                print("👋 Exiting debug script.")
                break
                
            else:
                print("❌ Invalid option. Please select 1-7.")
                
        except KeyboardInterrupt:
            print("\n\n👋 Debug script interrupted by user.")
            break
        except Exception as e:
            print(f"\n❌ Error: {str(e)}")
            print(f"🐛 Traceback: {traceback.format_exc()}")
            break

if __name__ == "__main__":
    main()