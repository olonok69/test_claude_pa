"""
CLTV AI Agent - Advanced Mortgage and Lending Analysis System

This script implements an intelligent lending assistant using LangGraph that helps mortgage 
and lending professionals analyze borrower risk using multiple financial metrics:

1. Combined Loan-to-Value (CLTV) Analysis
2. Debt-to-Income (DTI) Ratio Assessment  
3. Payment-to-Income (PTI) Analysis
4. Loan Qualification Scoring System
5. PMI and Risk Assessment Tools

The agent provides comprehensive analysis by:
- Calculating risk scores based on multiple lending metrics
- Providing actionable recommendations for loan officers
- Comparing borrower profiles against lending standards
- Generating detailed risk assessments and approval recommendations

Scoring System:
+80 to +100: Excellent Borrower (Prime lending candidate)
+60 to +80: Good Borrower (Standard approval likely)  
+40 to +60: Fair Borrower (Conditional approval possible)
+20 to +40: Marginal Borrower (High scrutiny required)
0 to +20: Poor Borrower (Likely denial)
-100 to 0: High Risk (Definite denial recommended)
"""

import os
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Annotated, Dict, List, Optional, Tuple, Union
from typing_extensions import TypedDict
from dataclasses import dataclass

# LangGraph and LangChain imports
from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages
from langgraph.prebuilt import ToolNode, tools_condition
from langgraph.checkpoint.memory import MemorySaver
from langchain_core.messages import BaseMessage, HumanMessage, ToolMessage, AIMessage
from langchain_core.tools import tool

# Model imports - conditional based on provider
try:
    from langchain_openai import ChatOpenAI
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False

try:
    from langchain_google_vertexai import ChatVertexAI
    VERTEXAI_AVAILABLE = True
except ImportError:
    VERTEXAI_AVAILABLE = False

# Environment setup
from dotenv import load_dotenv
load_dotenv()

# Model configuration
MODEL_PROVIDER = os.getenv("MODEL_PROVIDER", "openai").lower()

# Borrower profile data structure
@dataclass
class BorrowerProfile:
    """Comprehensive borrower profile for lending analysis"""
    gross_monthly_income: float
    monthly_debt_payments: float
    property_value: float
    primary_loan_amount: float
    secondary_loans: List[Dict[str, float]]  # [{'balance': amount, 'payment': monthly_payment}]
    down_payment: float
    credit_score: int
    employment_years: float
    liquid_assets: float
    property_type: str = "primary_residence"  # primary_residence, investment, second_home
    loan_purpose: str = "purchase"  # purchase, refinance, cash_out_refinance

# State definition for LangGraph
class State(TypedDict):
    messages: Annotated[list[BaseMessage], add_messages]

def get_llm():
    """Get the appropriate LLM based on MODEL_PROVIDER"""
    if MODEL_PROVIDER == "openai" and OPENAI_AVAILABLE:
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise ValueError("OPENAI_API_KEY not found in environment variables")
        return ChatOpenAI(
            model="gpt-4o-mini",
            temperature=0.1,
            api_key=api_key
        )
    elif MODEL_PROVIDER == "vertexai" and VERTEXAI_AVAILABLE:
        project = os.getenv("GOOGLE_CLOUD_PROJECT")
        if not project:
            raise ValueError("GOOGLE_CLOUD_PROJECT not found in environment variables")
        return ChatVertexAI(
            model_name="gemini-2.0-flash-001",
            temperature=0.1,
            project=project
        )
    else:
        raise ValueError(f"Unsupported MODEL_PROVIDER: {MODEL_PROVIDER}")

