import sys
import subprocess
import time

# List of subjects that need data
targets = [
    {"subject": "General Knowledge", "type": "objective", "count": 500},
    {"subject": "Physics", "type": "objective", "count": 500},
    {"subject": "Chemistry", "type": "objective", "count": 500},
    {"subject": "Islamic Studies", "type": "objective", "count": 1000},
    {"subject": "Pakistan Studies", "type": "objective", "count": 1000}
    
]

def run_gen():
    for target in targets:
        print(f"\n--- Starting Generation for {target['subject']} ({target['type']}) ---")
        cmd = [
            sys.executable, "scripts/generate_mock_data.py",
            "--subject", target['subject'],
            "--year", "2024",
            "--type", target['type'],
            "--count", str(target['count'])
        ]
        try:
            subprocess.run(cmd, check=True)
            print(f"Completed {target['subject']}")
            time.sleep(2) # Prevent rate limiting
        except Exception as e:
            print(f"Failed {target['subject']}: {e}")

if __name__ == "__main__":
    run_gen()
