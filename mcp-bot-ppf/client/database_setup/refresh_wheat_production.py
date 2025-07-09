import pandas as pd
import sqlite3
from datetime import datetime
import os
import sys
import numpy as np

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from wheat_helpers.database_helper import WheatProductionDB


def parse_value_with_change(cell_value):
    """Parse a cell that might contain value and change in parentheses"""
    if pd.isna(cell_value):
        return None, None

    # Convert to string and clean
    cell_str = str(cell_value).strip()

    # Check if there's a parenthesis (indicating change value)
    if "(" in cell_str and ")" in cell_str:
        # Split by first parenthesis
        parts = cell_str.split("(")
        value = float(parts[0].strip())
        change = float(parts[1].replace(")", "").strip())
        return value, change
    else:
        # Just a simple value
        try:
            return float(cell_str), None
        except:
            return None, None


def refresh_wheat_production_data(excel_path: str, dry_run: bool = True):
    """
    Refresh wheat production data from Excel file

    Args:
        excel_path: Path to the Excel file
        dry_run: If True, shows what would be updated without making changes
    """
    print(f"{'[DRY RUN] ' if dry_run else ''}Starting wheat production data refresh...")

    # Read Excel file
    try:
        # Read the specific sheet
        df = pd.read_excel(excel_path, sheet_name="Supply & Demand", header=None)
        print(f"✅ Successfully read Excel file: {excel_path}")
    except Exception as e:
        print(f"❌ Error reading Excel file: {e}")
        return

    # Initialize database connection
    db = WheatProductionDB()

    # Define the countries we want to keep
    countries_to_keep = [
        "WORLD",
        "China",
        "European Union",
        "India",
        "Russia",
        "United States",
        "Australia",
        "Canada",
    ]

    # Find the row with "Global Wheat Production"
    production_start_row = None
    for idx, row in df.iterrows():
        if any(
            "Global Wheat Production" in str(cell) for cell in row if pd.notna(cell)
        ):
            production_start_row = idx
            break

    if production_start_row is None:
        print("❌ Could not find 'Global Wheat Production' section in the Excel file")
        return

    print(f"✅ Found 'Global Wheat Production' at row {production_start_row}")

    # Find the header row (contains years)
    header_row = None
    for idx in range(production_start_row + 1, min(production_start_row + 10, len(df))):
        row = df.iloc[idx]
        # Look for row containing year patterns like "2021/2022"
        year_pattern_count = sum(
            1
            for cell in row
            if pd.notna(cell) and "/" in str(cell) and len(str(cell).split("/")) == 2
        )
        if year_pattern_count >= 4:  # Expect at least 4 years
            header_row = idx
            break

    if header_row is None:
        print("❌ Could not find header row with years")
        return

    # Extract years from header
    years_row = df.iloc[header_row]
    year_columns = {}

    for col_idx, cell in enumerate(years_row):
        if pd.notna(cell) and "/" in str(cell):
            year = str(cell).strip()
            if len(year.split("/")) == 2:
                year_columns[col_idx] = year

    print(f"✅ Found years: {list(year_columns.values())}")

    # Process data
    updates_count = 0
    errors_count = 0

    conn = sqlite3.connect("wheat_production.db")
    cursor = conn.cursor()

    try:
        # First, update any existing "European Union (FR, DE)" to "European Union"
        if not dry_run:
            cursor.execute(
                """
                UPDATE wheat_production 
                SET country = 'European Union'
                WHERE country = 'European Union (FR, DE)'
            """
            )
            print("✅ Updated European Union naming in database")

        # Process each country row
        data_start_row = header_row + 1

        for idx in range(
            data_start_row, min(data_start_row + 20, len(df))
        ):  # Process up to 20 rows
            row = df.iloc[idx]

            # Get country name (usually in first column)
            country = None
            for col in range(3):  # Check first 3 columns for country name
                if pd.notna(row.iloc[col]) and isinstance(row.iloc[col], str):
                    country = row.iloc[col].strip()
                    break

            if not country or country not in countries_to_keep:
                continue

            print(f"\nProcessing {country}:")

            # Process each year column
            for col_idx, year in year_columns.items():
                cell_value = row.iloc[col_idx] if col_idx < len(row) else None

                if pd.isna(cell_value):
                    continue

                try:
                    # Parse value and change
                    production_value, change_value = parse_value_with_change(cell_value)

                    if production_value is None:
                        continue

                    # Determine status based on year
                    if year in ["2021/2022", "2022/2023", "2023/2024"]:
                        status = "act"
                    elif year == "2024/2025":
                        status = "estimate"
                    elif year == "2025/2026":
                        status = "projection"
                    else:
                        status = "act"

                    # Calculate percentage of world if this is not WORLD
                    percentage_world = None
                    if country != "WORLD":
                        # Find WORLD row
                        for world_idx in range(
                            data_start_row, min(data_start_row + 20, len(df))
                        ):
                            world_row = df.iloc[world_idx]
                            world_country = None
                            for col in range(3):
                                if pd.notna(world_row.iloc[col]) and isinstance(
                                    world_row.iloc[col], str
                                ):
                                    world_country = world_row.iloc[col].strip()
                                    break

                            if world_country == "WORLD":
                                world_cell = (
                                    world_row.iloc[col_idx]
                                    if col_idx < len(world_row)
                                    else None
                                )
                                if pd.notna(world_cell):
                                    world_value, _ = parse_value_with_change(world_cell)
                                    if world_value and world_value > 0:
                                        percentage_world = (
                                            production_value / world_value
                                        ) * 100
                                break

                    if dry_run:
                        print(
                            f"  Would update {year}: {production_value:.1f} Mt (status: {status}, change: {change_value:.1f if change_value else 'N/A'})"
                        )
                    else:
                        # Check if record exists
                        cursor.execute(
                            """
                            SELECT id FROM wheat_production 
                            WHERE country = ? AND year = ?
                        """,
                            (country, year),
                        )

                        exists = cursor.fetchone()

                        if exists:
                            # Update existing record
                            cursor.execute(
                                """
                                UPDATE wheat_production 
                                SET production_value = ?, percentage_world = ?, 
                                    change_value = ?, status = ?, updated_at = ?
                                WHERE country = ? AND year = ?
                            """,
                                (
                                    production_value,
                                    percentage_world,
                                    change_value,
                                    status,
                                    datetime.now().isoformat(),
                                    country,
                                    year,
                                ),
                            )
                        else:
                            # Insert new record
                            cursor.execute(
                                """
                                INSERT INTO wheat_production 
                                (country, year, production_value, percentage_world, 
                                 change_value, status, created_at, updated_at)
                                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                            """,
                                (
                                    country,
                                    year,
                                    production_value,
                                    percentage_world,
                                    change_value,
                                    status,
                                    datetime.now().isoformat(),
                                    datetime.now().isoformat(),
                                ),
                            )

                        print(f"  Updated {year}: {production_value:.1f} Mt")
                        updates_count += 1

                except Exception as e:
                    print(f"  ❌ Error processing {year}: {e}")
                    errors_count += 1

        if not dry_run:
            # Update metadata
            cursor.execute(
                """
                UPDATE metadata 
                SET value = ?, updated_at = ?
                WHERE key = 'production_last_updated'
            """,
                (datetime.now().strftime("%d %b'%y"), datetime.now().isoformat()),
            )

            # Update display years and status configuration
            cursor.execute(
                """
                INSERT OR REPLACE INTO metadata (key, value, updated_at)
                VALUES (?, ?, ?)
            """,
                (
                    "display_years",
                    "2022/2023,2023/2024,2024/2025,2025/2026",
                    datetime.now().isoformat(),
                ),
            )

            cursor.execute(
                """
                INSERT OR REPLACE INTO metadata (key, value, updated_at)
                VALUES (?, ?, ?)
            """,
                (
                    "year_status",
                    '{"2022/2023": "act", "2023/2024": "act", "2024/2025": "estimate", "2025/2026": "projection"}',
                    datetime.now().isoformat(),
                ),
            )

            # Clean up any countries not in our list
            placeholders = ",".join(["?"] * len(countries_to_keep))
            cursor.execute(
                f"""
                DELETE FROM wheat_production 
                WHERE country NOT IN ({placeholders})
            """,
                countries_to_keep,
            )

            deleted_count = cursor.rowcount
            if deleted_count > 0:
                print(
                    f"\n🧹 Cleaned up {deleted_count} records from countries not in the allowed list"
                )

            conn.commit()
            print(f"\n✅ Database updated successfully!")

        print(f"\n📊 Summary:")
        print(f"  - Records {'would be' if dry_run else ''} updated: {updates_count}")
        print(f"  - Errors encountered: {errors_count}")

    except Exception as e:
        conn.rollback()
        print(f"\n❌ Database error: {e}")
        import traceback

        traceback.print_exc()
    finally:
        conn.close()


