from flask import Blueprint, request, jsonify
from datetime import datetime, timedelta
import json
import os
import math
import jwt

from app.models.models import db, User, UserSubject, ScheduleTask
from app.api.routers.auth import JWT_SECRET

prep_bp = Blueprint('prep', __name__)

def get_user_from_token(auth_header):
    if not auth_header or not auth_header.startswith('Bearer '):
        return None
    token = auth_header.split(' ')[1]
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=["HS256"])
        return User.query.get(payload['user_id'])
    except:
        return None

def load_pattern(exam_target, province=None):
    base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
    if exam_target == 'CSS':
        with open(os.path.join(base_dir, '..', 'css_pattern_updated.json'), 'r', encoding='utf-8') as f:
            return json.load(f).get('CSS', {})
    elif exam_target == 'PMS':
        with open(os.path.join(base_dir, '..', 'pms_pattern.json'), 'r', encoding='utf-8') as f:
            data = json.load(f).get('PMS', {})
            return data.get(province, {}) if province else data
    elif exam_target == 'PPSC':
        with open(os.path.join(base_dir, '..', 'ppsc_pattern.json'), 'r', encoding='utf-8') as f:
            return json.load(f).get('PPSC', {})
    return {}

@prep_bp.route('/patterns', methods=['GET'])
def get_patterns():
    base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
    try:
        with open(os.path.join(base_dir, '..', 'css_pattern_updated.json'), 'r', encoding='utf-8') as f:
            css_data = json.load(f).get('CSS', {})
        with open(os.path.join(base_dir, '..', 'pms_pattern.json'), 'r', encoding='utf-8') as f:
            pms_data = json.load(f).get('PMS', {})
        with open(os.path.join(base_dir, '..', 'ppsc_pattern.json'), 'r', encoding='utf-8') as f:
            ppsc_data = json.load(f).get('PPSC', {})
        return jsonify({"CSS": css_data, "PMS": pms_data, "PPSC": ppsc_data})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@prep_bp.route('/save', methods=['POST'])
def save_preparation():
    user = get_user_from_token(request.headers.get('Authorization'))
    if not user:
        return jsonify({"error": "Unauthorized"}), 401
        
    data = request.json
    exam_target = data.get('exam_target')
    province = data.get('province')
    exam_date_str = data.get('exam_date')
    selected_optionals = data.get('optional_subjects', [])
    
    if not exam_target or not exam_date_str:
        return jsonify({"error": "Exam target and date are required"}), 400
        
    try:
        exam_date = datetime.strptime(exam_date_str, '%Y-%m-%d').date()
    except:
        return jsonify({"error": "Invalid date format"}), 400

    today = datetime.utcnow().date()
    if exam_date <= today:
        return jsonify({"error": "Exam date must be in the future"}), 400
        
    # Load pattern to get topics
    pattern = load_pattern(exam_target, province)
    if not pattern:
        return jsonify({"error": "Pattern not found"}), 400

    # Validate optional subjects for PMS exams
    if exam_target == 'PMS':
        required_opts = pattern.get('meta', {}).get('optional_subjects_required', 3)
        if len(selected_optionals) < required_opts:
            return jsonify({
                "error": f"PMS {province} requires {required_opts} optional subjects. You selected {len(selected_optionals)}."
            }), 400

    # Determine if this is an update or a new preparation
    existing_subjects = UserSubject.query.filter_by(user_id=user.id).all()
    is_update = len(existing_subjects) > 0

    # If updating, we keep track of completed topics for subjects that remain
    completed_topics = []
    if is_update:
        # Get all completed tasks to preserve progress
        completed_tasks = ScheduleTask.query.filter_by(user_id=user.id, is_completed=True).all()
        # We only keep completed topics if the subject is still selected (compulsory or in selected_optionals)
        # Compulsory subjects are always there
        compulsory_ids = [s['id'] for s in pattern.get('compulsory_subjects', [])]
        for task in completed_tasks:
            if task.subject_id in compulsory_ids or task.subject_id in selected_optionals:
                completed_topics.append((task.subject_id, task.topic_id))

    # Update user details
    user.exam_target = exam_target
    user.province = province
    user.exam_date = exam_date
    
    # Sync UserSubject table
    UserSubject.query.filter_by(user_id=user.id).delete()
    
    topics_to_schedule = []
    
    # Handle PPSC differently - sections instead of compulsory_subjects
    if exam_target == 'PPSC':
        # For PPSC, treat sections as subjects
        for section in pattern.get('sections', []):
            db.session.add(UserSubject(user_id=user.id, subject_id=section['id'], subject_name=section['name'], is_compulsory=True))
            # Create topics from section topics/metadata
            for topic_idx, topic_name in enumerate(section.get('topics', [])):
                t_id = f"{section['id']}_topic_{topic_idx}"
                if (section['id'], t_id) not in completed_topics:
                    topics_to_schedule.append({
                        "subject_id": section['id'],
                        "topic_id": t_id,
                        "topic_name": topic_name if isinstance(topic_name, str) else topic_name.get('name', f'Topic {topic_idx+1}')
                    })
    else:
        # Process Compulsory for CSS/PMS
        for sub in pattern.get('compulsory_subjects', []):
            db.session.add(UserSubject(user_id=user.id, subject_id=sub['id'], subject_name=sub['name'], is_compulsory=True))
            for topic in sub.get('topics', []):
                t_id = topic.get('id', topic.get('name'))
                if (sub['id'], t_id) not in completed_topics:
                    topics_to_schedule.append({
                        "subject_id": sub['id'],
                        "topic_id": t_id,
                        "topic_name": topic['name']
                    })
                
        # Process Optionals
        all_opts = []
        opt_data = pattern.get('optional_subjects', {})
        if isinstance(opt_data, dict) and 'groups' in opt_data:
            for group in opt_data.get('groups', []):
                all_opts.extend(group.get('subjects', []))
        elif isinstance(opt_data, list):
            all_opts = opt_data
                
        for opt_id in selected_optionals:
            sub_info = next((s for s in all_opts if s['id'] == opt_id), None)
            if sub_info:
                db.session.add(UserSubject(user_id=user.id, subject_id=sub_info['id'], subject_name=sub_info['name'], is_compulsory=False))
                for topic in sub_info.get('topics', []):
                    t_id = topic.get('id', topic.get('name'))
                    if (sub_info['id'], t_id) not in completed_topics:
                        topics_to_schedule.append({
                            "subject_id": sub_info['id'],
                            "topic_id": t_id,
                            "topic_name": topic['name']
                        })
                
    # Delete all uncompleted tasks
    ScheduleTask.query.filter_by(user_id=user.id, is_completed=False).delete()
    # Delete completed tasks for subjects that are NO LONGER in the list
    # (they weren't added to completed_topics)
    # Actually, it's easier to just delete ALL tasks that aren't in completed_topics
    all_tasks = ScheduleTask.query.filter_by(user_id=user.id).all()
    for t in all_tasks:
        if t.is_completed and (t.subject_id, t.topic_id) not in completed_topics:
            db.session.delete(t)

    db.session.commit()
    
    # Rescheduling Logic
    total_days = (exam_date - today).days
    
    mock_test_days = max(1, int(total_days * 0.10))
    study_days = total_days - mock_test_days
    
    if study_days <= 0:
        study_days = 1
        
    tasks_per_day = math.ceil(len(topics_to_schedule) / study_days)
    
    current_date = today + timedelta(days=1)
    task_idx = 0
    
    # Assign study tasks
    for i in range(study_days):
        for _ in range(tasks_per_day):
            if task_idx < len(topics_to_schedule):
                t = topics_to_schedule[task_idx]
                db.session.add(ScheduleTask(
                    user_id=user.id,
                    subject_id=t['subject_id'],
                    topic_id=t['topic_id'],
                    topic_name=t['topic_name'],
                    date_assigned=current_date,
                    is_completed=False,
                    is_mock_test_day=False
                ))
                task_idx += 1
        current_date += timedelta(days=1)
        
    # Assign mock test days
    for i in range(mock_test_days):
        db.session.add(ScheduleTask(
            user_id=user.id,
            subject_id='mock_test',
            topic_id=f'mock_{i+1}',
            topic_name=f'Full Mock Test {i+1}',
            date_assigned=current_date,
            is_completed=False,
            is_mock_test_day=True
        ))
        current_date += timedelta(days=1)
        
    db.session.commit()
    
    return jsonify({"message": "Preparation updated and schedule adjusted." if is_update else "Preparation saved and syllabus scheduled."}), 200

