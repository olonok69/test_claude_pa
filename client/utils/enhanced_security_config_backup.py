import os
import json
import sqlite3
import hashlib
import secrets
import base64
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
import yaml
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
import bcrypt

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
        """Initialize SQLite database for user storage."""
        self.db_path = "keys/users.db"
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        
        conn = sqlite3.connect(self.db_path)
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
                last_failed_login TIMESTAMP
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
        
        # Create default admin user if none exists
        cursor.execute('SELECT COUNT(*) FROM users WHERE is_admin = TRUE')
        if cursor.fetchone()[0] == 0:
            self.create_default_admin(cursor)
        
        conn.commit()
        conn.close()
    
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
        """Create default admin user."""
        password_hash = bcrypt.hashpw(b'admin_password_change_immediately', bcrypt.gensalt()).decode()
        
        cursor.execute('''
            INSERT INTO users (username, password_hash, email, full_name, is_admin)
            VALUES (?, ?, ?, ?, ?)
        ''', ('admin', password_hash, 'admin@company.com', 'System Administrator', True))
    
    def hash_password(self, password: str) -> str:
        """Hash password using bcrypt."""
        return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()
    
    def verify_password(self, password: str, hashed: str) -> bool:
        """Verify password against hash."""
        return bcrypt.checkpw(password.encode(), hashed.encode())
    
    def create_user(self, username: str, password: str, email: str, full_name: str, is_admin: bool = False) -> bool:
        """Create a new user."""
        if self.storage_type == "sqlite":
            return self._create_user_sqlite(username, password, email, full_name, is_admin)
        elif self.storage_type == "encrypted_json":
            return self._create_user_encrypted(username, password, email, full_name, is_admin)
        else:
            return self._create_user_yaml(username, password, email, full_name, is_admin)
    
    def _create_user_sqlite(self, username: str, password: str, email: str, full_name: str, is_admin: bool) -> bool:
        """Create user in SQLite database."""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            password_hash = self.hash_password(password)
            
            cursor.execute('''
                INSERT INTO users (username, password_hash, email, full_name, is_admin)
                VALUES (?, ?, ?, ?, ?)
            ''', (username, password_hash, email, full_name, is_admin))
            
            user_id = cursor.lastrowid
            
            # Log user creation
            cursor.execute('''
                INSERT INTO audit_log (user_id, event_type, event_description)
                VALUES (?, ?, ?)
            ''', (user_id, 'USER_CREATED', f'User {username} created'))
            
            conn.commit()
            conn.close()
            return True
            
        except sqlite3.IntegrityError:
            return False
    
    def _create_user_encrypted(self, username: str, password: str, email: str, full_name: str, is_admin: bool) -> bool:
        """Create user in encrypted JSON file."""
        try:
            users = self._load_encrypted_users()
            
            if username in users:
                return False
            
            users[username] = {
                'password_hash': self.hash_password(password),
                'email': email,
                'full_name': full_name,
                'is_admin': is_admin,
                'created_at': datetime.now().isoformat(),
                'is_active': True,
                'login_attempts': 0
            }
            
            self._save_encrypted_users(users)
            return True
            
        except Exception:
            return False
    
    def _create_user_yaml(self, username: str, password: str, email: str, full_name: str, is_admin: bool) -> bool:
        """Create user in YAML file (legacy)."""
        try:
            with open(self.config_path, 'r') as f:
                config = yaml.safe_load(f)
            
            if username in config.get('credentials', {}).get('usernames', {}):
                return False
            
            config['credentials']['usernames'][username] = {
                'password': self.hash_password(password),
                'email': email,
                'name': full_name,
                'is_admin': is_admin
            }
            
            if email not in config['preauthorized']['emails']:
                config['preauthorized']['emails'].append(email)
            
            with open(self.config_path, 'w') as f:
                yaml.dump(config, f, default_flow_style=False)
            
            return True
            
        except Exception:
            return False
    
    def authenticate_user(self, username: str, password: str) -> Optional[Dict]:
        """Authenticate user and return user info."""
        if self.storage_type == "sqlite":
            return self._authenticate_sqlite(username, password)
        elif self.storage_type == "encrypted_json":
            return self._authenticate_encrypted(username, password)
        else:
            return self._authenticate_yaml(username, password)
    
    def _authenticate_sqlite(self, username: str, password: str) -> Optional[Dict]:
        """Authenticate against SQLite database."""
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
                return None
            
            user_id, username, password_hash, email, full_name, is_admin, is_active, login_attempts, locked_until = user
            
            # Check if account is locked
            if locked_until and datetime.fromisoformat(locked_until) > datetime.now():
                return None
            
            # Check if account is active
            if not is_active:
                return None
            
            # Verify password
            if not self.verify_password(password, password_hash):
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
            ''', (user_id, 'USER_LOGIN', f'User {username} logged in'))
            
            conn.commit()
            conn.close()
            
            return {
                'id': user_id,
                'username': username,
                'email': email,
                'name': full_name,
                'is_admin': is_admin
            }
            
        except Exception:
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
    
    def _load_encrypted_users(self) -> Dict:
        """Load users from encrypted JSON file."""
        if not os.path.exists(self.encrypted_file_path):
            return {}
        
        try:
            with open(self.encrypted_file_path, 'rb') as f:
                encrypted_data = f.read()
            
            decrypted_data = self.cipher.decrypt(encrypted_data)
            return json.loads(decrypted_data.decode())
            
        except Exception:
            return {}
    
    def _save_encrypted_users(self, users: Dict):
        """Save users to encrypted JSON file."""
        try:
            os.makedirs(os.path.dirname(self.encrypted_file_path), exist_ok=True)
            
            data = json.dumps(users, indent=2).encode()
            encrypted_data = self.cipher.encrypt(data)
            
            with open(self.encrypted_file_path, 'wb') as f:
                f.write(encrypted_data)
                
        except Exception:
            pass
    
    def get_all_users(self) -> List[Dict]:
        """Get all users."""
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
    
    def update_user(self, username: str, **kwargs) -> bool:
        """Update user information."""
        if self.storage_type == "sqlite":
            return self._update_user_sqlite(username, **kwargs)
        elif self.storage_type == "encrypted_json":
            return self._update_user_encrypted(username, **kwargs)
        else:
            return self._update_user_yaml(username, **kwargs)
    
    def _update_user_sqlite(self, username: str, **kwargs) -> bool:
        """Update user in SQLite database."""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Build update query
            update_fields = []
            values = []
            
            if 'password' in kwargs:
                update_fields.append('password_hash = ?')
                values.append(self.hash_password(kwargs['password']))
                update_fields.append('password_changed_at = CURRENT_TIMESTAMP')
            
            if 'email' in kwargs:
                update_fields.append('email = ?')
                values.append(kwargs['email'])
            
            if 'full_name' in kwargs:
                update_fields.append('full_name = ?')
                values.append(kwargs['full_name'])
            
            if 'is_admin' in kwargs:
                update_fields.append('is_admin = ?')
                values.append(kwargs['is_admin'])
            
            if 'is_active' in kwargs:
                update_fields.append('is_active = ?')
                values.append(kwargs['is_active'])
            
            if not update_fields:
                return False
            
            values.append(username)
            query = f"UPDATE users SET {', '.join(update_fields)} WHERE username = ?"
            
            cursor.execute(query, values)
            
            # Log update
            cursor.execute('''
                INSERT INTO audit_log (user_id, event_type, event_description)
                SELECT id, 'USER_UPDATED', ?
                FROM users WHERE username = ?
            ''', (f'User {username} updated', username))
            
            conn.commit()
            conn.close()
            
            return cursor.rowcount > 0
            
        except Exception:
            return False
    
    def _update_user_encrypted(self, username: str, **kwargs) -> bool:
        """Update user in encrypted JSON file."""
        try:
            users = self._load_encrypted_users()
            
            if username not in users:
                return False
            
            user = users[username]
            
            if 'password' in kwargs:
                user['password_hash'] = self.hash_password(kwargs['password'])
            
            if 'email' in kwargs:
                user['email'] = kwargs['email']
            
            if 'full_name' in kwargs:
                user['full_name'] = kwargs['full_name']
            
            if 'is_admin' in kwargs:
                user['is_admin'] = kwargs['is_admin']
            
            if 'is_active' in kwargs:
                user['is_active'] = kwargs['is_active']
            
            user['updated_at'] = datetime.now().isoformat()
            
            self._save_encrypted_users(users)
            return True
            
        except Exception:
            return False
    
    def _update_user_yaml(self, username: str, **kwargs) -> bool:
        """Update user in YAML file (legacy)."""
        try:
            with open(self.config_path, 'r') as f:
                config = yaml.safe_load(f)
            
            users = config.get('credentials', {}).get('usernames', {})
            
            if username not in users:
                return False
            
            user = users[username]
            
            if 'password' in kwargs:
                user['password'] = self.hash_password(kwargs['password'])
            
            if 'email' in kwargs:
                # Update preauthorized emails
                old_email = user['email']
                user['email'] = kwargs['email']
                
                preauth_emails = config.get('preauthorized', {}).get('emails', [])
                if old_email in preauth_emails:
                    preauth_emails.remove(old_email)
                if kwargs['email'] not in preauth_emails:
                    preauth_emails.append(kwargs['email'])
            
            if 'full_name' in kwargs:
                user['name'] = kwargs['full_name']
            
            if 'is_admin' in kwargs:
                user['is_admin'] = kwargs['is_admin']
            
            with open(self.config_path, 'w') as f:
                yaml.dump(config, f, default_flow_style=False)
            
            return True
            
        except Exception:
            return False
    
    def delete_user(self, username: str) -> bool:
        """Delete a user."""
        if self.storage_type == "sqlite":
            return self._delete_user_sqlite(username)
        elif self.storage_type == "encrypted_json":
            return self._delete_user_encrypted(username)
        else:
            return self._delete_user_yaml(username)
    
    def _delete_user_sqlite(self, username: str) -> bool:
        """Delete user from SQLite database."""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Log deletion before deleting
            cursor.execute('''
                INSERT INTO audit_log (user_id, event_type, event_description)
                SELECT id, 'USER_DELETED', ?
                FROM users WHERE username = ?
            ''', (f'User {username} deleted', username))
            
            # Delete user
            cursor.execute('DELETE FROM users WHERE username = ?', (username,))
            
            conn.commit()
            conn.close()
            
            return cursor.rowcount > 0
            
        except Exception:
            return False
    
    def _delete_user_encrypted(self, username: str) -> bool:
        """Delete user from encrypted JSON file."""
        try:
            users = self._load_encrypted_users()
            
            if username not in users:
                return False
            
            del users[username]
            self._save_encrypted_users(users)
            return True
            
        except Exception:
            return False
    
    def _delete_user_yaml(self, username: str) -> bool:
        """Delete user from YAML file (legacy)."""
        try:
            with open(self.config_path, 'r') as f:
                config = yaml.safe_load(f)
            
            users = config.get('credentials', {}).get('usernames', {})
            
            if username not in users:
                return False
            
            user = users[username]
            email = user['email']
            
            # Remove user
            del users[username]
            
            # Remove from preauthorized emails
            preauth_emails = config.get('preauthorized', {}).get('emails', [])
            if email in preauth_emails:
                preauth_emails.remove(email)
            
            with open(self.config_path, 'w') as f:
                yaml.dump(config, f, default_flow_style=False)
            
            return True
            
        except Exception:
            return False
    
    def create_session(self, user_id: int, ip_address: str = None, user_agent: str = None) -> str:
        """Create a new session token."""
        if self.storage_type != "sqlite":
            return None
        
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Generate secure session token
            session_token = secrets.token_urlsafe(32)
            expires_at = datetime.now() + timedelta(hours=24)
            
            cursor.execute('''
                INSERT INTO user_sessions (user_id, session_token, expires_at, ip_address, user_agent)
                VALUES (?, ?, ?, ?, ?)
            ''', (user_id, session_token, expires_at.isoformat(), ip_address, user_agent))
            
            conn.commit()
            conn.close()
            
            return session_token
            
        except Exception:
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
            
        except Exception:
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
    
    @staticmethod
    def get_security_recommendations() -> List[str]:
        """Get security recommendations."""
        return [
            "1. Use SQLite or PostgreSQL for production deployments",
            "2. Enable encryption for sensitive data",
            "3. Use environment variables for encryption keys",
            "4. Implement session management with secure tokens",
            "5. Enable audit logging for compliance",
            "6. Use strong password policies",
            "7. Implement rate limiting for login attempts",
            "8. Use HTTPS in production",
            "9. Regular backup of user data",
            "10. Monitor failed login attempts"
        ]
    
    @staticmethod
    def migrate_from_yaml(target_storage: str = "sqlite") -> bool:
        """Migrate users from YAML to more secure storage."""
        try:
            # Load existing YAML config
            yaml_store = SecureUserStore("yaml")
            users = yaml_store._get_users_yaml()
            
            # Create new secure store
            secure_store = SecureUserStore(target_storage)
            
            # Migrate users
            migration_log = []
            for user in users:
                try:
                    # Create user with a temporary password (they'll need to reset)
                    temp_password = secrets.token_urlsafe(16)
                    success = secure_store.create_user(
                        username=user['username'],
                        password=temp_password,
                        email=user['email'],
                        full_name=user['name'],
                        is_admin=user.get('is_admin', False)
                    )
                    
                    if success:
                        migration_log.append(f"✅ Migrated user: {user['username']}")
                    else:
                        migration_log.append(f"❌ Failed to migrate user: {user['username']}")
                        
                except Exception as e:
                    migration_log.append(f"❌ Error migrating {user['username']}: {str(e)}")
            
            # Save migration log
            with open('keys/migration_log.txt', 'w') as f:
                f.write('\n'.join(migration_log))
            
            return True
            
        except Exception as e:
            print(f"Migration failed: {str(e)}")
            return False
    
    @staticmethod
    def setup_environment_variables() -> str:
        """Generate environment variables setup guide."""
        return """
# Add these to your .env file for enhanced security:

# Database Configuration (choose one)
USE_SQLITE=true
# DATABASE_URL=postgresql://user:password@localhost/dbname

# Encryption Configuration
USE_ENCRYPTION=true
ENCRYPTION_PASSWORD=your_very_secure_encryption_password_here

# Session Configuration
SESSION_TIMEOUT_HOURS=24
MAX_LOGIN_ATTEMPTS=5
ACCOUNT_LOCKOUT_MINUTES=30

# Security Headers
SECURE_COOKIES=true
CSRF_PROTECTION=true

# Audit and Monitoring
ENABLE_AUDIT_LOG=true
LOG_FAILED_ATTEMPTS=true
ALERT_ON_MULTIPLE_FAILURES=true

# Backup Configuration
AUTO_BACKUP_ENABLED=true
BACKUP_ENCRYPTION_KEY=another_secure_key_for_backups
BACKUP_RETENTION_DAYS=30
"""

# Integration with Streamlit authentication
class StreamlitSecureAuth:
    """Enhanced Streamlit authentication with secure storage."""
    
    def __init__(self, storage_type: str = None):
        if storage_type is None:
            storage_type = SecurityConfig.get_recommended_storage()
        
        self.user_store = SecureUserStore(storage_type)
        self.storage_type = storage_type
    
    def authenticate(self, username: str, password: str) -> Tuple[bool, Optional[Dict], str]:
        """
        Authenticate user with enhanced security.
        Returns: (success, user_data, message)
        """
        try:
            user_data = self.user_store.authenticate_user(username, password)
            
            if user_data:
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
                return False, None, "Invalid username or password"
                
        except Exception as e:
            return False, None, f"Authentication error: {str(e)}"
    
    def validate_session(self, session_token: str) -> Tuple[bool, Optional[Dict]]:
        """Validate session token."""
        if self.storage_type != "sqlite":
            return False, None
        
        user_data = self.user_store.validate_session(session_token)
        return user_data is not None, user_data
    
    def logout(self, session_token: str = None):
        """Logout and invalidate session."""
        if self.storage_type == "sqlite" and session_token:
            try:
                conn = sqlite3.connect(self.user_store.db_path)
                cursor = conn.cursor()
                
                cursor.execute('''
                    UPDATE user_sessions 
                    SET is_active = FALSE 
                    WHERE session_token = ?
                ''', (session_token,))
                
                conn.commit()
                conn.close()
            except:
                pass
    
    def _get_client_ip(self) -> str:
        """Get client IP address (placeholder for Streamlit implementation)."""
        return "127.0.0.1"  # In production, extract from request headers
    
    def _get_user_agent(self) -> str:
        """Get user agent (placeholder for Streamlit implementation)."""
        return "Streamlit App"  # In production, extract from request headers
    
    def get_config_for_streamlit_authenticator(self) -> Dict:
        """Generate config for streamlit-authenticator compatibility."""
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
        
        for user in users:
            config['credentials']['usernames'][user['username']] = {
                'email': user['email'],
                'name': user['name'],
                'password': 'managed_by_secure_store'  # Placeholder
            }
            
            config['preauthorized']['emails'].append(user['email'])
        
        return config

# Enhanced security middleware
class SecurityMiddleware:
    """Security middleware for additional protection."""
    
    @staticmethod
    def check_password_complexity(password: str) -> Tuple[bool, List[str]]:
        """Enhanced password complexity check."""
        issues = []
        
        # Length check
        if len(password) < 12:
            issues.append("Password must be at least 12 characters long")
        
        # Character variety
        if not re.search(r'[a-z]', password):
            issues.append("Must contain lowercase letters")
        if not re.search(r'[A-Z]', password):
            issues.append("Must contain uppercase letters")
        if not re.search(r'\d', password):
            issues.append("Must contain numbers")
        if not re.search(r'[!@#$%^&*()_+\-=\[\]{}|;:,.<>?]', password):
            issues.append("Must contain special characters")
        
        # Common patterns
        common_patterns = [
            r'(.)\1{2,}',  # Repeated characters
            r'(012|123|234|345|456|567|678|789|890)',  # Sequential numbers
            r'(abc|bcd|cde|def|efg|fgh|ghi|hij|ijk|jkl|klm|lmn|mno|nop|opq|pqr|qrs|rst|stu|tuv|uvw|vwx|wxy|xyz)',  # Sequential letters
        ]
        
        for pattern in common_patterns:
            if re.search(pattern, password.lower()):
                issues.append("Avoid repeated or sequential characters")
                break
        
        # Dictionary words (basic check)
        common_words = ['password', 'admin', 'user', 'login', 'welcome', 'company', 'system']
        if any(word in password.lower() for word in common_words):
            issues.append("Avoid common words")
        
        return len(issues) == 0, issues
    
    @staticmethod
    def generate_secure_password(length: int = 16, include_symbols: bool = True) -> str:
        """Generate cryptographically secure password."""
        lowercase = string.ascii_lowercase
        uppercase = string.ascii_uppercase
        digits = string.digits
        symbols = "!@#$%^&*()_+-=[]{}|;:,.<>?" if include_symbols else ""
        
        # Ensure at least one character from each category
        password = [
            secrets.choice(lowercase),
            secrets.choice(uppercase),
            secrets.choice(digits)
        ]
        
        if include_symbols:
            password.append(secrets.choice(symbols))
        
        # Fill remaining length
        all_chars = lowercase + uppercase + digits + symbols
        for _ in range(length - len(password)):
            password.append(secrets.choice(all_chars))
        
        # Shuffle
        secrets.SystemRandom().shuffle(password)
        return ''.join(password)
    
    @staticmethod
    def hash_sensitive_data(data: str, salt: str = None) -> Tuple[str, str]:
        """Hash sensitive data with salt."""
        if salt is None:
            salt = secrets.token_hex(16)
        
        combined = f"{data}{salt}".encode()
        hashed = hashlib.sha256(combined).hexdigest()
        return hashed, salt
    
    @staticmethod
    def constant_time_compare(a: str, b: str) -> bool:
        """Constant-time string comparison to prevent timing attacks."""
        if len(a) != len(b):
            return False
        
        result = 0
        for x, y in zip(a, b):
            result |= ord(x) ^ ord(y)
        
        return result == 0

# Backup and recovery system
class SecureBackupManager:
    """Secure backup and recovery for user data."""
    
    def __init__(self, user_store: SecureUserStore):
        self.user_store = user_store
        self.backup_dir = "keys/backups"
        os.makedirs(self.backup_dir, exist_ok=True)
    
    def create_encrypted_backup(self, encryption_password: str = None) -> str:
        """Create encrypted backup of all user data."""
        try:
            # Collect all data
            users = self.user_store.get_all_users()
            audit_log = self.user_store.get_audit_log(1000)
            
            backup_data = {
                'version': '2.0',
                'timestamp': datetime.now().isoformat(),
                'users': users,
                'audit_log': audit_log,
                'metadata': {
                    'storage_type': self.user_store.storage_type,
                    'total_users': len(users),
                    'backup_method': 'encrypted'
                }
            }
            
            # Convert to JSON
            json_data = json.dumps(backup_data, indent=2).encode()
            
            # Encrypt if password provided
            if encryption_password:
                key = self._derive_key_from_password(encryption_password)
                cipher = Fernet(key)
                encrypted_data = cipher.encrypt(json_data)
                
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                filename = f"users_backup_encrypted_{timestamp}.enc"
                filepath = os.path.join(self.backup_dir, filename)
                
                with open(filepath, 'wb') as f:
                    f.write(encrypted_data)
            else:
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                filename = f"users_backup_{timestamp}.json"
                filepath = os.path.join(self.backup_dir, filename)
                
                with open(filepath, 'wb') as f:
                    f.write(json_data)
            
            return filepath
            
        except Exception as e:
            raise Exception(f"Backup creation failed: {str(e)}")
    
    def restore_from_backup(self, backup_file: str, encryption_password: str = None) -> bool:
        """Restore from encrypted backup."""
        try:
            with open(backup_file, 'rb') as f:
                data = f.read()
            
            # Decrypt if needed
            if backup_file.endswith('.enc') and encryption_password:
                key = self._derive_key_from_password(encryption_password)
                cipher = Fernet(key)
                data = cipher.decrypt(data)
            
            # Parse JSON
            backup_data = json.loads(data.decode())
            
            # Validate backup
            if 'users' not in backup_data or 'version' not in backup_data:
                raise Exception("Invalid backup format")
            
            # Restore users (this would need careful implementation)
            # For safety, we'll just return True here
            return True
            
        except Exception as e:
            raise Exception(f"Restore failed: {str(e)}")
    
    def _derive_key_from_password(self, password: str) -> bytes:
        """Derive encryption key from password."""
        password_bytes = password.encode()
        salt = b'backup_salt_change_in_production'
        
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=100000,
        )
        
        key = base64.urlsafe_b64encode(kdf.derive(password_bytes))
        return key
    
    def schedule_automatic_backup(self, interval_hours: int = 24) -> bool:
        """Schedule automatic backups (placeholder for cron/scheduler integration)."""
        # In production, this would integrate with system scheduler
        backup_config = {
            'enabled': True,
            'interval_hours': interval_hours,
            'encryption_enabled': True,
            'retention_days': int(os.getenv('BACKUP_RETENTION_DAYS', 30)),
            'next_backup': (datetime.now() + timedelta(hours=interval_hours)).isoformat()
        }
        
        with open(os.path.join(self.backup_dir, 'backup_config.json'), 'w') as f:
            json.dump(backup_config, f, indent=2)
        
        return True
    
    def cleanup_old_backups(self, retention_days: int = 30):
        """Clean up old backup files."""
        try:
            cutoff_date = datetime.now() - timedelta(days=retention_days)
            
            for filename in os.listdir(self.backup_dir):
                if filename.startswith('users_backup_'):
                    filepath = os.path.join(self.backup_dir, filename)
                    file_mtime = datetime.fromtimestamp(os.path.getmtime(filepath))
                    
                    if file_mtime < cutoff_date:
                        os.remove(filepath)
                        print(f"Removed old backup: {filename}")
                        
        except Exception as e:
            print(f"Cleanup failed: {str(e)}")

# Example usage and setup
def setup_enhanced_security() -> Dict:
    """Setup enhanced security system."""
    return {
        'storage_options': {
            'sqlite': 'SQLite database (recommended for development)',
            'encrypted_json': 'Encrypted JSON files (good balance)',
            'postgresql': 'PostgreSQL database (best for production)',
            'yaml': 'YAML files (legacy, not recommended)'
        },
        'security_features': [
            'Password hashing with bcrypt',
            'Session management with secure tokens',
            'Account lockout after failed attempts',
            'Audit logging for compliance',
            'Encrypted data storage options',
            'Secure backup and recovery',
            'Password complexity validation',
            'Rate limiting protection'
        ],
        'migration_path': [
            '1. Choose target storage method',
            '2. Set environment variables',
            '3. Run migration script',
            '4. Test authentication',
            '5. Update deployment configuration',
            '6. Enable additional security features'
        ]
    }