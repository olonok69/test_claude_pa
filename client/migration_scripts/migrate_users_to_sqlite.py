#!/usr/bin/env python3
"""
User Migration Script: YAML to SQLite
Safely migrates users from YAML configuration to SQLite database
"""

import os
import sys
import yaml
import sqlite3
import bcrypt
import json
import shutil
from datetime import datetime
from typing import Dict, List, Tuple, Optional
import secrets
import string

class UserMigrator:
    """Handles migration of users from YAML to SQLite with full backup and recovery."""
    
    def __init__(self, yaml_config_path: str = "keys/config.yaml", 
                 sqlite_db_path: str = "keys/users.db"):
        self.yaml_config_path = yaml_config_path
        self.sqlite_db_path = sqlite_db_path
        self.backup_dir = "keys/migration_backup"
        self.migration_log = []
        
        # Ensure backup directory exists
        os.makedirs(self.backup_dir, exist_ok=True)
        os.makedirs(os.path.dirname(self.sqlite_db_path), exist_ok=True)
    
    def log_message(self, message: str, level: str = "INFO"):
        """Log migration messages."""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_entry = f"[{timestamp}] {level}: {message}"
        self.migration_log.append(log_entry)
        print(log_entry)
    
    def create_backup(self) -> bool:
        """Create backup of current configuration."""
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            
            # Backup YAML config
            if os.path.exists(self.yaml_config_path):
                backup_yaml = os.path.join(self.backup_dir, f"config_backup_{timestamp}.yaml")
                shutil.copy2(self.yaml_config_path, backup_yaml)
                self.log_message(f"Created YAML backup: {backup_yaml}")
            
            # Backup existing SQLite database if it exists
            if os.path.exists(self.sqlite_db_path):
                backup_db = os.path.join(self.backup_dir, f"users_backup_{timestamp}.db")
                shutil.copy2(self.sqlite_db_path, backup_db)
                self.log_message(f"Created SQLite backup: {backup_db}")
            
            return True
            
        except Exception as e:
            self.log_message(f"Backup creation failed: {str(e)}", "ERROR")
            return False
    
    def load_yaml_users(self) -> Optional[Dict]:
        """Load users from YAML configuration."""
        try:
            if not os.path.exists(self.yaml_config_path):
                self.log_message(f"YAML config file not found: {self.yaml_config_path}", "ERROR")
                return None
            
            with open(self.yaml_config_path, 'r') as file:
                config = yaml.safe_load(file)
            
            users_data = config.get('credentials', {}).get('usernames', {})
            preauth_emails = config.get('preauthorized', {}).get('emails', [])
            
            self.log_message(f"Loaded {len(users_data)} users from YAML config")
            
            return {
                'users': users_data,
                'preauthorized_emails': preauth_emails,
                'full_config': config
            }
            
        except Exception as e:
            self.log_message(f"Failed to load YAML config: {str(e)}", "ERROR")
            return None
    
    def init_sqlite_database(self) -> bool:
        """Initialize SQLite database with proper schema."""
        try:
            conn = sqlite3.connect(self.sqlite_db_path)
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
            
            # Create sessions table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS user_sessions (
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
                CREATE TABLE IF NOT EXISTS audit_log (
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
            
            # Create migration log table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS migration_log (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    migration_type TEXT NOT NULL,
                    migration_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    source_format TEXT,
                    target_format TEXT,
                    users_migrated INTEGER,
                    success BOOLEAN,
                    notes TEXT
                )
            ''')
            
            conn.commit()
            conn.close()
            
            self.log_message("SQLite database initialized successfully")
            return True
            
        except Exception as e:
            self.log_message(f"SQLite database initialization failed: {str(e)}", "ERROR")
            return False
    
    def generate_secure_password(self, length: int = 16) -> str:
        """Generate a secure temporary password."""
        lowercase = string.ascii_lowercase
        uppercase = string.ascii_uppercase
        digits = string.digits
        special_chars = "!@#$%^&*()_+-=[]{}|;:,.<>?"
        
        # Ensure at least one character from each category
        password = [
            secrets.choice(lowercase),
            secrets.choice(uppercase),
            secrets.choice(digits),
            secrets.choice(special_chars)
        ]
        
        # Fill the rest with random characters
        all_chars = lowercase + uppercase + digits + special_chars
        for _ in range(length - 4):
            password.append(secrets.choice(all_chars))
        
        # Shuffle the password
        secrets.SystemRandom().shuffle(password)
        return ''.join(password)
    
    def migrate_user(self, username: str, user_data: Dict, conn: sqlite3.Connection) -> Tuple[bool, str, str]:
        """
        Migrate a single user to SQLite.
        Returns: (success, temp_password, error_message)
        """
        try:
            cursor = conn.cursor()
            
            # Extract user information
            email = user_data.get('email', '')
            full_name = user_data.get('name', username)
            is_admin = user_data.get('is_admin', False)
            
            # Validate required fields
            if not email:
                return False, "", f"Missing email for user {username}"
            
            # Check if user already exists
            cursor.execute('SELECT username FROM users WHERE username = ? OR email = ?', 
                          (username, email))
            if cursor.fetchone():
                return False, "", f"User {username} or email {email} already exists in SQLite"
            
            # Generate new temporary password (old hash can't be migrated securely)
            temp_password = self.generate_secure_password()
            new_password_hash = bcrypt.hashpw(temp_password.encode(), bcrypt.gensalt()).decode()
            
            # Store original YAML data for reference
            original_data = json.dumps(user_data)
            
            # Insert user into SQLite
            cursor.execute('''
                INSERT INTO users (
                    username, password_hash, email, full_name, is_admin,
                    migrated_from_yaml, migration_date, original_yaml_data,
                    password_changed_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                username, new_password_hash, email, full_name, is_admin,
                True, datetime.now(), original_data, datetime.now()
            ))
            
            user_id = cursor.lastrowid
            
            # Log migration in audit table
            cursor.execute('''
                INSERT INTO audit_log (user_id, event_type, event_description)
                VALUES (?, ?, ?)
            ''', (user_id, 'USER_MIGRATED', f'User {username} migrated from YAML to SQLite'))
            
            return True, temp_password, ""
            
        except Exception as e:
            return False, "", f"Error migrating user {username}: {str(e)}"
    
    def perform_migration(self, dry_run: bool = False) -> Dict:
        """
        Perform the actual migration.
        
        Args:
            dry_run: If True, simulate migration without making changes
        
        Returns:
            Dict with migration results
        """
        migration_results = {
            'success': False,
            'users_processed': 0,
            'users_migrated': 0,
            'users_failed': 0,
            'temp_passwords': {},
            'errors': [],
            'warnings': []
        }
        
        try:
            # Step 1: Create backup
            if not dry_run:
                if not self.create_backup():
                    migration_results['errors'].append("Failed to create backup")
                    return migration_results
            
            # Step 2: Load YAML users
            yaml_data = self.load_yaml_users()
            if not yaml_data:
                migration_results['errors'].append("Failed to load YAML users")
                return migration_results
            
            users_data = yaml_data['users']
            migration_results['users_processed'] = len(users_data)
            
            if not users_data:
                migration_results['warnings'].append("No users found in YAML config")
                migration_results['success'] = True
                return migration_results
            
            # Step 3: Initialize SQLite database
            if not dry_run:
                if not self.init_sqlite_database():
                    migration_results['errors'].append("Failed to initialize SQLite database")
                    return migration_results
            
            # Step 4: Migrate users
            if not dry_run:
                conn = sqlite3.connect(self.sqlite_db_path)
            else:
                conn = None
            
            try:
                for username, user_data in users_data.items():
                    self.log_message(f"Processing user: {username}")
                    
                    if dry_run:
                        # Simulate migration
                        email = user_data.get('email', '')
                        if not email:
                            migration_results['errors'].append(f"User {username} missing email")
                            migration_results['users_failed'] += 1
                        else:
                            self.log_message(f"Would migrate user: {username} ({email})")
                            migration_results['users_migrated'] += 1
                            migration_results['temp_passwords'][username] = "[WOULD_BE_GENERATED]"
                    else:
                        # Actual migration
                        success, temp_password, error = self.migrate_user(username, user_data, conn)
                        
                        if success:
                            migration_results['users_migrated'] += 1
                            migration_results['temp_passwords'][username] = temp_password
                            self.log_message(f"Successfully migrated user: {username}")
                        else:
                            migration_results['users_failed'] += 1
                            migration_results['errors'].append(error)
                            self.log_message(error, "ERROR")
                
                if not dry_run:
                    # Record migration in database
                    cursor = conn.cursor()
                    cursor.execute('''
                        INSERT INTO migration_log (
                            migration_type, source_format, target_format, 
                            users_migrated, success, notes
                        ) VALUES (?, ?, ?, ?, ?, ?)
                    ''', (
                        'YAML_TO_SQLITE', 'YAML', 'SQLite',
                        migration_results['users_migrated'],
                        migration_results['users_failed'] == 0,
                        f"Processed {migration_results['users_processed']} users"
                    ))
                    
                    conn.commit()
                
            finally:
                if conn:
                    conn.close()
            
            # Step 5: Save migration report
            migration_results['success'] = migration_results['users_failed'] == 0
            self.save_migration_report(migration_results, dry_run)
            
            return migration_results
            
        except Exception as e:
            error_msg = f"Migration failed with exception: {str(e)}"
            self.log_message(error_msg, "ERROR")
            migration_results['errors'].append(error_msg)
            return migration_results
    
    def save_migration_report(self, results: Dict, dry_run: bool):
        """Save detailed migration report."""
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            report_type = "dry_run" if dry_run else "actual"
            report_file = os.path.join(self.backup_dir, f"migration_report_{report_type}_{timestamp}.json")
            
            report_data = {
                'migration_type': 'YAML_TO_SQLITE',
                'dry_run': dry_run,
                'timestamp': datetime.now().isoformat(),
                'results': results,
                'log_messages': self.migration_log
            }
            
            with open(report_file, 'w') as f:
                json.dump(report_data, f, indent=2)
            
            self.log_message(f"Migration report saved: {report_file}")
            
            # Also save temporary passwords separately for security
            if not dry_run and results.get('temp_passwords'):
                passwords_file = os.path.join(self.backup_dir, f"temp_passwords_{timestamp}.txt")
                with open(passwords_file, 'w') as f:
                    f.write("TEMPORARY PASSWORDS FOR MIGRATED USERS\n")
                    f.write("=" * 50 + "\n")
                    f.write("IMPORTANT: Users must change these passwords on first login!\n\n")
                    
                    for username, password in results['temp_passwords'].items():
                        f.write(f"Username: {username}\n")
                        f.write(f"Temp Password: {password}\n")
                        f.write("-" * 30 + "\n")
                
                self.log_message(f"Temporary passwords saved: {passwords_file}")
                
        except Exception as e:
            self.log_message(f"Failed to save migration report: {str(e)}", "ERROR")
    
    def verify_migration(self) -> Dict:
        """Verify the migration was successful."""
        verification_results = {
            'success': False,
            'sqlite_users': 0,
            'yaml_users': 0,
            'missing_users': [],
            'extra_users': [],
            'data_integrity_issues': []
        }
        
        try:
            # Load YAML users
            yaml_data = self.load_yaml_users()
            if not yaml_data:
                verification_results['data_integrity_issues'].append("Cannot load YAML data")
                return verification_results
            
            yaml_users = set(yaml_data['users'].keys())
            verification_results['yaml_users'] = len(yaml_users)
            
            # Load SQLite users
            if not os.path.exists(self.sqlite_db_path):
                verification_results['data_integrity_issues'].append("SQLite database not found")
                return verification_results
            
            conn = sqlite3.connect(self.sqlite_db_path)
            cursor = conn.cursor()
            
            cursor.execute('SELECT username, email, full_name, is_admin FROM users WHERE migrated_from_yaml = TRUE')
            sqlite_users_data = cursor.fetchall()
            sqlite_users = set(row[0] for row in sqlite_users_data)
            verification_results['sqlite_users'] = len(sqlite_users)
            
            # Find differences
            verification_results['missing_users'] = list(yaml_users - sqlite_users)
            verification_results['extra_users'] = list(sqlite_users - yaml_users)
            
            # Verify data integrity for common users
            for username, email, full_name, is_admin in sqlite_users_data:
                if username in yaml_data['users']:
                    yaml_user = yaml_data['users'][username]
                    
                    # Check email
                    if email != yaml_user.get('email', ''):
                        verification_results['data_integrity_issues'].append(
                            f"Email mismatch for {username}: SQLite='{email}' vs YAML='{yaml_user.get('email', '')}'"
                        )
                    
                    # Check name
                    if full_name != yaml_user.get('name', ''):
                        verification_results['data_integrity_issues'].append(
                            f"Name mismatch for {username}: SQLite='{full_name}' vs YAML='{yaml_user.get('name', '')}'"
                        )
                    
                    # Check admin status
                    yaml_is_admin = yaml_user.get('is_admin', False)
                    if bool(is_admin) != bool(yaml_is_admin):
                        verification_results['data_integrity_issues'].append(
                            f"Admin status mismatch for {username}: SQLite={bool(is_admin)} vs YAML={bool(yaml_is_admin)}"
                        )
            
            conn.close()
            
            # Overall success check
            verification_results['success'] = (
                len(verification_results['missing_users']) == 0 and
                len(verification_results['data_integrity_issues']) == 0
            )
            
            return verification_results
            
        except Exception as e:
            verification_results['data_integrity_issues'].append(f"Verification failed: {str(e)}")
            return verification_results
    
    def rollback_migration(self) -> bool:
        """Rollback migration by restoring from backup."""
        try:
            # Find most recent backup
            backup_files = [f for f in os.listdir(self.backup_dir) if f.startswith('config_backup_')]
            if not backup_files:
                self.log_message("No backup files found for rollback", "ERROR")
                return False
            
            # Get most recent backup
            backup_files.sort(reverse=True)
            latest_backup = os.path.join(self.backup_dir, backup_files[0])
            
            # Restore YAML config
            shutil.copy2(latest_backup, self.yaml_config_path)
            self.log_message(f"Restored YAML config from: {latest_backup}")
            
            # Remove SQLite database
            if os.path.exists(self.sqlite_db_path):
                os.remove(self.sqlite_db_path)
                self.log_message("Removed SQLite database")
            
            self.log_message("Migration rollback completed successfully")
            return True
            
        except Exception as e:
            self.log_message(f"Rollback failed: {str(e)}", "ERROR")
            return False


