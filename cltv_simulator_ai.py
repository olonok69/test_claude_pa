import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime
import numpy as np
import json

# Import the AI Agent
from cltv_ai_agent import (
    create_cltv_agent, 
    analyze_borrower_comprehensive,
    quick_loan_prequalification,
    CLTVCalculator  # Your existing calculator
)

def main():
    st.set_page_config(
        page_title="AI-Powered CLTV Analysis",
        page_icon="🏠",
        layout="wide"
    )
    
    st.title("🤖 AI-Powered CLTV & Mortgage Analysis")
    st.markdown("""
    **Enhanced CLTV Simulator** with AI-powered lending analysis using LLM technology.
    Get comprehensive borrower risk assessment and loan recommendations.
    """)
    
    # Sidebar configuration
    st.sidebar.header("Analysis Configuration")
    
    # AI Model Selection
    model_provider = st.sidebar.selectbox(
        "AI Model Provider",
        ["openai", "vertexai"],
        help="Choose between OpenAI GPT or Google Gemini"
    )
    
    # Analysis Type
    analysis_type = st.sidebar.radio(
        "Analysis Type",
        ["Quick Prequalification", "Comprehensive Analysis", "Scenario Comparison"]
    )
    
    # Main input section
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.header("📝 Borrower Information")
        
        # Property and loan details
        st.subheader("Property & Loan Details")
        property_value = st.number_input(
            "Property Value ($)",
            min_value=1000,
            value=500000,
            step=10000
        )
        
        down_payment = st.number_input(
            "Down Payment ($)",
            min_value=0,
            value=100000,
            step=5000
        )
        
        primary_loan = property_value - down_payment
        st.metric("Primary Loan Amount", f"${primary_loan:,.0f}")
        
        # Secondary loans
        st.subheader("Additional Loans")
        num_secondary = st.selectbox("Number of Secondary Loans", [0, 1, 2, 3])
        secondary_loans = []
        
        for i in range(num_secondary):
            loan_amount = st.number_input(
                f"Secondary Loan {i+1} ($)",
                min_value=0,
                value=25000,
                step=1000,
                key=f"secondary_{i}"
            )
            if loan_amount > 0:
                secondary_loans.append(loan_amount)
        
        # Borrower financial details
        st.subheader("Borrower Financials")
        gross_income = st.number_input(
            "Gross Monthly Income ($)",
            min_value=1000,
            value=8000,
            step=100
        )
        
        monthly_debts = st.number_input(
            "Monthly Debt Payments ($)",
            min_value=0,
            value=800,
            step=50
        )
        
        credit_score = st.number_input(
            "Credit Score",
            min_value=300,
            max_value=850,
            value=740,
            step=10
        )
        
        # Advanced fields for comprehensive analysis
        if analysis_type == "Comprehensive Analysis":
            employment_years = st.number_input(
                "Years of Employment",
                min_value=0.0,
                value=3.5,
                step=0.5
            )
            
            liquid_assets = st.number_input(
                "Liquid Assets ($)",
                min_value=0,
                value=50000,
                step=5000
            )
            
            loan_type = st.selectbox(
                "Loan Type",
                ["conventional", "fha", "va", "usda"]
            )
        else:
            employment_years = 2.0
            liquid_assets = 0.0
            loan_type = "conventional"
    
    with col2:
        st.header("🎯 Quick Metrics")
        
        # Calculate basic metrics
        calculator = CLTVCalculator()
        calculator.set_property_value(property_value)
        calculator.add_loan("Primary Mortgage", primary_loan, 6.5)
        
        for i, loan in enumerate(secondary_loans):
            calculator.add_loan(f"Secondary Loan {i+1}", loan, 7.5)
        
        cltv_ratio = calculator.calculate_cltv()
        ltv_ratio = calculator.calculate_ltv(primary_loan)
        available_equity = calculator.calculate_available_equity()
        
        st.metric("LTV Ratio", f"{ltv_ratio:.1f}%")
        st.metric("CLTV Ratio", f"{cltv_ratio:.1f}%") 
        st.metric("Available Equity", f"${available_equity:,.0f}")
        
        # Estimated monthly payment
        monthly_rate = 0.065 / 12
        n_payments = 360
        if primary_loan > 0:
            pi_payment = primary_loan * (monthly_rate * (1 + monthly_rate)**n_payments) / ((1 + monthly_rate)**n_payments - 1)
            estimated_payment = pi_payment * 1.3  # Add taxes, insurance
            st.metric("Est. Monthly Payment", f"${estimated_payment:,.0f}")
        
        # DTI ratios
        if gross_income > 0:
            estimated_housing_dti = (estimated_payment / gross_income) * 100
            total_dti = ((estimated_payment + monthly_debts) / gross_income) * 100
            st.metric("Housing DTI", f"{estimated_housing_dti:.1f}%")
            st.metric("Total DTI", f"{total_dti:.1f}%")
    
    # AI Analysis Section
    st.header("🤖 AI-Powered Analysis")
    
    if st.button("🚀 Run AI Analysis", type="primary"):
        with st.spinner("Running AI analysis..."):
            try:
                # Estimate housing payment for analysis
                if primary_loan > 0:
                    monthly_rate = 0.065 / 12
                    n_payments = 360
                    pi_payment = primary_loan * (monthly_rate * (1 + monthly_rate)**n_payments) / ((1 + monthly_rate)**n_payments - 1)
                    estimated_housing_payment = pi_payment * 1.3
                else:
                    estimated_housing_payment = 0
                
                if analysis_type == "Quick Prequalification":
                    result = quick_loan_prequalification(
                        property_value=property_value,
                        down_payment=down_payment,
                        gross_monthly_income=gross_income,
                        monthly_debt_payments=monthly_debts,
                        credit_score=credit_score
                    )
                
                elif analysis_type == "Comprehensive Analysis":
                    result = analyze_borrower_comprehensive(
                        property_value=property_value,
                        primary_loan_amount=primary_loan,
                        gross_monthly_income=gross_income,
                        monthly_debt_payments=monthly_debts,
                        proposed_housing_payment=estimated_housing_payment,
                        credit_score=credit_score,
                        down_payment=down_payment,
                        secondary_loans=secondary_loans,
                        employment_years=employment_years,
                        liquid_assets=liquid_assets,
                        loan_type=loan_type
                    )
                
                elif analysis_type == "Scenario Comparison":
                    # Create an agent and run scenario comparison
                    graph = create_cltv_agent()
                    config = {"configurable": {"thread_id": "scenario_comparison"}}
                    
                    scenario_request = f"""
                    Please compare different loan scenarios for this borrower using compare_loan_scenarios:
                    
                    - Property Value: ${property_value:,.2f}
                    - Current Income: ${gross_income:,.2f}
                    - Monthly Debts: ${monthly_debts:,.2f}
                    - Credit Score: {credit_score}
                    
                    Compare down payments of $50,000, $75,000, and $100,000 with 
                    corresponding loan amounts. Provide recommendations for the optimal scenario.
                    """
                    
                    from langchain_core.messages import HumanMessage
                    scenario_result = graph.invoke(
                        {"messages": [HumanMessage(content=scenario_request)]},
                        config
                    )
                    result = scenario_result["messages"][-1].content
                
                # Display results
                st.subheader("📊 AI Analysis Results")
                st.markdown(result)
                
            except Exception as e:
                st.error(f"Analysis failed: {str(e)}")
                st.info("Please check your AI configuration and try again.")
    
    # Traditional Analysis Section (your existing functionality)
    st.header("📈 Traditional CLTV Analysis")
    
    # Include your existing visualization and analysis code here
    # This maintains backward compatibility with your current simulator
    
    # Risk gauge
    fig_gauge = go.Figure(go.Indicator(
        mode="gauge+number+delta",
        value=cltv_ratio,
        domain={'x': [0, 1], 'y': [0, 1]},
        title={'text': "CLTV %"},
        delta={'reference': 80},
        gauge={
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
    
    # Educational content
    st.header("📚 Understanding AI-Enhanced CLTV Analysis")
    
    with st.expander("How the AI Agent Works"):
        st.markdown("""
        The AI agent uses multiple sophisticated tools to analyze borrower risk:
        
        **🔧 Analysis Tools:**
        - **CLTV Calculator**: Comprehensive combined loan-to-value analysis
        - **DTI Analyzer**: Front-end and back-end debt-to-income assessment
        - **Comprehensive Scorer**: Multi-factor risk scoring (0-100 scale)
        - **Scenario Comparator**: Optimal loan structure recommendations
        
        **🎯 Scoring Components:**
        - CLTV Ratio (25% weight)
        - DTI Ratios (25% weight)  
        - Credit Score (25% weight)
        - Employment & Assets (15% weight)
        - Down Payment (10% weight)
        
        **📊 Output:**
        - Clear approve/conditional/deny recommendations
        - Risk level assessment and rate tier suggestions
        - Specific improvement recommendations
        - Alternative loan product suggestions
        """)
    
    with st.expander("AI vs Traditional Analysis"):
        st.markdown("""
        **Traditional CLTV Analysis:**
        - Fixed thresholds and calculations
        - Limited scenario modeling
        - Basic risk categorization
        
        **AI-Enhanced Analysis:**
        - Natural language interaction
        - Multi-factor comprehensive scoring
        - Contextual recommendations
        - Automated scenario optimization
        - Regulatory compliance checking
        - Real-time market condition integration
        """)

if __name__ == "__main__":
    main()