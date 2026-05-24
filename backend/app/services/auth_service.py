#!/usr/bin/env python3
"""
User Authentication and Profile Management Service.
"""

import hashlib
import secrets
import re
from datetime import datetime, timedelta
from flask import current_app
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

class AuthService:
    """Handle user authentication."""
    
    @staticmethod
    def hash_password(password):
        """Hash password using SHA-256."""
        return hashlib.sha256(password.encode()).hexdigest()
    
    @staticmethod
    def verify_password(password, hash_):
        """Verify password against hash."""
        return AuthService.hash_password(password) == hash_
    
    @staticmethod
    def generate_verification_code():
        """Generate 6-digit verification code."""
        return str(secrets.randbelow(1000000)).zfill(6)
    
    @staticmethod
    def validate_email(email):
        """Validate email format."""
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return re.match(pattern, email) is not None
    
    @staticmethod
    def validate_password(password):
        """
        Validate password strength.
        Requirements:
        - At least 8 characters
        - At least one uppercase
        - At least one lowercase
        - At least one digit
        - At least one special character
        """
        if len(password) < 8:
            return False, "Password must be at least 8 characters long"
        
        if not re.search(r'[A-Z]', password):
            return False, "Password must contain at least one uppercase letter"
        
        if not re.search(r'[a-z]', password):
            return False, "Password must contain at least one lowercase letter"
        
        if not re.search(r'\d', password):
            return False, "Password must contain at least one digit"
        
        if not re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
            return False, "Password must contain at least one special character"
        
        return True, "Password is valid"


class EmailService:
    """Send verification codes and notifications."""
    
    @staticmethod
    def send_verification_code(email, code):
        """Send verification code via email."""
        try:
            # Note: Requires SMTP configuration
            # For now, just log it
            print(f"[EmailService] Verification code for {email}: {code}")
            return True
        except Exception as e:
            print(f"[EmailService] Error sending email: {e}")
            return False
    
    @staticmethod
    def send_password_reset_code(email, code):
        """Send password reset code via email."""
        try:
            print(f"[EmailService] Password reset code for {email}: {code}")
            return True
        except Exception as e:
            print(f"[EmailService] Error sending email: {e}")
            return False


class ProfileService:
    """Handle user profile operations."""
    
    @staticmethod
    def get_recommended_optional_subjects(degree, exam_type, pattern_data):
        """
        Get recommended optional subjects based on user's degree.
        
        Args:
            degree: User's degree (e.g., "BS Computer Science")
            exam_type: 'CSS' or 'PMS'
            pattern_data: Exam pattern data
            
        Returns:
            list of recommended subject IDs
        """
        recommendations = {
            'computer science': ['cs', 'business', 'ir'],
            'business': ['business', 'economics', 'ir'],
            'law': ['law', 'ps', 'ir'],
            'international relations': ['ir', 'ps', 'history'],
            'history': ['history', 'ir', 'ps'],
            'islamic studies': ['isl_studies', 'ir', 'history'],
            'biology': ['biology', 'chemistry', 'physics'],
            'chemistry': ['chemistry', 'biology', 'physics'],
            'physics': ['physics', 'mathematics', 'cs'],
            'mathematics': ['mathematics', 'physics', 'cs'],
        }
        
        degree_lower = degree.lower() if degree else ''
        
        # Find matching degree keywords
        for key, subjects in recommendations.items():
            if key in degree_lower:
                return subjects
        
        # Default recommendations
        if exam_type == 'CSS':
            return ['ir', 'ps', 'history']
        else:
            return []
    
    @staticmethod
    def validate_profile_data(name, age=None, degree=None, profile_photo_url=None):
        """Validate profile data."""
        if not name or len(name.strip()) < 2:
            return False, "Name is required and must be at least 2 characters"
        
        if age and (age < 18 or age > 100):
            return False, "Age must be between 18 and 100"
        
        return True, "Profile data is valid"


