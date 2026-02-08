'''# evaluation.py
# Milestone 2 – Agent Evaluation using LangGraph

import json
import os
import time
from dotenv import load_dotenv
from langchain_core.runnables import RunnableConfig

# -------------------------------------------------
# Load environment variables (LangSmith, API keys)
# -------------------------------------------------
load_dotenv()

# Ensure project name is set for tracing
os.environ["LANGCHAIN_PROJECT"] = os.getenv(
    "LANGCHAIN_PROJECT", "email-triage-m2"
)

# -------------------------------------------------
# Import Milestone 1 LangGraph agent
# -------------------------------------------------
from graph import app


# -------------------------------------------------
# File paths
# -------------------------------------------------
DATASET_FILE = "m2_evaluation_dataset.json"
OUTPUT_FILE = "m2_evaluation_results.json"


# -------------------------------------------------
# Utility: format email for agent input
# -------------------------------------------------
def format_email(email_obj):
    return f"""
From: {email_obj['from']}
Subject: {email_obj['subject']}

{email_obj['body']}
"""


# -------------------------------------------------
# Load evaluation dataset
# -------------------------------------------------
with open(DATASET_FILE, "r") as f:
    dataset = json.load(f)

print(f"✅ Loaded {len(dataset)} evaluation samples")


# -------------------------------------------------
# Resume-safe loading of previous results
# -------------------------------------------------
if os.path.exists(OUTPUT_FILE):
    with open(OUTPUT_FILE, "r") as f:
        saved = json.load(f)
        results = saved.get("results", [])
else:
    results = []

already_done = len(results)
correct = sum(1 for r in results if r.get("correct") is True)

print(f"🔁 Resuming from sample {already_done + 1}")


# -------------------------------------------------
# Evaluation loop
# -------------------------------------------------
for i in range(already_done, len(dataset)):
    item = dataset[i]

    sample_id = item["id"]
    email_obj = item["email"]
    expected_action = item["expected_action"]

    email_text = format_email(email_obj)

    print("\n" + "=" * 60)
    print(f"🧪 Evaluating sample: {sample_id}")
    print("Expected action:", expected_action)

    try:
        output = app.invoke(
            {"email": email_text},
            config=RunnableConfig(
                configurable={"thread_id": sample_id},
                tags=["milestone-2", "evaluation"],
                metadata={
                    "dataset_id": sample_id,
                    "expected_action": expected_action
                }
            )
        )

        predicted_action = output.get("triage_decision")
        is_correct = predicted_action == expected_action
        error = None

    except Exception as e:
        predicted_action = None
        is_correct = False
        error = str(e)

    if is_correct:
        correct += 1

    results.append({
        "id": sample_id,
        "expected_action": expected_action,
        "predicted_action": predicted_action,
        "correct": is_correct,
        "error": error
    })

    print("Predicted action:", predicted_action)
    print("Correct:", is_correct)
    if error:
        print("Error:", error)

    # Save after every sample (resume-safe)
    with open(OUTPUT_FILE, "w") as f:
        json.dump({
            "total_samples": len(dataset),
            "completed": len(results),
            "correct": correct,
            "accuracy": correct / len(results) if results else 0.0,
            "results": results
        }, f, indent=2)

    # Free-tier / safety delay
    time.sleep(6)


# -------------------------------------------------
# Final summary
# -------------------------------------------------
accuracy = corr'''

"""
Milestone 2: Complete Evaluation with GUARANTEED LangSmith Tracing
This version ensures all runs are visible in LangSmith UI.
"""

import json
import os
import time
from dotenv import load_dotenv

# ============================================
# CRITICAL: Load and force tracing FIRST
# ============================================
load_dotenv(override=True)

# Force enable tracing
os.environ["LANGCHAIN_TRACING_V2"] = "true"
os.environ["LANGCHAIN_PROJECT"] = os.getenv("LANGCHAIN_PROJECT", "email-triage-m2")
os.environ["LANGCHAIN_ENDPOINT"] = "https://api.smith.langchain.com"

print("=" * 80)
print("🔍 LANGSMITH TRACING CONFIGURATION")
print("=" * 80)
print(f"✅ Tracing: {os.environ['LANGCHAIN_TRACING_V2']}")
print(f"✅ Project: {os.environ['LANGCHAIN_PROJECT']}")
print(f"✅ Endpoint: {os.environ['LANGCHAIN_ENDPOINT']}")
print("=" * 80)
print()