# Lending Analysis Tools
# CLTV Analysis
@tool
def calculate_cltv_analysis(
    property_value: float,
    primary_loan_amount: float,
    secondary_loans: str = "[]",  # JSON string of secondary loans
    down_payment: float = 0.0
) -> str:
    """
    Calculate Combined Loan-to-Value (CLTV) ratio and provide risk assessment.
    
    CLTV includes all liens against the property (primary mortgage + secondary loans)
    Formula: CLTV = (Sum of all loans) / Property Value × 100
    
    Parameters:
    property_value (float): Current property value
    primary_loan_amount (float): Primary mortgage amount
    secondary_loans (str): JSON string of secondary loan amounts [amount1, amount2, ...]
    down_payment (float): Down payment amount (for purchase loans)
    
    Returns:
    str: Detailed CLTV analysis with risk assessment
    """
    import json
    
    try:
        # Parse secondary loans
        if isinstance(secondary_loans, str):
            secondary_loan_list = json.loads(secondary_loans) if secondary_loans.strip() else []
        else:
            secondary_loan_list = secondary_loans if isinstance(secondary_loans, list) else []
        
        # Calculate total debt
        total_debt = primary_loan_amount + sum(secondary_loan_list)
        
        # Calculate LTV and CLTV
        ltv = (primary_loan_amount / property_value) * 100 if property_value > 0 else 0
        cltv = (total_debt / property_value) * 100 if property_value > 0 else 0
        
        # Calculate equity
        equity = property_value - total_debt
        equity_percentage = (equity / property_value) * 100 if property_value > 0 else 0
        
        # Risk assessment based on CLTV thresholds
        if cltv <= 65:
            risk_level = "Excellent"
            risk_description = "Prime borrower - best rates available"
            risk_score = 90
        elif cltv <= 75:
            risk_level = "Good" 
            risk_description = "Standard lending terms"
            risk_score = 75
        elif cltv <= 80:
            risk_level = "Acceptable"
            risk_description = "Standard approval threshold"
            risk_score = 60
        elif cltv <= 85:
            risk_level = "Elevated"
            risk_description = "May require PMI, higher rates"
            risk_score = 40
        elif cltv <= 95:
            risk_level = "High"
            risk_description = "Limited lending options"
            risk_score = 20
        else:
            risk_level = "Very High"
            risk_description = "Underwater/High risk position"
            risk_score = 5
        
        # PMI requirement
        pmi_required = ltv > 80 and down_payment > 0
        
        result = f"""
📊 CLTV ANALYSIS REPORT
=======================

💰 LOAN DETAILS:
• Property Value: ${property_value:,.2f}
• Primary Loan: ${primary_loan_amount:,.2f}
• Secondary Loans: ${sum(secondary_loan_list):,.2f}
• Total Debt: ${total_debt:,.2f}
• Down Payment: ${down_payment:,.2f}

📈 RATIOS:
• LTV (Primary): {ltv:.2f}%
• CLTV (Combined): {cltv:.2f}%
• Equity: ${equity:,.2f} ({equity_percentage:.1f}%)

⚖️ RISK ASSESSMENT:
• Risk Level: {risk_level}
• Risk Score: {risk_score}/100
• Description: {risk_description}
• PMI Required: {"Yes" if pmi_required else "No"}

📋 LENDING IMPLICATIONS:
• Conventional Loan Approval: {"✅ Likely" if cltv <= 80 else "⚠️ Conditional" if cltv <= 95 else "❌ Unlikely"}
• FHA Eligibility: {"✅ Yes" if cltv <= 96.5 else "❌ No"}
• VA Loan (if applicable): {"✅ Yes" if cltv <= 100 else "❌ No"}
• Jumbo Loan Approval: {"✅ Likely" if cltv <= 75 else "⚠️ Conditional" if cltv <= 80 else "❌ Unlikely"}

💡 RECOMMENDATIONS:
{_generate_cltv_recommendations(cltv, ltv, equity_percentage)}
        """
        
        return result.strip()
        
    except Exception as e:
        return f"Error calculating CLTV: {str(e)}"
# Calculate Debt-to-Income (DTI) ratios and assess loan qualification

