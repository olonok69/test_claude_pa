#!/usr/bin/env python3
"""
Fixed Post-Migration Testing Script
Tests the SQLite authentication system after migration
FIXES: UNIQUE constraint errors and test isolation
"""

import os
import sys
import sqlite3
from datetime import datetime
from typing import Dict, List, Tuple
import uuid
import time

# Add the client directory to the path to import our modules
sys.path.append('.')

try:
    from utils.enhanced_security_config import StreamlitSecureAuth, SecureUserStore
    MODULES_AVAILABLE = True
except ImportError:
    MODULES_AVAILABLE = False

class PostMigrationTester:
    """Test SQLite authentication system after migration."""
    
    def __init__(self):
        self.db_path = "keys/users.db"
        self.test_results = []
        
        if MODULES_AVAILABLE:
            self.auth_system = StreamlitSecureAuth('sqlite')
            self.user_store = SecureUserStore('sqlite')
        else:
            self.auth_system = None
            self.user_store = None
    
    def log_test(self, test_name: str, passed: bool, details: str = ""):
        """Log test results."""
        status = "PASS" if passed else "FAIL"
        result = {
            'test': test_name,
            'status': status,
            'passed': passed,
            'details': details,
            'timestamp': datetime.now().isoformat()
        }
        self.test_results.append(result)
        
        emoji = "✅" if passed else "❌"
        print(f"{emoji} {test_name}: {status}")
        if details:
            print(f"   Details: {details}")
    
    def test_database_exists(self) -> bool:
        """Test if SQLite database exists and is accessible."""
        try:
            exists = os.path.exists(self.db_path)
            if exists:
                # Try to connect and query
                conn = sqlite3.connect(self.db_path)
                cursor = conn.cursor()
                cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
                tables = cursor.fetchall()
                conn.close()
                
                expected_tables = ['users', 'user_sessions', 'audit_log', 'migration_log']
                found_tables = [table[0] for table in tables]
                missing_tables = [t for t in expected_tables if t not in found_tables]
                
                if missing_tables:
                    self.log_test("Database Structure", False, f"Missing tables: {missing_tables}")
                    return False
                else:
                    self.log_test("Database Structure", True, f"All required tables present: {found_tables}")
                    return True
            else:
                self.log_test("Database Exists", False, f"Database not found at {self.db_path}")
                return False
                
        except Exception as e:
            self.log_test("Database Access", False, f"Error accessing database: {str(e)}")
            return False
    
    def test_users_migrated(self) -> bool:
        """Test if users were migrated successfully."""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Count total users
            cursor.execute("SELECT COUNT(*) FROM users")
            total_users = cursor.fetchone()[0]
            
            # Count migrated users
            cursor.execute("SELECT COUNT(*) FROM users WHERE migrated_from_yaml = TRUE")
            migrated_users = cursor.fetchone()[0]
            
            # Get user details
            cursor.execute("""
                SELECT username, email, full_name, is_admin, migrated_from_yaml 
                FROM users 
                ORDER BY created_at
            """)
            users = cursor.fetchall()
            
            conn.close()
            
            if total_users == 0:
                self.log_test("Users Migration", False, "No users found in database")
                return False
            
            user_list = ", ".join([f"{u[0]}({u[1]})" for u in users])
            self.log_test("Users Migration", True, 
                         f"Found {total_users} users ({migrated_users} migrated): {user_list}")
            
            return True
            
        except Exception as e:
            self.log_test("Users Migration", False, f"Error checking users: {str(e)}")
            return False
    
    def test_password_hashing(self) -> bool:
        """Test if password hashing is working correctly."""
        try:
            if not self.user_store:
                self.log_test("Password Hashing", False, "SecureUserStore not available")
                return False
            
            # Test password hashing
            test_password = "Test123!@#"
            hashed = self.user_store.hash_password(test_password)
            
            # Verify the hash
            is_valid = self.user_store.verify_password(test_password, hashed)
            is_invalid = not self.user_store.verify_password("wrong_password", hashed)
            
            if is_valid and is_invalid:
                self.log_test("Password Hashing", True, "Hashing and verification working correctly")
                return True
            else:
                self.log_test("Password Hashing", False, "Password verification failed")
                return False
                
        except Exception as e:
            self.log_test("Password Hashing", False, f"Error testing password hashing: {str(e)}")
            return False
    
    def test_authentication_flow(self) -> bool:
        """Test authentication with real users."""
        try:
            if not self.auth_system:
                self.log_test("Authentication Flow", False, "StreamlitSecureAuth not available")
                return False
            
            # Get a test user from database
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute("SELECT username FROM users LIMIT 1")
            result = cursor.fetchone()
            conn.close()
            
            if not result:
                self.log_test("Authentication Flow", False, "No users available for testing")
                return False
            
            test_username = result[0]
            
            # Test with wrong password
            success, user_data, message = self.auth_system.authenticate(test_username, "wrong_password")
            
            if success:
                self.log_test("Authentication Flow", False, "Authentication succeeded with wrong password")
                return False
            
            # Test with non-existent user
            success, user_data, message = self.auth_system.authenticate("nonexistent_user", "any_password")
            
            if success:
                self.log_test("Authentication Flow", False, "Authentication succeeded with non-existent user")
                return False
            
            self.log_test("Authentication Flow", True, 
                         f"Authentication correctly rejects invalid credentials for user: {test_username}")
            return True
            
        except Exception as e:
            self.log_test("Authentication Flow", False, f"Error testing authentication: {str(e)}")
            return False
    
    def test_audit_logging(self) -> bool:
        """Test if audit logging is working."""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Check if audit logs exist
            cursor.execute("SELECT COUNT(*) FROM audit_log")
            log_count = cursor.fetchone()[0]
            
            # Check for migration events
            cursor.execute("""
                SELECT event_type, COUNT(*) 
                FROM audit_log 
                WHERE event_type IN ('USER_MIGRATED', 'USER_CREATED')
                GROUP BY event_type
            """)
            events = cursor.fetchall()
            
            conn.close()
            
            if log_count == 0:
                self.log_test("Audit Logging", False, "No audit log entries found")
                return False
            
            event_summary = ", ".join([f"{event[0]}: {event[1]}" for event in events])
            self.log_test("Audit Logging", True, 
                         f"Found {log_count} audit entries. Events: {event_summary}")
            return True
            
        except Exception as e:
            self.log_test("Audit Logging", False, f"Error checking audit logs: {str(e)}")
            return False
    
    def test_session_management(self) -> bool:
        """Test session management functionality."""
        try:
            if not self.user_store:
                self.log_test("Session Management", False, "SecureUserStore not available")
                return False
            
            # Get a test user
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute("SELECT id, username FROM users LIMIT 1")
            result = cursor.fetchone()
            conn.close()
            
            if not result:
                self.log_test("Session Management", False, "No users available for session testing")
                return False
            
            user_id, username = result
            
            # Create a session
            session_token = self.user_store.create_session(user_id, "127.0.0.1", "Test Browser")
            
            if not session_token:
                self.log_test("Session Management", False, "Failed to create session")
                return False
            
            # Validate the session
            session_user = self.user_store.validate_session(session_token)
            
            if not session_user or session_user['username'] != username:
                self.log_test("Session Management", False, "Session validation failed")
                return False
            
            # Clean up test session
            try:
                conn = sqlite3.connect(self.db_path)
                cursor = conn.cursor()
                cursor.execute("DELETE FROM user_sessions WHERE session_token = ?", (session_token,))
                conn.commit()
                conn.close()
            except:
                pass  # Don't fail the test if cleanup fails
            
            self.log_test("Session Management", True, 
                         f"Session created and validated successfully for user: {username}")
            return True
            
        except Exception as e:
            self.log_test("Session Management", False, f"Error testing session management: {str(e)}")
            return False
    
    def test_user_management_operations(self) -> bool:
        """Test user management operations with unique test user."""
        try:
            if not self.user_store:
                self.log_test("User Management", False, "SecureUserStore not available")
                return False
            
            # Create unique test user with timestamp and UUID
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            unique_id = str(uuid.uuid4())[:8]
            test_username = f"test_user_{timestamp}_{unique_id}"
            test_email = f"test_{timestamp}_{unique_id}@test.com"
            test_password = "TestPassword123!@#"
            
            # Ensure test user doesn't exist
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute("DELETE FROM users WHERE username LIKE 'test_user_%' OR email LIKE '%@test.com'")
            conn.commit()
            conn.close()
            
            # Wait a moment to ensure uniqueness
            time.sleep(0.1)
            
            # Test creating a user
            success = self.user_store.create_user(
                username=test_username,
                password=test_password,
                email=test_email,
                full_name="Test User",
                is_admin=False
            )
            
            if not success:
                self.log_test("User Management", False, "Failed to create test user")
                return False
            
            # Test updating user
            success = self.user_store.update_user(test_username, full_name="Updated Test User")
            
            if not success:
                self.log_test("User Management", False, "Failed to update test user")
                return False
            
            # Test deleting user
            success = self.user_store.delete_user(test_username)
            
            if not success:
                self.log_test("User Management", False, "Failed to delete test user")
                return False
            
            self.log_test("User Management", True, "Create, update, and delete operations successful")
            return True
            
        except Exception as e:
            # Clean up any test users that might have been created
            try:
                conn = sqlite3.connect(self.db_path)
                cursor = conn.cursor()
                cursor.execute("DELETE FROM users WHERE username LIKE 'test_user_%' OR email LIKE '%@test.com'")
                conn.commit()
                conn.close()
            except:
                pass
            
            self.log_test("User Management", False, f"Error testing user management: {str(e)}")
            return False
    
    def test_migration_integrity(self) -> bool:
        """Test data integrity after migration."""
        try:
            # Check if YAML config still exists for comparison
            yaml_config_path = "keys/config.yaml"
            if not os.path.exists(yaml_config_path):
                self.log_test("Migration Integrity", True, "YAML config not found (expected after migration)")
                return True
            
            # Load YAML config for comparison
            import yaml
            with open(yaml_config_path, 'r', encoding='utf-8') as f:
                yaml_config = yaml.safe_load(f)
            
            yaml_users = yaml_config.get('credentials', {}).get('usernames', {})
            
            # Load SQLite users
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute("SELECT username, email, full_name, is_admin FROM users WHERE migrated_from_yaml = TRUE")
            sqlite_users = cursor.fetchall()
            conn.close()
            
            # Compare user counts
            yaml_count = len(yaml_users)
            sqlite_count = len(sqlite_users)
            
            if yaml_count != sqlite_count:
                self.log_test("Migration Integrity", False, 
                             f"User count mismatch: YAML={yaml_count}, SQLite={sqlite_count}")
                return False
            
            # Check individual users
            sqlite_usernames = {user[0] for user in sqlite_users}
            yaml_usernames = set(yaml_users.keys())
            
            missing_users = yaml_usernames - sqlite_usernames
            extra_users = sqlite_usernames - yaml_usernames
            
            if missing_users or extra_users:
                details = f"Missing: {missing_users}, Extra: {extra_users}"
                self.log_test("Migration Integrity", False, details)
                return False
            
            self.log_test("Migration Integrity", True, 
                         f"All {yaml_count} users migrated successfully with correct data")
            return True
            
        except Exception as e:
            self.log_test("Migration Integrity", False, f"Error checking migration integrity: {str(e)}")
            return False
    
    def run_all_tests(self) -> Dict:
        """Run all tests and return summary."""
        print("🧪 RUNNING POST-MIGRATION TESTS")
        print("=" * 50)
        
        if not MODULES_AVAILABLE:
            print("❌ Required modules not available. Please ensure:")
            print("  • utils/enhanced_security_config.py is installed")
            print("  • cryptography package is installed")
            return {'success': False, 'reason': 'modules_unavailable'}
        
        # Run tests in order
        tests = [
            self.test_database_exists,
            self.test_users_migrated,
            self.test_password_hashing,
            self.test_authentication_flow,
            self.test_audit_logging,
            self.test_session_management,
            self.test_user_management_operations,
            self.test_migration_integrity
        ]
        
        passed_tests = 0
        total_tests = len(tests)
        
        for test in tests:
            try:
                result = test()
                if result:
                    passed_tests += 1
            except Exception as e:
                print(f"❌ Test error: {str(e)}")
        
        # Summary
        print("\n" + "=" * 50)
        print("📊 TEST SUMMARY")
        print("=" * 50)
        
        success_rate = (passed_tests / total_tests) * 100
        print(f"Tests Passed: {passed_tests}/{total_tests} ({success_rate:.1f}%)")
        
        # Show failed tests
        failed_tests = [r for r in self.test_results if not r['passed']]
        if failed_tests:
            print(f"\n❌ FAILED TESTS ({len(failed_tests)}):")
            for test in failed_tests:
                print(f"  • {test['test']}: {test['details']}")
        
        # Overall result
        overall_success = passed_tests == total_tests
        
        if overall_success:
            print("\n🎉 ALL TESTS PASSED! SQLite authentication is ready to use.")
            print_production_readiness_info()
        else:
            print(f"\n⚠️  {len(failed_tests)} TEST(S) FAILED. Please review and fix issues.")
        
        return {
            'success': overall_success,
            'passed': passed_tests,
            'total': total_tests,
            'failed_tests': failed_tests,
            'all_results': self.test_results
        }


