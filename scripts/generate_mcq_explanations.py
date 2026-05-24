import os
import json
import requests
import time
from dotenv import load_dotenv

# Load environment variables
load_dotenv(os.path.join(os.path.dirname(os.path.dirname(__file__)), '.env'))

API_URL = "https://api.openai.com/v1/chat/completions"
API_KEY = os.environ.get("OPENAI_API_KEY")

def call_openai_for_explanations(mcqs):
    if not API_KEY:
        print("Error: OPENAI_API_KEY not found in .env")
        return None

    prompt_data = []
    for m in mcqs:
        prompt_data.append({
            "id": m.get("id"),
            "question": m.get("question"),
            "options": m.get("options"),
            "correct": m.get("correct")
        })

    system_msg = "You are an expert academic tutor. For each MCQ, provide a concise, 1-2 sentence logical explanation of why the correct answer is right. Return a JSON object with a key 'explanations' which is a list of objects, each having 'id' and 'explanation' fields."
    
    payload = {
        "model": "gpt-4o-mini",
        "messages": [
            {"role": "system", "content": system_msg},
            {"role": "user", "content": json.dumps(prompt_data)}
        ],
        "response_format": { "type": "json_object" }
    }

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {API_KEY}"
    }

    try:
        response = requests.post(API_URL, headers=headers, json=payload, timeout=120)
        response.raise_for_status()
        content = response.json()['choices'][0]['message']['content']
        return json.loads(content).get("explanations", [])
    except Exception as e:
        print(f"API Error: {e}")
        return None

def main():
    import argparse
    parser = argparse.ArgumentParser(description="Generate explanations for MCQs using GPT-4o-mini")
    parser.add_argument("--limit", type=int, default=10, help="Number of MCQs to process")
    parser.add_argument("--batch-size", type=int, default=5, help="Number of MCQs per API call")
    args = parser.parse_args()
    count = 0
    limit = args.limit
    batch_size = args.batch_size
    
    dataset_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "complete_mcq_dataset_20260423_004201.json")
    
    if not os.path.exists(dataset_path):
        print(f"Error: Dataset not found at {dataset_path}")
        return

    with open(dataset_path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    # Find MCQs without explanation
    to_process = [m for m in data if "explanation" not in m]
    print(f"Total MCQs: {len(data)}")
    print(f"MCQs missing explanation: {len(to_process)}")

    count = 0
    limit = args.limit
    batch_size = args.batch_size

    for i in range(0, min(limit, len(to_process)), batch_size):
        batch = to_process[i : i + batch_size]
        print(f"Processing batch {i//batch_size + 1} ({len(batch)} items)...")
        
        explanations = call_openai_for_explanations(batch)
        if explanations:
            # Map explanations back to data
            exp_map = {e['id']: e['explanation'] for e in explanations if 'id' in e and 'explanation' in e}
            
            updated_in_batch = 0
            for m in data:
                if m.get('id') in exp_map:
                    m['explanation'] = exp_map[m['id']]
                    updated_in_batch += 1
            
            count += updated_in_batch
            print(f"Successfully updated {updated_in_batch} MCQs.")
            
            # Save progress after each batch
            with open(dataset_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
        else:
            print("Failed to get explanations for this batch.")
            break
        
        # Small delay to be safe
        time.sleep(1)

    print(f"\nFinished. Updated {count} MCQs in total.")

if __name__ == "__main__":
    main()
