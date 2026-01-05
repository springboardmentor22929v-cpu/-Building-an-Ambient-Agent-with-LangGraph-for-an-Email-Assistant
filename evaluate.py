from react_agent import process_email
from test_data import GOLDEN_TEST_SET
import json
from datetime import datetime
import os

def evaluate_triage_accuracy():
    """Evaluate agent triage accuracy against golden test set"""
    
    results = []
    correct_predictions = 0
    total_predictions = len(GOLDEN_TEST_SET)
    
    print(f"Evaluating triage accuracy on {total_predictions} test cases...")
    print("=" * 60)
    
    for i, test_case in enumerate(GOLDEN_TEST_SET, 1):
        print(f"Test {i}/{total_predictions}: {test_case['subject'][:50]}...")
        
        try:
            # Process email through agent
            result = process_email(
                email_subject=test_case['subject'],
                email_sender=test_case['sender'],
                email_content=test_case['content']
            )
            
            predicted = result['triage_decision']
            expected = test_case['expected_triage']
            is_correct = predicted == expected
            
            if is_correct:
                correct_predictions += 1
                status = "✓ CORRECT"
            else:
                status = "✗ INCORRECT"
            
            print(f"  Expected: {expected} | Predicted: {predicted} | {status}")
            
            # Store detailed results
            results.append({
                "test_id": i,
                "subject": test_case['subject'],
                "sender": test_case['sender'],
                "expected": expected,
                "predicted": predicted,
                "correct": is_correct,
                "reasoning": result['reasoning'],
                "tools_used": result['tools_used']
            })
            
        except Exception as e:
            print(f"  ERROR: {str(e)}")
            results.append({
                "test_id": i,
                "subject": test_case['subject'],
                "expected": test_case['expected_triage'],
                "predicted": "ERROR",
                "correct": False,
                "error": str(e)
            })
    
    # Calculate metrics
    accuracy = (correct_predictions / total_predictions) * 100
    
    print("\n" + "=" * 60)
    print(f"EVALUATION RESULTS:")
    print(f"Total test cases: {total_predictions}")
    print(f"Correct predictions: {correct_predictions}")
    print(f"Accuracy: {accuracy:.1f}%")
    
    # Success criteria check
    success_threshold = 80.0
    if accuracy >= success_threshold:
        print(f"✓ SUCCESS: Achieved {accuracy:.1f}% accuracy (>= {success_threshold}%)")
    else:
        print(f"✗ FAILED: Only {accuracy:.1f}% accuracy (< {success_threshold}%)")
    
    # Save detailed results
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    results_file = f"evaluation_results_{timestamp}.json"
    
    evaluation_summary = {
        "timestamp": timestamp,
        "total_cases": total_predictions,
        "correct_predictions": correct_predictions,
        "accuracy_percentage": accuracy,
        "success_criteria_met": accuracy >= success_threshold,
        "detailed_results": results
    }
    
    with open(results_file, 'w') as f:
        json.dump(evaluation_summary, f, indent=2)
    
    print(f"\nDetailed results saved to: {results_file}")
    
    # Show breakdown by category
    print("\nBreakdown by expected category:")
    categories = {}
    for result in results:
        expected = result['expected']
        if expected not in categories:
            categories[expected] = {'total': 0, 'correct': 0}
        categories[expected]['total'] += 1
        if result['correct']:
            categories[expected]['correct'] += 1
    
    for category, stats in categories.items():
        cat_accuracy = (stats['correct'] / stats['total']) * 100
        print(f"  {category}: {stats['correct']}/{stats['total']} ({cat_accuracy:.1f}%)")
    
    return accuracy >= success_threshold

def run_single_test():
    """Run a single test case for debugging"""
    test_case = {
        "subject": "Meeting request for next week",
        "sender": "colleague@company.com", 
        "content": "Hi, could we schedule a meeting to discuss the project timeline?"
    }
    
    print("Testing single email:")
    print(f"Subject: {test_case['subject']}")
    print(f"Sender: {test_case['sender']}")
    print(f"Content: {test_case['content']}")
    print("\nProcessing...")
    
    result = process_email(
        email_subject=test_case['subject'],
        email_sender=test_case['sender'],
        email_content=test_case['content']
    )
    
    print(f"\nResults:")
    print(f"Triage Decision: {result['triage_decision']}")
    print(f"Reasoning: {result['reasoning']}")
    print(f"Tools Used: {result['tools_used']}")
    print(f"Response: {result['response_content']}")

if __name__ == "__main__":
    # Check if API keys are set
    if not os.getenv("GOOGLE_API_KEY"):
        print("ERROR: Please set GOOGLE_API_KEY in .env file")
        exit(1)
    
    print("Email Assistant Agent - Milestone 1 Evaluation")
    print("Choose an option:")
    print("1. Run full evaluation (all test cases)")
    print("2. Run single test case")
    
    choice = input("Enter choice (1 or 2): ").strip()
    
    if choice == "1":
        evaluate_triage_accuracy()
    elif choice == "2":
        run_single_test()
    else:
        print("Invalid choice. Running full evaluation...")
        evaluate_triage_accuracy()