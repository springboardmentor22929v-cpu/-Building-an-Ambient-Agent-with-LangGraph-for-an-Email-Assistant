from state import AgentState
from memory.AgentMemory import AgentMemory


def load_memory_node(state: AgentState) -> AgentState:
    print("\n🧠 Loading Memory")

    memory = AgentMemory()

    sender_email = state.get("email_from")

    # Get full structured memory context
    full_context = memory.get_full_context(sender_email)

    return {
        **state,
        "user_preferences": full_context
    }
