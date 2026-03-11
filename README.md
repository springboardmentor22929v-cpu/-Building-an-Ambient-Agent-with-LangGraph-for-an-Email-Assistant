# Ambient Email Assistant with LangGraph

An intelligent email assistant built with LangGraph that autonomously manages email workflows using AI agents, featuring human-in-the-loop workflows and memory persistence.

## Features

- Email triage and classification (ignore/notify/respond)
- ReAct agent architecture with tool integration
- Human-in-the-loop approval workflows
- SQLite-based memory for user preferences
- Gmail API integration for production use

## Installation

**Prerequisites**: Python 3.11+, Google Gemini API key, LangSmith account

```bash
# Clone and setup
git clone <repository-url>
cd ambient_agent_101-m

# Create .env file
cp .env.example .env

# Install dependencies
pip install uv
uv sync --extra dev
source .venv/bin/activate  # Windows: .venv\Scripts\activate
```

## Environment Configuration

Edit `.env` file with your credentials:

```env
GEMINI_API_KEY=Your_API_Key
LLM_MODEL=gemini-2.5-flash-lite
GOOGLE_APPLICATION_CREDENTIALS=credentials.json
LANGSMITH_API_KEY=Your_API_Key
LANGSMITH_TRACING=true
LANGSMITH_PROJECT=Your_Project_Name
```

## Usage

**LangGraph Studio**: `langgraph dev`

**Available Agents**:
- `email_assistant` - Basic ReAct agent
- `email_assistant_hitl` - Human-in-the-loop
- `email_assistant_hitl_memory` - With memory
- `email_assistant_hitl_memory_gmail` - Full Gmail integration

**Gmail Setup**: Setup Gmail OAuth and run `python src/email_assistant/tools/gmail/setup_gmail.py`

**Testing**: `python tests/run_all_tests.py`

## Resources

- [LangGraph Documentation](https://langchain-ai.github.io/langgraph/)
- [LangChain Academy](https://academy.langchain.com/)
- [Ambient Agents Concept](https://blog.langchain.dev/introducing-ambient-agents/)
- [Gmail API Documentation](https://developers.google.com/gmail/api)


This section shows how to add human-in-the-loop (HITL), allowing the user to review specific tool calls (e.g., send email, schedule meeting). For this, we use [Agent Inbox](https://github.com/langchain-ai/agent-inbox) as an interface for human in the loop. You can see the linked code for the full implementation in [src/email_assistant/email_assistant_hitl.py](/src/email_assistant/email_assistant_hitl.py).



### Section 3. Memory  
* Code: [src/email_assistant/email_assistant_hitl_memory.py](/src/email_assistant/email_assistant_hitl_memory.py)

This notebook shows how to add memory to the email assistant, allowing it to learn from user feedback and adapt to preferences over time. The memory-enabled assistant ([email_assistant_hitl_memory.py](/src/email_assistant/email_assistant_hitl_memory.py)) uses the [LangGraph Store](https://langchain-ai.github.io/langgraph/concepts/memory/#long-term-memory) to persist memories. You can see the linked code for the full implementation in [src/email_assistant/email_assistant_hitl_memory.py](/src/email_assistant/email_assistant_hitl_memory.py).

  




### [Optional for Training] Section 4. Evaluation 
* Notebook: [notebooks/evaluation.ipynb](/notebooks/evaluation.ipynb)


This notebook introduces evaluation with an email dataset in [eval/email_dataset.py](/eval/email_dataset.py). It shows how to run evaluations using Pytest and the LangSmith `evaluate` API. It runs evaluation for emails responses using LLM-as-a-judge as well as evaluations for tools calls and triage decisions.






## Connecting to APIs  

The above notebooks using mock email and calendar tools. 

### Gmail Integration and Deployment

Set up Google API credentials following the instructions in [Gmail Tools README](src/email_assistant/tools/gmail/README.md).

The README also explains how to deploy the graph to LangGraph Platform.

The full implementation of the Gmail integration is in [src/email_assistant/email_assistant_hitl_memory_gmail.py](/src/email_assistant/email_assistant_hitl_memory_gmail.py).

## Running Tests

The repository includes an automated test suite to evaluate the email assistant. 

Tests verify correct tool usage and response quality using LangSmith for tracking.

### Running Tests with [run_all_tests.py](/tests/run_all_tests.py)

```shell
python tests/run_all_tests.py
```

### Test Results

Test results are logged to LangSmith under the project name specified in your `.env` file (`LANGSMITH_PROJECT`). This provides:
- Visual inspection of agent traces
- Detailed evaluation metrics
- Comparison of different agent implementations

### Available Test Implementations

The available implementations for testing are:
- `email_assistant` - Basic email assistant

### Testing Notebooks

You can also run tests to verify all notebooks execute without errors:

```shell
# Run all notebook tests
python tests/test_notebooks.py

# Or run via pytest
pytest tests/test_notebooks.py -v
```

