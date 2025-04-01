import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import math
import openai

# Configure page settings
st.set_page_config(
    page_title="Mortgage & ChatGPT",
    page_icon="🏠",
    layout="wide"
)

# Create sidebar with page navigation
st.sidebar.title("Navigation")
page = st.sidebar.radio("Go to", ["Mortgage Calculator", "ChatGPT"])

# Initialize session state for chat history
if "messages" not in st.session_state:
    st.session_state.messages = []

# Set OpenAI API key - use Streamlit secrets in production
# For security, we're using a placeholder here
# In Streamlit Cloud, you'll set this in the app's secrets management
openai_api_key = st.sidebar.text_input("OpenAI API Key", 
                                      type="password", 
                                      placeholder="sk-...",
                                      help="Enter your OpenAI API key here. It will not be stored.")

# Disable the API key warning in sidebar when deploying
if not openai_api_key:
    st.sidebar.warning("Please enter your OpenAI API key to use the ChatGPT feature.")

# Helper function for older Streamlit versions
def legacy_chat_message(role, content):
    if role == "user":
        st.markdown(f"**You:** {content}")
    else:  # assistant
        st.markdown(f"**Assistant:** {content}")
    st.markdown("---")

# Mortgage Calculator Page
if page == "Mortgage Calculator":
    st.title("Mortgage Repayments Calculator")

    st.write("### Input Data")
    col1, col2 = st.columns(2)
    home_value = col1.number_input("Home Value", min_value=0, value=500000)
    deposit = col1.number_input("Deposit", min_value=0, value=100000)
    interest_rate = col2.number_input("Interest Rate (in %)", min_value=0.0, value=5.5)
    loan_term = col2.number_input("Loan Term (in years)", min_value=1, value=30)

    # Calculate the repayments.
    loan_amount = home_value - deposit
    monthly_interest_rate = (interest_rate / 100) / 12
    number_of_payments = loan_term * 12
    monthly_payment = (
        loan_amount
        * (monthly_interest_rate * (1 + monthly_interest_rate) ** number_of_payments)
        / ((1 + monthly_interest_rate) ** number_of_payments - 1)
    )

    # Display the repayments.
    total_payments = monthly_payment * number_of_payments
    total_interest = total_payments - loan_amount

    st.write("### Repayments")
    col1, col2, col3 = st.columns(3)
    col1.metric(label="Monthly Repayments", value=f"${monthly_payment:,.2f}")
    col2.metric(label="Total Repayments", value=f"${total_payments:,.0f}")
    col3.metric(label="Total Interest", value=f"${total_interest:,.0f}")

    # Create a data-frame with the payment schedule.
    schedule = []
    remaining_balance = loan_amount

    for i in range(1, number_of_payments + 1):
        interest_payment = remaining_balance * monthly_interest_rate
        principal_payment = monthly_payment - interest_payment
        remaining_balance -= principal_payment
        year = math.ceil(i / 12)  # Calculate the year into the loan
        schedule.append(
            [
                i,
                monthly_payment,
                principal_payment,
                interest_payment,
                remaining_balance,
                year,
            ]
        )

    df = pd.DataFrame(
        schedule,
        columns=["Month", "Payment", "Principal", "Interest", "Remaining Balance", "Year"],
    )

    # Display the data-frame as a chart.
    st.write("### Payment Schedule")
    payments_df = df[["Year", "Remaining Balance"]].groupby("Year").min()
    
    # Improve the visualization
    st.line_chart(payments_df)
    
    # Display amortization table for the first year
    st.write("### Amortization Schedule (First Year)")
    first_year_df = df[df["Year"] == 1]
    st.dataframe(first_year_df.style.format({
        "Payment": "${:.2f}",
        "Principal": "${:.2f}",
        "Interest": "${:.2f}",
        "Remaining Balance": "${:.2f}"
    }))
    
    # Download option for full schedule
    @st.cache_data
    def convert_df_to_csv(df):
        return df.to_csv().encode('utf-8')
    
    csv = convert_df_to_csv(df)
    st.download_button(
        "Download Full Amortization Schedule",
        csv,
        "mortgage_amortization.csv",
        "text/csv",
        key='download-csv'
    )

# ChatGPT Page
elif page == "ChatGPT":
    st.title("Chat with GPT")
    st.write("Have a conversation with ChatGPT. Ask any questions about mortgages or any other topic.")
    
    # Skip API calls if no key is provided
    if not openai_api_key:
        st.info("Please enter your OpenAI API key in the sidebar to use this feature.")
    else:
        # Display chat messages from history
        has_chat_message = True
        try:
            # Test if chat_message exists
            st.chat_message
            for message in st.session_state.messages:
                with st.chat_message(message["role"]):
                    st.markdown(message["content"])
        except AttributeError:
            # Fallback for older Streamlit versions
            has_chat_message = False
            st.write("### Chat History")
            for message in st.session_state.messages:
                legacy_chat_message(message["role"], message["content"])
        
        # Accept user input - with fallback for older Streamlit versions
        try:
            prompt = st.chat_input("What would you like to know?")
        except AttributeError:
            # Fallback for older Streamlit versions that don't have chat_input
            st.write("### Your message")
            prompt = st.text_area("Type your message here:", key="user_input", height=100)
            send_button = st.button("Send")
            if send_button:
                pass  # This will allow the prompt to be processed below
            else:
                prompt = None  # If button not clicked, don't process input
                
        if prompt:
            # Add user message to chat history
            st.session_state.messages.append({"role": "user", "content": prompt})
            
            # Display user message in chat message container
            if has_chat_message:
                with st.chat_message("user"):
                    st.markdown(prompt)
            
            # Display assistant thinking indicator
            if has_chat_message:
                with st.chat_message("assistant"):
                    message_placeholder = st.empty()
                    message_placeholder.markdown("Thinking...")
            else:
                st.write("**Assistant is thinking...**")
                message_placeholder = st.empty()
                message_placeholder.markdown("Thinking...")
                
            try:
                # Initialize OpenAI client with the provided API key
                client = openai.OpenAI(api_key=openai_api_key)
                
                # Call OpenAI API
                response = client.chat.completions.create(
                    model="gpt-4o",
                    messages=[
                        {"role": m["role"], "content": m["content"]}
                        for m in st.session_state.messages
                    ],
                    stream=True
                )
                
                # Stream the response
                full_response = ""
                for chunk in response:
                    if chunk.choices[0].delta.content is not None:
                        full_response += chunk.choices[0].delta.content
                    message_placeholder.markdown(full_response + "▌")
                
                # Final response without cursor
                message_placeholder.markdown(full_response)
                
                # Add assistant response to chat history
                st.session_state.messages.append({"role": "assistant", "content": full_response})
                
                # If using legacy display, show the new message
                if not has_chat_message:
                    st.write("**New response:**")
                    legacy_chat_message("assistant", full_response)
            
            except Exception as e:
                error_message = f"Error: {str(e)}"
                message_placeholder.markdown(error_message)
                st.error(f"An error occurred: {str(e)}")
                
                # Add error message to chat history instead of undefined full_response
                st.session_state.messages.append({"role": "assistant", "content": error_message})

        # Add a button to clear chat history
        if st.button("Clear Conversation"):
            st.session_state.messages = []
            # Use the appropriate rerun method based on Streamlit version
            try:
                st.rerun()
            except AttributeError:
                # Fallback for older Streamlit versions
                st.experimental_rerun()