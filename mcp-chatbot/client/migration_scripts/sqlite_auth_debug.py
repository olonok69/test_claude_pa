#!/usr/bin/env python3
"""
SQLite Authentication Debug Script
Check if SQLite authentication is working and debug password issues
"""

import os
import sys
import sqlite3
import bcrypt
from datetime import datetime

# Add the client directory to the path
sys.path.append('.')

def check_sqlite_users():
    """Check what users exist in SQLite and test authentication."""
    print("🔍 CHECKING SQLITE USERS AND AUTHENTICATION")
    print("=" * 60)
    
    db_path = "keys/users.db"
    if not os.path.exists(db_path):
        print("❌ SQLite database not found!")
        return False
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Get all users
        cursor.execute("""
            SELECT id, username, email, full_name, is_admin, 
                   password_hash, created_at, migrated_from_yaml
            FROM users 
            ORDER BY created_at
        """)
        users = cursor.fetchall()
        
        print(f"📊 Found {len(users)} users in SQLite database:")
        print()
        
        for user in users:
            user_id, username, email, full_name, is_admin, password_hash, created_at, migrated = user
            admin_flag = "👑 ADMIN" if is_admin else "👤 USER"
            migrated_flag = "🔄 MIGRATED" if migrated else "➕ CREATED"
            
            print(f"ID: {user_id}")
            print(f"Username: {username}")
            print(f"Email: {email}")
            print(f"Name: {full_name}")
            print(f"Role: {admin_flag}")
            print(f"Status: {migrated_flag}")
            print(f"Created: {created_at}")
            print(f"Password Hash: {password_hash[:50]}...")
            print("-" * 40)
        
        conn.close()
        return users
        
    except Exception as e:
        print(f"❌ Error checking SQLite users: {str(e)}")
        return False

def test_password_verification():
    """Test password verification with known passwords."""
    print("\n🔑 TESTING PASSWORD VERIFICATION")
    print("=" * 60)
    
    db_path = "keys/users.db"
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Get all users
        cursor.execute("SELECT username, password_hash FROM users")
        users = cursor.fetchall()
        
        print("Testing password verification for each user:")
        print("(You'll need to provide the temporary passwords from migration)")
        print()
        
        for username, password_hash in users:
            print(f"👤 User: {username}")
            
            # Ask for the temporary password
            temp_password = input(f"Enter temporary password for {username} (or 'skip'): ").strip()
            
            if temp_password.lower() == 'skip':
                print("⏭️  Skipped")
                continue
            
            # Test password verification
            try:
                is_valid = bcrypt.checkpw(temp_password.encode(), password_hash.encode())
                
                if is_valid:
                    print("✅ Password verification SUCCESS!")
                else:
                    print("❌ Password verification FAILED!")
                    
                    # Try with some common variations
                    variations = [
                        temp_password.strip(),
                        temp_password.replace(' ', ''),
                        temp_password.upper(),
                        temp_password.lower()
                    ]
                    
                    print("🔄 Trying password variations...")
                    for i, variation in enumerate(variations):
                        if bcrypt.checkpw(variation.encode(), password_hash.encode()):
                            print(f"✅ Variation {i+1} works: '{variation}'")
                            break
                    else:
                        print("❌ No variations worked")
                        
            except Exception as e:
                print(f"❌ Error testing password: {str(e)}")
            
            print("-" * 40)
        
        conn.close()
        
    except Exception as e:
        print(f"❌ Error testing passwords: {str(e)}")

