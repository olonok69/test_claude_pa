import os
import json
import sqlite3
import hashlib
import secrets
import base64
import re
import string
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
import yaml
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
import bcrypt
import logging

class SecureUserStore:
    """Enhanced security user management with multiple storage options."""
    
    def __init__(self, storage_type: str = "sqlite", encryption_key: str = None):
        self.storage_type = storage_type
        self.encryption_key = encryption_key
        
        if storage_type == "sqlite":
            self.init_sqlite_database()
        elif storage_type == "encrypted_json":
            self.init_encryption()
        elif storage_type == "yaml":
            self.config_path = "keys/config.yaml"
    
    def init_sqlite_database(self):
        """Initialize SQLite database for user storage with migration-safe logic."""
        self.db_path = "keys/users.db"
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        
        # Check if database file exists before connecting
        db_exists = os.path.exists(self.db_path)
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Create users table if it doesn't exist
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
        logging.info("✅ Users table created successfully")
        
        # Create sessions table if it doesn't exist
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
        logging.info("✅ User sessions table created successfully")
        
        # Create audit log table if it doesn't exist
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
        
        # Create migration log table if it doesn't exist
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
        logging.info("✅ Migration log table created successfully")
        
        # Enhanced user creation logic with multiple safety checks
        if db_exists:
            logging.info("📂 Existing database found, checking user status...")
            
            # Check total users first
            cursor.execute('SELECT COUNT(*) FROM users')
            total_users = cursor.fetchone()[0]
            
            if total_users > 0:
                logging.info(f"👥 Found {total_users} existing users in database")
                
                # Check admin users
                cursor.execute('SELECT COUNT(*) FROM users WHERE is_admin = TRUE')
                admin_count = cursor.fetchone()[0]
                
                if admin_count > 0:
                    logging.info(f"👑 Found {admin_count} admin user(s) - no action needed")
                else:
                    logging.warning(f"⚠️  Found {total_users} users but NO admin users!")
                    logging.info("💡 Consider promoting an existing user to admin or manually creating one")
            else:
                logging.info("📝 Empty database found, creating default admin user")
                self.create_default_admin(cursor)
        else:
            logging.info("🆕 New database created, adding default admin user")
            self.create_default_admin(cursor)
        
        conn.commit()
        conn.close()
        
        logging.info("✅ SQLite database initialization complete")
    
    def init_encryption(self):
        """Initialize encryption for JSON storage."""
        if self.encryption_key:
            key = self.encryption_key.encode()
        else:
            # Generate key from password
            password = os.getenv('ENCRYPTION_PASSWORD', 'default_password_change_in_production')
            key = password.encode()
        
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=b'salt_change_in_production',
            iterations=100000,
        )
        key = base64.urlsafe_b64encode(kdf.derive(key))
        self.cipher = Fernet(key)
        
        self.encrypted_file_path = "keys/users_encrypted.json"
    
    def create_default_admin(self, cursor):
        """Create default admin user ONLY if specifically needed."""
        try:
            # Use environment variable for default password if available
            default_password = os.getenv('ADMIN_DEFAULT_PASSWORD', 'admin_password_change_immediately')
            password_hash = bcrypt.hashpw(default_password.encode(), bcrypt.gensalt()).decode()
            
            cursor.execute('''
                INSERT INTO users (username, password_hash, email, full_name, is_admin)
                VALUES (?, ?, ?, ?, ?)
            ''', ('admin', password_hash, 'admin@company.com', 'System Administrator', True))
            
            # Log the admin creation in audit log
            admin_id = cursor.lastrowid
            cursor.execute('''
                INSERT INTO audit_log (user_id, event_type, event_description)
                VALUES (?, ?, ?)
            ''', (admin_id, 'ADMIN_CREATED', 'Default admin user created during initialization'))
            
            logging.info("✅ Default admin user created successfully")
            logging.warning("🔐 IMPORTANT: Change the admin password immediately!")
            
        except sqlite3.IntegrityError as e:
            if "UNIQUE constraint failed" in str(e):
                logging.info("ℹ️  Admin user already exists (integrity constraint)")
            else:
                logging.error(f"❌ Error creating admin user: {str(e)}")
        except Exception as e:
            logging.error(f"❌ Unexpected error creating admin: {str(e)}")
    
    def hash_password(self, password: str) -> str:
        """Hash password using bcrypt - FIXED VERSION."""
        return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()
    
    def verify_password(self, password: str, hashed: str) -> bool:
        """Verify password against hash - FIXED VERSION."""
        try:
            return bcrypt.checkpw(password.encode(), hashed.encode())
        except Exception as e:
            logging.error(f"Password verification error: {str(e)}")
            return False
    
    def get_user_by_username(self, username: str) -> Optional[Dict]:
        """Get user details by username - FIXED VERSION."""
        if self.storage_type != "sqlite":
            return None
            
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT id, username, password_hash, email, full_name, is_admin, is_active
                FROM users WHERE username = ? AND is_active = TRUE
            ''', (username,))
            
            user = cursor.fetchone()
            conn.close()
            
            if user:
                return {
                    'id': user[0],
                    'username': user[1],
                    'password_hash': user[2],
                    'email': user[3],
                    'full_name': user[4],
                    'is_admin': bool(user[5]),
                    'is_active': bool(user[6])
                }
            return None
            
        except Exception as e:
            logging.error(f"Error getting user by username: {str(e)}")
            return None
    
    def authenticate_user(self, username: str, password: str) -> Optional[Dict]:
        """Authenticate user and return user info - FIXED VERSION."""
        if self.storage_type == "sqlite":
            return self._authenticate_sqlite(username, password)
        elif self.storage_type == "encrypted_json":
            return self._authenticate_encrypted(username, password)
        else:
            return self._authenticate_yaml(username, password)
    
    def _authenticate_sqlite(self, username: str, password: str) -> Optional[Dict]:
        """Authenticate against SQLite database - FIXED VERSION."""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT id, username, password_hash, email, full_name, is_admin, is_active, 
                       login_attempts, locked_until
                FROM users WHERE username = ?
            ''', (username,))
            
            user = cursor.fetchone()
            
            if not user:
                logging.info(f"❌ User {username} not found in database")
                conn.close()
                return None
                
            logging.info(f"✅ User {username} found, verifying password")
            user_id, username, password_hash, email, full_name, is_admin, is_active, login_attempts, locked_until = user
            
            # Check if account is locked
            if locked_until and datetime.fromisoformat(locked_until) > datetime.now():
                logging.warning(f"🔒 Account {username} is locked until {locked_until}")
                conn.close()
                return None
            
            # Check if account is active
            if not is_active:
                logging.warning(f"🚫 Account {username} is not active")
                conn.close()
                return None
            
            # Verify password
            if not self.verify_password(password, password_hash):
                logging.warning(f"❌ Invalid password for user {username}")
                
                # Increment failed attempts
                cursor.execute('''
                    UPDATE users 
                    SET failed_login_attempts = failed_login_attempts + 1,
                        last_failed_login = CURRENT_TIMESTAMP
                    WHERE id = ?
                ''', (user_id,))
                
                # Lock account if too many failed attempts
                if login_attempts >= 5:
                    lock_until = datetime.now() + timedelta(minutes=30)
                    cursor.execute('''
                        UPDATE users SET locked_until = ? WHERE id = ?
                    ''', (lock_until.isoformat(), user_id))
                    logging.warning(f"🔒 Account {username} locked due to too many failed attempts")
                
                conn.commit()
                conn.close()
                return None
            
            # Reset failed attempts and update last login
            cursor.execute('''
                UPDATE users 
                SET last_login = CURRENT_TIMESTAMP,
                    failed_login_attempts = 0,
                    locked_until = NULL
                WHERE id = ?
            ''', (user_id,))
            
            # Log successful login
            cursor.execute('''
                INSERT INTO audit_log (user_id, event_type, event_description)
                VALUES (?, ?, ?)
            ''', (user_id, 'USER_LOGIN', f'User {username} logged in successfully'))
            
            conn.commit()
            conn.close()
            
            logging.info(f"✅ User {username} authenticated successfully")
            
            return {
                'id': user_id,
                'username': username,
                'email': email,
                'name': full_name,
                'is_admin': is_admin
            }
            
        except Exception as e:
            logging.error(f"❌ SQLite authentication error for {username}: {str(e)}")
            return None
    
    def _authenticate_encrypted(self, username: str, password: str) -> Optional[Dict]:
        """Authenticate against encrypted JSON file."""
        try:
            users = self._load_encrypted_users()
            
            if username not in users:
                return None
            
            user = users[username]
            
            if not user.get('is_active', True):
                return None
            
            if not self.verify_password(password, user['password_hash']):
                return None
            
            # Update last login
            user['last_login'] = datetime.now().isoformat()
            self._save_encrypted_users(users)
            
            return {
                'username': username,
                'email': user['email'],
                'name': user['full_name'],
                'is_admin': user.get('is_admin', False)
            }
            
        except Exception:
            return None
    
    def _authenticate_yaml(self, username: str, password: str) -> Optional[Dict]:
        """Authenticate against YAML file (legacy)."""
        try:
            with open(self.config_path, 'r') as f:
                config = yaml.safe_load(f)
            
            users = config.get('credentials', {}).get('usernames', {})
            
            if username not in users:
                return None
            
            user = users[username]
            
            if not self.verify_password(password, user['password']):
                return None
            
            return {
                'username': username,
                'email': user['email'],
                'name': user['name'],
                'is_admin': user.get('is_admin', False)
            }
            
        except Exception:
            return None
    
    def get_all_users(self) -> List[Dict]:
        """Get all users - FIXED VERSION."""
        if self.storage_type == "sqlite":
            return self._get_users_sqlite()
        elif self.storage_type == "encrypted_json":
            return self._get_users_encrypted()
        else:
            return self._get_users_yaml()
    
    def _get_users_sqlite(self) -> List[Dict]:
        """Get users from SQLite database."""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT username, email, full_name, is_admin, is_active, 
                       created_at, last_login, failed_login_attempts
                FROM users
                ORDER BY created_at DESC
            ''')
            
            users = []
            for row in cursor.fetchall():
                users.append({
                    'username': row[0],
                    'email': row[1],
                    'name': row[2],
                    'is_admin': row[3],
                    'is_active': row[4],
                    'created_at': row[5],
                    'last_login': row[6],
                    'failed_attempts': row[7]
                })
            
            conn.close()
            return users
            
        except Exception:
            return []
    
    def create_session(self, user_id: int, ip_address: str = None, user_agent: str = None) -> str:
        """Create a new session token."""
        if self.storage_type != "sqlite":
            return None
        
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Generate secure session token
            import secrets
            session_token = secrets.token_urlsafe(32)
            expires_at = datetime.now() + timedelta(hours=24)
            
            cursor.execute('''
                INSERT INTO user_sessions (user_id, session_token, expires_at, ip_address, user_agent)
                VALUES (?, ?, ?, ?, ?)
            ''', (user_id, session_token, expires_at.isoformat(), ip_address, user_agent))
            
            conn.commit()
            conn.close()
            
            return session_token
            
        except Exception as e:
            logging.error(f"Error creating session: {str(e)}")
            return None
    
    def validate_session(self, session_token: str) -> Optional[Dict]:
        """Validate a session token."""
        if self.storage_type != "sqlite":
            return None
        
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT u.id, u.username, u.email, u.full_name, u.is_admin, s.expires_at
                FROM user_sessions s
                JOIN users u ON s.user_id = u.id
                WHERE s.session_token = ? AND s.is_active = TRUE
            ''', (session_token,))
            
            result = cursor.fetchone()
            
            if not result:
                conn.close()
                return None
            
            user_id, username, email, full_name, is_admin, expires_at = result
            
            # Check if session is expired
            if datetime.fromisoformat(expires_at) < datetime.now():
                # Deactivate expired session
                cursor.execute('''
                    UPDATE user_sessions SET is_active = FALSE WHERE session_token = ?
                ''', (session_token,))
                conn.commit()
                conn.close()
                return None
            
            conn.close()
            
            return {
                'id': user_id,
                'username': username,
                'email': email,
                'name': full_name,
                'is_admin': is_admin
            }
            
        except Exception as e:
            logging.error(f"Error validating session: {str(e)}")
            return None
    
    def get_audit_log(self, limit: int = 100) -> List[Dict]:
        """Get audit log entries."""
        if self.storage_type != "sqlite":
            return []
        
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT u.username, a.event_type, a.event_description, a.timestamp, a.ip_address
                FROM audit_log a
                LEFT JOIN users u ON a.user_id = u.id
                ORDER BY a.timestamp DESC
                LIMIT ?
            ''', (limit,))
            
            logs = []
            for row in cursor.fetchall():
                logs.append({
                    'username': row[0] or 'System',
                    'event_type': row[1],
                    'description': row[2],
                    'timestamp': row[3],
                    'ip_address': row[4]
                })
            
            conn.close()
            return logs
            
        except Exception:
            return []
    
    def _get_users_encrypted(self) -> List[Dict]:
        """Get users from encrypted JSON file."""
        try:
            users_data = self._load_encrypted_users()
            
            users = []
            for username, user_data in users_data.items():
                users.append({
                    'username': username,
                    'email': user_data['email'],
                    'name': user_data['full_name'],
                    'is_admin': user_data.get('is_admin', False),
                    'is_active': user_data.get('is_active', True),
                    'created_at': user_data.get('created_at'),
                    'last_login': user_data.get('last_login'),
                    'failed_attempts': user_data.get('login_attempts', 0)
                })
            
            return users
            
        except Exception:
            return []
    
    def _get_users_yaml(self) -> List[Dict]:
        """Get users from YAML file (legacy)."""
        try:
            with open(self.config_path, 'r') as f:
                config = yaml.safe_load(f)
            
            users_data = config.get('credentials', {}).get('usernames', {})
            
            users = []
            for username, user_data in users_data.items():
                users.append({
                    'username': username,
                    'email': user_data['email'],
                    'name': user_data['name'],
                    'is_admin': user_data.get('is_admin', False),
                    'is_active': True,
                    'created_at': user_data.get('created_at'),
                    'last_login': user_data.get('last_login'),
                    'failed_attempts': 0
                })
            
            return users
            
        except Exception:
            return []

# Integration with Streamlit authentication - FIXED VERSION
class StreamlitSecureAuth:
    """Enhanced Streamlit authentication with secure storage - FIXED VERSION."""
    
    def __init__(self, storage_type: str = None):
        if storage_type is None:
            storage_type = SecurityConfig.get_recommended_storage()
        
        self.user_store = SecureUserStore(storage_type)
        self.storage_type = storage_type
    
    def authenticate(self, username: str, password: str) -> Tuple[bool, Optional[Dict], str]:
        """
        Authenticate user with enhanced security - FIXED VERSION.
        Returns: (success, user_data, message)
        """
        try:
            logging.info(f"🔐 Attempting authentication for user: {username}")
            
            user_data = self.user_store.authenticate_user(username, password)
            
            if user_data:
                logging.info(f"✅ Authentication successful for user: {username}")
                
                # Create session if using SQLite
                if self.storage_type == "sqlite":
                    session_token = self.user_store.create_session(
                        user_data['id'],
                        ip_address=self._get_client_ip(),
                        user_agent=self._get_user_agent()
                    )
                    user_data['session_token'] = session_token
                
                return True, user_data, "Authentication successful"
            else:
                logging.warning(f"❌ Authentication failed for user: {username}")
                return False, None, "Invalid username or password"
                
        except Exception as e:
            logging.error(f"❌ Authentication error for {username}: {str(e)}")
            return False, None, f"Authentication error: {str(e)}"
    
    def get_config_for_streamlit_authenticator(self) -> Dict:
        """Generate config for streamlit-authenticator compatibility - FIXED VERSION."""
        try:
            users = self.user_store.get_all_users()
            
            config = {
                'credentials': {
                    'usernames': {}
                },
                'cookie': {
                    'expiry_days': int(os.getenv('SESSION_TIMEOUT_HOURS', 24)) // 24,
                    'key': os.getenv('COOKIE_KEY', 'default_key_change_in_production'),
                    'name': 'secure_auth_cookie'
                },
                'preauthorized': {
                    'emails': []
                }
            }
            
            # ✅ FIXED: Get actual password hashes from SQLite users
            for user in users:
                # Get the actual password hash from the database
                user_details = self.user_store.get_user_by_username(user['username'])
                if user_details:
                    config['credentials']['usernames'][user['username']] = {
                        'email': user['email'],
                        'name': user['name'],
                        'password': user_details['password_hash']  # ✅ ACTUAL HASH
                    }
                    
                    config['preauthorized']['emails'].append(user['email'])
            
            logging.info(f"✅ Generated config for {len(users)} users")
            return config
            
        except Exception as e:
            logging.error(f"❌ Error generating config: {str(e)}")
            return {
                'credentials': {'usernames': {}},
                'cookie': {
                    'expiry_days': 30,
                    'key': 'fallback_key',
                    'name': 'fallback_cookie'
                },
                'preauthorized': {'emails': []}
            }
    
    def _get_client_ip(self) -> str:
        """Get client IP address (placeholder for Streamlit implementation)."""
        return "127.0.0.1"  # In production, extract from request headers
    
    def _get_user_agent(self) -> str:
        """Get user agent (placeholder for Streamlit implementation)."""
        return "Streamlit App"  # In production, extract from request headers

# Configuration class to choose storage method
class SecurityConfig:
    """Configuration for security settings."""
    
    @staticmethod
    def get_recommended_storage() -> str:
        """Get recommended storage method based on environment."""
        if os.getenv('DATABASE_URL'):
            return "postgresql"  # For production with PostgreSQL
        elif os.getenv('USE_SQLITE', 'false').lower() == 'true':
            return "sqlite"
        elif os.getenv('USE_ENCRYPTION', 'false').lower() == 'true':
            return "encrypted_json"
        else:
            return "yaml"  # Default/legacy

# MIGRATION FUNCTION TO FIX EXISTING USERS - NEW ADDITION
def migrate_yaml_users_to_sqlite():
    """Migrate users from YAML to SQLite with proper password handling."""
    try:
        logging.info("🔄 Starting YAML to SQLite migration...")
        
        # Load YAML config
        yaml_path = "keys/config.yaml"
        if not os.path.exists(yaml_path):
            logging.error("❌ YAML config file not found")
            return False
        
        with open(yaml_path, 'r') as f:
            yaml_config = yaml.safe_load(f)
        
        yaml_users = yaml_config.get('credentials', {}).get('usernames', {})
        
        if not yaml_users:
            logging.warning("⚠️  No users found in YAML config")
            return False
        
        # Initialize SQLite store
        sqlite_store = SecureUserStore('sqlite')
        
        # Clear existing SQLite users to avoid conflicts
        conn = sqlite3.connect(sqlite_store.db_path)
        cursor = conn.cursor()
        cursor.execute('DELETE FROM users')
        conn.commit()
        
        # Migrate each user
        migrated_count = 0
        for username, user_data in yaml_users.items():
            try:
                # Insert user directly with existing password hash
                cursor.execute('''
                    INSERT INTO users (username, password_hash, email, full_name, is_admin, migrated_from_yaml)
                    VALUES (?, ?, ?, ?, ?, ?)
                ''', (
                    username,
                    user_data['password'],  # Use existing hash from YAML
                    user_data['email'],
                    user_data['name'],
                    user_data.get('is_admin', False),
                    True
                ))
                
                migrated_count += 1
                logging.info(f"✅ Migrated user: {username}")
                
            except Exception as e:
                logging.error(f"❌ Failed to migrate user {username}: {str(e)}")
        
        conn.commit()
        conn.close()
        
        logging.info(f"✅ Migration completed: {migrated_count} users migrated")
        return migrated_count > 0
        
    except Exception as e:
        logging.error(f"❌ Migration failed: {str(e)}")
        return False

# ADD TO __main__ FOR TESTING
if __name__ == "__main__":
    # Test function for debugging authentication
    def test_sqlite_auth():
        """Test SQLite authentication setup."""
        print("🧪 Testing SQLite Authentication...")
        
        # Test user store creation
        store = SecureUserStore('sqlite')
        print("✅ SQLite store created")
        
        # Test user lookup
        admin_user = store.get_user_by_username('admin')
        if admin_user:
            print(f"✅ Found admin user: {admin_user['email']}")
        else:
            print("❌ Admin user not found")
        
        # Test authentication
        auth = StreamlitSecureAuth('sqlite')
        success, user_data, message = auth.authenticate('admin', 'admin_password_change_immediately')
        
        if success:
            print(f"✅ Authentication successful: {user_data['name']}")
        else:
            print(f"❌ Authentication failed: {message}")
        
        # Test config generation
        config = auth.get_config_for_streamlit_authenticator()
        print(f"✅ Config generated with {len(config['credentials']['usernames'])} users")
        
        return success
    
    test_sqlite_auth()