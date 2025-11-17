# chat_assistant.py

"""
Chat assistant logic using:
- OpenAI (if API key is provided), OR
- A simple rule-based fallback.

This file stays clean and focused on chat functions only.
"""

from openai import OpenAI
from finance_logic import calculate_german_income_tax, RECOMMENDED_PCT

# ================================================================
#   🔑 DIRECT API KEY MODE — PASTE YOUR OPENAI API KEY BELOW
# ================================================================

OPENAI_API_KEY = ""

OPENAI_ENABLED = len(OPENAI_API_KEY) > 0
client = OpenAI(api_key=OPENAI_API_KEY) if OPENAI_ENABLED else None

# ================================================================
#   RULE-BASED FALLBACK ASSISTANT
# ================================================================

def generate_rule_based_reply(user_message: str, ctx: dict) -> str:
    """
    Simple fallback AI if no OpenAI key is provided.
    """
    text = user_message.lower()
    currency = ctx.get("currency", "€")

    # --- Savings goal ---
    if "goal" in text or ("save" in text and "month" in text):
        if ctx["goal_amount"] <= 0:
            return "Please add a savings goal amount in the sidebar and ask again."

        monthly_required = ctx["required_monthly_savings"]
        msg = (
            f"To reach **{currency}{ctx['goal_amount']:,.0f}** "
            f"in **{ctx['goal_months']} months**, you must save "
            f"**{currency}{monthly_required:,.0f} per month**.\n"
        )

        if ctx["savings"] < monthly_required:
            diff = monthly_required - ctx["savings"]
            msg += (
                f"Right now you save **{currency}{ctx['savings']:,.0f}**, "
                f"so you're short by **{currency}{diff:,.0f}** per month."
            )
        else:
            msg += "You are saving enough to reach the goal 🎉"
        return msg

    # --- Budget summary ---
    if "summary" in text or "budget" in text or "overview" in text:
        summary = [
            f"Gross income: {currency}{ctx['gross_income']:,.0f}",
            f"Net income: {currency}{ctx['net_income']:,.0f}",
            f"Tax (Class {ctx['selected_tax_class']}): {currency}{ctx['estimated_tax_selected']:,.0f}",
            f"Total expenses: {currency}{ctx['total_expenses']:,.0f}",
            f"Savings: {currency}{ctx['savings']:,.0f} ({ctx['savings_rate']:.1f}% of net income)",
        ]
        return "\n".join(summary)

    # --- Overspending analysis ---
    if "reduce" in text or "overspend" in text or "improve" in text:
        tips = []
        for cat, amount in ctx["expenses"].items():
            pct = amount / ctx["net_income"] if ctx["net_income"] > 0 else 0
            rec_pct = RECOMMENDED_PCT.get(cat, 0.10)
            if pct > rec_pct + 0.05:
                tips.append(
                    f"- {cat}: You spend {pct*100:.1f}% (recommended ~{rec_pct*100:.0f}%)."
                )

        if tips:
            return "Areas to improve:\n\n" + "\n".join(tips)
        else:
            return "Nothing looks drastically overspent, but you can still fine-tune."

    # --- Tax questions ---
    if "tax" in text or "steuer" in text or "class" in text:
        base_tax = calculate_german_income_tax(ctx["gross_income"])
        msg = (
            f"Here’s a rough tax breakdown:\n"
            f"- Gross: {currency}{ctx['gross_income']:,.0f}\n"
            f"- Base tax (no class): {currency}{base_tax:,.0f}\n"
            f"- Tax class {ctx['selected_tax_class']} estimate: "
            f"{currency}{ctx['estimated_tax_selected']:,.0f}\n"
            f"- Net income: {currency}{ctx['net_income']:,.0f}\n\n"
            "This is simplified for educational use."
        )
        return msg

    return (
        "I can help with:\n"
        "- Budget summary\n"
        "- Savings goal planning\n"
        "- Overspending analysis\n"
        "- German tax class questions\n"
        "Try asking: *Where am I overspending?*"
    )

# ================================================================
#   OPENAI-POWERED ASSISTANT
# ================================================================

def generate_openai_reply(user_message: str, ctx: dict, history: list) -> str:
    """
    Uses OpenAI to generate a financial answer using user context.
    """

    currency = ctx.get("currency", "€")

    # Build financial snapshot for the model
    snapshot = "\n".join([
        f"Currency: {currency}",
        f"Gross income: {ctx['gross_income']}",
        f"Net income: {ctx['net_income']}",
        f"Tax class: {ctx['selected_tax_class']}",
        f"Tax: {ctx['estimated_tax_selected']}",
        f"Expenses: {ctx['total_expenses']}",
        f"Savings: {ctx['savings']}",
        f"Savings rate: {ctx['savings_rate']}",
        f"Goal: {ctx['goal_amount']} in {ctx['goal_months']} months",
    ])

    messages = [
        {"role": "system", "content": (
            "You are a financial assistant for users living in Germany.\n"
            "Use the user's financial snapshot to answer questions.\n"
            "Provide clear, friendly explanations.\n"
            "Avoid legal or professional tax advice; stay educational."
        )},
        {"role": "system", "content": "User financial snapshot:\n" + snapshot},
    ]

    # Add last few chat messages to maintain conversation
    for msg in history[-5:]:
        messages.append({"role": msg["role"], "content": msg["content"]})

    messages.append({"role": "user", "content": user_message})

    try:
        response = client.chat.completions.create(
            model="gpt-4.1-mini",
            messages=messages,
            temperature=0.5,
        )
        return response.choices[0].message.content

    except Exception as e:
        return f"OpenAI error: {e}\nFalling back to offline assistant."

# ================================================================
#   SELECT BETWEEN OPENAI OR RULE-BASED
# ================================================================

def generate_bot_reply(user_message: str, ctx: dict, history: list) -> str:
    """
    Routes the query to OpenAI or to the rule-based fallback.
    """
    if OPENAI_ENABLED and client is not None:
        return generate_openai_reply(user_message, ctx, history)
    else:
        return generate_rule_based_reply(user_message, ctx)
