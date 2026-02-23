# 🧠 Milestone 4: Persistent Memory & Real Tools

This milestone upgrades your agent with a "Brain" (SQLite Memory) and "Hands" (Real Gmail/Calendar APIs).

## 📁 New Files
- **`m4_memory.py`**: Manages the SQLvite database for storing user preferences.
- **`m4_learning.py`**: Analyzes your edits to learn new rules (e.g., "Call me Bob").
- **`m4_tools.py`**: Real Gmail and Google Calendar integrations.
- **`m4_graph.py`**: The updated agent graph that uses memory and real tools.
- **`m4_evaluation.py`**: A test script to verify the agent learns from your corrections.

## 🚀 Setup Instructions

### 1. Update Credentials
Ensure your `credentials.json` is in the project root.
*Note: You might need to re-authenticate because we added the `Calendar` scope.*
Delete `token.json` if you see permission errors, and run the agent to re-login.

### 2. Run the Evaluation (Test Learning)
This script simulates the "Email Bob" -> "Edit" -> "Email Bob again" flow to prove the agent learns.

```bash
python m4_evaluation.py
```

### 3. Run in LangGraph Studio
To use the new memory-enabled agent in the UI:

1.  Open `langgraph.json`
2.  Change the graph path to `m4_graph.py`:
    ```json
    "graphs": {
      "email_agent": "./m4_graph.py:app"
    }
    ```
3.  Run `langgraph dev` (or `studio`).

## 🧠 How Learning Works
1.  Agent drafts a reply.
2.  You click **Edit** in Studio and change something (e.g., change "Best," to "Cheers,").
3.  You click **Approve** (with the edited text).
4.  The agent detects the change, calls the LLM to figure out *why* you changed it, and saves a rule (e.g., `sign_off: Cheers`) to `agent_memory.sqlite`.
5.  Next time, it loads that rule *before* drafting!
