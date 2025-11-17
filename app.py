# app.py

import streamlit as st
import pandas as pd

from finance_logic import compute_financials, RECOMMENDED_PCT
from chat_assistant import generate_bot_reply, OPENAI_ENABLED

# ---------- PAGE CONFIG ----------
st.set_page_config(
    page_title="Personal Finance Assistant – Germany",
    page_icon="💶",
    layout="centered",
)

# ---------- TITLE & INTRO ----------
st.title("💶 Personal Finance Assistant – Germany")
st.write(
    "This app helps you understand your **budget, savings, and German tax classes (Steuerklassen)**, "
    "and includes an **AI assistant** powered by OpenAI.\n\n"
    "_All calculations are simplified and for educational purposes only – "
    "not professional tax or financial advice._"
)

if OPENAI_ENABLED:
    st.success("✅ For further guidence you can ask also"
    ".")
else:
    st.info(
        "ℹ️ OpenAI API key not found. The chat assistant will use a simple built-in logic.\n\n"
        "Set the `OPENAI_API_KEY` environment variable to enable OpenAI."
    )

# ---------- SIDEBAR INPUTS ----------
st.sidebar.header("📥 Your monthly details")

currency = st.sidebar.selectbox("Currency", ["€", "$", "£", "₹"], index=0)

gross_income = st.sidebar.number_input(
    f"Monthly gross income (before tax) ({currency})",
    min_value=0.0,
    step=100.0,
    value=3000.0,
    help="Bruttoeinkommen pro Monat (before income tax).",
)

selected_tax_class = st.sidebar.selectbox(
    "Your tax class (Steuerklasse)",
    ["I", "II", "III", "IV", "V", "VI"],
    help="Very simplified impact for demo. Real tax can be different.",
)

st.sidebar.markdown("### 🎯 Savings goal (optional)")

goal_amount = st.sidebar.number_input(
    f"Savings goal ({currency})",
    min_value=0.0,
    step=500.0,
    value=0.0,
    help="How much money you want to save in total.",
)

goal_months = st.sidebar.number_input(
    "Goal timeframe (months)",
    min_value=1,
    step=1,
    value=12,
    help="In how many months you want to reach this goal.",
)

st.sidebar.markdown("### 🧾 Expenses by category (per month, after tax)")

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

st.write("### ▶️ When you're ready, analyze your budget + tax")
analyze = st.button("Analyze my situation 💡")

