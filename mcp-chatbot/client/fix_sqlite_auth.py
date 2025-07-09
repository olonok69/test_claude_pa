#!/usr/bin/env python3
"""
Script to fix SQLite authentication issues
Run this to diagnose and fix SQLite authentication problems

Usage:
    python fix_sqlite_auth.py
"""

import os
import sys
import sqlite3
import yaml
import bcrypt
import logging
from datetime import datetime

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def check_sqlite_database():
    """Check SQLite database status."""
    print("🔍 Checking SQLite database...")
    
    db_path = "keys/users.db"
    if not os.path.exists(db_path):
        print("❌ SQLite database not found")
        return False
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Check users table
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='users'")
        if not cursor.fetchone():
            print("❌ Users table not found")
            return False
        
        # Get user count
        cursor.execute('SELECT COUNT(*) FROM users')
        total_users = cursor.fetchone()[0]
        
        cursor.execute('SELECT COUNT(*) FROM users WHERE is_admin = TRUE')
        admin_users = cursor.fetchone()[0]
        
        print(f"✅ Database found with {total_users} users ({admin_users} admin)")
        
        # Show sample users
        cursor.execute('SELECT username, email, is_admin, is_active FROM users LIMIT 5')
        users = cursor.fetchall()
        
        print("\n📋 Sample users:")
        for username, email, is_admin, is_active in users:
            status = "👑 Admin" if is_admin else "👤 User"
            active = "✅ Active" if is_active else "❌ Inactive"
            print(f"  • {username} ({email}) - {status} - {active}")
        
        conn.close()
        return True
        
    except Exception as e:
        print(f"❌ Database error: {str(e)}")
        return False

def check_yaml_config():
    """Check YAML configuration."""
    print("\n🔍 Checking YAML configuration...")
    
    yaml_path = "keys/config.yaml"
    if not os.path.exists(yaml_path):
        print("❌ YAML config not found")
        return False, {}
    
    try:
        with open(yaml_path, 'r') as f:
            config = yaml.safe_load(f)
        
        users = config.get('credentials', {}).get('usernames', {})
        print(f"✅ YAML config found with {len(users)} users")
        
        for username, user_data in users.items():
            role = "👑 Admin" if user_data.get('is_admin', False) else "👤 User"
            print(f"  • {username} ({user_data['name']}) - {role}")
        
        return True, users
        
    except Exception as e:
        print(f"❌ YAML error: {str(e)}")
        return False, {}

