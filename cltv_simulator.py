import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime
import numpy as np

class CLTVCalculator:
    """
    Combined Loan-to-Value (CLTV) Ratio Calculator
    
    CLTV measures the total amount of debt secured by a property relative to its value.
    Formula: CLTV = (Sum of all loan balances) / Property Value × 100
    """
    
    def __init__(self):
        self.loans = []
        self.property_value = 0
        
    def add_loan(self, loan_name, balance, interest_rate=None, loan_type="mortgage"):
        """Add a loan to the calculation"""
        loan = {
            'name': loan_name,
            'balance': balance,
            'interest_rate': interest_rate,
            'type': loan_type
        }
        self.loans.append(loan)
        
    def set_property_value(self, value):
        """Set the current property value"""
        self.property_value = value
        
    def calculate_cltv(self):
        """Calculate the Combined Loan-to-Value ratio"""
        if self.property_value == 0:
            return 0
        
        total_debt = sum(loan['balance'] for loan in self.loans)
        cltv = (total_debt / self.property_value) * 100
        return round(cltv, 2)
    
    def calculate_ltv(self, primary_loan_balance):
        """Calculate the standard Loan-to-Value ratio for primary mortgage only"""
        if self.property_value == 0:
            return 0
        
        ltv = (primary_loan_balance / self.property_value) * 100
        return round(ltv, 2)
    
    def get_risk_assessment(self, cltv_ratio):
        """Assess risk level based on CLTV ratio"""
        if cltv_ratio <= 65:
            return "Low Risk", "Excellent borrowing position"
        elif cltv_ratio <= 75:
            return "Moderate Risk", "Good borrowing position"
        elif cltv_ratio <= 80:
            return "Moderate-High Risk", "Standard lending threshold"
        elif cltv_ratio <= 85:
            return "High Risk", "May require PMI or higher rates"
        elif cltv_ratio <= 95:
            return "Very High Risk", "Limited lending options"
        else:
            return "Extreme Risk", "Underwater/Upside down on property"
    
    def calculate_available_equity(self):
        """Calculate available equity in the property"""
        total_debt = sum(loan['balance'] for loan in self.loans)
        equity = self.property_value - total_debt
        return max(0, equity)
    
    def simulate_scenarios(self, property_value_changes, new_loan_amounts):
        """Simulate different scenarios for CLTV ratios"""
        scenarios = []
        base_debt = sum(loan['balance'] for loan in self.loans)
        
        for pv_change in property_value_changes:
            for new_loan in new_loan_amounts:
                new_property_value = self.property_value * (1 + pv_change/100)
                total_new_debt = base_debt + new_loan
                new_cltv = (total_new_debt / new_property_value) * 100
                
                scenarios.append({
                    'Property Value Change (%)': pv_change,
                    'New Loan Amount': new_loan,
                    'New Property Value': new_property_value,
                    'Total Debt': total_new_debt,
                    'CLTV (%)': round(new_cltv, 2)
                })
        
        return pd.DataFrame(scenarios)

