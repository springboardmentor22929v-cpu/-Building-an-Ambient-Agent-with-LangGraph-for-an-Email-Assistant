# 📧 Ambient Email Assistant – Milestone 1

## 🎯 Project Overview
This project is an **ambient email assistant** built with **LangGraph** and **LangChain**.  
Its job is to automatically **triage incoming emails** into three categories:
- **Ignore** → newsletters, promotions, routine notifications
- **Notify Human** → urgent issues, escalations, errors
- **Respond** → meeting requests, questions, feedback

Milestone 1 focused on building the agent’s **basic brain** and evaluation framework.

---

## 🛠️ Components Built
- **Environment Setup**
  - Python project structure (`src/`, `data/`, `requirements.txt`)
  - Dependencies: `langgraph`, `langchain`, `langsmith`, `python-dotenv`
- **Mock LLM (`MockLLM`)**
  - Rule‑based classifier for triage
  - Simple draft reply generator
- **Agent Workflow (LangGraph)**
  - **Triage Node** → decides category
  - **Act Node** → executes action (archive, notify, respond)
- **Mock Tools**
  - `archive_email()` → simulate ignoring
  - `notify_human()` → simulate escalation
  - `send_draft()` → simulate replying
- **Evaluation Framework**
  - Golden dataset of 50 labeled emails (`data/test_emails.json`)
  - `evaluate.py` script to measure accuracy
- **LangSmith Integration**
  - Logs runs and shows reasoning traces

## 📊 Results
- Initial dataset (30 emails): ~73% accuracy  
- Improved classifier rules: 80%  
- Expanded dataset (50 emails): **Final Accuracy = 86%**  
- ✅ Milestone 1 success criteria (>80% accuracy) achieved and exceeded

---

