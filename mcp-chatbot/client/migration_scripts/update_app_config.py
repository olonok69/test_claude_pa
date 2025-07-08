#!/usr/bin/env python3
"""
Fixed Application Configuration Updater
Updates your Streamlit app to use SQLite authentication after migration
FIXES: Character encoding issues on Windows
"""

import os
import shutil
from datetime import datetime
from typing import Dict
import chardet

class AppConfigUpdater:
    """Updates application configuration to use SQLite authentication."""
    
    def __init__(self):
        self.app_py_path = "app.py"
        self.backup_dir = "keys/app_backup"
        os.makedirs(self.backup_dir, exist_ok=True)
    
    def detect_encoding(self, file_path: str) -> str:
        """Detect file encoding to handle Windows encoding issues."""
        try:
            with open(file_path, 'rb') as f:
                raw_data = f.read()
            
            result = chardet.detect(raw_data)
            encoding = result['encoding']
            
            if encoding is None:
                # Fallback encodings to try
                fallback_encodings = ['utf-8', 'utf-8-sig', 'latin1', 'cp1252']
                for enc in fallback_encodings:
                    try:
                        with open(file_path, 'r', encoding=enc) as f:
                            f.read()
                        print(f"✅ Using fallback encoding: {enc}")
                        return enc
                    except UnicodeDecodeError:
                        continue
                
                # If all else fails, use utf-8 with error handling
                print("⚠️  Using utf-8 with error handling")
                return 'utf-8'
            
            print(f"✅ Detected encoding: {encoding}")
            return encoding
            
        except Exception as e:
            print(f"⚠️  Encoding detection failed: {str(e)}, using utf-8")
            return 'utf-8'
    
    def read_file_safely(self, file_path: str) -> str:
        """Read file with proper encoding detection."""
        encoding = self.detect_encoding(file_path)
        
        try:
            with open(file_path, 'r', encoding=encoding) as f:
                return f.read()
        except UnicodeDecodeError:
            # Try with error handling
            try:
                with open(file_path, 'r', encoding=encoding, errors='replace') as f:
                    content = f.read()
                print("⚠️  Some characters were replaced due to encoding issues")
                return content
            except Exception as e:
                # Last resort - binary read and decode
                print(f"⚠️  Using binary read due to encoding issues: {str(e)}")
                with open(file_path, 'rb') as f:
                    raw_content = f.read()
                return raw_content.decode('utf-8', errors='replace')
    
    def write_file_safely(self, file_path: str, content: str) -> bool:
        """Write file with UTF-8 encoding."""
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            return True
        except Exception as e:
            print(f"❌ Error writing file: {str(e)}")
            return False
    
    def create_backup(self) -> bool:
        """Create backup of current app.py."""
        try:
            if os.path.exists(self.app_py_path):
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                backup_path = os.path.join(self.backup_dir, f"app_backup_{timestamp}.py")
                shutil.copy2(self.app_py_path, backup_path)
                print(f"✅ Created backup: {backup_path}")
                return True
            else:
                print(f"❌ app.py not found at {self.app_py_path}")
                return False
        except Exception as e:
            print(f"❌ Backup failed: {str(e)}")
            return False
    
    def update_app_py(self) -> bool:
        """Update app.py to use SQLite authentication."""
        try:
            if not os.path.exists(self.app_py_path):
                print(f"❌ app.py not found at {self.app_py_path}")
                return False
            
            # Read current app.py with encoding detection
            print("📖 Reading app.py with encoding detection...")
            content = self.read_file_safely(self.app_py_path)
            
            # Check if already updated
            if "StreamlitSecureAuth" in content:
                print("⚠️  app.py already appears to be updated for SQLite authentication")
                return True
            
            # Prepare the updated content
            updated_content = self.prepare_updated_content(content)
            
            # Write updated content
            if self.write_file_safely(self.app_py_path, updated_content):
                print("✅ app.py updated successfully")
                return True
            else:
                print("❌ Failed to write updated app.py")
                return False
                
        except Exception as e:
            print(f"❌ Failed to update app.py: {str(e)}")
            return False
    
    def prepare_updated_content(self, content: str) -> str:
        """Prepare the updated content for app.py."""
        
        # Enhanced security imports to add
        enhanced_imports = """
# Enhanced security imports for SQLite authentication
try:
    from utils.enhanced_security_config import StreamlitSecureAuth, SecurityConfig
    ENHANCED_SECURITY_AVAILABLE = True
except ImportError:
    ENHANCED_SECURITY_AVAILABLE = False
    print("⚠️  Enhanced security module not available. Using YAML fallback.")
"""
        
        # Updated load_config function
        new_load_config = '''
def load_config():
    """Load authentication configuration from secure storage or YAML fallback."""
    try:
        # Check if SQLite is enabled and available
        use_sqlite = os.getenv('USE_SQLITE', 'false').lower() == 'true'
        
        if use_sqlite and ENHANCED_SECURITY_AVAILABLE:
            print("🔒 Using SQLite authentication")
            # Use enhanced SQLite authentication
            secure_auth = StreamlitSecureAuth('sqlite')
            return secure_auth.get_config_for_streamlit_authenticator()
        else:
            print("📋 Using YAML authentication")
            # Fallback to YAML configuration
            config_path = os.path.join('keys', 'config.yaml')
            if not os.path.exists(config_path):
                st.error("❌ Configuration file not found at keys/config.yaml")
                st.stop()
            
            with open(config_path, 'r', encoding='utf-8') as file:
                return yaml.load(file, Loader=SafeLoader)
                
    except FileNotFoundError:
        st.error("❌ Configuration not found. Please check your setup.")
        st.stop()
    except Exception as e:
        st.error(f"❌ Error loading configuration: {str(e)}")
        st.stop()
'''
        
        # Find where to insert enhanced imports
        import_insertion_point = None
        lines = content.split('\n')
        
        # Look for existing imports
        for i, line in enumerate(lines):
            if "import streamlit_authenticator as stauth" in line:
                import_insertion_point = i + 1
                break
            elif "from services.chat_service import" in line:
                import_insertion_point = i + 1
                break
        
        if import_insertion_point is None:
            # Try to find any import statement
            for i, line in enumerate(lines):
                if line.strip().startswith("import ") or line.strip().startswith("from "):
                    import_insertion_point = i + 1
        
        # Insert enhanced imports
        if import_insertion_point is not None:
            lines.insert(import_insertion_point, enhanced_imports)
        else:
            # Add at the beginning after initial comments
            for i, line in enumerate(lines):
                if not line.strip().startswith('#') and line.strip():
                    lines.insert(i, enhanced_imports)
                    break
        
        # Reconstruct content
        content = '\n'.join(lines)
        
        # Replace the load_config function
        start_marker = "def load_config():"
        end_markers = [
            "def initialize_authentication_state():",
            "def handle_authentication():",
            "def show_authentication_required_message():",
            "def main():"
        ]
        
        start_pos = content.find(start_marker)
        if start_pos != -1:
            # Find the end of the function
            end_pos = len(content)
            for marker in end_markers:
                marker_pos = content.find(marker, start_pos + len(start_marker))
                if marker_pos != -1 and marker_pos < end_pos:
                    end_pos = marker_pos
            
            # Replace the function
            content = content[:start_pos] + new_load_config + "\n\n" + content[end_pos:]
        
        return content
    
    def create_env_template(self) -> bool:
        """Create .env template with SQLite configuration."""
        try:
            env_template = """# Enhanced Security Configuration
# Set to 'true' to use SQLite authentication (after migration)
USE_SQLITE=true

# Optional: Enable encryption for JSON storage
USE_ENCRYPTION=false
ENCRYPTION_PASSWORD=your_secure_encryption_password_change_in_production

# Session and Security Settings
SESSION_TIMEOUT_HOURS=24
MAX_LOGIN_ATTEMPTS=5
ACCOUNT_LOCKOUT_MINUTES=30

# Audit and Logging
ENABLE_AUDIT_LOG=true
LOG_FAILED_ATTEMPTS=true

# Backup Settings
AUTO_BACKUP_ENABLED=true
BACKUP_RETENTION_DAYS=30
BACKUP_ENCRYPTION_KEY=another_secure_key_for_backups

# Existing AI Provider Settings (keep your current values)
# OPENAI_API_KEY=your_openai_api_key_here
# AZURE_API_KEY=your_azure_api_key
# AZURE_ENDPOINT=https://your-endpoint.openai.azure.com/
# AZURE_DEPLOYMENT=your_deployment_name
# AZURE_API_VERSION=2023-12-01-preview

# MSSQL Configuration (keep your current values)
# MSSQL_HOST=localhost
# MSSQL_USER=your_username
# MSSQL_PASSWORD=your_password
# MSSQL_DATABASE=your_database
# MSSQL_DRIVER=ODBC Driver 18 for SQL Server
# TrustServerCertificate=yes
# Trusted_Connection=no
"""
            
            template_path = ".env.template"
            with open(template_path, 'w', encoding='utf-8') as f:
                f.write(env_template)
            
            print(f"✅ Created environment template: {template_path}")
            print("📝 Copy this to .env and update with your values")
            return True
            
        except Exception as e:
            print(f"❌ Failed to create .env template: {str(e)}")
            return False
    
    def update_requirements(self) -> bool:
        """Update requirements.txt with new dependencies."""
        try:
            requirements_path = "requirements.txt"
            
            if not os.path.exists(requirements_path):
                print(f"❌ requirements.txt not found at {requirements_path}")
                return False
            
            # Read current requirements with encoding detection
            content = self.read_file_safely(requirements_path)
            
            # Check if cryptography and chardet are already included
            missing_deps = []
            if "cryptography" not in content.lower():
                missing_deps.append("cryptography==42.0.5")
            if "chardet" not in content.lower():
                missing_deps.append("chardet==5.2.0")
            
            if not missing_deps:
                print("✅ All required dependencies already in requirements.txt")
                return True
            
            # Add missing dependencies
            if missing_deps:
                content += "\n# Enhanced security dependencies\n"
                content += "\n".join(missing_deps) + "\n"
            
            # Save updated requirements
            if self.write_file_safely(requirements_path, content):
                print(f"✅ Updated requirements.txt with: {', '.join(missing_deps)}")
                return True
            else:
                return False
            
        except Exception as e:
            print(f"❌ Failed to update requirements.txt: {str(e)}")
            return False
    
    def verify_setup(self) -> Dict:
        """Verify the setup is correct."""
        results = {
            'files_present': {},
            'dependencies_installed': {},
            'configuration_valid': False,
            'ready_for_sqlite': False
        }
        
        # Check required files
        required_files = [
            'app.py',
            'utils/enhanced_security_config.py',
            'ui_components/user_management_tab.py',
            'keys/users.db'
        ]
        
        for file_path in required_files:
            results['files_present'][file_path] = os.path.exists(file_path)
        
        # Check dependencies
        try:
            import cryptography
            results['dependencies_installed']['cryptography'] = True
        except ImportError:
            results['dependencies_installed']['cryptography'] = False
        
        try:
            import chardet
            results['dependencies_installed']['chardet'] = True
        except ImportError:
            results['dependencies_installed']['chardet'] = False
        
        try:
            import sqlite3
            results['dependencies_installed']['sqlite3'] = True
        except ImportError:
            results['dependencies_installed']['sqlite3'] = False
        
        # Check if SQLite database exists and has users
        if os.path.exists('keys/users.db'):
            try:
                import sqlite3
                conn = sqlite3.connect('keys/users.db')
                cursor = conn.cursor()
                cursor.execute('SELECT COUNT(*) FROM users')
                user_count = cursor.fetchone()[0]
                conn.close()
                
                results['configuration_valid'] = user_count > 0
            except:
                results['configuration_valid'] = False
        
        # Check if app.py has been updated
        try:
            content = self.read_file_safely('app.py')
            app_updated = "StreamlitSecureAuth" in content or "ENHANCED_SECURITY_AVAILABLE" in content
            results['app_updated'] = app_updated
        except:
            results['app_updated'] = False
        
        # Overall readiness
        all_files_present = all(results['files_present'].values())
        all_deps_installed = all(results['dependencies_installed'].values())
        results['ready_for_sqlite'] = (
            all_files_present and 
            all_deps_installed and 
            results['configuration_valid'] and
            results.get('app_updated', False)
        )
        
        return results
    
    def create_simple_fallback_app(self) -> bool:
        """Create a simple fallback version if the main update fails."""
        try:
            print("📝 Creating fallback app configuration...")
            
            fallback_content = '''import streamlit as st
import asyncio
import os
import nest_asyncio
import atexit
import yaml
import streamlit_authenticator as stauth
from yaml.loader import SafeLoader
import logging
from services.chat_service import init_session
from utils.async_helpers import on_shutdown
from apps import mcp_app

# Enhanced security imports (with fallback)
try:
    from utils.enhanced_security_config import StreamlitSecureAuth, SecurityConfig
    ENHANCED_SECURITY_AVAILABLE = True
except ImportError:
    ENHANCED_SECURITY_AVAILABLE = False
    print("⚠️  Enhanced security module not available. Using YAML fallback.")

# Apply nest_asyncio to allow nested asyncio event loops
nest_asyncio.apply()

page_icon_path = os.path.join('.', 'icons', 'playground.png')

st.set_page_config(
    page_title="The Machine Learning Engineer - MCP Client",
    page_icon=page_icon_path,
    layout='wide',
    initial_sidebar_state="expanded"
)

# Customize css
css_path = os.path.join('.', '.streamlit', 'style.css')
if os.path.exists(css_path):
    with open(css_path, encoding='utf-8') as f:
        st.markdown(f'<style>{f.read()}</style>', unsafe_allow_html=True)


def load_config():
    """Load authentication configuration from secure storage or YAML fallback."""
    try:
        # Check if SQLite is enabled and available
        use_sqlite = os.getenv('USE_SQLITE', 'false').lower() == 'true'
        
        if use_sqlite and ENHANCED_SECURITY_AVAILABLE:
            print("🔒 Using SQLite authentication")
            # Use enhanced SQLite authentication
            secure_auth = StreamlitSecureAuth('sqlite')
            return secure_auth.get_config_for_streamlit_authenticator()
        else:
            print("📋 Using YAML authentication")
            # Fallback to YAML configuration
            config_path = os.path.join('keys', 'config.yaml')
            if not os.path.exists(config_path):
                st.error("❌ Configuration file not found at keys/config.yaml")
                st.stop()
            
            with open(config_path, 'r', encoding='utf-8') as file:
                return yaml.load(file, Loader=SafeLoader)
                
    except FileNotFoundError:
        st.error("❌ Configuration not found. Please check your setup.")
        st.stop()
    except Exception as e:
        st.error(f"❌ Error loading configuration: {str(e)}")
        st.stop()


def initialize_authentication_state():
    """Initialize authentication-related session state variables."""
    if "authentication_status" not in st.session_state:
        st.session_state["authentication_status"] = None
    if "name" not in st.session_state:
        st.session_state["name"] = None
    if "username" not in st.session_state:
        st.session_state["username"] = None


def handle_authentication():
    """Handle user authentication in the sidebar."""
    # Load configuration
    config = load_config()
    
    # Initialize authentication state
    initialize_authentication_state()
    
    # Create authenticator using the updated API
    authenticator = stauth.Authenticate(
        config["credentials"],
        config["cookie"]["name"],
        config["cookie"]["key"],
        config["cookie"]["expiry_days"],
    )
    
    # Create sidebar authentication section
    with st.sidebar:
        st.markdown("## 🔐 Authentication")
        
        # Show login form or logout button based on authentication status
        if st.session_state["authentication_status"] is None:
            # Show login form
            try:
                authenticator.login()
            except Exception as e:
                st.error(f"Authentication error: {str(e)}")
                
            if st.session_state["authentication_status"] is False:
                st.error("❌ Username/password is incorrect")
            elif st.session_state["authentication_status"] is None:
                st.warning("⚠️ Please enter your username and password")
                
        elif st.session_state["authentication_status"]:
            # User is authenticated - show user info and logout button
            st.success(f"✅ Welcome, **{st.session_state['name']}**!")
            st.info(f"👤 Username: {st.session_state['username']}")
            
            # Add logout button
            authenticator.logout("Logout")
            
            # Add separator
            st.markdown("---")
    
    # Log authentication status
    logging.info(
        f'Authentication Status: {st.session_state["authentication_status"]}, '
        f'Name: {st.session_state["name"]}, '
        f'Username: {st.session_state["username"]}'
    )
    
    return st.session_state["authentication_status"]


def show_authentication_required_message():
    """Show a message when user is not authenticated."""
    st.title("🔐 Authentication Required")
    
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        # Add logo in the welcome message if available
        logo_path = os.path.join('.', 'icons', 'Logo.png')
        if os.path.exists(logo_path):
            # Center the logo
            col_a, col_b, col_c = st.columns([1, 1, 1])
            with col_b:
                st.image(logo_path, width=120)
            st.markdown("<br>", unsafe_allow_html=True)
        
        st.markdown("""
        ### Welcome to CloserStill Media - MCP Client
        
        This application provides AI-powered interactions with **MSSQL databases** 
        through Model Context Protocol (MCP) servers.
        
        **Please authenticate using the sidebar to access the application.**
        """)


def main():
    """Main application function with authentication."""
    try:
        # Initialize session state for event loop
        if "loop" not in st.session_state:
            st.session_state.loop = asyncio.new_event_loop()
            asyncio.set_event_loop(st.session_state.loop)
        
        # Register shutdown handler
        atexit.register(on_shutdown)
        
        # Always show logo at the top of sidebar first
        with st.sidebar:
            from ui_components.sidebar_components import create_sidebar_header_with_icon
            create_sidebar_header_with_icon()
        
        # Handle authentication
        authentication_status = handle_authentication()
        
        # Check authentication status and proceed accordingly
        if authentication_status:
            # User is authenticated - initialize and run the main application
            init_session()
            mcp_app.main()
            
        elif authentication_status is False:
            # Authentication failed - show error message
            show_authentication_required_message()
            st.error("❌ Authentication failed. Please check your credentials and try again.")
            
        else:
            # Not authenticated yet - show welcome message
            show_authentication_required_message()
            
    except Exception as e:
        st.error(f"❌ Application error: {str(e)}")
        logging.error(f"Application error: {str(e)}")
        # Still show authentication if there's an error
        if st.session_state.get("authentication_status") is None:
            show_authentication_required_message()


if __name__ == "__main__":
    main()
'''
            
            # Backup original app.py first
            if os.path.exists(self.app_py_path):
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                backup_path = os.path.join(self.backup_dir, f"app_original_{timestamp}.py")
                shutil.copy2(self.app_py_path, backup_path)
                print(f"✅ Original app.py backed up to: {backup_path}")
            
            # Write fallback app
            if self.write_file_safely(self.app_py_path, fallback_content):
                print("✅ Fallback app.py created successfully")
                return True
            else:
                return False
                
        except Exception as e:
            print(f"❌ Failed to create fallback app: {str(e)}")
            return False


