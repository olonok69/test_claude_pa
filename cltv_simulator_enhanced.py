"""
Enhanced CLTV Simulator with AI Integration - FIXED VERSION

This Streamlit app enhances your existing CLTV simulator with AI-powered analysis.
It imports your existing CLTVCalculator and adds AI capabilities on top.

FIXES APPLIED:
1. Fixed tool calling method from __call__ to invoke
2. Fixed pandas styling from applymap to map
3. Improved error handling and user feedback
4. Clean chat message display
"""

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime
import numpy as np
import json
import os
import sys
from typing import Dict, Any, Optional

# Import your existing CLTV calculator
from cltv_simulator import CLTVCalculator

# Import AI agent components (with error handling)
try:
    from cltv_ai_agent import (
        create_cltv_agent,
        analyze_borrower_comprehensive,
        quick_loan_prequalification
    )
    AI_AVAILABLE = True
except ImportError as e:
    st.error(f"AI features not available: {e}")
    AI_AVAILABLE = False

try:
    from mortgage_tools import (
        calculate_pmi_analysis,
        analyze_debt_consolidation_impact,
        calculate_affordability_analysis
    )
    ADVANCED_TOOLS_AVAILABLE = True
except ImportError:
    ADVANCED_TOOLS_AVAILABLE = False

from langchain_core.messages import HumanMessage


class EnhancedCLTVCalculator(CLTVCalculator):
    """Enhanced CLTV Calculator with AI integration"""
    
    def __init__(self):
        super().__init__()
        if AI_AVAILABLE:
            try:
                self.ai_agent = create_cltv_agent()
                self.chat_config = {"configurable": {"thread_id": "enhanced_cltv"}}
                self.ai_enabled = True
            except Exception as e:
                st.warning(f"AI agent initialization failed: {e}")
                self.ai_enabled = False
        else:
            self.ai_enabled = False
    
    def get_ai_analysis(self, borrower_profile: Dict[str, Any]) -> str:
        """Get AI-powered analysis of borrower profile"""
        if not self.ai_enabled:
            return "AI analysis not available. Please check your configuration."
        
        try:
            analysis_prompt = f"""
            Provide comprehensive mortgage lending analysis for this borrower:
            
            Property Value: ${borrower_profile['property_value']:,.2f}
            Primary Loan: ${borrower_profile['primary_loan']:,.2f}
            Secondary Loans: {borrower_profile.get('secondary_loans', [])}
            Gross Income: ${borrower_profile.get('gross_income', 0):,.2f}
            Monthly Debts: ${borrower_profile.get('monthly_debts', 0):,.2f}
            Credit Score: {borrower_profile.get('credit_score', 'Not provided')}
            Down Payment: ${borrower_profile.get('down_payment', 0):,.2f}
            
            Use all available tools to provide:
            1. CLTV risk assessment
            2. DTI qualification analysis  
            3. Comprehensive borrower score
            4. Final lending recommendation
            """
            
            result = self.ai_agent.invoke(
                {"messages": [HumanMessage(content=analysis_prompt)]},
                self.chat_config
            )
            return result["messages"][-1].content
            
        except Exception as e:
            return f"AI Analysis Error: {str(e)}"