@prep_bp.route('/status/delete', methods=['DELETE'])
def delete_preparation():
    user = get_user_from_token(request.headers.get('Authorization'))
    if not user:
        return jsonify({"error": "Unauthorized"}), 401
        
    # Reset user fields
    user.exam_target = None
    user.province = None
    user.exam_date = None
    
    # Delete all subjects and tasks
    UserSubject.query.filter_by(user_id=user.id).delete()
    ScheduleTask.query.filter_by(user_id=user.id).delete()
    
    db.session.commit()
    return jsonify({"message": "Preparation deleted successfully."}), 200

@prep_bp.route('/schedule', methods=['GET'])
def get_schedule():
    user = get_user_from_token(request.headers.get('Authorization'))
    if not user:
        return jsonify({"error": "Unauthorized"}), 401
        
    tasks = ScheduleTask.query.filter_by(user_id=user.id).order_by(ScheduleTask.date_assigned).all()
    
    res = []
    for t in tasks:
        res.append({
            "id": t.id,
            "subject_id": t.subject_id,
            "topic_name": t.topic_name,
            "date_assigned": t.date_assigned.isoformat(),
            "is_completed": t.is_completed,
            "is_mock_test_day": t.is_mock_test_day
        })
        
    return jsonify({"tasks": res}), 200

@prep_bp.route('/task/<int:task_id>/complete', methods=['POST'])
def toggle_task(task_id):
    user = get_user_from_token(request.headers.get('Authorization'))
    if not user:
        return jsonify({"error": "Unauthorized"}), 401
        
    task = ScheduleTask.query.filter_by(id=task_id, user_id=user.id).first()
    if not task:
        return jsonify({"error": "Task not found"}), 404
        
    data = request.json
    task.is_completed = data.get('is_completed', True)
    db.session.commit()
    
    return jsonify({"message": "Task updated"}), 200

@prep_bp.route('/status', methods=['GET'])
def get_prep_status():
    user = get_user_from_token(request.headers.get('Authorization'))
    if not user:
        return jsonify({"error": "Unauthorized"}), 401
        
    subjects = UserSubject.query.filter_by(user_id=user.id).all()
    
    return jsonify({
        "exam_target": user.exam_target,
        "province": user.province,
        "exam_date": user.exam_date.isoformat() if user.exam_date else None,
        "subjects": [{"subject_id": s.subject_id, "is_compulsory": s.is_compulsory} for s in subjects]
    }), 200
