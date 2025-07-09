#!/usr/bin/env python3
"""
Authentication Verification Script
Test if SQLite authentication is now working properly

Usage:
    python verify_authentication.py
"""

import sys
import os

def test_sqlite_authentication():
    """Test SQLite authentication with the fixed module."""
    print("🧪 Testing Fixed SQLite Authentication")
    print("=" * 40)
    
    try:
        # Import the fixed module
        sys.path.insert(0, '.')
        from utils.enhanced_security_config import StreamlitSecureAuth
        
        # Test credentials from the comprehensive fix
        test_credentials = [
            ('admin', 'very_Secure_p@ssword_123!'),
            ('juan', 'Larisa1000@'),
            ('giovanni_romero', 'MrRomero2024!'),
            ('demo_user', 'strong_password_123!'),
            ('test_admin', 'test_admin_123!')
        ]
        
        auth = StreamlitSecureAuth('sqlite')
        successful_logins = []
        
        for username, password in test_credentials:
            print(f"\n🔐 Testing: {username}")
            
            try:
                success, user_data, message = auth.authenticate(username, password)
                
                if success:
                    print(f"   ✅ SUCCESS - {user_data['name']}")
                    print(f"   📧 Email: {user_data['email']}")
                    print(f"   👑 Admin: {'Yes' if user_data.get('is_admin') else 'No'}")
                    if 'session_token' in user_data:
                        print(f"   🎫 Session: {user_data['session_token'][:20]}...")
                    successful_logins.append((username, password))
                else:
                    print(f"   ❌ FAILED - {message}")
                    
            except Exception as e:
                print(f"   💥 ERROR - {str(e)}")
        
        print(f"\n" + "=" * 40)
        print("📊 RESULTS:")
        print(f"   Successful logins: {len(successful_logins)}/{len(test_credentials)}")
        
        if successful_logins:
            print(f"\n✅ WORKING CREDENTIALS:")
            for username, password in successful_logins:
                print(f"   • {username} / {password}")
            
            return True
        else:
            print(f"\n❌ No successful logins")
            return False
            
    except ImportError as e:
        print(f"❌ Import error: {str(e)}")
        print("💡 Make sure the enhanced_security_config.py file is updated")
        return False
    except Exception as e:
        print(f"❌ Test error: {str(e)}")
        return False

def test_streamlit_config():
    """Test streamlit-authenticator config generation."""
    print(f"\n🔧 Testing Streamlit Config Generation")
    print("=" * 40)
    
    try:
        from utils.enhanced_security_config import StreamlitSecureAuth
        
        auth = StreamlitSecureAuth('sqlite')
        config = auth.get_config_for_streamlit_authenticator()
        
        users = config.get('credentials', {}).get('usernames', {})
        print(f"✅ Config generated with {len(users)} users")
        
        # Check structure
        required_keys = ['credentials', 'cookie', 'preauthorized']
        for key in required_keys:
            if key in config:
                print(f"   ✅ {key}: Present")
            else:
                print(f"   ❌ {key}: Missing")
                return False
        
        # Check users have valid hashes
        valid_users = 0
        for username, user_data in users.items():
            password_hash = user_data.get('password', '')
            if password_hash and password_hash.startswith('$2b$'):
                valid_users += 1
        
        print(f"   ✅ Users with valid hashes: {valid_users}/{len(users)}")
        
        return valid_users == len(users)
        
    except Exception as e:
        print(f"❌ Config test error: {str(e)}")
        return False

def main():
    """Main verification function."""
    print("🔍 SQLite Authentication Verification")
    print("=" * 50)
    
    # Check environment
    use_sqlite = os.getenv('USE_SQLITE', 'false').lower() == 'true'
    print(f"🔍 USE_SQLITE: {use_sqlite}")
    
    if not use_sqlite:
        print("⚠️  Set USE_SQLITE=true in your environment")
        return
    
    # Test authentication
    auth_success = test_sqlite_authentication()
    
    # Test config generation
    config_success = test_streamlit_config()
    
    # Final results
    print(f"\n" + "=" * 50)
    print("🎯 FINAL VERIFICATION RESULTS:")
    print(f"   Authentication: {'✅ WORKING' if auth_success else '❌ FAILED'}")
    print(f"   Config Generation: {'✅ WORKING' if config_success else '❌ FAILED'}")
    
    if auth_success and config_success:
        print(f"\n🎉 SUCCESS! SQLite authentication is now working!")
        print(f"🚀 You can restart your Streamlit app and login with any of the working credentials above.")
    else:
        print(f"\n❌ There are still issues that need to be resolved.")
        print(f"💡 Check the error messages above for guidance.")

if __name__ == "__main__":
    main()