from cltv_ai_agent import analyze_borrower_comprehensive

result = analyze_borrower_comprehensive(
    property_value=500000,
    primary_loan_amount=400000,
    gross_monthly_income=8000,
    monthly_debt_payments=800,
    proposed_housing_payment=3200,
    credit_score=740,
    down_payment=100000
)
print(result)