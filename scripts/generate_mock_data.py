import os
import json
import requests
from dotenv import load_dotenv

# Load environment variables
load_dotenv(os.path.join(os.path.dirname(os.path.dirname(__file__)), '.env'))

def call_openai_api(prompt, system_message):
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        print("Error: OPENAI_API_KEY is not set in the .env file.")
        return None
        
    url = "https://api.openai.com/v1/chat/completions"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}"
    }
    
    data = {
        "model": "gpt-4o-mini",
        "messages": [
            {"role": "system", "content": system_message},
            {"role": "user", "content": prompt}
        ],
        "response_format": { "type": "json_object" }
    }
    
    try:
        response = requests.post(url, headers=headers, json=data)
        response.raise_for_status()
        content = response.json()['choices'][0]['message']['content']
        return json.loads(content)
    except requests.exceptions.RequestException as e:
        print(f"API request failed: {e}")
        if hasattr(e, 'response') and e.response is not None:
            print(f"Response: {e.response.text}")
        return None
    except json.JSONDecodeError as e:
        print(f"Failed to parse JSON response: {e}")
        return None

def generate_subjective_paper(subject, year, num_questions=10):
    """Generates subjective past paper questions."""
    print(f"Generating subjective paper for {subject} {year}...")
    
    prompt = (
        f"Generate {num_questions} subjective/essay-type questions for a competitive exam "
        f"(like CSS/PMS) on the subject of '{subject}' for the year {year}. "
        f"Return the output STRICTLY as a JSON object with this exact structure: "
        f'{{"subject": "{subject}", "year": "{year}", "questions": [{{"question_number": "1", "question_text": "...", "marks": 20}}]}}'
    )
    system_msg = "You are an expert exam paper setter for competitive exams. You always output valid, raw JSON."
    
    return call_openai_api(prompt, system_msg)

def generate_objective_paper(subject, year, num_questions=20):
    """Generates objective (MCQ) past paper questions."""
    print(f"Generating objective paper for {subject} {year}...")
    
    prompt = (
        f"Generate {num_questions} multiple choice questions (MCQs) for a competitive exam "
        f"(like CSS/PMS) on the subject of '{subject}' for the year {year}. "
        f"Return the output STRICTLY as a JSON object with a key 'mcqs' containing a list of objects with this exact structure: "
        f'{{"mcqs": [{{"question": "...", "options": ["A", "B", "C", "D"], "correct": "A", "year": {year}, "exam": "CSS", "subject": "{subject}", "topic": "General"}}]}}'
    )
    system_msg = "You are an expert exam paper setter for competitive exams. You always output valid, raw JSON."
    
    data = call_openai_api(prompt, system_msg)
    if data and "mcqs" in data:
        return data["mcqs"]
    return None

def main():
    import argparse
    parser = argparse.ArgumentParser(description="Generate Mock Test Data using GPT-4o-mini")
    parser.add_argument("--subject", type=str, required=True, help="Name of the subject (e.g., 'English Essay')")
    parser.add_argument("--year", type=int, required=True, help="Year of the paper (e.g., 2024)")
    parser.add_argument("--type", type=str, choices=['objective', 'subjective'], required=True, help="Type of paper to generate")
    parser.add_argument("--count", type=int, default=10, help="Number of questions to generate")
    
    args = parser.parse_args()
    
    output_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "generated_data")
    os.makedirs(output_dir, exist_ok=True)
    
    if args.type == "subjective":
        data = generate_subjective_paper(args.subject, args.year, args.count)
        if data:
            filename = f"{args.subject.replace(' ', '_').lower()}_{args.year}_subjective.json"
            filepath = os.path.join(output_dir, filename)
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            print(f"Successfully generated and saved subjective data to {filepath}")
            
    elif args.type == "objective":
        data = generate_objective_paper(args.subject, args.year, args.count)
        if data:
            filename = f"{args.subject.replace(' ', '_').lower()}_{args.year}_objective.json"
            filepath = os.path.join(output_dir, filename)
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            print(f"Successfully generated and saved objective data to {filepath}")

if __name__ == "__main__":
    main()
