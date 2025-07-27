# client/scripts/add_ai_research_to_pages.py
"""
Helper script to automatically add AI Research functionality to all wheat and corn pages.
Run this script to generate the exact modifications needed for each page.
"""

import os
import re
from typing import Dict, List

# Page configurations
PAGES_CONFIG = {
    # Wheat pages
    "1_wheat_production.py": {
        "commodity": "wheat",
        "data_type": "production",
        "session_var": "st.session_state.wheat_data",
        "title": "Wheat Production",
    },
    "2_wheat_exports.py": {
        "commodity": "wheat",
        "data_type": "exports",
        "session_var": "st.session_state.wheat_exports_data",
        "title": "Wheat Exports",
    },
    "3_wheat_imports.py": {
        "commodity": "wheat",
        "data_type": "imports",
        "session_var": "st.session_state.wheat_imports_data",
        "title": "Wheat Imports",
    },
    "4_wheat_stocks.py": {
        "commodity": "wheat",
        "data_type": "stocks",
        "session_var": "st.session_state.wheat_stocks_data",
        "title": "Wheat Stocks",
    },
    "5_stock_to_use_ratio.py": {
        "commodity": "wheat",
        "data_type": "su_ratio",
        "session_var": "st.session_state.wheat_su_ratio_data",
        "title": "Wheat S/U Ratio",
    },
    "6_wheat_acreage.py": {
        "commodity": "wheat",
        "data_type": "acreage",
        "session_var": "st.session_state.wheat_acreage_data",
        "title": "Wheat Acreage",
    },
    "7_wheat_yield.py": {
        "commodity": "wheat",
        "data_type": "yield",
        "session_var": "st.session_state.wheat_yield_data",
        "title": "Wheat Yield",
    },
    "8_wheat_world_demand.py": {
        "commodity": "wheat",
        "data_type": "world_demand",
        "session_var": "st.session_state.wheat_demand_data",
        "title": "Wheat World Demand",
    },
    # Corn pages
    "10_corn_production.py": {
        "commodity": "corn",
        "data_type": "production",
        "session_var": "st.session_state.corn_data",
        "title": "Corn Production",
    },
    "11_corn_exports.py": {
        "commodity": "corn",
        "data_type": "exports",
        "session_var": "st.session_state.corn_exports_data",
        "title": "Corn Exports",
    },
    "12_corn_imports.py": {
        "commodity": "corn",
        "data_type": "imports",
        "session_var": "st.session_state.corn_imports_data",
        "title": "Corn Imports",
    },
    "13_corn_stocks.py": {
        "commodity": "corn",
        "data_type": "stocks",
        "session_var": "st.session_state.corn_stocks_data",
        "title": "Corn Stocks",
    },
    "14_corn_stock_to_use_ratio.py": {
        "commodity": "corn",
        "data_type": "su_ratio",
        "session_var": "st.session_state.corn_su_ratio_data",
        "title": "Corn S/U Ratio",
    },
    "15_corn_acreage.py": {
        "commodity": "corn",
        "data_type": "acreage",
        "session_var": "st.session_state.corn_acreage_data",
        "title": "Corn Acreage",
    },
    "16_corn_yield.py": {
        "commodity": "corn",
        "data_type": "yield",
        "session_var": "st.session_state.corn_yield_data",
        "title": "Corn Yield",
    },
    "17_corn_world_demand.py": {
        "commodity": "corn",
        "data_type": "world_demand",
        "session_var": "st.session_state.corn_demand_data",
        "title": "Corn World Demand",
    },
}


def generate_imports_addition():
    """Generate the import statements to add"""
    return """# Import AI Research components (Perplexity-optimized)
from utils.ai_research_components import create_ai_research_tab, add_ai_research_to_page"""


def generate_tab_modification(config: Dict) -> str:
    """Generate the tab modification code"""
    return f"""# Add AI Research tab
tab_names = ["📈 Data Overview", "✏️ Edit Projections", "📊 Visualizations", "💾 Data Export"]

# Add AI Research tab using reusable components
tab_names = add_ai_research_to_page(
    "{config['commodity']}", 
    "{config['data_type']}",
    get_database(), 
    {config['session_var']},
    tab_names
)

# Create tabs
tabs = st.tabs(tab_names)"""