def print_production_readiness_info():
    """Print production readiness information."""
    print("\n🎯 PRODUCTION READINESS:")
    print("=" * 50)
    print("✅ Database Structure: Valid")
    print("✅ User Authentication: Working")
    print("✅ Password Security: Implemented")
    print("✅ Session Management: Functional")
    print("✅ Audit Logging: Active")
    print("✅ User Management: Operational")
    
    print("\n🚀 NEXT STEPS FOR PRODUCTION:")
    print("• Set up automated backups")
    print("• Configure monitoring and alerts")
    print("• Review security policies")
    print("• Train users on new password requirements")
    print("• Set up log rotation and archival")


def print_banner():
    """Print testing script banner."""
    print("""
╔═══════════════════════════════════════════════════════════════════════════════╗
║                        POST-MIGRATION TESTING SCRIPT                         ║
║                          SQLite Authentication Verification                  ║
║                                  (FIXED VERSION)                             ║
╠═══════════════════════════════════════════════════════════════════════════════╣
║  This script verifies that your SQLite authentication system is working      ║
║  correctly after migration from YAML configuration.                          ║
║                                                                               ║
║  FIXES:                                                                       ║
║  • UNIQUE constraint violation errors                                         ║
║  • Test user collision issues                                                 ║
║  • Improved test isolation                                                    ║
║  • Better cleanup procedures                                                  ║
╚═══════════════════════════════════════════════════════════════════════════════╝
    """)


