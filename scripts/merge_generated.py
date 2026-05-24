import os
import json
import uuid
import glob
import shutil

ROOT_DIR = os.path.dirname(os.path.dirname(__file__))
GENERATED_DIR = os.path.join(ROOT_DIR, "generated_data")
SUBJECTIVE_DIR = os.path.join(ROOT_DIR, "subjective")
MCQ_FILE = os.path.join(ROOT_DIR, "complete_mcq_dataset_20260423_004201.json")

def process_objective_file(filepath, existing_mcqs):
    print(f"Processing objective file: {filepath}")
    with open(filepath, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    new_mcqs = 0
    for item in data:
        # Standardize 'correct' field
        correct_val = item.get('correct', '')
        options = item.get('options', [])
        
        # Strip "A. ", "B. " from options if they exist
        clean_options = []
        for opt in options:
            if isinstance(opt, str) and len(opt) > 3 and opt[1] == '.' and opt[0] in ['A', 'B', 'C', 'D']:
                clean_options.append(opt[3:].strip())
            else:
                clean_options.append(opt)
        item['options'] = clean_options
        
        # Map A, B, C, D to actual text
        if correct_val in ['A', 'B', 'C', 'D'] and len(clean_options) >= 4:
            idx = ord(correct_val) - ord('A')
            item['correct'] = clean_options[idx]
            
        # Ensure it has an ID
        if 'id' not in item:
            subj_slug = str(item.get('subject', 'subject')).replace(' ', '_')
            topic_slug = str(item.get('topic', 'General')).replace(' ', '_')
            item['id'] = f"CSS_-_{subj_slug}_{topic_slug}_{uuid.uuid4().hex[:8]}"
            
        existing_mcqs.append(item)
        new_mcqs += 1
        
    return new_mcqs

def process_subjective_file(filepath):
    print(f"Processing subjective file: {filepath}")
    filename = os.path.basename(filepath)
    # E.g. pakistan_affairs_2025_subjective.json -> pakistan-affairs-past-paper-2025.json
    parts = filename.replace("_subjective.json", "").split("_")
    year = parts[-1] if parts[-1].isdigit() else "Unknown"
    subj = "-".join(parts[:-1]) if parts[-1].isdigit() else "-".join(parts)
    
    new_filename = f"{subj}-past-paper-{year}.json"
    dest_path = os.path.join(SUBJECTIVE_DIR, new_filename)
    
    shutil.copy2(filepath, dest_path)
    print(f"  -> Copied to {dest_path}")
    return 1

def main():
    if not os.path.exists(GENERATED_DIR):
        print(f"No generated_data directory found at {GENERATED_DIR}")
        return
        
    # Load existing MCQs
    print(f"Loading existing MCQs from {MCQ_FILE}...")
    try:
        with open(MCQ_FILE, 'r', encoding='utf-8') as f:
            existing_mcqs = json.load(f)
    except FileNotFoundError:
        print("Existing MCQ file not found, creating new array.")
        existing_mcqs = []
        
    initial_mcq_count = len(existing_mcqs)
    total_new_mcqs = 0
    total_subj_files = 0
    
    for filepath in glob.glob(os.path.join(GENERATED_DIR, "*.json")):
        if filepath.endswith("_objective.json"):
            total_new_mcqs += process_objective_file(filepath, existing_mcqs)
        elif filepath.endswith("_subjective.json"):
            total_subj_files += process_subjective_file(filepath)
            
    # Save MCQs back
    if total_new_mcqs > 0:
        print(f"Saving {len(existing_mcqs)} total MCQs back to {MCQ_FILE}...")
        with open(MCQ_FILE, 'w', encoding='utf-8') as f:
            json.dump(existing_mcqs, f, indent=2, ensure_ascii=False)
            
    print("\n--- Merge Complete ---")
    print(f"New Objective Questions Merged: {total_new_mcqs}")
    print(f"New Subjective Files Copied: {total_subj_files}")
    print(f"Total MCQs now in dataset: {len(existing_mcqs)}")

if __name__ == "__main__":
    main()
