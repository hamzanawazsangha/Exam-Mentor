#!/usr/bin/env python3
"""
Preparation, Mock Tests, and Syllabus Tracker API Routes.
"""

from flask import Blueprint, request, jsonify
import json
from datetime import datetime
from app.models.models import (db, User, CourseSelection, SyllabusTracker, MockTestAttempt, 
                               SyllabusPlan, UserProgress)
from app.services.paper_generator import PaperGenerator
from app.services.syllabus_planner import SyllabusPlanner
from app.services.auth_service import ProfileService, DashboardAnalytics

prep_bp = Blueprint('preparation', __name__, url_prefix='/api/preparation')

# ─────────────────────────────────────────────
# COURSE SELECTION
# ─────────────────────────────────────────────

@prep_bp.route('/select-exam', methods=['POST'])
def select_exam():
    """Select exam and basic details."""
    data = request.json
    user_id = data.get('user_id')
    exam_type = data.get('exam_type')  # CSS or PMS
    province = data.get('province')  # For PMS only
    exam_date_str = data.get('exam_date')  # ISO format
    
    if not user_id or not exam_type or not exam_date_str:
        return jsonify({"error": "Missing required fields"}), 400
    
    if exam_type not in ['CSS', 'PMS']:
        return jsonify({"error": "Invalid exam type"}), 400
    
    if exam_type == 'PMS' and not province:
        return jsonify({"error": "Province is required for PMS"}), 400
    
    # Check user exists
    user = db.session.query(User).filter_by(id=user_id).first()
    if not user:
        return jsonify({"error": "User not found"}), 404
    
    # Parse exam date
    try:
        exam_date = datetime.fromisoformat(exam_date_str)
    except ValueError:
        return jsonify({"error": "Invalid date format (use ISO format)"}), 400
    
    # Check if selection already exists
    existing = db.session.query(CourseSelection).filter_by(user_id=user_id).first()
    if existing:
        db.session.delete(existing)
        db.session.commit()
    
    try:
        # Get compulsory subjects from pattern
        pattern_file = r"e:\css\pms_pattern.json" if exam_type == 'PMS' else r"e:\css\css_pattern_updated.json"
        with open(pattern_file, 'r') as f:
            pattern = json.load(f)
        
        # Extract compulsory subjects
        if exam_type == 'CSS':
            pattern_data = pattern['CSS']
            compulsory_subjects = [s['id'] for s in pattern_data.get('compulsory_subjects', [])]
        else:  # PMS
            if province not in pattern['PMS']:
                return jsonify({"error": f"Invalid province: {province}"}), 400
            pattern_data = pattern['PMS'][province]
            compulsory_subjects = [s['id'] for s in pattern_data.get('compulsory_subjects', [])]
        
        # Create course selection
        course_selection = CourseSelection(
            user_id=user_id,
            exam_type=exam_type,
            province=province,
            expected_exam_date=exam_date,
            compulsory_subjects=json.dumps(compulsory_subjects),
            optional_subjects=json.dumps([])
        )
        db.session.add(course_selection)
        db.session.commit()
        
        return jsonify({
            "message": "Exam selected successfully",
            "exam_type": exam_type,
            "exam_date": exam_date.isoformat(),
            "compulsory_subjects": compulsory_subjects,
            "course_selection_id": course_selection.id
        }), 201
    
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500

@prep_bp.route('/select-optional-subjects', methods=['POST'])
def select_optional_subjects():
    """Select optional subjects."""
    data = request.json
    user_id = data.get('user_id')
    optional_subjects = data.get('optional_subjects', [])  # List of subject IDs
    
    if not user_id or not optional_subjects:
        return jsonify({"error": "User ID and optional subjects are required"}), 400
    
    try:
        # Get course selection
        course_selection = db.session.query(CourseSelection).filter_by(user_id=user_id).first()
        if not course_selection:
            return jsonify({"error": "Course selection not found"}), 404
        
        # Validate optional subjects (should be 3 from different groups)
        if len(optional_subjects) < 2:
            return jsonify({"error": "At least 2 optional subjects required"}), 400
        
        # Update optional subjects
        course_selection.optional_subjects = json.dumps(optional_subjects)
        course_selection.updated_at = datetime.utcnow()
        db.session.commit()
        
        # Generate syllabus plan
        return generate_syllabus_plan_for_user(user_id)
    
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500

# ─────────────────────────────────────────────
# OPTIONAL SUBJECTS RECOMMENDATIONS
# ─────────────────────────────────────────────

@prep_bp.route('/recommend-subjects/<int:user_id>', methods=['GET'])
def get_subject_recommendations(user_id):
    """Get recommended optional subjects based on degree."""
    try:
        user = db.session.query(User).filter_by(id=user_id).first()
        if not user or not user.profile:
            return jsonify({"error": "User profile not found"}), 404
        
        course_selection = db.session.query(CourseSelection).filter_by(user_id=user_id).first()
        if not course_selection:
            return jsonify({"error": "Course selection not found"}), 404
        
        # Load pattern
        pattern_file = r"e:\css\pms_pattern.json" if course_selection.exam_type == 'PMS' else r"e:\css\css_pattern_updated.json"
        with open(pattern_file, 'r') as f:
            pattern = json.load(f)
        
        # Get recommendations
        recommendations = ProfileService.get_recommended_optional_subjects(
            user.profile.degree,
            course_selection.exam_type,
            pattern
        )
        
        return jsonify({
            "degree": user.profile.degree,
            "exam_type": course_selection.exam_type,
            "recommendations": recommendations
        }), 200
    
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# ─────────────────────────────────────────────
# SYLLABUS TRACKER
# ─────────────────────────────────────────────

