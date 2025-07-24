#!/usr/bin/env python3
"""
Fix Implementation Issues Script
Fixes two critical issues:
1. Duplicate button IDs in AI Research tabs
2. Incorrect session state variable names
"""

import os
import re
from typing import Dict, List

# Correct session state variable mapping based on actual page analysis
CORRECT_SESSION_VARS = {
    "1_wheat_production.py": "st.session_state.wheat_data",
    "2_wheat_exports.py": "st.session_state.export_data",
    "3_wheat_imports.py": "st.session_state.import_data",
    "4_wheat_stocks.py": "st.session_state.stock_data",
    "5_stock_to_use_ratio.py": "st.session_state.su_ratio_data",
    "6_wheat_acreage.py": "st.session_state.acreage_data",
    "7_wheat_yield.py": "st.session_state.yield_data",
    "8_wheat_world_demand.py": "st.session_state.demand_data",
    "10_corn_production.py": "st.session_state.corn_data",
    "11_corn_exports.py": "st.session_state.corn_export_data",  # Note: singular "export_data"
    "12_corn_imports.py": "st.session_state.corn_import_data",  # Note: singular "import_data"
    "13_corn_stocks.py": "st.session_state.corn_stock_data",  # Note: singular "stock_data"
    "14_corn_stock_to_use_ratio.py": "st.session_state.corn_su_ratio_data",
    "15_corn_acreage.py": "st.session_state.corn_acreage_data",
    "16_corn_yield.py": "st.session_state.corn_yield_data",
    "17_corn_world_demand.py": "st.session_state.corn_demand_data",
}


