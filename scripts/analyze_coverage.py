import json
import os
import re

def get_clean_subject_name(name):
    clean = re.sub(r'\(.*?\)', '', name).split('/')[0].strip()
    return clean.lower()

def analyze():
    base_dir = os.path.dirname(os.path.dirname(__file__))
    
    # Load MCQs
    mcq_path = os.path.join(base_dir, 'complete_mcq_dataset_20260423_004201.json')
    with open(mcq_path, 'r', encoding='utf-8') as f:
        mcq_data = json.load(f)
        
    # Load Subjective
    subj_dir = os.path.join(base_dir, 'subjective')
    subj_data = []
    if os.path.exists(subj_dir):
        for f_name in os.listdir(subj_dir):
            if f_name.endswith('.json'):
                with open(os.path.join(subj_dir, f_name), 'r', encoding='utf-8') as f:
                    d = json.load(f)
                    if 'questions' in d:
                        for q in d['questions']:
                            q['subject'] = d.get('subject', 'Unknown')
                            subj_data.append(q)

    # Load Patterns to get all subjects
    patterns = []
    for p_file in ['css_pattern_updated.json', 'pms_pattern.json', 'ppsc_pattern.json']:
        p_path = os.path.join(base_dir, p_file)
        if os.path.exists(p_path):
            with open(p_path, 'r', encoding='utf-8') as f:
                patterns.append(json.load(f))

    all_subjects = {} # id -> name
    
    for p in patterns:
        # Simple extraction for analysis
        def extract(obj):
            if isinstance(obj, dict):
                if 'id' in obj and 'name' in obj:
                    all_subjects[obj['id']] = obj['name']
                for v in obj.values():
                    extract(v)
            elif isinstance(obj, list):
                for v in obj:
                    extract(v)
        extract(p)

    coverage = {}
    for sub_id, sub_name in all_subjects.items():
        clean_name = get_clean_subject_name(sub_name)
        
        # Count MCQs
        mcq_count = sum(1 for q in mcq_data if clean_name in q.get('subject', '').lower() or clean_name in q.get('topic', '').lower())
        
        # Count Subjective
        subj_count = sum(1 for q in subj_data if clean_name in q.get('subject', '').lower())
        
        coverage[sub_name] = {'mcqs': mcq_count, 'subjective': subj_count}

    print("Subject Coverage Analysis:")
    print("-" * 60)
    print(f"{'Subject':<40} | {'MCQs':<6} | {'Subj':<6}")
    print("-" * 60)
    
    sorted_coverage = sorted(coverage.items(), key=lambda x: (x[1]['mcqs'], x[1]['subjective']))
    
    for name, counts in sorted_coverage:
        if counts['mcqs'] < 50 or counts['subjective'] < 10:
            print(f"{name:<40} | {counts['mcqs']:<6} | {counts['subjective']:<6}")

if __name__ == "__main__":
    analyze()
