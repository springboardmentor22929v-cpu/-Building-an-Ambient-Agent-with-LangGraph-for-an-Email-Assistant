from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
import asyncio
import json
import uuid
from typing import Dict
from datetime import datetime
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv
load_dotenv()

from src.integrations.gmail_auth import authenticate_google_services
from src.tools.google_tools import initialize_tools
from src.agents.email_graph import create_email_agent

app = FastAPI(title="Email Agent HITL Interface")

templates = Jinja2Templates(directory="ui/templates")

# Store workflow states and websocket connections
pending_approvals: Dict[str, dict] = {}
approval_events: Dict[str, asyncio.Event] = {}
approval_decisions: Dict[str, dict] = {}
websocket_connections: list = []

# Initialize agent
agent = None
gmail_service = None
calendar_service = None


@app.on_event("startup")
async def startup_event():
    """Initialize services on startup."""
    global agent, gmail_service, calendar_service
    
    print("\n🚀 Starting Email Agent HITL Server...")
    
    try:
        gmail_service, calendar_service = authenticate_google_services()
        initialize_tools(gmail_service, calendar_service)
        agent = create_email_agent()
        print("✅ Agent initialized successfully")
    except Exception as e:
        print(f"⚠️  Warning: Could not initialize services: {e}")
        print("   You can still test the UI manually")


