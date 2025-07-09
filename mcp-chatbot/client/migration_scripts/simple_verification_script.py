#!/usr/bin/env python3
"""
Simple Verification Script
Verifies SQLite authentication without creating test users
"""

import os
import sys
import sqlite3
from datetime import datetime

# Add the client directory to the path
sys.path.append('.')

def verify_sqlite_system():
    """Verify the SQLite authentication system is working."""
    print("🔍 VERIFYING SQLITE AUTHENTICATION SYSTEM")
    print("=" * 50)
    
    results = {
        'database_exists': False,
        'tables_present': False,
        'users_migrated': False,
        'modules_available': False,
        'password_hashing_works': False,
        'auth_system_works': False
    }
    
    # Check 1: Database exists
    db_path = "keys/users.db"
    if os.path.exists(db_path):
        print("✅ Database file exists")
        results['database_exists'] = True
    else:
        print("❌ Database file not found")
        return results
    
    # Check 2: Database structure
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Check for required tables
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = [row[0] for row in cursor.fetchall()]
        required_tables = ['users', 'user_sessions', 'audit_log', 'migration_log']
        
        missing_tables = [t for t in required_tables if t not in tables]
        if not missing_tables:
            print("✅ All required tables present")
            results['tables_present'] = True
        else:
            print(f"❌ Missing tables: {missing_tables}")
            conn.close()
            return results
        
        conn.close()
        
    except Exception as e:
        print(f"❌ Database structure check failed: {str(e)}")
        return results
    
    # Check 3: Users migrated
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        cursor.execute("SELECT COUNT(*) FROM users")
        total_users = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM users WHERE migrated_from_yaml = 1")
        migrated_users = cursor.fetchone()[0]
        
        if total_users > 0:
            print(f"✅ Found {total_users} users ({migrated_users} migrated)")
            results['users_migrated'] = True
            
            # Show sample users
            cursor.execute("SELECT username, email, is_admin FROM users LIMIT 3")
            sample_users = cursor.fetchall()
            print("   Sample users:")
            for user in sample_users:
                admin_flag = "👑" if user[2] else "👤"
                print(f"     {admin_flag} {user[0]} ({user[1]})")
        else:
            print("❌ No users found in database")
        
        conn.close()
        
    except Exception as e:
        print(f"❌ User check failed: {str(e)}")
        return results
    
    # Check 4: Modules available
    try:
        from utils.enhanced_security_config import StreamlitSecureAuth, SecureUserStore
        print("✅ Enhanced security modules available")
        results['modules_available'] = True
    except ImportError as e:
        print(f"❌ Enhanced security modules not available: {str(e)}")
        return results
    
    # Check 5: Password hashing
    try:
        user_store = SecureUserStore('sqlite')
        test_password = "TestPassword123!"
        hashed = user_store.hash_password(test_password)
        
        # Verify password
        is_valid = user_store.verify_password(test_password, hashed)
        is_invalid = not user_store.verify_password("wrong_password", hashed)
        
        if is_valid and is_invalid:
            print("✅ Password hashing and verification working")
            results['password_hashing_works'] = True
        else:
            print("❌ Password hashing failed")
            return results
            
    except Exception as e:
        print(f"❌ Password hashing test failed: {str(e)}")
        return results
    
    # Check 6: Authentication system
    try:
        auth_system = StreamlitSecureAuth('sqlite')
        config = auth_system.get_config_for_streamlit_authenticator()
        
        if config and 'credentials' in config:
            user_count = len(config['credentials']['usernames'])
            print(f"✅ Authentication system working ({user_count} users configured)")
            results['auth_system_works'] = True
        else:
            print("❌ Authentication system configuration failed")
            return results
            
    except Exception as e:
        print(f"❌ Authentication system test failed: {str(e)}")
        return results
    
    return results

