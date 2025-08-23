"""
Additional Mortgage and Lending Analysis Tools

This module provides specialized tools for mortgage lending analysis including:
- PMI/MIP analysis and calculations
- Debt consolidation impact assessment
- Home affordability calculations
- Credit impact analysis
- Loan program comparison
- Refinancing analysis

These tools complement the core CLTV AI agent and provide deeper insights
into specific lending scenarios and borrower situations.
"""

from langchain_core.tools import tool
import json
import math
from typing import List, Dict, Union



@tool
def calculate_pmi_analysis(
    loan_amount: float,
    property_value: float,
    credit_score: int,
    loan_type: str = "conventional"
) -> str:
    """
    Calculate Private Mortgage Insurance (PMI) requirements and costs.
    
    Analyzes PMI requirements based on loan type, LTV ratio, and credit score.
    Provides detailed cost breakdown and removal timeline.
    
    Parameters:
    loan_amount (float): Loan amount
    property_value (float): Property value
    credit_score (int): Borrower credit score (300-850)
    loan_type (str): Type of loan (conventional, fha, va, usda)
    
    Returns:
    str: Comprehensive PMI analysis with costs and removal timeline
    """
    
    try:
        ltv = (loan_amount / property_value) * 100 if property_value > 0 else 0
        
        if loan_type.lower() == "conventional" and ltv > 80:
            # PMI rate based on LTV and credit score
            if credit_score >= 760:
                if ltv <= 85:
                    pmi_rate = 0.0025
                elif ltv <= 90:
                    pmi_rate = 0.004
                elif ltv <= 95:
                    pmi_rate = 0.0065
                else:
                    pmi_rate = 0.008
            elif credit_score >= 700:
                if ltv <= 85:
                    pmi_rate = 0.004
                elif ltv <= 90:
                    pmi_rate = 0.0065
                elif ltv <= 95:
                    pmi_rate = 0.008
                else:
                    pmi_rate = 0.01
            else:
                if ltv <= 85:
                    pmi_rate = 0.0065
                elif ltv <= 90:
                    pmi_rate = 0.008
                elif ltv <= 95:
                    pmi_rate = 0.01
                else:
                    pmi_rate = 0.012
            
            annual_pmi = loan_amount * pmi_rate
            monthly_pmi = annual_pmi / 12
            
            # Calculate when PMI drops off (78% LTV)
            target_balance = property_value * 0.78
            pmi_removal_paydown = loan_amount - target_balance
            
            # Calculate years to PMI removal (assuming 30-year loan at 6.5%)
            monthly_rate = 0.065 / 12
            monthly_payment = loan_amount * (monthly_rate * (1 + monthly_rate)**360) / ((1 + monthly_rate)**360 - 1)
            
            # Find when balance reaches 78% LTV
            balance = loan_amount
            months = 0
            while balance > target_balance and months < 360:
                interest_payment = balance * monthly_rate
                principal_payment = monthly_payment - interest_payment
                balance -= principal_payment
                months += 1
            
            years_to_removal = months / 12
            
            result = f"""
📋 PMI ANALYSIS
===============

💰 LOAN DETAILS:
• Loan Amount: ${loan_amount:,.2f}
• Property Value: ${property_value:,.2f}
• LTV Ratio: {ltv:.1f}%
• Credit Score: {credit_score}

💳 PMI REQUIREMENTS:
• PMI Required: Yes (LTV > 80%)
• Annual PMI Rate: {pmi_rate*100:.3f}%
• Monthly PMI: ${monthly_pmi:,.2f}
• Annual PMI: ${annual_pmi:,.2f}

📅 PMI REMOVAL:
• Automatic Removal at: 78% LTV
• Target Loan Balance: ${target_balance:,.2f}
• Paydown Required: ${pmi_removal_paydown:,.2f}
• Estimated Years to Removal: {years_to_removal:.1f} years
• Request Removal at: 80% LTV (appraisal required)

💡 PMI STRATEGIES:
• Consider 80% LTV loan to avoid PMI
• Lender-paid PMI option may be available
• Single premium PMI option reduces monthly payment
• Make extra principal payments to reach 78% faster
            """
            
        elif loan_type.lower() == "fha":
            upfront_mip = loan_amount * 0.0175
            annual_mip_rate = 0.0085 if ltv > 90 else 0.0080
            annual_mip = loan_amount * annual_mip_rate
            monthly_mip = annual_mip / 12
            
            result = f"""
📋 FHA MIP ANALYSIS
==================

💰 LOAN DETAILS:
• Loan Amount: ${loan_amount:,.2f}
• Property Value: ${property_value:,.2f}
• LTV Ratio: {ltv:.1f}%

💳 MIP REQUIREMENTS:
• Upfront MIP: 1.75% (${upfront_mip:,.2f})
• Annual MIP Rate: {annual_mip_rate*100:.2f}%
• Annual MIP: ${annual_mip:,.2f}
• Monthly MIP: ${monthly_mip:,.2f}

📅 MIP REMOVAL:
{"• FHA MIP for life (LTV > 90%)" if ltv > 90 else "• MIP removed after 11 years (LTV ≤ 90%)"}
• No early removal option for high LTV loans
• Refinance to conventional when 20% equity reached

💡 FHA STRATEGIES:
• Consider conventional loan if 20% down available
• Refinance to conventional when equity builds to 20%
• Factor MIP into long-term cost analysis
            """
            
        elif loan_type.lower() == "va":
            va_funding_fee_rate = 0.023  # 2.3% for first-time use, 0% down
            va_funding_fee = loan_amount * va_funding_fee_rate
            
            result = f"""
📋 VA LOAN ANALYSIS
==================

💰 LOAN DETAILS:
• Loan Amount: ${loan_amount:,.2f}
• Property Value: ${property_value:,.2f}
• LTV Ratio: {ltv:.1f}%

💳 VA FUNDING FEE:
• Funding Fee Rate: {va_funding_fee_rate*100:.1f}%
• Funding Fee: ${va_funding_fee:,.2f}
• Monthly PMI: $0 (No PMI required)

✅ VA LOAN BENEFITS:
• No PMI required regardless of LTV
• No down payment required
• Competitive interest rates
• No prepayment penalties

💡 VA LOAN ADVANTAGES:
• Significant monthly savings vs conventional + PMI
• 100% financing available
• Reusable benefit (with entitlement restoration)
            """
            
        else:  # No MI required (conventional with LTV ≤ 80% or USDA)
            result = f"""
📋 NO MI REQUIRED
=================

💰 LOAN DETAILS:
• Loan Amount: ${loan_amount:,.2f}
• Property Value: ${property_value:,.2f}
• LTV Ratio: {ltv:.1f}%

✅ MORTGAGE INSURANCE:
• PMI Required: No (LTV ≤ 80%)
• Monthly Savings: Approximately $200-800/month
• Excellent lending position

💡 BENEFITS:
• Lower monthly payment
• Better cash flow
• Faster equity building
• No removal requirements or timeline
            """
        
        return result.strip()
        
    except Exception as e:
        return f"Error calculating PMI analysis: {str(e)}"


