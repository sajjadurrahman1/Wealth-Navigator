# finance_logic.py
# Core calculations for the app (simple estimates, not real tax advice)

# Rule-of-thumb guideline percentages for budgeting
RECOMMENDED_PCT = {
    "Rent / Housing": 0.30,
    "Food & Groceries": 0.15,
    "Transport": 0.10,
    "Utilities & Bills": 0.10,
    "Entertainment & Eating Out": 0.10,
    "Shopping & Other": 0.10,
}


def calculate_german_income_tax(monthly_income: float) -> float:
    """
    Rough German income tax estimate:
    - Convert monthly income to annual income
    - Apply a simplified progressive model
    - Convert back to a monthly tax number

    This is intentionally simplified for demo/education.
    """
    annual_income = monthly_income * 12

    # Basic allowance (very rough)
    if annual_income <= 11604:
        tax_year = 0

    # Simplified progressive band
    elif annual_income <= 66760:
        tax_year = (annual_income - 11604) * 0.20

    # Higher band: treat the first band at ~20%, then the rest at 42%
    elif annual_income <= 277825:
        tax_year = (55156 * 0.20) + (annual_income - 66760) * 0.42

    # Very high income: add an extra top rate above the last threshold
    else:
        tax_year = (
            (55156 * 0.20)
            + (211065 * 0.42)
            + (annual_income - 277825) * 0.45
        )

    # Return monthly tax estimate
    return tax_year / 12


def apply_tax_class_modifier(base_tax: float, tax_class: str) -> float:
    """
    Quick adjustment for German tax class.
    This is a *toy model* — real Steuerklasse impact depends on personal situation.
    """
    modifiers = {
        "I": 1.00,    # single
        "II": 0.90,   # single parent
        "III": 0.80,  # married, higher earner
        "IV": 1.00,   # married, similar earners
        "V": 1.20,    # married, lower earner
        "VI": 1.30,   # second job
    }

    # Default back to class I behavior if an unknown value is passed
    return base_tax * modifiers.get(tax_class, 1.00)


def compute_financials(
    gross_income: float,
    selected_tax_class: str,
    expenses: dict,
    goal_amount: float,
    goal_months: int,
):
    """
    Compute the key values the UI and chatbot need:
    tax estimate, net income, savings, goal math, and per-tax-class comparison.
    """
    # Tax + net income estimate
    base_tax = calculate_german_income_tax(gross_income)
    estimated_tax_selected = apply_tax_class_modifier(base_tax, selected_tax_class)
    net_income = gross_income - estimated_tax_selected

    # Expense totals + savings
    total_expenses = sum(expenses.values())
    savings = net_income - total_expenses
    savings_rate = (savings / net_income * 100) if net_income > 0 else 0

    # How much the user needs to save per month to hit their goal
    required_monthly_savings = (
        goal_amount / goal_months if goal_amount > 0 and goal_months > 0 else 0
    )

    # Helpful comparison: estimated tax if they were in other tax classes
    tax_per_class = {}
    for cls in ["I", "II", "III", "IV", "V", "VI"]:
        tax_per_class[cls] = apply_tax_class_modifier(base_tax, cls)

    # Pack everything into one dict so Streamlit + chat can reuse it easily
    return {
        "gross_income": gross_income,
        "selected_tax_class": selected_tax_class,
        "base_tax": base_tax,
        "estimated_tax_selected": estimated_tax_selected,
        "net_income": net_income,
        "expenses": expenses,
        "total_expenses": total_expenses,
        "savings": savings,
        "savings_rate": savings_rate,
        "goal_amount": goal_amount,
        "goal_months": goal_months,
        "required_monthly_savings": required_monthly_savings,
        "tax_per_class": tax_per_class,
        "recommended_pct": RECOMMENDED_PCT,
    }