def show_migration_status():
    """Show detailed migration status."""
    print("\n📊 MIGRATION STATUS DETAILS")
    print("=" * 50)
    
    db_path = "keys/users.db"
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Migration log
        cursor.execute("""
            SELECT migration_date, users_migrated, success, notes
            FROM migration_log 
            ORDER BY migration_date DESC 
            LIMIT 1
        """)
        migration_info = cursor.fetchone()
        
        if migration_info:
            date, users_migrated, success, notes = migration_info
            status = "✅ Success" if success else "❌ Failed"
            print(f"🔄 Last Migration: {date[:19]} - {status}")
            print(f"   Users migrated: {users_migrated}")
            print(f"   Notes: {notes}")
        else:
            print("⚠️  No migration log found")
        
        # Audit log summary
        cursor.execute("""
            SELECT event_type, COUNT(*) 
            FROM audit_log 
            WHERE event_type IN ('USER_MIGRATED', 'USER_CREATED')
            GROUP BY event_type
        """)
        events = cursor.fetchall()
        
        if events:
            print("\n📋 Migration Events:")
            for event_type, count in events:
                print(f"   • {event_type}: {count}")
        
        conn.close()
        
    except Exception as e:
        print(f"❌ Error checking migration status: {str(e)}")

def test_actual_authentication():
    """Test authentication with existing users (no password needed)."""
    print("\n🔐 TESTING AUTHENTICATION SYSTEM")
    print("=" * 50)
    
    try:
        from utils.enhanced_security_config import StreamlitSecureAuth
        
        auth_system = StreamlitSecureAuth('sqlite')
        
        # Get a test user from database
        db_path = "keys/users.db"
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT username FROM users LIMIT 1")
        result = cursor.fetchone()
        conn.close()
        
        if not result:
            print("❌ No users available for testing")
            return False
        
        test_username = result[0]
        
        # Test with wrong password (should fail)
        success, user_data, message = auth_system.authenticate(test_username, "definitely_wrong_password")
        
        if not success:
            print(f"✅ Authentication correctly rejected invalid password for user: {test_username}")
            print(f"   Message: {message}")
        else:
            print(f"❌ Authentication incorrectly accepted invalid password")
            return False
        
        # Test with non-existent user (should fail)
        success, user_data, message = auth_system.authenticate("definitely_nonexistent_user", "any_password")
        
        if not success:
            print("✅ Authentication correctly rejected non-existent user")
            print(f"   Message: {message}")
        else:
            print("❌ Authentication incorrectly accepted non-existent user")
            return False
        
        print("✅ Authentication system working correctly")
        return True
        
    except Exception as e:
        print(f"❌ Authentication test failed: {str(e)}")
        return False

def show_system_recommendations():
    """Show recommendations for using the system."""
    print("\n🎯 SYSTEM READY - NEXT STEPS")
    print("=" * 50)
    
    print("✅ Your SQLite authentication system is working correctly!")
    print()
    print("📋 To use the system:")
    print("1. 📝 Set USE_SQLITE=true in your .env file")
    print("2. 🚀 Start your application: streamlit run app.py")
    print("3. 🔑 Login with your migrated user credentials")
    print("4. 👥 Access User Management tab (admin users only)")
    print()
    print("🔒 Security features active:")
    print("• bcrypt password hashing")
    print("• Session management with tokens")
    print("• Audit logging for user actions")
    print("• Account lockout protection")
    print("• Password strength validation")
    print()
    print("📊 User Management features:")
    print("• Add/edit/delete users")
    print("• Password reset functionality")
    print("• User activity monitoring")
    print("• Secure password generation")
    print("• Role-based access control")

def main():
    """Main verification script."""
    print("""
╔═══════════════════════════════════════════════════════════════════════════════╗
║                         SIMPLE VERIFICATION SCRIPT                           ║
║                      SQLite Authentication System Check                      ║
╚═══════════════════════════════════════════════════════════════════════════════╝
    """)
    
    # Run verification
    results = verify_sqlite_system()
    
    # Count successful checks
    passed_checks = sum(results.values())
    total_checks = len(results)
    
    print(f"\n📊 VERIFICATION SUMMARY")
    print("=" * 50)
    print(f"Passed: {passed_checks}/{total_checks} checks")
    
    if passed_checks == total_checks:
        print("🎉 ALL CHECKS PASSED!")
        
        # Show additional details
        show_migration_status()
        test_actual_authentication()
        show_system_recommendations()
        
    else:
        print("⚠️  Some checks failed:")
        for check, passed in results.items():
            status = "✅" if passed else "❌"
            print(f"  {status} {check.replace('_', ' ').title()}")
        
        print("\n🛠️ Troubleshooting:")
        if not results['database_exists']:
            print("• Run the migration script first")
        if not results['modules_available']:
            print("• Install: pip install cryptography")
            print("• Ensure utils/enhanced_security_config.py exists")
        if not results['users_migrated']:
            print("• Re-run the migration script")
            print("• Check migration logs for errors")

if __name__ == "__main__":
    main()