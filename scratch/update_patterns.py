import json
import os

def update_css_pattern():
    path = r'e:\css - Copy\css_pattern_updated.json'
    with open(path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    # Compulsory Subjects
    for sub in data['CSS']['compulsory_subjects']:
        if sub['id'] == 'essay':
            sub['type'] = 'subjective_only'
            sub['marks'] = 100
        elif sub['id'] == 'precis':
            sub['type'] = 'subjective_only'
            sub['marks'] = 100
        else:
            sub['type'] = 'mixed_objective_subjective'
            sub['marks'] = 100
            
    # Optional Subjects
    for group in data['CSS']['optional_subjects']['groups']:
        for sub in group['subjects']:
            sub['type'] = 'mixed_objective_subjective'
            # Note: For 200 marks subjects, the system should handle 2 papers.
            # But the 'type' is what matters for generation logic.
    
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=4)
    print("Updated CSS Pattern")

def update_pms_pattern():
    path = r'e:\css - Copy\pms_pattern.json'
    with open(path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    # Punjab
    for sub in data['PMS']['Punjab']['compulsory_subjects']:
        if sub['id'] == 'punjab_essay':
            sub['type'] = 'subjective_only'
        elif sub['id'] == 'punjab_english':
            sub['type'] = 'subjective_only'
        elif sub['id'] == 'punjab_urdu':
            sub['type'] = 'subjective_only'
        elif sub['id'] == 'punjab_gk':
            sub['type'] = 'objective_only'
        else:
            sub['type'] = 'mixed_objective_subjective'
            
    for group in data['PMS']['Punjab']['optional_subjects']['groups']:
        for sub in group['subjects']:
            sub['type'] = 'mixed_objective_subjective'

    # Sindh
    for sub in data['PMS']['Sindh']['compulsory_subjects']:
        if sub['id'] == 'sindh_essay':
            sub['type'] = 'subjective_only'
        elif sub['id'] == 'sindh_english':
            sub['type'] = 'subjective_only'
        elif sub['id'] == 'sindh_general_paper':
            sub['type'] = 'subjective_only'
        else:
            sub['type'] = 'mixed_objective_subjective'

    for group in data['PMS']['Sindh']['optional_subjects']['groups']:
        for sub in group['subjects']:
            sub['type'] = 'mixed_objective_subjective'

    # KPK
    for sub in data['PMS']['KhyberPakhtunkhwa']['compulsory_subjects']:
        if sub['id'] == 'kpk_essay':
            sub['type'] = 'subjective_only'
        elif sub['id'] == 'kpk_english':
            sub['type'] = 'subjective_only'
        else:
            sub['type'] = 'mixed_objective_subjective'

    for group in data['PMS']['KhyberPakhtunkhwa']['optional_subjects']['groups']:
        for sub in group['subjects']:
            sub['type'] = 'mixed_objective_subjective'

    # Balochistan
    for sub in data['PMS']['Balochistan']['compulsory_subjects']:
        if sub['id'] == 'balochistan_essay':
            sub['type'] = 'subjective_only'
        elif sub['id'] == 'balochistan_english':
            sub['type'] = 'subjective_only'
        elif sub['id'] == 'balochistan_urdu':
            sub['type'] = 'subjective_only'
        elif sub['id'] == 'balochistan_gk':
            sub['type'] = 'objective_only'
        else:
            sub['type'] = 'mixed_objective_subjective'

    for group in data['PMS']['Balochistan']['optional_subjects']['groups']:
        for sub in group['subjects']:
            sub['type'] = 'mixed_objective_subjective'

    with open(path, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=4)
    print("Updated PMS Pattern")

if __name__ == "__main__":
    update_css_pattern()
    update_pms_pattern()
