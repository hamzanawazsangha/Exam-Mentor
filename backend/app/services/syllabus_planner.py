#!/usr/bin/env python3
"""
Syllabus Planner Service.
Automatically generates study schedule based on exam date and topics.
"""

import json
from datetime import datetime, timedelta
from pathlib import Path

class SyllabusPlanner:
    """Generate intelligent study schedules."""
    
    def __init__(self, pattern_file):
        """Initialize syllabus planner."""
        self.pattern_file = pattern_file
        self.pattern = self._load_json(pattern_file)
    
    def _load_json(self, file_path):
        """Load JSON file."""
        if not Path(file_path).exists():
            raise FileNotFoundError(f"File not found: {file_path}")
        
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    
    def generate_schedule(self, exam_type, exam_date, subjects, num_optional=3, days_per_week=6):
        """
        Generate study schedule for an exam.
        
        Args:
            exam_type: 'CSS' or 'PMS'
            exam_date: datetime object for exam
            subjects: dict with 'compulsory': [...] and 'optional': [...]
            num_optional: number of optional subjects selected
            days_per_week: study days per week (default 6)
            
        Returns:
            dict with schedule and syllabus tracker items
        """
        # Get pattern for exam type
        if exam_type not in self.pattern:
            raise ValueError(f"Exam type not found: {exam_type}")
        
        pattern_data = self.pattern[exam_type]
        
        # Calculate days available
        days_available = (exam_date - datetime.utcnow()).days
        if days_available < 30:
            raise ValueError("Not enough time before exam (minimum 30 days)")
        
        # Reserve days for mock tests and revision
        mock_test_days = max(7, days_available // 10)  # 10% of time for mock tests
        revision_days = max(7, days_available // 6)  # 16% for revision
        study_days = days_available - mock_test_days - revision_days
        
        # Collect all topics to study
        all_topics = []
        
        # Add compulsory subjects
        for subject_id in subjects.get('compulsory', []):
            subject = self._find_subject(pattern_data, subject_id)
            if subject:
                topics = subject.get('topics', [])
                for topic in topics:
                    all_topics.append({
                        'subject_id': subject_id,
                        'subject_name': subject.get('name', ''),
                        'topic_id': topic.get('id', ''),
                        'topic_name': topic.get('name', ''),
                        'weightage': topic.get('weightage', 0),
                        'is_compulsory': True,
                        'difficulty': topic.get('difficulty', {})
                    })
        
        # Add optional subjects
        for subject_id in subjects.get('optional', []):
            subject = self._find_subject(pattern_data, subject_id)
            if subject:
                topics = subject.get('topics', [])
                for topic in topics:
                    all_topics.append({
                        'subject_id': subject_id,
                        'subject_name': subject.get('name', ''),
                        'topic_id': topic.get('id', ''),
                        'topic_name': topic.get('name', ''),
                        'weightage': topic.get('weightage', 0),
                        'is_compulsory': False,
                        'difficulty': topic.get('difficulty', {})
                    })
        
        if not all_topics:
            raise ValueError("No topics found for selected subjects")
        
        # Generate day-by-day schedule
        schedule = self._distribute_topics(all_topics, study_days, days_per_week, exam_date)
        
        # Generate mock test dates
        mock_dates = self._generate_mock_test_dates(exam_date, mock_test_days)
        
        return {
            'exam_type': exam_type,
            'exam_date': exam_date.isoformat(),
            'total_days_available': days_available,
            'study_days': study_days,
            'revision_days': revision_days,
            'mock_test_days': mock_test_days,
            'days_per_week': days_per_week,
            'total_topics': len(all_topics),
            'topics': all_topics,
            'schedule': schedule,
            'mock_test_dates': mock_dates,
            'generated_at': datetime.utcnow().isoformat()
        }
    
    def _find_subject(self, pattern_data, subject_id):
        """Find subject in pattern."""
        for subject_list in [pattern_data.get('compulsory_subjects', []),
                            pattern_data.get('optional_subjects', [])]:
            if isinstance(subject_list, list):
                for subject in subject_list:
                    if subject.get('id') == subject_id:
                        return subject
        return None
    
    def _distribute_topics(self, topics, num_days, days_per_week, exam_date):
        """Distribute topics across available days."""
        schedule = {}
        
        # Sort topics by weightage (high weightage = more study days)
        sorted_topics = sorted(topics, key=lambda x: x['weightage'], reverse=True)
        
        # Calculate study hours per topic
        total_weightage = sum(t['weightage'] for t in topics)
        
        current_date = datetime.utcnow()
        day_count = 0
        topic_index = 0
        
        while current_date < exam_date and day_count < num_days:
            # Skip non-study days (weekends)
            if current_date.weekday() < 5 or (current_date.weekday() == 5 and days_per_week >= 6):  # Mon-Sat
                day_key = current_date.strftime('%Y-%m-%d')
                
                # Assign topics for this day
                daily_topics = []
                
                # Assign 2-3 topics per day based on weightage
                topics_per_day = 3
                for _ in range(topics_per_day):
                    if topic_index < len(sorted_topics):
                        daily_topics.append(sorted_topics[topic_index])
                        topic_index = (topic_index + 1) % len(sorted_topics)
                
                schedule[day_key] = {
                    'date': day_key,
                    'day_name': current_date.strftime('%A'),
                    'topics': daily_topics,
                    'recommended_hours': 6,
                    'is_mock_day': False
                }
                
                day_count += 1
            
            current_date += timedelta(days=1)
        
        return schedule
    
    def _generate_mock_test_dates(self, exam_date, num_mock_tests):
        """Generate recommended dates for mock tests."""
        mock_dates = []
        
        # First mock test: 70 days before exam
        # Subsequent: every 10-14 days
        gap_between_mocks = (exam_date - datetime.utcnow()).days // (num_mock_tests + 1)
        
        for i in range(num_mock_tests):
            mock_date = datetime.utcnow() + timedelta(days=(i + 1) * gap_between_mocks)
            
            if mock_date < exam_date:
                mock_dates.append({
                    'mock_number': i + 1,
                    'date': mock_date.isoformat(),
                    'recommended_subject': 'Mixed',
                    'duration_hours': 3
                })
        
        return mock_dates


if __name__ == "__main__":
    try:
        planner = SyllabusPlanner(r"e:\css\css_pattern_updated.json")
        
        # Generate schedule for CSS
        exam_date = datetime.utcnow() + timedelta(days=90)
        
        schedule = planner.generate_schedule(
            exam_type='CSS',
            exam_date=exam_date,
            subjects={
                'compulsory': ['essay', 'precis', 'gsa', 'ca', 'pa', 'isl'],
                'optional': ['ir', 'ps', 'history']
            },
            num_optional=3,
            days_per_week=6
        )
        
        print("CSS Study Schedule Generated:")
        print(f"Total Days Available: {schedule['total_days_available']}")
        print(f"Study Days: {schedule['study_days']}")
        print(f"Mock Test Dates: {len(schedule['mock_test_dates'])}")
        print(f"Total Topics: {schedule['total_topics']}")
        print(f"\nFirst 5 days of schedule:")
        
        for i, (date, day_info) in enumerate(list(schedule['schedule'].items())[:5]):
            print(f"\n{day_info['day_name']}, {date}:")
            for topic in day_info['topics']:
                print(f"  - {topic['topic_name']} ({topic['subject_name']})")
        
        print("\n\nMock Test Dates:")
        for mock in schedule['mock_test_dates']:
            print(f"  Mock {mock['mock_number']}: {mock['date']}")
        
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
