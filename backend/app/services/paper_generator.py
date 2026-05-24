#!/usr/bin/env python3
"""
Paper/Mock Test Generation Service.
Generates papers according to exam patterns with random question selection.
"""

import os
import json
import random
from pathlib import Path
from datetime import datetime
import hashlib

class PaperGenerator:
    """Generate mock test papers based on exam patterns."""
    
    def __init__(self, pattern_file, mcq_dataset, subjective_folder):
        """
        Initialize paper generator.
        
        Args:
            pattern_file: Path to pattern JSON file (css_pattern_updated.json or pms_pattern.json)
            mcq_dataset: Path to MCQ dataset JSON file
            subjective_folder: Path to folder containing subjective papers
        """
        self.pattern_file = pattern_file
        self.mcq_dataset = mcq_dataset
        self.subjective_folder = subjective_folder
        
        # Load data
        self.pattern = self._load_json(pattern_file)
        self.mcqs = self._load_json(mcq_dataset)
        self.subjective_papers = self._load_subjective_papers()
        
        # Track generated papers to ensure uniqueness
        self.generated_papers_history = {}
    
    def _load_json(self, file_path):
        """Load JSON file."""
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"File not found: {file_path}")
        
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    
    def _load_subjective_papers(self):
        """Load all subjective papers from folder."""
        subjective_data = {}
        
        if not os.path.isdir(self.subjective_folder):
            print(f"Warning: Subjective folder not found: {self.subjective_folder}")
            return subjective_data
        
        for file_path in Path(self.subjective_folder).glob("*.json"):
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    
                    # Extract subject from filename
                    subject = file_path.stem.replace('-past-paper-', ' ').replace('-', ' ')
                    
                    if subject not in subjective_data:
                        subjective_data[subject] = []
                    
                    if isinstance(data, list):
                        subjective_data[subject].extend(data)
                    else:
                        subjective_data[subject].append(data)
            except Exception as e:
                print(f"Warning: Failed to load {file_path}: {e}")
        
        return subjective_data
    
    def generate_css_paper(self, subject_id, paper_number=1):
        """
        Generate a CSS exam paper for a specific subject.
        
        Args:
            subject_id: Subject ID from CSS pattern (e.g., 'essay', 'precis', 'gsa')
            paper_number: Paper number (1 or 2 for two-paper subjects)
            
        Returns:
            dict with generated paper details
        """
        if 'CSS' not in self.pattern:
            raise ValueError("CSS pattern not found in pattern file")
        
        css_pattern = self.pattern['CSS']
        
        # Find the subject in compulsory or optional subjects
        subject = self._find_subject(css_pattern, subject_id)
        if not subject:
            raise ValueError(f"Subject not found: {subject_id}")
        
        paper_pattern = css_pattern['paper_pattern']
        
        # Generate paper based on subject type
        if subject.get('type') == 'subjective_only':
            return self._generate_subjective_paper(subject, paper_pattern)
        else:
            return self._generate_mixed_paper(subject, paper_pattern)
    
    def generate_pms_paper(self, province, subject_id, paper_number=1):
        """
        Generate a PMS exam paper for a specific province and subject.
        
        Args:
            province: Province name (Punjab, Sindh, KPK, etc.)
            subject_id: Subject ID from PMS pattern
            paper_number: Paper number
            
        Returns:
            dict with generated paper details
        """
        if 'PMS' not in self.pattern:
            raise ValueError("PMS pattern not found in pattern file")
        
        pms_data = self.pattern['PMS']
        if province not in pms_data:
            raise ValueError(f"Province not found: {province}")
        
        province_pattern = pms_data[province]
        
        # Find the subject
        subject = self._find_subject(province_pattern, subject_id)
        if not subject:
            raise ValueError(f"Subject not found: {subject_id}")
        
        paper_pattern = province_pattern['paper_pattern']
        
        # Generate paper
        if subject.get('type') == 'subjective_only':
            return self._generate_subjective_paper(subject, paper_pattern)
        else:
            return self._generate_mixed_paper(subject, paper_pattern)
    
    def _find_subject(self, pattern_data, subject_id):
        """Find subject in pattern."""
        for subject_list in [pattern_data.get('compulsory_subjects', []),
                            pattern_data.get('optional_subjects', [])]:
            for subject in subject_list:
                if subject.get('id') == subject_id:
                    return subject
        return None
    
    def _generate_subjective_paper(self, subject, paper_pattern):
        """Generate subjective-only paper (e.g., essay)."""
        questions = []
        total_marks = subject.get('marks', 100)
        
        # Get topic distribution
        topics = subject.get('topics', [])
        if not topics:
            topics = [{'id': subject['id'], 'name': subject['name'], 'weightage': 100}]
        
        # Calculate marks per question
        num_questions = paper_pattern['subjective']['attempt']
        marks_per_question = total_marks // num_questions
        
        # Select questions from different topics based on weightage
        selected_topics = self._select_topics_by_weightage(topics, num_questions)
        
        for i, topic in enumerate(selected_topics):
            questions.append({
                "question_number": i + 1,
                "topic": topic['name'],
                "topic_id": topic['id'],
                "marks": marks_per_question,
                "type": "long_essay",
                "question_text": f"[{topic['name']}] - Write a comprehensive essay (5-10 pages) on this topic with relevant examples and analysis."
            })
        
        return {
            "paper_id": self._generate_paper_id(subject['id']),
            "subject": subject['name'],
            "subject_id": subject['id'],
            "type": "subjective_only",
            "total_questions": len(paper_pattern['subjective'].get('total_questions', 7)),
            "attempt": paper_pattern['subjective']['attempt'],
            "total_marks": total_marks,
            "time_minutes": paper_pattern['subjective']['time_minutes'],
            "questions": questions,
            "generated_at": datetime.utcnow().isoformat()
        }
    
    def _generate_mixed_paper(self, subject, paper_pattern):
        """Generate mixed (objective + subjective) paper."""
        questions = []
        total_marks = subject.get('marks', 100)
        
        # Get topics
        topics = subject.get('topics', [])
        if not topics:
            topics = [{'id': subject['id'], 'name': subject['name'], 'weightage': 100}]
        
        question_id = 1
        
        # 1. Generate MCQs
        mcq_marks = paper_pattern['objective']['marks']
        num_mcqs = paper_pattern['objective']['mcqs']
        marks_per_mcq = mcq_marks // num_mcqs
        
        mcq_questions = self._select_mcqs_by_weightage(subject['id'], topics, num_mcqs)
        for mcq in mcq_questions:
            questions.append({
                "question_number": question_id,
                "type": "mcq",
                "marks": marks_per_mcq,
                "topic": mcq.get('topic', 'General'),
                "question_text": mcq.get('question', ''),
                "options": mcq.get('options', []),
                "correct_answer": mcq.get('correct_answer', 0),
                "negative_marking": paper_pattern['objective'].get('negative_marking', 0)
            })
            question_id += 1
        
        # 2. Generate Subjective Questions
        subjective_marks = total_marks - mcq_marks
        num_subjective = paper_pattern['subjective']['attempt']
        marks_per_subjective = subjective_marks // num_subjective
        
        selected_topics = self._select_topics_by_weightage(topics, num_subjective)
        for topic in selected_topics:
            questions.append({
                "question_number": question_id,
                "type": "subjective",
                "marks": marks_per_subjective,
                "topic": topic['name'],
                "topic_id": topic['id'],
                "question_text": f"[{topic['name']}] - Answer in 300-500 words with relevant points and analysis."
            })
            question_id += 1
        
        return {
            "paper_id": self._generate_paper_id(subject['id']),
            "subject": subject['name'],
            "subject_id": subject['id'],
            "type": "mixed",
            "total_marks": total_marks,
            "time_minutes": paper_pattern['objective']['time_minutes'] + paper_pattern['subjective']['time_minutes'],
            "questions": questions,
            "objective_count": num_mcqs,
            "subjective_count": num_subjective,
            "generated_at": datetime.utcnow().isoformat()
        }
    
    def _select_topics_by_weightage(self, topics, num_selections):
        """Select topics based on weightage distribution."""
        if not topics:
            return []
        
        # Calculate total weightage
        total_weightage = sum(t.get('weightage', 0) for t in topics)
        if total_weightage == 0:
            return random.sample(topics, min(num_selections, len(topics)))
        
        # Select topics proportionally
        selected = []
        for i in range(num_selections):
            # Weighted random selection
            weights = [t.get('weightage', 0) / total_weightage for t in topics]
            selected_topic = random.choices(topics, weights=weights, k=1)[0]
            selected.append(selected_topic)
        
        return selected
    
    def _select_mcqs_by_weightage(self, subject_id, topics, num_selections):
        """Select MCQs from dataset based on topic weightage."""
        if not self.mcqs:
            return []
        
        # Filter MCQs by subject
        subject_mcqs = [q for q in self.mcqs if q.get('subject', '').lower() == subject_id.lower()]
        if not subject_mcqs:
            # Try broad matching
            subject_mcqs = [q for q in self.mcqs if subject_id.lower() in q.get('topic', '').lower()]
        
        if not subject_mcqs:
            subject_mcqs = random.sample(self.mcqs, min(num_selections, len(self.mcqs)))
        
        # Select by topic weightage
        selected = []
        for topic in topics:
            topic_name = topic.get('name', '')
            topic_mcqs = [q for q in subject_mcqs if topic_name.lower() in q.get('topic', '').lower()]
            
            if topic_mcqs:
                num_for_topic = max(1, int((topic.get('weightage', 0) / 100) * num_selections))
                selected.extend(random.sample(topic_mcqs, min(num_for_topic, len(topic_mcqs))))
        
        # Fill remaining with random MCQs
        if len(selected) < num_selections:
            remaining = num_selections - len(selected)
            available = [q for q in subject_mcqs if q not in selected]
            if available:
                selected.extend(random.sample(available, min(remaining, len(available))))
        
        return selected[:num_selections]
    
    def _generate_paper_id(self, subject_id):
        """Generate unique paper ID."""
        timestamp = datetime.utcnow().strftime('%Y%m%d%H%M%S')
        random_suffix = str(random.randint(1000, 9999))
        paper_id = f"PAPER_{subject_id}_{timestamp}_{random_suffix}"
        return paper_id


if __name__ == "__main__":
    # Test the paper generator
    try:
        gen = PaperGenerator(
            pattern_file=r"e:\css\css_pattern_updated.json",
            mcq_dataset=r"e:\css\complete_mcq_dataset_20260423_004201.json",
            subjective_folder=r"e:\css\subjective"
        )
        
        # Generate a CSS paper
        print("Generating CSS English Essay Paper...\n")
        paper1 = gen.generate_css_paper('essay')
        print(json.dumps(paper1, indent=2))
        
        print("\n" + "="*80 + "\n")
        
        print("Generating CSS English (Precis & Composition) Paper...\n")
        paper2 = gen.generate_css_paper('precis')
        print(json.dumps(paper2, indent=2)[:1000] + "...\n[truncated]")
        
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