@tool
def calculate_dti_analysis(
    gross_monthly_income: float,
    monthly_debt_payments: float,
    proposed_housing_payment: float,
    loan_type: str = "conventional"
) -> str:
    """
    Calculate Debt-to-Income (DTI) ratios and assess loan qualification.
    
    Calculates both front-end (housing only) and back-end (total debt) DTI ratios.
    
    Parameters:
    gross_monthly_income (float): Borrower's gross monthly income
    monthly_debt_payments (float): Total monthly debt payments (excluding housing)
    proposed_housing_payment (float): Proposed monthly housing payment (PITI)
    loan_type (str): Type of loan (conventional, fha, va, usda)
    
    Returns:
    str: Detailed DTI analysis with qualification assessment
    """
    
    try:
        # Calculate DTI ratios
        front_end_dti = (proposed_housing_payment / gross_monthly_income) * 100
        back_end_dti = ((proposed_housing_payment + monthly_debt_payments) / gross_monthly_income) * 100
        
        # DTI thresholds by loan type
        dti_limits = {
            "conventional": {"front_end": 28, "back_end": 36, "max_back_end": 45},
            "fha": {"front_end": 31, "back_end": 43, "max_back_end": 57},
            "va": {"front_end": 41, "back_end": 41, "max_back_end": 41},
            "usda": {"front_end": 29, "back_end": 41, "max_back_end": 41}
        }
        
        limits = dti_limits.get(loan_type.lower(), dti_limits["conventional"])
        
        # Qualification assessment
        front_end_status = "✅ Qualified" if front_end_dti <= limits["front_end"] else "❌ Exceeds Limit"
        back_end_status = (
            "✅ Qualified" if back_end_dti <= limits["back_end"] 
            else "⚠️ Compensating Factors Needed" if back_end_dti <= limits["max_back_end"]
            else "❌ Exceeds Maximum"
        )
        
        # Score calculation (0-100)
        front_end_score = max(0, 100 - (front_end_dti - limits["front_end"]) * 2)
        back_end_score = max(0, 100 - (back_end_dti - limits["back_end"]) * 2)
        overall_score = (front_end_score + back_end_score) / 2
        
        # Remaining income analysis
        remaining_income = gross_monthly_income - proposed_housing_payment - monthly_debt_payments
        remaining_percentage = (remaining_income / gross_monthly_income) * 100
        
        result = f"""
📊 DEBT-TO-INCOME ANALYSIS
==========================

💰 INCOME & PAYMENTS:
• Gross Monthly Income: ${gross_monthly_income:,.2f}
• Monthly Debt Payments: ${monthly_debt_payments:,.2f}
• Proposed Housing Payment: ${proposed_housing_payment:,.2f}
• Remaining Income: ${remaining_income:,.2f} ({remaining_percentage:.1f}%)

📈 DTI RATIOS ({loan_type.upper()} Loan):
• Front-End DTI: {front_end_dti:.2f}% (Limit: {limits["front_end"]}%) - {front_end_status}
• Back-End DTI: {back_end_dti:.2f}% (Limit: {limits["back_end"]}%) - {back_end_status}

⚖️ QUALIFICATION SCORE:
• Overall DTI Score: {overall_score:.1f}/100
• Front-End Score: {front_end_score:.1f}/100  
• Back-End Score: {back_end_score:.1f}/100

📋 LOAN QUALIFICATION:
• Conventional: {"✅ Qualified" if back_end_dti <= 36 else "⚠️ Manual Review" if back_end_dti <= 45 else "❌ Likely Denial"}
• FHA: {"✅ Qualified" if back_end_dti <= 43 else "⚠️ Compensating Factors" if back_end_dti <= 57 else "❌ Likely Denial"}
• VA: {"✅ Qualified" if back_end_dti <= 41 else "❌ Exceeds Guidelines"}
• USDA: {"✅ Qualified" if back_end_dti <= 41 else "❌ Exceeds Guidelines"}

💡 RECOMMENDATIONS:
{_generate_dti_recommendations(front_end_dti, back_end_dti, remaining_percentage, limits)}
        """
        
        return result.strip()
        
    except Exception as e:
        return f"Error calculating DTI: {str(e)}"
