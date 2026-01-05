# Ambient Email Agent (LangGraph + Gemini)

This repository contains a prototype ambient email assistant that performs
triage and can draft or send responses. The code includes a small LLM
integration layer that will attempt to use Google Generative AI / Gemini
when a valid `GEMINI_API_KEY` is provided.

Setup

1. Create a virtual environment and install dependencies:

```bash
python -m venv .venv
source .venv/bin/activate  # on Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

2. Copy `.env.example` to `.env` and set your API key:

```bash
copy .env.example .env
# then edit .env and set GEMINI_API_KEY
```

3. Run the evaluation on the sample "golden" emails:

```bash
python -m src_py.evaluate
```

Notes

- The LLM wrapper is in `src_py/llm.py`. It reads `GEMINI_API_KEY` from the
  environment and attempts to call the `google-generativeai` SDK. If the SDK
  or key are not available, the system falls back to the deterministic
  heuristic in `src_py/triage.py`.
- For production use, do not commit API keys to source control. Use a secrets
  manager or environment variables.
