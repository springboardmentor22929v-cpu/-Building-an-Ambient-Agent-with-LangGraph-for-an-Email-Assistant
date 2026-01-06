import json
from typing import List, Dict, Any
from email_agent import EmailAgent

class TriageEvaluator:
    def __init__(self):
        self.agent = EmailAgent()
        self.test_dataset = self._create_golden_dataset()
    
    def _create_golden_dataset(self) -> List[Dict[str, Any]]:
        """Create a golden dataset of emails with expected triage decisions."""
        
        return [
            # IGNORE emails (spam, newsletters, unimportant)
            {
                "content": "CONGRATULATIONS! You've won $1,000,000! Click here now!",
                "sender": "winner@spam.com",
                "subject": "You're a WINNER!!!",
                "expected": "ignore"
            },
            {
                "content": "Weekly newsletter: Top 10 productivity tips for remote workers",
                "sender": "newsletter@productivity.com",
                "subject": "Weekly Productivity Newsletter",
                "expected": "ignore"
            },
            {
                "content": "Your subscription to Premium Service expires in 30 days. Renew now!",
                "sender": "billing@service.com",
                "subject": "Subscription Renewal Notice",
                "expected": "ignore"
            },
            
            # NOTIFY_HUMAN emails (urgent, sensitive, complex)
            {
                "content": "The production server is down! All customer services are affected. Need immediate action!",
                "sender": "ops@company.com",
                "subject": "CRITICAL: Production Server Down",
                "expected": "notify_human"
            },
            {
                "content": "I'm disappointed with the service quality and considering canceling our contract.",
                "sender": "bigclient@enterprise.com",
                "subject": "Service Quality Concerns",
                "expected": "notify_human"
            },
            {
                "content": "Legal notice: Patent infringement claim regarding your product XYZ.",
                "sender": "legal@lawfirm.com",
                "subject": "Legal Notice - Patent Infringement",
                "expected": "notify_human"
            },
            {
                "content": "Confidential: Merger discussion details for next board meeting",
                "sender": "ceo@company.com",
                "subject": "Confidential - Board Meeting Agenda",
                "expected": "notify_human"
            },
            
            # RESPOND emails (can be handled automatically)
            {
                "content": "Hi, I'd like to schedule a meeting next week to discuss the project proposal. Are you available Tuesday afternoon?",
                "sender": "client@business.com",
                "subject": "Meeting Request - Project Discussion",
                "expected": "respond"
            },
            {
                "content": "Thank you for your presentation yesterday. Could you send me the slides?",
                "sender": "attendee@conference.com",
                "subject": "Request for Presentation Slides",
                "expected": "respond"
            },
            {
                "content": "What's the status of the quarterly report? The deadline is approaching.",
                "sender": "manager@company.com",
                "subject": "Quarterly Report Status",
                "expected": "respond"
            },
            {
                "content": "I'm interested in your consulting services. Can we set up a call to discuss pricing?",
                "sender": "prospect@newclient.com",
                "subject": "Inquiry About Consulting Services",
                "expected": "respond"
            },
            {
                "content": "The document you requested is attached. Please review and let me know if you need any changes.",
                "sender": "colleague@company.com",
                "subject": "Document Review Request",
                "expected": "respond"
            },
            {
                "content": "Can you confirm your attendance at tomorrow's team meeting at 2 PM?",
                "sender": "assistant@company.com",
                "subject": "Meeting Confirmation Required",
                "expected": "respond"
            },
            {
                "content": "I have a question about the invoice #12345. The amount seems incorrect.",
                "sender": "accounting@client.com",
                "subject": "Question About Invoice #12345",
                "expected": "respond"
            },
            {
                "content": "Could you provide an update on the project timeline? The client is asking for status.",
                "sender": "pm@company.com",
                "subject": "Project Timeline Update Request",
                "expected": "respond"
            },
            {
                "content": "I'm out of office next week. Can we reschedule our Friday meeting?",
                "sender": "partner@business.com",
                "subject": "Meeting Reschedule Request",
                "expected": "respond"
            }
        ]
    
    def evaluate_triage_accuracy(self) -> Dict[str, Any]:
        """Evaluate the agent's triage accuracy on the golden dataset."""
        
        results = []
        correct_predictions = 0
        total_predictions = len(self.test_dataset)
        
        print("Evaluating Triage Accuracy...")
        print("=" * 60)
        
        for i, test_case in enumerate(self.test_dataset, 1):
            print(f"\nTest {i}/{total_predictions}")
            print(f"From: {test_case['sender']}")
            print(f"Subject: {test_case['subject']}")
            print(f"Expected: {test_case['expected']}")
            
            # Process email through agent
            result = self.agent.process_email(
                email_content=test_case['content'],
                sender=test_case['sender'],
                subject=test_case['subject']
            )
            
            predicted = result.get('triage_decision', 'unknown')
            is_correct = predicted == test_case['expected']
            
            if is_correct:
                correct_predictions += 1
            
            print(f"Predicted: {predicted}")
            print(f"Correct: {'✓' if is_correct else '✗'}")
            
            results.append({
                'test_id': i,
                'email': test_case['content'][:50] + "...",
                'expected': test_case['expected'],
                'predicted': predicted,
                'correct': is_correct,
                'reasoning': result.get('reasoning', '')
            })
            
            print("-" * 40)
        
        accuracy = correct_predictions / total_predictions
        
        # Summary
        print(f"\nEVALUATION SUMMARY")
        print("=" * 60)
        print(f"Total Tests: {total_predictions}")
        print(f"Correct Predictions: {correct_predictions}")
        print(f"Accuracy: {accuracy:.2%}")
        print(f"Success Criteria (>80%): {'✓ PASSED' if accuracy > 0.8 else '✗ FAILED'}")
        
        # Breakdown by category
        categories = ['ignore', 'notify_human', 'respond']
        for category in categories:
            category_tests = [r for r in results if r['expected'] == category]
            category_correct = [r for r in category_tests if r['correct']]
            if category_tests:
                cat_accuracy = len(category_correct) / len(category_tests)
                print(f"{category.upper()} accuracy: {cat_accuracy:.2%} ({len(category_correct)}/{len(category_tests)})")
        
        # Save detailed results
        evaluation_results = {
            'accuracy': accuracy,
            'total_tests': total_predictions,
            'correct_predictions': correct_predictions,
            'detailed_results': results,
            'passed_criteria': accuracy > 0.8
        }
        
        with open('triage_evaluation_results.json', 'w') as f:
            json.dump(evaluation_results, f, indent=2)
        
        print(f"\nDetailed results saved to: triage_evaluation_results.json")
        
        return evaluation_results

def main():
    """Run the triage evaluation."""
    evaluator = TriageEvaluator()
    results = evaluator.evaluate_triage_accuracy()
    
    if results['passed_criteria']:
        print("\n🎉 Milestone 1 SUCCESS: Triage accuracy >80% achieved!")
    else:
        print(f"\n⚠️  Milestone 1 needs improvement: Current accuracy {results['accuracy']:.2%}")
        print("Consider refining the triage prompts or adding more context.")

if __name__ == "__main__":
    main()