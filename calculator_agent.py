"""
Calculator Agent: Provides calculation tools for the finance assistant.

This module defines calculator functions that can be called by the AI assistant
to perform accurate financial calculations.
"""

from finance_logic import (
    calculate_german_income_tax,
    apply_tax_class_modifier,
    RECOMMENDED_PCT,
)


# Calculator tool definitions for OpenAI function calling
CALCULATOR_TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "calculate_savings_rate",
            "description": "Calculate the savings rate as a percentage of net income. Formula: (Savings / Net Income) * 100",
            "parameters": {
                "type": "object",
                "properties": {
                    "savings": {
                        "type": "number",
                        "description": "Monthly savings amount (net income - expenses)",
                    },
                    "net_income": {
                        "type": "number",
                        "description": "Monthly net income after taxes",
                    },
                },
                "required": ["savings", "net_income"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "calculate_required_monthly_savings",
            "description": "Calculate how much needs to be saved per month to reach a savings goal. Formula: Goal Amount / Goal Months",
            "parameters": {
                "type": "object",
                "properties": {
                    "goal_amount": {
                        "type": "number",
                        "description": "Total savings goal amount",
                    },
                    "goal_months": {
                        "type": "number",
                        "description": "Number of months to reach the goal",
                    },
                },
                "required": ["goal_amount", "goal_months"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "calculate_net_income",
            "description": "Calculate net income after taxes. Formula: Gross Income - Tax",
            "parameters": {
                "type": "object",
                "properties": {
                    "gross_income": {
                        "type": "number",
                        "description": "Monthly gross income before taxes",
                    },
                    "tax_amount": {
                        "type": "number",
                        "description": "Monthly tax amount",
                    },
                },
                "required": ["gross_income", "tax_amount"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "calculate_tax_estimate",
            "description": "Calculate German income tax estimate for a given gross income and tax class",
            "parameters": {
                "type": "object",
                "properties": {
                    "gross_income": {
                        "type": "number",
                        "description": "Monthly gross income before taxes",
                    },
                    "tax_class": {
                        "type": "string",
                        "description": "German tax class (Steuerklasse): I, II, III, IV, V, or VI",
                        "enum": ["I", "II", "III", "IV", "V", "VI"],
                    },
                },
                "required": ["gross_income", "tax_class"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "calculate_savings",
            "description": "Calculate monthly savings. Formula: Net Income - Total Expenses",
            "parameters": {
                "type": "object",
                "properties": {
                    "net_income": {
                        "type": "number",
                        "description": "Monthly net income after taxes",
                    },
                    "total_expenses": {
                        "type": "number",
                        "description": "Total monthly expenses",
                    },
                },
                "required": ["net_income", "total_expenses"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "calculate_expense_percentage",
            "description": "Calculate what percentage of net income a specific expense category represents. Formula: (Expense Amount / Net Income) * 100",
            "parameters": {
                "type": "object",
                "properties": {
                    "expense_amount": {
                        "type": "number",
                        "description": "Amount spent in a specific category",
                    },
                    "net_income": {
                        "type": "number",
                        "description": "Monthly net income after taxes",
                    },
                },
                "required": ["expense_amount", "net_income"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "calculate_goal_shortfall",
            "description": "Calculate how much more needs to be saved per month to reach a goal. Formula: Required Monthly Savings - Current Monthly Savings",
            "parameters": {
                "type": "object",
                "properties": {
                    "required_monthly_savings": {
                        "type": "number",
                        "description": "Required monthly savings to reach goal",
                    },
                    "current_monthly_savings": {
                        "type": "number",
                        "description": "Current monthly savings amount",
                    },
                },
                "required": ["required_monthly_savings", "current_monthly_savings"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "calculate_time_to_goal",
            "description": "Calculate how many months it will take to reach a savings goal at current savings rate. Formula: Goal Amount / Current Monthly Savings",
            "parameters": {
                "type": "object",
                "properties": {
                    "goal_amount": {
                        "type": "number",
                        "description": "Total savings goal amount",
                    },
                    "current_monthly_savings": {
                        "type": "number",
                        "description": "Current monthly savings amount",
                    },
                },
                "required": ["goal_amount", "current_monthly_savings"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "perform_arithmetic",
            "description": "Perform basic arithmetic operations: addition, subtraction, multiplication, division. Use this for any mathematical calculations needed.",
            "parameters": {
                "type": "object",
                "properties": {
                    "operation": {
                        "type": "string",
                        "description": "The arithmetic operation to perform",
                        "enum": ["add", "subtract", "multiply", "divide"],
                    },
                    "a": {
                        "type": "number",
                        "description": "First number",
                    },
                    "b": {
                        "type": "number",
                        "description": "Second number",
                    },
                },
                "required": ["operation", "a", "b"],
            },
        },
    },
]


def execute_calculator_function(function_name: str, arguments: dict) -> dict:
    """
    Execute a calculator function and return the result with step-by-step explanation.
    
    Args:
        function_name: Name of the function to execute
        arguments: Dictionary of arguments for the function
        
    Returns:
        Dictionary with 'result' (the calculated value) and 'explanation' (step-by-step)
    """
    result = None
    explanation = ""
    
    if function_name == "calculate_savings_rate":
        savings = arguments["savings"]
        net_income = arguments["net_income"]
        if net_income == 0:
            result = 0
            explanation = "Savings rate = (Savings / Net Income) × 100 = (0 / 0) × 100 = 0% (net income is zero)"
        else:
            result = (savings / net_income) * 100
            explanation = (
                f"Savings rate = (Savings / Net Income) × 100\n"
                f"= ({savings:,.2f} / {net_income:,.2f}) × 100\n"
                f"= {result:.2f}%"
            )
    
    elif function_name == "calculate_required_monthly_savings":
        goal_amount = arguments["goal_amount"]
        goal_months = arguments["goal_months"]
        if goal_months == 0:
            result = 0
            explanation = "Required monthly savings = Goal Amount / Goal Months = Cannot divide by zero"
        else:
            result = goal_amount / goal_months
            explanation = (
                f"Required monthly savings = Goal Amount / Goal Months\n"
                f"= {goal_amount:,.2f} / {goal_months}\n"
                f"= {result:,.2f} per month"
            )
    
    elif function_name == "calculate_net_income":
        gross_income = arguments["gross_income"]
        tax_amount = arguments["tax_amount"]
        result = gross_income - tax_amount
        explanation = (
            f"Net Income = Gross Income - Tax\n"
            f"= {gross_income:,.2f} - {tax_amount:,.2f}\n"
            f"= {result:,.2f}"
        )
    
    elif function_name == "calculate_tax_estimate":
        gross_income = arguments["gross_income"]
        tax_class = arguments["tax_class"]
        base_tax = calculate_german_income_tax(gross_income)
        result = apply_tax_class_modifier(base_tax, tax_class)
        explanation = (
            f"Tax calculation for Class {tax_class}:\n"
            f"1. Base tax (monthly): {base_tax:,.2f}\n"
            f"2. Apply tax class {tax_class} modifier\n"
            f"3. Estimated tax = {result:,.2f}"
        )
    
    elif function_name == "calculate_savings":
        net_income = arguments["net_income"]
        total_expenses = arguments["total_expenses"]
        result = net_income - total_expenses
        explanation = (
            f"Monthly Savings = Net Income - Total Expenses\n"
            f"= {net_income:,.2f} - {total_expenses:,.2f}\n"
            f"= {result:,.2f}"
        )
    
    elif function_name == "calculate_expense_percentage":
        expense_amount = arguments["expense_amount"]
        net_income = arguments["net_income"]
        if net_income == 0:
            result = 0
            explanation = "Expense percentage = (Expense / Net Income) × 100 = Cannot calculate (net income is zero)"
        else:
            result = (expense_amount / net_income) * 100
            explanation = (
                f"Expense % = (Expense Amount / Net Income) × 100\n"
                f"= ({expense_amount:,.2f} / {net_income:,.2f}) × 100\n"
                f"= {result:.2f}%"
            )
    
    elif function_name == "calculate_goal_shortfall":
        required = arguments["required_monthly_savings"]
        current = arguments["current_monthly_savings"]
        result = required - current
        explanation = (
            f"Shortfall = Required Monthly Savings - Current Monthly Savings\n"
            f"= {required:,.2f} - {current:,.2f}\n"
            f"= {result:,.2f}"
        )
        if result < 0:
            explanation += f"\n(You are saving {abs(result):,.2f} more than required!)"
    
    elif function_name == "calculate_time_to_goal":
        goal_amount = arguments["goal_amount"]
        current_savings = arguments["current_monthly_savings"]
        if current_savings == 0:
            result = float('inf')
            explanation = "Time to goal = Goal Amount / Current Monthly Savings = Cannot calculate (current savings is zero)"
        else:
            result = goal_amount / current_savings
            explanation = (
                f"Time to goal = Goal Amount / Current Monthly Savings\n"
                f"= {goal_amount:,.2f} / {current_savings:,.2f}\n"
                f"= {result:.2f} months"
            )
    
    elif function_name == "perform_arithmetic":
        operation = arguments["operation"]
        a = arguments["a"]
        b = arguments["b"]
        
        if operation == "add":
            result = a + b
            explanation = f"{a} + {b} = {result}"
        elif operation == "subtract":
            result = a - b
            explanation = f"{a} - {b} = {result}"
        elif operation == "multiply":
            result = a * b
            explanation = f"{a} × {b} = {result}"
        elif operation == "divide":
            if b == 0:
                result = None
                explanation = f"{a} ÷ {b} = Cannot divide by zero"
            else:
                result = a / b
                explanation = f"{a} ÷ {b} = {result}"
        else:
            result = None
            explanation = f"Unknown operation: {operation}"
    
    else:
        result = None
        explanation = f"Unknown function: {function_name}"
    
    return {
        "result": result,
        "explanation": explanation,
        "function_name": function_name,
    }