def print_banner():
    """Print configuration updater banner."""
    print("""
╔═══════════════════════════════════════════════════════════════════════════════╗
║                      APPLICATION CONFIGURATION UPDATER                       ║
║                          SQLite Authentication Setup                         ║
║                                  (FIXED VERSION)                             ║
╠═══════════════════════════════════════════════════════════════════════════════╣
║  This script will update your Streamlit application to use SQLite            ║
║  authentication after user migration.                                        ║
║                                                                               ║
║  FIXES:                                                                       ║
║  • Windows character encoding issues                                          ║
║  • Automatic encoding detection                                               ║
║  • Safe file reading/writing                                                  ║
║  • Fallback options for problematic files                                     ║
╚═══════════════════════════════════════════════════════════════════════════════╝
    """)


def main():
    """Main configuration update script."""
    print_banner()
    
    updater = AppConfigUpdater()
    
    # Check prerequisites
    print("\n🔍 CHECKING PREREQUISITES:")
    print("-" * 50)
    
    prerequisites = {
        'SQLite Database': os.path.exists('keys/users.db'),
        'Enhanced Security Module': os.path.exists('utils/enhanced_security_config.py'),
        'User Management Tab': os.path.exists('ui_components/user_management_tab.py'),
        'Application File': os.path.exists('app.py')
    }
    
    all_prereqs_met = True
    for name, exists in prerequisites.items():
        status = "✅ Found" if exists else "❌ Missing"
        print(f"{name}: {status}")
        if not exists:
            all_prereqs_met = False
    
    if not all_prereqs_met:
        print("\n❌ Prerequisites not met. Please:")
        print("1. Run user migration script first")
        print("2. Ensure all required files are in place")
        return
    
    # Configuration options
    print("\n🔧 CONFIGURATION OPTIONS:")
    print("-" * 50)
    print("1. 🔄 Update Application Configuration")
    print("2. 📋 Create Environment Template")
    print("3. 📦 Update Dependencies")
    print("4. ✅ Verify Complete Setup")
    print("5. 🚀 Full Setup (All of the above)")
    print("6. 🛠️ Create Fallback App (if main update fails)")
    print("7. ❌ Exit")
    
    while True:
        try:
            choice = input("\nSelect option (1-7): ").strip()
            
            if choice == "1":
                print("\n🔄 Updating Application Configuration...")
                if updater.create_backup():
                    if updater.update_app_py():
                        print("✅ Application configuration updated successfully!")
                    else:
                        print("❌ Failed to update application configuration")
                        print("💡 Try option 6 (Create Fallback App) instead")
                break
                
            elif choice == "2":
                print("\n📋 Creating Environment Template...")
                if updater.create_env_template():
                    print("✅ Environment template created successfully!")
                    print("📝 Next step: Copy .env.template to .env and update values")
                else:
                    print("❌ Failed to create environment template")
                break
                
            elif choice == "3":
                print("\n📦 Updating Dependencies...")
                if updater.update_requirements():
                    print("✅ Dependencies updated successfully!")
                    print("📝 Next step: Run 'pip install -r requirements.txt'")
                else:
                    print("❌ Failed to update dependencies")
                break
                
            elif choice == "4":
                print("\n✅ Verifying Complete Setup...")
                results = updater.verify_setup()
                print_verification_results(results)
                break
                
            elif choice == "5":
                print("\n🚀 Running Full Setup...")
                
                success_count = 0
                total_steps = 4
                
                # Step 1: Backup and update app
                if updater.create_backup():
                    print("✅ Application backup created")
                    success_count += 1
                else:
                    print("❌ Backup failed - stopping")
                    break
                
                if updater.update_app_py():
                    print("✅ Application configuration updated")
                    success_count += 1
                else:
                    print("⚠️  App update failed - trying fallback...")
                    if updater.create_simple_fallback_app():
                        print("✅ Fallback app created successfully")
                        success_count += 1
                    else:
                        print("❌ Fallback app creation failed - stopping")
                        break
                
                # Step 2: Create environment template
                if updater.create_env_template():
                    print("✅ Environment template created")
                    success_count += 1
                else:
                    print("⚠️  Environment template creation failed")
                
                # Step 3: Update requirements
                if updater.update_requirements():
                    print("✅ Requirements updated")
                    success_count += 1
                else:
                    print("⚠️  Requirements update failed")
                
                # Step 4: Verify setup
                print("\n🔍 Verifying complete setup...")
                results = updater.verify_setup()
                print_verification_results(results)
                
                print(f"\n📊 Setup Progress: {success_count}/{total_steps} steps completed")
                
                if success_count >= 2:  # At least backup and app update
                    print("\n🎉 SETUP COMPLETED!")
                    print_next_steps()
                else:
                    print("\n⚠️  Setup completed with issues. See verification results above.")
                
                break
                
            elif choice == "6":
                print("\n🛠️ Creating Fallback App...")
                if updater.create_backup():
                    if updater.create_simple_fallback_app():
                        print("✅ Fallback app created successfully!")
                        print("📝 This app includes SQLite support with YAML fallback")
                    else:
                        print("❌ Failed to create fallback app")
                else:
                    print("❌ Backup failed - stopping")
                break
                
            elif choice == "7":
                print("👋 Exiting configuration updater.")
                break
                
            else:
                print("❌ Invalid option. Please select 1-7.")
                
        except KeyboardInterrupt:
            print("\n\n👋 Configuration updater interrupted by user.")
            break
        except Exception as e:
            print(f"\n❌ Error: {str(e)}")
            break