# This tool combines CLTV, DTI, credit score, employment history, and assets    to provide an overall lending recommendation.
@tool  
def calculate_comprehensive_borrower_score(
    property_value: float,
    primary_loan_amount: float,
    gross_monthly_income: float,
    monthly_debt_payments: float,
    proposed_housing_payment: float,
    credit_score: int,
    down_payment: float = 0.0,
    secondary_loans: str = "[]",
    employment_years: float = 2.0,
    liquid_assets: float = 0.0,
    loan_type: str = "conventional"
) -> str:
    """
    Generate a comprehensive borrower risk score combining multiple lending factors.
    
    This tool combines CLTV, DTI, credit score, employment history, and assets 
    to provide an overall lending recommendation.
    
    Parameters:
    property_value (float): Property value
    primary_loan_amount (float): Primary loan amount
    gross_monthly_income (float): Gross monthly income
    monthly_debt_payments (float): Monthly debt payments
    proposed_housing_payment (float): Proposed housing payment
    credit_score (int): Credit score (300-850)
    down_payment (float): Down payment amount
    secondary_loans (str): JSON string of secondary loan amounts
    employment_years (float): Years of employment history
    liquid_assets (float): Liquid assets/reserves
    loan_type (str): Loan type
    
    Returns:
    str: Comprehensive borrower analysis with final recommendation
    """
    
    try:
        import json
        
        # Parse secondary loans
        secondary_loan_list = json.loads(secondary_loans) if secondary_loans.strip() else []
        total_debt = primary_loan_amount + sum(secondary_loan_list)
        
        # Calculate key ratios
        cltv = (total_debt / property_value) * 100 if property_value > 0 else 0
        ltv = (primary_loan_amount / property_value) * 100 if property_value > 0 else 0
        front_end_dti = (proposed_housing_payment / gross_monthly_income) * 100
        back_end_dti = ((proposed_housing_payment + monthly_debt_payments) / gross_monthly_income) * 100
        
        # Calculate down payment percentage
        down_payment_pct = (down_payment / property_value) * 100 if property_value > 0 else 0
        
        # Calculate liquid assets in months of payments
        asset_months = liquid_assets / proposed_housing_payment if proposed_housing_payment > 0 else 0
        
        # Scoring components (each 0-100)
        
        # 1. CLTV Score (25% weight)
        if cltv <= 65: cltv_score = 100
        elif cltv <= 75: cltv_score = 85
        elif cltv <= 80: cltv_score = 70
        elif cltv <= 85: cltv_score = 50
        elif cltv <= 95: cltv_score = 25
        else: cltv_score = 0
        
        # 2. DTI Score (25% weight)  
        if back_end_dti <= 28: dti_score = 100
        elif back_end_dti <= 36: dti_score = 85
        elif back_end_dti <= 43: dti_score = 70
        elif back_end_dti <= 50: dti_score = 40
        else: dti_score = 0
        
        # 3. Credit Score (25% weight)
        if credit_score >= 780: credit_score_pts = 100
        elif credit_score >= 740: credit_score_pts = 90
        elif credit_score >= 680: credit_score_pts = 75
        elif credit_score >= 620: credit_score_pts = 60
        elif credit_score >= 580: credit_score_pts = 35
        else: credit_score_pts = 10
        
        # 4. Employment & Assets Score (15% weight)
        employment_score = min(100, employment_years * 25)  # 4+ years = 100
        asset_score = min(100, asset_months * 20)  # 5+ months = 100
        stability_score = (employment_score + asset_score) / 2
        
        # 5. Down Payment Score (10% weight)  
        if down_payment_pct >= 20: dp_score = 100
        elif down_payment_pct >= 10: dp_score = 75
        elif down_payment_pct >= 5: dp_score = 50
        elif down_payment_pct >= 3: dp_score = 25
        else: dp_score = 0
        
        # Calculate weighted final score
        final_score = (
            cltv_score * 0.25 + 
            dti_score * 0.25 + 
            credit_score_pts * 0.25 + 
            stability_score * 0.15 + 
            dp_score * 0.10
        )
        
        # Determine recommendation
        if final_score >= 80:
            recommendation = "STRONG APPROVAL"
            risk_level = "Low Risk"
            rate_tier = "Best Available Rates"
        elif final_score >= 65:
            recommendation = "APPROVAL LIKELY" 
            risk_level = "Low-Moderate Risk"
            rate_tier = "Standard Rates"
        elif final_score >= 50:
            recommendation = "CONDITIONAL APPROVAL"
            risk_level = "Moderate Risk" 
            rate_tier = "Above-Market Rates"
        elif final_score >= 35:
            recommendation = "MANUAL UNDERWRITING"
            risk_level = "High Risk"
            rate_tier = "Premium Rates"
        else:
            recommendation = "LIKELY DENIAL"
            risk_level = "Very High Risk"
            rate_tier = "N/A"
        
        # PMI and loan program assessment
        pmi_required = ltv > 80 and loan_type.lower() == "conventional"
        
        result = f"""
🎯 COMPREHENSIVE BORROWER ANALYSIS
==================================

📊 BORROWER PROFILE:
• Loan Amount: ${primary_loan_amount:,.2f}
• Property Value: ${property_value:,.2f}  
• Down Payment: ${down_payment:,.2f} ({down_payment_pct:.1f}%)
• Monthly Income: ${gross_monthly_income:,.2f}
• Monthly Debts: ${monthly_debt_payments:,.2f}
• Housing Payment: ${proposed_housing_payment:,.2f}
• Credit Score: {credit_score}
• Employment: {employment_years:.1f} years
• Liquid Assets: ${liquid_assets:,.2f} ({asset_months:.1f} months)

📈 KEY RATIOS:
• LTV: {ltv:.1f}%
• CLTV: {cltv:.1f}%  
• Front-End DTI: {front_end_dti:.1f}%
• Back-End DTI: {back_end_dti:.1f}%

🏆 SCORING BREAKDOWN:
• CLTV Score: {cltv_score:.0f}/100 (25% weight)
• DTI Score: {dti_score:.0f}/100 (25% weight)  
• Credit Score: {credit_score_pts:.0f}/100 (25% weight)
• Stability Score: {stability_score:.0f}/100 (15% weight)
• Down Payment Score: {dp_score:.0f}/100 (10% weight)

🎯 FINAL ASSESSMENT:
• Overall Score: {final_score:.1f}/100
• Recommendation: {recommendation}
• Risk Level: {risk_level}
• Expected Rate Tier: {rate_tier}
• PMI Required: {"Yes" if pmi_required else "No"}

💰 LOAN PROGRAM SUITABILITY:
• Conventional: {"✅ Excellent" if final_score >= 70 else "⚠️ Review Required" if final_score >= 50 else "❌ Poor Fit"}
• FHA: {"✅ Excellent" if final_score >= 60 else "⚠️ Review Required" if final_score >= 40 else "❌ Poor Fit"}
• VA (if eligible): {"✅ Excellent" if final_score >= 65 else "⚠️ Review Required" if final_score >= 45 else "❌ Poor Fit"}

💡 KEY RECOMMENDATIONS:
{_generate_comprehensive_recommendations(final_score, cltv, back_end_dti, credit_score, down_payment_pct)}
        """
        
        return result.strip()
        
    except Exception as e:
        return f"Error calculating comprehensive score: {str(e)}"

