import streamlit as st
import bcrypt
import yaml
import os
import json
import re
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
import secrets
import string

class UserManager:
    """Secure user management with enhanced security features."""
    
    def __init__(self, config_path: str = "keys/config.yaml"):
        self.config_path = config_path
        self.backup_path = "keys/config_backup.yaml"
        self.audit_log_path = "keys/audit_log.json"
        
    def load_config(self) -> Dict:
        """Load the current configuration."""
        try:
            with open(self.config_path, 'r') as file:
                return yaml.load(file, Loader=yaml.SafeLoader)
        except FileNotFoundError:
            st.error(f"❌ Configuration file not found: {self.config_path}")
            return {}
        except Exception as e:
            st.error(f"❌ Error loading configuration: {str(e)}")
            return {}
    
    def save_config(self, config: Dict) -> bool:
        """Save configuration with backup."""
        try:
            # Create backup of current config
            if os.path.exists(self.config_path):
                with open(self.config_path, 'r') as src:
                    with open(self.backup_path, 'w') as dst:
                        dst.write(src.read())
            
            # Save new config
            os.makedirs(os.path.dirname(self.config_path), exist_ok=True)
            with open(self.config_path, 'w') as file:
                yaml.dump(config, file, default_flow_style=False, sort_keys=False)
            
            return True
        except Exception as e:
            st.error(f"❌ Error saving configuration: {str(e)}")
            return False
    
    def hash_password(self, password: str) -> str:
        """Hash a password using bcrypt."""
        password_bytes = password.encode('utf-8')
        salt = bcrypt.gensalt()
        hashed = bcrypt.hashpw(password_bytes, salt)
        return hashed.decode('utf-8')
    
    def verify_password(self, password: str, hashed: str) -> bool:
        """Verify a password against its hash."""
        try:
            return bcrypt.checkpw(password.encode('utf-8'), hashed.encode('utf-8'))
        except Exception:
            return False
    
    def generate_secure_password(self, length: int = 16) -> str:
        """Generate a secure random password."""
        # Character sets for password generation
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
    
    def validate_password_strength(self, password: str) -> Tuple[bool, List[str]]:
        """Validate password strength."""
        issues = []
        
        if len(password) < 8:
            issues.append("Password must be at least 8 characters long")
        
        if not re.search(r'[a-z]', password):
            issues.append("Password must contain at least one lowercase letter")
        
        if not re.search(r'[A-Z]', password):
            issues.append("Password must contain at least one uppercase letter")
        
        if not re.search(r'\d', password):
            issues.append("Password must contain at least one digit")
        
        if not re.search(r'[!@#$%^&*()_+\-=\[\]{}|;:,.<>?]', password):
            issues.append("Password must contain at least one special character")
        
        # Check for common patterns
        if password.lower() in ['password', '12345678', 'qwerty', 'admin']:
            issues.append("Password is too common")
        
        return len(issues) == 0, issues
    
    def validate_email(self, email: str) -> bool:
        """Validate email format."""
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return re.match(pattern, email) is not None
    
    def log_audit_event(self, event_type: str, username: str, details: str = ""):
        """Log audit events."""
        try:
            audit_entry = {
                "timestamp": datetime.now().isoformat(),
                "event_type": event_type,
                "username": username,
                "details": details,
                "performed_by": st.session_state.get('username', 'unknown')
            }
            
            # Load existing log or create new
            audit_log = []
            if os.path.exists(self.audit_log_path):
                with open(self.audit_log_path, 'r') as f:
                    audit_log = json.load(f)
            
            audit_log.append(audit_entry)
            
            # Keep only last 1000 entries
            audit_log = audit_log[-1000:]
            
            # Save log
            os.makedirs(os.path.dirname(self.audit_log_path), exist_ok=True)
            with open(self.audit_log_path, 'w') as f:
                json.dump(audit_log, f, indent=2)
                
        except Exception as e:
            st.error(f"❌ Error logging audit event: {str(e)}")
    
    def get_audit_log(self, limit: int = 50) -> List[Dict]:
        """Get recent audit log entries."""
        try:
            if os.path.exists(self.audit_log_path):
                with open(self.audit_log_path, 'r') as f:
                    audit_log = json.load(f)
                return audit_log[-limit:]
            return []
        except Exception:
            return []
    
    def add_user(self, username: str, name: str, email: str, password: str, is_admin: bool = False) -> bool:
        """Add a new user."""
        config = self.load_config()
        
        # Validate inputs
        if not username or not name or not email or not password:
            st.error("❌ All fields are required")
            return False
        
        if username in config.get('credentials', {}).get('usernames', {}):
            st.error(f"❌ Username '{username}' already exists")
            return False
        
        if not self.validate_email(email):
            st.error("❌ Invalid email format")
            return False
        
        # Check if email already exists
        existing_emails = [user['email'] for user in config.get('credentials', {}).get('usernames', {}).values()]
        if email in existing_emails:
            st.error(f"❌ Email '{email}' already exists")
            return False
        
        is_valid, issues = self.validate_password_strength(password)
        if not is_valid:
            st.error("❌ Password validation failed:")
            for issue in issues:
                st.error(f"  • {issue}")
            return False
        
        # Hash password
        hashed_password = self.hash_password(password)
        
        # Add user to config
        if 'credentials' not in config:
            config['credentials'] = {'usernames': {}}
        
        config['credentials']['usernames'][username] = {
            'email': email,
            'name': name,
            'password': hashed_password,
            'is_admin': is_admin,
            'created_at': datetime.now().isoformat(),
            'last_login': None,
            'login_attempts': 0,
            'locked_until': None
        }
        
        # Add to preauthorized emails
        if 'preauthorized' not in config:
            config['preauthorized'] = {'emails': []}
        
        if email not in config['preauthorized']['emails']:
            config['preauthorized']['emails'].append(email)
        
        # Save config
        if self.save_config(config):
            self.log_audit_event("USER_CREATED", username, f"New user created with email {email}")
            return True
        
        return False
    
    def update_user(self, username: str, name: str = None, email: str = None, password: str = None, is_admin: bool = None) -> bool:
        """Update an existing user."""
        config = self.load_config()
        
        if username not in config.get('credentials', {}).get('usernames', {}):
            st.error(f"❌ Username '{username}' not found")
            return False
        
        user = config['credentials']['usernames'][username]
        changes = []
        
        # Update name
        if name and name != user['name']:
            user['name'] = name
            changes.append(f"name: {name}")
        
        # Update email
        if email and email != user['email']:
            if not self.validate_email(email):
                st.error("❌ Invalid email format")
                return False
            
            # Check if email already exists for other users
            existing_emails = {k: v['email'] for k, v in config['credentials']['usernames'].items() if k != username}
            if email in existing_emails.values():
                st.error(f"❌ Email '{email}' already exists")
                return False
            
            # Update preauthorized emails
            old_email = user['email']
            user['email'] = email
            
            if old_email in config['preauthorized']['emails']:
                config['preauthorized']['emails'].remove(old_email)
            
            if email not in config['preauthorized']['emails']:
                config['preauthorized']['emails'].append(email)
            
            changes.append(f"email: {email}")
        
        # Update password
        if password:
            is_valid, issues = self.validate_password_strength(password)
            if not is_valid:
                st.error("❌ Password validation failed:")
                for issue in issues:
                    st.error(f"  • {issue}")
                return False
            
            user['password'] = self.hash_password(password)
            changes.append("password updated")
        
        # Update admin status
        if is_admin is not None and is_admin != user.get('is_admin', False):
            user['is_admin'] = is_admin
            changes.append(f"admin status: {is_admin}")
        
        # Update last modified
        user['last_modified'] = datetime.now().isoformat()
        
        # Save config
        if self.save_config(config):
            self.log_audit_event("USER_UPDATED", username, f"Updated: {', '.join(changes)}")
            return True
        
        return False
    
    def delete_user(self, username: str) -> bool:
        """Delete a user."""
        config = self.load_config()
        
        if username not in config.get('credentials', {}).get('usernames', {}):
            st.error(f"❌ Username '{username}' not found")
            return False
        
        # Prevent deletion of current user
        if username == st.session_state.get('username'):
            st.error("❌ Cannot delete your own account")
            return False
        
        # Remove from credentials
        user = config['credentials']['usernames'][username]
        email = user['email']
        del config['credentials']['usernames'][username]
        
        # Remove from preauthorized emails
        if email in config['preauthorized']['emails']:
            config['preauthorized']['emails'].remove(email)
        
        # Save config
        if self.save_config(config):
            self.log_audit_event("USER_DELETED", username, f"User deleted (email: {email})")
            return True
        
        return False
    
    def get_all_users(self) -> Dict:
        """Get all users."""
        config = self.load_config()
        return config.get('credentials', {}).get('usernames', {})
    
    def backup_users(self) -> str:
        """Create a backup of all users."""
        config = self.load_config()
        backup_data = {
            'users': config.get('credentials', {}).get('usernames', {}),
            'preauthorized': config.get('preauthorized', {}).get('emails', []),
            'backup_timestamp': datetime.now().isoformat(),
            'backup_version': '1.0'
        }
        
        # Remove password hashes from backup for security
        safe_backup = backup_data.copy()
        for username, user_data in safe_backup['users'].items():
            user_data = user_data.copy()
            user_data['password'] = '[REDACTED]'
            safe_backup['users'][username] = user_data
        
        return json.dumps(safe_backup, indent=2)