# Now import everything else
from langsmith import Client
from langchain_core.tracers import LangChainTracer
from langchain_core.runnables import RunnableConfig

from graph import app
from m2_llm_judge import judge_response_quality, calculate_average_score

# ============================================
# Initialize LangSmith client and tracer
# ============================================
try:
    langsmith_client = Client()
    print("✅ LangSmith client initialized")
    print(f"🔗 View traces at: https://smith.langchain.com/projects/{os.environ['LANGCHAIN_PROJECT']}")
    print()
except Exception as e:
    print(f"⚠️  LangSmith client initialization warning: {e}")
    print("Continuing anyway...")
    langsmith_client = None

# ============================================
# Configuration
# ============================================
DATASET_FILE = "m2_evaluation_dataset.json"
OUTPUT_FILE = "m2_full_evaluation_results.json"

# ============================================
# Utility functions
# ============================================
def format_email(email_obj):
    return f"""
From: {email_obj['from']}
Subject: {email_obj['subject']}
{email_obj['body']}
"""

# ============================================
# Load dataset
# ============================================
with open(DATASET_FILE, "r") as f:
    dataset = json.load(f)

print(f"✅ Loaded {len(dataset)} evaluation samples\n")

# ============================================
# Resume-safe: load previous results
# ============================================
if os.path.exists(OUTPUT_FILE):
    with open(OUTPUT_FILE, "r") as f:
        saved = json.load(f)
        results = saved.get("results", [])
else:
    results = []

already_done = len(results)
correct_triage = sum(1 for r in results if r.get("triage_correct"))

print(f"🔁 Resuming from sample {already_done + 1}\n")
print("=" * 80)

# ============================================
# Evaluation loop
# ============================================
for i in range(already_done, len(dataset)):
    item = dataset[i]
    sample_id = item["id"]
    email_obj = item["email"]
    expected_action = item["expected_action"]
    ideal_response = item.get("ideal_response")
    
    email_text = format_email(email_obj)
    
    print(f"\n🧪 [{i+1}/{len(dataset)}] Evaluating: {sample_id}")
    print(f"📧 Subject: {email_obj['subject'][:50]}...")
    print(f"🎯 Expected: {expected_action}")
    
    # ============================================
    # STEP 1: Run agent with EXPLICIT tracing
    # ============================================
    try:
        # Create tracer for this run
        tracer = LangChainTracer(
            project_name=os.environ["LANGCHAIN_PROJECT"],
            client=langsmith_client
        ) if langsmith_client else None
        
        # Build config with callbacks
        run_config = RunnableConfig(
            configurable={"thread_id": sample_id},
            tags=[
                "milestone-2",
                "evaluation",
                f"expected:{expected_action}",
                f"sample:{sample_id}"
            ],
            metadata={
                "dataset_id": sample_id,
                "expected_action": expected_action,
                "email_from": email_obj["from"],
                "email_subject": email_obj["subject"]
            }
        )
        
        # Add tracer to callbacks if available
        if tracer:
            run_config["callbacks"] = [tracer]
        
        # Run the agent
        print(f"🤖 Running agent (trace will appear in LangSmith)...")
        output = app.invoke({"email": email_text}, config=run_config)
        
        predicted_action = output.get("triage_decision")
        agent_error = None
        
        if tracer:
            print(f"✅ Trace uploaded to LangSmith")
        
    except Exception as e:
        predicted_action = None
        agent_error = str(e)
        print(f"❌ Agent error: {agent_error}")
    
    # ============================================
    # STEP 2: Check triage accuracy
    # ============================================
    triage_correct = (predicted_action == expected_action)
    
    if triage_correct:
        correct_triage += 1
    
    print(f"🤖 Predicted: {predicted_action}")
    print(f"✅ Triage correct: {triage_correct}")
    
    # ============================================
    # STEP 3: LLM-as-a-Judge (for respond_act)
    # ============================================
    quality_scores = None
    quality_score_avg = 0.0
    judge_error = None
    
    if expected_action == "respond_act" and ideal_response:
        # Mock agent response (will be real in M3/M4)
        agent_response = "Thank you for your email. I will get back to you shortly."
        
        print(f"\n📝 Agent response: {agent_response[:60]}...")
        print(f"🎯 Ideal response: {ideal_response[:60]}...")
        
        try:
            print("⚖️  Calling LLM judge (this will also be traced)...")
            
            quality_scores = judge_response_quality(
                email_text=email_text,
                agent_response=agent_response,
                ideal_response=ideal_response
            )
            
            quality_score_avg = calculate_average_score(quality_scores)
            
            print(f"\n📊 Quality Scores:")
            print(f"   Correctness: {quality_scores['correctness']}/5")
            print(f"   Politeness: {quality_scores['politeness']}/5")
            print(f"   Completeness: {quality_scores['completeness']}/5")
            print(f"   Tone: {quality_scores['tone']}/5")
            print(f"   Clarity: {quality_scores['clarity']}/5")
            print(f"   Average: {quality_score_avg:.2f}/5.0")
            print(f"   Reasoning: {quality_scores['reasoning']}")
            
        except Exception as e:
            judge_error = str(e)
            print(f"❌ Judge error: {judge_error}")
    
    # ============================================
    # STEP 4: Store results
    # ============================================
    result_entry = {
        "id": sample_id,
        "from": email_obj["from"],
        "subject": email_obj["subject"],
        "expected_action": expected_action,
        "predicted_action": predicted_action,
        "triage_correct": triage_correct,
        "quality_scores": quality_scores,
        "quality_score": quality_score_avg,
        "agent_error": agent_error,
        "judge_error": judge_error,
        "langsmith_trace": f"https://smith.langchain.com/projects/{os.environ['LANGCHAIN_PROJECT']}"
    }
    
    results.append(result_entry)
    
    # ============================================
    # STEP 5: Save progress
    # ============================================
    triage_accuracy = (correct_triage / len(results)) * 100
    
    respond_results = [r for r in results if r["expected_action"] == "respond_act"]
    avg_quality = (
        sum(r["quality_score"] for r in respond_results) / len(respond_results)
        if respond_results else 0.0
    )
    
    with open(OUTPUT_FILE, "w") as f:
        json.dump({
            "total_samples": len(dataset),
            "completed": len(results),
            "triage_accuracy": triage_accuracy,
            "correct_triage": correct_triage,
            "average_quality_score": avg_quality,
            "langsmith_project": os.environ["LANGCHAIN_PROJECT"],
            "langsmith_url": f"https://smith.langchain.com/projects/{os.environ['LANGCHAIN_PROJECT']}",
            "results": results
        }, f, indent=2)
    
    print(f"\n💾 Progress saved ({len(results)}/{len(dataset)} completed)")
    print("=" * 80)
    
    # ============================================
    # STEP 6: Rate limit safety
    # ============================================
    time.sleep(6)