@app.get("/")
async def get_ui(request: Request):
    """Serve the main HITL interface."""
    return templates.TemplateResponse("index.html", {"request": request})


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket for real-time updates."""
    await websocket.accept()
    websocket_connections.append(websocket)
    
    try:
        # Send any pending approvals to new connection
        for workflow_id, approval in pending_approvals.items():
            await websocket.send_json({
                "type": "approval_request",
                "data": approval
            })
        
        # Keep connection alive and listen for decisions
        while True:
            data = await websocket.receive_text()
            message = json.loads(data)
            
            if message["type"] == "human_decision":
                workflow_id = message["workflow_id"]
                decision = message["decision"]
                edited_content = message.get("edited_content", "")
                
                print(f"\n👤 Human decision received:")
                print(f"   Workflow: {workflow_id}")
                print(f"   Decision: {decision}")
                
                # Store the decision
                approval_decisions[workflow_id] = {
                    "decision": decision,
                    "edited_content": edited_content,
                    "timestamp": datetime.now().isoformat()
                }
                
                # Signal the waiting workflow
                if workflow_id in approval_events:
                    approval_events[workflow_id].set()
                
                # Remove from pending
                if workflow_id in pending_approvals:
                    del pending_approvals[workflow_id]
                
                # Notify all clients
                await broadcast_message({
                    "type": "decision_recorded",
                    "workflow_id": workflow_id,
                    "decision": decision
                })
    
    except WebSocketDisconnect:
        websocket_connections.remove(websocket)
    except Exception as e:
        print(f"WebSocket error: {e}")
        if websocket in websocket_connections:
            websocket_connections.remove(websocket)


async def broadcast_message(message: dict):
    """Send message to all connected clients."""
    disconnected = []
    for ws in websocket_connections:
        try:
            await ws.send_json(message)
        except Exception:
            disconnected.append(ws)
    
    for ws in disconnected:
        websocket_connections.remove(ws)


@app.post("/process-email")
async def process_email(request: Request):
    """
    Process an email through the agent.
    Triggers HITL if needed.
    """
    body = await request.json()
    
    workflow_id = str(uuid.uuid4())[:8]
    
    email_data = {
        "email_id": workflow_id,
        "email_from": body.get("email_from", ""),
        "email_subject": body.get("email_subject", ""),
        "email_body": body.get("email_body", ""),
        "user_preferences": {},
        "workflow_id": workflow_id
    }
    
    print(f"\n📧 Processing email: {email_data['email_subject']}")
    
    # Notify UI that processing started
    await broadcast_message({
        "type": "processing_started",
        "workflow_id": workflow_id,
        "email": {
            "from": email_data["email_from"],
            "subject": email_data["email_subject"]
        }
    })
    
    # Run agent in background
    asyncio.create_task(
        run_agent_workflow(workflow_id, email_data)
    )
    
    return {
        "status": "processing",
        "workflow_id": workflow_id
    }


async def run_agent_workflow(workflow_id: str, email_data: dict):
    """
    Run the agent workflow asynchronously.
    Handles HITL pause/resume.
    """
    try:
        config = {
            "configurable": {
                "thread_id": workflow_id
            }
        }
        
        # Phase 1: Run until HITL checkpoint
        loop = asyncio.get_event_loop()
        result = await loop.run_in_executor(
            None,
            lambda: agent.invoke(email_data, config)
        )
        
        # Notify triage result
        await broadcast_message({
            "type": "triage_complete",
            "workflow_id": workflow_id,
            "decision": result.get("triage_decision", ""),
            "reasoning": result.get("triage_reasoning", "")
        })
        
        # Check if HITL needed
        if result.get("requires_approval"):
            pending_action = result.get("pending_action", {})
            args = pending_action.get("args", {})
            
            # Get draft preview
            draft_preview = ""
            if result.get("messages"):
                msg = result["messages"][0]
                if isinstance(msg, dict):
                    draft_preview = msg.get("content", "")
            
            approval_data = {
                "workflow_id": workflow_id,
                "action_type": pending_action.get("action_type", ""),
                "recipient": args.get("recipient", ""),
                "subject": args.get("subject", ""),
                "body": args.get("body", ""),
                "draft_preview": draft_preview,
                "timestamp": datetime.now().isoformat()
            }
            
            # Store and broadcast
            pending_approvals[workflow_id] = approval_data
            
            # Create event for waiting
            approval_events[workflow_id] = asyncio.Event()
            
            # Send to UI
            await broadcast_message({
                "type": "approval_required",
                "data": approval_data
            })
            
            print(f"\n⏸️  Workflow {workflow_id} paused for approval")
            
            # Wait for human decision (timeout after 10 minutes)
            try:
                await asyncio.wait_for(
                    approval_events[workflow_id].wait(),
                    timeout=600
                )
            except asyncio.TimeoutError:
                print(f"⏰ Workflow {workflow_id} timed out")
                await broadcast_message({
                    "type": "workflow_timeout",
                    "workflow_id": workflow_id
                })
                return
            
            # Get decision
            decision_data = approval_decisions.get(workflow_id, {})
            decision = decision_data.get("decision", "deny")
            edited_content = decision_data.get("edited_content", "")
            
            print(f"\n▶️  Resuming workflow {workflow_id}")
            print(f"   Decision: {decision}")
            
            # Update state
            updated_state = {
                **result,
                "human_decision": decision
            }
            
            if decision == "edit" and edited_content:
                updated_state["human_feedback"] = {
                    "body_content": edited_content
                }
                updated_state["human_decision"] = "edit"
            
            # Resume workflow
            final_result = await loop.run_in_executor(
                None,
                lambda: agent.invoke(updated_state, config)
            )
            
            # Notify completion
            await broadcast_message({
                "type": "workflow_complete",
                "workflow_id": workflow_id,
                "decision": decision,
                "execution_status": final_result.get("execution_status", ""),
                "execution_result": final_result.get("execution_result", "")
            })
            
        else:
            # No approval needed
            await broadcast_message({
                "type": "workflow_complete",
                "workflow_id": workflow_id,
                "decision": "auto_approved",
                "execution_status": "complete"
            })
    
    except Exception as e:
        print(f"❌ Workflow error: {e}")
        import traceback
        traceback.print_exc()
        
        await broadcast_message({
            "type": "workflow_error",
            "workflow_id": workflow_id,
            "error": str(e)
        })


@app.get("/pending-approvals")
async def get_pending_approvals():
    """Get all pending approvals."""
    return {
        "count": len(pending_approvals),
        "approvals": list(pending_approvals.values())
    }


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "agent_ready": agent is not None,
        "gmail_connected": gmail_service is not None,
        "calendar_connected": calendar_service is not None,
        "pending_approvals": len(pending_approvals),
        "connected_clients": len(websocket_connections)
    }