def print_banner():
    """Print migration script banner."""
    print("""
╔═══════════════════════════════════════════════════════════════════════════════╗
║                          USER MIGRATION SCRIPT                               ║
║                          YAML → SQLite Migration                             ║
╠═══════════════════════════════════════════════════════════════════════════════╣
║  This script will migrate your users from YAML configuration to SQLite       ║
║  database with enhanced security features.                                   ║
║                                                                               ║
║  ⚠️  IMPORTANT SECURITY NOTICE:                                               ║
║  - Users will receive new temporary passwords                                ║
║  - Original password hashes cannot be migrated securely                      ║
║  - Users must change passwords on first login                                ║
║  - Automatic backup will be created before migration                         ║
╚═══════════════════════════════════════════════════════════════════════════════╝
    """)


def main():
    """Main migration script."""
    print_banner()
    
    # Initialize migrator
    migrator = UserMigrator()
    
    # Show current status
    print("\n🔍 CURRENT STATUS:")
    print("-" * 50)
    
    yaml_exists = os.path.exists(migrator.yaml_config_path)
    sqlite_exists = os.path.exists(migrator.sqlite_db_path)
    
    print(f"YAML Config: {'✅ Found' if yaml_exists else '❌ Not found'} ({migrator.yaml_config_path})")
    print(f"SQLite DB:   {'⚠️  Exists' if sqlite_exists else '✅ Ready'} ({migrator.sqlite_db_path})")
    
    if not yaml_exists:
        print("\n❌ No YAML configuration found. Nothing to migrate.")
        return
    
    # Load and show YAML users
    yaml_data = migrator.load_yaml_users()
    if yaml_data:
        users = yaml_data['users']
        print(f"\n📊 Found {len(users)} users in YAML config:")
        for username, user_data in users.items():
            admin_status = "👑 Admin" if user_data.get('is_admin', False) else "👤 User"
            print(f"  • {username} ({user_data.get('email', 'no-email')}) - {admin_status}")
    
    # Migration options
    print("\n🚀 MIGRATION OPTIONS:")
    print("-" * 50)
    print("1. 🧪 Dry Run (simulate migration)")
    print("2. 🔄 Full Migration")
    print("3. ✅ Verify Existing Migration")
    print("4. ↩️  Rollback Migration")
    print("5. ❌ Exit")
    
    while True:
        try:
            choice = input("\nSelect option (1-5): ").strip()
            
            if choice == "1":
                print("\n🧪 Running Dry Run Migration...")
                results = migrator.perform_migration(dry_run=True)
                print_migration_results(results, dry_run=True)
                break
                
            elif choice == "2":
                # Confirm full migration
                print("\n⚠️  FINAL CONFIRMATION:")
                print("This will:")
                print("• Create backup of current YAML config")
                print("• Create new SQLite database")
                print("• Generate new temporary passwords for all users")
                print("• Users will need to reset passwords on first login")
                
                confirm = input("\nProceed with full migration? (type 'YES' to confirm): ").strip()
                if confirm == "YES":
                    print("\n🔄 Running Full Migration...")
                    results = migrator.perform_migration(dry_run=False)
                    print_migration_results(results, dry_run=False)
                    
                    if results['success']:
                        print("\n✅ Migration completed successfully!")
                        print("📋 Next steps:")
                        print("1. Update your application to use SQLite storage")
                        print("2. Distribute temporary passwords to users")
                        print("3. Ensure users change passwords on first login")
                        print("4. Test authentication with new system")
                    else:
                        print("\n❌ Migration completed with errors!")
                        print("Review the migration report for details.")
                else:
                    print("Migration cancelled.")
                break
                
            elif choice == "3":
                print("\n✅ Verifying Migration...")
                results = migrator.verify_migration()
                print_verification_results(results)
                break
                
            elif choice == "4":
                confirm = input("\n⚠️  Rollback will restore YAML config and remove SQLite database. Continue? (y/N): ").strip()
                if confirm.lower() == 'y':
                    print("\n↩️  Rolling back migration...")
                    if migrator.rollback_migration():
                        print("✅ Rollback completed successfully!")
                    else:
                        print("❌ Rollback failed!")
                else:
                    print("Rollback cancelled.")
                break
                
            elif choice == "5":
                print("👋 Exiting migration script.")
                break
                
            else:
                print("❌ Invalid option. Please select 1-5.")
                
        except KeyboardInterrupt:
            print("\n\n👋 Migration script interrupted by user.")
            break
        except Exception as e:
            print(f"\n❌ Error: {str(e)}")
            break