def migrate_yaml_to_sqlite():
    """Migrate users from YAML to SQLite."""
    print("\n🔄 Migrating users from YAML to SQLite...")
    
    # Load YAML users
    yaml_success, yaml_users = check_yaml_config()
    if not yaml_success or not yaml_users:
        print("❌ Cannot migrate - no YAML users found")
        return False
    
    try:
        # Create/connect to SQLite database
        db_path = "keys/users.db"
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
        
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Create users table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                email TEXT UNIQUE NOT NULL,
                full_name TEXT NOT NULL,
                is_admin BOOLEAN DEFAULT FALSE,
                is_active BOOLEAN DEFAULT TRUE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_login TIMESTAMP,
                login_attempts INTEGER DEFAULT 0,
                locked_until TIMESTAMP,
                password_changed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                failed_login_attempts INTEGER DEFAULT 0,
                last_failed_login TIMESTAMP,
                migrated_from_yaml BOOLEAN DEFAULT FALSE,
                migration_date TIMESTAMP,
                original_yaml_data TEXT
            )
        ''')
        
        # Clear existing users to avoid conflicts
        cursor.execute('DELETE FROM users')
        
        # Migrate each user
        migrated_count = 0
        for username, user_data in yaml_users.items():
            try:
                cursor.execute('''
                    INSERT INTO users (username, password_hash, email, full_name, is_admin, migrated_from_yaml, migration_date)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                ''', (
                    username,
                    user_data['password'],  # Use existing hash from YAML
                    user_data['email'],
                    user_data['name'],
                    user_data.get('is_admin', False),
                    True,
                    datetime.now().isoformat()
                ))
                
                migrated_count += 1
                print(f"✅ Migrated: {username}")
                
            except Exception as e:
                print(f"❌ Failed to migrate {username}: {str(e)}")
        
        conn.commit()
        conn.close()
        
        print(f"\n✅ Migration completed: {migrated_count} users migrated")
        return migrated_count > 0
        
    except Exception as e:
        print(f"❌ Migration failed: {str(e)}")
        return False

def test_authentication():
    """Test authentication with common credentials."""
    print("\n🧪 Testing authentication...")
    
    try:
        from utils.enhanced_security_config import StreamlitSecureAuth
        
        auth = StreamlitSecureAuth('sqlite')
        
        # Test common credentials
        test_credentials = [
            ('admin', 'admin_password_change_immediately'),
            ('admin', 'very_Secure_p@ssword_123!'),
            ('juan', 'Larisa1000@'),
            ('giovanni_romero', 'MrRomero2024!'),
            ('demo_user', 'StrongPassword123!')
        ]
        
        for username, password in test_credentials:
            success, user_data, message = auth.authenticate(username, password)
            
            if success:
                print(f"✅ Authentication successful: {username} -> {user_data['name']}")
                return True, username, password
            else:
                print(f"❌ Authentication failed: {username} -> {message}")
        
        print("❌ All authentication tests failed")
        return False, None, None
        
    except ImportError:
        print("❌ Enhanced security module not available")
        return False, None, None
    except Exception as e:
        print(f"❌ Authentication test error: {str(e)}")
        return False, None, None

def create_test_admin():
    """Create a test admin user."""
    print("\n👑 Creating test admin user...")
    
    try:
        db_path = "keys/users.db"
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Create admin user with known password
        test_password = "test_admin_123!"
        password_hash = bcrypt.hashpw(test_password.encode(), bcrypt.gensalt()).decode()
        
        # Delete existing admin if exists
        cursor.execute('DELETE FROM users WHERE username = ?', ('test_admin',))
        
        cursor.execute('''
            INSERT INTO users (username, password_hash, email, full_name, is_admin)
            VALUES (?, ?, ?, ?, ?)
        ''', ('test_admin', password_hash, 'test@admin.com', 'Test Administrator', True))
        
        conn.commit()
        conn.close()
        
        print(f"✅ Test admin created:")
        print(f"   Username: test_admin")
        print(f"   Password: {test_password}")
        print(f"   Email: test@admin.com")
        
        return True, 'test_admin', test_password
        
    except Exception as e:
        print(f"❌ Failed to create test admin: {str(e)}")
        return False, None, None

def fix_config_generation():
    """Fix the config generation for streamlit-authenticator."""
    print("\n🔧 Testing config generation...")
    
    try:
        from utils.enhanced_security_config import StreamlitSecureAuth
        
        auth = StreamlitSecureAuth('sqlite')
        config = auth.get_config_for_streamlit_authenticator()
        
        users = config.get('credentials', {}).get('usernames', {})
        print(f"✅ Config generated with {len(users)} users")
        
        # Check if passwords are actual hashes
        for username, user_data in users.items():
            password = user_data.get('password', '')
            if password == 'managed_by_secure_store':
                print(f"❌ User {username} has placeholder password")
                return False
            elif password.startswith('$2b$'):
                print(f"✅ User {username} has valid bcrypt hash")
            else:
                print(f"⚠️  User {username} has unknown password format: {password[:20]}...")
        
        return True
        
    except Exception as e:
        print(f"❌ Config generation error: {str(e)}")
        return False

def main():
    """Main diagnostic and fix function."""
    print("🔧 SQLite Authentication Diagnostic and Fix Tool")
    print("=" * 50)
    
    # Check environment
    use_sqlite = os.getenv('USE_SQLITE', 'false').lower() == 'true'
    print(f"🔍 USE_SQLITE environment variable: {use_sqlite}")
    
    if not use_sqlite:
        print("⚠️  SQLite is not enabled. Set USE_SQLITE=true in your .env file")
        return
    
    # Step 1: Check SQLite database
    sqlite_ok = check_sqlite_database()
    
    # Step 2: Check YAML config
    yaml_ok, yaml_users = check_yaml_config()
    
    # Step 3: Migrate if needed
    if yaml_ok and yaml_users and not sqlite_ok:
        print("\n🔄 SQLite database needs setup, migrating from YAML...")
        migrate_yaml_to_sqlite()
        sqlite_ok = check_sqlite_database()
    
    # Step 4: Test authentication
    if sqlite_ok:
        auth_ok, test_user, test_pass = test_authentication()
        
        if not auth_ok:
            print("\n⚠️  Authentication failed, creating test admin...")
            auth_ok, test_user, test_pass = create_test_admin()
    
    # Step 5: Test config generation
    if sqlite_ok:
        config_ok = fix_config_generation()
    
    # Summary
    print("\n" + "=" * 50)
    print("📊 SUMMARY:")
    print(f"  SQLite Database: {'✅ OK' if sqlite_ok else '❌ ISSUES'}")
    print(f"  YAML Config: {'✅ OK' if yaml_ok else '❌ ISSUES'}")
    
    if sqlite_ok:
        print(f"  Authentication: {'✅ OK' if 'auth_ok' in locals() and auth_ok else '❌ ISSUES'}")
        print(f"  Config Generation: {'✅ OK' if 'config_ok' in locals() and config_ok else '❌ ISSUES'}")
        
        if 'test_user' in locals() and test_user:
            print(f"\n✅ You can now login with:")
            print(f"   Username: {test_user}")
            print(f"   Password: {test_pass}")
    
    print("\n🚀 Restart your Streamlit app to test the authentication!")

if __name__ == "__main__":
    main()