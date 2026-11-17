# Wealth Navigator - Personal Finance Assistant for Germany

Wealth Navigator is a Streamlit web app that helps people living in Germany understand their budget, estimated income tax, savings rate and savings goals. It combines deterministic finance calculations with a chat assistant powered by OpenAI, and it keeps working with a rule-based offline assistant when no API key is available.

Note: the tax model is simplified and for educational purposes only. It is not financial or legal advice.

## Team

Wealth Navigator was developed as a capstone project at the Hamburg University of Applied Sciences (HAW Hamburg).

| Role | Name |
|---|---|
| Team member | Sajjadur Rahman ([GitHub](https://github.com/sajjadurrahman1)) |
| Team member | Tanjid Tonmoy |
| Supervising professor | Sailesh Conjeti |

---

## Features

- **Budget and tax analysis:** enter monthly gross income and a tax class (Steuerklasse I to VI) to get an estimated tax, net income, total expenses, savings and savings rate.
- **Savings goals:** enter a goal amount and a timeframe in months to see the monthly savings required.
- **Spending breakdown:** pie chart of six expense categories (housing, food, transport, utilities, entertainment, shopping and other), compared with rule-of-thumb budget percentages.
- **Chat assistant:** ask questions about your spending, taxes and goals. The assistant receives a snapshot of your numbers, answers briefly by default and shows step-by-step calculations when asked.
- **Offline fallback:** if no API key is set or the OpenAI call fails, a rule-based assistant answers instead. It handles questions such as "where do I spend the most", simple arithmetic ("add 100 and 50") and currency conversion ("convert 100 EUR to USD").
- **Currency conversion:** live exchange rates from a public API, cached for one hour, with built-in approximate rates as a fallback.
- **Optional document-grounded answers (RAG):** the code can index finance PDFs with FAISS and cite sources as `[Book.pdf p.12]`. This needs extra setup (see "Optional: RAG with your own PDFs").

---

## How It Works

```
app.py                     Streamlit interface: sidebar inputs, metrics, pie chart, chat
   |
   +-- finance_logic.py    Simplified German tax estimate, tax-class modifiers,
   |                       budget percentages, savings and goal calculations
   |
   +-- chat_assistant.py   Chat logic
         |                   1. build a snapshot of the user's numbers
         |                   2. OpenAI mode: gpt-4o-mini (temperature 0.2) with the snapshot,
         |                      style instructions and the last 6 messages
         |                   3. optional RAG context from FAISS, with source citations
         |                   4. on any failure or missing key: rule-based fallback
         |
         +-- calculator_agent.py          Exact finance calculations (9 functions)
         +-- currency_converter_agent.py  Currency conversion (3 functions), cached rates
         +-- rag_query.py / ingest_pdfs.py  Optional RAG (all-MiniLM-L6-v2 + FAISS)

memory_store.py            SQLite storage module for chats and preferences
                           (present in the repository, not yet connected to the UI)
```

**Tax model:** the monthly income is converted to an annual figure, a simplified progressive scheme is applied (tax-free allowance up to EUR 11,604, 20 % band, 42 % band, 45 % top rate), and the result is adjusted by a simple factor per tax class. It does not include social contributions or church tax.

---

## Tech Stack

- Python 3.9 or newer
- Streamlit, pandas, matplotlib, numpy
- OpenAI API (`gpt-4o-mini`)
- requests (exchange rates)
- Optional RAG: sentence-transformers (`all-MiniLM-L6-v2`), FAISS, pypdf
- SQLite (memory module)

---

## Project Structure

```
Wealth-Navigator/
|-- app.py                        Streamlit app
|-- finance_logic.py              Tax, budget and savings calculations
|-- chat_assistant.py             Chat orchestration, OpenAI, RAG hook, fallback
|-- calculator_agent.py           Calculation tools
|-- currency_converter_agent.py   Currency conversion tools
|-- memory_store.py               SQLite memory module (not yet used by the UI)
|-- rag_query.py                  Optional: search a FAISS index
|-- ingest_pdfs.py                Optional: build the FAISS index from PDFs
|-- requirements.txt
`-- README.md
```

---

## Getting Started

### 1. Clone and install

```bash
git clone https://github.com/sajjadurrahman1/Wealth-Navigator.git
cd Wealth-Navigator
python -m venv .venv
source .venv/bin/activate        # macOS / Linux
.venv\Scripts\activate           # Windows
pip install -r requirements.txt
```

### 2. Add your OpenAI API key (optional)

Without a key the app still runs with the rule-based assistant. To enable OpenAI answers, set the key as an environment variable or put it in a local `.env` file (already ignored by git):

```
OPENAI_API_KEY=sk-...
```

Never write the key into the source code and never commit it.

### 3. Run

```bash
streamlit run app.py
```

The app opens at http://localhost:8501.

---

## Optional: RAG with your own PDFs

The RAG code expects this layout, relative to the project root:

```
rag/
|-- rag_query.py
|-- ingest_pdfs.py
`-- data/
    |-- pdfs/            put your finance PDFs here
    |-- faiss.index      created by the ingestion script
    `-- metadata.jsonl   created by the ingestion script
```

1. Create the `rag/` folder and move `rag_query.py` and `ingest_pdfs.py` into it.
2. Put your PDFs in `rag/data/pdfs/`.
3. From the project root, run `python rag/ingest_pdfs.py`.
4. Start the app. If the index is found, answers include citations such as `[Book.pdf p.12]`.

The PDFs and the index are not included in this repository.

---

## Example Questions

- Where am I spending the most?
- How much do I need to save per month to reach my goal?
- Explain how my tax was calculated, step by step.
- convert 100 EUR to USD

---

## Limitations

- Simplified German tax model (no social contributions, church tax or deductions).
- The tax-class factors are a rough approximation.
- Exchange rates depend on a public API; approximate fallback rates are used if it is unavailable.
- RAG needs your own PDFs and a local index; scanned PDFs without text are not supported (no OCR).
- Chat history exists only in the browser session; the SQLite memory module is not connected to the interface yet.
- Not financial or legal advice.

## Possible Improvements

- Connect `memory_store.py` to the interface for persistent, multi-chat history.
- More realistic German net salary calculation.
- Add the RAG data folder and a small public document set.
- OCR for scanned documents, and export of reports to PDF or CSV.
- Investment and retirement planning.
