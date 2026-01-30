# core/state.py

from typing import TypedDict, Annotated, List
from langchain_core.messages import BaseMessage
import operator

class AgentState(TypedDict):
    # 'messages' stores the conversation history (Email -> AI Thought -> Draft)
    # operator.add means "append new messages to the list" instead of overwriting.
    messages: Annotated[List[BaseMessage], operator.add]
    
    # 'triage_decision' stores the final classification: 'RESPOND', 'IGNORE', or 'NOTIFY'
    triage_decision: str