class ImplementationFixer:
    """Fixes critical issues in the AI Research implementation"""

    def __init__(self, pages_dir: str = "client/pages"):
        self.pages_dir = pages_dir

    def fix_button_keys(self, content: str, page_file: str) -> str:
        """Add unique keys to buttons in AI Research functionality"""
        # Get the base name for unique keys
        page_base = page_file.replace(".py", "").replace("_", "")

        # Fix the research button key
        content = re.sub(
            r'st\.button\(\s*"🔍 Research Latest Data"([^)]*)\)',
            f'st.button("🔍 Research Latest Data", key="research_btn_{page_base}"\\1)',
            content,
        )

        # Fix update button key
        content = re.sub(
            r'st\.button\(\s*"📊 Update 2025/2026 Projections"([^)]*)\)',
            f'st.button("📊 Update 2025/2026 Projections", key="update_btn_{page_base}"\\1)',
            content,
        )

        # Fix clear button key
        content = re.sub(
            r'st\.button\(\s*"🗑️ Clear Research"([^)]*)\)',
            f'st.button("🗑️ Clear Research", key="clear_btn_{page_base}"\\1)',
            content,
        )

        return content

    def fix_session_variable(self, content: str, page_file: str) -> str:
        """Fix session state variable name in create_ai_research_tab call"""
        correct_var = CORRECT_SESSION_VARS.get(page_file)
        if not correct_var:
            return content

        # Find and replace the create_ai_research_tab call
        pattern = r"create_ai_research_tab\s*\(\s*([^)]+)\)"

        def replace_session_var(match):
            call_content = match.group(1)
            # Replace current_data parameter
            call_content = re.sub(
                r"current_data\s*=\s*st\.session_state\.[^,\)]+",
                f"current_data={correct_var}",
                call_content,
            )
            return f"create_ai_research_tab(\n        {call_content}\n    )"

        content = re.sub(pattern, replace_session_var, content, flags=re.DOTALL)

        return content

    def fix_page(self, page_file: str) -> bool:
        """Fix issues in a single page"""
        file_path = os.path.join(self.pages_dir, page_file)

        if not os.path.exists(file_path):
            print(f"❌ File not found: {file_path}")
            return False

        try:
            # Read current content
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()

            original_content = content

            # Apply fixes
            print(f"🔧 Fixing {page_file}...")

            # Fix button keys
            content = self.fix_button_keys(content, page_file)

            # Fix session variable
            content = self.fix_session_variable(content, page_file)

            # Only write if changes were made
            if content != original_content:
                with open(file_path, "w", encoding="utf-8") as f:
                    f.write(content)
                print(f"   ✅ Fixed button keys and session variables")
                return True
            else:
                print(f"   ℹ️  No changes needed")
                return True

        except Exception as e:
            print(f"❌ Error fixing {page_file}: {e}")
            return False

    def fix_enhanced_ai_research_tab(self) -> bool:
        """Fix the enhanced_ai_research_tab.py to add unique button keys"""
        tab_file = "client/utils/enhanced_ai_research_tab.py"

        if not os.path.exists(tab_file):
            print(f"❌ File not found: {tab_file}")
            return False

        try:
            with open(tab_file, "r", encoding="utf-8") as f:
                content = f.read()

            original_content = content

            print("🔧 Fixing enhanced_ai_research_tab.py...")

            # Add unique keys to buttons by using function parameters
            # Pattern: st.button("🔍 Research Latest Data"
            content = re.sub(
                r'st\.button\(\s*"🔍 Research Latest Data"([^)]*)\)',
                r'st.button("🔍 Research Latest Data", key=f"research_{commodity}_{data_type}"\\1)',
                content,
            )

            # Pattern: st.button("📊 Update 2025/2026 Projections"
            content = re.sub(
                r'st\.button\(\s*"📊 Update 2025/2026 Projections"([^)]*)\)',
                r'st.button("📊 Update 2025/2026 Projections", key=f"update_{commodity}_{data_type}"\\1)',
                content,
            )

            # Pattern: st.button("🗑️ Clear Research"
            content = re.sub(
                r'st\.button\(\s*"🗑️ Clear Research"([^)]*)\)',
                r'st.button("🗑️ Clear Research", key=f"clear_{commodity}_{data_type}"\\1)',
                content,
            )

            if content != original_content:
                with open(tab_file, "w", encoding="utf-8") as f:
                    f.write(content)
                print("   ✅ Added unique button keys using function parameters")
                return True
            else:
                print("   ℹ️  No changes needed in enhanced_ai_research_tab.py")
                return True

        except Exception as e:
            print(f"❌ Error fixing enhanced_ai_research_tab.py: {e}")
            return False

    def fix_all_issues(self) -> Dict[str, bool]:
        """Fix all implementation issues"""
        print("🛠️  FIXING AI RESEARCH IMPLEMENTATION ISSUES")
        print("=" * 60)

        results = {}

        # First, fix the core enhanced_ai_research_tab.py
        results["enhanced_ai_research_tab.py"] = self.fix_enhanced_ai_research_tab()

        # Then fix each page
        for page_file in CORRECT_SESSION_VARS.keys():
            results[page_file] = self.fix_page(page_file)

        return results

    def generate_fix_report(self, results: Dict[str, bool]):
        """Generate fix report"""
        successful = sum(1 for success in results.values() if success)
        total = len(results)

        print("\n" + "=" * 60)
        print("📊 FIX REPORT")
        print("=" * 60)
        print(f"Total Files: {total}")
        print(f"Successfully Fixed: {successful}")
        print(f"Failed: {total - successful}")
        print(f"Success Rate: {(successful/total)*100:.1f}%")

        print("\n📋 DETAILED RESULTS:")
        for file_name, success in results.items():
            status = "✅ FIXED" if success else "❌ FAILED"
            print(f"  {status} - {file_name}")

        if successful == total:
            print("\n🎉 All issues fixed successfully!")
            print("\n🧪 NEXT STEPS:")
            print("   1. Restart your Streamlit application")
            print("   2. Test each page to ensure no errors")
            print("   3. Verify AI Research tabs work correctly")
            print("   4. Test Perplexity functionality")
        else:
            print(f"\n⚠️  Some fixes failed. Check error messages above.")

        print("\n🔄 RESTART COMMAND:")
        print("   streamlit run app.py")


def main():
    """Main execution function"""
    print("🚨 AI RESEARCH IMPLEMENTATION FIXER")
    print("🔧 Fixing duplicate button IDs and session variable issues")
    print("=" * 60)

    fixer = ImplementationFixer()

    # Show what will be fixed
    print("Issues to fix:")
    print("  1. Duplicate button IDs across pages")
    print("  2. Incorrect session state variable names")
    print("  3. Missing unique keys in enhanced_ai_research_tab.py")

    response = input("\n❓ Proceed with fixes? (y/N): ")
    if response.lower() != "y":
        print("🛑 Fix cancelled.")
        return

    # Run fixes
    results = fixer.fix_all_issues()

    # Generate report
    fixer.generate_fix_report(results)


if __name__ == "__main__":
    main()