class DashboardAnalytics:
    """Generate dashboard analytics and statistics."""
    
    @staticmethod
    def calculate_progress(user_id, db, CourseSelection, SyllabusTracker):
        """Calculate overall progress percentage."""
        try:
            # Get course selection
            course = db.session.query(CourseSelection).filter_by(user_id=user_id).first()
            if not course:
                return 0
            
            # Get syllabus tracker items
            tracker_items = db.session.query(SyllabusTracker).filter_by(user_id=user_id).all()
            if not tracker_items:
                return 0
            
            completed = sum(1 for item in tracker_items if item.is_completed)
            total = len(tracker_items)
            
            return (completed / total * 100) if total > 0 else 0
        except Exception as e:
            print(f"Error calculating progress: {e}")
            return 0
    
    @staticmethod
    def identify_weak_topics(user_id, db, MockTestAttempt, PerformanceLog):
        """Identify weak topics based on performance."""
        try:
            performance_logs = db.session.query(PerformanceLog).filter(
                PerformanceLog.user_id == user_id,
                PerformanceLog.score < 0.5  # Less than 50%
            ).all()
            
            weak_topics = {}
            for log in performance_logs:
                if log.topic_id not in weak_topics:
                    weak_topics[log.topic_id] = []
                weak_topics[log.topic_id].append(log.score)
            
            # Calculate average score for each topic
            weak_summary = []
            for topic_id, scores in weak_topics.items():
                avg_score = sum(scores) / len(scores)
                weak_summary.append({
                    'topic_id': topic_id,
                    'average_score': avg_score,
                    'attempts': len(scores)
                })
            
            # Sort by average score (lowest first)
            return sorted(weak_summary, key=lambda x: x['average_score'])[:5]
        except Exception as e:
            print(f"Error identifying weak topics: {e}")
            return []
    
    @staticmethod
    def calculate_syllabus_coverage(user_id, db, SyllabusTracker):
        """Calculate syllabus coverage by subject."""
        try:
            tracker_items = db.session.query(SyllabusTracker).filter_by(user_id=user_id).all()
            
            coverage_by_subject = {}
            for item in tracker_items:
                if item.subject_id not in coverage_by_subject:
                    coverage_by_subject[item.subject_id] = {'completed': 0, 'total': 0}
                
                coverage_by_subject[item.subject_id]['total'] += 1
                if item.is_completed:
                    coverage_by_subject[item.subject_id]['completed'] += 1
            
            # Calculate percentages
            coverage_summary = []
            for subject_id, data in coverage_by_subject.items():
                percentage = (data['completed'] / data['total'] * 100) if data['total'] > 0 else 0
                coverage_summary.append({
                    'subject_id': subject_id,
                    'completed': data['completed'],
                    'total': data['total'],
                    'percentage': round(percentage, 1)
                })
            
            return coverage_summary
        except Exception as e:
            print(f"Error calculating coverage: {e}")
            return []
    
    @staticmethod
    def get_mock_test_statistics(user_id, db, MockTestAttempt):
        """Get mock test performance statistics."""
        try:
            mock_attempts = db.session.query(MockTestAttempt).filter_by(
                user_id=user_id,
                is_submitted=True
            ).all()
            
            if not mock_attempts:
                return {
                    'total_mocks': 0,
                    'average_accuracy': 0,
                    'average_score': 0,
                    'improvement_trend': []
                }
            
            total_mocks = len(mock_attempts)
            avg_accuracy = sum(m.accuracy_percentage for m in mock_attempts) / total_mocks
            avg_score = sum(m.obtained_marks for m in mock_attempts) / total_mocks
            
            # Calculate improvement trend
            improvement_trend = [
                {
                    'mock_number': i + 1,
                    'accuracy': m.accuracy_percentage,
                    'score': m.obtained_marks,
                    'date': m.attempted_at.isoformat()
                }
                for i, m in enumerate(sorted(mock_attempts, key=lambda x: x.attempted_at))
            ]
            
            return {
                'total_mocks': total_mocks,
                'average_accuracy': round(avg_accuracy, 1),
                'average_score': round(avg_score, 1),
                'improvement_trend': improvement_trend
            }
        except Exception as e:
            print(f"Error getting mock statistics: {e}")
            return {}


if __name__ == "__main__":
    # Test authentication
    auth = AuthService()
    
    print("Testing password hashing...")
    pwd = "TestPass123!"
    hash_ = auth.hash_password(pwd)
    print(f"Password: {pwd}")
    print(f"Hash: {hash_}")
    print(f"Verified: {auth.verify_password(pwd, hash_)}")
    
    print("\nTesting verification code generation...")
    code = auth.generate_verification_code()
    print(f"Code: {code}")
    
    print("\nTesting email validation...")
    print(f"test@example.com: {auth.validate_email('test@example.com')}")
    print(f"invalid.email: {auth.validate_email('invalid.email')}")
    
    print("\nTesting password validation...")
    result, msg = auth.validate_password("weak")
    print(f"'weak': {msg}")
    
    result, msg = auth.validate_password("StrongPass123!")
    print(f"'StrongPass123!': {msg}")