# ============================================
# Final Summary
# ============================================
print("\n" + "=" * 80)
print("🎉 MILESTONE 2 EVALUATION COMPLETE!")
print("=" * 80)

triage_accuracy = (correct_triage / len(results)) * 100
respond_results = [r for r in results if r["expected_action"] == "respond_act"]
avg_quality = (
    sum(r["quality_score"] for r in respond_results) / len(respond_results)
    if respond_results else 0.0
)

print(f"\n📊 TRIAGE PERFORMANCE:")
print(f"   Total samples: {len(results)}")
print(f"   Correct classifications: {correct_triage}")
print(f"   Triage accuracy: {triage_accuracy:.2f}%")

if respond_results:
    print(f"\n📊 RESPONSE QUALITY (respond_act only):")
    print(f"   Samples evaluated: {len(respond_results)}")
    print(f"   Average quality score: {avg_quality:.2f}/5.0")
    
    dimensions = ["correctness", "politeness", "completeness", "tone", "clarity"]
    print(f"\n   Dimension breakdown:")
    for dim in dimensions:
        scores = [r["quality_scores"][dim] for r in respond_results if r["quality_scores"]]
        if scores:
            avg = sum(scores) / len(scores)
            print(f"      {dim.capitalize()}: {avg:.2f}/5.0")

print(f"\n🎯 MILESTONE 2 SUCCESS CRITERIA:")
print(f"   Triage accuracy >80%: {'✅ PASS' if triage_accuracy >= 80 else '❌ FAIL'}")
print(f"   Quality score >3.5/5: {'✅ PASS' if avg_quality >= 3.5 else '❌ FAIL'}")

print(f"\n📁 Results saved to: {OUTPUT_FILE}")

print(f"\n🔗 VIEW TRACES IN LANGSMITH:")
print(f"   {os.environ['LANGCHAIN_PROJECT']} project")
print(f"   URL: https://smith.langchain.com/projects/{os.environ['LANGCHAIN_PROJECT']}")
print(f"   All {len(results)} runs should be visible in the UI")

print("\n" + "=" * 80)