@tool
def analyze_debt_consolidation_impact(
    current_monthly_debts: float,
    debt_balances: str,  # JSON string of debt balances
    consolidation_amount: float,
    new_payment: float,
    gross_monthly_income: float
) -> str:
    """
    Analyze the impact of debt consolidation on DTI and loan qualification.
    
    Evaluates how consolidating existing debts affects borrower qualification
    and borrowing capacity for mortgage lending.
    
    Parameters:
    current_monthly_debts (float): Current monthly debt payments
    debt_balances (str): JSON string of current debt balances [balance1, balance2, ...]
    consolidation_amount (float): Amount to consolidate
    new_payment (float): New consolidated payment
    gross_monthly_income (float): Gross monthly income
    
    Returns:
    str: Comprehensive debt consolidation impact analysis
    """
    
    try:
        debt_list = json.loads(debt_balances) if debt_balances.strip() else []
        total_debt_balance = sum(debt_list)
        
        # Calculate DTI improvement
        current_dti = (current_monthly_debts / gross_monthly_income) * 100
        new_dti = (new_payment / gross_monthly_income) * 100
        dti_improvement = current_dti - new_dti
        monthly_savings = current_monthly_debts - new_payment
        
        # Calculate new available borrowing capacity
        # Using different DTI thresholds for different loan types
        max_allowable_debt_conventional = gross_monthly_income * 0.43
        max_allowable_debt_fha = gross_monthly_income * 0.57
        
        current_available_conv = max_allowable_debt_conventional - current_monthly_debts
        new_available_conv = max_allowable_debt_conventional - new_payment
        additional_capacity_conv = new_available_conv - current_available_conv
        
        current_available_fha = max_allowable_debt_fha - current_monthly_debts
        new_available_fha = max_allowable_debt_fha - new_payment
        additional_capacity_fha = new_available_fha - current_available_fha
        
        # Calculate qualification improvement
        if current_dti > 43 and new_dti <= 43:
            qualification_impact = "Significant - Now qualifies for conventional loans"
        elif current_dti > 57 and new_dti <= 57:
            qualification_impact = "Major - Now qualifies for FHA loans"
        elif dti_improvement > 5:
            qualification_impact = "Moderate - Improved qualification likelihood"
        elif dti_improvement > 2:
            qualification_impact = "Minor - Slight improvement in qualification"
        else:
            qualification_impact = "Minimal - Limited impact on qualification"
        
        result = f"""
📊 DEBT CONSOLIDATION ANALYSIS
==============================

💰 CURRENT SITUATION:
• Monthly Debt Payments: ${current_monthly_debts:,.2f}
• Total Debt Balances: ${total_debt_balance:,.2f}
• Current DTI: {current_dti:.1f}%
• Gross Monthly Income: ${gross_monthly_income:,.2f}

🔄 AFTER CONSOLIDATION:
• New Monthly Payment: ${new_payment:,.2f}
• New DTI: {new_dti:.1f}%
• DTI Improvement: {dti_improvement:.1f} percentage points
• Monthly Savings: ${monthly_savings:,.2f}

📈 BORROWING CAPACITY ANALYSIS:

🏛️ CONVENTIONAL LOANS (43% max DTI):
• Current Available Capacity: ${current_available_conv:,.2f}
• New Available Capacity: ${new_available_conv:,.2f}
• Additional Capacity: ${additional_capacity_conv:,.2f}

🏠 FHA LOANS (57% max DTI):
• Current Available Capacity: ${current_available_fha:,.2f}
• New Available Capacity: ${new_available_fha:,.2f}
• Additional Capacity: ${additional_capacity_fha:,.2f}

💡 QUALIFICATION IMPACT:
• Overall Impact: {qualification_impact}
{"• Now qualifies for better loan programs" if dti_improvement > 5 else ""}
{"• May qualify for larger loan amount" if additional_capacity_conv > 500 else ""}
{"• Better interest rate tier possible" if dti_improvement > 3 else ""}

⚠️ IMPORTANT CONSIDERATIONS:
• Consolidation may extend repayment period
• Compare total interest cost over loan life
• Ensure no prepayment penalties on existing debts
• Maintain emergency fund after consolidation
• Consider impact on credit utilization ratios
• Timing: Complete consolidation before mortgage application

🎯 RECOMMENDATIONS:
{"• Proceed with consolidation - significant benefit" if dti_improvement > 5 else "• Consider consolidation - moderate benefit" if dti_improvement > 2 else "• Analyze cost vs benefit carefully"}
• Document savings for loan application
• Ensure new payment is sustainable long-term
        """
        
        return result.strip()
        
    except Exception as e:
        return f"Error analyzing debt consolidation: {str(e)}"