def generate_ai_research_tab(config: Dict) -> str:
    """Generate the AI Research tab code"""
    return f"""# Add the new AI Research tab
with tabs[4]:  # AI Research tab
    create_ai_research_tab(
        commodity="{config['commodity']}",
        data_type="{config['data_type']}",
        db_helper=get_database(),
        current_data={config['session_var']}
    )"""


def generate_modification_instructions(page_file: str, config: Dict) -> str:
    """Generate complete modification instructions for a page"""
    instructions = f"""
{'='*70}
MODIFICATION INSTRUCTIONS FOR: pages/{page_file}
{config['title']} Dashboard
{'='*70}

STEP 1: ADD IMPORTS
Add this line after the existing imports (around line 15-20):

{generate_imports_addition()}

STEP 2: MODIFY TAB CREATION
Find the section where tabs are created (usually around line 200+).
Look for something like:
    tab1, tab2, tab3, tab4 = st.tabs([...])
    
Replace it with:

{generate_tab_modification(config)}

STEP 3: UPDATE EXISTING TABS
Change all existing tab references:
- Replace 'with tab1:' with 'with tabs[0]:'
- Replace 'with tab2:' with 'with tabs[1]:'  
- Replace 'with tab3:' with 'with tabs[2]:'
- Replace 'with tab4:' with 'with tabs[3]:'

STEP 4: ADD AI RESEARCH TAB
Add this at the end of the tab sections:

{generate_ai_research_tab(config)}

STEP 5: TEST
1. Run the page to ensure no errors
2. Check that all existing tabs still work
3. Test the new AI Research tab
4. Verify Perplexity connection works

{'='*70}
"""
    return instructions


def generate_all_modifications():
    """Generate modification instructions for all pages"""
    print("AI RESEARCH INTEGRATION GUIDE")
    print("=" * 60)
    print("This script generates the exact modifications needed to add")
    print("Perplexity AI Research functionality to all wheat and corn pages.")
    print()

    for page_file, config in PAGES_CONFIG.items():
        instructions = generate_modification_instructions(page_file, config)
        print(instructions)

        # Ask if user wants to continue (for interactive mode)
        response = input(f"\nPress Enter to continue to next page, or 'q' to quit: ")
        if response.lower() == "q":
            break


def create_modification_files():
    """Create individual modification files for each page"""
    output_dir = "ai_research_modifications"
    os.makedirs(output_dir, exist_ok=True)

    for page_file, config in PAGES_CONFIG.items():
        instructions = generate_modification_instructions(page_file, config)

        output_file = os.path.join(output_dir, f"{page_file}_modifications.txt")
        with open(output_file, "w", encoding="utf-8") as f:
            f.write(instructions)

        print(f"Created: {output_file}")


def generate_summary_checklist():
    """Generate a summary checklist for all modifications"""
    checklist = """
AI RESEARCH INTEGRATION CHECKLIST
================================

For each page, complete these steps:

□ 1. Add import statement for AI research components
□ 2. Modify tab creation to use dynamic tab list
□ 3. Update existing tab references (tab1 → tabs[0], etc.)
□ 4. Add AI Research tab code
□ 5. Test functionality

PAGES TO MODIFY:
"""

    for i, (page_file, config) in enumerate(PAGES_CONFIG.items(), 1):
        checklist += f"\n□ {i:2d}. {config['title']} (pages/{page_file})"

    checklist += """

REQUIRED FILES:
□ client/utils/ai_research_components.py
□ client/utils/ai_research_config.py
□ client/utils/perplexity_prompts.py

DEPENDENCIES:
□ Perplexity MCP server connected and functioning
□ perplexity_advanced_search tool available
□ Database helpers (WheatProductionDB, CornProductionDB)
□ Session state variables properly initialized

TESTING CHECKLIST:
□ All existing tabs work correctly
□ AI Research button appears and is functional
□ Perplexity search executes successfully
□ Progress bar displays during research
□ Research results are parsed and displayed correctly
□ Update functionality works for 2025/2026 projections
□ Database updates are saved correctly
□ Only Perplexity tools are used (no Google Search or Firecrawl)
"""

    return checklist


def generate_quick_reference():
    """Generate a quick reference table"""
    print("\nQUICK REFERENCE TABLE:")
    print("=" * 80)
    print(f"{'Page':<25} {'Commodity':<10} {'Data Type':<15} {'Session Variable'}")
    print("-" * 80)

    for page_file, config in PAGES_CONFIG.items():
        session_var_short = config["session_var"].replace("st.session_state.", "")
        print(
            f"{page_file:<25} {config['commodity']:<10} {config['data_type']:<15} {session_var_short}"
        )


