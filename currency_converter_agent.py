"""
Currency Converter Agent: Provides currency conversion tools for the finance assistant.

This module defines currency conversion functions that can be called by the AI assistant
to convert amounts between different currencies.
"""

import json
import requests
from typing import Optional
from datetime import datetime, timedelta

# Currency symbol to ISO code mapping
CURRENCY_CODES = {
    "€": "EUR",
    "$": "USD",
    "£": "GBP",
    "₹": "INR",
}

# Reverse mapping: ISO code to symbol
CURRENCY_SYMBOLS = {v: k for k, v in CURRENCY_CODES.items()}

# Fallback exchange rates (used if API fails)
# These are approximate rates - only used as fallback
FALLBACK_EXCHANGE_RATES = {
    "EUR": 1.0,      # Base currency
    "USD": 1.06,     # Fallback rate
    "GBP": 0.86,     # Fallback rate
    "INR": 88.5,     # Fallback rate
}

# Cache for exchange rates (to avoid too many API calls)
_rate_cache = {
    "rates": None,
    "timestamp": None,
    "cache_duration": timedelta(hours=1)  # Cache for 1 hour
}


def fetch_live_exchange_rates() -> Optional[dict]:
    """
    Fetch real-time exchange rates from exchangerate-api.com (free, no API key required).
    Returns rates relative to EUR as base currency.
    
    Returns:
        Dictionary with currency codes as keys and rates as values, or None if fetch fails
    """
    try:
        # exchangerate-api.com free endpoint (no API key needed)
        response = requests.get(
            "https://api.exchangerate-api.com/v4/latest/EUR",
            timeout=5  # 5 second timeout
        )
        response.raise_for_status()
        data = response.json()
        
        # Extract rates for supported currencies
        rates = {
            "EUR": 1.0,  # Base currency
            "USD": data["rates"].get("USD", FALLBACK_EXCHANGE_RATES["USD"]),
            "GBP": data["rates"].get("GBP", FALLBACK_EXCHANGE_RATES["GBP"]),
            "INR": data["rates"].get("INR", FALLBACK_EXCHANGE_RATES["INR"]),
        }
        
        return rates
    except Exception as e:
        # If API fails, return None to use fallback rates
        print(f"Warning: Failed to fetch live exchange rates: {e}")
        return None


def get_cached_or_fetch_rates() -> dict:
    """
    Get exchange rates from cache if available and fresh, otherwise fetch from API.
    
    Returns:
        Dictionary of exchange rates
    """
    global _rate_cache
    
    now = datetime.now()
    
    # Check if cache is valid
    if (_rate_cache["rates"] is not None and 
        _rate_cache["timestamp"] is not None and
        now - _rate_cache["timestamp"] < _rate_cache["cache_duration"]):
        return _rate_cache["rates"]
    
    # Fetch new rates
    live_rates = fetch_live_exchange_rates()
    
    if live_rates:
        # Update cache with live rates
        _rate_cache["rates"] = live_rates
        _rate_cache["timestamp"] = now
        return live_rates
    else:
        # Use fallback rates if API fails
        print("Using fallback exchange rates (API unavailable)")
        return FALLBACK_EXCHANGE_RATES


def get_exchange_rate(from_currency: str, to_currency: str) -> Optional[float]:
    """
    Get real-time exchange rate from one currency to another.
    Fetches live rates from API (cached for 1 hour) or uses fallback if API fails.
    
    Args:
        from_currency: Source currency (ISO code or symbol)
        to_currency: Target currency (ISO code or symbol)
        
    Returns:
        Exchange rate (how many units of to_currency per 1 unit of from_currency)
        Returns None if currencies are invalid
    """
    # Get current exchange rates (from API or cache)
    exchange_rates = get_cached_or_fetch_rates()
    
    # Convert symbols to ISO codes if needed
    from_code = CURRENCY_CODES.get(from_currency, from_currency.upper())
    to_code = CURRENCY_CODES.get(to_currency, to_currency.upper())
    
    # Validate currencies
    if from_code not in exchange_rates or to_code not in exchange_rates:
        return None
    
    # If same currency, rate is 1
    if from_code == to_code:
        return 1.0
    
    # Convert via EUR (base currency)
    # Rate = (1 EUR / from_currency) * (to_currency / 1 EUR)
    from_rate = exchange_rates[from_code]
    to_rate = exchange_rates[to_code]
    
    # Convert from_currency -> EUR -> to_currency
    # If from_currency is EUR, from_rate = 1.0, so: 1 * to_rate = to_rate
    # If from_currency is USD, from_rate = 1.08, so: (1/1.08) * to_rate
    eur_equivalent = 1.0 / from_rate  # How many EUR per 1 unit of from_currency
    result = eur_equivalent * to_rate  # Convert EUR to to_currency
    
    return result


