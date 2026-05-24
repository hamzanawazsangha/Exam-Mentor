import json
import os

def merge_notes(css_path, pms_path, output_path):
    merged_data = []
    
    # Process CSS Notes
    if os.path.exists(css_path):
        with open(css_path, 'r', encoding='utf-8') as f:
            for line in f:
                if line.strip():
                    item = json.loads(line)
                    item['exam_type'] = 'CSS'
                    merged_data.append(item)
                    
    # Process PMS Notes
    if os.path.exists(pms_path):
        with open(pms_path, 'r', encoding='utf-8') as f:
            for line in f:
                if line.strip():
                    item = json.loads(line)
                    item['exam_type'] = 'PMS'
                    merged_data.append(item)
                    
    # Write merged data
    with open(output_path, 'w', encoding='utf-8') as f:
        for item in merged_data:
            f.write(json.dumps(item) + '\n')
            
    print(f"Successfully merged {len(merged_data)} items into {output_path}")

if __name__ == "__main__":
    css_file = r"e:\css\css_notes_rag.jsonl"
    pms_file = r"e:\css\pms_notes_rag.jsonl"
    output_file = r"e:\css\master_notes_rag.jsonl"
    merge_notes(css_file, pms_file, output_file)