# ---------- MAIN ANALYSIS ----------
if analyze:
    if gross_income <= 0:
        st.warning("Please enter a positive monthly gross income in the sidebar first.")
    else:
        # Compute all financials
        ctx = compute_financials(
            gross_income=gross_income,
            selected_tax_class=selected_tax_class,
            expenses=expenses,
            goal_amount=goal_amount,
            goal_months=goal_months,
        )
        # add currency to context for the chat assistant
        ctx["currency"] = currency

        # ----- SUMMARY METRICS -----
        st.subheader("📊 Income, Tax & Budget Summary")

        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Gross income", f"{currency}{ctx['gross_income']:,.0f}")
        col2.metric(
            f"Tax (Class {ctx['selected_tax_class']})",
            f"{currency}{ctx['estimated_tax_selected']:,.0f}",
        )
        col3.metric("Net income", f"{currency}{ctx['net_income']:,.0f}")
        col4.metric(
            "Savings (approx.)",
            f"{currency}{ctx['savings']:,.0f}",
            f"{ctx['savings_rate']:.1f}%" if ctx['net_income'] > 0 else None,
        )

        if ctx["net_income"] <= 0:
            st.error(
                "Your estimated net income is **0 or negative**. "
                "Check if the entered gross income is realistic."
            )

        if ctx["savings"] < 0:
            st.error(
                f"You're spending **{currency}{abs(ctx['savings']):,.0f} more** than your net income each month. "
                "This is not sustainable — you need to cut costs or increase income."
            )
        elif ctx["savings"] == 0:
            st.warning(
                "You’re breaking even: you save **0**. "
                "Try to aim for at least 10–20% of your **net income** as savings."
            )
        else:
            st.success(
                f"Nice! You are saving about **{currency}{ctx['savings']:,.0f}** each month "
                f"(**{ctx['savings_rate']:.1f}%** of your net income)."
            )

        st.caption(
            "All tax values are simplified estimates. Real German tax depends on many "
            "more factors (health insurance, pension, church tax, etc.)."
        )

        # ----- GOAL FEASIBILITY -----
        st.write("---")
        st.subheader("🎯 Goal feasibility (based on net income)")

        if ctx["goal_amount"] <= 0:
            st.info(
                "You haven't set a savings goal amount yet. "
                "Enter a goal in the sidebar to see if it's realistic."
            )
        else:
            st.write(
                f"Your goal is to save **{currency}{ctx['goal_amount']:,.0f}** "
                f"in **{ctx['goal_months']} months**."
            )
            st.write(
                f"To reach this goal, you’d need to save about "
                f"**{currency}{ctx['required_monthly_savings']:,.0f} per month**."
            )

            if ctx["savings"] <= 0:
                st.warning(
                    "Right now, you are not saving money (or are in deficit). "
                    "You need to fix your monthly cashflow first before this goal is realistic."
                )
            else:
                if ctx["savings"] >= ctx["required_monthly_savings"]:
                    st.success(
                        "Based on your current numbers, your goal looks **mathematically achievable**.\n\n"
                        "Make sure you consistently move that amount into savings each month."
                    )
                else:
                    gap = ctx["required_monthly_savings"] - ctx["savings"]
                    st.warning(
                        f"Currently you can save about **{currency}{ctx['savings']:,.0f} per month**, "
                        f"but you need **{currency}{ctx['required_monthly_savings']:,.0f}**.\n\n"
                        f"You're short by roughly **{currency}{gap:,.0f} per month**.\n"
                        "Options:\n"
                        "- Reduce expenses\n"
                        "- Increase income\n"
                        "- Extend the time frame for your goal"
                    )

        # ----- EXPENDITURE GRAPH (BAR CHART) -----
        st.write("---")
        st.subheader("📉 Your spending by category (vs. net income)")

        df_expenses = pd.DataFrame(
            {"Category": list(expenses.keys()), "Amount": list(expenses.values())}
        ).set_index("Category")

        if ctx["total_expenses"] > 0:
            st.bar_chart(df_expenses)
        else:
            st.info("You haven't entered any expenses yet. Add some amounts in the sidebar.")

        # ----- GUIDELINE COMPARISON + BUDGET ADVICE -----
        st.write("---")
        st.subheader("🧠 Where you might need to work on your budget")

        if ctx["net_income"] == 0:
            st.info("Once your net income is positive, I can compare your expenses to guidelines.")
        else:
            overspending_tips = []
            guideline_rows = []

            for cat, amount in expenses.items():
                actual_pct = amount / ctx["net_income"] if ctx["net_income"] > 0 else 0
                rec_pct = RECOMMENDED_PCT.get(cat, 0.10)

                guideline_rows.append(
                    {
                        "Category": cat,
                        "You spend (% of net)": round(actual_pct * 100, 1),
                        "Suggested max (%)": round(rec_pct * 100, 1),
                    }
                )

                if actual_pct > rec_pct + 0.05:
                    overspending_tips.append(
                        f"- **{cat}**: you spend about **{actual_pct*100:.1f}%** of your net income. "
                        f"Suggested maximum is around **{rec_pct*100:.1f}%**."
                    )

            st.write("#### 📋 Comparison with simple guideline")
            st.dataframe(pd.DataFrame(guideline_rows).set_index("Category"))

            st.write("#### 🎯 Comments on your budget")

            if ctx["savings"] < 0:
                st.write(
                    "- Overall you’re running a **deficit**. Start by targeting the biggest categories where you "
                    "spend more than the suggested percentage."
                )
            elif ctx["savings_rate"] < 10:
                st.write(
                    "- You are saving **less than 10%** of your net income. Try to reduce non-essential categories "
                    "to push savings closer to **15–20%**."
                )
            elif 10 <= ctx["savings_rate"] < 20:
                st.write(
                    "- You’re doing **okay** (saving 10–20%). You could still optimise a few categories to reach "
                    "a stronger savings rate."
                )
            else:
                st.write(
                    "- You’re doing **great** in terms of savings rate! Now the focus is fine-tuning where your "
                    "spending goes so it matches your priorities."
                )

            if overspending_tips:
                st.write("Here are the main areas to work on:")
                for tip in overspending_tips:
                    st.markdown(tip)
                st.write(
                    "\nTry lowering these categories a bit and re-running the analysis to see the effect."
                )
            else:
                st.write(
                    "Based on these rough guidelines, none of your categories look **massively** out of control. "
                    "You can still adjust them depending on your personal priorities."
                )

        # ----- TAX CLASS COMPARISON (TABLE + BAR CHART) -----
        st.write("---")
        st.subheader("🇩🇪 Tax comparison across all classes (simplified)")

        tax_table_rows = []
        for cls, tax_value in ctx["tax_per_class"].items():
            cls_net = ctx["gross_income"] - tax_value
            tax_table_rows.append({
                "Tax Class": cls,
                "Estimated Tax / Month": round(tax_value, 2),
                "Net Income / Month": round(cls_net, 2),
            })

        df_tax = pd.DataFrame(tax_table_rows).set_index("Tax Class")
        st.write("#### 💶 Estimated monthly tax & net income per Steuerklasse")
        st.dataframe(df_tax.style.format({
            "Estimated Tax / Month": f"{currency}{{:,.2f}}",
            "Net Income / Month": f"{currency}{{:,.2f}}",
        }))

        st.write("#### 📊 Tax per class (bar chart)")
        df_tax_chart = pd.DataFrame({"Tax / Month": ctx["tax_per_class"]})
        st.bar_chart(df_tax_chart)