@tool
def calculate_affordability_analysis(
    gross_monthly_income: float,
    monthly_debt_payments: float,
    down_payment_available: float,
    target_dti: float = 36.0,
    interest_rate: float = 6.5,
    loan_term: int = 30
) -> str:
    """
    Calculate maximum affordable home price and loan amount based on income and DTI targets.
    
    Provides comprehensive affordability analysis including multiple scenarios
    and loan program options.
    
    Parameters:
    gross_monthly_income (float): Gross monthly income
    monthly_debt_payments (float): Current monthly debt payments
    down_payment_available (float): Available down payment
    target_dti (float): Target DTI ratio (default 36%)
    interest_rate (float): Interest rate assumption (default 6.5%)
    loan_term (int): Loan term in years (default 30)
    
    Returns:
    str: Comprehensive affordability analysis with multiple scenarios
    """
    
    try:
        # Calculate maximum allowable housing payment
        max_total_payment = gross_monthly_income * (target_dti / 100)
        max_housing_payment = max_total_payment - monthly_debt_payments
        
        if max_housing_payment <= 0:
            return f"""
❌ AFFORDABILITY ANALYSIS
=========================

⚠️ QUALIFICATION ISSUE:
• Current DTI: {(monthly_debt_payments / gross_monthly_income) * 100:.1f}%
• Target DTI: {target_dti:.1f}%
• Current debt payments exceed target DTI ratio
• Debt reduction required before home purchase

💡 RECOMMENDATIONS:
• Pay down existing debts to improve DTI
• Consider higher income documentation (overtime, bonuses)
• Look into debt consolidation options
• Consider higher DTI loan programs (FHA up to 57%)
• Increase income through additional employment
            """
        
        # Estimate taxes, insurance, HOA (PITI components)
        # Typical breakdown: PI = 75%, TI = 20%, PMI = 5% of total payment
        principal_interest_budget = max_housing_payment * 0.75
        
        # Calculate maximum loan amount using loan payment formula
        monthly_rate = interest_rate / 100 / 12
        n_payments = loan_term * 12
        
        if monthly_rate > 0:
            max_loan_amount = principal_interest_budget * ((1 + monthly_rate)**n_payments - 1) / (monthly_rate * (1 + monthly_rate)**n_payments)
        else:
            max_loan_amount = principal_interest_budget * n_payments
        
        # Calculate maximum home price
        max_home_price = max_loan_amount + down_payment_available
        
        # Calculate LTV and adjust for PMI if needed
        ltv = (max_loan_amount / max_home_price) * 100 if max_home_price > 0 else 0
        
        # PMI consideration for conventional loans
        pmi_required = ltv > 80
        if pmi_required:
            # Estimate PMI at 0.5% annually
            estimated_pmi = max_loan_amount * 0.005 / 12
            adjusted_pi_budget = principal_interest_budget - estimated_pmi
            
            if adjusted_pi_budget > 0 and monthly_rate > 0:
                adjusted_loan_amount = adjusted_pi_budget * ((1 + monthly_rate)**n_payments - 1) / (monthly_rate * (1 + monthly_rate)**n_payments)
                adjusted_home_price = adjusted_loan_amount + down_payment_available
                adjusted_ltv = (adjusted_loan_amount / adjusted_home_price) * 100
            else:
                adjusted_loan_amount = max_loan_amount
                adjusted_home_price = max_home_price
                adjusted_ltv = ltv
                estimated_pmi = 0
        else:
            adjusted_loan_amount = max_loan_amount
            adjusted_home_price = max_home_price
            adjusted_ltv = ltv
            estimated_pmi = 0
        
        # Down payment percentage
        down_payment_pct = (down_payment_available / adjusted_home_price) * 100 if adjusted_home_price > 0 else 0
        
        # Calculate scenarios for different DTI targets
        scenarios = []
        for dti in [28, 36, 43, 50]:
            scenario_payment = gross_monthly_income * (dti / 100) - monthly_debt_payments
            if scenario_payment > 0:
                scenario_pi = scenario_payment * 0.75
                if monthly_rate > 0:
                    scenario_loan = scenario_pi * ((1 + monthly_rate)**n_payments - 1) / (monthly_rate * (1 + monthly_rate)**n_payments)
                else:
                    scenario_loan = scenario_pi * n_payments
                scenario_price = scenario_loan + down_payment_available
                scenario_ltv = (scenario_loan / scenario_price) * 100 if scenario_price > 0 else 0
                
                scenarios.append({
                    'dti': dti,
                    'payment': scenario_payment,
                    'loan': scenario_loan,
                    'price': scenario_price,
                    'ltv': scenario_ltv
                })
        
        # Estimate closing costs and cash needed
        closing_costs = adjusted_home_price * 0.025  # 2.5% estimate
        total_cash_needed = down_payment_available + closing_costs
        
        result = f"""
🏠 HOME AFFORDABILITY ANALYSIS
==============================

💰 INCOME & DEBT PROFILE:
• Gross Monthly Income: ${gross_monthly_income:,.2f}
• Current Monthly Debts: ${monthly_debt_payments:,.2f}
• Available Down Payment: ${down_payment_available:,.2f}
• Target DTI Ratio: {target_dti:.1f}%
• Interest Rate: {interest_rate:.2f}%
• Loan Term: {loan_term} years

📊 AFFORDABILITY CALCULATIONS:
• Maximum Total Payment: ${max_total_payment:,.2f}
• Maximum Housing Payment: ${max_housing_payment:,.2f}
• Principal & Interest Budget: ${principal_interest_budget:,.2f}
{"• Estimated PMI: $" + f"{estimated_pmi:,.2f}/month" if pmi_required else "• PMI: Not Required"}

🎯 MAXIMUM PURCHASE SCENARIO:
• Maximum Home Price: ${adjusted_home_price:,.2f}
• Maximum Loan Amount: ${adjusted_loan_amount:,.2f}
• Down Payment: ${down_payment_available:,.2f} ({down_payment_pct:.1f}%)
• Resulting LTV: {adjusted_ltv:.1f}%
• Estimated Closing Costs: ${closing_costs:,.2f}
• Total Cash Needed: ${total_cash_needed:,.2f}

📋 DTI SCENARIO COMPARISON:
"""
        
        for scenario in scenarios:
            loan_program = ""
            if scenario['dti'] <= 28:
                loan_program = "Conventional (Conservative)"
            elif scenario['dti'] <= 36:
                loan_program = "Conventional (Standard)"
            elif scenario['dti'] <= 43:
                loan_program = "Conventional (Max)"
            else:
                loan_program = "FHA/Non-QM"
            
            result += f"""
• {scenario['dti']:.0f}% DTI ({loan_program}):
  - Max Price: ${scenario['price']:,.0f}
  - Max Loan: ${scenario['loan']:,.0f}
  - Monthly Payment: ${scenario['payment']:,.0f}
"""
        
        result += f"""

💡 AFFORDABILITY STRATEGIES:
{"• Excellent purchasing power - wide range of options" if max_housing_payment > 2500 else "• Good purchasing power - solid options available" if max_housing_payment > 1800 else "• Moderate budget - focus on starter homes" if max_housing_payment > 1200 else "• Limited budget - consider lower-cost areas or increase income"}
{"• Consider 20% down to avoid PMI and maximize buying power" if pmi_required and down_payment_available < adjusted_home_price * 0.2 else "• Great down payment position - no PMI required"}
{"• Room to increase budget if income grows" if target_dti < 40 else "• At maximum comfortable DTI level"}

📊 LOAN PROGRAM RECOMMENDATIONS:
• Conventional: Best if 20% down payment available
• FHA: Consider if down payment limited (3.5% minimum)
• VA: Excellent option if eligible (0% down, no PMI)
• USDA: Rural properties (0% down, income limits apply)

⚠️ IMPORTANT CONSIDERATIONS:
• Property taxes vary significantly by location
• HOA fees can impact affordability substantially  
• Maintenance and utility costs (budget 1-3% of home value annually)
• Moving costs and immediate home improvements
• Market conditions affect inventory and pricing
• Pre-approval recommended before house hunting

🎯 NEXT STEPS:
• Get pre-approved to confirm actual buying power
• Research local property tax rates and insurance costs
• Factor in commute costs and lifestyle preferences
• Maintain reserves for closing costs and moving expenses
        """
        
        return result.strip()
        
    except Exception as e:
        return f"Error calculating affordability: {str(e)}"


