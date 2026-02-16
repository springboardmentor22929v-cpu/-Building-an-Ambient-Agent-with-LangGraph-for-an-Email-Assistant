# How to Run the Email Assistant

To get your Ambient Agent up and running, follow these steps:

## 1. Prerequisites
Ensure you have the following in the project root (`d:\SpringBord`):
- [ ] **`.env`**: Should contain your `GOOGLE_API_KEY` and `LANGCHAIN_API_KEY`.
- [ ] **`credentials.json`**: This is required for Google OAuth. (I noticed this file is currently missing or in a different folder).

## 2. Install Dependencies
Open your terminal in the project folder and run:
```bash
pip install -r requirements.txt
```
*(You may also need `pip install jupyter` if you haven't installed it yet)*.

## 3. Run Setup & Authentication
The `setup_auth.ipynb` notebook is your first step. It will create the necessary `token.json` for Google APIs.

1.  Open `setup_auth.ipynb` in VS Code or Jupyter.
2.  Run the cells one by one.
3.  When you reach the **"Authenticate Google Services"** cell, a browser window will open. Log in with your Google account and grant the requested permissions.

## 4. Run the Agent
Once authenticated, you can explore the agent's logic in `build_agents.ipynb` or run the system using **LangGraph Studio**.

### Running via Studio
If you have LangGraph Studio installed, you can point it to this directory. It will use the configuration in `langgraph.json` and the graph defined in `agent.py`.

### Manual Test
You can also run tests or manual execution scripts if you create a `main.py` using the `graph` instance from `agent.py`.
