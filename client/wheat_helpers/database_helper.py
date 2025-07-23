import sqlite3
import json
from datetime import datetime
from typing import Dict, List, Tuple, Optional
import pandas as pd


class WheatProductionDB:
    """Database handler for wheat production and export data"""

    def __init__(self, db_path: str = "wheat_production.db"):
        self.db_path = db_path

    def get_connection(self):
        """Get database connection"""
        return sqlite3.connect(self.db_path)

    # Add these methods to the WheatProductionDB class

    def get_all_world_demand_data(self) -> Dict:
        """Get all world demand data in the format expected by the Streamlit app"""

        conn = self.get_connection()
        cursor = conn.cursor()

        try:
            cursor.execute(
                """
                SELECT category, year, demand_value, percentage_total, change_value, 
                    change_percentage, status
                FROM wheat_world_demand
                ORDER BY 
                    CASE category
                        WHEN 'Food' THEN 1
                        WHEN 'Feed' THEN 2
                        WHEN 'Industrial' THEN 3
                        WHEN 'Seed' THEN 4
                        WHEN 'Other' THEN 5
                        WHEN 'Total Consumption' THEN 6
                    END,
                    year
            """
            )

            rows = cursor.fetchall()

            # Convert to the nested dictionary format
            data = {}
            for category, year, value, pct_total, change, change_pct, status in rows:
                if category not in data:
                    data[category] = {}

                data[category][year] = value
                if pct_total is not None:
                    data[category][f"{year}_pct"] = pct_total
                if change is not None:
                    data[category][f"{year}_change"] = change
                if change_pct is not None:
                    data[category][f"{year}_change_pct"] = change_pct

            return data

        finally:
            conn.close()

    def update_world_demand_value(
        self,
        category: str,
        year: str,
        value: float,
        change: float = None,
        change_pct: float = None,
    ):
        """Update world demand value for a specific category and year"""

        conn = self.get_connection()
        cursor = conn.cursor()

        try:
            # Get old values for audit
            cursor.execute(
                """
                SELECT demand_value, change_value, change_percentage 
                FROM wheat_world_demand 
                WHERE category = ? AND year = ?
            """,
                (category, year),
            )

            old_data = cursor.fetchone()
            old_values = (
                {
                    "demand": old_data[0],
                    "change": old_data[1],
                    "change_pct": old_data[2],
                }
                if old_data
                else None
            )

            # Update the record
            cursor.execute(
                """
                UPDATE wheat_world_demand 
                SET demand_value = ?, change_value = ?, change_percentage = ?, updated_at = ?
                WHERE category = ? AND year = ?
            """,
                (value, change, change_pct, datetime.now().isoformat(), category, year),
            )

            # Log the change
            if old_values:
                new_values = {
                    "demand": value,
                    "change": change,
                    "change_pct": change_pct,
                }
                self._log_audit(
                    cursor,
                    "wheat_world_demand",
                    f"{category}_{year}",
                    "UPDATE",
                    old_values,
                    new_values,
                    "streamlit_user",
                )

            conn.commit()
            return True

        except Exception as e:
            conn.rollback()
            print(f"Error updating world demand value: {e}")
            return False
        finally:
            conn.close()

    def get_world_demand_dataframe(self) -> pd.DataFrame:
        """Get world demand data as a pandas DataFrame"""

        conn = self.get_connection()

        try:
            df = pd.read_sql_query(
                """
                SELECT category, year, demand_value, percentage_total, change_value, 
                    change_percentage, status
                FROM wheat_world_demand
                ORDER BY 
                    CASE category
                        WHEN 'Food' THEN 1
                        WHEN 'Feed' THEN 2
                        WHEN 'Industrial' THEN 3
                        WHEN 'Seed' THEN 4
                        WHEN 'Other' THEN 5
                        WHEN 'Total Consumption' THEN 6
                    END,
                    year
            """,
                conn,
            )

            return df
        finally:
            conn.close()

    # Production Data Methods
    def get_all_production_data(self) -> Dict:
        """Get all production data in the format expected by the Streamlit app"""

        conn = self.get_connection()
        cursor = conn.cursor()

        try:
            cursor.execute(
                """
                SELECT country, year, production_value, percentage_world, change_value, status
                FROM wheat_production
                ORDER BY country, year
            """
            )

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

    def update_production_value(
        self, country: str, year: str, production: float, change: float = None
    ):
        """Update production value for a specific country and year"""

        conn = self.get_connection()
        cursor = conn.cursor()

        try:
            # Get old values for audit
            cursor.execute(
                """
                SELECT production_value, change_value FROM wheat_production 
                WHERE country = ? AND year = ?
            """,
                (country, year),
            )

            old_data = cursor.fetchone()
            old_values = (
                {"production": old_data[0], "change": old_data[1]} if old_data else None
            )

            # Update the record
            cursor.execute(
                """
                UPDATE wheat_production 
                SET production_value = ?, change_value = ?, updated_at = ?
                WHERE country = ? AND year = ?
            """,
                (production, change, datetime.now().isoformat(), country, year),
            )

            # Log the change
            if old_values:
                new_values = {"production": production, "change": change}
                self._log_audit(
                    cursor,
                    "wheat_production",
                    f"{country}_{year}",
                    "UPDATE",
                    old_values,
                    new_values,
                    "streamlit_user",
                )

            conn.commit()
            return True

        except Exception as e:
            conn.rollback()
            print(f"Error updating production value: {e}")
            return False
        finally:
            conn.close()

    # Yield Data Methods
    def get_all_yield_data(self) -> Dict:
        """Get all yield data in the format expected by the Streamlit app"""

        conn = self.get_connection()
        cursor = conn.cursor()

        try:
            cursor.execute(
                """
                SELECT country, year, yield_value, change_value, change_percentage, 
                       yield_category, weather_impact, status
                FROM wheat_yield
                ORDER BY 
                    CASE country
                        WHEN 'WORLD' THEN 1
                        ELSE 2
                    END,
                    yield_value DESC
            """
            )

            rows = cursor.fetchall()

            # Convert to the nested dictionary format
            data = {}
            for (
                country,
                year,
                yield_val,
                change,
                change_pct,
                category,
                weather,
                status,
            ) in rows:
                if country not in data:
                    data[country] = {}

                data[country][year] = yield_val
                if change is not None:
                    data[country][f"{year}_change"] = change
                if change_pct is not None:
                    data[country][f"{year}_pct"] = change_pct
                if category is not None:
                    data[country][f"{year}_category"] = category
                if weather is not None:
                    data[country][f"{year}_weather"] = weather

            return data

        finally:
            conn.close()

    def update_yield_value(
        self,
        country: str,
        year: str,
        yield_val: float,
        change: float = None,
        change_pct: float = None,
        weather: str = None,
    ):
        """Update yield value for a specific country and year"""

        conn = self.get_connection()
        cursor = conn.cursor()

        try:
            # Determine category based on yield
            if yield_val >= 7.0:
                category = "Very High"
            elif yield_val >= 5.0:
                category = "High"
            elif yield_val >= 3.0:
                category = "Medium"
            elif yield_val >= 2.0:
                category = "Low"
            else:
                category = "Very Low"

            # Get old values for audit
            cursor.execute(
                """
                SELECT yield_value, change_value, change_percentage, weather_impact 
                FROM wheat_yield 
                WHERE country = ? AND year = ?
            """,
                (country, year),
            )

            old_data = cursor.fetchone()
            old_values = (
                {
                    "yield": old_data[0],
                    "change": old_data[1],
                    "change_pct": old_data[2],
                    "weather": old_data[3],
                }
                if old_data
                else None
            )

            # Update the record
            cursor.execute(
                """
                UPDATE wheat_yield 
                SET yield_value = ?, change_value = ?, change_percentage = ?, 
                    yield_category = ?, weather_impact = ?, updated_at = ?
                WHERE country = ? AND year = ?
            """,
                (
                    yield_val,
                    change,
                    change_pct,
                    category,
                    weather,
                    datetime.now().isoformat(),
                    country,
                    year,
                ),
            )

            # Log the change
            if old_values:
                new_values = {
                    "yield": yield_val,
                    "change": change,
                    "change_pct": change_pct,
                    "weather": weather,
                }
                self._log_audit(
                    cursor,
                    "wheat_yield",
                    f"{country}_{year}",
                    "UPDATE",
                    old_values,
                    new_values,
                    "streamlit_user",
                )

            conn.commit()
            return True

        except Exception as e:
            conn.rollback()
            print(f"Error updating yield value: {e}")
            return False
        finally:
            conn.close()

    # Acreage Data Methods
    def get_all_acreage_data(self) -> Dict:
        """Get all acreage data in the format expected by the Streamlit app"""

        conn = self.get_connection()
        cursor = conn.cursor()

        try:
            cursor.execute(
                """
                SELECT country, year, acreage_value, percentage_world, change_value, yield_per_hectare, status
                FROM wheat_acreage
                ORDER BY 
                    CASE country
                        WHEN 'WORLD' THEN 1
                        ELSE 2
                    END,
                    acreage_value DESC
            """
            )

            rows = cursor.fetchall()

            # Convert to the nested dictionary format
            data = {}
            for country, year, acreage, percentage, change, yield_val, status in rows:
                if country not in data:
                    data[country] = {}

                data[country][year] = acreage
                if percentage is not None:
                    data[country][f"{year}_pct"] = percentage
                if change is not None:
                    data[country][f"{year}_change"] = change
                if yield_val is not None:
                    data[country][f"{year}_yield"] = yield_val

            return data

        finally:
            conn.close()

    def update_acreage_value(
        self,
        country: str,
        year: str,
        acreage: float,
        change: float = None,
        yield_val: float = None,
    ):
        """Update acreage value for a specific country and year"""

        conn = self.get_connection()
        cursor = conn.cursor()

        try:
            # Get old values for audit
            cursor.execute(
                """
                SELECT acreage_value, change_value, yield_per_hectare FROM wheat_acreage 
                WHERE country = ? AND year = ?
            """,
                (country, year),
            )

            old_data = cursor.fetchone()
            old_values = (
                {"acreage": old_data[0], "change": old_data[1], "yield": old_data[2]}
                if old_data
                else None
            )

            # Update the record
            cursor.execute(
                """
                UPDATE wheat_acreage 
                SET acreage_value = ?, change_value = ?, yield_per_hectare = ?, updated_at = ?
                WHERE country = ? AND year = ?
            """,
                (acreage, change, yield_val, datetime.now().isoformat(), country, year),
            )

            # Log the change
            if old_values:
                new_values = {"acreage": acreage, "change": change, "yield": yield_val}
                self._log_audit(
                    cursor,
                    "wheat_acreage",
                    f"{country}_{year}",
                    "UPDATE",
                    old_values,
                    new_values,
                    "streamlit_user",
                )

            conn.commit()
            return True

        except Exception as e:
            conn.rollback()
            print(f"Error updating acreage value: {e}")
            return False
        finally:
            conn.close()

    # Stock-to-Use Ratio Methods
    def get_all_su_ratio_data(self) -> Dict:
        """Get all stock-to-use ratio data in the format expected by the Streamlit app"""

        conn = self.get_connection()
        cursor = conn.cursor()

        try:
            cursor.execute(
                """
                SELECT country, year, su_ratio, change_value, category, status
                FROM wheat_su_ratio
                ORDER BY 
                    CASE country
                        WHEN 'WORLD' THEN 1
                        WHEN 'China' THEN 2
                        WHEN 'United States' THEN 3
                        WHEN 'India' THEN 4
                        WHEN 'Russia' THEN 5
                        ELSE 999
                    END,
                    country, year
            """
            )

            rows = cursor.fetchall()

            # Convert to the nested dictionary format
            data = {}
            for country, year, su_ratio, change, category, status in rows:
                if country not in data:
                    data[country] = {}

                data[country][year] = su_ratio
                if change is not None:
                    data[country][f"{year}_change"] = change
                if category is not None:
                    data[country][f"{year}_category"] = category

            return data

        finally:
            conn.close()

    def update_su_ratio_value(
        self, country: str, year: str, su_ratio: float, change: float = None
    ):
        """Update S/U ratio value for a specific country and year"""

        conn = self.get_connection()
        cursor = conn.cursor()

        try:
            # Determine category based on ratio
            if su_ratio >= 50:
                category = "Strategic Reserve"
            elif su_ratio >= 30:
                category = "Comfortable"
            elif su_ratio >= 20:
                category = "Adequate"
            elif su_ratio >= 10:
                category = "Tight"
            else:
                category = "Critical"

            # Get old values for audit
            cursor.execute(
                """
                SELECT su_ratio, change_value, category FROM wheat_su_ratio 
                WHERE country = ? AND year = ?
            """,
                (country, year),
            )

            old_data = cursor.fetchone()
            old_values = (
                {
                    "su_ratio": old_data[0],
                    "change": old_data[1],
                    "category": old_data[2],
                }
                if old_data
                else None
            )

            # Update the record
            cursor.execute(
                """
                UPDATE wheat_su_ratio 
                SET su_ratio = ?, change_value = ?, category = ?, updated_at = ?
                WHERE country = ? AND year = ?
            """,
                (su_ratio, change, category, datetime.now().isoformat(), country, year),
            )

            # Log the change
            if old_values:
                new_values = {
                    "su_ratio": su_ratio,
                    "change": change,
                    "category": category,
                }
                self._log_audit(
                    cursor,
                    "wheat_su_ratio",
                    f"{country}_{year}",
                    "UPDATE",
                    old_values,
                    new_values,
                    "streamlit_user",
                )

            conn.commit()
            return True

        except Exception as e:
            conn.rollback()
            print(f"Error updating S/U ratio value: {e}")
            return False
        finally:
            conn.close()

    # Stocks Data Methods
    def get_all_stocks_data(self) -> Dict:
        """Get all ending stocks data in the format expected by the Streamlit app"""

        conn = self.get_connection()
        cursor = conn.cursor()

        try:
            cursor.execute(
                """
                SELECT country, year, stock_value, percentage_world, change_value, stock_to_use_ratio, status
                FROM wheat_stocks
                ORDER BY 
                    CASE country
                        WHEN 'WORLD' THEN 1
                        WHEN 'China' THEN 2
                        WHEN 'United States' THEN 3
                        WHEN 'European Union 27 (FR, DE)' THEN 4
                        WHEN 'India' THEN 5
                        WHEN 'Russia' THEN 6
                        ELSE 999
                    END,
                    country, year
            """
            )

            rows = cursor.fetchall()

            # Convert to the nested dictionary format
            data = {}
            for country, year, stock, percentage, change, su_ratio, status in rows:
                if country not in data:
                    data[country] = {}

                data[country][year] = stock
                if percentage is not None:
                    data[country][f"{year}_pct"] = percentage
                if change is not None:
                    data[country][f"{year}_change"] = change
                if su_ratio is not None:
                    data[country][f"{year}_s_u"] = su_ratio

            return data

        finally:
            conn.close()

    def update_stocks_value(
        self,
        country: str,
        year: str,
        stock: float,
        change: float = None,
        su_ratio: float = None,
    ):
        """Update stocks value for a specific country and year"""

        conn = self.get_connection()
        cursor = conn.cursor()

        try:
            # Get old values for audit
            cursor.execute(
                """
                SELECT stock_value, change_value, stock_to_use_ratio FROM wheat_stocks 
                WHERE country = ? AND year = ?
            """,
                (country, year),
            )

            old_data = cursor.fetchone()
            old_values = (
                {"stock": old_data[0], "change": old_data[1], "su_ratio": old_data[2]}
                if old_data
                else None
            )

            # Update the record
            cursor.execute(
                """
                UPDATE wheat_stocks 
                SET stock_value = ?, change_value = ?, stock_to_use_ratio = ?, updated_at = ?
                WHERE country = ? AND year = ?
            """,
                (stock, change, su_ratio, datetime.now().isoformat(), country, year),
            )

            # Log the change
            if old_values:
                new_values = {"stock": stock, "change": change, "su_ratio": su_ratio}
                self._log_audit(
                    cursor,
                    "wheat_stocks",
                    f"{country}_{year}",
                    "UPDATE",
                    old_values,
                    new_values,
                    "streamlit_user",
                )

            conn.commit()
            return True

        except Exception as e:
            conn.rollback()
            print(f"Error updating stocks value: {e}")
            return False
        finally:
            conn.close()

    # Import Data Methods
    def get_all_import_data(self) -> Dict:
        """Get all import data in the format expected by the Streamlit app"""

        conn = self.get_connection()
        cursor = conn.cursor()

        try:
            cursor.execute(
                """
                SELECT country, year, import_value, percentage_world, change_value, status
                FROM wheat_imports
                ORDER BY 
                    CASE country
                        WHEN 'TOTAL MAJOR IMPORTERS' THEN 999
                        ELSE 1
                    END,
                    country, year
            """
            )

            rows = cursor.fetchall()

            # Convert to the nested dictionary format
            data = {}
            for country, year, import_val, percentage, change, status in rows:
                if country not in data:
                    data[country] = {}

                data[country][year] = import_val
                if percentage is not None:
                    data[country][f"{year}_pct"] = percentage
                if change is not None:
                    data[country][f"{year}_change"] = change

            return data

        finally:
            conn.close()

    def update_import_value(
        self, country: str, year: str, import_val: float, change: float = None
    ):
        """Update import value for a specific country and year"""

        conn = self.get_connection()
        cursor = conn.cursor()

        try:
            # Get old values for audit
            cursor.execute(
                """
                SELECT import_value, change_value FROM wheat_imports 
                WHERE country = ? AND year = ?
            """,
                (country, year),
            )

            old_data = cursor.fetchone()
            old_values = (
                {"import": old_data[0], "change": old_data[1]} if old_data else None
            )

            # Update the record
            cursor.execute(
                """
                UPDATE wheat_imports 
                SET import_value = ?, change_value = ?, updated_at = ?
                WHERE country = ? AND year = ?
            """,
                (import_val, change, datetime.now().isoformat(), country, year),
            )

            # Log the change
            if old_values:
                new_values = {"import": import_val, "change": change}
                self._log_audit(
                    cursor,
                    "wheat_imports",
                    f"{country}_{year}",
                    "UPDATE",
                    old_values,
                    new_values,
                    "streamlit_user",
                )

            conn.commit()
            return True

        except Exception as e:
            conn.rollback()
            print(f"Error updating import value: {e}")
            return False
        finally:
            conn.close()

    # Export Data Methods
    def get_all_export_data(self) -> Dict:
        """Get all export data in the format expected by the Streamlit app"""

        conn = self.get_connection()
        cursor = conn.cursor()

        try:
            cursor.execute(
                """
                SELECT country, year, export_value, percentage_world, change_value, status
                FROM wheat_exports
                ORDER BY 
                    CASE country
                        WHEN 'TOTAL MAJOR EXPORTERS' THEN 999
                        ELSE 1
                    END,
                    country, year
            """
            )

            rows = cursor.fetchall()

            # Convert to the nested dictionary format
            data = {}
            for country, year, export, percentage, change, status in rows:
                if country not in data:
                    data[country] = {}

                data[country][year] = export
                if percentage is not None:
                    data[country][f"{year}_pct"] = percentage
                if change is not None:
                    data[country][f"{year}_change"] = change

            return data

        finally:
            conn.close()

    def update_export_value(
        self, country: str, year: str, export: float, change: float = None
    ):
        """Update export value for a specific country and year"""

        conn = self.get_connection()
        cursor = conn.cursor()

        try:
            # Get old values for audit
            cursor.execute(
                """
                SELECT export_value, change_value FROM wheat_exports 
                WHERE country = ? AND year = ?
            """,
                (country, year),
            )

            old_data = cursor.fetchone()
            old_values = (
                {"export": old_data[0], "change": old_data[1]} if old_data else None
            )

            # Update the record
            cursor.execute(
                """
                UPDATE wheat_exports 
                SET export_value = ?, change_value = ?, updated_at = ?
                WHERE country = ? AND year = ?
            """,
                (export, change, datetime.now().isoformat(), country, year),
            )

            # Log the change
            if old_values:
                new_values = {"export": export, "change": change}
                self._log_audit(
                    cursor,
                    "wheat_exports",
                    f"{country}_{year}",
                    "UPDATE",
                    old_values,
                    new_values,
                    "streamlit_user",
                )

            conn.commit()
            return True

        except Exception as e:
            conn.rollback()
            print(f"Error updating export value: {e}")
            return False
        finally:
            conn.close()

    # Common Methods
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
            cursor.execute(
                """
                INSERT OR REPLACE INTO metadata (key, value, updated_at)
                VALUES (?, ?, ?)
            """,
                (key, value, datetime.now().isoformat()),
            )

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
            df = pd.read_sql_query(
                """
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
            """,
                conn,
            )

            return df
        finally:
            conn.close()

    def get_export_dataframe(self) -> pd.DataFrame:
        """Get export data as a pandas DataFrame"""

        conn = self.get_connection()

        try:
            df = pd.read_sql_query(
                """
                SELECT country, year, export_value, percentage_world, change_value, status
                FROM wheat_exports
                ORDER BY 
                    CASE country
                        WHEN 'TOTAL MAJOR EXPORTERS' THEN 999
                        ELSE 1
                    END,
                    country, year
            """,
                conn,
            )

            return df
        finally:
            conn.close()

    def get_yield_dataframe(self) -> pd.DataFrame:
        """Get yield data as a pandas DataFrame"""

        conn = self.get_connection()

        try:
            df = pd.read_sql_query(
                """
                SELECT country, year, yield_value, change_value, change_percentage, 
                       yield_category, weather_impact, status
                FROM wheat_yield
                ORDER BY 
                    CASE country
                        WHEN 'WORLD' THEN 1
                        ELSE 2
                    END,
                    yield_value DESC
            """,
                conn,
            )

            return df
        finally:
            conn.close()

    def get_acreage_dataframe(self) -> pd.DataFrame:
        """Get acreage data as a pandas DataFrame"""

        conn = self.get_connection()

        try:
            df = pd.read_sql_query(
                """
                SELECT country, year, acreage_value, percentage_world, change_value, yield_per_hectare, status
                FROM wheat_acreage
                ORDER BY 
                    CASE country
                        WHEN 'WORLD' THEN 1
                        ELSE 2
                    END,
                    acreage_value DESC
            """,
                conn,
            )

            return df
        finally:
            conn.close()

    def get_su_ratio_dataframe(self) -> pd.DataFrame:
        """Get S/U ratio data as a pandas DataFrame"""

        conn = self.get_connection()

        try:
            df = pd.read_sql_query(
                """
                SELECT country, year, su_ratio, change_value, category, status
                FROM wheat_su_ratio
                ORDER BY 
                    CASE country
                        WHEN 'WORLD' THEN 1
                        ELSE 2
                    END,
                    su_ratio DESC
            """,
                conn,
            )

            return df
        finally:
            conn.close()

    def get_stocks_dataframe(self) -> pd.DataFrame:
        """Get stocks data as a pandas DataFrame"""

        conn = self.get_connection()

        try:
            df = pd.read_sql_query(
                """
                SELECT country, year, stock_value, percentage_world, change_value, stock_to_use_ratio, status
                FROM wheat_stocks
                ORDER BY 
                    CASE country
                        WHEN 'WORLD' THEN 1
                        ELSE 2
                    END,
                    stock_value DESC
            """,
                conn,
            )

            return df
        finally:
            conn.close()

    def get_import_dataframe(self) -> pd.DataFrame:
        """Get import data as a pandas DataFrame"""

        conn = self.get_connection()

        try:
            df = pd.read_sql_query(
                """
                SELECT country, year, import_value, percentage_world, change_value, status
                FROM wheat_imports
                ORDER BY 
                    CASE country
                        WHEN 'TOTAL MAJOR IMPORTERS' THEN 999
                        ELSE 1
                    END,
                    country, year
            """,
                conn,
            )

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

            # Get all export data
            cursor.execute("SELECT * FROM wheat_exports")
            export_data = cursor.fetchall()

            # Get all import data
            cursor.execute("SELECT * FROM wheat_imports")
            import_data = cursor.fetchall()

            # Get all stocks data
            cursor.execute("SELECT * FROM wheat_stocks")
            stocks_data = cursor.fetchall()

            # Get all S/U ratio data
            cursor.execute("SELECT * FROM wheat_su_ratio")
            su_ratio_data = cursor.fetchall()

            # Get all acreage data
            cursor.execute("SELECT * FROM wheat_acreage")
            acreage_data = cursor.fetchall()

            # Get all yield data
            cursor.execute("SELECT * FROM wheat_yield")
            yield_data = cursor.fetchall()

            # Get all metadata
            cursor.execute("SELECT * FROM metadata")
            metadata_data = cursor.fetchall()

            backup = {
                "backup_timestamp": datetime.now().isoformat(),
                "production_data": production_data,
                "export_data": export_data,
                "import_data": import_data,
                "stocks_data": stocks_data,
                "su_ratio_data": su_ratio_data,
                "acreage_data": acreage_data,
                "yield_data": yield_data,
                "metadata_data": metadata_data,
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
            cursor.execute("DELETE FROM wheat_exports")
            cursor.execute("DELETE FROM metadata")

            # Restore production data
            if "production_data" in backup_data:
                for row in backup_data["production_data"]:
                    cursor.execute(
                        """
                        INSERT INTO wheat_production 
                        (id, country, year, production_value, percentage_world, change_value, status, created_at, updated_at)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                        row,
                    )

            # Restore export data
            if "export_data" in backup_data:
                for row in backup_data["export_data"]:
                    cursor.execute(
                        """
                        INSERT INTO wheat_exports 
                        (id, country, year, export_value, percentage_world, change_value, status, created_at, updated_at)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                        row,
                    )

            # Restore import data
            if "import_data" in backup_data:
                for row in backup_data["import_data"]:
                    cursor.execute(
                        """
                        INSERT INTO wheat_imports 
                        (id, country, year, import_value, percentage_world, change_value, status, created_at, updated_at)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                        row,
                    )

            # Restore stocks data
            if "stocks_data" in backup_data:
                for row in backup_data["stocks_data"]:
                    cursor.execute(
                        """
                        INSERT INTO wheat_stocks 
                        (id, country, year, stock_value, percentage_world, change_value, stock_to_use_ratio, status, created_at, updated_at)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                        row,
                    )

            # Restore S/U ratio data
            if "su_ratio_data" in backup_data:
                for row in backup_data["su_ratio_data"]:
                    cursor.execute(
                        """
                        INSERT INTO wheat_su_ratio 
                        (id, country, year, su_ratio, change_value, category, status, created_at, updated_at)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                        row,
                    )

            # Restore acreage data
            if "acreage_data" in backup_data:
                for row in backup_data["acreage_data"]:
                    cursor.execute(
                        """
                        INSERT INTO wheat_acreage 
                        (id, country, year, acreage_value, percentage_world, change_value, yield_per_hectare, status, created_at, updated_at)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                        row,
                    )

            # Restore yield data
            if "yield_data" in backup_data:
                for row in backup_data["yield_data"]:
                    cursor.execute(
                        """
                        INSERT INTO wheat_yield 
                        (id, country, year, yield_value, change_value, change_percentage, 
                         yield_category, weather_impact, status, created_at, updated_at)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                        row,
                    )

            # Restore metadata
            if "metadata_data" in backup_data:
                for row in backup_data["metadata_data"]:
                    cursor.execute(
                        """
                        INSERT INTO metadata (id, key, value, created_at, updated_at)
                        VALUES (?, ?, ?, ?, ?)
                    """,
                        row,
                    )

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
            cursor.execute(
                """
                SELECT table_name, record_id, action, old_values, new_values, changed_by, changed_at
                FROM audit_log
                ORDER BY changed_at DESC
                LIMIT ?
            """,
                (limit,),
            )

            return cursor.fetchall()
        finally:
            conn.close()

    def _log_audit(
        self,
        cursor,
        table_name: str,
        record_id: str,
        action: str,
        old_values: Dict,
        new_values: Dict,
        changed_by: str,
    ):
        """Log an audit entry"""

        cursor.execute(
            """
            INSERT INTO audit_log (table_name, record_id, action, old_values, new_values, changed_by)
            VALUES (?, ?, ?, ?, ?, ?)
        """,
            (
                table_name,
                record_id,
                action,
                json.dumps(old_values) if old_values else None,
                json.dumps(new_values) if new_values else None,
                changed_by,
            ),
        )

    def get_countries_list(self, table: str = "wheat_production") -> List[str]:
        """Get list of all countries in the specified table"""

        conn = self.get_connection()
        cursor = conn.cursor()

        try:
            cursor.execute(f"SELECT DISTINCT country FROM {table} ORDER BY country")
            return [row[0] for row in cursor.fetchall()]
        finally:
            conn.close()

    def get_years_list(self, table: str = "wheat_production") -> List[str]:
        """Get list of all years in the specified table"""

        conn = self.get_connection()
        cursor = conn.cursor()

        try:
            cursor.execute(f"SELECT DISTINCT year FROM {table} ORDER BY year")
            return [row[0] for row in cursor.fetchall()]
        finally:
            conn.close()

    def filter_countries_data(self, data: Dict, allowed_countries: List[str]) -> Dict:
        """Filter data to include only allowed countries"""
        return {
            country: country_data
            for country, country_data in data.items()
            if country in allowed_countries
        }

    def get_years_for_display(self) -> List[str]:
        """Get the years that should be displayed based on metadata"""
        metadata = self.get_metadata()
        display_years = metadata.get(
            "display_years", "2021/2022,2022/2023,2023/2024,2024/2025"
        )
        return display_years.split(",")

    def update_year_statuses(self, year_status_map: Dict[str, str]):
        """Update the status for multiple years at once"""
        conn = self.get_connection()
        cursor = conn.cursor()

        try:
            for year, status in year_status_map.items():
                cursor.execute(
                    """
                    UPDATE wheat_production 
                    SET status = ?, updated_at = ?
                    WHERE year = ?
                """,
                    (status, datetime.now().isoformat(), year),
                )

                # Also update other tables
                for table in [
                    "wheat_exports",
                    "wheat_imports",
                    "wheat_stocks",
                    "wheat_su_ratio",
                    "wheat_acreage",
                    "wheat_yield",
                ]:
                    cursor.execute(
                        f"""
                        UPDATE {table} 
                        SET status = ?, updated_at = ?
                        WHERE year = ?
                    """,
                        (status, datetime.now().isoformat(), year),
                    )

            conn.commit()
            return True
        except Exception as e:
            conn.rollback()
            print(f"Error updating year statuses: {e}")
            return False
        finally:
            conn.close()

    def copy_year_data(
        self,
        source_year: str,
        target_year: str,
        countries: List[str],
        tables: List[str] = None,
    ):
        """Copy data from one year to another for specified countries"""
        if tables is None:
            tables = [
                "wheat_production",
                "wheat_exports",
                "wheat_imports",
                "wheat_stocks",
                "wheat_su_ratio",
                "wheat_acreage",
                "wheat_yield",
            ]

        conn = self.get_connection()
        cursor = conn.cursor()

        try:
            for table in tables:
                # Check which columns exist in the table
                cursor.execute(f"PRAGMA table_info({table})")
                columns = [col[1] for col in cursor.fetchall()]

                # Build appropriate INSERT statement based on table
                if table == "wheat_production":
                    cursor.execute(
                        f"""
                        INSERT OR IGNORE INTO {table} 
                        (country, year, production_value, percentage_world, 
                        change_value, status, created_at, updated_at)
                        SELECT country, ?, production_value, percentage_world, 
                            0, 'projection', ?, ?
                        FROM {table}
                        WHERE year = ? AND country IN ({','.join(['?'] * len(countries))})
                    """,
                        (
                            target_year,
                            datetime.now().isoformat(),
                            datetime.now().isoformat(),
                            source_year,
                            *countries,
                        ),
                    )

                # Similar for other tables...

            conn.commit()
            return True
        except Exception as e:
            conn.rollback()
            print(f"Error copying year data: {e}")
            return False
        finally:
            conn.close()

    def get_filtered_production_data(self, allowed_countries: List[str]) -> Dict:
        """Get production data filtered by allowed countries"""
        all_data = self.get_all_production_data()
        return self.filter_countries_data(all_data, allowed_countries)


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
    cursor.execute(
        """
        SELECT name FROM sqlite_master 
        WHERE type='table' AND name='wheat_production'
    """
    )

    if not cursor.fetchone():
        conn.close()
        print("Database not found. Please run the setup script first:")
        print("python database_setup.py")
        return False

    conn.close()
    return True