def print_verification_results(results: Dict):
    """Print formatted verification results."""
    print("\n✅ SETUP VERIFICATION RESULTS:")
    print("=" * 50)
    
    print("📁 Required Files:")
    for file_path, exists in results['files_present'].items():
        status = "✅ Present" if exists else "❌ Missing"
        print(f"  • {file_path}: {status}")
    
    print("\n📦 Dependencies:")
    for dep, installed in results['dependencies_installed'].items():
        status = "✅ Installed" if installed else "❌ Missing"
        print(f"  • {dep}: {status}")
    
    config_status = "✅ Valid" if results['configuration_valid'] else "❌ Invalid"
    print(f"\n🔧 Configuration: {config_status}")
    
    app_status = "✅ Updated" if results.get('app_updated', False) else "❌ Not Updated"
    print(f"📱 App.py: {app_status}")
    
    overall_status = "🎉 READY" if results['ready_for_sqlite'] else "⚠️  NEEDS ATTENTION"
    print(f"\n🚀 SQLite Authentication: {overall_status}")


def print_next_steps():
    """Print next steps after successful setup."""
    print("\n📋 NEXT STEPS:")
    print("=" * 50)
    print("1. 📦 Install new dependencies:")
    print("   pip install -r requirements.txt")
    print()
    print("2. 📝 Update your .env file:")
    print("   cp .env.template .env")
    print("   # Edit .env with your specific values")
    print("   # Set USE_SQLITE=true to enable SQLite authentication")
    print()
    print("3. 🧪 Test the application:")
    print("   streamlit run app.py")
    print("   # Login with migrated user credentials")
    print()
    print("4. 👥 Distribute temporary passwords:")
    print("   # Check keys/migration_backup/ for temp passwords")
    print("   # Ensure users change passwords on first login")
    print()
    print("🔒 Security Notes:")
    print("• The app now supports both SQLite and YAML authentication")
    print("• Set USE_SQLITE=true in .env to use SQLite")
    print("• Users will need to change their temporary passwords")
    print("• Monitor audit logs for security events")


if __name__ == "__main__":
    main()