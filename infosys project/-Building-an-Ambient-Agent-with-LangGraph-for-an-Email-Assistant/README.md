# Email Assistant Agent - Milestone 1

An autonomous email assistant built with LangGraph and Google Gemini that can triage emails and perform intelligent responses.

## Project Structure

```
├── email_agent.py          # Main agent implementation
├── evaluate_triage.py      # Triage accuracy evaluation
├── development.ipynb       # Interactive development notebook
├── requirements.txt        # Python dependencies
├── .env                   # Environment variables (create from template)
└── README.md              # This file
```

## Setup Instructions

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Configure API Keys

1. Copy the `.env` file and add your API keys:
   - Get a Google Gemini API key from [Google AI Studio](https://makersuite.google.com/app/apikey)
   - (Optional) Get a LangSmith API key from [LangSmith](https://smith.langchain.com/)

2. Update the `.env` file:
```env
GOOGLE_API_KEY=your_actual_google_api_key_here
LANGCHAIN_API_KEY=your_langsmith_api_key_here  # Optional
```

### 3. Test the Agent

Run the basic test:
```bash
python email_agent.py
```

Run the triage evaluation:
```bash
python evaluate_triage.py
```

## Features Implemented (Milestone 1)

### ✅ Core Components
- **Triage Node**: Classifies emails into `ignore`, `notify_human`, or `respond`
- **ReAct Agent Loop**: Reasoning and action cycle with tool usage
- **Mock Tools**: Calendar reading, user preferences, draft responses
- **LangGraph Integration**: Stateful graph-based agent architecture

### ✅ Evaluation Framework
- Golden dataset of 15 test emails across all categories
- Automated accuracy measurement
- Success criteria: >80% triage accuracy
- Detailed results logging and visualization

### ✅ Development Environment
- Jupyter notebook for interactive testing
- Modular code structure
- Environment variable management
- LangSmith integration for tracing (optional)

## Agent Architecture

```
Email Input → Triage Node → Decision Branch
                ↓
    ┌─────────────┼─────────────┐
    ↓             ↓             ↓
  ignore    notify_human     respond
    ↓             ↓             ↓
   END           END      Reason Node
                            ↓
                      Tool Selection
                            ↓
                       Act (Tools)
                            ↓
                      Complete Node
                            ↓
                           END
```

## Usage Examples

### Basic Email Processing
```python
from email_agent import EmailAgent

agent = EmailAgent()
result = agent.process_email(
    email_content="Hi, can we schedule a meeting next week?",
    sender="client@company.com",
    subject="Meeting Request"
)

print(f"Decision: {result['triage_decision']}")
print(f"Reasoning: {result['reasoning']}")
```

### Running Evaluation
```python
from evaluate_triage import TriageEvaluator

evaluator = TriageEvaluator()
results = evaluator.evaluate_triage_accuracy()
print(f"Accuracy: {results['accuracy']:.2%}")
```

## Triage Categories

- **ignore**: Spam, newsletters, unimportant automated emails
- **notify_human**: Urgent, sensitive, or complex emails requiring human attention
- **respond**: Standard emails that can be handled automatically

## Tools Available

- `read_calendar`: Check calendar availability
- `get_user_preferences`: Retrieve user email handling preferences  
- `draft_response`: Generate email response drafts

## Success Metrics

- **Target**: >80% triage accuracy on golden dataset
- **Current Status**: Run `python evaluate_triage.py` to check

## Next Steps (Future Milestones)

- [ ] Human-in-the-Loop (HITL) implementation
- [ ] Persistent memory system
- [ ] Gmail API integration
- [ ] Advanced tool safety classification
- [ ] User interface development

## Troubleshooting

### Common Issues

1. **API Key Error**: Ensure your Google API key is correctly set in `.env`
2. **Import Errors**: Run `pip install -r requirements.txt`
3. **Low Accuracy**: Check the evaluation results and refine triage prompts

### Debug Mode

Enable LangSmith tracing by setting these environment variables:
```env
LANGCHAIN_TRACING_V2=true
LANGCHAIN_API_KEY=your_langsmith_key
```

## Contributing

This is a learning project following the milestone-based development approach outlined in the project specification.