def main():
    st.set_page_config(
        page_title="Enhanced CLTV Simulator with AI",
        page_icon="🤖",
        layout="wide"
    )
    
    # Custom CSS for better styling and comprehensive font/rendering fixes
    st.markdown("""
    <style>
    /* Reset and normalize all fonts */
    * {
        font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Roboto', 'Oxygen', 'Ubuntu', 'Cantarell', 'Open Sans', 'Helvetica Neue', sans-serif !important;
        font-variant-ligatures: none !important;
        font-feature-settings: normal !important;
        text-rendering: optimizeLegibility !important;
        -webkit-font-smoothing: antialiased !important;
        -moz-osx-font-smoothing: grayscale !important;
    }
    
    /* Global app styling */
    .stApp {
        font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Roboto', 'Oxygen', 'Ubuntu', 'Cantarell', 'Open Sans', 'Helvetica Neue', sans-serif !important;
    }
    
    /* Fix chat messages specifically */
    .stChatMessage {
        font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Roboto', 'Oxygen', 'Ubuntu', 'Cantarell', 'Open Sans', 'Helvetica Neue', sans-serif !important;
    }
    
    .stChatMessage [data-testid="chatAvatarIcon-user"],
    .stChatMessage [data-testid="chatAvatarIcon-assistant"] {
        font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Roboto', 'Oxygen', 'Ubuntu', 'Cantarell', 'Open Sans', 'Helvetica Neue', sans-serif !important;
    }
    
    /* Fix all markdown content */
    .stMarkdown, .stMarkdown * {
        font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Roboto', 'Oxygen', 'Ubuntu', 'Cantarell', 'Open Sans', 'Helvetica Neue', sans-serif !important;
        font-variant-ligatures: none !important;
        font-feature-settings: normal !important;
        letter-spacing: normal !important;
        word-spacing: normal !important;
    }
    
    /* Fix markdown containers */
    div[data-testid="stMarkdownContainer"], 
    div[data-testid="stMarkdownContainer"] * {
        font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Roboto', 'Oxygen', 'Ubuntu', 'Cantarell', 'Open Sans', 'Helvetica Neue', sans-serif !important;
        font-variant-ligatures: none !important;
        font-feature-settings: normal !important;
        letter-spacing: normal !important;
        word-spacing: normal !important;
        line-height: 1.5 !important;
    }
    
    /* Fix code blocks to use monospace only where appropriate */
    code, pre {
        font-family: 'Consolas', 'Monaco', 'Courier New', monospace !important;
        font-variant-ligatures: none !important;
    }
    
    /* Custom component styles */
    .main-header {
        background: linear-gradient(90deg, #1f4e79 0%, #2e8b57 100%);
        padding: 1rem;
        border-radius: 10px;
        margin-bottom: 2rem;
        color: white;
        font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Roboto', 'Oxygen', 'Ubuntu', 'Cantarell', 'Open Sans', 'Helvetica Neue', sans-serif !important;
    }
    
    .metric-card {
        background-color: #f8f9fa;
        padding: 1rem;
        border-radius: 8px;
        border-left: 4px solid #2e8b57;
        margin-bottom: 0.5rem;
        font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Roboto', 'Oxygen', 'Ubuntu', 'Cantarell', 'Open Sans', 'Helvetica Neue', sans-serif !important;
    }
    
    .ai-section {
        background-color: #e8f4fd;
        padding: 1.5rem;
        border-radius: 10px;
        border: 2px solid #1f4e79;
        margin: 1rem 0;
        font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Roboto', 'Oxygen', 'Ubuntu', 'Cantarell', 'Open Sans', 'Helvetica Neue', sans-serif !important;
    }
    
    .warning-box {
        background-color: #fff3cd;
        border: 1px solid #ffeaa7;
        padding: 1rem;
        border-radius: 8px;
        margin: 1rem 0;
        font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Roboto', 'Oxygen', 'Ubuntu', 'Cantarell', 'Open Sans', 'Helvetica Neue', sans-serif !important;
    }
    
    /* Fix specific Streamlit components */
    .stSelectbox label, .stNumberInput label, .stTextInput label, 
    .stRadio label, .stMultiSelect label, .stSlider label,
    .stButton button, .dataframe, .metric-container {
        font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Roboto', 'Oxygen', 'Ubuntu', 'Cantarell', 'Open Sans', 'Helvetica Neue', sans-serif !important;
        font-variant-ligatures: none !important;
        font-feature-settings: normal !important;
    }
    
    /* Override any remaining problematic styling */
    p, div, span, h1, h2, h3, h4, h5, h6, li, td, th {
        font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Roboto', 'Oxygen', 'Ubuntu', 'Cantarell', 'Open Sans', 'Helvetica Neue', sans-serif !important;
        font-variant-ligatures: none !important;
        font-feature-settings: normal !important;
        letter-spacing: normal !important;
        word-spacing: normal !important;
    }
    
    /* Specifically target chat messages and content */
    [data-testid="chatAvatarIcon-user"] + div,
    [data-testid="chatAvatarIcon-assistant"] + div {
        font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Roboto', 'Oxygen', 'Ubuntu', 'Cantarell', 'Open Sans', 'Helvetica Neue', sans-serif !important;
    }
    </style>
    """, unsafe_allow_html=True)
    
    # Header
    st.markdown("""
    <div class="main-header">
        <h1 style="margin: 0;">🤖 Enhanced CLTV Simulator with AI</h1>
        <p style="margin: 0; opacity: 0.9;">Advanced lending analysis with AI-powered insights</p>
    </div>
    """, unsafe_allow_html=True)
    
    # AI Status indicator
    if AI_AVAILABLE:
        st.success("✅ AI Features Available")
    else:
        st.markdown("""
        <div class="warning-box">
            <h4>⚠️ AI Features Unavailable</h4>
            <p>The AI analysis features are not available. You can still use the traditional CLTV calculator.</p>
            <p><strong>To enable AI features:</strong></p>
            <ol>
                <li>Ensure <code>cltv_ai_agent.py</code> is in the same directory</li>
                <li>Install required packages: <code>pip install langchain langgraph langchain-openai</code></li>
                <li>Set up your <code>.env</code> file with API keys</li>
            </ol>
        </div>
        """, unsafe_allow_html=True)
    
    # Initialize session state
    if 'calculator' not in st.session_state:
        st.session_state.calculator = EnhancedCLTVCalculator()
    
    # Sidebar navigation
    st.sidebar.header("🧭 Navigation")
    
    if AI_AVAILABLE:
        analysis_modes = [
            "🏠 Traditional CLTV", 
            "🤖 AI Analysis", 
            "💬 AI Chat", 
            "🔍 Advanced Tools"
        ]
    else:
        analysis_modes = ["🏠 Traditional CLTV"]
    
    analysis_mode = st.sidebar.radio("Select Analysis Mode", analysis_modes)
    
    # Environment info in sidebar
    st.sidebar.header("🔧 System Status")
    st.sidebar.write(f"AI Available: {'✅' if AI_AVAILABLE else '❌'}")
    st.sidebar.write(f"Advanced Tools: {'✅' if ADVANCED_TOOLS_AVAILABLE else '❌'}")
    
    # Main content based on selected mode
    if analysis_mode == "🏠 Traditional CLTV":
        render_traditional_analysis()
    elif analysis_mode == "🤖 AI Analysis" and AI_AVAILABLE:
        render_ai_analysis()
    elif analysis_mode == "💬 AI Chat" and AI_AVAILABLE:
        render_chat_interface()
    elif analysis_mode == "🔍 Advanced Tools" and ADVANCED_TOOLS_AVAILABLE:
        render_advanced_tools()


