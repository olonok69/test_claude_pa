import sqlite3
import json
from datetime import datetime
from typing import Dict, List, Tuple, Optional
import pandas as pd

class WheatProductionDB:
    """Database handler for wheat production data"""
    
    def __init__(self, db_path: str = "wheat_production.db"):
        self.db_path = db_path
    
    def get_connection(self):
        """Get database connection"""
        return sqlite3.connect(self.db_path)
    
    def get_all_production_data(self) -> Dict:
        """Get all production data in the format expected by the Streamlit app"""
        
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute('''
                SELECT country, year, production_value, percentage_world, change_value, status
                FROM wheat_production
                ORDER BY country, year
            ''')
            
            rows = cursor.fetchall()
            
            # Convert to the nested dictionary format
            data = {}
            for country, year, production, percentage, change, status in rows:
                if country not in data:
                    data[country] = {}
                
                data[country][year] = production
                if percentage is not None:
                    data[country][f"{year}_pct"] = percentage
                if change is not None:
                    data[country][f"{year}_change"] = change
            
            return data
            
        finally:
            conn.close()
    
    def update_production_value(self, country: str, year: str, production: float, change: float = None):
        """Update production value for a specific country and year"""
        
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            # Get old values for audit
            cursor.execute('''
                SELECT production_value, change_value FROM wheat_production 
                WHERE country = ? AND year = ?
            ''', (country, year))
            
            old_data = cursor.fetchone()
            old_values = {"production": old_data[0], "change": old_data[1]} if old_data else None
            
            # Update the record
            cursor.execute('''
                UPDATE wheat_production 
                SET production_value = ?, change_value = ?, updated_at = ?
                WHERE country = ? AND year = ?
            ''', (production, change, datetime.now().isoformat(), country, year))
            
            # Log the change
            if old_values:
                new_values = {"production": production, "change": change}
                self._log_audit(cursor, "wheat_production", f"{country}_{year}", "UPDATE", 
                              old_values, new_values, "streamlit_user")
            
            conn.commit()
            return True
            
        except Exception as e:
            conn.rollback()
            print(f"Error updating production value: {e}")
            return False
        finally:
            conn.close()
    
    def get_metadata(self, key: str = None) -> Dict:
        """Get metadata values"""
        
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            if key:
                cursor.execute("SELECT value FROM metadata WHERE key = ?", (key,))
                result = cursor.fetchone()
                return result[0] if result else None
            else:
                cursor.execute("SELECT key, value FROM metadata")
                return dict(cursor.fetchall())
        finally:
            conn.close()
    
    def update_metadata(self, key: str, value: str):
        """Update metadata value"""
        
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute('''
                INSERT OR REPLACE INTO metadata (key, value, updated_at)
                VALUES (?, ?, ?)
            ''', (key, value, datetime.now().isoformat()))
            
            conn.commit()
            return True
        except Exception as e:
            print(f"Error updating metadata: {e}")
            return False
        finally:
            conn.close()
    
    def get_production_dataframe(self) -> pd.DataFrame:
        """Get production data as a pandas DataFrame"""
        
        conn = self.get_connection()
        
        try:
            df = pd.read_sql_query('''
                SELECT country, year, production_value, percentage_world, change_value, status
                FROM wheat_production
                ORDER BY 
                    CASE country
                        WHEN 'WORLD' THEN 1
                        WHEN 'China' THEN 2
                        WHEN 'European Union (FR, DE)' THEN 3
                        WHEN 'India' THEN 4
                        WHEN 'Russia' THEN 5
                        WHEN 'United States' THEN 6
                        WHEN 'Australia' THEN 7
                        WHEN 'Canada' THEN 8
                        ELSE 9
                    END,
                    year
            ''', conn)
            
            return df
        finally:
            conn.close()
    
    def backup_data(self) -> Dict:
        """Create a backup of all data"""
        
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            # Get all production data
            cursor.execute("SELECT * FROM wheat_production")
            production_data = cursor.fetchall()
            
            # Get all metadata
            cursor.execute("SELECT * FROM metadata")
            metadata_data = cursor.fetchall()
            
            backup = {
                "backup_timestamp": datetime.now().isoformat(),
                "production_data": production_data,
                "metadata_data": metadata_data
            }
            
            return backup
        finally:
            conn.close()
    
    def restore_data(self, backup_data: Dict):
        """Restore data from backup"""
        
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            # Clear existing data
            cursor.execute("DELETE FROM wheat_production")
            cursor.execute("DELETE FROM metadata")
            
            # Restore production data
            for row in backup_data["production_data"]:
                cursor.execute('''
                    INSERT INTO wheat_production 
                    (id, country, year, production_value, percentage_world, change_value, status, created_at, updated_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', row)
            
            # Restore metadata
            for row in backup_data["metadata_data"]:
                cursor.execute('''
                    INSERT INTO metadata (id, key, value, created_at, updated_at)
                    VALUES (?, ?, ?, ?, ?)
                ''', row)
            
            conn.commit()
            return True
        except Exception as e:
            conn.rollback()
            print(f"Error restoring data: {e}")
            return False
        finally:
            conn.close()
    
    def get_audit_log(self, limit: int = 50) -> List[Tuple]:
        """Get recent audit log entries"""
        
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute('''
                SELECT table_name, record_id, action, old_values, new_values, changed_by, changed_at
                FROM audit_log
                ORDER BY changed_at DESC
                LIMIT ?
            ''', (limit,))
            
            return cursor.fetchall()
        finally:
            conn.close()
    
    def _log_audit(self, cursor, table_name: str, record_id: str, action: str, 
                   old_values: Dict, new_values: Dict, changed_by: str):
        """Log an audit entry"""
        
        cursor.execute('''
            INSERT INTO audit_log (table_name, record_id, action, old_values, new_values, changed_by)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (
            table_name,
            record_id,
            action,
            json.dumps(old_values) if old_values else None,
            json.dumps(new_values) if new_values else None,
            changed_by
        ))
    
    def get_countries_list(self) -> List[str]:
        """Get list of all countries in the database"""
        
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute("SELECT DISTINCT country FROM wheat_production ORDER BY country")
            return [row[0] for row in cursor.fetchall()]
        finally:
            conn.close()
    
    def get_years_list(self) -> List[str]:
        """Get list of all years in the database"""
        
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute("SELECT DISTINCT year FROM wheat_production ORDER BY year")
            return [row[0] for row in cursor.fetchall()]
        finally:
            conn.close()
    
    def export_to_csv(self, filename: str = None) -> str:
        """Export data to CSV file"""
        
        if not filename:
            filename = f"wheat_production_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        
        df = self.get_production_dataframe()
        df.to_csv(filename, index=False)
        return filename
    
    def import_from_csv(self, filename: str) -> bool:
        """Import data from CSV file"""
        
        try:
            df = pd.read_csv(filename)
            
            conn = self.get_connection()
            cursor = conn.cursor()
            
            # Clear existing data
            cursor.execute("DELETE FROM wheat_production")
            
            # Insert new data
            for _, row in df.iterrows():
                cursor.execute('''
                    INSERT INTO wheat_production 
                    (country, year, production_value, percentage_world, change_value, status)
                    VALUES (?, ?, ?, ?, ?, ?)
                ''', (
                    row['country'],
                    row['year'],
                    row['production_value'],
                    row.get('percentage_world'),
                    row.get('change_value'),
                    row.get('status', 'estimate')
                ))
            
            conn.commit()
            conn.close()
            return True
            
        except Exception as e:
            print(f"Error importing from CSV: {e}")
            return False

# Convenience functions for direct use
def get_db_instance():
    """Get database instance"""
    return WheatProductionDB()

def init_database():
    """Initialize database if it doesn't exist"""
    db = WheatProductionDB()
    conn = db.get_connection()
    
    # Check if tables exist
    cursor = conn.cursor()
    cursor.execute("""
        SELECT name FROM sqlite_master 
        WHERE type='table' AND name='wheat_production'
    """)
    
    if not cursor.fetchone():
        conn.close()
        print("Database not found. Please run the setup script first:")
        print("python database_setup.py")
        return False
    
    conn.close()
    return True