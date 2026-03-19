# 💶 Wealth Navigator  
**A Retrieval-Augmented Personal Finance Assistant for Germany**

Wealth Navigator is an **explainable, retrieval-augmented personal finance assistant** designed for users living in Germany.  
It combines deterministic financial calculations, conversational AI, persistent memory, and document-grounded responses to help users understand their income, taxes, expenses, and savings goals in a **transparent and trustworthy way**.

---

## 📌 Key Features

### 🇩🇪 Germany-Specific Finance Logic
- Simplified German income tax estimation  
- Support for all **Steuerklassen (I–VI)**  

### 📊 Budget & Savings Analysis
- Net income calculation  
- Expense breakdown & savings rate  
- Savings goal feasibility checks  

### 💬 Conversational Assistant
- Ask questions about spending, taxes, goals, and budgeting  
- Maintains conversation context  

### 📚 Retrieval-Augmented Generation (RAG)
- Answers grounded in financial PDF documents  
- Page-level citations *(Book + page number)*  

### 🧠 Persistent Memory
- SQLite-based storage for chats and user preferences  
- Multi-chat support *(create, rename, delete chats)*  

### 🧮 Agent Tools for Accuracy
- **Calculator Agent** (step-by-step math)  
- **Currency Converter Agent** (live + cached rates)  

### 📴 Offline-First Design
- Rule-based fallback when OpenAI or RAG is unavailable  

---

## 🏗️ System Architecture

The project follows a **modular layered architecture**:

---

## 📁 Project Structure
wealth-navigator/
│
├── app.py # Streamlit frontend (UI + chat interface)
├── finance_logic.py # Deterministic finance calculations
├── chat_assistant.py # Chat orchestration, RAG, agents, fallback logic
├── memory_store.py # SQLite-based persistent memory
├── calculator_agent.py # Exact arithmetic & financial calculations
├── currency_converter_agent.py # Live & cached currency conversion
│
├── rag/
│ ├── ingest_pdfs.py # PDF ingestion & FAISS index creation
│ ├── rag_query.py # Vector search over indexed documents
│ └── data/
│ ├── pdfs/ # Financial PDF sources
│ ├── faiss.index # FAISS vector index
│ └── metadata.jsonl # Chunk metadata (source, page, text)
│
├── requirements.txt
└── README.md

---

## 🧮 Finance Logic Overview (`finance_logic.py`)

- Converts **monthly income → annual income**  
- Applies simplified **progressive tax brackets**  
- Adjusts tax using **Steuerklasse modifiers**  

### Computes:
- Net income  
- Total expenses  
- Savings & savings rate  
- Required monthly savings for goals  

- Uses **rule-of-thumb budget guidelines** for analysis  

> ⚠️ **Note:** Tax logic is simplified and intended for educational purposes only.

---

## 💬 Chat Assistant Logic (`chat_assistant.py`)

The assistant operates in three modes:

### 1. OpenAI Mode
- Short, practical answers by default  
- Detailed step-by-step explanations on request  

### 2. RAG Mode (Additive)
- Retrieves relevant PDF excerpts using FAISS  
- Injects them into prompts with enforced citations  

### 3. Rule-Based Offline Mode
- Ensures the app works without external APIs  

### 🔒 Built-in Guardrails
- Deterministic finance calculations  
- Tool-based math and currency conversion  
- Citation enforcement *(no invented sources)*  
- Automatic fallback if APIs fail  

---

## 📚 Retrieval-Augmented Generation (RAG)

### Pipeline

1. Extract text from PDFs *(page-wise)*  
2. Clean and normalize text  
3. Chunk text with overlap  
4. Generate embeddings using `all-MiniLM-L6-v2`  
5. Store vectors in FAISS  
6. Retrieve top-k chunks at query time  

### Example Citation

---

## 🧠 Memory & Multi-Chat Support (`memory_store.py`)

- SQLite-backed storage  

### Stores:
- Conversations  
- Messages  
- Long-term user preferences  

### Features:
- Multi-chat UI  
- Rename / delete chats  
- Clear inputs vs clear memory  
- Optional TTL expiration  

> ✅ All data is stored locally to protect user privacy.

---

## 🧮 Agent Tools

### Calculator Agent
- Exact arithmetic  
- Savings rate  
- Required savings  
- Tax estimation  
- Time-to-goal  
- Step-by-step explanations  

### Currency Converter Agent
- Live exchange rates *(cached)*  
- Fallback rates if API unavailable  

### Supports:
- Individual amounts  
- Full financial summaries  

**Example:**
convert 100 EUR to USD

---

## 🚀 Getting Started

### 1️⃣ Install Dependencies
```bash
pip install -r requirements.txt
python rag/ingest_pdfs.py
## ⚠️ Limitations

- Simplified German tax model *(no social contributions, Kirchensteuer, etc.)*  
- No OCR support for scanned PDFs  
- Exchange rates depend on a public API  
- Not intended as legal or financial advice  

---

## 🔮 Future Improvements

- More realistic German net salary calculations  
- OCR integration for scanned documents  
- Investment & retirement planning  
- Cloud deployment with authentication  
- PDF / CSV export of financial reports  

---

## 🎓 Academic Context

This project was developed as a **Capstone Project**, demonstrating:

- Explainable AI  
- Retrieval-Augmented Generation  
- Guardrails for high-risk domains (finance)  
- Robust system design with offline fallback  

---

## 👥 Authors

- **Sajjadur Rahman**  
- **Tanjid Tonmoy**  