def main():
    st.set_page_config(
        page_title="CLTV Ratio Simulator",
        page_icon="🏠",
        layout="wide"
    )
    
    st.title("🏠 Combined Loan-to-Value (CLTV) Ratio Simulator")
    st.markdown("""
    **Combined Loan-to-Value (CLTV)** measures the total amount of debt secured by a property 
    relative to its current market value. Unlike LTV which only considers the primary mortgage, 
    CLTV includes all liens and secured loans against the property.
    
    **Formula**: CLTV = (Sum of all loan balances / Property Value) × 100
    """)
    
    # Initialize calculator
    calculator = CLTVCalculator()
    
    # Sidebar for inputs
    st.sidebar.header("Property & Loan Information")
    
    # Property value input
    property_value = st.sidebar.number_input(
        "Current Property Value ($)",
        min_value=1000,
        value=500000,
        step=10000,
        help="Current appraised or market value of the property"
    )
    calculator.set_property_value(property_value)
    
    # Loan inputs
    st.sidebar.subheader("Existing Loans")
    
    # Primary mortgage
    primary_mortgage = st.sidebar.number_input(
        "Primary Mortgage Balance ($)",
        min_value=0,
        value=350000,
        step=5000
    )
    primary_rate = st.sidebar.number_input(
        "Primary Mortgage Rate (%)",
        min_value=0.0,
        value=6.5,
        step=0.1
    )
    
    if primary_mortgage > 0:
        calculator.add_loan("Primary Mortgage", primary_mortgage, primary_rate, "Primary Mortgage")
    
    # Additional loans
    num_additional_loans = st.sidebar.selectbox(
        "Number of Additional Loans",
        options=[0, 1, 2, 3, 4],
        index=1
    )
    
    for i in range(num_additional_loans):
        st.sidebar.markdown(f"**Additional Loan {i+1}**")
        loan_name = st.sidebar.text_input(f"Loan {i+1} Name", value=f"HELOC/Second Mortgage {i+1}", key=f"name_{i}")
        loan_balance = st.sidebar.number_input(f"Loan {i+1} Balance ($)", min_value=0, value=50000, step=1000, key=f"balance_{i}")
        loan_rate = st.sidebar.number_input(f"Loan {i+1} Rate (%)", min_value=0.0, value=7.5, step=0.1, key=f"rate_{i}")
        
        if loan_balance > 0:
            calculator.add_loan(loan_name, loan_balance, loan_rate, "Secondary Loan")
    
    # Main content area
    col1, col2 = st.columns([2, 1])
    
    with col1:
        # Calculate current metrics
        cltv_ratio = calculator.calculate_cltv()
        ltv_ratio = calculator.calculate_ltv(primary_mortgage)
        available_equity = calculator.calculate_available_equity()
        risk_level, risk_description = calculator.get_risk_assessment(cltv_ratio)
        
        # Display key metrics
        st.header("Current Financial Position")
        
        metric_col1, metric_col2, metric_col3, metric_col4 = st.columns(4)
        
        with metric_col1:
            st.metric("CLTV Ratio", f"{cltv_ratio}%", 
                     delta=f"{cltv_ratio - 80:.1f}% vs 80% threshold")
        
        with metric_col2:
            st.metric("LTV Ratio", f"{ltv_ratio}%")
        
        with metric_col3:
            st.metric("Available Equity", f"${available_equity:,.0f}")
        
        with metric_col4:
            color = "red" if cltv_ratio > 80 else "orange" if cltv_ratio > 75 else "green"
            st.markdown(f"**Risk Level**: <span style='color: {color}'>{risk_level}</span>", 
                       unsafe_allow_html=True)
        
        # Loan breakdown table
        if calculator.loans:
            st.subheader("Loan Breakdown")
            loan_data = []
            total_debt = 0
            
            for loan in calculator.loans:
                loan_data.append({
                    'Loan Type': loan['name'],
                    'Balance': f"${loan['balance']:,.0f}",
                    'Interest Rate': f"{loan['interest_rate']:.2f}%" if loan['interest_rate'] else "N/A",
                    'Percentage of Property Value': f"{(loan['balance']/property_value)*100:.1f}%"
                })
                total_debt += loan['balance']
            
            # Add total row
            loan_data.append({
                'Loan Type': '**TOTAL**',
                'Balance': f"**${total_debt:,.0f}**",
                'Interest Rate': '**-**',
                'Percentage of Property Value': f"**{cltv_ratio:.1f}%**"
            })
            
            df_loans = pd.DataFrame(loan_data)
            st.dataframe(df_loans, use_container_width=True)
    
    with col2:
        # CLTV gauge chart
        st.subheader("CLTV Risk Gauge")
        
        fig_gauge = go.Figure(go.Indicator(
            mode = "gauge+number+delta",
            value = cltv_ratio,
            domain = {'x': [0, 1], 'y': [0, 1]},
            title = {'text': "CLTV %"},
            delta = {'reference': 80},
            gauge = {
                'axis': {'range': [None, 100]},
                'bar': {'color': "darkblue"},
                'steps': [
                    {'range': [0, 65], 'color': "lightgreen"},
                    {'range': [65, 75], 'color': "yellow"},
                    {'range': [75, 80], 'color': "orange"},
                    {'range': [80, 95], 'color': "lightcoral"},
                    {'range': [95, 100], 'color': "red"}
                ],
                'threshold': {
                    'line': {'color': "red", 'width': 4},
                    'thickness': 0.75,
                    'value': 80
                }
            }
        ))
        
        fig_gauge.update_layout(height=300)
        st.plotly_chart(fig_gauge, use_container_width=True)
        
        # Risk assessment
        st.subheader("Risk Assessment")
        st.write(f"**{risk_level}**")
        st.write(risk_description)
        
        if cltv_ratio > 80:
            st.warning("⚠️ CLTV above 80% - May require PMI or face higher interest rates")
        elif cltv_ratio > 95:
            st.error("🚨 CLTV above 95% - Very limited lending options")
    
    # Scenario Analysis
    st.header("Scenario Analysis")
    
    scenario_col1, scenario_col2 = st.columns(2)
    
    with scenario_col1:
        st.subheader("Property Value Changes")
        value_changes = st.multiselect(
            "Property Value Change (%)",
            options=[-20, -10, -5, 0, 5, 10, 15, 20],
            default=[-10, 0, 10]
        )
    
    with scenario_col2:
        st.subheader("Additional Borrowing")
        max_additional = min(100000, available_equity)
        additional_loans = st.multiselect(
            "Additional Loan Amounts ($)",
            options=[0, 10000, 25000, 50000, 75000, 100000],
            default=[0, 25000, 50000]
        )
    
    if value_changes and additional_loans:
        scenarios_df = calculator.simulate_scenarios(value_changes, additional_loans)
        
        # Scenario results table
        st.subheader("Scenario Results")
        
        # Color code CLTV values
        def color_cltv(val):
            if val <= 65:
                return 'background-color: lightgreen'
            elif val <= 75:
                return 'background-color: yellow'
            elif val <= 80:
                return 'background-color: orange'
            elif val <= 95:
                return 'background-color: lightcoral'
            else:
                return 'background-color: red'
        
        styled_df = scenarios_df.style.applymap(color_cltv, subset=['CLTV (%)'])
        st.dataframe(styled_df, use_container_width=True)
        
        # Scenario visualization
        fig_scenarios = px.scatter(
            scenarios_df,
            x='Property Value Change (%)',
            y='New Loan Amount',
            size='CLTV (%)',
            color='CLTV (%)',
            color_continuous_scale='RdYlGn_r',
            title="CLTV Scenarios: Property Value vs Additional Borrowing",
            hover_data=['New Property Value', 'Total Debt']
        )
        
        fig_scenarios.add_hline(y=0, line_dash="dash", line_color="gray")
        fig_scenarios.add_vline(x=0, line_dash="dash", line_color="gray")
        
        st.plotly_chart(fig_scenarios, use_container_width=True)
    
    # Educational content
    st.header("Understanding CLTV")
    
    edu_col1, edu_col2 = st.columns(2)
    
    with edu_col1:
        st.subheader("Key Differences: LTV vs CLTV")
        st.markdown("""
        **LTV (Loan-to-Value)**:
        - Only considers primary mortgage
        - Formula: Primary Loan / Property Value × 100
        - Used for initial mortgage qualification
        
        **CLTV (Combined Loan-to-Value)**:
        - Includes ALL secured loans against property
        - Formula: (All Loans) / Property Value × 100
        - Used when applying for second mortgages, HELOCs
        """)
    
    with edu_col2:
        st.subheader("Typical CLTV Thresholds")
        st.markdown("""
        - **≤ 65%**: Excellent position, best rates
        - **65-75%**: Good position, favorable terms
        - **75-80%**: Standard lending threshold
        - **80-85%**: May require PMI, higher rates
        - **85-95%**: Limited options, high risk
        - **> 95%**: Very limited lending options
        """)
    
    # Tips for improvement
    st.subheader("Tips to Improve Your CLTV")
    
    tip_col1, tip_col2, tip_col3 = st.columns(3)
    
    with tip_col1:
        st.markdown("""
        **💰 Reduce Debt**
        - Pay down existing loans faster
        - Make extra principal payments
        - Pay off smaller loans completely
        """)
    
    with tip_col2:
        st.markdown("""
        **🏠 Increase Property Value**
        - Home improvements/renovations
        - Proper maintenance
        - Market appreciation over time
        """)
    
    with tip_col3:
        st.markdown("""
        **📊 Strategic Borrowing**
        - Borrow only what you need
        - Time applications with market conditions
        - Consider refinancing options
        """)
    
    # Footer with disclaimer
    st.markdown("---")
    st.caption("""
    **Disclaimer**: This tool is for educational and estimation purposes only. 
    Actual lending decisions depend on multiple factors including credit score, 
    income, debt-to-income ratio, and lender-specific requirements. 
    Consult with qualified financial professionals for personalized advice.
    """)

if __name__ == "__main__":
    main()