def generate_syllabus_plan_for_user(user_id):
    """Generate syllabus plan and tracker."""
    try:
        course_selection = db.session.query(CourseSelection).filter_by(user_id=user_id).first()
        if not course_selection:
            return jsonify({"error": "Course selection not found"}), 404
        
        # Load pattern
        pattern_file = r"e:\css\pms_pattern.json" if course_selection.exam_type == 'PMS' else r"e:\css\css_pattern_updated.json"
        
        # Generate plan
        planner = SyllabusPlanner(pattern_file)
        
        subjects = {
            'compulsory': json.loads(course_selection.compulsory_subjects),
            'optional': json.loads(course_selection.optional_subjects)
        }
        
        plan = planner.generate_schedule(
            course_selection.exam_type,
            course_selection.expected_exam_date,
            subjects
        )
        
        # Create or update syllabus plan
        existing_plan = db.session.query(SyllabusPlan).filter_by(
            course_selection_id=course_selection.id
        ).first()
        
        if existing_plan:
            db.session.delete(existing_plan)
        
        syllabus_plan = SyllabusPlan(
            course_selection_id=course_selection.id,
            plan_data=json.dumps(plan),
            total_days=plan['total_days_available'],
            study_days_per_week=6,
            mock_test_dates=json.dumps(plan['mock_test_dates'])
        )
        db.session.add(syllabus_plan)
        db.session.commit()
        
        # Create syllabus tracker items
        db.session.query(SyllabusTracker).filter_by(user_id=user_id).delete()
        
        for topic in plan['topics']:
            tracker = SyllabusTracker(
                user_id=user_id,
                subject_id=topic['subject_id'],
                topic_id=topic['topic_id'],
                topic_name=topic['topic_name'],
                weightage=topic['weightage']
            )
            db.session.add(tracker)
        
        db.session.commit()
        
        return jsonify({
            "message": "Syllabus plan generated successfully",
            "total_topics": plan['total_topics'],
            "study_days": plan['study_days'],
            "mock_tests": len(plan['mock_test_dates']),
            "plan_id": syllabus_plan.id
        }), 201
    
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500

@prep_bp.route('/syllabus-tracker/<int:user_id>', methods=['GET'])
def get_syllabus_tracker(user_id):
    """Get syllabus tracker items."""
    try:
        items = db.session.query(SyllabusTracker).filter_by(user_id=user_id).all()
        
        tracker_data = [
            {
                "id": item.id,
                "subject_id": item.subject_id,
                "topic_id": item.topic_id,
                "topic_name": item.topic_name,
                "weightage": item.weightage,
                "is_completed": item.is_completed,
                "self_marked": item.self_marked,
                "scheduled_date": item.scheduled_date.isoformat() if item.scheduled_date else None
            }
            for item in items
        ]
        
        return jsonify({
            "total_topics": len(items),
            "completed": sum(1 for item in items if item.is_completed),
            "tracker": tracker_data
        }), 200
    
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@prep_bp.route('/syllabus-tracker/<int:user_id>/<int:tracker_id>', methods=['PUT'])
def mark_topic_complete(user_id, tracker_id):
    """Mark topic as complete."""
    data = request.json
    self_marked = data.get('self_marked', False)
    
    try:
        tracker = db.session.query(SyllabusTracker).filter_by(
            id=tracker_id,
            user_id=user_id
        ).first()
        
        if not tracker:
            return jsonify({"error": "Tracker item not found"}), 404
        
        tracker.is_completed = True
        tracker.self_marked = self_marked
        if not self_marked:
            tracker.system_marked_at = datetime.utcnow()
        
        db.session.commit()
        
        return jsonify({
            "message": "Topic marked as complete"
        }), 200
    
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500

# ─────────────────────────────────────────────
# MOCK TESTS / PAPER GENERATION
# ─────────────────────────────────────────────

@prep_bp.route('/generate-paper/<int:user_id>/<subject_id>', methods=['POST'])
def generate_mock_paper(user_id, subject_id):
    """Generate a mock test paper."""
    try:
        course_selection = db.session.query(CourseSelection).filter_by(user_id=user_id).first()
        if not course_selection:
            return jsonify({"error": "Course selection not found"}), 404
        
        # Initialize paper generator
        gen = PaperGenerator(
            pattern_file=r"e:\css\pms_pattern.json" if course_selection.exam_type == 'PMS' else r"e:\css\css_pattern_updated.json",
            mcq_dataset=r"e:\css\complete_mcq_dataset_20260423_004201.json",
            subjective_folder=r"e:\css\subjective"
        )
        
        # Generate paper based on exam type
        if course_selection.exam_type == 'CSS':
            paper = gen.generate_css_paper(subject_id)
        else:
            paper = gen.generate_pms_paper(course_selection.province, subject_id)
        
        # Create mock test attempt record
        mock_attempt = MockTestAttempt(
            user_id=user_id,
            exam_type=course_selection.exam_type,
            subject=subject_id,
            total_marks=paper['total_marks'],
            time_taken_minutes=0,
            generated_paper_id=paper['paper_id']
        )
        db.session.add(mock_attempt)
        db.session.commit()
        
        return jsonify({
            "message": "Paper generated successfully",
            "paper": paper,
            "attempt_id": mock_attempt.id
        }), 200
    
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500