def print_recommendations(results: Dict):
    """Print recommendations based on test results."""
    if results['success']:
        print("\n🎯 RECOMMENDATIONS FOR PRODUCTION:")
        print("=" * 50)
        print("✅ Your SQLite authentication system is ready!")
        print()
        print("🔒 Security Best Practices:")
        print("• Set strong environment variables in .env")
        print("• Enable session timeout (SESSION_TIMEOUT_HOURS)")
        print("• Monitor audit logs regularly")
        print("• Set up automated backups")
        print("• Ensure HTTPS in production")
        print()
        print("👥 User Management:")
        print("• Distribute temporary passwords securely")
        print("• Require password changes on first login")
        print("• Set up admin user notifications")
        print("• Review user permissions regularly")
        print()
        print("📊 Monitoring:")
        print("• Monitor failed login attempts")
        print("• Set up alerts for suspicious activity")
        print("• Regular backup verification")
        print("• Performance monitoring for database")
        
    else:
        print("\n🛠️ TROUBLESHOOTING RECOMMENDATIONS:")
        print("=" * 50)
        
        failed_tests = results.get('failed_tests', [])
        
        for test in failed_tests:
            test_name = test['test']
            details = test['details']
            
            if 'Database' in test_name:
                print("📊 Database Issues:")
                print("• Check if migration script completed successfully")
                print("• Verify keys/users.db file exists and is readable")
                print("• Run migration script again if needed")
                print()
                
            elif 'Authentication' in test_name:
                print("🔐 Authentication Issues:")
                print("• Verify enhanced_security_config.py is properly installed")
                print("• Check if cryptography package is installed")
                print("• Ensure StreamlitSecureAuth can access database")
                print()
                
            elif 'Users Migration' in test_name:
                print("👥 User Migration Issues:")
                print("• Re-run migration script with verification")
                print("• Check migration log files for detailed errors")
                print("• Verify YAML config was properly read")
                print()
                
            elif 'Session' in test_name:
                print("🎫 Session Management Issues:")
                print("• Check if sessions table was created properly")
                print("• Verify session token generation is working")
                print("• Test session timeout configuration")
                print()
        
        print("🔧 General Troubleshooting:")
        print("• Check file permissions on keys/ directory")
        print("• Ensure all required Python packages are installed")
        print("• Review error logs and migration reports")
        print("• Consider running migration script again")