@tool
def analyze_credit_impact_on_lending(
    current_credit_score: int,
    target_credit_score: int,
    loan_amount: float,
    loan_type: str = "conventional"
) -> str:
    """
    Analyze the impact of credit score improvements on lending terms and costs.
    
    Shows potential savings and improved terms from credit score enhancement.
    
    Parameters:
    current_credit_score (int): Current credit score
    target_credit_score (int): Target credit score
    loan_amount (float): Loan amount for analysis
    loan_type (str): Type of loan (conventional, fha, va)
    
    Returns:
    str: Credit impact analysis with potential savings
    """
    
    try:
        # Interest rate estimates based on credit score tiers
        rate_matrix = {
            "conventional": {
                800: 6.25, 780: 6.35, 760: 6.45, 740: 6.55, 720: 6.75,
                700: 6.95, 680: 7.25, 660: 7.65, 640: 8.15, 620: 8.75, 600: 9.25
            },
            "fha": {
                800: 6.45, 780: 6.50, 760: 6.55, 740: 6.60, 720: 6.65,
                700: 6.70, 680: 6.75, 660: 6.80, 640: 6.85, 620: 6.90, 580: 6.95
            }
        }
        
        def get_rate(score, loan_type):
            rates = rate_matrix.get(loan_type.lower(), rate_matrix["conventional"])
            for threshold in sorted(rates.keys(), reverse=True):
                if score >= threshold:
                    return rates[threshold]
            return max(rates.values())  # Worst rate if below all thresholds
        
        current_rate = get_rate(current_credit_score, loan_type)
        target_rate = get_rate(target_credit_score, loan_type)
        rate_improvement = current_rate - target_rate
        
        # Calculate monthly payments
        def calculate_payment(principal, rate, years):
            monthly_rate = rate / 100 / 12
            n_payments = years * 12
            if monthly_rate > 0:
                return principal * (monthly_rate * (1 + monthly_rate)**n_payments) / ((1 + monthly_rate)**n_payments - 1)
            else:
                return principal / n_payments
        
        current_payment = calculate_payment(loan_amount, current_rate, 30)
        target_payment = calculate_payment(loan_amount, target_rate, 30)
        monthly_savings = current_payment - target_payment
        
        # Total interest savings over loan life
        current_total_interest = (current_payment * 360) - loan_amount
        target_total_interest = (target_payment * 360) - loan_amount
        total_interest_savings = current_total_interest - target_total_interest
        
        # PMI impact (if applicable)
        pmi_impact = ""
        if loan_type.lower() == "conventional":
            if current_credit_score < 620:
                pmi_impact = "• Credit improvement may enable PMI approval"
            elif current_credit_score < 720:
                current_pmi_rate = 0.008 if current_credit_score < 680 else 0.006
                target_pmi_rate = 0.004 if target_credit_score >= 760 else 0.005
                pmi_savings = (current_pmi_rate - target_pmi_rate) * loan_amount / 12
                if pmi_savings > 0:
                    pmi_impact = f"• PMI savings: ${pmi_savings:,.2f}/month"
        
        # Approval likelihood
        if current_credit_score < 580:
            current_approval = "Very Poor - Limited options"
        elif current_credit_score < 620:
            current_approval = "Poor - FHA may be only option"
        elif current_credit_score < 680:
            current_approval = "Fair - Standard terms with higher rates"
        elif current_credit_score < 740:
            current_approval = "Good - Competitive terms available"
        else:
            current_approval = "Excellent - Best rates and terms"
        
        if target_credit_score < 580:
            target_approval = "Very Poor - Limited options"
        elif target_credit_score < 620:
            target_approval = "Poor - FHA may be only option"
        elif target_credit_score < 680:
            target_approval = "Fair - Standard terms with higher rates"
        elif target_credit_score < 740:
            target_approval = "Good - Competitive terms available"
        else:
            target_approval = "Excellent - Best rates and terms"
        
        result = f"""
📊 CREDIT SCORE IMPACT ANALYSIS
===============================

💳 CREDIT PROFILE:
• Current Credit Score: {current_credit_score}
• Target Credit Score: {target_credit_score}
• Score Improvement: {target_credit_score - current_credit_score} points
• Loan Amount: ${loan_amount:,.2f}
• Loan Type: {loan_type.title()}

💰 INTEREST RATE IMPACT:
• Current Estimated Rate: {current_rate:.2f}%
• Target Estimated Rate: {target_rate:.2f}%
• Rate Improvement: {rate_improvement:.2f} percentage points

📈 PAYMENT COMPARISON:
• Current Monthly Payment: ${current_payment:,.2f}
• Target Monthly Payment: ${target_payment:,.2f}
• Monthly Savings: ${monthly_savings:,.2f}
• Annual Savings: ${monthly_savings * 12:,.2f}

💡 LONG-TERM SAVINGS:
• Total Interest (Current): ${current_total_interest:,.2f}
• Total Interest (Target): ${target_total_interest:,.2f}
• Lifetime Interest Savings: ${total_interest_savings:,.2f}
{pmi_impact}

📋 APPROVAL LIKELIHOOD:
• Current Score Rating: {current_approval}
• Target Score Rating: {target_approval}

🎯 CREDIT IMPROVEMENT STRATEGIES:
• Pay down credit card balances (reduce utilization)
• Make all payments on time (payment history = 35% of score)
• Don't close old credit cards (maintain credit history length)
• Limit new credit inquiries before mortgage application
• Consider credit score monitoring services
• Pay off collections and charge-offs if possible

⏰ TIMELINE CONSIDERATIONS:
• Most credit improvements take 30-90 days to reflect
• Significant improvements may take 6-12 months
• Plan credit optimization before mortgage shopping
• Avoid major credit changes during mortgage process

💡 IMMEDIATE ACTIONS:
• Pay down credit cards below 30% utilization (10% is ideal)
• Verify credit report accuracy and dispute errors
• Make sure all accounts are current
• Consider becoming authorized user on family member's account
        """
        
        return result.strip()
        
    except Exception as e:
        return f"Error analyzing credit impact: {str(e)}"


