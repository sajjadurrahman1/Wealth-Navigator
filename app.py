import streamlit as st
import pandas as pd

# ---------- PAGE CONFIG ----------
st.set_page_config(
    page_title="Personal Finance Assistant",
    page_icon="💸",
    layout="centered",
)

# ---------- TITLE & INTRO ----------
st.title("💸 Personal Finance Assistant")
st.write(
    "Enter your monthly income, expenses, and goals. "
    "I'll calculate your budget, show charts, compare with simple guidelines, "
    "and you can chat with me about your situation.\n\n"
    "_This is for education only and not professional financial advice._"
)

# ---------- SIDEBAR INPUTS ----------
st.sidebar.header("📥 Your monthly details")

currency = st.sidebar.selectbox("Currency", ["€", "$", "£", "₹"], index=0)

income = st.sidebar.number_input(
    f"Monthly net income ({currency})",
    min_value=0.0,
    step=100.0,
    value=3000.0,
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

st.sidebar.markdown("### 🧾 Expenses by category")

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

# ---------- CORE CALCULATIONS ----------
total_expenses = sum(expenses.values())
savings = income - total_expenses
savings_rate = (savings / income * 100) if income > 0 else 0

# Savings goal math
required_monthly_savings = (
    goal_amount / goal_months if goal_months > 0 else 0
) if goal_amount > 0 else 0

# Recommended guideline percentages (rule-of-thumb)
recommended_pct = {
    "Rent / Housing": 0.30,              # 30%
    "Food & Groceries": 0.15,            # 15%
    "Transport": 0.10,                   # 10%
    "Utilities & Bills": 0.10,           # 10%
    "Entertainment & Eating Out": 0.10,  # 10%
    "Shopping & Other": 0.10,            # 10%
}
# Remaining income ideally goes to savings

st.write("### ▶️ When you're ready, analyze your budget")
analyze = st.button("Analyze my budget 💡")

# ---------- MAIN ANALYSIS OUTPUT ----------
if analyze:
    if income <= 0:
        st.warning("Please enter a positive monthly income in the sidebar first.")
    else:
        # ----- SUMMARY METRICS -----
        st.subheader("📊 Budget Summary")

        col1, col2, col3 = st.columns(3)
        col1.metric("Income", f"{currency}{income:,.0f}")
        col2.metric("Total expenses", f"{currency}{total_expenses:,.0f}")
        col3.metric(
            "Estimated savings",
            f"{currency}{savings:,.0f}",
            f"{savings_rate:.1f}%" if income > 0 else None,
        )

        if savings < 0:
            st.error(
                f"You're spending **{currency}{abs(savings):,.0f} more** than you earn each month. "
                "This is not sustainable — you need to cut costs or increase income."
            )
        elif savings == 0:
            st.warning(
                "You’re breaking even: you save **0**. "
                "Try to aim for at least 10–20% of your income as savings."
            )
        else:
            st.success(
                f"Nice! You are saving about **{currency}{savings:,.0f}** each month "
                f"(**{savings_rate:.1f}%** of your income)."
            )

        # ----- GOAL FEASIBILITY (FROM FIRST VERSION) -----
        st.write("---")
        st.subheader("🎯 Goal feasibility")

        if goal_amount <= 0:
            st.info(
                "You haven't set a savings goal amount yet. "
                "Enter a goal in the sidebar to see if it's realistic."
            )
        else:
            st.write(
                f"Your goal is to save **{currency}{goal_amount:,.0f}** "
                f"in **{goal_months} months**."
            )
            st.write(
                f"To reach this goal, you’d need to save about "
                f"**{currency}{required_monthly_savings:,.0f} per month**."
            )

            if savings <= 0:
                st.warning(
                    "Right now, you are not saving money (or are in deficit). "
                    "You need to fix your monthly cashflow first before this goal is realistic."
                )
            else:
                if savings >= required_monthly_savings:
                    st.success(
                        "Based on your current numbers, your goal looks **mathematically achievable**.\n\n"
                        "Make sure you consistently move that amount into savings each month."
                    )
                else:
                    gap = required_monthly_savings - savings
                    st.warning(
                        f"Currently you can save about **{currency}{savings:,.0f} per month**, "
                        f"but you need **{currency}{required_monthly_savings:,.0f}**.\n\n"
                        f"You're short by roughly **{currency}{gap:,.0f} per month**.\n"
                        "Options:\n"
                        "- Reduce expenses\n"
                        "- Increase income\n"
                        "- Extend the time frame for your goal"
                    )

        # ----- EXPENDITURE GRAPH (BAR CHART) -----
        st.write("---")
        st.subheader("📉 Your spending by category")

        df_expenses = pd.DataFrame(
            {"Category": list(expenses.keys()), "Amount": list(expenses.values())}
        ).set_index("Category")

        if total_expenses > 0:
            st.bar_chart(df_expenses)
        else:
            st.info("You haven't entered any expenses yet. Add some amounts in the sidebar.")

        # ----- GUIDELINE COMPARISON + ADVICE -----
        st.write("---")
        st.subheader("🧠 Where you might need to work on your budget")

        if income == 0:
            st.info("Once you enter an income, I can compare your expenses to guidelines.")
        else:
            overspending_tips = []
            guideline_rows = []

            for cat, amount in expenses.items():
                actual_pct = amount / income if income > 0 else 0
                rec_pct = recommended_pct.get(cat, 0.10)

                guideline_rows.append(
                    {
                        "Category": cat,
                        "You spend (%)": round(actual_pct * 100, 1),
                        "Suggested max (%)": round(rec_pct * 100, 1),
                    }
                )

                # Mark overspending if > recommended + 5 percentage points
                if actual_pct > rec_pct + 0.05:
                    overspending_tips.append(
                        f"- **{cat}**: you spend about **{actual_pct*100:.1f}%** of your income. "
                        f"Suggested maximum is around **{rec_pct*100:.1f}%**."
                    )

            st.write("#### 📋 Comparison with simple guideline")
            st.dataframe(pd.DataFrame(guideline_rows).set_index("Category"))

            st.write("#### 🎯 Comments on your budget")

            if savings < 0:
                st.write(
                    "- Overall you’re running a **deficit**. Start by targeting the biggest categories where you "
                    "spend more than the suggested percentage."
                )
            elif savings_rate < 10:
                st.write(
                    "- You are saving **less than 10%** of your income. Try to reduce non-essential categories "
                    "to push savings closer to **15–20%**."
                )
            elif 10 <= savings_rate < 20:
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
                    "\nTry lowering those categories a bit and re-running the analysis to see the effect."
                )
            else:
                st.write(
                    "Based on these rough guidelines, none of your categories look **massively** out of control. "
                    "You can still adjust them depending on your personal priorities."
                )

        st.caption(
            "Presentation tip: change a category (like Entertainment) live and show how the graph, "
            "savings and advice all update."
        )