# compare_loan_scenarios  Analyzes different combinations of down payments and loan amounts to identify
# the best lending options for the borrower.
@tool
def compare_loan_scenarios(
    property_value: float,
    gross_monthly_income: float,
    monthly_debt_payments: float,
    credit_score: int,
    down_payment_amounts: str = "[50000, 75000, 100000]",
    loan_amounts: str = "[350000, 400000, 450000]"
) -> str:
    """
    Compare multiple loan scenarios to find optimal lending structure.
    
    Analyzes different combinations of down payments and loan amounts to identify
    the best lending options for the borrower.
    
    Parameters:
    property_value (float): Property value
    gross_monthly_income (float): Gross monthly income
    monthly_debt_payments (float): Monthly debt payments  
    credit_score (int): Credit score
    down_payment_amounts (str): JSON array of down payment amounts to compare
    loan_amounts (str): JSON array of loan amounts to compare
    
    Returns:
    str: Comparison analysis of different loan scenarios
    """
    
    try:
        import json
        
        down_payments = json.loads(down_payment_amounts)
        loan_amounts_list = json.loads(loan_amounts)
        
        scenarios = []
        
        for dp in down_payments:
            for loan_amt in loan_amounts_list:
                # Skip if loan + down payment doesn't equal property value
                if abs((loan_amt + dp) - property_value) > 1000:
                    continue
                    
                # Calculate estimated monthly payment (principal + interest only)
                # Using 6.5% rate estimate for comparison
                monthly_rate = 0.065 / 12
                n_payments = 360  # 30 years
                monthly_payment = loan_amt * (monthly_rate * (1 + monthly_rate)**n_payments) / ((1 + monthly_rate)**n_payments - 1)
                
                # Add estimated taxes, insurance, PMI
                annual_property_tax = property_value * 0.012  # 1.2% estimate
                annual_insurance = property_value * 0.003    # 0.3% estimate
                monthly_tax_ins = (annual_property_tax + annual_insurance) / 12
                
                # PMI if needed
                ltv = (loan_amt / property_value) * 100
                monthly_pmi = (loan_amt * 0.005 / 12) if ltv > 80 else 0  # 0.5% annually
                
                total_housing_payment = monthly_payment + monthly_tax_ins + monthly_pmi
                
                # Calculate ratios
                front_end_dti = (total_housing_payment / gross_monthly_income) * 100
                back_end_dti = ((total_housing_payment + monthly_debt_payments) / gross_monthly_income) * 100
                down_payment_pct = (dp / property_value) * 100
                
                # Simple approval likelihood
                if back_end_dti <= 36 and front_end_dti <= 28 and credit_score >= 620:
                    approval_likelihood = "High"
                elif back_end_dti <= 43 and front_end_dti <= 31 and credit_score >= 580:
                    approval_likelihood = "Moderate"
                else:
                    approval_likelihood = "Low"
                
                scenarios.append({
                    'loan_amount': loan_amt,
                    'down_payment': dp,
                    'down_payment_pct': down_payment_pct,
                    'ltv': ltv,
                    'monthly_payment': total_housing_payment,
                    'front_end_dti': front_end_dti,
                    'back_end_dti': back_end_dti,
                    'pmi_required': ltv > 80,
                    'monthly_pmi': monthly_pmi,
                    'approval_likelihood': approval_likelihood
                })
        
        # Sort by approval likelihood and DTI
        scenarios.sort(key=lambda x: (x['approval_likelihood'] == 'High', -x['back_end_dti']), reverse=True)
        
        result = f"""
🔄 LOAN SCENARIO COMPARISON
===========================

📋 ANALYZED SCENARIOS:
Property Value: ${property_value:,.2f}
Gross Monthly Income: ${gross_monthly_income:,.2f}
Monthly Debt Payments: ${monthly_debt_payments:,.2f}
Credit Score: {credit_score}

📊 SCENARIO RESULTS:

"""
        
        for i, scenario in enumerate(scenarios[:5], 1):  # Top 5 scenarios
            result += f"""
💰 SCENARIO {i}:
• Loan Amount: ${scenario['loan_amount']:,.2f}
• Down Payment: ${scenario['down_payment']:,.2f} ({scenario['down_payment_pct']:.1f}%)
• LTV: {scenario['ltv']:.1f}%
• Monthly Payment: ${scenario['monthly_payment']:,.2f}
• Front-End DTI: {scenario['front_end_dti']:.1f}%
• Back-End DTI: {scenario['back_end_dti']:.1f}%
• PMI Required: {"Yes" if scenario['pmi_required'] else "No"}
• PMI Amount: ${scenario['monthly_pmi']:,.2f}/month
• Approval Likelihood: {scenario['approval_likelihood']}
---
"""
        
        # Recommendations
        best_scenario = scenarios[0] if scenarios else None
        if best_scenario:
            result += f"""

🎯 RECOMMENDATIONS:

✅ OPTIMAL SCENARIO:
• Down Payment: ${best_scenario['down_payment']:,.2f} ({best_scenario['down_payment_pct']:.1f}%)
• Loan Amount: ${best_scenario['loan_amount']:,.2f}
• Monthly Payment: ${best_scenario['monthly_payment']:,.2f}
• This scenario provides the best balance of approval likelihood and manageable payments.

💡 ADDITIONAL INSIGHTS:
{_generate_scenario_recommendations(scenarios)}
"""
        
        return result.strip()
        
    except Exception as e:
        return f"Error comparing loan scenarios: {str(e)}"

