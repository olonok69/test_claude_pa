from cltv_ai_agent import quick_loan_prequalification

result = quick_loan_prequalification(
    property_value=500000,
    down_payment=100000,
    gross_monthly_income=8000,
    monthly_debt_payments=800,
    credit_score=740
)
print(result)