def convert_currency(amount: float, from_currency: str, to_currency: str) -> dict:
    """
    Convert an amount from one currency to another.
    
    Args:
        amount: Amount to convert
        from_currency: Source currency (ISO code or symbol)
        to_currency: Target currency (ISO code or symbol)
        
    Returns:
        Dictionary with converted amount, rate, and explanation
    """
    rate = get_exchange_rate(from_currency, to_currency)
    
    if rate is None:
        return {
            "success": False,
            "error": f"Invalid currency conversion: {from_currency} to {to_currency}",
            "result": None,
            "explanation": f"Could not convert {from_currency} to {to_currency}. Supported currencies: EUR, USD, GBP, INR",
        }
    
    converted_amount = amount * rate
    
    # Get symbols for display
    from_symbol = CURRENCY_SYMBOLS.get(
        CURRENCY_CODES.get(from_currency, from_currency.upper()),
        from_currency
    )
    to_symbol = CURRENCY_SYMBOLS.get(
        CURRENCY_CODES.get(to_currency, to_currency.upper()),
        to_currency
    )
    
    explanation = (
        f"Conversion: {from_symbol}{amount:,.2f} → {to_symbol}{converted_amount:,.2f}\n"
        f"Exchange rate: 1 {from_currency} = {rate:.4f} {to_currency}\n"
        f"Calculation: {amount:,.2f} × {rate:.4f} = {converted_amount:,.2f}"
    )
    
    return {
        "success": True,
        "result": converted_amount,
        "rate": rate,
        "from_currency": from_currency,
        "to_currency": to_currency,
        "explanation": explanation,
    }


