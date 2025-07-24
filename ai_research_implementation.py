#!/usr/bin/env python3
"""
Comprehensive AI Research Implementation Script
Adds Perplexity AI Research functionality to all wheat and corn pages (1-8, 10-17)
"""

import os
import re
import shutil
from typing import Dict, List, Tuple
from datetime import datetime

# Page configuration mapping
PAGE_CONFIGS = {
    # Wheat pages (1-8)
    "1_wheat_production.py": {
        "commodity": "wheat",
        "data_type": "production",
        "session_var": "st.session_state.wheat_data",
        "update_method": "update_production_value",
        "db_helper": "get_database()",
        "allowed_countries": [
            "WORLD",
            "China",
            "European Union",
            "India",
            "Russia",
            "United States",
            "Australia",
            "Canada",
        ],
        "unit": "Million Metric Tons",
        "title": "Wheat Production",
    },
    "2_wheat_exports.py": {
        "commodity": "wheat",
        "data_type": "exports",
        "session_var": "st.session_state.wheat_exports_data",
        "update_method": "update_export_value",
        "db_helper": "get_database()",
        "allowed_countries": [
            "WORLD",
            "China",
            "European Union",
            "Russia",
            "United States",
            "Australia",
            "Canada",
            "India",
        ],
        "unit": "Million Metric Tons",
        "title": "Wheat Exports",
    },
    "3_wheat_imports.py": {
        "commodity": "wheat",
        "data_type": "imports",
        "session_var": "st.session_state.wheat_imports_data",
        "update_method": "update_import_value",
        "db_helper": "get_database()",
        "allowed_countries": [
            "TOTAL MAJOR IMPORTERS",
            "China",
            "European Union",
            "India",
            "Russia",
            "United States",
            "Australia",
            "Canada",
        ],
        "unit": "Million Metric Tons",
        "title": "Wheat Imports",
    },
    "4_wheat_stocks.py": {
        "commodity": "wheat",
        "data_type": "stocks",
        "session_var": "st.session_state.wheat_stocks_data",
        "update_method": "update_stock_value",
        "db_helper": "get_database()",
        "allowed_countries": [
            "WORLD",
            "China",
            "European Union",
            "India",
            "Russia",
            "United States",
            "Australia",
            "Canada",
        ],
        "unit": "Million Metric Tons",
        "title": "Wheat Ending Stocks",
    },
    "5_stock_to_use_ratio.py": {
        "commodity": "wheat",
        "data_type": "su_ratio",
        "session_var": "st.session_state.wheat_su_ratio_data",
        "update_method": "update_su_ratio_value",
        "db_helper": "get_database()",
        "allowed_countries": [
            "WORLD",
            "China",
            "European Union",
            "India",
            "Russia",
            "United States",
            "Australia",
            "Canada",
        ],
        "unit": "%",
        "title": "Wheat Stock-to-Use Ratio",
    },
    "6_wheat_acreage.py": {
        "commodity": "wheat",
        "data_type": "acreage",
        "session_var": "st.session_state.wheat_acreage_data",
        "update_method": "update_acreage_value",
        "db_helper": "get_database()",
        "allowed_countries": [
            "WORLD",
            "China",
            "European Union",
            "India",
            "Russia",
            "United States",
            "Australia",
            "Canada",
        ],
        "unit": "Million Hectares",
        "title": "Wheat Acreage",
    },
    "7_wheat_yield.py": {
        "commodity": "wheat",
        "data_type": "yield",
        "session_var": "st.session_state.wheat_yield_data",
        "update_method": "update_yield_value",
        "db_helper": "get_database()",
        "allowed_countries": [
            "WORLD",
            "China",
            "European Union",
            "India",
            "Russia",
            "United States",
            "Australia",
            "Canada",
        ],
        "unit": "tonnes per hectare",
        "title": "Wheat Yield",
    },
    "8_wheat_world_demand.py": {
        "commodity": "wheat",
        "data_type": "world_demand",
        "session_var": "st.session_state.demand_data",
        "update_method": "update_demand_value",
        "db_helper": "get_database()",
        "allowed_countries": [
            "Food",
            "Feed",
            "Industrial",
            "Seed",
            "Other",
            "Total Consumption",
        ],
        "unit": "Million Metric Tons",
        "title": "Wheat World Demand",
    },
    # Corn pages (10-17)
    "10_corn_production.py": {
        "commodity": "corn",
        "data_type": "production",
        "session_var": "st.session_state.corn_data",
        "update_method": "update_corn_production_value",
        "db_helper": "get_database()",
        "allowed_countries": [
            "WORLD",
            "United States",
            "China",
            "Brazil",
            "European Union",
            "Argentina",
            "Ukraine",
            "India",
        ],
        "unit": "Million Metric Tons",
        "title": "Corn Production",
    },
    "11_corn_exports.py": {
        "commodity": "corn",
        "data_type": "exports",
        "session_var": "st.session_state.corn_exports_data",
        "update_method": "update_corn_export_value",
        "db_helper": "get_database()",
        "allowed_countries": [
            "WORLD",
            "United States",
            "China",
            "Brazil",
            "European Union",
            "Argentina",
            "Ukraine",
            "India",
        ],
        "unit": "Million Metric Tons",
        "title": "Corn Exports",
    },
    "12_corn_imports.py": {
        "commodity": "corn",
        "data_type": "imports",
        "session_var": "st.session_state.corn_imports_data",
        "update_method": "update_corn_import_value",
        "db_helper": "get_database()",
        "allowed_countries": [
            "TOTAL MAJOR IMPORTERS",
            "United States",
            "China",
            "Brazil",
            "European Union",
            "Argentina",
            "Ukraine",
            "India",
        ],
        "unit": "Million Metric Tons",
        "title": "Corn Imports",
    },
    "13_corn_stocks.py": {
        "commodity": "corn",
        "data_type": "stocks",
        "session_var": "st.session_state.corn_stocks_data",
        "update_method": "update_corn_stock_value",
        "db_helper": "get_database()",
        "allowed_countries": [
            "WORLD",
            "United States",
            "China",
            "Brazil",
            "European Union",
            "Argentina",
            "Ukraine",
            "India",
        ],
        "unit": "Million Metric Tons",
        "title": "Corn Ending Stocks",
    },
    "14_corn_stock_to_use_ratio.py": {
        "commodity": "corn",
        "data_type": "su_ratio",
        "session_var": "st.session_state.corn_su_ratio_data",
        "update_method": "update_corn_su_ratio_value",
        "db_helper": "get_database()",
        "allowed_countries": [
            "WORLD",
            "United States",
            "China",
            "Brazil",
            "European Union",
            "Argentina",
            "Ukraine",
            "India",
        ],
        "unit": "%",
        "title": "Corn Stock-to-Use Ratio",
    },
    "15_corn_acreage.py": {
        "commodity": "corn",
        "data_type": "acreage",
        "session_var": "st.session_state.corn_acreage_data",
        "update_method": "update_corn_acreage_value",
        "db_helper": "get_database()",
        "allowed_countries": [
            "WORLD",
            "United States",
            "China",
            "Brazil",
            "European Union",
            "Argentina",
            "Ukraine",
            "India",
        ],
        "unit": "Million Hectares",
        "title": "Corn Acreage",
    },
    "16_corn_yield.py": {
        "commodity": "corn",
        "data_type": "yield",
        "session_var": "st.session_state.corn_yield_data",
        "update_method": "update_corn_yield_value",
        "db_helper": "get_database()",
        "allowed_countries": [
            "WORLD",
            "United States",
            "China",
            "Brazil",
            "European Union",
            "Argentina",
            "Ukraine",
            "India",
        ],
        "unit": "tonnes per hectare",
        "title": "Corn Yield",
    },
    "17_corn_world_demand.py": {
        "commodity": "corn",
        "data_type": "world_demand",
        "session_var": "st.session_state.corn_demand_data",
        "update_method": "update_corn_demand_value",
        "db_helper": "get_database()",
        "allowed_countries": [
            "Food",
            "Feed",
            "Industrial",
            "Seed",
            "Other",
            "Total Consumption",
        ],
        "unit": "Million Metric Tons",
        "title": "Corn World Demand",
    },
}


