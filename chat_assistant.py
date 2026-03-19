"""
Chat assistant logic:
- Uses OpenAI if an API key is provided
- Otherwise falls back to a simple rule-based assistant
- Optionally uses a FAISS-based knowledge base (RAG) built from PDF books

Keep this file focused on chat behavior (no Streamlit UI here).
"""

import os
from typing import List, Dict, Any

# Try to load .env file if python-dotenv is available
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass  # python-dotenv not installed, skip

from finance_logic import calculate_german_income_tax, RECOMMENDED_PCT

# Import agent tools
try:
    from calculator_agent import CALCULATOR_TOOLS, execute_calculator_function
except ImportError:
    CALCULATOR_TOOLS = []
    def execute_calculator_function(function_name, arguments):
        return {"result": None, "explanation": "Calculator agent not available."}

try:
    from currency_converter_agent import CURRENCY_CONVERTER_TOOLS, execute_currency_function
except ImportError:
    CURRENCY_CONVERTER_TOOLS = []
    def execute_currency_function(function_name, arguments):
        return {"result": None, "explanation": "Currency converter agent not available."}

# ---------- Optional RAG (FAISS) retrieval ----------
try:
    from rag.rag_query import RAGStore  # expects rag/rag_query.py
    rag_store = RAGStore()
except FileNotFoundError as e:
    # Index not built yet - this is expected if user hasn't run ingestion
    rag_store = None
except Exception as e:
    # Other errors - log but don't crash
    print(f"Warning: RAG system unavailable: {e}")
    rag_store = None


def retrieve_context(query: str, top_k: int = 5) -> str:
    """
    Retrieve top-k relevant chunks from the FAISS knowledge base.
    Returns a single formatted string with citations like [Book.pdf p.12].
    """
    if rag_store is None:
        return ""

    try:
        results = rag_store.search(query, top_k=top_k)
    except Exception:
        return ""

    if not results:
        return ""

    return "\n\n".join(
        [f"[{r['source']} p.{r['page']}] {r['text']}" for r in results]
    )


def retrieve_context_with_sources(query: str, top_k: int = 5) -> tuple:
    """
    Retrieve context and return both formatted text and source list.
    Returns: (formatted_text, list_of_sources)
    """
    if rag_store is None:
        return "", []

    try:
        results = rag_store.search(query, top_k=top_k)
    except Exception:
        return "", []

    if not results:
        return "", []

    formatted = "\n\n".join(
        [f"[{r['source']} p.{r['page']}] {r['text']}" for r in results]
    )
    
    # Extract unique sources with page numbers
    sources = []
    seen = set()
    for r in results:
        source_key = (r['source'], r['page'])
        if source_key not in seen:
            sources.append({
                'source': r['source'],
                'page': r['page']
            })
            seen.add(source_key)
    
    return formatted, sources


# ---------- Optional OpenAI ----------
# Best practice: set OPENAI_API_KEY as an environment variable, not in code.
# e.g. in terminal: export OPENAI_API_KEY="..."
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "").strip()

# If not in environment, you can set it here (not recommended for production)
if not OPENAI_API_KEY:
    OPENAI_API_KEY = "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"

OPENAI_ENABLED = len(OPENAI_API_KEY) > 0
client = None

if OPENAI_ENABLED:
    try:
        from openai import OpenAI
        client = OpenAI(api_key=OPENAI_API_KEY)
        print("✅ OpenAI client initialized successfully")  # Debug message
    except Exception as e:
        print(f"❌ Failed to initialize OpenAI client: {e}")  # Debug message
        client = None
        OPENAI_ENABLED = False