def render_traditional_analysis():
    """Render the traditional CLTV analysis interface"""
    st.header("🏠 Traditional CLTV Analysis")
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.subheader("📝 Property & Loan Information")
        
        # Property details
        property_value = st.number_input(
            "Property Value ($)",
            min_value=1000,
            value=500000,
            step=10000,
            format="%d"
        )
        
        down_payment = st.number_input(
            "Down Payment ($)",
            min_value=0,
            value=100000,
            step=5000,
            format="%d"
        )
        
        primary_loan = property_value - down_payment
        st.info(f"Primary Loan Amount: ${primary_loan:,.0f}")
        
        # Secondary loans
        st.subheader("Additional Loans")
        num_additional = st.selectbox("Number of Additional Loans", [0, 1, 2, 3, 4])
        
        calculator = st.session_state.calculator
        calculator.set_property_value(property_value)
        calculator.loans = []  # Reset loans
        calculator.add_loan("Primary Mortgage", primary_loan, 6.5)
        
        secondary_total = 0
        secondary_loans = []
        
        for i in range(num_additional):
            loan_name = st.text_input(f"Loan {i+1} Name", value=f"HELOC/Second {i+1}", key=f"name_{i}")
            loan_balance = st.number_input(f"Loan {i+1} Balance ($)", min_value=0, value=25000, step=1000, key=f"balance_{i}")
            loan_rate = st.number_input(f"Loan {i+1} Rate (%)", min_value=0.0, value=7.5, step=0.1, key=f"rate_{i}")
            
            if loan_balance > 0:
                calculator.add_loan(loan_name, loan_balance, loan_rate)
                secondary_total += loan_balance
                secondary_loans.append(loan_balance)
    
    with col2:
        st.subheader("📊 Current Metrics")
        
        # Calculate metrics
        cltv_ratio = calculator.calculate_cltv()
        ltv_ratio = calculator.calculate_ltv(primary_loan)
        available_equity = calculator.calculate_available_equity()
        risk_level, risk_description = calculator.get_risk_assessment(cltv_ratio)
        
        # Display metrics in cards
        st.markdown('<div class="metric-card">', unsafe_allow_html=True)
        st.metric("Primary LTV", f"{ltv_ratio:.1f}%", delta=f"{ltv_ratio-80:.1f}% vs 80%")
        st.markdown('</div>', unsafe_allow_html=True)
        
        st.markdown('<div class="metric-card">', unsafe_allow_html=True)
        st.metric("Combined CLTV", f"{cltv_ratio:.1f}%", delta=f"{cltv_ratio-80:.1f}% vs 80%")
        st.markdown('</div>', unsafe_allow_html=True)
        
        st.markdown('<div class="metric-card">', unsafe_allow_html=True)
        st.metric("Available Equity", f"${available_equity:,.0f}")
        st.markdown('</div>', unsafe_allow_html=True)
        
        # Risk assessment
        if cltv_ratio <= 65:
            risk_color = "green"
        elif cltv_ratio <= 80:
            risk_color = "orange"
        else:
            risk_color = "red"
        
        st.markdown(f'<div class="metric-card"><h4 style="color: {risk_color};">{risk_level}</h4><p>{risk_description}</p></div>', unsafe_allow_html=True)
        
        # AI Analysis button (if available)
        if AI_AVAILABLE and st.button("🤖 Get AI Analysis", type="primary"):
            with st.spinner("Running AI analysis..."):
                borrower_profile = {
                    'property_value': property_value,
                    'primary_loan': primary_loan,
                    'secondary_loans': secondary_loans,
                    'down_payment': down_payment
                }
                ai_result = calculator.get_ai_analysis(borrower_profile)
                
                st.subheader("🤖 AI Analysis Results")
                st.markdown(ai_result)
    
    # Visualization
    st.subheader("📈 CLTV Risk Visualization")
    
    col1, col2 = st.columns(2)
    
    with col1:
        # CLTV Gauge
        fig_gauge = go.Figure(go.Indicator(
            mode="gauge+number+delta",
            value=cltv_ratio,
            domain={'x': [0, 1], 'y': [0, 1]},
            title={'text': "CLTV %", 'font': {'size': 20}},
            delta={'reference': 80, 'increasing': {'color': "red"}, 'decreasing': {'color': "green"}},
            gauge={
                'axis': {'range': [None, 100], 'tickwidth': 1, 'tickcolor': "darkblue"},
                'bar': {'color': "darkblue"},
                'bgcolor': "white",
                'borderwidth': 2,
                'bordercolor': "gray",
                'steps': [
                    {'range': [0, 65], 'color': 'lightgreen'},
                    {'range': [65, 75], 'color': 'yellow'},
                    {'range': [75, 80], 'color': 'orange'},
                    {'range': [80, 95], 'color': 'lightcoral'},
                    {'range': [95, 100], 'color': 'red'}
                ],
                'threshold': {
                    'line': {'color': "red", 'width': 4},
                    'thickness': 0.75,
                    'value': 80
                }
            }
        ))
        fig_gauge.update_layout(height=300, margin=dict(l=20, r=20, t=40, b=20))
        st.plotly_chart(fig_gauge, use_container_width=True)
    
    with col2:
        # Loan breakdown pie chart
        if calculator.loans:
            loan_data = []
            for loan in calculator.loans:
                loan_data.append({
                    'Loan': loan['name'],
                    'Amount': loan['balance']
                })
            
            df_loans = pd.DataFrame(loan_data)
            
            fig_pie = px.pie(
                df_loans, 
                values='Amount', 
                names='Loan',
                title="Loan Distribution",
                color_discrete_sequence=px.colors.qualitative.Set3
            )
            fig_pie.update_layout(height=300, margin=dict(l=20, r=20, t=40, b=20))
            st.plotly_chart(fig_pie, use_container_width=True)
    
    # Scenario Analysis (from your original)
    render_scenario_analysis(calculator, property_value)


