"""
Milestone 2: LLM-as-a-Judge Evaluator
Evaluates agent response quality using Gemini as a judge.
"""

import os
from dotenv import load_dotenv
from google import genai

load_dotenv()

# Create Gemini client
api_key = os.getenv("GOOGLE_API_KEY")
client = genai.Client(api_key=api_key)


def judge_response_quality(
    email_text: str,
    agent_response: str,
    ideal_response: str = None
) -> dict:
    """
    Use Gemini to judge the quality of an agent's response.
    
    Args:
        email_text: The original email
        agent_response: What the agent generated
        ideal_response: The expected/ideal response (optional)
    
    Returns:
        Dictionary with scores for different quality dimensions
    """
    
    # Build the judging prompt
    if ideal_response:
        prompt = f"""
You are an expert email evaluator. Evaluate the quality of the agent's email response.

ORIGINAL EMAIL:
\"\"\"
{email_text}
\"\"\"

AGENT'S RESPONSE:
\"\"\"
{agent_response}
\"\"\"

IDEAL RESPONSE (for reference):
\"\"\"
{ideal_response}
\"\"\"

Evaluate the agent's response on these dimensions (score 1-5, where 5 is best):

1. CORRECTNESS: Does it address the email properly and provide correct information?
2. POLITENESS: Is the tone professional and courteous?
3. COMPLETENESS: Does it answer all questions and address all points?
4. TONE: Is the formality level appropriate for the context?
5. CLARITY: Is the response clear and well-written?

Provide your evaluation in this EXACT format (one score per line):
CORRECTNESS: [score]
POLITENESS: [score]
COMPLETENESS: [score]
TONE: [score]
CLARITY: [score]
OVERALL: [score]
REASONING: [one sentence explanation]
"""
    else:
        prompt = f"""
You are an expert email evaluator. Evaluate the quality of the agent's email response.

ORIGINAL EMAIL:
\"\"\"
{email_text}
\"\"\"

AGENT'S RESPONSE:
\"\"\"
{agent_response}
\"\"\"

Evaluate the agent's response on these dimensions (score 1-5, where 5 is best):

1. CORRECTNESS: Does it address the email properly?
2. POLITENESS: Is the tone professional and courteous?
3. COMPLETENESS: Does it answer the questions asked?
4. TONE: Is the formality level appropriate?
5. CLARITY: Is the response clear and well-written?

Provide your evaluation in this EXACT format (one score per line):
CORRECTNESS: [score]
POLITENESS: [score]
COMPLETENESS: [score]
TONE: [score]
CLARITY: [score]
OVERALL: [score]
REASONING: [one sentence explanation]
"""
    
    try:
        # Call Gemini to judge
        response = client.models.generate_content(
            model="gemini-flash-latest",
            contents=prompt
        )
        
        # Parse the response
        judge_text = response.text.strip()
        scores = parse_judge_output(judge_text)
        
        return scores
    
    except Exception as e:
        print(f"❌ Error in LLM judge: {e}")
        return {
            "correctness": 0,
            "politeness": 0,
            "completeness": 0,
            "tone": 0,
            "clarity": 0,
            "overall": 0,
            "reasoning": f"Error: {str(e)}",
            "raw_output": ""
        }


def parse_judge_output(judge_text: str) -> dict:
    """
    Parse the judge's output into structured scores.
    
    Args:
        judge_text: Raw text from Gemini judge
    
    Returns:
        Dictionary with parsed scores
    """
    scores = {
        "correctness": 0,
        "politeness": 0,
        "completeness": 0,
        "tone": 0,
        "clarity": 0,
        "overall": 0,
        "reasoning": "",
        "raw_output": judge_text
    }
    
    lines = judge_text.split('\n')
    
    for line in lines:
        line = line.strip()
        
        if line.startswith("CORRECTNESS:"):
            try:
                scores["correctness"] = int(line.split(":")[1].strip().split()[0])
            except:
                pass
        
        elif line.startswith("POLITENESS:"):
            try:
                scores["politeness"] = int(line.split(":")[1].strip().split()[0])
            except:
                pass
        
        elif line.startswith("COMPLETENESS:"):
            try:
                scores["completeness"] = int(line.split(":")[1].strip().split()[0])
            except:
                pass
        
        elif line.startswith("TONE:"):
            try:
                scores["tone"] = int(line.split(":")[1].strip().split()[0])
            except:
                pass
        
        elif line.startswith("CLARITY:"):
            try:
                scores["clarity"] = int(line.split(":")[1].strip().split()[0])
            except:
                pass
        
        elif line.startswith("OVERALL:"):
            try:
                scores["overall"] = int(line.split(":")[1].strip().split()[0])
            except:
                pass
        
        elif line.startswith("REASONING:"):
            scores["reasoning"] = line.split(":", 1)[1].strip()
    
    return scores


def calculate_average_score(scores: dict) -> float:
    """Calculate average score from quality dimensions"""
    dimensions = ["correctness", "politeness", "completeness", "tone", "clarity"]
    total = sum(scores.get(dim, 0) for dim in dimensions)
    return total / len(dimensions) if total > 0 else 0.0


# Test function
if __name__ == "__main__":
    # Test the judge
    test_email = """
From: Project Guide <guide@college.edu>
Subject: Project Review Meeting

Hi Abinaya,

Can we schedule the project review meeting for Friday at 3 PM?

Please confirm.

Regards,
Guide
"""
    
    test_agent_response = """
Hello Sir,

Yes, Friday at 3 PM works perfectly for me. I will be available for the project review meeting.

Regards,
Abinaya
"""
    
    test_ideal = """
Hello Sir,

Yes, Friday at 3 PM works for me. I will be available for the project review meeting.

Regards,
Abinaya
"""
    
    print("🧪 Testing LLM Judge...\n")
    
    scores = judge_response_quality(
        email_text=test_email,
        agent_response=test_agent_response,
        ideal_response=test_ideal
    )
    
    print("📊 JUDGE SCORES:")
    print(f"  Correctness: {scores['correctness']}/5")
    print(f"  Politeness: {scores['politeness']}/5")
    print(f"  Completeness: {scores['completeness']}/5")
    print(f"  Tone: {scores['tone']}/5")
    print(f"  Clarity: {scores['clarity']}/5")
    print(f"  Overall: {scores['overall']}/5")
    print(f"\n💭 Reasoning: {scores['reasoning']}")
    print(f"\n✅ Average Score: {calculate_average_score(scores):.2f}/5.0")