def create_user_management_tab():
    """Create the User Management tab."""
    st.header("👥 User Management")
    st.markdown("Manage user accounts, permissions, and security settings.")
    
    # Check if current user is admin
    current_user = st.session_state.get('username')
    if not current_user:
        st.error("❌ Authentication required")
        return
    
    # Initialize user manager
    user_manager = UserManager()
    
    # Load current users
    users = user_manager.get_all_users()
    
    # Check admin privileges (for now, admin user has full access)
    is_admin = current_user == 'admin'
    
    if not is_admin:
        st.warning("⚠️ Limited access: You can only view users and change your own password.")
    
    # Create tabs within the user management
    if is_admin:
        user_tab, audit_tab, security_tab, backup_tab = st.tabs(["👤 Users", "📊 Audit Log", "🔒 Security", "💾 Backup"])
    else:
        user_tab, profile_tab = st.tabs(["👤 View Users", "👤 My Profile"])
    
    with user_tab:
        create_users_tab(user_manager, users, is_admin)
    
    if is_admin:
        with audit_tab:
            create_audit_tab(user_manager)
        
        with security_tab:
            create_security_tab(user_manager)
        
        with backup_tab:
            create_backup_tab(user_manager)
    else:
        with profile_tab:
            create_profile_tab(user_manager, current_user)

