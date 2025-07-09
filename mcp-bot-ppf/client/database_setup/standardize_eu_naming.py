#!/usr/bin/env python3
"""
Script to standardize European Union naming across all wheat database tables.
This will update all variations to simply "European Union".
"""

import sqlite3
import sys
import os
from datetime import datetime


def standardize_european_union_naming(database_path: str = "wheat_production.db"):
    """
    Standardize all European Union naming variations to 'European Union'

    Args:
        database_path: Path to the SQLite database
    """

    if not os.path.exists(database_path):
        print(f"❌ Database not found: {database_path}")
        return False

    conn = sqlite3.connect(database_path)
    cursor = conn.cursor()

    # Define all possible variations of European Union naming
    eu_variations = [
        "European Union (FR, DE)",
        "European Union 27 (FR, DE)",
        "European Union (27)",
        "European Union 27",
        "EU",
        "EU-27",
        "EU27",
    ]

    # Tables to update
    tables = [
        "wheat_production",
        "wheat_exports",
        "wheat_imports",
        "wheat_stocks",
        "wheat_su_ratio",
        "wheat_acreage",
        "wheat_yield",
    ]

    print("🔧 Starting European Union naming standardization...")
    print("-" * 50)

    try:
        total_updated = 0

        for table in tables:
            # Check if table exists
            cursor.execute(
                f"""
                SELECT name FROM sqlite_master 
                WHERE type='table' AND name='{table}'
            """
            )

            if not cursor.fetchone():
                print(f"⚠️  Table '{table}' not found, skipping...")
                continue

            # First, check what variations exist in this table
            cursor.execute(
                f"""
                SELECT DISTINCT country 
                FROM {table} 
                WHERE country LIKE 'European Union%' 
                   OR country LIKE 'EU%'
                ORDER BY country
            """
            )

            existing_variations = [row[0] for row in cursor.fetchall()]

            if existing_variations:
                print(f"\n📊 Table: {table}")
                print(f"   Found variations: {', '.join(existing_variations)}")

                # Update all variations to 'European Union'
                for variation in existing_variations:
                    if variation != "European Union":
                        cursor.execute(
                            f"""
                            UPDATE {table} 
                            SET country = 'European Union',
                                updated_at = ?
                            WHERE country = ?
                        """,
                            (datetime.now().isoformat(), variation),
                        )

                        count = cursor.rowcount
                        if count > 0:
                            print(
                                f"   ✅ Updated {count} records: '{variation}' → 'European Union'"
                            )
                            total_updated += count
            else:
                print(f"\n📊 Table: {table}")
                print(f"   No European Union entries found")

        # Update metadata
        cursor.execute(
            """
            INSERT OR REPLACE INTO metadata (key, value, updated_at)
            VALUES ('eu_naming_standardized', ?, ?)
        """,
            ("true", datetime.now().isoformat()),
        )

        conn.commit()

        print("\n" + "=" * 50)
        print(f"✅ Standardization complete!")
        print(f"📊 Total records updated: {total_updated}")

        # Verify the results
        print("\n🔍 Verification:")
        for table in tables:
            cursor.execute(
                f"""
                SELECT COUNT(*) 
                FROM {table} 
                WHERE country = 'European Union'
            """
            )
            count = cursor.fetchone()[0]
            if count > 0:
                print(f"   {table}: {count} European Union records")

        return True

    except Exception as e:
        conn.rollback()
        print(f"\n❌ Error during standardization: {e}")
        return False

    finally:
        conn.close()


def check_database_consistency(database_path: str = "wheat_production.db"):
    """
    Check database consistency after standardization
    """

    conn = sqlite3.connect(database_path)
    cursor = conn.cursor()

    print("\n🔍 Database Consistency Check:")
    print("-" * 50)

    # Define allowed countries
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

    tables = [
        "wheat_production",
        "wheat_exports",
        "wheat_imports",
        "wheat_stocks",
        "wheat_su_ratio",
        "wheat_acreage",
        "wheat_yield",
    ]

    issues_found = False

    for table in tables:
        # Check if table exists
        cursor.execute(
            f"""
            SELECT name FROM sqlite_master 
            WHERE type='table' AND name='{table}'
        """
        )

        if not cursor.fetchone():
            continue

        # Get all unique countries
        cursor.execute(
            f"""
            SELECT DISTINCT country, COUNT(*) as count
            FROM {table}
            GROUP BY country
            ORDER BY country
        """
        )

        countries = cursor.fetchall()

        # Check for countries not in allowed list
        disallowed = []
        for country, count in countries:
            if country not in allowed_countries:
                disallowed.append(f"{country} ({count} records)")
                issues_found = True

        if disallowed:
            print(f"\n⚠️  {table}: Found disallowed countries:")
            for item in disallowed:
                print(f"     - {item}")
        else:
            print(f"\n✅ {table}: All countries are in the allowed list")

        # Check for any remaining EU variations
        cursor.execute(
            f"""
            SELECT DISTINCT country 
            FROM {table} 
            WHERE (country LIKE 'European Union%' AND country != 'European Union')
               OR country LIKE 'EU%'
        """
        )

        eu_variations = [row[0] for row in cursor.fetchall()]
        if eu_variations:
            print(f"   ⚠️  Still has EU variations: {', '.join(eu_variations)}")
            issues_found = True

    conn.close()

    if not issues_found:
        print("\n✅ Database consistency check passed!")
    else:
        print("\n⚠️  Some consistency issues found. Consider running cleanup.")

    return not issues_found


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(
        description="Standardize European Union naming in wheat database"
    )
    parser.add_argument(
        "--database",
        default="wheat_production.db",
        help="Path to the database file (default: wheat_production.db)",
    )
    parser.add_argument(
        "--check-only",
        action="store_true",
        help="Only check consistency without making changes",
    )

    args = parser.parse_args()

    if args.check_only:
        print("🔍 Running consistency check only...")
        check_database_consistency(args.database)
    else:
        # Run standardization
        success = standardize_european_union_naming(args.database)

        if success:
            # Run consistency check
            check_database_consistency(args.database)
        else:
            sys.exit(1)
