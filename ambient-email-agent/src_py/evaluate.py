import json
from pathlib import Path
from agent import run_agent_on_email

DATA_PATH = Path('data') / 'golden_emails.json'
OUT_PATH = Path('data') / 'triage_results_py.json'


def load_emails():
    with open(DATA_PATH, 'r', encoding='utf-8') as f:
        return json.load(f)


def run_evaluation():
    emails = load_emails()
    correct = 0
    results = []

    for em in emails:
        res = run_agent_on_email(em)
        match = res['classification'] == em.get('human_label')
        if match:
            correct += 1
        results.append({
            'id': em.get('id'),
            'subject': em.get('subject'),
            'human_label': em.get('human_label'),
            'classification': res['classification'],
            'match': match,
            'triage_reason': res['triage_reason']
        })
        print(f"Email {em.get('id')}: {res['classification']} — {res['triage_reason']} — match: {match}")

    accuracy = (correct / len(emails)) * 100 if emails else 0.0
    summary = {'total': len(emails), 'correct': correct, 'accuracy': accuracy}

    with open(OUT_PATH, 'w', encoding='utf-8') as f:
        json.dump({'summary': summary, 'results': results}, f, indent=2)

    print('\n--- Evaluation ---')
    print(f"Total: {len(emails)}, Correct: {correct}, Accuracy: {accuracy:.1f}%")
    print(f"Saved trace: {OUT_PATH}")


if __name__ == '__main__':
    run_evaluation()