def create_users_tab(user_manager: UserManager, users: Dict, is_admin: bool):
    """Create the users management tab."""
    
    # Users overview
    with st.container(border=True):
        st.subheader("📊 Users Overview")
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("Total Users", len(users))
        
        with col2:
            admin_count = sum(1 for user in users.values() if user.get('is_admin', False))
            st.metric("Admin Users", admin_count)
        
        with col3:
            active_count = sum(1 for user in users.values() if user.get('last_login'))
            st.metric("Active Users", active_count)
        
        with col4:
            recent_count = sum(1 for user in users.values() 
                             if user.get('created_at') and 
                             datetime.fromisoformat(user['created_at']) > datetime.now() - timedelta(days=30))
            st.metric("New (30 days)", recent_count)
    
    # Add new user (admin only) - FIXED VERSION
    if is_admin:
        with st.container(border=True):
            st.subheader("➕ Add New User")
            
            # Initialize session state for form data
            if 'add_user_form_data' not in st.session_state:
                st.session_state.add_user_form_data = {
                    'username': '',
                    'name': '',
                    'email': '',
                    'password_option': 'Generate Secure Password',
                    'manual_password': '',
                    'is_admin': False,
                    'generated_password': None
                }
            
            # Form inputs
            col1, col2 = st.columns(2)
            
            with col1:
                new_username = st.text_input(
                    "Username", 
                    value=st.session_state.add_user_form_data['username'],
                    placeholder="Enter username",
                    key="new_username_input"
                )
                new_name = st.text_input(
                    "Full Name", 
                    value=st.session_state.add_user_form_data['name'],
                    placeholder="Enter full name",
                    key="new_name_input"
                )
                new_email = st.text_input(
                    "Email", 
                    value=st.session_state.add_user_form_data['email'],
                    placeholder="Enter email address",
                    key="new_email_input"
                )
            
            with col2:
                # Password options
                password_option = st.radio(
                    "Password Setup", 
                    ["Generate Secure Password", "Manual Password"],
                    index=0 if st.session_state.add_user_form_data['password_option'] == 'Generate Secure Password' else 1,
                    key="password_option_radio"
                )
                
                new_password = ""
                
                if password_option == "Generate Secure Password":
                    if st.button("🎲 Generate Password", key="generate_password_btn"):
                        generated_password = user_manager.generate_secure_password()
                        st.session_state.add_user_form_data['generated_password'] = generated_password
                        st.rerun()
                    
                    if st.session_state.add_user_form_data['generated_password']:
                        st.success(f"Generated Password: `{st.session_state.add_user_form_data['generated_password']}`")
                        st.warning("⚠️ Copy this password now - it won't be shown again!")
                        new_password = st.session_state.add_user_form_data['generated_password']
                else:
                    new_password = st.text_input(
                        "Password", 
                        type="password", 
                        placeholder="Enter password",
                        value=st.session_state.add_user_form_data['manual_password'],
                        key="manual_password_input"
                    )
                
                new_is_admin = st.checkbox(
                    "Admin User", 
                    value=st.session_state.add_user_form_data['is_admin'],
                    help="Grant administrative privileges",
                    key="is_admin_checkbox"
                )
            
            # Add user button (outside of form)
            col1, col2 = st.columns([1, 3])
            with col1:
                if st.button("➕ Add User", type="primary", key="add_user_submit_btn"):
                    # Validate inputs
                    if not all([new_username, new_name, new_email, new_password]):
                        st.error("❌ All fields are required")
                    else:
                        # Update session state
                        st.session_state.add_user_form_data.update({
                            'username': new_username,
                            'name': new_name,
                            'email': new_email,
                            'password_option': password_option,
                            'manual_password': new_password if password_option == "Manual Password" else '',
                            'is_admin': new_is_admin
                        })
                        
                        # Try to add user
                        if user_manager.add_user(new_username, new_name, new_email, new_password, new_is_admin):
                            st.success(f"✅ User '{new_username}' added successfully!")
                            # Clear form data
                            st.session_state.add_user_form_data = {
                                'username': '',
                                'name': '',
                                'email': '',
                                'password_option': 'Generate Secure Password',
                                'manual_password': '',
                                'is_admin': False,
                                'generated_password': None
                            }
                            st.rerun()
            
            with col2:
                if st.button("🔄 Clear Form", key="clear_form_btn"):
                    st.session_state.add_user_form_data = {
                        'username': '',
                        'name': '',
                        'email': '',
                        'password_option': 'Generate Secure Password',
                        'manual_password': '',
                        'is_admin': False,
                        'generated_password': None
                    }
                    st.rerun()
    
    # Users list
    with st.container(border=True):
        st.subheader("👥 User List")
        
        if not users:
            st.info("No users found.")
            return
        
        # Search and filter
        col1, col2 = st.columns(2)
        
        with col1:
            search_term = st.text_input("🔍 Search Users", placeholder="Search by username, name, or email")
        
        with col2:
            filter_admin = st.selectbox("Filter by Role", ["All Users", "Admin Only", "Regular Users"])
        
        # Filter users
        filtered_users = users.copy()
        
        if search_term:
            filtered_users = {
                username: user for username, user in filtered_users.items()
                if (search_term.lower() in username.lower() or 
                    search_term.lower() in user['name'].lower() or
                    search_term.lower() in user['email'].lower())
            }
        
        if filter_admin == "Admin Only":
            filtered_users = {username: user for username, user in filtered_users.items() if user.get('is_admin', False)}
        elif filter_admin == "Regular Users":
            filtered_users = {username: user for username, user in filtered_users.items() if not user.get('is_admin', False)}
        
        # Display users
        for username, user in filtered_users.items():
            with st.container(border=True):
                col1, col2, col3 = st.columns([3, 2, 1])
                
                with col1:
                    # User info
                    admin_badge = "🔴 Admin" if user.get('is_admin', False) else "🟢 User"
                    st.markdown(f"**{user['name']}** ({username}) {admin_badge}")
                    st.markdown(f"📧 {user['email']}")
                    
                    # Additional info
                    if user.get('created_at'):
                        try:
                            created_date = datetime.fromisoformat(user['created_at']).strftime('%Y-%m-%d')
                            st.markdown(f"📅 Created: {created_date}")
                        except:
                            st.markdown("📅 Created: Unknown")
                    
                    if user.get('last_login'):
                        try:
                            last_login = datetime.fromisoformat(user['last_login']).strftime('%Y-%m-%d %H:%M')
                            st.markdown(f"🕒 Last Login: {last_login}")
                        except:
                            st.markdown("🕒 Last Login: Invalid date")
                    else:
                        st.markdown("🕒 Last Login: Never")
                
                with col2:
                    # User status
                    if user.get('locked_until'):
                        try:
                            locked_until = datetime.fromisoformat(user['locked_until'])
                            if locked_until > datetime.now():
                                st.error("🔒 Account Locked")
                            else:
                                st.success("✅ Active")
                        except:
                            st.success("✅ Active")
                    else:
                        st.success("✅ Active")
                    
                    # Login attempts
                    attempts = user.get('login_attempts', 0)
                    if attempts > 0:
                        st.warning(f"⚠️ Failed attempts: {attempts}")
                
                with col3:
                    # Actions
                    if is_admin:
                        if st.button("✏️ Edit", key=f"edit_{username}"):
                            st.session_state[f'edit_user_{username}'] = True
                            st.rerun()
                        
                        if username != st.session_state.get('username'):  # Can't delete self
                            if st.button("🗑️ Delete", key=f"delete_{username}"):
                                st.session_state[f'delete_user_{username}'] = True
                                st.rerun()
                    else:
                        if username == st.session_state.get('username'):
                            if st.button("🔑 Change Password", key=f"change_pwd_{username}"):
                                st.session_state[f'change_password_{username}'] = True
                                st.rerun()
                
                # Handle edit/delete/change password modals
                if is_admin and st.session_state.get(f'edit_user_{username}'):
                    edit_user_modal(user_manager, username, user)
                
                if is_admin and st.session_state.get(f'delete_user_{username}'):
                    delete_user_modal(user_manager, username, user)
                
                if st.session_state.get(f'change_password_{username}'):
                    change_password_modal(user_manager, username)