else:
    st.info("➡️ Enter your numbers on the left, then click **Analyze my budget 💡**.")


# ---------- CHAT ASSISTANT (FROM FIRST VERSION + UPDATED CONTEXT) ----------
st.write("---")
st.write("### 💬 Chat with your finance assistant")

# Initialize chat history
if "messages" not in st.session_state:
    st.session_state.messages = [
        {
            "role": "assistant",
            "content": (
                "Hi! I'm your finance assistant 🤖\n\n"
                "You can ask me things like:\n"
                "- *Is my savings goal realistic with my current budget?*\n"
                "- *How much should I save every month to reach my goal?*\n"
                "- *Can you summarise my budget?*\n"
                "- *Where am I overspending?*"
            ),
        }
    ]


def generate_bot_reply(user_message: str) -> str:
    """
    Simple rule-based assistant using the current financial context.
    You can replace this with an API call to a real LLM later.
    """
    ctx = {
        "income": income,
        "total_expenses": total_expenses,
        "savings": savings,
        "savings_rate": savings_rate,
        "goal_amount": goal_amount,
        "goal_months": goal_months,
        "required_savings": required_monthly_savings,
        "currency": currency,
        "expenses": expenses,
        "recommended_pct": recommended_pct,
    }

    text = user_message.lower()

    # 1) Questions about reaching the goal
    if "reach" in text or ("goal" in text and "save" in text):
        if ctx["goal_amount"] <= 0:
            return (
                "You haven't set a savings goal yet. Add a goal amount and timeframe in the sidebar, "
                "then ask me again."
            )

        msg = (
            f"Your goal is **{ctx['currency']}{ctx['goal_amount']:,.0f}** "
            f"in **{ctx['goal_months']} months**.\n\n"
            f"To reach that, you’d need to save about "
            f"**{ctx['currency']}{ctx['required_savings']:,.0f} per month**.\n"
        )

        if ctx["savings"] <= 0:
            msg += (
                "\nRight now you are not saving anything (or you’re in deficit). "
                "You’ll need to fix your monthly cashflow first by cutting expenses "
                "or increasing income."
            )
        elif ctx["savings"] >= ctx["required_savings"]:
            msg += (
                "\nBased on your current numbers, this goal is **mathematically achievable**. "
                "Just make sure you consistently save that amount."
            )
        else:
            gap = ctx["required_savings"] - ctx["savings"]
            msg += (
                f"\nCurrently you save about **{ctx['currency']}{ctx['savings']:,.0f} per month**, "
                f"so you're short by roughly **{ctx['currency']}{gap:,.0f} per month**.\n"
                "You could:\n"
                "- Reduce expenses\n"
                "- Increase income\n"
                "- Extend your goal timeframe"
            )
        return msg

    # 2) "How much should I save?"
    if "how much" in text and "save" in text:
        if ctx["goal_amount"] <= 0:
            return (
                "To estimate how much to save each month, I need a goal amount and timeframe. "
                "Please set those in the sidebar and ask again."
            )
        return (
            f"To reach **{ctx['currency']}{ctx['goal_amount']:,.0f}** in "
            f"**{ctx['goal_months']} months**, you should save about "
            f"**{ctx['currency']}{ctx['required_savings']:,.0f} per month**.\n\n"
            f"Right now, it looks like you can save about "
            f"**{ctx['currency']}{ctx['savings']:,.0f} per month** "
            f"(**{ctx['savings_rate']:.1f}%** of your income)."
        )

    # 3) Budget summary
    if "budget" in text or "overview" in text or "summary" in text:
        lines = [
            f"- Income: **{ctx['currency']}{ctx['income']:,.0f}**",
            f"- Total expenses: **{ctx['currency']}{ctx['total_expenses']:,.0f}**",
            f"- Savings: **{ctx['currency']}{ctx['savings']:,.0f}** "
            f"({ctx['savings_rate']:.1f}% of income)",
            "",
            "By category:",
        ]
        for cat, amount in ctx["expenses"].items():
            if ctx["income"] > 0:
                pct = amount / ctx["income"] * 100
            else:
                pct = 0
            lines.append(
                f"  - {cat}: **{ctx['currency']}{amount:,.0f}** ({pct:.1f}% of income)"
            )
        return "\n".join(lines)

    # 4) Overspending / where to improve
    if "overspend" in text or "improve" in text or "reduce" in text or "cut" in text:
        if ctx["income"] <= 0:
            return "I need a positive income value to judge where you're overspending."

        overspending_tips = []
        for cat, amount in ctx["expenses"].items():
            actual_pct = amount / ctx["income"] if ctx["income"] > 0 else 0
            rec_pct = ctx["recommended_pct"].get(cat, 0.10)
            if actual_pct > rec_pct + 0.05:
                overspending_tips.append(
                    f"- **{cat}**: you spend about **{actual_pct*100:.1f}%** of your income, "
                    f"guideline is around **{rec_pct*100:.1f}%**."
                )

        if not overspending_tips:
            return (
                "Based on simple guideline percentages, none of your categories look extremely high. "
                "But you can still tweak them based on your personal priorities."
            )

        msg = "Here are the main areas where you may be overspending:\n\n"
        msg += "\n".join(overspending_tips)
        msg += (
            "\n\nTry lowering these categories slightly and see how it affects your savings."
        )
        return msg

    # 5) Fallback generic answer
    return (
        "I’ve read your message, but I’m still a simple rules-based bot.\n\n"
        "You can ask me about:\n"
        "- Whether your savings goal is realistic\n"
        "- How much to save per month\n"
        "- A summary of your budget\n"
        "- Where you might be overspending\n\n"
        "Also try changing your numbers in the sidebar and asking again."
    )


# Display chat history
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# Chat input
user_input = st.chat_input("Ask me something about your finances…")

if user_input:
    # Add user message
    st.session_state.messages.append({"role": "user", "content": user_input})

    # Generate and add assistant response
    reply = generate_bot_reply(user_input)
    st.session_state.messages.append({"role": "assistant", "content": reply})

    # Display just-entered messages
    with st.chat_message("user"):
        st.markdown(user_input)
    with st.chat_message("assistant"):
        st.markdown(reply)
