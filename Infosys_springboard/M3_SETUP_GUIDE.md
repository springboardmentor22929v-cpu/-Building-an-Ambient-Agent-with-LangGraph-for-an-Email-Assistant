# 🚀 Milestone 3: HITL + Agent Inbox - Complete Setup Guide

## 🎯 What You're Building

Milestone 3 adds **Human-in-the-Loop (HITL)** with:
- ✅ Interrupts for dangerous tools (send_email, schedule_meeting)
- ✅ Agent Inbox UI for approvals
- ✅ State persistence across interrupts
- ✅ Memory of human decisions

---

## 📋 Prerequisites

Make sure you completed:
- ✅ Milestone 1 (Triage working)
- ✅ Milestone 2 (LLM judge working)
- ✅ LangSmith tracing setup (optional but helpful)

---

## 📁 Files You Need

### ✅ Keep from M1/M2:
- `triage.py`
- `m2_evaluation_dataset.json`
- `.env`

### ✅ M3 Core Files (you have these):
- `graph.py` - Your HITL graph with interrupts
- `m2_tools.py` - Tool implementations
- `m2_tools_langgraph.py` - LangChain wrapped tools

### ✅ NEW Files (download from me):
- `langgraph.json` - Studio configuration
- `m3_test_hitl.py` - Test HITL flow
- `m3_evaluation.py` - Full M3 evaluation
- `M3_SETUP_GUIDE.md` - This file

---

## 🔧 Setup Steps

### **STEP 1: Install LangGraph CLI**

```bash
pip install langgraph-cli
```

Or with conda:

```bash
pip install langgraph-cli --break-system-packages
```

**Verify installation:**

```bash
langgraph --version
```

Should show: `langgraph, version 0.x.x`

---

### **STEP 2: Create langgraph.json**

This file tells LangGraph Studio where your graph is.

**Create `langgraph.json` in your project root:**

```json
{
  "dependencies": ["."],
  "graphs": {
    "email_agent": "./graph.py:app"
  },
  "env": ".env"
}
```

**File structure should be:**

```
your_project/
├── .env
├── langgraph.json          ← NEW
├── graph.py
├── triage.py
├── m2_tools.py
├── m2_tools_langgraph.py
├── m2_evaluation_dataset.json
├── m3_test_hitl.py         ← NEW
└── m3_evaluation.py        ← NEW
```

---

### **STEP 3: Test HITL in Console (No UI)**

Before using Studio, test that interrupts work:

```bash
python m3_test_hitl.py
```

**Expected output:**

```
🧪 MILESTONE 3: TESTING HITL FLOW
================================================================================

📧 Test Email:
From: Project Guide <guide@college.edu>
Subject: Project Review Meeting
...

1️⃣ RUNNING AGENT (will interrupt for approval)...
--------------------------------------------------------------------------------
🔥 TRIAGE NODE EXECUTED
⛔ INTERRUPTING FOR HUMAN APPROVAL

⛔ INTERRUPT TRIGGERED!
   Message: Approval required to execute dangerous tool: schedule_meeting

✅ This is CORRECT behavior for Milestone 3!

2️⃣ CHECKING INTERRUPTED STATE...
--------------------------------------------------------------------------------
📊 Current State:
   Next node: ('human_decision',)
   State values: {...}

3️⃣ SIMULATING HUMAN APPROVAL...
--------------------------------------------------------------------------------
✅ Human approved the action

4️⃣ RESUMING EXECUTION...
--------------------------------------------------------------------------------
🛠️ TOOL NODE EXECUTED
🗓️ Checking calendar for Friday at 3 PM
📅 Scheduling meeting with Project Guide on Friday at 3 PM
✉️ Drafting email reply

✅ EXECUTION COMPLETED!

🎉 MILESTONE 3 HITL TEST COMPLETE!
================================================================================
✅ Successfully demonstrated:
   1. Interrupt on dangerous tool
   2. State preservation
   3. Human approval
   4. Resume execution
```

**If you see this → HITL works! ✅ Proceed to Studio.**

---

### **STEP 4: Launch LangGraph Studio**

**In your project directory, run:**

```bash
langgraph studio
```

**What happens:**