@tool
def compare_loan_programs(
    loan_amount: float,
    property_value: float,
    credit_score: int,
    down_payment: float,
    gross_monthly_income: float,
    monthly_debts: float,
    is_first_time_buyer: bool = False,
    is_veteran: bool = False,
    is_rural_property: bool = False
) -> str:
    """
    Compare different loan programs and their suitability for the borrower.
    
    Analyzes conventional, FHA, VA, and USDA loan options with detailed comparison.
    
    Parameters:
    loan_amount (float): Requested loan amount
    property_value (float): Property value
    credit_score (int): Borrower credit score
    down_payment (float): Down payment amount
    gross_monthly_income (float): Gross monthly income
    monthly_debts (float): Monthly debt payments
    is_first_time_buyer (bool): First-time homebuyer status
    is_veteran (bool): Veteran status for VA loan eligibility
    is_rural_property (bool): Rural property for USDA eligibility
    
    Returns:
    str: Comprehensive loan program comparison
    """
    
    try:
        ltv = (loan_amount / property_value) * 100
        down_payment_pct = (down_payment / property_value) * 100
        
        # Estimate monthly payment components
        def calculate_payment(principal, rate, years):
            monthly_rate = rate / 100 / 12
            n_payments = years * 12
            if monthly_rate > 0:
                return principal * (monthly_rate * (1 + monthly_rate)**n_payments) / ((1 + monthly_rate)**n_payments - 1)
            else:
                return principal / n_payments
        
        # Estimated rates by credit score and program
        def get_program_rate(program, credit_score):
            if program == "conventional":
                if credit_score >= 760: return 6.45
                elif credit_score >= 740: return 6.55
                elif credit_score >= 720: return 6.75
                elif credit_score >= 700: return 6.95
                elif credit_score >= 680: return 7.25
                elif credit_score >= 660: return 7.65
                elif credit_score >= 640: return 8.15
                else: return 8.75
            elif program == "fha":
                if credit_score >= 740: return 6.60
                elif credit_score >= 680: return 6.75
                elif credit_score >= 620: return 6.90
                elif credit_score >= 580: return 6.95
                else: return 7.25
            elif program == "va":
                if credit_score >= 740: return 6.40
                elif credit_score >= 680: return 6.55
                elif credit_score >= 620: return 6.70
                else: return 6.85
            elif program == "usda":
                if credit_score >= 740: return 6.50
                elif credit_score >= 680: return 6.65
                elif credit_score >= 640: return 6.80
                else: return 6.95
            return 7.00
        
        programs = []
        
        # Conventional Loan Analysis
        conv_eligible = credit_score >= 620 and down_payment_pct >= 3
        if conv_eligible:
            conv_rate = get_program_rate("conventional", credit_score)
            conv_payment = calculate_payment(loan_amount, conv_rate, 30)
            conv_pmi = (loan_amount * 0.005 / 12) if ltv > 80 else 0
            conv_total_payment = conv_payment + conv_pmi
            
            programs.append({
                "name": "Conventional",
                "eligible": True,
                "rate": conv_rate,
                "payment": conv_payment,
                "pmi": conv_pmi,
                "total_payment": conv_total_payment,
                "down_payment_min": max(property_value * 0.03, 1000),
                "pros": [
                    "No upfront mortgage insurance",
                    "PMI removable at 78% LTV" if ltv > 80 else "No PMI required",
                    "Higher loan limits",
                    "Fewer restrictions on property types"
                ],
                "cons": [
                    "Higher credit score requirements",
                    "Larger down payment typically needed",
                    "PMI required if LTV > 80%" if ltv > 80 else "Stricter DTI requirements"
                ]
            })
        
        # FHA Loan Analysis
        fha_eligible = credit_score >= 580
        if fha_eligible:
            fha_rate = get_program_rate("fha", credit_score)
            fha_payment = calculate_payment(loan_amount, fha_rate, 30)
            fha_upfront_mip = loan_amount * 0.0175
            fha_monthly_mip = loan_amount * 0.0085 / 12
            fha_total_payment = fha_payment + fha_monthly_mip
            
            programs.append({
                "name": "FHA",
                "eligible": True,
                "rate": fha_rate,
                "payment": fha_payment,
                "pmi": fha_monthly_mip,
                "total_payment": fha_total_payment,
                "down_payment_min": property_value * 0.035,
                "upfront_cost": fha_upfront_mip,
                "pros": [
                    "Low down payment (3.5%)",
                    "Lower credit score requirements",
                    "Higher DTI ratios allowed",
                    "Gift funds allowed for down payment"
                ],
                "cons": [
                    "Upfront MIP required",
                    "MIP for life if LTV > 90%",
                    "Property condition requirements",
                    "Loan limits may be lower"
                ]
            })
        
        # VA Loan Analysis
        if is_veteran:
            va_rate = get_program_rate("va", credit_score)
            va_payment = calculate_payment(loan_amount, va_rate, 30)
            va_funding_fee = loan_amount * 0.023 if down_payment_pct == 0 else loan_amount * 0.015
            
            programs.append({
                "name": "VA",
                "eligible": True,
                "rate": va_rate,
                "payment": va_payment,
                "pmi": 0,
                "total_payment": va_payment,
                "down_payment_min": 0,
                "upfront_cost": va_funding_fee,
                "pros": [
                    "No down payment required",
                    "No PMI ever required",
                    "Competitive interest rates",
                    "No prepayment penalties",
                    "Assumable loans"
                ],
                "cons": [
                    "VA funding fee required",
                    "Veteran eligibility required",
                    "Property must be primary residence",
                    "VA appraisal requirements"
                ]
            })
        
        # USDA Loan Analysis
        if is_rural_property:
            # Income limits check (simplified - actual limits vary by area)
            income_limit_estimate = 115000  # Example for family of 4
            usda_income_eligible = gross_monthly_income * 12 <= income_limit_estimate
            
            if usda_income_eligible:
                usda_rate = get_program_rate("usda", credit_score)
                usda_payment = calculate_payment(loan_amount, usda_rate, 30)
                usda_guarantee_fee = loan_amount * 0.01
                usda_annual_fee = loan_amount * 0.0035 / 12
                usda_total_payment = usda_payment + usda_annual_fee
                
                programs.append({
                    "name": "USDA",
                    "eligible": True,
                    "rate": usda_rate,
                    "payment": usda_payment,
                    "pmi": usda_annual_fee,
                    "total_payment": usda_total_payment,
                    "down_payment_min": 0,
                    "upfront_cost": usda_guarantee_fee,
                    "pros": [
                        "No down payment required",
                        "Below-market interest rates",
                        "Low annual guarantee fee",
                        "Primary residence only"
                    ],
                    "cons": [
                        "Rural property requirement",
                        "Income limits apply",
                        "Upfront guarantee fee",
                        "Limited property types"
                    ]
                })
        
        # Sort programs by total monthly payment
        programs.sort(key=lambda x: x["total_payment"])
        
        result = f"""
🏦 LOAN PROGRAM COMPARISON
==========================

👤 BORROWER PROFILE:
• Credit Score: {credit_score}
• Loan Amount: ${loan_amount:,.2f}
• Property Value: ${property_value:,.2f}
• Down Payment: ${down_payment:,.2f} ({down_payment_pct:.1f}%)
• LTV Ratio: {ltv:.1f}%
• Monthly Income: ${gross_monthly_income:,.2f}
• Monthly Debts: ${monthly_debts:,.2f}

📊 PROGRAM ANALYSIS:
"""
        
        for i, program in enumerate(programs, 1):
            result += f"""
🏛️ {program["name"].upper()} LOAN - {"✅ ELIGIBLE" if program["eligible"] else "❌ NOT ELIGIBLE"}
• Interest Rate: {program["rate"]:.2f}%
• Principal & Interest: ${program["payment"]:,.2f}
• Mortgage Insurance: ${program["pmi"]:,.2f}
• Total Monthly Payment: ${program["total_payment"]:,.2f}
• Minimum Down Payment: ${program["down_payment_min"]:,.2f}
{"• Upfront Cost: $" + f"{program.get('upfront_cost', 0):,.2f}" if program.get('upfront_cost') else ""}

✅ ADVANTAGES:
{chr(10).join([f"  - {pro}" for pro in program["pros"]])}

⚠️ CONSIDERATIONS:
{chr(10).join([f"  - {con}" for con in program["cons"]])}
---
"""
        
        # DTI Analysis
        best_program = programs[0] if programs else None
        if best_program:
            estimated_total_housing = best_program["total_payment"] + (property_value * 0.015 / 12)  # Add taxes/insurance estimate
            housing_dti = (estimated_total_housing / gross_monthly_income) * 100
            total_dti = ((estimated_total_housing + monthly_debts) / gross_monthly_income) * 100
            
            result += f"""
📈 DTI ANALYSIS (Best Option: {best_program["name"]}):
• Estimated Total Housing Payment: ${estimated_total_housing:,.2f}
• Front-End DTI: {housing_dti:.1f}%
• Back-End DTI: {total_dti:.1f}%
• DTI Status: {"✅ Qualified" if total_dti <= 43 else "⚠️ May Need Review" if total_dti <= 50 else "❌ May Not Qualify"}

🎯 RECOMMENDATIONS:
"""
            
            if len(programs) > 1:
                savings = programs[-1]["total_payment"] - programs[0]["total_payment"]
                result += f"• {programs[0]['name']} offers lowest payment (${savings:,.2f}/month savings vs highest)\n"
            
            if any(p["name"] == "VA" for p in programs):
                result += "• VA loan recommended if eligible - best overall value\n"
            elif any(p["name"] == "USDA" for p in programs):
                result += "• USDA loan excellent for rural properties with income eligibility\n"
            elif down_payment_pct < 20:
                result += "• Consider saving for 20% down to avoid mortgage insurance\n"
            
            if total_dti > 43:
                result += "• Consider debt reduction or income increase for better qualification\n"
            
            result += f"""
💡 NEXT STEPS:
• Get pre-qualified with top 2-3 programs
• Compare actual rates and terms from multiple lenders
• Consider timing of application based on market conditions
• Factor in closing costs and cash-to-close requirements
• Review property eligibility for chosen program
        """
        
        return result.strip()
        
    except Exception as e:
        return f"Error comparing loan programs: {str(e)}"


