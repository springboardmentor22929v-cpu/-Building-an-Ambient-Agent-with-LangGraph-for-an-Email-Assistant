from langgraph.graph import StateGraph, END
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.schema import HumanMessage, SystemMessage
from agent_core import AgentState, TriageNode, MockTools
import json
import os
from dotenv import load_dotenv

load_dotenv()

class ReActAgent:
    def __init__(self):
        self.llm = ChatGoogleGenerativeAI(
            model="gemini-1.5-flash",
            google_api_key=os.getenv("GOOGLE_API_KEY"),
            temperature=0.2
        )
        self.triage_node = TriageNode()
        self.tools = MockTools()
        
    def should_respond(self, state: AgentState) -> str:
        """Route based on triage decision"""
        decision = state.get("triage_decision", "notify_human")
        
        if decision == "respond":
            return "react_loop"
        else:
            return "end_process"
    
    def react_reasoning(self, state: AgentState) -> AgentState:
        """ReAct loop: Reason about what action to take"""
        
        react_prompt = f"""
You are processing an email that needs a response. Use the ReAct framework:

Email Subject: {state['email_subject']}
Email Content: {state['email_content']}
Sender: {state['email_sender']}

Available tools:
- read_calendar(date): Get calendar information
- get_contact_info(name): Look up contact details

Think step by step:
1. What information do I need to respond appropriately?
2. What tools should I use?
3. How should I structure my response?

Format your response as:
THOUGHT: [your reasoning]
ACTION: [tool_name(parameters) or "compose_response"]
"""

        messages = [
            SystemMessage(content="You are a helpful email assistant using ReAct reasoning."),
            HumanMessage(content=react_prompt)
        ]
        
        response = self.llm.invoke(messages)
        
        # Parse and execute action
        lines = response.content.strip().split('\n')
        thought = ""
        action = "compose_response"
        
        for line in lines:
            if line.startswith("THOUGHT:"):
                thought = line.split(":", 1)[1].strip()
            elif line.startswith("ACTION:"):
                action = line.split(":", 1)[1].strip()
        
        state["reasoning"] = thought
        
        # Execute tool if needed
        if "read_calendar" in action:
            calendar_data = self.tools.read_calendar()
            state["tools_used"].append("read_calendar")
            state["reasoning"] += f" | Calendar: {calendar_data}"
        elif "get_contact_info" in action:
            # Extract name from action
            if "(" in action:
                name = action.split("(")[1].split(")")[0].strip('"\'')
                contact_data = self.tools.get_contact_info(name)
                state["tools_used"].append("get_contact_info")
                state["reasoning"] += f" | Contact: {contact_data}"
        
        return state
    
    def compose_response(self, state: AgentState) -> AgentState:
        """Generate email response based on reasoning and tool results"""
        
        compose_prompt = f"""
Based on your analysis, compose a professional email response.

Original Email:
Subject: {state['email_subject']}
From: {state['email_sender']}
Content: {state['email_content']}

Your reasoning: {state['reasoning']}
Tools used: {state['tools_used']}

Write a concise, professional response. Include subject line.

Format:
SUBJECT: [response subject]
BODY: [response body]
"""

        messages = [
            SystemMessage(content="You are a professional email assistant."),
            HumanMessage(content=compose_prompt)
        ]
        
        response = self.llm.invoke(messages)
        state["response_content"] = response.content
        
        return state
    
    def end_process(self, state: AgentState) -> AgentState:
        """Handle non-response cases"""
        decision = state["triage_decision"]
        
        if decision == "ignore":
            state["response_content"] = "Email marked as ignore - no action needed"
        elif decision == "notify_human":
            state["response_content"] = "Email requires human attention - forwarded to human"
        
        return state
    
    def create_graph(self):
        """Create the LangGraph workflow"""
        workflow = StateGraph(AgentState)
        
        # Add nodes
        workflow.add_node("triage", self.triage_node.classify_email)
        workflow.add_node("react_loop", self.react_reasoning)
        workflow.add_node("compose_response", self.compose_response)
        workflow.add_node("end_process", self.end_process)
        
        # Set entry point
        workflow.set_entry_point("triage")
        
        # Add conditional routing
        workflow.add_conditional_edges(
            "triage",
            self.should_respond,
            {
                "react_loop": "react_loop",
                "end_process": "end_process"
            }
        )
        
        # Add edges
        workflow.add_edge("react_loop", "compose_response")
        workflow.add_edge("compose_response", END)
        workflow.add_edge("end_process", END)
        
        return workflow.compile()

# Main execution function
def process_email(email_subject: str, email_sender: str, email_content: str) -> dict:
    """Process a single email through the agent"""
    
    agent = ReActAgent()
    graph = agent.create_graph()
    
    initial_state = AgentState(
        email_content=email_content,
        email_subject=email_subject,
        email_sender=email_sender,
        triage_decision="notify_human",
        reasoning="",
        tools_used=[],
        response_content=""
    )
    
    result = graph.invoke(initial_state)
    
    return {
        "triage_decision": result["triage_decision"],
        "reasoning": result["reasoning"],
        "tools_used": result["tools_used"],
        "response_content": result["response_content"]
    }