def edit_user_modal(user_manager: UserManager, username: str, user: Dict):
    """Modal for editing user."""
    st.subheader(f"✏️ Edit User: {username}")
    
    col1, col2 = st.columns(2)
    
    with col1:
        edit_name = st.text_input("Full Name", value=user['name'], key=f"edit_name_{username}")
        edit_email = st.text_input("Email", value=user['email'], key=f"edit_email_{username}")
    
    with col2:
        edit_is_admin = st.checkbox("Admin User", value=user.get('is_admin', False), key=f"edit_admin_{username}")
        change_password = st.checkbox("Change Password", key=f"change_pwd_check_{username}")
    
    edit_password = ""
    if change_password:
        edit_password = st.text_input("New Password", type="password", key=f"edit_password_{username}")
    
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("💾 Save Changes", type="primary", key=f"save_changes_{username}"):
            if user_manager.update_user(username, edit_name, edit_email, edit_password or None, edit_is_admin):
                st.success("✅ User updated successfully!")
                st.session_state[f'edit_user_{username}'] = False
                st.rerun()
    
    with col2:
        if st.button("❌ Cancel", key=f"cancel_edit_{username}"):
            st.session_state[f'edit_user_{username}'] = False
            st.rerun()

def delete_user_modal(user_manager: UserManager, username: str, user: Dict):
    """Modal for deleting user."""
    st.subheader(f"🗑️ Delete User: {username}")
    
    st.warning(f"⚠️ Are you sure you want to delete user **{user['name']}** ({username})?")
    st.error("This action cannot be undone!")
    
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("🗑️ Confirm Delete", type="primary", key=f"confirm_delete_{username}"):
            if user_manager.delete_user(username):
                st.success("✅ User deleted successfully!")
                st.session_state[f'delete_user_{username}'] = False
                st.rerun()
    
    with col2:
        if st.button("❌ Cancel", key=f"cancel_delete_{username}"):
            st.session_state[f'delete_user_{username}'] = False
            st.rerun()