# Helper function for mortgage calculations
def calculate_monthly_payment(principal: float, annual_rate: float, years: int) -> float:
    """Calculate monthly mortgage payment using standard formula"""
    monthly_rate = annual_rate / 100 / 12
    n_payments = years * 12
    
    if monthly_rate > 0:
        payment = principal * (monthly_rate * (1 + monthly_rate)**n_payments) / ((1 + monthly_rate)**n_payments - 1)
    else:
        payment = principal / n_payments
    
    return payment


# Additional utility functions can be added here for complex calculations
def calculate_loan_amortization(principal: float, annual_rate: float, years: int, extra_payment: float = 0) -> dict:
    """Calculate loan amortization schedule with optional extra payments"""
    monthly_rate = annual_rate / 100 / 12
    n_payments = years * 12
    
    base_payment = calculate_monthly_payment(principal, annual_rate, years)
    total_payment = base_payment + extra_payment
    
    balance = principal
    total_interest = 0
    months = 0
    
    while balance > 0.01 and months < n_payments:
        interest_payment = balance * monthly_rate
        principal_payment = min(total_payment - interest_payment, balance)
        
        balance -= principal_payment
        total_interest += interest_payment
        months += 1
    
    return {
        'months_to_payoff': months,
        'years_to_payoff': months / 12,
        'total_interest': total_interest,
        'monthly_payment': base_payment,
        'total_with_extra': total_payment,
        'interest_saved': (base_payment * n_payments - principal) - total_interest
    }