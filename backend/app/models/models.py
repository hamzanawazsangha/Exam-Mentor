from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import json

db = SQLAlchemy()

class PendingRegistration(db.Model):
    """Temporary storage for registration data until email verification"""
    __tablename__ = 'pending_registrations'
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    first_name = db.Column(db.String(50), nullable=False)
    last_name = db.Column(db.String(50), nullable=False)
    verification_code = db.Column(db.String(10), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class User(db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    is_verified = db.Column(db.Boolean, default=True)  # Users created after verification are always verified
    verification_code = db.Column(db.String(10), nullable=True)
    
    first_name = db.Column(db.String(50), nullable=True)
    last_name = db.Column(db.String(50), nullable=True)
    photo_url = db.Column(db.String(255), nullable=True)
    age = db.Column(db.Integer, nullable=True)
    degree = db.Column(db.String(100), nullable=True)
    
    exam_target = db.Column(db.String(50), nullable=True) # CSS or PMS
    province = db.Column(db.String(50), nullable=True) # for PMS
    exam_date = db.Column(db.Date, nullable=True)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class UserSubject(db.Model):
    __tablename__ = 'user_subjects'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    subject_id = db.Column(db.String(100), nullable=False)
    subject_name = db.Column(db.String(255), nullable=False)
    is_compulsory = db.Column(db.Boolean, default=True)

class ScheduleTask(db.Model):
    __tablename__ = 'schedule_tasks'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    subject_id = db.Column(db.String(100), nullable=False)
    topic_id = db.Column(db.String(100), nullable=False)
    topic_name = db.Column(db.String(255), nullable=False)
    date_assigned = db.Column(db.Date, nullable=False)
    is_completed = db.Column(db.Boolean, default=False)
    is_mock_test_day = db.Column(db.Boolean, default=False) # For days dedicated to mock tests

class MockTest(db.Model):
    __tablename__ = 'mock_tests'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    exam_target = db.Column(db.String(50), nullable=False) # CSS/PMS
    paper_data = db.Column(db.Text, nullable=False) # JSON of the generated test
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    score_objective = db.Column(db.Float, nullable=True)
    score_subjective = db.Column(db.Float, nullable=True)
    user_answers = db.Column(db.Text, nullable=True) # JSON of user answers for subjective
    ai_feedback = db.Column(db.Text, nullable=True) # AI feedback text or JSON

class UserProgress(db.Model):
    __tablename__ = 'user_progress'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    topic_id = db.Column(db.String(100), nullable=False)
    subject_id = db.Column(db.String(100), nullable=False)
    completion_percentage = db.Column(db.Float, default=0.0)
    last_updated = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class PerformanceLog(db.Model):
    __tablename__ = 'performance_log'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    topic_id = db.Column(db.String(100), nullable=False)
    subject_id = db.Column(db.String(100), nullable=False)
    score = db.Column(db.Float, nullable=False) # e.g. 0.8 for 80%
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    question_type = db.Column(db.String(20)) # MCQ, Subjective

class Essay(db.Model):
    __tablename__ = 'essays'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    topic = db.Column(db.String(255), nullable=False)
    content = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