def verify_database_state():
    """Verify the current state of the database"""
    db = WheatProductionDB()
    conn = sqlite3.connect("wheat_production.db")
    cursor = conn.cursor()

    print("\n📊 Current Database State:")
    print("-" * 50)

    # Get unique years
    cursor.execute("SELECT DISTINCT year FROM wheat_production ORDER BY year")
    years = [row[0] for row in cursor.fetchall()]
    print(f"Years in database: {', '.join(years)}")

    # Get countries
    cursor.execute("SELECT DISTINCT country FROM wheat_production ORDER BY country")
    countries = [row[0] for row in cursor.fetchall()]
    print(f"\nCountries in database ({len(countries)} total):")

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

    for country in countries:
        if country in allowed_countries:
            print(f"  ✅ {country}")
        else:
            print(f"  ❌ {country} (not in allowed list)")

    # Show sample data for WORLD
    print("\n🌍 WORLD Production Data:")
    cursor.execute(
        """
        SELECT year, production_value, change_value, status 
        FROM wheat_production 
        WHERE country = 'WORLD' 
        ORDER BY year
    """
    )

    for year, value, change, status in cursor.fetchall():
        change_str = f"({change:+.1f})" if change else ""
        print(f"  {year}: {value:.1f} Mt {change_str} [{status}]")

    # Show metadata
    print("\n📋 Metadata:")
    cursor.execute(
        "SELECT key, value FROM metadata WHERE key IN ('display_years', 'year_status', 'production_last_updated')"
    )
    for key, value in cursor.fetchall():
        print(f"  {key}: {value}")

    conn.close()