def change_password_modal(user_manager: UserManager, username: str):
    """Modal for changing password."""
    st.subheader(f"🔑 Change Password: {username}")
    
    new_password = st.text_input("New Password", type="password", key=f"new_pwd_{username}")
    confirm_password = st.text_input("Confirm Password", type="password", key=f"confirm_pwd_{username}")
    
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("🔑 Change Password", type="primary", key=f"submit_pwd_change_{username}"):
            if new_password != confirm_password:
                st.error("❌ Passwords do not match")
            elif user_manager.update_user(username, password=new_password):
                st.success("✅ Password changed successfully!")
                st.session_state[f'change_password_{username}'] = False
                st.rerun()
    
    with col2:
        if st.button("❌ Cancel", key=f"cancel_pwd_change_{username}"):
            st.session_state[f'change_password_{username}'] = False
            st.rerun()

def create_audit_tab(user_manager: UserManager):
    """Create the audit log tab."""
    st.subheader("📊 Audit Log")
    
    # Get audit log
    audit_log = user_manager.get_audit_log(100)
    
    if not audit_log:
        st.info("No audit log entries found.")
        return
    
    # Display audit log
    for entry in reversed(audit_log):
        with st.container(border=True):
            col1, col2, col3 = st.columns([2, 1, 2])
            
            with col1:
                try:
                    timestamp = datetime.fromisoformat(entry['timestamp']).strftime('%Y-%m-%d %H:%M:%S')
                except:
                    timestamp = entry.get('timestamp', 'Unknown')
                st.markdown(f"**{timestamp}**")
                st.markdown(f"Event: {entry['event_type']}")
            
            with col2:
                st.markdown(f"**User:** {entry['username']}")
                st.markdown(f"**By:** {entry['performed_by']}")
            
            with col3:
                if entry.get('details'):
                    st.markdown(f"**Details:** {entry['details']}")