def render_ai_analysis():
    """Render the AI-powered analysis interface"""
    st.header("🤖 AI-Powered Mortgage Analysis")
    
    st.markdown("""
    <div class="ai-section">
        <h3>🧠 Intelligent Lending Analysis</h3>
        <p>Get comprehensive borrower risk assessment using advanced AI models that analyze multiple lending factors simultaneously.</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Input form
    with st.form("ai_analysis_form"):
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("🏠 Property Information")
            property_value = st.number_input("Property Value ($)", value=500000, step=10000)
            down_payment = st.number_input("Down Payment ($)", value=100000, step=5000)
            primary_loan = property_value - down_payment
            st.info(f"Primary Loan Amount: ${primary_loan:,.0f}")
            
            # Secondary loans
            num_secondary = st.number_input("Number of Secondary Loans", min_value=0, max_value=5, value=1)
            secondary_loans = []
            for i in range(int(num_secondary)):
                loan_amt = st.number_input(f"Secondary Loan {i+1} ($)", value=25000, step=1000, key=f"sec_loan_{i}")
                if loan_amt > 0:
                    secondary_loans.append(loan_amt)
        
        with col2:
            st.subheader("👤 Borrower Profile")
            gross_income = st.number_input("Gross Monthly Income ($)", value=8000, step=100)
            monthly_debts = st.number_input("Monthly Debt Payments ($)", value=800, step=50)
            credit_score = st.number_input("Credit Score", min_value=300, max_value=850, value=740, step=10)
            employment_years = st.number_input("Years of Employment", value=3.5, step=0.5)
            liquid_assets = st.number_input("Liquid Assets ($)", value=50000, step=5000)
            loan_type = st.selectbox("Loan Type", ["conventional", "fha", "va", "usda"])
        
        # Analysis type
        st.subheader("📊 Analysis Type")
        analysis_type = st.radio(
            "Select Analysis Level",
            ["Quick Prequalification", "Comprehensive Analysis"]
        )
        
        submitted = st.form_submit_button("🚀 Run AI Analysis", type="primary")
    
    if submitted:
        with st.spinner("🤖 AI is analyzing the borrower profile..."):
            try:
                # Estimate housing payment
                monthly_rate = 0.065 / 12
                n_payments = 360
                if primary_loan > 0:
                    pi_payment = primary_loan * (monthly_rate * (1 + monthly_rate)**n_payments) / ((1 + monthly_rate)**n_payments - 1)
                    estimated_housing_payment = pi_payment * 1.3  # Add taxes, insurance
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
                else:  # Comprehensive Analysis
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
                
                # Display results
                st.success("✅ Analysis Complete!")
                st.markdown(result)
                
            except Exception as e:
                st.error(f"❌ Analysis failed: {str(e)}")
                st.info("Please check your AI configuration and try again.")


def clean_user_input(text: str) -> str:
    """
    Clean user input to prevent text formatting issues and ensure proper spacing.
    
    Args:
        text (str): Raw user input text
        
    Returns:
        str: Cleaned and properly formatted text
    """
    import re
    
    # Remove any problematic characters or formatting
    cleaned = text.strip()
    
    # Fix common number formatting issues (add spaces after commas in numbers)
    cleaned = re.sub(r'(\d),(\d)', r'\1, \2', cleaned)
    
    # Fix missing spaces after periods
    cleaned = re.sub(r'\.([A-Z])', r'. \1', cleaned)
    
    # Fix missing spaces after common abbreviations and numbers
    cleaned = re.sub(r'(\d)([A-Za-z])', r'\1 \2', cleaned)
    
    # Fix missing spaces before monetary amounts
    cleaned = re.sub(r'([A-Za-z])(\$\d)', r'\1 \2', cleaned)
    
    # Ensure proper spacing around common financial terms
    financial_terms = [
        'homepurchase', 'monthlyincome', 'carpayment', 'downpayment',
        'creditcards', 'studentloans', 'creditScore', 'monthlyincome'
    ]
    
    for term in financial_terms:
        # Add spaces around concatenated financial terms
        pattern = r'(\d)(' + term + r')'
        cleaned = re.sub(pattern, r'\1 \2', cleaned, flags=re.IGNORECASE)
        
        pattern = r'(' + term + r')(\d)'
        cleaned = re.sub(pattern, r'\1 \2', cleaned, flags=re.IGNORECASE)
    
    # Clean up multiple spaces
    cleaned = re.sub(r'\s+', ' ', cleaned)
    
    return cleaned.strip()


def render_chat_interface():
    """Render the AI chat interface"""
    st.header("💬 AI Mortgage Lending Assistant")
    
    st.markdown("""
    <div class="ai-section">
        <h3>🗣️ Chat with an AI Lending Expert</h3>
        <p>Ask questions about CLTV, DTI, loan qualification, mortgage products, or get personalized lending advice.</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Initialize chat history
    if "chat_messages" not in st.session_state:
        st.session_state.chat_messages = [
            {"role": "assistant", "content": "Hello! I'm your AI mortgage lending assistant. I can help you with CLTV analysis, DTI calculations, loan qualification assessments, and provide lending recommendations. What would you like to know?"}
        ]
    
    # Display chat messages with clean formatting
    for message in st.session_state.chat_messages:
        with st.chat_message(message["role"]):
            if message["role"] == "user":
                # Use st.write for user messages to ensure proper text rendering
                st.write(message["content"])
            else:
                # Use st.markdown for AI responses to maintain formatting
                st.markdown(message["content"])
    
    # Chat input
    if prompt := st.chat_input("Ask me about mortgage lending, CLTV, DTI, or loan qualification..."):
        # Clean and format the user input to prevent text formatting issues
        cleaned_prompt = clean_user_input(prompt)
        
        # Add user message
        st.session_state.chat_messages.append({"role": "user", "content": cleaned_prompt})
        with st.chat_message("user"):
            # Use proper text formatting for user messages
            st.write(cleaned_prompt)
        
        # Generate AI response
        with st.chat_message("assistant"):
            with st.spinner("🤖 Thinking..."):
                try:
                    calculator = st.session_state.calculator
                    if calculator.ai_enabled:
                        # Use the original prompt for AI processing, but cleaned prompt for display
                        result = calculator.ai_agent.invoke(
                            {"messages": [HumanMessage(content=prompt)]},  # Original for AI
                            calculator.chat_config
                        )
                        response = result["messages"][-1].content
                        st.markdown(response)
                        st.session_state.chat_messages.append({"role": "assistant", "content": response})
                    else:
                        error_msg = "AI chat is not available. Please check your configuration."
                        st.error(error_msg)
                        st.session_state.chat_messages.append({"role": "assistant", "content": error_msg})
                    
                except Exception as e:
                    error_msg = f"I apologize, but I encountered an error: {str(e)}"
                    st.error(error_msg)
                    st.session_state.chat_messages.append({"role": "assistant", "content": error_msg})
    
    # Clear chat button
    if st.sidebar.button("🗑️ Clear Chat History"):
        st.session_state.chat_messages = [
            {"role": "assistant", "content": "Chat cleared! How can I help you with mortgage lending analysis?"}
        ]
        st.rerun()
    
    # Sidebar with example prompts
    with st.sidebar:
        st.subheader("💡 Example Questions")
        
        example_prompts = [
            "What's a good CLTV ratio for conventional loans?",
            "Calculate DTI for $6K income, $1K debts, $2.5K housing",
            "What are PMI requirements and costs?",
            "How does credit score affect loan approval?",
            "What's the difference between LTV and CLTV?"
        ]
        
        for prompt in example_prompts:
            if st.button(prompt, key=f"example_{hash(prompt)}", use_container_width=True):
                st.session_state.chat_messages.append({"role": "user", "content": prompt})
                st.rerun()


def render_advanced_tools():
    """Render advanced lending analysis tools"""
    st.header("🔍 Advanced Lending Analysis Tools")
    
    tool_selection = st.selectbox(
        "Select Analysis Tool",
        [
            "PMI Analysis & Calculation",
            "Debt Consolidation Impact",
            "Home Affordability Calculator"
        ]
    )
    
    if tool_selection == "PMI Analysis & Calculation":
        render_pmi_tool()
    elif tool_selection == "Debt Consolidation Impact":
        render_debt_consolidation_tool()
    elif tool_selection == "Home Affordability Calculator":
        render_affordability_tool()


def render_pmi_tool():
    """Render PMI analysis tool - FIXED VERSION"""
    st.subheader("🏠 PMI Analysis & Calculation")
    
    col1, col2 = st.columns(2)
    
    with col1:
        loan_amount = st.number_input("Loan Amount ($)", value=400000, step=5000)
        property_value = st.number_input("Property Value ($)", value=500000, step=10000)
        credit_score = st.number_input("Credit Score", min_value=300, max_value=850, value=740)
        loan_type = st.selectbox("Loan Type", ["conventional", "fha", "va"])
    
    with col2:
        if st.button("📊 Calculate PMI", type="primary"):
            with st.spinner("Calculating PMI requirements..."):
                try:
                    # FIXED: Use invoke instead of __call__
                    result = calculate_pmi_analysis.invoke({
                        "loan_amount": loan_amount,
                        "property_value": property_value,
                        "credit_score": credit_score,
                        "loan_type": loan_type
                    })
                    st.markdown(result)
                except Exception as e:
                    st.error(f"PMI calculation failed: {str(e)}")
                    # Provide fallback calculation
                    ltv = (loan_amount / property_value) * 100
                    st.info(f"Basic calculation: LTV = {ltv:.1f}%. PMI required: {'Yes' if ltv > 80 else 'No'}")


def render_debt_consolidation_tool():
    """Render debt consolidation analysis tool - FIXED VERSION"""
    st.subheader("💳 Debt Consolidation Impact Analysis")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.write("**Current Debt Situation:**")
        current_payments = st.number_input("Current Monthly Debt Payments ($)", value=1200, step=50)
        debt_balances = st.text_area(
            "Current Debt Balances (JSON format)", 
            value='[15000, 8000, 12000, 5000]',
            help="Enter debt balances as a JSON array, e.g., [15000, 8000, 12000]"
        )
        gross_income = st.number_input("Gross Monthly Income ($)", value=8000, step=100)
    
    with col2:
        st.write("**Consolidation Scenario:**")
        consolidation_amount = st.number_input("Amount to Consolidate ($)", value=40000, step=1000)
        new_payment = st.number_input("New Consolidated Payment ($)", value=800, step=50)
    
    if st.button("🔄 Analyze Consolidation Impact", type="primary"):
        with st.spinner("Analyzing debt consolidation impact..."):
            try:
                # FIXED: Use invoke instead of __call__
                result = analyze_debt_consolidation_impact.invoke({
                    "current_monthly_debts": current_payments,
                    "debt_balances": debt_balances,
                    "consolidation_amount": consolidation_amount,
                    "new_payment": new_payment,
                    "gross_monthly_income": gross_income
                })
                st.markdown(result)
            except Exception as e:
                st.error(f"Debt consolidation analysis failed: {str(e)}")
                # Provide fallback calculation
                current_dti = (current_payments / gross_income) * 100
                new_dti = (new_payment / gross_income) * 100
                savings = current_payments - new_payment
                st.info(f"Basic calculation: Current DTI = {current_dti:.1f}%, New DTI = {new_dti:.1f}%, Monthly Savings = ${savings:.0f}")


def render_affordability_tool():
    """Render home affordability calculator - FIXED VERSION"""
    st.subheader("🏠 Home Affordability Calculator")
    
    col1, col2 = st.columns(2)
    
    with col1:
        gross_income = st.number_input("Gross Monthly Income ($)", value=8000, step=100)
        monthly_debts = st.number_input("Monthly Debt Payments ($)", value=800, step=50)
        down_payment = st.number_input("Available Down Payment ($)", value=100000, step=5000)
    
    with col2:
        target_dti = st.slider("Target DTI Ratio (%)", min_value=25.0, max_value=50.0, value=36.0, step=0.5)
        interest_rate = st.number_input("Interest Rate (%)", value=6.5, step=0.1)
        loan_term = st.selectbox("Loan Term (years)", [15, 20, 25, 30], index=3)
    
    if st.button("💰 Calculate Affordability", type="primary"):
        with st.spinner("Calculating home affordability..."):
            try:
                # FIXED: Use invoke instead of __call__
                result = calculate_affordability_analysis.invoke({
                    "gross_monthly_income": gross_income,
                    "monthly_debt_payments": monthly_debts,
                    "down_payment_available": down_payment,
                    "target_dti": target_dti,
                    "interest_rate": interest_rate,
                    "loan_term": loan_term
                })
                st.markdown(result)
            except Exception as e:
                st.error(f"Affordability calculation failed: {str(e)}")
                # Provide fallback calculation
                max_payment = gross_income * (target_dti / 100) - monthly_debts
                st.info(f"Basic calculation: Maximum housing payment = ${max_payment:.0f}")


def render_scenario_analysis(calculator: CLTVCalculator, property_value: float):
    """Render scenario analysis from your original simulator - FIXED VERSION"""
    st.header("📊 Scenario Analysis")
    
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
        available_equity = calculator.calculate_available_equity()
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
        
        # FIXED: Use map instead of applymap (deprecated)
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
        
        # Apply styling using the modern method
        styled_df = scenarios_df.style.map(color_cltv, subset=['CLTV (%)'])
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


if __name__ == "__main__":
    main()