def generate_rule_based_reply(user_message: str, ctx: dict) -> str:
    import re
    # --- Currency Converter Agent ---
    match = re.match(r"convert (\d+(?:\.\d+)?) (\w+|[€$£₹]) to (\w+|[€$£₹])", user_message, re.I)
    if match:
        amount = float(match.group(1))
        from_curr = match.group(2).upper()
        to_curr = match.group(3).upper()
        result = execute_currency_function("convert_currency_amount", {"amount": amount, "from_currency": from_curr, "to_currency": to_curr})
        if result["success"]:
            return result["explanation"]
        else:
            return result["error"]

    # --- Calculator Agent (arithmetic) ---
    match = re.match(r"(add|subtract|multiply|divide) (\d+(?:\.\d+)?) (and|by) (\d+(?:\.\d+)?)", user_message, re.I)
    if match:
        op = match.group(1).lower()
        a = float(match.group(2))
        b = float(match.group(4))
        result = execute_calculator_function("perform_arithmetic", {"operation": op, "a": a, "b": b})
        return result["explanation"]

    text = user_message.lower()
    currency = ctx.get("currency", "€")
    # Spending most category
    if (
        "spending the most" in text
        or "most on" in text
        or "highest expense" in text
        or "biggest expense" in text
        or "top expense" in text
        or ("where" in text and "spend" in text)
    ):
        expenses = ctx.get("expenses", {})
        if not expenses:
            return "I don't have your expense breakdown yet. Please enter your expenses in the sidebar."
        top_cat = max(expenses, key=expenses.get)
        top_amt = expenses[top_cat]
        msg = f"You spend the most on **{top_cat}**: {currency}{top_amt:,.0f}."
        # Optionally, show top 3
        sorted_exp = sorted(expenses.items(), key=lambda x: x[1], reverse=True)
        msg += "\n\nYour top 3 expense categories are:\n"
        for i, (cat, amt) in enumerate(sorted_exp[:3]):
            msg += f"{i+1}. {cat}: {currency}{amt:,.0f}\n"
        return msg

    # Savings goal questions
    if "goal" in text or ("save" in text and "month" in text):
        if ctx.get("goal_amount", 0) <= 0:
            return "Please add a savings goal amount in the sidebar and ask again."

        monthly_required = ctx.get("required_monthly_savings", 0)
        msg = (
            f"To reach **{currency}{ctx['goal_amount']:,.0f}** "
            f"in **{ctx['goal_months']} months**, you must save "
            f"**{currency}{monthly_required:,.0f} per month**.\n"
        )

        if ctx.get("savings", 0) < monthly_required:
            diff = monthly_required - ctx.get("savings", 0)
            msg += (
                f"Right now you save **{currency}{ctx.get('savings', 0):,.0f}**, "
                f"so you're short by **{currency}{diff:,.0f}** per month."
            )
        else:
            msg += "You are saving enough to reach the goal 🎉"
        return msg

    # Budget summary / overview
    if "summary" in text or "budget" in text or "overview" in text:
        summary = [
            f"Gross income: {currency}{ctx.get('gross_income', 0):,.0f}",
            f"Net income: {currency}{ctx.get('net_income', 0):,.0f}",
            f"Tax (Class {ctx.get('selected_tax_class', 'I')}): {currency}{ctx.get('estimated_tax_selected', 0):,.0f}",
            f"Total expenses: {currency}{ctx.get('total_expenses', 0):,.0f}",
            f"Savings: {currency}{ctx.get('savings', 0):,.0f} ({ctx.get('savings_rate', 0):.1f}% of net income)",
        ]
        return "\n".join(summary)

    # Overspending / improvement tips
    if "reduce" in text or "overspend" in text or "improve" in text:
        tips = []
        net_income = ctx.get("net_income", 0)

        for cat, amount in ctx.get("expenses", {}).items():
            pct = amount / net_income if net_income > 0 else 0
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
        gross = ctx.get("gross_income", 0)
        base_tax = calculate_german_income_tax(gross)
        return (
            "Here’s a rough tax breakdown:\n"
            f"- Gross: {currency}{gross:,.0f}\n"
            f"- Base tax (no class): {currency}{base_tax:,.0f}\n"
            f"- Tax class {ctx.get('selected_tax_class', 'I')} estimate: {currency}{ctx.get('estimated_tax_selected', 0):,.0f}\n"
            f"- Net income: {currency}{ctx.get('net_income', 0):,.0f}\n\n"
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
    Uses RAG (FAISS) context when available.

    By default we keep answers short and practical.
    If the user asks for steps / formulas, we switch to a detailed explanation.
    """
    currency = ctx.get("currency", "€")
    text = user_message.lower()
    
    # Check if user is asking about sources/references
    asking_about_sources = any(
        kw in text for kw in [
            "source", "reference", "page number", "page numbers",
            "where did you get", "which book", "which pdf", "cite"
        ]
    )

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

    expenses = ctx.get("expenses", {}) or {}
    expenses_lines = "\n".join([f"- {k}: {v}" for k, v in expenses.items()])
    
    # A short "snapshot" of the current financial situation for the model
    
    snapshot = "\n".join(
        [
            f"Currency: {currency}",
            f"Gross income: {ctx.get('gross_income', 0)}",
            f"Net income: {ctx.get('net_income', 0)}",
            f"Tax class: {ctx.get('selected_tax_class', 'I')}",
            f"Tax: {ctx.get('estimated_tax_selected', 0)}",
            f"Expenses total: {ctx.get('total_expenses', 0)}",
            f"Expenses breakdown:\n{expenses_lines}" if expenses_lines else "Expenses breakdown: (missing)",
            f"Savings: {ctx.get('savings', 0)}",
            f"Savings rate (% of net): {ctx.get('savings_rate', 0)}",
            f"Goal amount: {ctx.get('goal_amount', 0)}",
            f"Goal months: {ctx.get('goal_months', 0)}",
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
                "You are a personal finance assistant for users living in Germany.\n\n"
                "You MUST use the financial snapshot to answer.\n\n"
                "IMPORTANT RULE:\n"
                "If the user asks about spending (e.g. biggest expense, where they spend the most), "
                "you MUST look at the expense values in the snapshot, identify the highest one, "
                "and answer with the category name and exact amount. "
                "Do NOT give generic advice when numbers are available."
            ),
        },
        {"role": "system", "content": "User financial snapshot:\n" + snapshot},
        {"role": "system", "content": style_instructions},
    ]

    # ✅ Add RAG context (FAISS) if available
    # If asking about sources, retrieve context for ALL previous questions in history
    if asking_about_sources and len(history) > 1:
        # Collect all user questions from history
        all_questions = []
        all_sources = []
        for msg in history:
            if msg.get("role") == "user":
                question = msg.get("content", "")
                if question and question.strip():
                    kb_text, sources = retrieve_context_with_sources(question, top_k=3)
                    if kb_text:
                        all_questions.append(f"Question: {question}\nContext: {kb_text}")
                    if sources:
                        all_sources.extend(sources)
        
        # Remove duplicate sources
        unique_sources = []
        seen = set()
        for src in all_sources:
            key = (src['source'], src['page'])
            if key not in seen:
                unique_sources.append(src)
                seen.add(key)
        
        if unique_sources:
            sources_list = "\n".join([f"- [{s['source']} p.{s['page']}]" for s in unique_sources])
            messages.append(
                {
                    "role": "system",
                    "content": (
                        f"IMPORTANT: The user is asking about sources. "
                        f"Here are ALL the sources used in this conversation:\n{sources_list}\n\n"
                        f"Provide the exact page numbers as listed above. Do NOT make up page numbers."
                    ),
                }
            )
        
        # Also get context for current question
        kb_context, current_sources = retrieve_context_with_sources(user_message, top_k=5)
    else:
        # Normal retrieval for current question only
        kb_context, current_sources = retrieve_context_with_sources(user_message, top_k=5)
    
    if kb_context:
        print(f"📚 RAG context retrieved: {len(kb_context)} characters")
        messages.append(
            {
                "role": "system",
                "content": (
                    "IMPORTANT: The following excerpts are from the knowledge base (PDF books). "
                    "You MUST cite sources using the EXACT format [Book.pdf p.12] as shown in the excerpts. "
                    "Use ONLY the page numbers provided in the excerpts - do NOT make up page numbers. "
                    "Always mention which source you're using. "
                    "If the user asks about sources, provide the EXACT sources and page numbers from the excerpts below.\n\n"
                    "Knowledge base excerpts:\n"
                    + kb_context
                ),
            }
        )
    else:
        # Even if no RAG context, tell the model to mention when it's using general knowledge
        messages.append(
            {
                "role": "system",
                "content": (
                    "If you use information from the knowledge base, cite sources like [Book.pdf p.12]. "
                    "If you're using general knowledge (not from the knowledge base), you can say so."
                ),
            }
        )

    # Keep a little bit of chat history so the assistant stays consistent.
    # IMPORTANT: history already includes the latest user message in your app,
    # so we exclude it here to avoid duplication.
    trimmed = history[-6:]
    if trimmed and trimmed[-1].get("role") == "user":
        trimmed = trimmed[:-1]

    for msg in trimmed:
        messages.append({"role": msg["role"], "content": msg["content"]})

    # If they want details, nudge the model once more in the user message
    if wants_detail:
        user_content = user_message + "\n\nPlease show the formula and each step you use."
    else:
        user_content = user_message

    messages.append({"role": "user", "content": user_content})

    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",  # Fixed: corrected model name (gpt-4.1-mini doesn't exist)
            messages=messages,
            temperature=0.2,
        )
        return response.choices[0].message.content
    except Exception as e:
        print(f"❌ Error in OpenAI API call: {type(e).__name__}: {e}")
        raise  # Re-raise to be caught by generate_bot_reply


def generate_bot_reply(user_message: str, ctx: dict, history: list) -> str:
    """
    Pick OpenAI when available, otherwise use the offline assistant.
    If OpenAI errors, fall back to offline assistant automatically.
    """
    # Debug: Check OpenAI status
    if not OPENAI_ENABLED:
        print("⚠️ OpenAI is not enabled - check API key")
    elif client is None:
        print("⚠️ OpenAI client is None - initialization failed")
    else:
        print(f"✅ OpenAI is ready - processing: '{user_message[:50]}...'")
    
    if OPENAI_ENABLED and client is not None:
        try:
            reply = generate_openai_reply(user_message, ctx, history)
            print("✅ OpenAI response received successfully")
            return reply
        except Exception as e:
            # Log error for debugging
            print(f"❌ OpenAI API error: {type(e).__name__}: {e}")
            import traceback
            traceback.print_exc()
            # True fallback (not just a message)
            return generate_rule_based_reply(user_message, ctx)

    print("⚠️ Using rule-based fallback assistant")
    return generate_rule_based_reply(user_message, ctx)