# Helper functions for recommendations
# Generate CLTV-specific recommendations
def _generate_cltv_recommendations(cltv: float, ltv: float, equity_pct: float) -> str:
    """Generate CLTV-specific recommendations"""
    recommendations = []
    
    if cltv > 80:
        recommendations.append("• Consider increasing down payment to reduce CLTV below 80%")
        recommendations.append("• Expect PMI requirement and higher interest rates")
    
    if equity_pct < 20:
        recommendations.append("• Build additional equity before considering cash-out refinancing")
    
    if cltv > 95:
        recommendations.append("• Consider FHA loan if first-time buyer")
        recommendations.append("• VA loan may be option if veteran status qualifies")
    
    if not recommendations:
        recommendations.append("• Excellent CLTV position - eligible for best rates and terms")
        recommendations.append("• Consider this borrower for portfolio retention")
    
    return "\n".join(recommendations)

# Generate DTI-specific recommendations
def _generate_dti_recommendations(front_dti: float, back_dti: float, remaining_pct: float, limits: dict) -> str:
    """Generate DTI-specific recommendations"""
    recommendations = []
    
    if back_dti > limits["back_end"]:
        recommendations.append("• Consider reducing monthly debt obligations before applying")
        recommendations.append("• May need compensating factors for approval")
    
    if front_dti > limits["front_end"]:
        recommendations.append("• Consider lower loan amount or higher down payment")
    
    if remaining_pct < 15:
        recommendations.append("• Very tight budget - consider lower housing payment")
    
    if back_dti <= limits["back_end"] and front_dti <= limits["front_end"]:
        recommendations.append("• Excellent DTI ratios - strong approval candidate")
        recommendations.append("• Eligible for competitive rate pricing")
    
    return "\n".join(recommendations)

# Generate comprehensive recommendations based on overall score
def _generate_comprehensive_recommendations(score: float, cltv: float, dti: float, credit: int, dp_pct: float) -> str:
    """Generate comprehensive recommendations based on overall score"""
    recommendations = []
    
    if score >= 80:
        recommendations.append("• Excellent borrower profile - expedite processing")
        recommendations.append("• Offer best available rates and terms")
        recommendations.append("• Consider for portfolio loan retention")
    elif score >= 65:
        recommendations.append("• Strong borrower - standard approval process")
        recommendations.append("• Competitive rates available")
    elif score >= 50:
        recommendations.append("• Manual underwriting recommended")
        recommendations.append("• Gather compensating factors documentation")
        recommendations.append("• Consider rate adjustments for risk")
    else:
        recommendations.append("• High-risk profile - extensive documentation required")
        recommendations.append("• Consider alternative loan products")
    
    # Specific improvement suggestions
    if cltv > 80:
        recommendations.append("• Increase down payment to improve CLTV")
    if dti > 43:
        recommendations.append("• Pay down debt to improve DTI ratios")
    if credit < 680:
        recommendations.append("• Credit improvement may unlock better terms")
    
    return "\n".join(recommendations)