def test_streamlit_auth():
    """Test the Streamlit authentication system."""
    print("\n🔐 TESTING STREAMLIT AUTHENTICATION SYSTEM")
    print("=" * 60)
    
    try:
        from utils.enhanced_security_config import StreamlitSecureAuth
        
        # Test authentication system
        auth_system = StreamlitSecureAuth('sqlite')
        print("✅ StreamlitSecureAuth initialized")
        
        # Get config for streamlit-authenticator
        config = auth_system.get_config_for_streamlit_authenticator()
        
        if config and 'credentials' in config:
            usernames = list(config['credentials']['usernames'].keys())
            print(f"✅ Found {len(usernames)} users in auth config: {usernames}")
            
            # Test authentication with a user
            if usernames:
                test_username = usernames[0]
                print(f"\n🧪 Testing authentication for: {test_username}")
                
                temp_password = input(f"Enter password for {test_username}: ").strip()
                
                success, user_data, message = auth_system.authenticate(test_username, temp_password)
                
                if success:
                    print("✅ Authentication SUCCESS!")
                    print(f"User data: {user_data}")
                else:
                    print(f"❌ Authentication FAILED: {message}")
            
        else:
            print("❌ Config generation failed")
            
    except ImportError:
        print("❌ Enhanced security config not available")
    except Exception as e:
        print(f"❌ Error testing Streamlit auth: {str(e)}")

def check_environment_variables():
    """Check environment variables."""
    print("\n🌍 CHECKING ENVIRONMENT VARIABLES")
    print("=" * 60)
    
    env_vars = [
        'USE_SQLITE',
        'SESSION_TIMEOUT_HOURS', 
        'MAX_LOGIN_ATTEMPTS',
        'ENABLE_AUDIT_LOG'
    ]
    
    for var in env_vars:
        value = os.getenv(var, 'NOT SET')
        print(f"{var}: {value}")
    
    # Check if SQLite should be used
    use_sqlite = os.getenv('USE_SQLITE', 'false').lower() == 'true'
    print(f"\n🎯 SQLite should be used: {use_sqlite}")

def check_migration_log():
    """Check migration log to see temporary passwords."""
    print("\n📋 CHECKING MIGRATION LOG FOR TEMPORARY PASSWORDS")
    print("=" * 60)
    
    backup_dir = "keys/migration_backup"
    if os.path.exists(backup_dir):
        # Look for password files
        password_files = [f for f in os.listdir(backup_dir) if 'password' in f.lower()]
        
        if password_files:
            print("🔑 Found password files:")
            for file in password_files:
                print(f"  • {file}")
                
            # Read the most recent one
            latest_file = max(password_files)
            file_path = os.path.join(backup_dir, latest_file)
            
            print(f"\n📖 Reading: {latest_file}")
            print("-" * 30)
            
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                print(content)
            except Exception as e:
                print(f"❌ Error reading file: {str(e)}")
        else:
            print("❌ No password files found in migration backup")
    else:
        print("❌ Migration backup directory not found")

def main():
    """Main debug function."""
    print("""
╔═══════════════════════════════════════════════════════════════════════════════╗
║                         SQLITE AUTHENTICATION DEBUG                          ║
║                     Diagnose SQLite Login Issues                             ║
╚═══════════════════════════════════════════════════════════════════════════════╝
    """)
    
    print("🛠️ DEBUG OPTIONS:")
    print("-" * 30)
    print("1. 🔍 Check SQLite Users")
    print("2. 🔑 Test Password Verification")
    print("3. 🔐 Test Streamlit Authentication")
    print("4. 🌍 Check Environment Variables")
    print("5. 📋 Check Migration Log (Find Passwords)")
    print("6. 🔄 Full Debug Sequence")
    print("7. ❌ Exit")
    
    while True:
        try:
            choice = input("\nSelect option (1-7): ").strip()
            
            if choice == "1":
                check_sqlite_users()
                break
                
            elif choice == "2":
                test_password_verification()
                break
                
            elif choice == "3":
                test_streamlit_auth()
                break
                
            elif choice == "4":
                check_environment_variables()
                break
                
            elif choice == "5":
                check_migration_log()
                break
                
            elif choice == "6":
                check_environment_variables()
                check_sqlite_users()
                check_migration_log()
                print("\n" + "="*60)
                print("Now test authentication with the passwords above:")
                test_streamlit_auth()
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
            break

if __name__ == "__main__":
    main()