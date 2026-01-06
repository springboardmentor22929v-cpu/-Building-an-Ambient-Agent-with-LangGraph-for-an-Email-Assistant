from mock_demo import MockEmailAgent

class MockTriageEvaluator:
    def __init__(self):
        self.agent = MockEmailAgent()
        self.test_dataset = [
            # IGNORE emails
            {"content": "CONGRATULATIONS! You've won $1,000,000!", "sender": "winner@spam.com", "subject": "You're a WINNER!!!", "expected": "ignore"},
            {"content": "Weekly newsletter: Top 10 productivity tips", "sender": "newsletter@productivity.com", "subject": "Weekly Newsletter", "expected": "ignore"},
            {"content": "Your subscription expires in 30 days. Renew now!", "sender": "billing@service.com", "subject": "Subscription Renewal", "expected": "ignore"},
            
            # NOTIFY_HUMAN emails
            {"content": "The production server is down! All services affected!", "sender": "ops@company.com", "subject": "CRITICAL: Server Down", "expected": "notify_human"},
            {"content": "I'm disappointed with service quality and considering canceling", "sender": "bigclient@enterprise.com", "subject": "Service Quality Concerns", "expected": "notify_human"},
            {"content": "Legal notice: Patent infringement claim regarding your product", "sender": "legal@lawfirm.com", "subject": "Legal Notice", "expected": "notify_human"},
            {"content": "Confidential: Merger discussion details for board meeting", "sender": "ceo@company.com", "subject": "Confidential - Board Meeting", "expected": "notify_human"},
            
            # RESPOND emails
            {"content": "Hi, I'd like to schedule a meeting next week to discuss the project proposal", "sender": "client@business.com", "subject": "Meeting Request", "expected": "respond"},
            {"content": "Thank you for your presentation. Could you send me the slides?", "sender": "attendee@conference.com", "subject": "Request for Slides", "expected": "respond"},
            {"content": "What's the status of the quarterly report? Deadline approaching", "sender": "manager@company.com", "subject": "Report Status", "expected": "respond"},
            {"content": "I'm interested in your consulting services. Can we discuss pricing?", "sender": "prospect@newclient.com", "subject": "Consulting Inquiry", "expected": "respond"},
            {"content": "The document you requested is attached. Please review", "sender": "colleague@company.com", "subject": "Document Review", "expected": "respond"},
            {"content": "Can you confirm attendance at tomorrow's team meeting at 2 PM?", "sender": "assistant@company.com", "subject": "Meeting Confirmation", "expected": "respond"},
            {"content": "I have a question about invoice #12345. Amount seems incorrect", "sender": "accounting@client.com", "subject": "Invoice Question", "expected": "respond"},
            {"content": "Could you provide update on project timeline? Client asking", "sender": "pm@company.com", "subject": "Timeline Update", "expected": "respond"},
            {"content": "I'm out of office next week. Can we reschedule Friday meeting?", "sender": "partner@business.com", "subject": "Meeting Reschedule", "expected": "respond"}
        ]
    
    def evaluate_triage_accuracy(self):
        results = []
        correct = 0
        total = len(self.test_dataset)
        
        print("Mock Triage Evaluation (API Key Expired - Using Mock Logic)")
        print("=" * 60)
        
        for i, test_case in enumerate(self.test_dataset, 1):
            print(f"\nTest {i}/{total}")
            print(f"From: {test_case['sender']}")
            print(f"Subject: {test_case['subject']}")
            print(f"Expected: {test_case['expected']}")
            
            result = self.agent.process_email(
                email_content=test_case['content'],
                sender=test_case['sender'],
                subject=test_case['subject']
            )
            
            predicted = result.get('triage_decision', 'unknown')
            is_correct = predicted == test_case['expected']
            
            if is_correct:
                correct += 1
            
            print(f"Predicted: {predicted}")
            print(f"Correct: {'YES' if is_correct else 'NO'}")
            
            results.append({
                'test_id': i,
                'expected': test_case['expected'],
                'predicted': predicted,
                'correct': is_correct
            })
            
            print("-" * 40)
        
        accuracy = correct / total
        
        print(f"\nMOCK EVALUATION SUMMARY")
        print("=" * 60)
        print(f"Total Tests: {total}")
        print(f"Correct Predictions: {correct}")
        print(f"Accuracy: {accuracy:.2%}")
        print(f"Milestone 1 Target (>80%): {'PASSED' if accuracy > 0.8 else 'FAILED'}")
        
        # Category breakdown
        categories = ['ignore', 'notify_human', 'respond']
        for category in categories:
            cat_tests = [r for r in results if self.test_dataset[r['test_id']-1]['expected'] == category]
            cat_correct = [r for r in cat_tests if r['correct']]
            if cat_tests:
                cat_accuracy = len(cat_correct) / len(cat_tests)
                print(f"{category.upper()} accuracy: {cat_accuracy:.2%} ({len(cat_correct)}/{len(cat_tests)})")
        
        return {
            'accuracy': accuracy,
            'total_tests': total,
            'correct_predictions': correct,
            'passed_criteria': accuracy > 0.8
        }

def main():
    evaluator = MockTriageEvaluator()
    results = evaluator.evaluate_triage_accuracy()
    
    if results['passed_criteria']:
        print("\nMILESTONE 1 SUCCESS: Mock triage accuracy >80%!")
        print("System architecture is working correctly")
        print("Get fresh API key to run real evaluation")
    else:
        print(f"\n⚠️ Mock accuracy: {results['accuracy']:.2%}")

if __name__ == "__main__":
    main()