import os
import re
import json
from typing_extensions import TypedDict
from typing import Literal, List, Dict, Any
from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI
from langgraph.graph import StateGraph, END
from langchain_core.messages import HumanMessage, SystemMessage
from mock_tools import MockTools, get_tool_descriptions

load_dotenv()

class EmailState(TypedDict):
    email_content: str
    sender: str
    subject: str
    triage_decision: Literal["ignore", "notify_human", "respond"]
    reasoning: str
    tools_used: List[str]
    response_draft: str
    react_steps: List[Dict[str, str]]

class EnhancedEmailAgent:
    def __init__(self):
        self.llm = ChatGoogleGenerativeAI(
            model="models/gemini-2.0-flash",
            google_api_key=os.getenv("GOOGLE_API_KEY"),
            temperature=0.1
        )
        self.tools = MockTools()
        
    def triage_node(self, state: EmailState) -> EmailState:
        """Enhanced triage node with better classification logic"""
        triage_prompt = f"""
        You are an expert email triage agent. Analyze this email and classify it into exactly one category:

        CLASSIFICATION RULES:
        1. "ignore" - Use for:
           - Newsletters, promotional emails, spam
           - Automated notifications (GitHub, social media, etc.)
           - Non-actionable informational emails
        
        2. "notify_human" - Use for:
           - Urgent emails from executives/management
           - Legal, HR, or security issues
           - Budget approvals or business-critical decisions
           - Customer complaints or sales opportunities
           - Emergency situations or system outages
        
        3. "respond" - Use for:
           - Meeting requests or scheduling
           - Status update requests
           - Simple questions that can be answered
           - Routine confirmations or acknowledgments
           - Code reviews or technical discussions

        EMAIL TO CLASSIFY:
        From: {state["sender"]}
        Subject: {state["subject"]}
        Content: {state["email_content"]}

        Respond with valid JSON only:
        {{
            "decision": "ignore|notify_human|respond",
            "reasoning": "Clear explanation of why this classification was chosen"
        }}
        """
        
        messages = [HumanMessage(content=triage_prompt)]
        response = self.llm.invoke(messages)
        
        try:
            # Clean response and extract JSON
            content = response.content.strip()
            if content.startswith("```json"):
                content = content[7:-3]
            elif content.startswith("```"):
                content = content[3:-3]
            
            result = json.loads(content)
            state["triage_decision"] = result["decision"]
            state["reasoning"] = result["reasoning"]
        except Exception as e:
            # Fallback classification based on keywords
            content_lower = (state["email_content"] + " " + state["subject"]).lower()
            sender_lower = state["sender"].lower()
            
            # Check for urgent/important keywords
            urgent_keywords = ["urgent", "asap", "emergency", "critical", "immediate"]
            important_senders = ["ceo", "manager", "legal", "hr", "security"]
            
            if any(keyword in content_lower for keyword in urgent_keywords) or \
               any(sender in sender_lower for sender in important_senders):
                state["triage_decision"] = "notify_human"
                state["reasoning"] = "Classified as urgent/important based on keywords"
            elif "noreply" in sender_lower or "newsletter" in content_lower:
                state["triage_decision"] = "ignore"
                state["reasoning"] = "Automated/promotional email"
            else:
                state["triage_decision"] = "respond"
                state["reasoning"] = "Standard email that can be handled automatically"
                
        return state

    def react_agent_node(self, state: EmailState) -> EmailState:
        """Enhanced ReAct agent with proper tool integration"""
        if state["triage_decision"] != "respond":
            return state
            
        state["react_steps"] = []
        
        # Initial reasoning step
        react_prompt = f"""
        You are a helpful email assistant using ReAct (Reason + Act) methodology.
        
        AVAILABLE TOOLS:
        {get_tool_descriptions()}
        
        EMAIL TO RESPOND TO:
        From: {state["sender"]}
        Subject: {state["subject"]}
        Content: {state["email_content"]}
        
        Follow this format EXACTLY:
        Thought: [Analyze what the email is asking for and what information you need]
        Action: [tool_name(parameters) OR "draft_response" if no tools needed]
        Observation: [This will be filled by tool execution]
        
        Start with your Thought:
        """
        
        messages = [HumanMessage(content=react_prompt)]
        response = self.llm.invoke(messages)
        
        # Parse ReAct steps
        max_iterations = 3
        current_context = response.content
        
        for iteration in range(max_iterations):
            # Extract thought and action
            thought_match = re.search(r'Thought:\s*(.*?)(?=Action:|$)', current_context, re.DOTALL)
            action_match = re.search(r'Action:\s*(.*?)(?=Observation:|$)', current_context, re.DOTALL)
            
            if not thought_match or not action_match:
                break
                
            thought = thought_match.group(1).strip()
            action = action_match.group(1).strip()
            
            # Execute action
            observation = self._execute_action(action, state)
            
            # Record step
            state["react_steps"].append({
                "thought": thought,
                "action": action,
                "observation": observation
            })
            
            # If action was draft_response, we're done
            if "draft_response" in action.lower():
                state["response_draft"] = observation
                break
                
            # Continue reasoning with new information
            continue_prompt = f"""
            Previous context:
            {current_context}
            Observation: {observation}
            
            Based on this observation, continue your reasoning:
            Thought: [What should you do next?]
            Action: [Next action or "draft_response" to finish]
            """
            
            messages = [HumanMessage(content=continue_prompt)]
            response = self.llm.invoke(messages)
            current_context = response.content
        
        # If no response was drafted, create a final one
        if not state["response_draft"]:
            state["response_draft"] = self._generate_final_response(state)
            
        return state
    
    def _execute_action(self, action: str, state: EmailState) -> str:
        """Execute a tool action and return the observation"""
        action = action.strip()
        
        if "draft_response" in action.lower():
            return self._generate_final_response(state)
        
        # Parse tool calls
        tool_patterns = {
            r'read_calendar\((\d*)\)': lambda m: self.tools.read_calendar(int(m.group(1)) if m.group(1) else 7),
            r'lookup_contact\(["\']([^"\']+)["\']\)': lambda m: self.tools.lookup_contact(m.group(1)),
            r'get_project_status\(["\']([^"\']+)["\']\)': lambda m: self.tools.get_project_status(m.group(1)),
            r'get_project_status\(\)': lambda m: self.tools.get_project_status(),
            r'check_availability\(["\']([^"\']+)["\']\)': lambda m: self.tools.check_availability(m.group(1)),
            r'get_company_info\(["\']([^"\']+)["\']\)': lambda m: self.tools.get_company_info(m.group(1)),
            r'get_company_info\(\)': lambda m: self.tools.get_company_info()
        }
        
        for pattern, func in tool_patterns.items():
            match = re.search(pattern, action)
            if match:
                try:
                    result = func(match)
                    tool_name = pattern.split('\\(')[0].replace('r\'', '')
                    if tool_name not in state["tools_used"]:
                        state["tools_used"].append(tool_name)
                    return result
                except Exception as e:
                    return f"Error executing tool: {str(e)}"
        
        return f"Unknown action: {action}"
    
    def _generate_final_response(self, state: EmailState) -> str:
        """Generate the final email response"""
        context_info = ""
        if state["tools_used"]:
            context_info = f"Tools used: {', '.join(state['tools_used'])}\n"
            
        response_prompt = f"""
        Generate a professional, helpful email response based on the following:
        
        Original Email:
        From: {state["sender"]}
        Subject: {state["subject"]}
        Content: {state["email_content"]}
        
        {context_info}
        
        Write a concise, professional response that addresses the sender's needs.
        Do not include subject line or email headers, just the body text.
        """
        
        messages = [HumanMessage(content=response_prompt)]
        response = self.llm.invoke(messages)
        return response.content.strip()

    def create_workflow(self) -> StateGraph:
        """Create the enhanced LangGraph workflow"""
        workflow = StateGraph(EmailState)
        
        # Add nodes
        workflow.add_node("triage", self.triage_node)
        workflow.add_node("react_agent", self.react_agent_node)
        
        # Define edges
        workflow.set_entry_point("triage")
        
        def should_respond(state: EmailState) -> str:
            if state["triage_decision"] == "respond":
                return "react_agent"
            return END
            
        workflow.add_conditional_edges(
            "triage",
            should_respond,
            {
                "react_agent": "react_agent",
                END: END
            }
        )
        
        workflow.add_edge("react_agent", END)
        
        return workflow.compile()

    def process_email(self, email_content: str, sender: str, subject: str) -> EmailState:
        """Process a single email through the enhanced workflow"""
        initial_state = EmailState(
            email_content=email_content,
            sender=sender,
            subject=subject,
            triage_decision="",
            reasoning="",
            tools_used=[],
            response_draft="",
            react_steps=[]
        )
        
        workflow = self.create_workflow()
        result = workflow.invoke(initial_state)
        return result