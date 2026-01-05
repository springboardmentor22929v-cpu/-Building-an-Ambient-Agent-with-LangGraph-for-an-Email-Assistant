# Email Assistant Agent - Milestone 1 Setup

## Quick Setup Guide

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Get API Keys

#### Google Gemini API Key:
1. Visit: https://aistudio.google.com/
2. Sign in with Google account
3. Click "Get API Key" 
4. Create new API key
5. Copy the key

#### LangSmith API Key (Optional for tracing):
1. Visit: https://smith.langchain.com/
2. Sign up/login
3. Go to Settings → API Keys
4. Create new key

### 3. Configure Environment
Edit `.env` file and add your keys:
```
GOOGLE_API_KEY=your_gemini_api_key_here
LANGCHAIN_API_KEY=your_langsmith_key_here
```

### 4. Run the Agent

#### Demo Mode:
```bash
python demo.py
```

#### Evaluation Mode:
```bash
python evaluate.py
```

## Project Structure
```
Email Assistant/
├── requirements.txt      # Dependencies
├── .env                 # API keys (create this)
├── agent_core.py        # Core agent components
├── react_agent.py       # ReAct agent with LangGraph
├── test_data.py         # Golden test dataset
├── evaluate.py          # Triage accuracy evaluation
└── demo.py             # Interactive demo
```

## Success Criteria
- Triage accuracy >80% on golden test set
- Agent classifies emails as: ignore, notify_human, respond
- ReAct loop uses mock tools (calendar, contacts)
- LangSmith tracing enabled for debugging

## Next Steps
1. Set up API keys
2. Run `python demo.py` to test
3. Run `python evaluate.py` for milestone evaluation
4. Check LangSmith traces for agent reasoning