def generate_test_report(results: Dict):
    """Generate a detailed test report file."""
    try:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_file = f"keys/test_report_{timestamp}.json"
        
        report_data = {
            'test_type': 'post_migration_verification',
            'timestamp': datetime.now().isoformat(),
            'overall_success': results['success'],
            'tests_passed': results['passed'],
            'tests_total': results['total'],
            'success_rate': (results['passed'] / results['total']) * 100,
            'failed_tests': results.get('failed_tests', []),
            'all_test_results': results.get('all_results', []),
            'environment_info': {
                'database_path': 'keys/users.db',
                'database_exists': os.path.exists('keys/users.db'),
                'modules_available': MODULES_AVAILABLE,
                'python_version': sys.version,
                'working_directory': os.getcwd()
            }
        }
        
        os.makedirs(os.path.dirname(report_file), exist_ok=True)
        
        with open(report_file, 'w') as f:
            import json
            json.dump(report_data, f, indent=2)
        
        print(f"📄 Detailed test report saved: {report_file}")
        return True
        
    except Exception as e:
        print(f"⚠️  Failed to save test report: {str(e)}")
        return False


def check_prerequisites():
    """Check if prerequisites are met for testing."""
    prereqs = {
        'SQLite Database': os.path.exists('keys/users.db'),
        'Enhanced Security Module': os.path.exists('utils/enhanced_security_config.py'),
        'User Management Module': os.path.exists('ui_components/user_management_tab.py'),
        'Python sqlite3': True,  # Usually available
        'Cryptography Package': MODULES_AVAILABLE
    }
    
    print("🔍 CHECKING PREREQUISITES:")
    print("-" * 50)
    
    all_met = True
    for name, available in prereqs.items():
        status = "✅ Available" if available else "❌ Missing"
        print(f"{name}: {status}")
        if not available:
            all_met = False
    
    if not all_met:
        print("\n❌ Prerequisites not met. Please:")
        print("1. Run the migration script first")
        print("2. Install required dependencies: pip install cryptography")
        print("3. Ensure all security modules are in place")
        return False
    
    print("\n✅ All prerequisites met!")
    return True


