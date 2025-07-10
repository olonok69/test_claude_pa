#!/usr/bin/env python3
"""
Comprehensive SQLite Authentication Fix Script
This script fixes password hash compatibility issues and ensures proper authentication

Usage:
    python comprehensive_fix.py
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

def check_password_format(password_hash):
    """Check the format of a password hash."""
    if password_hash.startswith('$2b$'):
        return "bcrypt"
    elif password_hash.startswith('$2a$'):
        return "bcrypt_old"
    elif len(password_hash) == 60 and password_hash.startswith('$'):
        return "bcrypt_variant"
    else:
        return "unknown"

def analyze_existing_users():
    """Analyze existing users and their password formats."""
    print("🔍 Analyzing existing users and password formats...")
    
    db_path = "keys/users.db"
    if not os.path.exists(db_path):
        print("❌ SQLite database not found")
        return False
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        cursor.execute('SELECT username, password_hash, email, full_name, is_admin FROM users')
        users = cursor.fetchall()
        
        print(f"\n📋 Found {len(users)} users:")
        for username, password_hash, email, full_name, is_admin in users:
            role = "👑 Admin" if is_admin else "👤 User"
            hash_format = check_password_format(password_hash)
            print(f"  • {username} ({full_name}) - {role}")
            print(f"    Email: {email}")
            print(f"    Hash format: {hash_format}")
            print(f"    Hash sample: {password_hash[:20]}...")
            print()
        
        conn.close()
        return True
        
    except Exception as e:
        print(f"❌ Error analyzing users: {str(e)}")
        return False

def reset_user_passwords():
    """Reset user passwords to known values for testing."""
    print("🔄 Resetting user passwords to known values...")
    
    # Known password mappings
    password_mappings = {
        'admin': 'very_Secure_p@ssword_123!',
        'juan': 'Larisa1000@',
        'giovanni_romero': 'MrRomero2024!',
        'demo_user': 'strong_password_123!',
        'test_admin': 'test_admin_123!'
    }
    
    try:
        db_path = "keys/users.db"
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Get existing users
        cursor.execute('SELECT username FROM users')
        existing_users = [row[0] for row in cursor.fetchall()]
        
        updated_count = 0
        for username in existing_users:
            if username in password_mappings:
                new_password = password_mappings[username]
                new_hash = bcrypt.hashpw(new_password.encode(), bcrypt.gensalt()).decode()
                
                cursor.execute('UPDATE users SET password_hash = ? WHERE username = ?', 
                             (new_hash, username))
                
                print(f"✅ Updated password for {username}")
                updated_count += 1
            else:
                # Use a default password for users not in mapping
                default_password = f"{username}_password_123!"
                new_hash = bcrypt.hashpw(default_password.encode(), bcrypt.gensalt()).decode()
                
                cursor.execute('UPDATE users SET password_hash = ? WHERE username = ?', 
                             (new_hash, username))
                
                print(f"✅ Set default password for {username}: {default_password}")
                updated_count += 1
        
        conn.commit()
        conn.close()
        
        print(f"\n✅ Updated passwords for {updated_count} users")
        
        # Print credential summary
        print("\n🔑 Updated Credentials:")
        print("-" * 40)
        for username in existing_users:
            if username in password_mappings:
                print(f"Username: {username}")
                print(f"Password: {password_mappings[username]}")
            else:
                print(f"Username: {username}")
                print(f"Password: {username}_password_123!")
            print()
        
        return True
        
    except Exception as e:
        print(f"❌ Error resetting passwords: {str(e)}")
        return False

def test_authentication_comprehensive():
    """Comprehensive authentication testing."""
    print("🧪 Testing authentication with updated credentials...")
    
    try:
        # Import the fixed module
        sys.path.insert(0, '.')
        from utils.enhanced_security_config import StreamlitSecureAuth
        
        auth = StreamlitSecureAuth('sqlite')
        
        # Get all users from database first
        db_path = "keys/users.db"
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute('SELECT username FROM users')
        usernames = [row[0] for row in cursor.fetchall()]
        conn.close()
        
        # Test credentials
        test_credentials = {
            'admin': 'very_Secure_p@ssword_123!',
            'juan': 'Larisa1000@',
            'giovanni_romero': 'MrRomero2024!',
            'demo_user': 'strong_password_123!',
            'test_admin': 'test_admin_123!'
        }
        
        successful_logins = []
        
        for username in usernames:
            if username in test_credentials:
                password = test_credentials[username]
            else:
                password = f"{username}_password_123!"
            
            success, user_data, message = auth.authenticate(username, password)
            
            if success:
                print(f"✅ {username} -> SUCCESS")
                successful_logins.append((username, password))
            else:
                print(f"❌ {username} -> FAILED: {message}")
        
        if successful_logins:
            print(f"\n✅ {len(successful_logins)} successful logins!")
            print("\n🎉 Working Credentials:")
            print("-" * 30)
            for username, password in successful_logins:
                print(f"Username: {username}")
                print(f"Password: {password}")
                print()
            return True
        else:
            print("❌ No successful logins")
            return False
            
    except Exception as e:
        print(f"❌ Authentication test error: {str(e)}")
        return False

def test_streamlit_config():
    """Test streamlit-authenticator config generation."""
    print("🔧 Testing streamlit-authenticator config generation...")
    
    try:
        from utils.enhanced_security_config import StreamlitSecureAuth
        
        auth = StreamlitSecureAuth('sqlite')
        config = auth.get_config_for_streamlit_authenticator()
        
        users = config.get('credentials', {}).get('usernames', {})
        print(f"✅ Config generated successfully with {len(users)} users")
        
        # Validate config structure
        required_keys = ['credentials', 'cookie', 'preauthorized']
        for key in required_keys:
            if key not in config:
                print(f"❌ Missing required key: {key}")
                return False
        
        # Check password hashes
        valid_hashes = 0
        for username, user_data in users.items():
            password_hash = user_data.get('password', '')
            if password_hash and password_hash.startswith('$2b$'):
                valid_hashes += 1
                print(f"✅ {username}: Valid bcrypt hash")
            else:
                print(f"❌ {username}: Invalid hash format")
        
        if valid_hashes == len(users):
            print(f"✅ All {valid_hashes} users have valid password hashes")
            return True
        else:
            print(f"❌ Only {valid_hashes}/{len(users)} users have valid hashes")
            return False
            
    except Exception as e:
        print(f"❌ Config test error: {str(e)}")
        return False

def create_clean_database():
    """Create a clean database with proper user setup."""
    print("🆕 Creating clean database with proper setup...")
    
    try:
        db_path = "keys/users.db"
        
        # Backup existing database
        if os.path.exists(db_path):
            backup_path = f"{db_path}.backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            os.rename(db_path, backup_path)
            print(f"📦 Backed up existing database to {backup_path}")
        
        # Create new database
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Create users table
        cursor.execute('''
            CREATE TABLE users (
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
        
        # Create sessions table
        cursor.execute('''
            CREATE TABLE user_sessions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                session_token TEXT UNIQUE NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                expires_at TIMESTAMP NOT NULL,
                is_active BOOLEAN DEFAULT TRUE,
                ip_address TEXT,
                user_agent TEXT,
                FOREIGN KEY (user_id) REFERENCES users (id)
            )
        ''')
        
        # Create audit log table
        cursor.execute('''
            CREATE TABLE audit_log (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                event_type TEXT NOT NULL,
                event_description TEXT,
                ip_address TEXT,
                user_agent TEXT,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (id)
            )
        ''')
        
        # Insert clean users with known passwords
        users_to_create = [
            ('admin', 'very_Secure_p@ssword_123!', 'admin@csm.com', 'Administrator', True),
            ('juan', 'Larisa1000@', 'olonok@gmail.com', 'Juan Perez', False),
            ('giovanni_romero', 'MrRomero2024!', 'g.romero@closerstillmedia.com', 'Giovanni Romero', False),
            ('demo_user', 'strong_password_123!', 'demo@example.com', 'Demo User', False),
            ('test_admin', 'test_admin_123!', 'test@admin.com', 'Test Administrator', True)
        ]
        
        for username, password, email, full_name, is_admin in users_to_create:
            password_hash = bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()
            
            cursor.execute('''
                INSERT INTO users (username, password_hash, email, full_name, is_admin)
                VALUES (?, ?, ?, ?, ?)
            ''', (username, password_hash, email, full_name, is_admin))
            
            print(f"✅ Created user: {username}")
        
        conn.commit()
        conn.close()
        
        print(f"\n✅ Clean database created with {len(users_to_create)} users")
        return True
        
    except Exception as e:
        print(f"❌ Error creating clean database: {str(e)}")
        return False

def main():
    """Main comprehensive fix function."""
    print("🔧 Comprehensive SQLite Authentication Fix")
    print("=" * 50)
    
    # Check environment
    use_sqlite = os.getenv('USE_SQLITE', 'false').lower() == 'true'
    print(f"🔍 USE_SQLITE environment variable: {use_sqlite}")
    
    if not use_sqlite:
        print("⚠️  SQLite is not enabled. Set USE_SQLITE=true in your .env file")
        return
    
    # Analyze current state
    print("\n" + "=" * 30)
    print("PHASE 1: ANALYSIS")
    print("=" * 30)
    
    analyze_existing_users()
    
    # Ask user what to do
    print("\n" + "=" * 30)
    print("PHASE 2: FIX OPTIONS")
    print("=" * 30)
    
    print("Choose an option:")
    print("1. Reset passwords for existing users (recommended)")
    print("2. Create completely clean database")
    print("3. Exit without changes")
    
    choice = input("\nEnter your choice (1-3): ").strip()
    
    if choice == "1":
        print("\n" + "=" * 30)
        print("PHASE 3: PASSWORD RESET")
        print("=" * 30)
        
        if reset_user_passwords():
            print("\n" + "=" * 30)
            print("PHASE 4: TESTING")
            print("=" * 30)
            
            auth_success = test_authentication_comprehensive()
            config_success = test_streamlit_config()
            
            print("\n" + "=" * 50)
            print("📊 FINAL RESULTS:")
            print(f"  Password Reset: ✅ SUCCESS")
            print(f"  Authentication: {'✅ SUCCESS' if auth_success else '❌ FAILED'}")
            print(f"  Config Generation: {'✅ SUCCESS' if config_success else '❌ FAILED'}")
            
    elif choice == "2":
        print("\n" + "=" * 30)
        print("PHASE 3: CLEAN DATABASE")
        print("=" * 30)
        
        if create_clean_database():
            print("\n" + "=" * 30)
            print("PHASE 4: TESTING")
            print("=" * 30)
            
            auth_success = test_authentication_comprehensive()
            config_success = test_streamlit_config()
            
            print("\n" + "=" * 50)
            print("📊 FINAL RESULTS:")
            print(f"  Clean Database: ✅ SUCCESS")
            print(f"  Authentication: {'✅ SUCCESS' if auth_success else '❌ FAILED'}")
            print(f"  Config Generation: {'✅ SUCCESS' if config_success else '❌ FAILED'}")
            
    else:
        print("👋 Exiting without changes")
        return
    
    print("\n🚀 Restart your Streamlit app to test the authentication!")
    print("💡 Use any of the working credentials shown above to login")

if __name__ == "__main__":
    main()