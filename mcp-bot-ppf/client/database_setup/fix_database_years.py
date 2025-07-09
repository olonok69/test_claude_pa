#!/usr/bin/env python3
"""
Script to manually fix the database to ensure proper year rotation
"""

import sqlite3
import json
from datetime import datetime


def fix_database_years():
    """Fix the database to ensure proper years and metadata"""

    conn = sqlite3.connect("wheat_production.db")
    cursor = conn.cursor()

    try:
        print("🔧 Fixing database years and metadata...")

        # 1. Update year statuses
        status_updates = [
            ("2021/2022", "act"),
            ("2022/2023", "act"),
            ("2023/2024", "act"),
            ("2024/2025", "estimate"),
            ("2025/2026", "projection"),
        ]

        for year, status in status_updates:
            cursor.execute(
                """
                UPDATE wheat_production 
                SET status = ?, updated_at = ?
                WHERE year = ?
            """,
                (status, datetime.now().isoformat(), year),
            )
            print(f"✅ Updated {year} to status: {status}")

        # 2. Ensure 2025/2026 exists for all allowed countries
        allowed_countries = [
            "WORLD",
            "China",
            "European Union",
            "India",
            "Russia",
            "United States",
            "Australia",
            "Canada",
        ]

        # Check which countries need 2025/2026 data
        cursor.execute(
            """
            SELECT DISTINCT country FROM wheat_production 
            WHERE year = '2025/2026'
        """
        )
        existing_2025_countries = [row[0] for row in cursor.fetchall()]

        for country in allowed_countries:
            if country not in existing_2025_countries:
                # Get 2024/2025 data to use as base
                cursor.execute(
                    """
                    SELECT production_value, percentage_world 
                    FROM wheat_production 
                    WHERE country = ? AND year = '2024/2025'
                """,
                    (country,),
                )

                result = cursor.fetchone()
                if result:
                    production_value, percentage_world = result
                    cursor.execute(
                        """
                        INSERT INTO wheat_production 
                        (country, year, production_value, percentage_world, change_value, status, created_at, updated_at)
                        VALUES (?, '2025/2026', ?, ?, 0, 'projection', ?, ?)
                    """,
                        (
                            country,
                            production_value,
                            percentage_world,
                            datetime.now().isoformat(),
                            datetime.now().isoformat(),
                        ),
                    )
                    print(f"✅ Created 2025/2026 data for {country}")

        # 3. Update metadata to show correct years
        display_years = ["2022/2023", "2023/2024", "2024/2025", "2025/2026"]
        year_status = {
            "2022/2023": "act",
            "2023/2024": "act",
            "2024/2025": "estimate",
            "2025/2026": "projection",
        }

        # Update display_years
        cursor.execute(
            """
            INSERT OR REPLACE INTO metadata (key, value, created_at, updated_at)
            VALUES ('display_years', ?, ?, ?)
        """,
            (
                ",".join(display_years),
                datetime.now().isoformat(),
                datetime.now().isoformat(),
            ),
        )

        # Update year_status
        cursor.execute(
            """
            INSERT OR REPLACE INTO metadata (key, value, created_at, updated_at)
            VALUES ('year_status', ?, ?, ?)
        """,
            (
                json.dumps(year_status),
                datetime.now().isoformat(),
                datetime.now().isoformat(),
            ),
        )

        print("✅ Updated metadata for display years")

        # 4. Clean up any invalid countries
        cursor.execute(
            """
            DELETE FROM wheat_production 
            WHERE country NOT IN ({})
        """.format(
                ",".join(["?"] * len(allowed_countries))
            ),
            allowed_countries,
        )

        deleted = cursor.rowcount
        if deleted > 0:
            print(f"🧹 Cleaned up {deleted} records from invalid countries")

        conn.commit()
        print("\n✅ Database fixed successfully!")

        # Verify the fix
        print("\n🔍 Verification:")

        # Check years
        cursor.execute("SELECT DISTINCT year FROM wheat_production ORDER BY year")
        years = [row[0] for row in cursor.fetchall()]
        print(f"Years in database: {', '.join(years)}")

        # Check metadata
        cursor.execute("SELECT value FROM metadata WHERE key = 'display_years'")
        result = cursor.fetchone()
        if result:
            print(f"Display years: {result[0]}")

        cursor.execute("SELECT value FROM metadata WHERE key = 'year_status'")
        result = cursor.fetchone()
        if result:
            print(f"Year status: {result[0]}")

        # Show sample WORLD data
        print("\n🌍 WORLD Production Data:")
        cursor.execute(
            """
            SELECT year, production_value, change_value, status 
            FROM wheat_production 
            WHERE country = 'WORLD' 
            ORDER BY year DESC
            LIMIT 5
        """
        )

        for year, value, change, status in cursor.fetchall():
            change_str = f"({change:+.1f})" if change else ""
            print(f"  {year}: {value:.1f} Mt {change_str} [{status}]")

    except Exception as e:
        conn.rollback()
        print(f"❌ Error: {e}")
        import traceback

        traceback.print_exc()
    finally:
        conn.close()


if __name__ == "__main__":
    fix_database_years()