# Generate recommendations based on scenario comparison
def _generate_scenario_recommendations(scenarios: list) -> str:
    """Generate recommendations based on scenario comparison"""
    recommendations = []
    
    high_approval_scenarios = [s for s in scenarios if s['approval_likelihood'] == 'High']
    
    if len(high_approval_scenarios) > 1:
        recommendations.append("• Multiple viable options available")
        recommendations.append("• Consider borrower's cash flow preferences")
    elif len(high_approval_scenarios) == 1:
        recommendations.append("• Limited options - focus on optimal scenario")
    else:
        recommendations.append("• No high-approval scenarios - consider loan alternatives")
        recommendations.append("• May need to adjust property price range")
    
    # PMI considerations
    pmi_scenarios = [s for s in scenarios if s['pmi_required']]
    no_pmi_scenarios = [s for s in scenarios if not s['pmi_required']]
    
    if no_pmi_scenarios:
        recommendations.append("• PMI avoidance possible with sufficient down payment")
    elif pmi_scenarios:
        recommendations.append("• All scenarios require PMI - factor into monthly budget")
    
    return "\n".join(recommendations)

# LangGraph setup

def chatbot(state: State):
    """
    CLTV and Mortgage Lending AI Assistant
    
    This AI assistant specializes in comprehensive mortgage lending analysis, helping 
    loan officers and underwriters evaluate borrower risk using multiple metrics:
    
    1. Combined Loan-to-Value (CLTV) Analysis
    2. Debt-to-Income (DTI) Assessment
    3. Comprehensive Borrower Scoring
    4. Loan Scenario Comparisons
    5. Risk Assessment and Recommendations
    
    The assistant uses industry-standard lending guidelines and provides actionable
    insights for loan approval decisions, pricing, and risk management.
    
    Key Features:
    - Multi-factor risk scoring system
    - Compliance with lending regulations (QM, ATR)
    - Loan program suitability analysis
    - PMI and MI requirement assessment
    - Comparative scenario modeling
    """
    
    # Filter out any non-text messages
    text_messages = [
        msg for msg in state["messages"] 
        if not (hasattr(msg, 'content') and isinstance(msg.content, list))
    ]
    
    try:
        # Get the appropriate LLM instance
        current_llm = get_llm()
        current_llm_with_tools = current_llm.bind_tools(tools)
        
        # Invoke the model
        response = current_llm_with_tools.invoke(text_messages)
        return {"messages": [response]}
        
    except Exception as e:
        print(f"Error in chatbot: {e}")
        # Fallback message
        error_message = AIMessage(
            content=f"I apologize, but I encountered an error: {str(e)}. "
                   "Please try rephrasing your question or check your input parameters."
        )
        return {"messages": [error_message]}

# Available tools for the agent
tools = [
    calculate_cltv_analysis,
    calculate_dti_analysis,
    calculate_comprehensive_borrower_score,
    compare_loan_scenarios
]

def create_cltv_agent():
    """Create and return the compiled LangGraph agent"""
    
    graph_builder = StateGraph(State)
    
    # Add nodes
    graph_builder.add_node("chatbot", chatbot)
    tool_node = ToolNode(tools)
    graph_builder.add_node("tools", tool_node)
    
    # Add edges
    graph_builder.add_edge(START, "chatbot")
    graph_builder.add_edge("tools", "chatbot")
    graph_builder.add_conditional_edges(
        "chatbot",
        tools_condition,
        {"tools": "tools", "__end__": "__end__"},
    )
    
    # Compile with memory
    memory = MemorySaver()
    graph = graph_builder.compile(checkpointer=memory)
    
    return graph

# Main analysis functions

