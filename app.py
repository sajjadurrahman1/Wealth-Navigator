import streamlit as st
import pandas as pd

# ---------- PAGE CONFIG ----------
st.set_page_config(
    page_title="Personal Finance Assistant – Germany",
    page_icon="💶",
    layout="wide",
)

# ---------- CUSTOM STYLES ----------
st.markdown(
    """
    <style>
    /* Overall background */
    .stApp {
        background: linear-gradient(135deg, #0f172a 0%, #111827 40%, #020617 100%);
        color: #e5e7eb;
        font-family: system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
    }

    /* Main containers */
    .main-card {
        background: rgba(15, 23, 42, 0.9);
        padding: 1.5rem 1.8rem;
        border-radius: 1.2rem;
        border: 1px solid rgba(148, 163, 184, 0.3);
        box-shadow: 0 18px 45px rgba(15, 23, 42, 0.8);
        margin-bottom: 1.5rem;
    }

    .metric-card {
        background: rgba(15, 23, 42, 0.95);
        padding: 1.1rem 1.3rem;
        border-radius: 1.0rem;
        border: 1px solid rgba(148, 163, 184, 0.4);
    }

    .section-title {
        font-size: 1.2rem;
        font-weight: 600;
        letter-spacing: 0.04em;
        text-transform: uppercase;
        color: #9ca3af;
    }

    .hero-title {
        font-size: 2.1rem;
        font-weight: 700;
        margin-bottom: 0.3rem;
        color: #f9fafb;
    }

    .hero-subtitle {
        font-size: 0.95rem;
        color: #9ca3af;
        max-width: 38rem;
    }

    .tag-pill {
        display: inline-block;
        padding: 0.2rem 0.7rem;
        border-radius: 999px;
        font-size: 0.75rem;
        background: rgba(34,197,94,0.12);
        color: #bbf7d0;
        border: 1px solid rgba(34,197,94,0.4);
        margin-right: 0.4rem;
    }

    /* Chat bubbles */
    .chat-bubble-user {
        background: rgba(59,130,246,0.15);
        padding: 0.75rem 0.9rem;
        border-radius: 0.9rem;
        border-top-right-radius: 0.2rem;
        border: 1px solid rgba(59,130,246,0.5);
        margin-bottom: 0.4rem;
    }
    .chat-bubble-assistant {
        background: rgba(15,23,42,0.95);
        padding: 0.75rem 0.9rem;
        border-radius: 0.9rem;
        border-top-left-radius: 0.2rem;
        border: 1px solid rgba(148,163,184,0.5);
        margin-bottom: 0.4rem;
    }

    /* Dataframe tweaks */
    .dataframe table {
        color: #e5e7eb !important;
    }

    /* Sidebar tweaks */
    section[data-testid="stSidebar"] {
        background: rgba(15, 23, 42, 0.98);
        border-right: 1px solid rgba(148, 163, 184, 0.4);
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# ---------- TAX FUNCTIONS (SIMPLIFIED, EDUCATIONAL ONLY) ----------
def calculate_german_income_tax(monthly_income: float) -> float:
    """
    Simplified German income tax estimation.
    Converts monthly → yearly → applies progressive tax → back to monthly.

    ⚠️ Educational approximation only – real German tax law is more complex.
    """
    annual_income = monthly_income * 12

    if annual_income <= 11604:
        tax_year = 0

    elif annual_income <= 66760:
        # Very rough linear-progressive approximation between 11,605 and 66,760
        tax_year = (annual_income - 11604) * 0.20  # ~20% average in this band

    elif annual_income <= 277825:
        tax_year = (55156 * 0.20) + (annual_income - 66760) * 0.42

    else:
        tax_year = (
            (55156 * 0.20) +
            (211065 * 0.42) +
            (annual_income - 277825) * 0.45
        )

    return tax_year / 12  # monthly tax


def apply_tax_class_modifier(base_tax: float, tax_class: str) -> float:
    """
    Simple adjustment based on German tax classes (Steuerklassen).
    ⚠️ Highly simplified! Real impact depends on family situation, spouse income, etc.
    """
    modifiers = {
        "I": 1.00,   # single
        "II": 0.90,  # single parent
        "III": 0.80, # married higher earner
        "IV": 1.00,  # married equal earners
        "V": 1.20,   # married lower earner
        "VI": 1.30,  # second job
    }
    return base_tax * modifiers.get(tax_class, 1.00)


# ---------- HERO SECTION ----------
with st.container():
    col_left, col_right = st.columns([2.2, 1])

    with col_left:
        st.markdown(
            """
            <div class="hero-title">💶 Smart Finance & Tax Assistant – Germany</div>
            <div class="hero-subtitle">
                See your <b>net income</b>, budget, and simplified <b>Steuerklasse</b> impact in one view.
                Perfect for experimenting with “what if I earn more / change tax class / cut some expenses”.
            </div>
            <br />
            <span class="tag-pill">Student capstone demo</span>
            <span class="tag-pill">GDPR-conscious</span>
            <span class="tag-pill">Simplified German taxes</span>
            """,
            unsafe_allow_html=True,
        )

    with col_right:
        with st.container():
            st.markdown('<div class="metric-card">', unsafe_allow_html=True)
            st.markdown(
                """
                <div class="section-title">Quick reminder</div>
                <p style="font-size:0.85rem; color:#d1d5db; margin-top:0.4rem;">
                    All calculations in this app are simplified and for educational purposes only.<br>
                    Real tax and financial decisions should be checked with official tools or a
                    Steuerberater.
                </p>
                """,
                unsafe_allow_html=True,
            )
            st.markdown("</div>", unsafe_allow_html=True)

# ---------- SIDEBAR INPUTS ----------
st.sidebar.header("📥 Profile & Inputs")

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

st.sidebar.markdown("---")
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

st.sidebar.markdown("---")
st.sidebar.markdown("### 🧾 Monthly expenses (after tax)")

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

st.sidebar.markdown("---")
st.sidebar.caption("Tip: change numbers live during your presentation and show how all sections react.")

# ---------- CORE CALCULATIONS ----------
base_tax = calculate_german_income_tax(gross_income)
estimated_tax_selected = apply_tax_class_modifier(base_tax, selected_tax_class)
net_income = gross_income - estimated_tax_selected

total_expenses = sum(expenses.values())
savings = net_income - total_expenses
savings_rate = (savings / net_income * 100) if net_income > 0 else 0

required_monthly_savings = (
    goal_amount / goal_months if goal_months > 0 else 0
) if goal_amount > 0 else 0

recommended_pct = {
    "Rent / Housing": 0.30,
    "Food & Groceries": 0.15,
    "Transport": 0.10,
    "Utilities & Bills": 0.10,
    "Entertainment & Eating Out": 0.10,
    "Shopping & Other": 0.10,
}

st.markdown("### ")
analyze = st.button("🚀 Analyze my situation", type="primary")

# ---------- TABS LAYOUT ----------
tab_overview, tab_expenses, tab_tax, tab_chat = st.tabs(
    ["📊 Overview", "🧾 Budget & Categories", "🇩🇪 Tax & Classes", "💬 Chat Assistant"]
)

# ========== TAB 1: OVERVIEW ==========
with tab_overview:
    st.markdown('<div class="main-card">', unsafe_allow_html=True)
    st.markdown('<div class="section-title">High level view</div>', unsafe_allow_html=True)
    st.markdown("#### ")

    if not analyze:
        st.info("Enter your details on the left and click **🚀 Analyze my situation** to start.")
    else:
        if gross_income <= 0:
            st.warning("Please enter a positive monthly gross income in the sidebar first.")
        else:
            c1, c2, c3, c4 = st.columns(4)
            with c1:
                st.markdown('<div class="metric-card">', unsafe_allow_html=True)
                st.metric("Gross income", f"{currency}{gross_income:,.0f}")
                st.markdown("</div>", unsafe_allow_html=True)

            with c2:
                st.markdown('<div class="metric-card">', unsafe_allow_html=True)
                st.metric(
                    f"Tax (Class {selected_tax_class})",
                    f"{currency}{estimated_tax_selected:,.0f}",
                )
                st.markdown("</div>", unsafe_allow_html=True)

            with c3:
                st.markdown('<div class="metric-card">', unsafe_allow_html=True)
                st.metric("Net income", f"{currency}{net_income:,.0f}")
                st.markdown("</div>", unsafe_allow_html=True)

            with c4:
                st.markdown('<div class="metric-card">', unsafe_allow_html=True)
                st.metric(
                    "Savings (approx.)",
                    f"{currency}{savings:,.0f}",
                    f"{savings_rate:.1f}%" if net_income > 0 else None,
                )
                st.markdown("</div>", unsafe_allow_html=True)

            st.markdown("### ")

            if net_income <= 0:
                st.error(
                    "Your estimated net income is **0 or negative**. "
                    "Check if the entered gross income is realistic."
                )
            if savings < 0:
                st.error(
                    f"You're spending **{currency}{abs(savings):,.0f} more** than your net income each month. "
                    "This is not sustainable — you need to cut costs or increase income."
                )
            elif savings == 0:
                st.warning(
                    "You’re breaking even: you save **0**. "
                    "Try to aim for at least 10–20% of your **net income** as savings."
                )
            else:
                st.success(
                    f"Nice! You are saving about **{currency}{savings:,.0f}** each month "
                    f"(**{savings_rate:.1f}%** of your net income)."
                )

            st.caption(
                "All tax values are simplified estimates. Real German tax depends on many "
                "more factors (health insurance, pension, church tax, etc.)."
            )

            st.markdown("---")
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

    st.markdown("</div>", unsafe_allow_html=True)

# ========== TAB 2: EXPENSES & BUDGET ==========
with tab_expenses:
    st.markdown('<div class="main-card">', unsafe_allow_html=True)
    st.markdown('<div class="section-title">Spending & categories</div>', unsafe_allow_html=True)
    st.markdown("### ")

    if not analyze:
        st.info("Run the analysis first to see your charts and tips.")
    else:
        df_expenses = pd.DataFrame(
            {"Category": list(expenses.keys()), "Amount": list(expenses.values())}
        ).set_index("Category")

        st.subheader("📉 Spending by category")
        if total_expenses > 0:
            st.bar_chart(df_expenses)
        else:
            st.info("You haven't entered any expenses yet. Add some amounts in the sidebar.")

        st.markdown("---")
        st.subheader("🧠 Budget guideline check (vs. net income)")

        if net_income == 0:
            st.info("Once your net income is positive, I can compare your expenses to guidelines.")
        else:
            overspending_tips = []
            guideline_rows = []

            for cat, amount in expenses.items():
                actual_pct = amount / net_income if net_income > 0 else 0
                rec_pct = recommended_pct.get(cat, 0.10)

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

            if savings < 0:
                st.write(
                    "- Overall you’re running a **deficit**. Start by targeting the biggest categories where you "
                    "spend more than the suggested percentage."
                )
            elif savings_rate < 10:
                st.write(
                    "- You are saving **less than 10%** of your net income. Try to reduce non-essential categories "
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
                    "\nTry lowering these categories a bit and re-running the analysis to see the effect."
                )
            else:
                st.write(
                    "Based on these rough guidelines, none of your categories look **massively** out of control. "
                    "You can still adjust them depending on your personal priorities."
                )

    st.markdown("</div>", unsafe_allow_html=True)

# ========== TAB 3: TAX & CLASSES ==========
with tab_tax:
    st.markdown('<div class="main-card">', unsafe_allow_html=True)
    st.markdown('<div class="section-title">German tax classes (simplified)</div>', unsafe_allow_html=True)
    st.markdown("### ")

    if not analyze:
        st.info("Run the analysis first to see your tax comparison.")
    else:
        st.subheader("🇩🇪 Estimated tax per Steuerklasse")

        tax_table_rows = []
        tax_for_chart = {}

        for cls in ["I", "II", "III", "IV", "V", "VI"]:
            cls_tax = apply_tax_class_modifier(base_tax, cls)
            cls_net = gross_income - cls_tax
            tax_table_rows.append({
                "Tax Class": cls,
                "Estimated Tax / Month": round(cls_tax, 2),
                "Net Income / Month": round(cls_net, 2),
            })
            tax_for_chart[cls] = cls_tax

        df_tax = pd.DataFrame(tax_table_rows).set_index("Tax Class")
        st.write("#### 💶 Monthly tax & net income (very rough estimate)")
        st.dataframe(df_tax.style.format({
            "Estimated Tax / Month": f"{currency}{{:,.2f}}",
            "Net Income / Month": f"{currency}{{:,.2f}}",
        }))

        st.write("#### 📊 Tax amount per class")
        df_tax_chart = pd.DataFrame({"Tax / Month": tax_for_chart})
        st.bar_chart(df_tax_chart)

        st.markdown("---")
        st.subheader("🧾 Tax optimization tips (very general)")

        st.caption(
            "These are general educational hints. Real tax choices must be checked with a Steuerberater "
            "or official tax calculator."
        )

        min_tax_class = min(tax_for_chart, key=tax_for_chart.get)

        if selected_tax_class == min_tax_class:
            st.write(
                f"- For your entered **gross income**, the lowest tax in this simplified model is in "
                f"**Steuerklasse {min_tax_class}**, which you have selected.\n"
                "  In real life, your possible tax class also depends on marital status and other criteria."
            )
        else:
            st.write(
                f"- In this **very simplified** model, **Steuerklasse {min_tax_class}** would result in the lowest "
                "monthly tax for the same gross income.\n"
                "  In reality, you may **not be allowed** to choose any tax class you want; it depends on your "
                "family situation (single, married, second job, etc.)."
            )

        if selected_tax_class in ["V", "VI"]:
            st.warning(
                "You selected **Steuerklasse V or VI**, which are often less favourable (higher withholding tax) "
                "in many real scenarios.\n\n"
                "Typical patterns in Germany:\n"
                "- Class III/V is used for married couples with very different incomes.\n"
                "- Class VI is used for a second job.\n\n"
                "If this doesn’t fit your situation in reality, a Steuerberater or official tool can help check "
                "whether another combination (e.g. IV/IV with factor) is better."
            )
        elif selected_tax_class in ["I", "II"]:
            st.info(
                "Classes I and II are typical for singles (II for single parents). If your life situation changes "
                "(marriage, second job), your tax class may change too."
            )
        elif selected_tax_class in ["III", "IV"]:
            st.info(
                "Classes III and IV are typical for married couples. In real life, the best choice depends on how "
                "different the two incomes are."
            )

        st.caption(
            "Demo idea: during your presentation, change the tax class and show how net income and savings change."
        )

    st.markdown("</div>", unsafe_allow_html=True)

# ========== TAB 4: CHAT ASSISTANT ==========
with tab_chat:
    st.markdown('<div class="main-card">', unsafe_allow_html=True)
    st.markdown('<div class="section-title">Conversational helper</div>', unsafe_allow_html=True)
    st.markdown("### ")

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

    def generate_bot_reply(user_message: str) -> str:
        ctx = {
            "gross_income": gross_income,
            "net_income": net_income,
            "base_tax": base_tax,
            "selected_tax_class": selected_tax_class,
            "estimated_tax_selected": estimated_tax_selected,
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
                f"(**{ctx['savings_rate']:.1f}%** of your net income)."
            )

        if "budget" in text or "overview" in text or "summary" in text:
            lines = [
                f"- Gross income: **{ctx['currency']}{ctx['gross_income']:,.0f}**",
                f"- Estimated tax (Class {ctx['selected_tax_class']}): "
                f"**{ctx['currency']}{ctx['estimated_tax_selected']:,.0f}**",
                f"- Net income: **{ctx['currency']}{ctx['net_income']:,.0f}**",
                f"- Total expenses: **{ctx['currency']}{ctx['total_expenses']:,.0f}**",
                f"- Savings: **{ctx['currency']}{ctx['savings']:,.0f}** "
                f"({ctx['savings_rate']:.1f}% of net income)",
                "",
                "By category:",
            ]
            for cat, amount in ctx["expenses"].items():
                if ctx["net_income"] > 0:
                    pct = amount / ctx["net_income"] * 100
                else:
                    pct = 0
                lines.append(
                    f"  - {cat}: **{ctx['currency']}{amount:,.0f}** ({pct:.1f}% of net income)"
                )
            return "\n".join(lines)

        if (
            "overspend" in text
            or "improve" in text
            or "reduce" in text
            or "cut" in text
        ):
            if ctx["net_income"] <= 0:
                return "I need a positive net income value to judge where you're overspending."

            overspending_tips = []
            for cat, amount in ctx["expenses"].items():
                actual_pct = amount / ctx["net_income"] if ctx["net_income"] > 0 else 0
                rec_pct = ctx["recommended_pct"].get(cat, 0.10)
                if actual_pct > rec_pct + 0.05:
                    overspending_tips.append(
                        f"- **{cat}**: you spend about **{actual_pct*100:.1f}%** of your net income, "
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

        if "tax" in text or "steuer" in text or "steuerklasse" in text:
            base_tax_local = calculate_german_income_tax(ctx["gross_income"])
            msg = (
                f"Here's a **very simplified** view of your tax situation:\n\n"
                f"- Gross income: **{ctx['currency']}{ctx['gross_income']:,.0f}** per month\n"
                f"- Base income tax (before tax class effect): "
                f"**{ctx['currency']}{base_tax_local:,.0f}** per month\n"
                f"- Selected tax class: **{ctx['selected_tax_class']}**\n"
                f"- Estimated tax with this class: "
                f"**{ctx['currency']}{ctx['estimated_tax_selected']:,.0f}** per month\n"
                f"- Estimated net income: **{ctx['currency']}{ctx['net_income']:,.0f}** per month\n\n"
                "Remember: Real German tax also includes social contributions, church tax, Solidaritätszuschlag, and more. "
                "Your actual tax can be quite different – this is just a teaching demo."
            )
            return msg

        return (
            "I’ve read your message, but I’m still a simple rules-based bot.\n\n"
            "You can ask me about:\n"
            "- Whether your savings goal is realistic\n"
            "- How much to save per month\n"
            "- A summary of your budget\n"
            "- Where you might be overspending\n"
            "- A rough explanation of your tax class and net income\n\n"
            "Also try changing your numbers in the sidebar and asking again."
        )

    # Display chat history
    for msg in st.session_state.messages:
        bubble_class = (
            "chat-bubble-assistant" if msg["role"] == "assistant" else "chat-bubble-user"
        )
        with st.chat_message(msg["role"]):
            st.markdown(
                f'<div class="{bubble_class}">{msg["content"]}</div>',
                unsafe_allow_html=True,
            )

    user_input = st.chat_input("Ask me something about your finances or taxes…")

    if user_input:
        st.session_state.messages.append({"role": "user", "content": user_input})
        reply = generate_bot_reply(user_input)
        st.session_state.messages.append({"role": "assistant", "content": reply})

        with st.chat_message("user"):
            st.markdown(
                f'<div class="chat-bubble-user">{user_input}</div>',
                unsafe_allow_html=True,
            )
        with st.chat_message("assistant"):
            st.markdown(
                f'<div class="chat-bubble-assistant">{reply}</div>',
                unsafe_allow_html=True,
            )

    st.markdown("</div>", unsafe_allow_html=True)
