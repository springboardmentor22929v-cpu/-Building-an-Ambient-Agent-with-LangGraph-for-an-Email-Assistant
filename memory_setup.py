from langgraph.checkpoint.sqlite import SqliteSaver

# Persistent memory setup
memory_saver = SqliteSaver("agent_memory.db")
print("Persistent memory initialized!")