def create_security_tab(user_manager: UserManager):
    """Create the security settings tab."""
    st.subheader("🔒 Security Settings")
    
    # Password policy
    with st.container(border=True):
        st.subheader("🔐 Password Policy")
        
        st.markdown("""
        **Current Password Requirements:**
        - Minimum 8 characters
        - At least one lowercase letter
        - At least one uppercase letter
        - At least one digit
        - At least one special character
        - Cannot be a common password
        """)
        
        # Password strength tester
        st.markdown("**Test Password Strength:**")
        test_password = st.text_input("Test Password", type="password", placeholder="Enter a password to test")
        
        if test_password:
            is_valid, issues = user_manager.validate_password_strength(test_password)
            if is_valid:
                st.success("✅ Password meets all requirements!")
            else:
                st.error("❌ Password does not meet requirements:")
                for issue in issues:
                    st.error(f"  • {issue}")
    
    # Security recommendations
    with st.container(border=True):
        st.subheader("🛡️ Security Recommendations")
        
        st.markdown("""
        **Enhanced Security Measures:**
        
        1. **Environment Variables**: Store sensitive configuration in environment variables
        2. **Database Storage**: Consider moving to database-based user management
        3. **Two-Factor Authentication**: Implement 2FA for admin accounts
        4. **Session Management**: Configure session timeout and secure cookies
        5. **Rate Limiting**: Implement login attempt rate limiting
        6. **Password Expiration**: Consider periodic password changes
        7. **Audit Logging**: Regular audit log reviews
        8. **Backup Security**: Encrypt user data backups
        """)

