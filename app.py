import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import plotly.express as px

# Set page configuration
st.set_page_config(
    page_title="Mortgage Calculator",
    page_icon="🏠",
    layout="wide"
)

# Title and description
st.title("🏠 Mortgage Calculator")
st.markdown("Use this calculator to estimate your monthly mortgage payments and visualize your amortization schedule.")

# Sidebar with inputs
st.sidebar.header("Mortgage Inputs")

loan_amount = st.sidebar.number_input(
    "Loan Amount ($)",
    min_value=10000,
    max_value=10000000,
    value=300000,
    step=10000
)

interest_rate = st.sidebar.number_input(
    "Annual Interest Rate (%)",
    min_value=0.1,
    max_value=20.0,
    value=4.5,
    step=0.1
)

loan_term = st.sidebar.number_input(
    "Loan Term (Years)",
    min_value=1,
    max_value=40,
    value=30,
    step=1
)

# Calculate mortgage details
monthly_interest_rate = interest_rate / 100 / 12
total_payments = loan_term * 12
monthly_payment = loan_amount * (monthly_interest_rate * (1 + monthly_interest_rate) ** total_payments) / ((1 + monthly_interest_rate) ** total_payments - 1)

# Display calculated values
col1, col2, col3 = st.columns(3)
col1.metric("Monthly Payment", f"${monthly_payment:.2f}")
col2.metric("Total Payment", f"${monthly_payment * total_payments:.2f}")
col3.metric("Total Interest", f"${(monthly_payment * total_payments) - loan_amount:.2f}")

# Create amortization schedule
def create_amortization_schedule(loan_amount, interest_rate, loan_term):
    monthly_rate = interest_rate / 100 / 12
    total_payments = loan_term * 12
    
    schedule = []
    remaining_balance = loan_amount
    
    for payment_no in range(1, total_payments + 1):
        interest_payment = remaining_balance * monthly_rate
        principal_payment = monthly_payment - interest_payment
        remaining_balance -= principal_payment
        
        # Ensure balance doesn't go negative due to rounding
        if remaining_balance < 0:
            remaining_balance = 0
            
        schedule.append({
            'Payment': payment_no,
            'Payment Amount': monthly_payment,
            'Principal': principal_payment,
            'Interest': interest_payment,
            'Remaining Balance': remaining_balance
        })
    
    return pd.DataFrame(schedule)

# Generate amortization schedule
amortization_df = create_amortization_schedule(loan_amount, interest_rate, loan_term)

# Visualization section
st.header("Mortgage Visualization")

# Create tabs for different visualizations
tab1, tab2, tab3 = st.tabs(["Balance Over Time", "Payment Breakdown", "Amortization Schedule"])