class AIResearchImplementer:
    """Implements AI Research functionality across all agricultural pages"""

    def __init__(self, pages_dir: str = "client/pages"):
        self.pages_dir = pages_dir
        self.backup_dir = f"backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

    def create_backup(self):
        """Create backup of all pages before modification"""
        if not os.path.exists(self.backup_dir):
            os.makedirs(self.backup_dir)

        for page_file in PAGE_CONFIGS.keys():
            source_path = os.path.join(self.pages_dir, page_file)
            if os.path.exists(source_path):
                backup_path = os.path.join(self.backup_dir, page_file)
                shutil.copy2(source_path, backup_path)
                print(f"✅ Backed up {page_file}")

    def add_import(self, content: str) -> str:
        """Add AI Research import if not already present"""
        import_line = (
            "from utils.enhanced_ai_research_tab import create_ai_research_tab"
        )

        if import_line in content:
            return content

        # Find the last import line
        lines = content.split("\n")
        import_insert_index = -1

        for i, line in enumerate(lines):
            if line.strip().startswith("from ") or line.strip().startswith("import "):
                import_insert_index = i

        if import_insert_index >= 0:
            lines.insert(
                import_insert_index + 1,
                f"# Import AI Research components\n{import_line}",
            )

        return "\n".join(lines)

    def modify_tab_creation(self, content: str, config: Dict) -> str:
        """Modify tab creation to include AI Research tab"""
        # Pattern to find existing tab creation
        tab_patterns = [
            r"tab1,\s*tab2,\s*tab3,\s*tab4\s*=\s*st\.tabs\([^)]+\)",
            r"tab1,\s*tab2,\s*tab3,\s*tab4,\s*tab5\s*=\s*st\.tabs\([^)]+\)",
            r"tabs?\s*=\s*st\.tabs\([^)]+\)",
        ]

        for pattern in tab_patterns:
            match = re.search(pattern, content, re.MULTILINE | re.DOTALL)
            if match:
                original_tabs = match.group(0)

                # Create new tab structure
                new_tabs = """# Create tabs with AI Research
tab_names = ["📈 Data Overview", "✏️ Edit Projections", "📊 Visualizations", "🤖 AI Research", "💾 Data Export"]
tabs = st.tabs(tab_names)"""

                content = content.replace(original_tabs, new_tabs)
                break

        return content

    def update_tab_references(self, content: str) -> str:
        """Update tab references from tab1, tab2, etc. to tabs[0], tabs[1], etc."""
        replacements = {
            r"with\s+tab1:": "with tabs[0]:",
            r"with\s+tab2:": "with tabs[1]:",
            r"with\s+tab3:": "with tabs[2]:",
            r"with\s+tab4:": "with tabs[4]:",  # Skip index 3 for AI Research
            r"with\s+tab5:": "with tabs[4]:",  # In case of 5 tabs originally
        }

        for pattern, replacement in replacements.items():
            content = re.sub(pattern, replacement, content)

        return content

    def add_ai_research_tab(self, content: str, config: Dict) -> str:
        """Add AI Research tab code"""
        ai_research_code = f"""
with tabs[3]:  # AI Research tab
    create_ai_research_tab(
        commodity="{config['commodity']}",
        data_type="{config['data_type']}",
        current_data={config['session_var']},
        db_helper={config['db_helper']},
        update_method_name="{config['update_method']}"
    )
"""

        # Find the position to insert AI Research tab (before Data Export tab)
        export_tab_pattern = r"with\s+tabs\[4\]:\s*\n\s*st\.header\([^}]+?Data Export"
        match = re.search(export_tab_pattern, content, re.MULTILINE | re.DOTALL)

        if match:
            insert_pos = match.start()
            content = (
                content[:insert_pos] + ai_research_code + "\n" + content[insert_pos:]
            )
        else:
            # Fallback: add at the end before the last closing bracket or tab
            content = content.rstrip() + "\n" + ai_research_code

        return content

    def implement_page(self, page_file: str, config: Dict) -> bool:
        """Implement AI Research functionality for a single page"""
        file_path = os.path.join(self.pages_dir, page_file)

        if not os.path.exists(file_path):
            print(f"❌ File not found: {file_path}")
            return False

        # Read original content
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()
        except Exception as e:
            print(f"❌ Error reading {page_file}: {e}")
            return False

        # Apply modifications
        try:
            print(f"🔧 Processing {config['title']}...")

            # Step 1: Add import
            content = self.add_import(content)
            print(f"   ✅ Added import")

            # Step 2: Modify tab creation
            content = self.modify_tab_creation(content, config)
            print(f"   ✅ Modified tab creation")

            # Step 3: Update tab references
            content = self.update_tab_references(content)
            print(f"   ✅ Updated tab references")

            # Step 4: Add AI Research tab
            content = self.add_ai_research_tab(content, config)
            print(f"   ✅ Added AI Research tab")

            # Write modified content
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(content)

            print(f"✅ Successfully implemented AI Research for {page_file}")
            return True

        except Exception as e:
            print(f"❌ Error implementing {page_file}: {e}")
            return False

    def implement_all_pages(self) -> Dict[str, bool]:
        """Implement AI Research functionality for all pages"""
        results = {}

        print("🚀 Starting AI Research Implementation")
        print("=" * 60)

        # Create backup
        print("📦 Creating backup...")
        self.create_backup()

        # Process each page
        for page_file, config in PAGE_CONFIGS.items():
            results[page_file] = self.implement_page(page_file, config)

        return results

    def generate_implementation_report(self, results: Dict[str, bool]):
        """Generate implementation report"""
        successful = sum(1 for success in results.values() if success)
        total = len(results)

        print("\n" + "=" * 60)
        print("📊 IMPLEMENTATION REPORT")
        print("=" * 60)
        print(f"Total Pages: {total}")
        print(f"Successful: {successful}")
        print(f"Failed: {total - successful}")
        print(f"Success Rate: {(successful/total)*100:.1f}%")

        print("\n📋 DETAILED RESULTS:")
        for page_file, success in results.items():
            config = PAGE_CONFIGS[page_file]
            status = "✅ SUCCESS" if success else "❌ FAILED"
            print(f"  {status} - {config['title']} ({page_file})")

        if successful < total:
            print("\n⚠️  Some implementations failed. Check the error messages above.")
            print("💡 You can restore from backup if needed:")
            print(f"   Backup location: {self.backup_dir}")
        else:
            print("\n🎉 All implementations successful!")
            print("🧪 Next steps:")
            print("   1. Test each page to ensure it loads correctly")
            print("   2. Verify AI Research tabs appear and function")
            print("   3. Test Perplexity connection and search functionality")

    def validate_infrastructure(self) -> bool:
        """Validate that required infrastructure files exist"""
        required_files = [
            "client/utils/enhanced_ai_research_tab.py",
            "client/utils/generic_agricultural_ai_agent.py",
            "client/utils/ai_research_components.py",
        ]

        print("🔍 Validating infrastructure...")
        all_exist = True

        for file_path in required_files:
            if os.path.exists(file_path):
                print(f"   ✅ {file_path}")
            else:
                print(f"   ❌ {file_path} - MISSING!")
                all_exist = False

        return all_exist


def main():
    """Main execution function"""
    print("🌾 AI RESEARCH IMPLEMENTATION SCRIPT")
    print("🌽 Adding Perplexity AI Research to all Wheat & Corn pages")
    print("=" * 60)

    implementer = AIResearchImplementer()

    # Validate infrastructure
    if not implementer.validate_infrastructure():
        print("\n❌ Missing required infrastructure files!")
        print("Please ensure all AI Research utility files are in place.")
        return

    # Confirm implementation
    print(f"\nThis will modify {len(PAGE_CONFIGS)} pages:")
    for page_file, config in PAGE_CONFIGS.items():
        print(f"  • {config['title']} ({page_file})")

    response = input("\n❓ Proceed with implementation? (y/N): ")
    if response.lower() != "y":
        print("🛑 Implementation cancelled.")
        return

    # Run implementation
    results = implementer.implement_all_pages()

    # Generate report
    implementer.generate_implementation_report(results)

    print("\n🔗 Related Documentation:")
    print("   • AI Research User Guide: docs/ai_research_guide.md")
    print("   • Troubleshooting: docs/troubleshooting.md")
    print("   • Configuration: client/utils/ai_research_config.py")


if __name__ == "__main__":
    main()