1. Studio starts a local server
2. Opens browser automatically (or shows URL)
3. URL usually: `http://localhost:3000`

**You'll see:**

```
🚀 LangGraph Studio
   Project: email_agent
   Graph: email_agent (from graph.py)
   
   Studio running at: http://localhost:3000
```

---

### **STEP 5: Use Agent Inbox in Studio**

**In the Studio UI:**

1. **Select your graph:** "email_agent"

2. **Create a new thread** (click "+ New Thread")

3. **Input your test email:**

```json
{
  "email": "From: guide@college.edu\nSubject: Meeting\n\nCan we meet Friday at 3 PM?"
}
```

4. **Click "Run"**

5. **Watch the graph execute:**
   - Triage node runs
   - HITL checkpoint triggers
   - **Graph PAUSES** ⏸️

6. **Agent Inbox appears!** 📥

You'll see:
```
⏸️ Waiting for Human Input

Tool: schedule_meeting
Action: awaiting_human_approval

[Approve] [Deny] [Edit]
```

7. **Click "Approve"**

8. **Graph resumes:**
   - Human decision node runs
   - Tool node executes
   - Completion!

---

## 🎨 Understanding the Agent Inbox UI

### **Visual Flow:**

```
┌─────────────────────────────────────┐
│  LangGraph Studio                   │
├─────────────────────────────────────┤
│  Thread: test_hitl_001              │
│                                      │
│  ┌────────────────────────────────┐ │
│  │ Triage Node         ✅         │ │
│  └────────────────────────────────┘ │
│           ↓                          │
│  ┌────────────────────────────────┐ │
│  │ HITL Checkpoint     ⏸️         │ │
│  └────────────────────────────────┘ │
│                                      │
│  📥 AGENT INBOX                     │
│  ┌────────────────────────────────┐ │
│  │ Approval Required               │ │
│  │                                  │ │
│  │ Tool: schedule_meeting          │ │
│  │ Message: Requires approval      │ │
│  │                                  │ │
│  │ [Approve] [Deny] [Edit]        │ │
│  └────────────────────────────────┘ │
│                                      │
│  (After approval)                   │
│           ↓                          │
│  ┌────────────────────────────────┐ │
│  │ Human Decision      ✅         │ │
│  └────────────────────────────────┘ │
│           ↓                          │
│  ┌────────────────────────────────┐ │
│  │ Tool Node           ✅         │ │
│  └────────────────────────────────┘ │
└─────────────────────────────────────┘
```

### **Features in Inbox:**

- **Approve**: Continue with the action
- **Deny**: Stop execution
- **Edit**: Modify the action before executing
- **View State**: See current state values
- **View Messages**: See conversation history

---

## 🧪 Running M3 Evaluation

After testing in Studio, run the full evaluation:

```bash
python m3_evaluation.py
```

**What it does:**

1. Runs all test emails
2. Auto-approves `respond_act` emails
3. Auto-denies others
4. Tracks interrupt statistics
5. Saves results to `m3_hitl_evaluation_results.json`

**Expected output:**

```
🧪 MILESTONE 3: HITL EVALUATION
================================================================================

[1/10] Testing: respond_01
📧 Subject: Project Review Meeting
🎯 Expected: respond_act
🤖 Running agent...
⛔ INTERRUPT: Requires human approval
✅ Auto-approving (expected respond_act)
🧑‍⚖️ Human decision set: approve
▶️  Resuming execution...
🛠️ TOOL NODE EXECUTED
✅ Execution completed after approval

💾 Progress saved (1/10)

...

🎉 MILESTONE 3 EVALUATION COMPLETE!
================================================================================

📊 HITL STATISTICS:
   Total samples: 10
   Interrupts triggered: 3
   Human approvals: 3
   Human denials: 0

📊 TRIAGE ACCURACY:
   Correct: 9/10
   Accuracy: 90.00%

🎯 MILESTONE 3 SUCCESS CRITERIA:
   ✅ HITL interrupts working: True
   ✅ State preserved across interrupts: True
   ✅ Human decisions processed: True
   ✅ Triage accuracy >80%: PASS
```

---

## 📊 Understanding the Results

### **m3_hitl_evaluation_results.json:**