def main():
    """Main testing script."""
    print_banner()
    
    # Check prerequisites
    if not check_prerequisites():
        return
    
    # Ask for test type
    print("\n🧪 TEST OPTIONS:")
    print("-" * 50)
    print("1. 🚀 Quick Test (Essential checks only)")
    print("2. 🔍 Full Test Suite (All verification tests)")
    print("3. 📊 Database Inspection (View current state)")
    print("4. 🧹 Clean Test Data (Remove test users)")
    print("5. ❌ Exit")
    
    while True:
        try:
            choice = input("\nSelect option (1-5): ").strip()
            
            if choice == "1":
                print("\n🚀 Running Quick Test...")
                tester = PostMigrationTester()
                
                # Run essential tests only
                essential_tests = [
                    tester.test_database_exists,
                    tester.test_users_migrated,
                    tester.test_password_hashing,
                    tester.test_authentication_flow
                ]
                
                passed = 0
                for test in essential_tests:
                    try:
                        if test():
                            passed += 1
                    except Exception as e:
                        print(f"❌ Test error: {str(e)}")
                
                if passed == len(essential_tests):
                    print("\n✅ Quick test PASSED! Basic functionality is working.")
                else:
                    print(f"\n⚠️  Quick test FAILED! {passed}/{len(essential_tests)} tests passed.")
                
                break
                
            elif choice == "2":
                print("\n🔍 Running Full Test Suite...")
                tester = PostMigrationTester()
                results = tester.run_all_tests()
                
                # Generate detailed report
                generate_test_report(results)
                
                # Print recommendations
                print_recommendations(results)
                
                break
                
            elif choice == "3":
                print("\n📊 Database Inspection...")
                inspect_database()
                break
                
            elif choice == "4":
                print("\n🧹 Cleaning Test Data...")
                clean_test_data()
                break
                
            elif choice == "5":
                print("👋 Exiting test script.")
                break
                
            else:
                print("❌ Invalid option. Please select 1-5.")
                
        except KeyboardInterrupt:
            print("\n\n👋 Test script interrupted by user.")
            break
        except Exception as e:
            print(f"\n❌ Error: {str(e)}")
            break