def create_backup_tab(user_manager: UserManager):
    """Create the backup tab."""
    st.subheader("💾 Backup & Recovery")
    
    # Create backup
    with st.container(border=True):
        st.subheader("📤 Create Backup")
        
        if st.button("📥 Create Users Backup", type="primary"):
            backup_data = user_manager.backup_users()
            
            st.download_button(
                label="💾 Download Backup",
                data=backup_data,
                file_name=f"users_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                mime="application/json"
            )
    
    # Restore from backup
    with st.container(border=True):
        st.subheader("📥 Restore from Backup")
        
        uploaded_file = st.file_uploader("Choose backup file", type=['json'])
        
        if uploaded_file is not None:
            try:
                backup_data = json.load(uploaded_file)
                
                if 'users' in backup_data:
                    st.success("✅ Valid backup file detected")
                    st.info(f"Backup contains {len(backup_data['users'])} users")
                    st.info(f"Backup timestamp: {backup_data.get('backup_timestamp', 'Unknown')}")
                    
                    if st.button("🔄 Restore Users", type="primary"):
                        st.error("⚠️ Restore functionality not implemented for security reasons")
                        st.info("Please manually restore users or contact administrator")
                else:
                    st.error("❌ Invalid backup file format")
            except Exception as e:
                st.error(f"❌ Error reading backup file: {str(e)}")

def create_profile_tab(user_manager: UserManager, username: str):
    """Create the profile tab for non-admin users."""
    st.subheader("👤 My Profile")
    
    users = user_manager.get_all_users()
    if username not in users:
        st.error("❌ User not found")
        return
    
    user = users[username]
    
    # Display profile info
    with st.container(border=True):
        st.subheader("ℹ️ Profile Information")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown(f"**Username:** {username}")
            st.markdown(f"**Full Name:** {user['name']}")
            st.markdown(f"**Email:** {user['email']}")
        
        with col2:
            if user.get('created_at'):
                try:
                    created_date = datetime.fromisoformat(user['created_at']).strftime('%Y-%m-%d')
                    st.markdown(f"**Member Since:** {created_date}")
                except:
                    st.markdown("**Member Since:** Unknown")
            
            if user.get('last_login'):
                try:
                    last_login = datetime.fromisoformat(user['last_login']).strftime('%Y-%m-%d %H:%M')
                    st.markdown(f"**Last Login:** {last_login}")
                except:
                    st.markdown("**Last Login:** Invalid date")
            else:
                st.markdown("**Last Login:** Never")
            
            role = "Administrator" if user.get('is_admin', False) else "Regular User"
            st.markdown(f"**Role:** {role}")
    
    # Change password
    with st.container(border=True):
        st.subheader("🔑 Change Password")
        
        new_password = st.text_input("New Password", type="password", key="profile_new_password")
        confirm_password = st.text_input("Confirm Password", type="password", key="profile_confirm_password")
        
        if st.button("🔑 Change Password", type="primary", key="profile_change_password"):
            if new_password != confirm_password:
                st.error("❌ Passwords do not match")
            elif user_manager.update_user(username, password=new_password):
                st.success("✅ Password changed successfully!")
                st.rerun()