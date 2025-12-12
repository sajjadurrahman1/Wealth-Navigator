# app.py
# Streamlit app for a simple personal finance assistant (Germany)

import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt

from finance_logic import compute_financials, RECOMMENDED_PCT
from chat_assistant import generate_bot_reply, OPENAI_ENABLED


# Page setup
st.set_page_config(
    page_title="Personal Finance Assistant – Germany",
    page_icon="💶",
    layout="centered",
)


# App title and short intro
st.title("💶 Personal Finance Assistant – Germany")
st.write(
    "This app helps you understand your **budget, savings, and German tax classes (Steuerklassen)**, "
    "and includes an **AI assistant** powered by OpenAI.\n\n"
    "_All calculations are simplified and for educational purposes only._"
)


# Sidebar inputs
st.sidebar.header("📥 Your monthly details")

# Currency is only for display
currency = st.sidebar.selectbox("Currency", ["€", "$", "£", "₹"], index=0)

# Monthly gross income before tax
gross_income = st.sidebar.number_input(
    f"Monthly gross income (before tax) ({currency})",
    min_value=0.0,
    step=100.0,
    value=3000.0,
)

# German tax class (very simplified)
selected_tax_class = st.sidebar.selectbox(
    "Your tax class (Steuerklasse)",
    ["I", "II", "III", "IV", "V", "VI"],
)


# Optional savings goal
st.sidebar.markdown("### 🎯 Savings goal")

goal_amount = st.sidebar.number_input(
    f"Savings goal ({currency})",
    min_value=0.0,
    step=500.0,
    value=0.0,
)

goal_months = st.sidebar.number_input(
    "Goal timeframe (months)",
    min_value=1,
    value=12,
)


# Monthly expenses (after tax)
st.sidebar.markdown("### 🧾 Expenses")

expense_categories = [
    "Rent / Housing",
    "Food & Groceries",
    "Transport",
    "Utilities & Bills",
    "Entertainment & Eating Out",
    "Shopping & Other",
]

expenses = {}
for cat in expense_categories:
    expenses[cat] = st.sidebar.number_input(
        f"{cat} ({currency})",
        min_value=0.0,
        step=50.0,
        value=0.0,
    )

# Trigger analysis
analyze = st.sidebar.button("Analyze my situation 💡")


# Main analysis
if analyze:
    if gross_income <= 0:
        st.warning("Please enter a positive monthly gross income.")
    else:
        # Run all calculations
        ctx = compute_financials(
            gross_income=gross_income,
            selected_tax_class=selected_tax_class,
            expenses=expenses,
            goal_amount=goal_amount,
            goal_months=goal_months,
        )
        ctx["currency"] = currency

        # Summary numbers
        st.subheader("📊 Income, tax and budget")

        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Gross income", f"{currency}{ctx['gross_income']:,.0f}")
        col2.metric(
            f"Tax (Class {ctx['selected_tax_class']})",
            f"{currency}{ctx['estimated_tax_selected']:,.0f}",
        )
        col3.metric("Net income", f"{currency}{ctx['net_income']:,.0f}")
        col4.metric(
            "Savings",
            f"{currency}{ctx['savings']:,.0f}",
            f"{ctx['savings_rate']:.1f}%" if ctx["net_income"] > 0 else None,
        )

        # Basic feedback
        if ctx["savings"] < 0:
            st.error("You are spending more than you earn each month.")
        elif ctx["savings"] == 0:
            st.warning("You are breaking even.")
        else:
            st.success("You are saving money each month.")

        # Savings goal check
        st.subheader("🎯 Savings goal check")

        if goal_amount > 0:
            st.write(
                f"You want to save {currency}{goal_amount:,.0f} "
                f"in {goal_months} months."
            )
            st.write(
                f"You need about {currency}{ctx['required_monthly_savings']:,.0f} per month."
            )
        else:
            st.info("No savings goal set.")


        # Expense breakdown chart
        st.subheader("📉 Spending breakdown")

        if ctx["total_expenses"] > 0:
            df_expenses = pd.DataFrame(
                {"Category": expenses.keys(), "Amount": expenses.values()}
            ).set_index("Category")

            fig, ax = plt.subplots()
            ax.pie(
                df_expenses["Amount"],
                labels=df_expenses.index,
                autopct="%1.1f%%",
                startangle=90,
            )
            ax.axis("equal")
            st.pyplot(fig)
        else:
            st.info("No expenses entered yet.")

else:
    st.info("Enter your numbers on the left and click **Analyze my situation 💡**.")


# Chat assistant
st.write("---")
st.write("### 💬 Chat with your finance assistant")

# Initialize chat history once
if "messages" not in st.session_state:
    st.session_state.messages = [
        {
            "role": "assistant",
            "content": (
                "Hi! I can help you understand your budget, savings, "
                "and German tax classes."
            ),
        }
    ]

# Build context for the chatbot
current_ctx = compute_financials(
    gross_income=gross_income,
    selected_tax_class=selected_tax_class,
    expenses=expenses,
    goal_amount=goal_amount,
    goal_months=goal_months,
)
current_ctx["currency"] = currency

# Show chat history
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# User input
user_input = st.chat_input("Ask me something about your finances…")

if user_input:
    st.session_state.messages.append({"role": "user", "content": user_input})

    reply = generate_bot_reply(
        user_message=user_input,
        ctx=current_ctx,
        history=st.session_state.messages,
    )

    st.session_state.messages.append({"role": "assistant", "content": reply})

    with st.chat_message("assistant"):
        st.markdown(reply)
