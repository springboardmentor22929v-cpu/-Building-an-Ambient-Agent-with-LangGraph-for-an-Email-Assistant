from triage import triage_email_with_llm
from tools import read_calendar, notify_human, send_response
from memory import init_db, log_interaction


# Dangerous tools require human approval
DANGEROUS_TOOLS = {'send_response'}


def generate_simple_response(email: dict) -> str:
    subject = email.get('subject', 'your message')
    return f"Hi, thanks for your message about \"{subject}\". Could you share a bit more detail so I can help?"


def run_agent_on_email(email: dict, require_human_for_dangerous: bool = True) -> dict:
    # initialize memory DB if needed
    init_db()

    classification, reasoning = triage_email_with_llm(email)
    reasoning_trace = [f"Triage decided: {classification} ({reasoning})"]

    action_result = None
    pending_human = False

    if classification == 'ignore':
        reasoning_trace.append('Action: ignore — no tools invoked')
        action_result = {'action': 'ignore'}
    elif classification == 'notify_human':
        reasoning_trace.append('Action: notify_human — calling notify_human tool')
        action_result = notify_human(email, note='Automated triage: please review.')
    elif classification == 'respond':
        reasoning_trace.append('Action: respond — planning to send a response')
        # decide if sending is dangerous; if so, require HITL
        if require_human_for_dangerous and 'send_response' in DANGEROUS_TOOLS:
            reasoning_trace.append('send_response is considered dangerous — pausing for human approval')
            pending_human = True
            action_result = {'status': 'pending_human', 'action': 'send_response', 'draft': generate_simple_response(email)}
        else:
            response_text = generate_simple_response(email)
            action_result = send_response(email, response_text)
            reasoning_trace.append('send_response executed')

    # Log the triage decision to memory
    log_interaction(email.get('id', ''), classification)

    return {
        'email_id': email.get('id'),
        'classification': classification,
        'triage_reason': reasoning,
        'reasoning_trace': reasoning_trace,
        'action_result': action_result,
        'pending_human': pending_human
    }