with tab1:
    # Balance over time visualization
    st.subheader("Loan Balance Over Time")
    
    # Simplify the approach - use the full dataset but sample points for clearer visualization
    # Take initial point (0), yearly points, and final point
    yearly_points = [0] + [i*12 for i in range(1, loan_term+1) if i*12 < len(amortization_df)]
    if len(amortization_df)-1 not in yearly_points:
        yearly_points.append(len(amortization_df)-1)
    
    yearly_data = amortization_df.iloc[yearly_points].copy()
    
    # Scale values to make the chart clearer (showing in thousands)
    yearly_data['Remaining Balance (Thousands)'] = yearly_data['Remaining Balance'] / 1000
    
    balance_fig = px.line(
        yearly_data, 
        x='Payment', 
        y='Remaining Balance (Thousands)',
        title="Remaining Loan Balance Over Time",
        labels={"Payment": "Payment Number (Month)", "Remaining Balance (Thousands)": "Remaining Balance ($, thousands)"}
    )
    
    # Improve the styling
    balance_fig.update_traces(line=dict(width=3))
    balance_fig.update_layout(
        xaxis=dict(showgrid=True),
        yaxis=dict(showgrid=True)
    )
    
    st.plotly_chart(balance_fig)
    
    # Principal vs Interest over time
    st.subheader("Principal vs Interest Payments")
    # Show yearly data for this chart as well
    interest_yearly = amortization_df.groupby(amortization_df.index // 12)[['Interest']].sum().reset_index()
    interest_yearly['Payment'] = (interest_yearly['index'] + 1) * 12
    interest_yearly = interest_yearly.drop('index', axis=1)
    
    principal_yearly = amortization_df.groupby(amortization_df.index // 12)[['Principal']].sum().reset_index()
    principal_yearly['Payment'] = (principal_yearly['index'] + 1) * 12
    principal_yearly = principal_yearly.drop('index', axis=1)
    
    interest_data = pd.DataFrame({
        'Payment': interest_yearly['Payment'],
        'Payment Type': 'Interest',
        'Amount': interest_yearly['Interest']
    })
    
    principal_data = pd.DataFrame({
        'Payment': principal_yearly['Payment'],
        'Payment Type': 'Principal',
        'Amount': principal_yearly['Principal']
    })
    
    payment_data = pd.concat([interest_data, principal_data])
    
    payment_fig = px.line(
        payment_data, 
        x='Payment', 
        y='Amount', 
        color='Payment Type',
        title="Principal vs Interest Payments Over Time (Yearly)",
        labels={"Payment": "Payment (Month)", "Amount": "Amount ($)"}
    )
    st.plotly_chart(payment_fig)

with tab2:
    # Payment breakdown pie chart
    total_interest = (monthly_payment * total_payments) - loan_amount
    data = pd.DataFrame({
        'Category': ['Principal', 'Interest'],
        'Amount': [loan_amount, total_interest]
    })
    
    fig = px.pie(
        data, 
        values='Amount', 
        names='Category',
        title="Principal vs Interest",
        color_discrete_sequence=px.colors.qualitative.Set2
    )
    st.plotly_chart(fig)

with tab3:
    # Show amortization table (first 12 rows)
    st.subheader("Amortization Schedule (First Year)")
    st.dataframe(amortization_df.head(12).style.format({
        'Payment Amount': '${:.2f}',
        'Principal': '${:.2f}',
        'Interest': '${:.2f}',
        'Remaining Balance': '${:.2f}'
    }))
    
    st.markdown("*Note: Full amortization schedule available upon download*")
    
    # Download option
    @st.cache_data
    def convert_df_to_csv(df):
        return df.to_csv().encode('utf-8')
    
    csv = convert_df_to_csv(amortization_df)
    st.download_button(
        "Download Full Amortization Schedule",
        csv,
        "mortgage_amortization.csv",
        "text/csv",
        key='download-csv'
    )

# Additional mortgage information
st.header("Additional Information")
with st.expander("What is a mortgage?"):
    st.write("""
    A mortgage is a loan used to purchase or maintain a home, land, or other types of real estate. 
    The borrower agrees to pay the lender over time, typically in a series of regular payments that are divided into principal and interest.
    The property serves as collateral to secure the loan.
    """)

with st.expander("How to use this calculator"):
    st.write("""
    1. Adjust the loan amount, interest rate, and loan term using the sliders in the sidebar
    2. View your monthly payment and total costs
    3. Explore the different visualization tabs to understand your mortgage better
    4. Download the full amortization schedule for detailed information
    """)

with st.expander("Mortgage Terminology"):
    st.markdown("""
    - **Principal**: The initial amount of the loan
    - **Interest**: The cost of borrowing money, expressed as a percentage
    - **Amortization**: The process of paying off a debt through regular payments
    - **Term**: The length of time to repay the loan (usually in years)
    - **Monthly Payment**: The amount paid each month, including principal and interest
    """)

# Footer
st.markdown("---")
st.markdown("*This is a simple mortgage calculator for educational purposes only. Actual mortgage terms may vary.*") 