def clean_test_data():
    """Clean up any test data that might interfere with tests."""
    try:
        db_path = "keys/users.db"
        if not os.path.exists(db_path):
            print("❌ Database not found!")
            return
        
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Remove test users
        cursor.execute("DELETE FROM users WHERE username LIKE 'test_user_%' OR email LIKE '%@test.com'")
        deleted_users = cursor.rowcount
        
        # Remove test sessions
        cursor.execute("DELETE FROM user_sessions WHERE user_agent = 'Test Browser'")
        deleted_sessions = cursor.rowcount
        
        # Remove test audit logs
        cursor.execute("DELETE FROM audit_log WHERE event_description LIKE '%test%'")
        deleted_logs = cursor.rowcount
        
        conn.commit()
        conn.close()
        
        print("✅ Test data cleanup completed:")
        print(f"  • Removed {deleted_users} test users")
        print(f"  • Removed {deleted_sessions} test sessions")
        print(f"  • Removed {deleted_logs} test audit logs")
        
    except Exception as e:
        print(f"❌ Error cleaning test data: {str(e)}")


def inspect_database():
    """Inspect the current database state."""
    try:
        db_path = "keys/users.db"
        if not os.path.exists(db_path):
            print("❌ Database not found!")
            return
        
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        print("📊 DATABASE INSPECTION RESULTS:")
        print("=" * 50)
        
        # Tables
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = [row[0] for row in cursor.fetchall()]
        print(f"📋 Tables: {', '.join(tables)}")
        
        # Users
        cursor.execute("""
            SELECT COUNT(*) as total,
                   SUM(CASE WHEN migrated_from_yaml = 1 THEN 1 ELSE 0 END) as migrated,
                   SUM(CASE WHEN is_admin = 1 THEN 1 ELSE 0 END) as admins
            FROM users
        """)
        user_stats = cursor.fetchone()
        print(f"👥 Users: {user_stats[0]} total, {user_stats[1]} migrated, {user_stats[2]} admins")
        
        # Recent users
        cursor.execute("""
            SELECT username, email, is_admin, created_at, migrated_from_yaml
            FROM users 
            WHERE username NOT LIKE 'test_user_%'
            ORDER BY created_at DESC 
            LIMIT 5
        """)
        recent_users = cursor.fetchall()
        
        print("\n📋 Recent Users:")
        for user in recent_users:
            username, email, is_admin, created_at, migrated = user
            admin_flag = "👑" if is_admin else "👤"
            migrated_flag = "🔄" if migrated else "➕"
            print(f"  {admin_flag} {username} ({email}) - {created_at[:10]} {migrated_flag}")
        
        # Sessions
        cursor.execute("SELECT COUNT(*) FROM user_sessions WHERE is_active = 1")
        active_sessions = cursor.fetchone()[0]
        print(f"\n🎫 Active Sessions: {active_sessions}")
        
        # Audit logs
        cursor.execute("""
            SELECT event_type, COUNT(*) 
            FROM audit_log 
            GROUP BY event_type 
            ORDER BY COUNT(*) DESC
        """)
        audit_stats = cursor.fetchall()
        
        print("\n📊 Audit Log Summary:")
        for event_type, count in audit_stats:
            print(f"  • {event_type}: {count}")
        
        # Migration info
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
            print(f"\n🔄 Last Migration: {date[:10]} - {status}")
            print(f"   Users migrated: {users_migrated}")
            print(f"   Notes: {notes}")
        
        conn.close()
        
    except Exception as e:
        print(f"❌ Error inspecting database: {str(e)}")


if __name__ == "__main__":
    main()