```json
{
  "total_samples": 10,
  "completed": 10,
  "interrupts_count": 3,
  "approvals_count": 3,
  "denials_count": 0,
  "results": [
    {
      "id": "respond_01",
      "subject": "Project Review Meeting",
      "expected_action": "respond_act",
      "triage_decision": "respond_act",
      "interrupted": true,
      "human_decision": "approve",
      "tool_result": "Meeting scheduled..."
    }
  ]
}
```

---

## 🎯 Milestone 3 Success Criteria

Your project passes M3 if:

- ✅ **Interrupts work**: Dangerous tools trigger interrupts
- ✅ **State preserved**: Agent resumes from exact point
- ✅ **Human decisions processed**: Approve/deny handled correctly
- ✅ **Inbox UI works**: Can approve/deny in Studio
- ✅ **Triage accuracy >80%**: Still classifying correctly

---

## 🐛 Troubleshooting

### **Issue 1: "langgraph: command not found"**

**Fix:**
```bash
pip install langgraph-cli
```

Check installation:
```bash
which langgraph
```

---

### **Issue 2: Studio won't start**

**Check:**
1. Is port 3000 in use?
2. Try different port: `langgraph studio --port 3001`
3. Check `langgraph.json` exists

---

### **Issue 3: Graph not showing in Studio**

**Fix:**
1. Check `langgraph.json` has correct path
2. Make sure `graph.py` has `app = builder.compile(...)`
3. Restart Studio

---

### **Issue 4: Interrupts not triggering**

**Check:**
1. Is tool in `DANGEROUS_TOOLS` set?
2. Does `hitl_checkpoint_node` raise `Interrupt()`?
3. Is email classified as `respond_act`?

**Debug:**
```bash
python m3_test_hitl.py
```

Should show interrupt in console.

---

### **Issue 5: Inbox doesn't appear**

**Check:**
1. Using LangGraph Studio (not just Python script)
2. Interrupt actually triggered (check logs)
3. Thread has correct configuration

---

## 📈 What Your Sir Will See

Demo this to your sir:

### **1. Console Test:**
```bash
python m3_test_hitl.py
```
Show interrupt → approval → resume flow

### **2. Studio UI:**
```bash
langgraph studio
```
Show visual graph, agent inbox, approve/deny buttons

### **3. Evaluation Results:**
```bash
python m3_evaluation.py
```
Show metrics: interrupts, approvals, accuracy

### **4. LangSmith Traces:**
Open LangSmith → Show interrupted runs with state

---

## 🎓 Key Concepts Demonstrated

### **1. Human-in-the-Loop (HITL)**
- Agent asks permission for critical actions
- Human approves/denies
- Safe autonomous operation

### **2. State Management**
- Graph pauses mid-execution
- State preserved perfectly
- Resumes from exact point

### **3. Dangerous Tools**
- Identified critical operations
- Require approval
- Safe vs unsafe distinction

### **4. Agent Inbox**
- Visual UI for approvals
- Better UX than console
- Professional interface

---

## 🚀 Next Steps (Milestone 4)

After M3, you'll add:
- ✅ Persistent memory (SQLite)
- ✅ Learning from corrections
- ✅ Gmail API integration
- ✅ Real-world deployment

---

## 💡 Quick Commands Cheat Sheet

```bash
# Test HITL in console
python m3_test_hitl.py

# Launch Studio UI
langgraph studio

# Run full evaluation
python m3_evaluation.py

# Check Studio is running
curl http://localhost:3000

# Stop Studio
Ctrl+C in terminal
```

---

## ✅ Final Checklist

Before showing to your sir:

- [ ] `langgraph-cli` installed
- [ ] `langgraph.json` created
- [ ] `m3_test_hitl.py` runs successfully
- [ ] LangGraph Studio launches
- [ ] Agent Inbox appears on interrupt
- [ ] Can approve/deny in UI
- [ ] `m3_evaluation.py` runs and passes
- [ ] Results saved to JSON
- [ ] Understand the flow

---

**Ready?** Start with: `python m3_test_hitl.py` to verify HITL works! 🚀

Then launch Studio: `langgraph studio` to see the inbox UI!