def create_batch_modification_script():
    """Create a batch script that shows all modifications"""
    script_content = """#!/usr/bin/env python3
# Batch modification script for all pages

import os
import sys

# Add this to each page after existing imports
IMPORT_LINE = '''
# Import AI Research components (Perplexity-optimized)
from utils.ai_research_components import create_ai_research_tab, add_ai_research_to_page
'''

# Modifications for each page
MODIFICATIONS = {
"""

    for page_file, config in PAGES_CONFIG.items():
        script_content += f"""
    "{page_file}": {{
        "commodity": "{config['commodity']}",
        "data_type": "{config['data_type']}",
        "session_var": "{config['session_var']}",
        "title": "{config['title']}"
    }},"""

    script_content += """
}

def apply_modifications():
    '''Apply modifications to all pages'''
    for page_file, config in MODIFICATIONS.items():
        print(f"Processing {config['title']}...")
        print(f"  Commodity: {config['commodity']}")
        print(f"  Data Type: {config['data_type']}")
        print(f"  Session Var: {config['session_var']}")
        print("  - Add imports")
        print("  - Modify tab creation")
        print("  - Update tab references")
        print("  - Add AI Research tab")
        print()

if __name__ == "__main__":
    apply_modifications()
"""

    with open("batch_modifications.py", "w", encoding="utf-8") as f:
        f.write(script_content)

    print("Created batch_modifications.py")


def main():
    """Main function to run the modification generator"""
    print("AI RESEARCH INTEGRATION HELPER")
    print("=" * 50)
    print("Choose an option:")
    print("1. Display all modifications (interactive)")
    print("2. Create modification files")
    print("3. Generate summary checklist")
    print("4. Generate quick reference")
    print("5. Create batch modification script")
    print("6. Test configuration validity")

    choice = input("\nEnter choice (1-6): ").strip()

    if choice == "1":
        generate_all_modifications()
    elif choice == "2":
        create_modification_files()
        print(f"\nModification files created in 'ai_research_modifications' directory")
    elif choice == "3":
        checklist = generate_summary_checklist()
        print(checklist)

        # Also save to file
        with open("ai_research_checklist.txt", "w", encoding="utf-8") as f:
            f.write(checklist)
        print("\nChecklist saved to: ai_research_checklist.txt")
    elif choice == "4":
        generate_quick_reference()
    elif choice == "5":
        create_batch_modification_script()
    elif choice == "6":
        test_config()
    else:
        print("Invalid choice")


def test_config():
    """Test that all configurations are valid"""
    print("Testing configurations...")

    required_keys = ["commodity", "data_type", "session_var", "title"]
    valid_commodities = ["wheat", "corn"]
    valid_data_types = [
        "production",
        "exports",
        "imports",
        "stocks",
        "su_ratio",
        "acreage",
        "yield",
        "world_demand",
    ]

    errors = []
    warnings = []

    for page_file, config in PAGES_CONFIG.items():
        # Check required keys
        for key in required_keys:
            if key not in config:
                errors.append(f"{page_file}: Missing key '{key}'")

        # Check valid values
        if config.get("commodity") not in valid_commodities:
            errors.append(f"{page_file}: Invalid commodity '{config.get('commodity')}'")

        if config.get("data_type") not in valid_data_types:
            errors.append(f"{page_file}: Invalid data_type '{config.get('data_type')}'")

        # Check session variable naming consistency
        expected_prefix = f"st.session_state.{config.get('commodity')}"
        if not config.get("session_var", "").startswith(expected_prefix):
            warnings.append(f"{page_file}: Session variable may be inconsistent")

    if errors:
        print("❌ Configuration errors found:")
        for error in errors:
            print(f"  - {error}")
    else:
        print("✅ All configurations are valid!")

    if warnings:
        print("\n⚠️  Warnings:")
        for warning in warnings:
            print(f"  - {warning}")

    print(f"\nSummary: {len(PAGES_CONFIG)} pages configured")
    print(
        f"Wheat pages: {len([p for p in PAGES_CONFIG.values() if p['commodity'] == 'wheat'])}"
    )
    print(
        f"Corn pages: {len([p for p in PAGES_CONFIG.values() if p['commodity'] == 'corn'])}"
    )


if __name__ == "__main__":
    main()
