"""
Chat assistant logic:
- Uses OpenAI if an API key is provided
- Otherwise falls back to a simple rule-based assistant

Keep this file focused on chat behavior (no Streamlit UI here).
"""

from openai import OpenAI
from finance_logic import calculate_german_income_tax, RECOMMENDED_PCT


# Put your OpenAI API key here if you want AI replies
OPENAI_API_KEY = ""

# If the key is empty, we run in offline/fallback mode
OPENAI_ENABLED = len(OPENAI_API_KEY) > 0
client = OpenAI(api_key=OPENAI_API_KEY) if OPENAI_ENABLED else None


def generate_rule_based_reply(user_message: str, ctx: dict) -> str:
    """Simple offline assistant for common finance questions."""
    text = user_message.lower()
    currency = ctx.get("currency", "€")

    # Savings goal questions
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

    # Budget summary / overview
    if "summary" in text or "budget" in text or "overview" in text:
        summary = [
            f"Gross income: {currency}{ctx['gross_income']:,.0f}",
            f"Net income: {currency}{ctx['net_income']:,.0f}",
            f"Tax (Class {ctx['selected_tax_class']}): {currency}{ctx['estimated_tax_selected']:,.0f}",
            f"Total expenses: {currency}{ctx['total_expenses']:,.0f}",
            f"Savings: {currency}{ctx['savings']:,.0f} ({ctx['savings_rate']:.1f}% of net income)",
        ]
        return "\n".join(summary)

    # Overspending / improvement tips
    if "reduce" in text or "overspend" in text or "improve" in text:
        tips = []
        for cat, amount in ctx["expenses"].items():
            pct = amount / ctx["net_income"] if ctx["net_income"] > 0 else 0
            rec_pct = RECOMMENDED_PCT.get(cat, 0.10)

            # Add a tip only if they are clearly above the guideline
            if pct > rec_pct + 0.05:
                tips.append(
                    f"- {cat}: You spend {pct*100:.1f}% (recommended ~{rec_pct*100:.0f}%)."
                )

        if tips:
            return "Areas to improve:\n\n" + "\n".join(tips)
        return "Nothing looks drastically overspent, but you can still fine-tune."

    # Tax / Steuerklasse questions
    if "tax" in text or "steuer" in text or "class" in text:
        base_tax = calculate_german_income_tax(ctx["gross_income"])
        return (
            "Here’s a rough tax breakdown:\n"
            f"- Gross: {currency}{ctx['gross_income']:,.0f}\n"
            f"- Base tax (no class): {currency}{base_tax:,.0f}\n"
            f"- Tax class {ctx['selected_tax_class']} estimate: {currency}{ctx['estimated_tax_selected']:,.0f}\n"
            f"- Net income: {currency}{ctx['net_income']:,.0f}\n\n"
            "This is simplified for educational use."
        )

    # Default help message when nothing matched
    return (
        "I can help with:\n"
        "- Budget summary\n"
        "- Savings goal planning\n"
        "- Overspending analysis\n"
        "- German tax class questions\n"
        "Try asking: *Where am I overspending?*"
    )


def generate_openai_reply(user_message: str, ctx: dict, history: list) -> str:
    """
    Uses OpenAI to generate a reply using the user's financial context.

    By default we keep answers short and practical.
    If the user asks for steps / formulas, we switch to a detailed explanation.
    """
    currency = ctx.get("currency", "€")
    text = user_message.lower()

    # Check if the user wants the math and steps
    wants_detail = any(
        kw in text
        for kw in [
            "show the calculation",
            "show calculation",
            "how did you calculate",
            "how did you get this",
            "how did you get that",
            "step by step",
            "explain the calculation",
            "explain in detail",
            "formula",
        ]
    )

    # A short "snapshot" of the current financial situation for the model
    snapshot = "\n".join(
        [
            f"Currency: {currency}",
            f"Gross income: {ctx['gross_income']}",
            f"Net income: {ctx['net_income']}",
            f"Tax class: {ctx['selected_tax_class']}",
            f"Tax: {ctx['estimated_tax_selected']}",
            f"Expenses total: {ctx['total_expenses']}",
            f"Savings: {ctx['savings']}",
            f"Savings rate (% of net): {ctx['savings_rate']}",
            f"Goal amount: {ctx['goal_amount']}",
            f"Goal months: {ctx['goal_months']}",
        ]
    )

    # Tell the model how to respond (short by default, detailed when requested)
    if wants_detail:
        style_instructions = (
            "User wants to see the calculation.\n"
            "Show formulas and intermediate steps, then the final result.\n"
            "Be structured and accurate."
        )
    else:
        style_instructions = (
            "Answer in a compact, practical way (2–4 short sentences).\n"
            "No formulas or step-by-step math unless the user asked for it.\n"
            "Give 1–3 concrete suggestions."
        )

    messages = [
        {
            "role": "system",
            "content": (
                "You are a personal finance assistant for users living in Germany. "
                "Use the snapshot and the user's question to answer in a helpful way."
            ),
        },
        {"role": "system", "content": "User financial snapshot:\n" + snapshot},
        {"role": "system", "content": style_instructions},
    ]

    # Keep a little bit of chat history so the assistant stays consistent
    for msg in history[-5:]:
        messages.append({"role": msg["role"], "content": msg["content"]})

    # If they want details, nudge the model once more in the user message
    if wants_detail:
        user_content = (
            user_message
            + "\n\nPlease show the formula and each step you use."
        )
    else:
        user_content = user_message

    messages.append({"role": "user", "content": user_content})

    try:
        response = client.chat.completions.create(
            model="gpt-4.1-mini",
            messages=messages,
            temperature=0.2,
        )
        return response.choices[0].message.content

    except Exception as e:
        # If OpenAI fails, return an error message so the user knows what happened
        return f"OpenAI error: {e}\nFalling back to offline assistant."


def generate_bot_reply(user_message: str, ctx: dict, history: list) -> str:
    """Pick OpenAI when available, otherwise use the offline assistant."""
    if OPENAI_ENABLED and client is not None:
        return generate_openai_reply(user_message, ctx, history)
    return generate_rule_based_reply(user_message, ctx)