# Currency converter tools for OpenAI function calling
CURRENCY_CONVERTER_TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "convert_currency_amount",
            "description": "Convert an amount from one currency to another. Supports EUR (€), USD ($), GBP (£), and INR (₹). Use this when users ask to convert amounts, income, expenses, or savings between currencies.",
            "parameters": {
                "type": "object",
                "properties": {
                    "amount": {
                        "type": "number",
                        "description": "The amount to convert",
                    },
                    "from_currency": {
                        "type": "string",
                        "description": "Source currency. Can be ISO code (EUR, USD, GBP, INR) or symbol (€, $, £, ₹)",
                        "enum": ["EUR", "USD", "GBP", "INR", "€", "$", "£", "₹"],
                    },
                    "to_currency": {
                        "type": "string",
                        "description": "Target currency. Can be ISO code (EUR, USD, GBP, INR) or symbol (€, $, £, ₹)",
                        "enum": ["EUR", "USD", "GBP", "INR", "€", "$", "£", "₹"],
                    },
                },
                "required": ["amount", "from_currency", "to_currency"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_exchange_rate_info",
            "description": "Get the current exchange rate between two currencies. Use this when users ask about exchange rates or want to know the conversion rate.",
            "parameters": {
                "type": "object",
                "properties": {
                    "from_currency": {
                        "type": "string",
                        "description": "Source currency. Can be ISO code (EUR, USD, GBP, INR) or symbol (€, $, £, ₹)",
                        "enum": ["EUR", "USD", "GBP", "INR", "€", "$", "£", "₹"],
                    },
                    "to_currency": {
                        "type": "string",
                        "description": "Target currency. Can be ISO code (EUR, USD, GBP, INR) or symbol (€, $, £, ₹)",
                        "enum": ["EUR", "USD", "GBP", "INR", "€", "$", "£", "₹"],
                    },
                },
                "required": ["from_currency", "to_currency"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "convert_financial_summary",
            "description": "Convert a user's entire financial summary (income, expenses, savings) from one currency to another. Use this when users want to see their finances in a different currency.",
            "parameters": {
                "type": "object",
                "properties": {
                    "gross_income": {
                        "type": "number",
                        "description": "Monthly gross income",
                    },
                    "net_income": {
                        "type": "number",
                        "description": "Monthly net income",
                    },
                    "total_expenses": {
                        "type": "number",
                        "description": "Total monthly expenses",
                    },
                    "savings": {
                        "type": "number",
                        "description": "Monthly savings",
                    },
                    "from_currency": {
                        "type": "string",
                        "description": "Current currency of the amounts",
                        "enum": ["EUR", "USD", "GBP", "INR", "€", "$", "£", "₹"],
                    },
                    "to_currency": {
                        "type": "string",
                        "description": "Target currency to convert to",
                        "enum": ["EUR", "USD", "GBP", "INR", "€", "$", "£", "₹"],
                    },
                },
                "required": ["gross_income", "net_income", "total_expenses", "savings", "from_currency", "to_currency"],
            },
        },
    },
]


def execute_currency_function(function_name: str, arguments: dict) -> dict:
    """
    Execute a currency converter function and return the result.
    
    Args:
        function_name: Name of the function to execute
        arguments: Dictionary of arguments for the function
        
    Returns:
        Dictionary with result and explanation
    """
    if function_name == "convert_currency_amount":
        amount = arguments.get("amount", 0)
        from_curr = arguments.get("from_currency", "EUR")
        to_curr = arguments.get("to_currency", "EUR")
        
        result = convert_currency(amount, from_curr, to_curr)
        return result
    
    elif function_name == "get_exchange_rate_info":
        from_curr = arguments.get("from_currency", "EUR")
        to_curr = arguments.get("to_currency", "EUR")
        
        rate = get_exchange_rate(from_curr, to_curr)
        
        if rate is None:
            return {
                "success": False,
                "error": f"Invalid currencies: {from_curr} to {to_curr}",
                "result": None,
                "explanation": f"Could not get exchange rate. Supported currencies: EUR, USD, GBP, INR",
            }
        
        from_symbol = CURRENCY_SYMBOLS.get(
            CURRENCY_CODES.get(from_curr, from_curr.upper()),
            from_curr
        )
        to_symbol = CURRENCY_SYMBOLS.get(
            CURRENCY_CODES.get(to_curr, to_curr.upper()),
            to_curr
        )
        
        explanation = (
            f"Exchange rate: 1 {from_symbol} ({from_curr}) = {rate:.4f} {to_symbol} ({to_curr})\n"
            f"Reverse rate: 1 {to_symbol} ({to_curr}) = {1/rate:.4f} {from_symbol} ({from_curr})"
        )
        
        return {
            "success": True,
            "result": rate,
            "explanation": explanation,
        }
    
    elif function_name == "convert_financial_summary":
        gross = arguments.get("gross_income", 0)
        net = arguments.get("net_income", 0)
        expenses = arguments.get("total_expenses", 0)
        savings = arguments.get("savings", 0)
        from_curr = arguments.get("from_currency", "EUR")
        to_curr = arguments.get("to_currency", "EUR")
        
        rate = get_exchange_rate(from_curr, to_curr)
        
        if rate is None:
            return {
                "success": False,
                "error": f"Invalid currency conversion: {from_curr} to {to_curr}",
                "result": None,
                "explanation": f"Could not convert. Supported currencies: EUR, USD, GBP, INR",
            }
        
        converted = {
            "gross_income": gross * rate,
            "net_income": net * rate,
            "total_expenses": expenses * rate,
            "savings": savings * rate,
        }
        
        from_symbol = CURRENCY_SYMBOLS.get(
            CURRENCY_CODES.get(from_curr, from_curr.upper()),
            from_curr
        )
        to_symbol = CURRENCY_SYMBOLS.get(
            CURRENCY_CODES.get(to_curr, to_curr.upper()),
            to_curr
        )
        
        explanation = (
            f"Financial Summary Conversion ({from_symbol} → {to_symbol}):\n"
            f"Exchange rate: 1 {from_symbol} = {rate:.4f} {to_symbol}\n\n"
            f"Gross Income: {from_symbol}{gross:,.2f} → {to_symbol}{converted['gross_income']:,.2f}\n"
            f"Net Income: {from_symbol}{net:,.2f} → {to_symbol}{converted['net_income']:,.2f}\n"
            f"Total Expenses: {from_symbol}{expenses:,.2f} → {to_symbol}{converted['total_expenses']:,.2f}\n"
            f"Savings: {from_symbol}{savings:,.2f} → {to_symbol}{converted['savings']:,.2f}"
        )
        
        return {
            "success": True,
            "result": converted,
            "rate": rate,
            "explanation": explanation,
        }
    
    else:
        return {
            "success": False,
            "error": f"Unknown function: {function_name}",
            "result": None,
            "explanation": f"Function {function_name} is not recognized.",
        }
