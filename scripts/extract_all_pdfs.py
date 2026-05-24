import os
import json
from pdfminer.high_level import extract_text
from tqdm import tqdm

def extract_all_pdfs(input_dir, output_file):
    pdf_files = [f for f in os.listdir(input_dir) if f.endswith('.pdf')]
    extracted_count = 0
    
    with open(output_file, 'w', encoding='utf-8') as out:
        for filename in tqdm(pdf_files, desc="Extracting PDFs"):
            filepath = os.path.join(input_dir, filename)
            try:
                text = extract_text(filepath)
                # Basic cleaning: remove extra whitespace
                text = " ".join(text.split())
                
                if text.strip():
                    item = {
                        "source": filename,
                        "content": text,
                        "type": "past_paper"
                    }
                    out.write(json.dumps(item) + '\n')
                    extracted_count += 1
            except Exception as e:
                print(f"Error processing {filename}: {e}")
                
    print(f"Successfully extracted text from {extracted_count} PDFs into {output_file}")

if __name__ == "__main__":
    input_directory = r"e:\css\CSS_Banks"
    output_jsonl = r"e:\css\past_papers_extracted.jsonl"
    extract_all_pdfs(input_directory, output_jsonl)
