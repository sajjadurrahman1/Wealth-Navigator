# finance_logic.py

"""
Core financial and tax logic for the German personal finance assistant.
All numbers are simplified and for educational purposes only.
"""

# Recommended guideline percentages (rule-of-thumb)
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
    Simplified German income tax estimation.
    Converts monthly → yearly → applies progressive tax → back to monthly.

    ⚠️ Educational approximation only – real German tax law is more complex.
    """
    annual_income = monthly_income * 12

    if annual_income <= 11604:
        tax_year = 0
    elif annual_income <= 66760:
        # Very rough linear-progressive approximation between 11,605 and 66,760
        tax_year = (annual_income - 11604) * 0.20  # ~20% average
    elif annual_income <= 277825:
        # 20% on the first band, then 42% on the rest
        tax_year = (55156 * 0.20) + (annual_income - 66760) * 0.42
    else:
        # 20% on first band, 42% up to 277,825, then 45% above
        tax_year = (
            (55156 * 0.20)
            + (211065 * 0.42)
            + (annual_income - 277825) * 0.45
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


def compute_financials(
    gross_income: float,
    selected_tax_class: str,
    expenses: dict,
    goal_amount: float,
    goal_months: int,
):
    """
    Given inputs, compute all core financial values and return a context dict.
    """
    base_tax = calculate_german_income_tax(gross_income)
    estimated_tax_selected = apply_tax_class_modifier(base_tax, selected_tax_class)
    net_income = gross_income - estimated_tax_selected

    total_expenses = sum(expenses.values())
    savings = net_income - total_expenses
    savings_rate = (savings / net_income * 100) if net_income > 0 else 0

    required_monthly_savings = (
        goal_amount / goal_months if goal_amount > 0 and goal_months > 0 else 0
    )

    # Tax per class for comparison
    tax_per_class = {}
    for cls in ["I", "II", "III", "IV", "V", "VI"]:
        cls_tax = apply_tax_class_modifier(base_tax, cls)
        tax_per_class[cls] = cls_tax

    ctx = {
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

    return ctx