def analyze_borrower_comprehensive(
    property_value: float,
    primary_loan_amount: float,
    gross_monthly_income: float,
    monthly_debt_payments: float,
    proposed_housing_payment: float,
    credit_score: int,
    down_payment: float = 0.0,
    secondary_loans: List[float] = None,
    employment_years: float = 2.0,
    liquid_assets: float = 0.0,
    loan_type: str = "conventional"
) -> str:
    """
    Comprehensive borrower analysis using all available tools
    
    Parameters:
    property_value (float): Property value
    primary_loan_amount (float): Primary loan amount
    gross_monthly_income (float): Gross monthly income
    monthly_debt_payments (float): Monthly debt payments
    proposed_housing_payment (float): Proposed housing payment
    credit_score (int): Credit score
    down_payment (float): Down payment amount
    secondary_loans (List[float]): List of secondary loan amounts
    employment_years (float): Years of employment
    liquid_assets (float): Liquid assets
    loan_type (str): Type of loan
    
    Returns:
    str: Complete borrower analysis
    """
    
    graph = create_cltv_agent()
    config = {"configurable": {"thread_id": "cltv_analysis"}}
    
    secondary_loans_json = str(secondary_loans or [])
    
    analysis_request = f"""
    Please provide a comprehensive mortgage lending analysis for this borrower with the following requirements:

    1. **CLTV Analysis**: Use calculate_cltv_analysis with:
       - Property Value: ${property_value:,.2f}
       - Primary Loan: ${primary_loan_amount:,.2f}
       - Secondary Loans: {secondary_loans_json}
       - Down Payment: ${down_payment:,.2f}

    2. **DTI Analysis**: Use calculate_dti_analysis with:
       - Gross Monthly Income: ${gross_monthly_income:,.2f}
       - Monthly Debt Payments: ${monthly_debt_payments:,.2f}
       - Proposed Housing Payment: ${proposed_housing_payment:,.2f}
       - Loan Type: {loan_type}

    3. **Comprehensive Score**: Use calculate_comprehensive_borrower_score with all parameters

    4. **Final Recommendation**: Based on all analyses, provide:
       - Clear APPROVE/CONDITIONAL/DENY recommendation
       - Risk level assessment
       - Interest rate tier recommendation
       - Required documentation or conditions
       - Alternative loan product suggestions if needed

    Please provide detailed reasoning for your final lending recommendation.
    """
    
    result = graph.invoke(
        {"messages": [HumanMessage(content=analysis_request)]},
        config
    )
    
    return result["messages"][-1].content

def quick_loan_prequalification(
    property_value: float,
    down_payment: float,
    gross_monthly_income: float,
    monthly_debt_payments: float,
    credit_score: int
) -> str:
    """
    Quick loan prequalification analysis
    
    Parameters:
    property_value (float): Property value
    down_payment (float): Down payment amount
    gross_monthly_income (float): Gross monthly income  
    monthly_debt_payments (float): Monthly debt payments
    credit_score (int): Credit score
    
    Returns:
    str: Quick prequalification assessment
    """
    
    graph = create_cltv_agent()
    config = {"configurable": {"thread_id": "quick_prequal"}}
    
    loan_amount = property_value - down_payment
    
    # Estimate housing payment (rough calculation)
    monthly_rate = 0.065 / 12  # 6.5% estimate
    n_payments = 360
    principal_interest = loan_amount * (monthly_rate * (1 + monthly_rate)**n_payments) / ((1 + monthly_rate)**n_payments - 1)
    estimated_housing_payment = principal_interest * 1.3  # Add taxes, insurance estimate
    
    prequalification_request = f"""
    Please provide a quick loan prequalification analysis for:

    - Property Value: ${property_value:,.2f}
    - Down Payment: ${down_payment:,.2f}
    - Loan Amount: ${loan_amount:,.2f}
    - Monthly Income: ${gross_monthly_income:,.2f}
    - Monthly Debts: ${monthly_debt_payments:,.2f}
    - Credit Score: {credit_score}

    Use calculate_comprehensive_borrower_score to determine:
    1. Prequalification status (Approved/Conditional/Denied)
    2. Maximum loan amount recommendation
    3. Best loan program fit
    4. Key requirements for full approval

    Focus on providing clear next steps for the borrower.
    """
    
    result = graph.invoke(
        {"messages": [HumanMessage(content=prequalification_request)]},
        config
    )
    
    return result["messages"][-1].content

if __name__ == "__main__":
    # Test the system
    print("🏠 CLTV AI Agent - Mortgage Lending Analysis System")
    print("=" * 60)
    print(f"🔧 Model Provider: {MODEL_PROVIDER.upper()}")
    
    try:
        # Test with sample borrower data
        test_analysis = analyze_borrower_comprehensive(
            property_value=500000,
            primary_loan_amount=400000,
            gross_monthly_income=8000,
            monthly_debt_payments=800,
            proposed_housing_payment=3200,
            credit_score=740,
            down_payment=100000,
            employment_years=3.5,
            liquid_assets=50000
        )
        
        print("\n📊 Sample Analysis Complete!")
        print("The CLTV AI Agent is ready for use.")
        
    except Exception as e:
        print(f"❌ Setup Error: {e}")
        print("Please check your environment configuration.")