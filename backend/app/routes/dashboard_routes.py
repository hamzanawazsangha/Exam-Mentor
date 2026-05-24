#!/usr/bin/env python3
"""
Dashboard Analytics and Statistics API Routes.
"""

from flask import Blueprint, request, jsonify
from app.models.models import (db, CourseSelection, SyllabusTracker, MockTestAttempt, 
                               PerformanceLog, UserProgress)
from app.services.auth_service import DashboardAnalytics

dashboard_bp = Blueprint('dashboard', __name__, url_prefix='/api/dashboard')

# ─────────────────────────────────────────────
# DASHBOARD METRICS
# ─────────────────────────────────────────────

@dashboard_bp.route('/metrics/<int:user_id>', methods=['GET'])
def get_dashboard_metrics(user_id):
    """Get all dashboard metrics."""
    try:
        # Check if course is selected
        course_selection = db.session.query(CourseSelection).filter_by(user_id=user_id).first()
        if not course_selection:
            return jsonify({
                "message": "Course not selected yet",
                "ready": False
            }), 200
        
        # Calculate metrics
        progress = DashboardAnalytics.calculate_progress(
            user_id, db, CourseSelection, SyllabusTracker
        )
        
        weak_topics = DashboardAnalytics.identify_weak_topics(
            user_id, db, MockTestAttempt, PerformanceLog
        )
        
        coverage = DashboardAnalytics.calculate_syllabus_coverage(
            user_id, db, SyllabusTracker
        )
        
        mock_stats = DashboardAnalytics.get_mock_test_statistics(
            user_id, db, MockTestAttempt
        )
        
        return jsonify({
            "ready": True,
            "exam_type": course_selection.exam_type,
            "exam_date": course_selection.expected_exam_date.isoformat(),
            "overall_progress": round(progress, 1),
            "remaining_syllabus": round(100 - progress, 1),
            "subjects_coverage": coverage,
            "weak_topics": weak_topics,
            "mock_test_statistics": mock_stats
        }), 200
    
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# ─────────────────────────────────────────────
# PROGRESS CARD
# ─────────────────────────────────────────────

@dashboard_bp.route('/progress/<int:user_id>', methods=['GET'])
def get_progress_card(user_id):
    """Get progress card data."""
    try:
        course_selection = db.session.query(CourseSelection).filter_by(user_id=user_id).first()
        if not course_selection:
            return jsonify({"message": "Course not selected"}), 200
        
        progress = DashboardAnalytics.calculate_progress(
            user_id, db, CourseSelection, SyllabusTracker
        )
        
        tracker_items = db.session.query(SyllabusTracker).filter_by(user_id=user_id).all()
        completed = sum(1 for item in tracker_items if item.is_completed)
        total = len(tracker_items)
        
        return jsonify({
            "title": "Overall Progress",
            "progress_percentage": round(progress, 1),
            "completed": completed,
            "total": total,
            "remaining": total - completed
        }), 200
    
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# ─────────────────────────────────────────────
# SYLLABUS COVERAGE CARD
# ─────────────────────────────────────────────

@dashboard_bp.route('/coverage/<int:user_id>', methods=['GET'])
def get_coverage_card(user_id):
    """Get syllabus coverage by subject."""
    try:
        coverage = DashboardAnalytics.calculate_syllabus_coverage(
            user_id, db, SyllabusTracker
        )
        
        if not coverage:
            return jsonify({"message": "No data available"}), 200
        
        return jsonify({
            "title": "Syllabus Coverage by Subject",
            "subjects": coverage,
            "average_coverage": round(sum(s['percentage'] for s in coverage) / len(coverage), 1) if coverage else 0
        }), 200
    
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# ─────────────────────────────────────────────
# WEAK TOPICS CARD
# ─────────────────────────────────────────────

@dashboard_bp.route('/weak-topics/<int:user_id>', methods=['GET'])
def get_weak_topics_card(user_id):
    """Get weak topics."""
    try:
        weak_topics = DashboardAnalytics.identify_weak_topics(
            user_id, db, MockTestAttempt, PerformanceLog
        )
        
        if not weak_topics:
            return jsonify({
                "title": "Weak Topics",
                "message": "No weak topics identified yet. Keep practicing!",
                "topics": []
            }), 200
        
        return jsonify({
            "title": "Weak Topics (Needs Improvement)",
            "count": len(weak_topics),
            "topics": weak_topics
        }), 200
    
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# ─────────────────────────────────────────────
# MOCK TEST PERFORMANCE CARD
# ─────────────────────────────────────────────

@dashboard_bp.route('/mock-performance/<int:user_id>', methods=['GET'])
def get_mock_performance_card(user_id):
    """Get mock test performance statistics."""
    try:
        stats = DashboardAnalytics.get_mock_test_statistics(
            user_id, db, MockTestAttempt
        )
        
        if stats['total_mocks'] == 0:
            return jsonify({
                "title": "Mock Test Performance",
                "message": "No mock tests attempted yet. Start practicing!",
                "total_mocks": 0
            }), 200
        
        return jsonify({
            "title": "Mock Test Performance",
            "total_mocks": stats['total_mocks'],
            "average_accuracy": stats['average_accuracy'],
            "average_score": stats['average_score'],
            "improvement_trend": stats['improvement_trend']
        }), 200
    
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# ─────────────────────────────────────────────
# MOCK TEST ATTEMPTS
# ─────────────────────────────────────────────

@dashboard_bp.route('/mock-attempts/<int:user_id>', methods=['GET'])
def get_mock_attempts(user_id):
    """Get all mock test attempts."""
    try:
        attempts = db.session.query(MockTestAttempt).filter_by(user_id=user_id).all()
        
        attempts_data = [
            {
                "id": attempt.id,
                "exam_type": attempt.exam_type,
                "subject": attempt.subject,
                "total_marks": attempt.total_marks,
                "obtained_marks": attempt.obtained_marks,
                "accuracy": attempt.accuracy_percentage,
                "attempted_at": attempt.attempted_at.isoformat(),
                "is_submitted": attempt.is_submitted
            }
            for attempt in sorted(attempts, key=lambda x: x.attempted_at, reverse=True)
        ]
        
        return jsonify({
            "total_attempts": len(attempts),
            "submitted_attempts": sum(1 for a in attempts if a.is_submitted),
            "attempts": attempts_data
        }), 200
    
    except Exception as e:
        return jsonify({"error": str(e)}), 500