else:
    st.info("➡️ Enter your numbers on the left, then click **Analyze my situation 💡**.")

# ---------- CHAT ASSISTANT ----------
st.write("---")
st.write("### 💬 Chat with your finance & tax assistant")

# Initialize chat history
if "messages" not in st.session_state:
    st.session_state.messages = [
        {
            "role": "assistant",
            "content": (
                "Hi! I'm your finance assistant 🤖 (Germany edition)\n\n"
                "You can ask me things like:\n"
                "- *Is my savings goal realistic with my current net income?*\n"
                "- *How much should I save every month to reach my goal?*\n"
                "- *Can you summarise my budget?*\n"
                "- *Where am I overspending?*\n"
                "- *What does my Steuerklasse mean for my net income (roughly)?*"
            ),
        }
    ]

# Build current context for chat (even if analyze not clicked, we pass something)
current_ctx = compute_financials(
    gross_income=gross_income,
    selected_tax_class=selected_tax_class,
    expenses=expenses,
    goal_amount=goal_amount,
    goal_months=goal_months,
)
current_ctx["currency"] = currency

# Display chat history
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

user_input = st.chat_input("Ask me something about your finances or taxes…")

if user_input:
    # Add user message
    st.session_state.messages.append({"role": "user", "content": user_input})

    # Generate and add assistant response
    reply = generate_bot_reply(
        user_message=user_input,
        ctx=current_ctx,
        history=st.session_state.messages,
    )
    st.session_state.messages.append({"role": "assistant", "content": reply})

    # Display just-entered messages
    with st.chat_message("user"):
        st.markdown(user_input)
    with st.chat_message("assistant"):
        st.markdown(reply)