def standardize_european_union():
    """Standardize all European Union entries to 'European Union'"""
    conn = sqlite3.connect("wheat_production.db")
    cursor = conn.cursor()

    try:
        # Update all tables
        tables = [
            "wheat_production",
            "wheat_exports",
            "wheat_imports",
            "wheat_stocks",
            "wheat_su_ratio",
            "wheat_acreage",
            "wheat_yield",
        ]

        total_updated = 0
        for table in tables:
            cursor.execute(
                f"""
                UPDATE {table} 
                SET country = 'European Union'
                WHERE country = 'European Union (FR, DE)' 
                   OR country = 'European Union 27 (FR, DE)'
                   OR country LIKE 'European Union%'
            """
            )

            updated = cursor.rowcount
            if updated > 0:
                print(f"✅ Updated {updated} records in {table}")
                total_updated += updated

        conn.commit()
        print(f"\n✅ Total records updated: {total_updated}")

    except Exception as e:
        conn.rollback()
        print(f"❌ Error standardizing European Union: {e}")
    finally:
        conn.close()


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(
        description="Refresh wheat production data from Excel"
    )
    parser.add_argument("excel_path", help="Path to the Excel file")
    parser.add_argument(
        "--execute",
        action="store_true",
        help="Execute the update (without this flag, it runs in dry-run mode)",
    )
    parser.add_argument(
        "--verify", action="store_true", help="Verify database state after update"
    )
    parser.add_argument(
        "--standardize-eu",
        action="store_true",
        help="Standardize European Union naming across all tables",
    )

    args = parser.parse_args()

    # Standardize EU naming if requested
    if args.standardize_eu:
        print("🔧 Standardizing European Union naming...")
        standardize_european_union()
        if args.verify:
            verify_database_state()
        sys.exit(0)

    # Check if Excel file exists
    if not os.path.exists(args.excel_path):
        print(f"❌ Excel file not found: {args.excel_path}")
        sys.exit(1)

    # Check if database exists
    if not os.path.exists("wheat_production.db"):
        print("❌ Database not found. Please run database_setup.py first.")
        sys.exit(1)

    # Run refresh
    refresh_wheat_production_data(args.excel_path, dry_run=not args.execute)

    # Verify if requested
    if args.verify:
        verify_database_state()