def print_migration_results(results: Dict, dry_run: bool):
    """Print formatted migration results."""
    print(f"\n{'🧪 DRY RUN' if dry_run else '🔄 MIGRATION'} RESULTS:")
    print("=" * 50)
    
    print(f"📊 Users processed: {results['users_processed']}")
    print(f"✅ Users migrated: {results['users_migrated']}")
    print(f"❌ Users failed: {results['users_failed']}")
    
    if results['errors']:
        print(f"\n❌ Errors ({len(results['errors'])}):")
        for error in results['errors']:
            print(f"  • {error}")
    
    if results['warnings']:
        print(f"\n⚠️  Warnings ({len(results['warnings'])}):")
        for warning in results['warnings']:
            print(f"  • {warning}")
    
    if not dry_run and results['temp_passwords']:
        print(f"\n🔑 Temporary Passwords Generated:")
        print("⚠️  SECURITY: Save these passwords securely and distribute to users!")
        print("-" * 30)
        for username, password in results['temp_passwords'].items():
            print(f"  {username}: {password}")
        print("-" * 30)
        print("📝 Passwords also saved to migration backup directory")


def print_verification_results(results: Dict):
    """Print formatted verification results."""
    print("\n✅ VERIFICATION RESULTS:")
    print("=" * 50)
    
    print(f"📊 YAML users: {results['yaml_users']}")
    print(f"📊 SQLite users: {results['sqlite_users']}")
    
    if results['missing_users']:
        print(f"\n❌ Missing users in SQLite ({len(results['missing_users'])}):")
        for user in results['missing_users']:
            print(f"  • {user}")
    
    if results['extra_users']:
        print(f"\n⚠️  Extra users in SQLite ({len(results['extra_users'])}):")
        for user in results['extra_users']:
            print(f"  • {user}")
    
    if results['data_integrity_issues']:
        print(f"\n❌ Data integrity issues ({len(results['data_integrity_issues'])}):")
        for issue in results['data_integrity_issues']:
            print(f"  • {issue}")
    
    overall_status = "✅ PASSED" if results['success'] else "❌ FAILED"
    print(f"\n🎯 Overall verification: {overall_status}")


if __name__ == "__main__":
    main()