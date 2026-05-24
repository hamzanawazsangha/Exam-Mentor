from flask import Blueprint, request, jsonify
import json
import os
import random
import jwt
from app.models.models import db, User, MockTest, PerformanceLog
from app.api.routers.auth import JWT_SECRET

mocktest_bp = Blueprint('mocktest', __name__)

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

def load_mcqs():
    base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
    path = os.path.join(base_dir, '..', 'complete_mcq_dataset_20260423_004201.json')
    try:
        with open(path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except:
        return []

def load_subjective():
    base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
    subj_dir = os.path.join(base_dir, '..', 'subjective')
    questions = []
    if os.path.exists(subj_dir):
        for f_name in os.listdir(subj_dir):
            if f_name.endswith('.json'):
                with open(os.path.join(subj_dir, f_name), 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    if 'questions' in data:
                        for q in data['questions']:
                            q['source_file'] = f_name
                            q['subject'] = data.get('subject', 'Unknown')
                            questions.append(q)
    return questions

MCQ_DATA = None
SUBJ_DATA = None

@mocktest_bp.route('/subjects', methods=['GET'])
def get_mock_subjects():
    user = get_user_from_token(request.headers.get('Authorization'))
    if not user:
        return jsonify({"error": "Unauthorized"}), 401
    
    from app.models.models import UserSubject
    subs = UserSubject.query.filter_by(user_id=user.id).all()
    
    pattern = load_pattern(user.exam_target, user.province)
    all_subjects = []
    
    # Handle PPSC sections
    if user.exam_target == 'PPSC':
        all_subjects.extend(pattern.get('sections', []))
    else:
        all_subjects.extend(pattern.get('compulsory_subjects', []))
        opt_data = pattern.get('optional_subjects', {})
        if isinstance(opt_data, dict) and 'groups' in opt_data:
            for group in opt_data.get('groups', []):
                all_subjects.extend(group.get('subjects', []))
        elif isinstance(opt_data, list):
            all_subjects.extend(opt_data)
        
    type_map = {s['id']: s.get('type', 'objective_only' if user.exam_target == 'PPSC' else 'mixed_objective_subjective') for s in all_subjects}
    
    res = []
    for s in subs:
        res.append({
            "id": s.subject_id,
            "name": s.subject_name,
            "type": type_map.get(s.subject_id, 'objective_only' if user.exam_target == 'PPSC' else 'mixed_objective_subjective')
        })
    
    # For PPSC, add the special "Mix Paper" option
    if user.exam_target == 'PPSC' and len(res) > 0:
        res.append({
            "id": "ppsc_mix_paper",
            "name": "Mix Paper (All Sections MCQs)",
            "type": "objective_only"
        })
    
    return jsonify(res), 200

@mocktest_bp.route('/generate', methods=['POST'])
def generate_mock_test():
    global MCQ_DATA, SUBJ_DATA
    user = get_user_from_token(request.headers.get('Authorization'))
    if not user:
        return jsonify({"error": "Unauthorized"}), 401
        
    data = request.json
    subject_id = data.get('subject_id')
    
    if not subject_id:
        return jsonify({"error": "Subject ID is required"}), 400
        
    pattern = load_pattern(user.exam_target, user.province)
    
    # Special handling for PPSC Mix Paper
    if user.exam_target == 'PPSC' and subject_id == 'ppsc_mix_paper':
        return generate_ppsc_mix_paper(user, pattern, data)
    
    # Extract all subjects from pattern
    all_subjects = []
    
    if user.exam_target == 'PPSC':
        all_subjects.extend(pattern.get('sections', []))
    else:
        all_subjects.extend(pattern.get('compulsory_subjects', []))
        opt_data = pattern.get('optional_subjects', {})
        if isinstance(opt_data, dict) and 'groups' in opt_data:
            for group in opt_data.get('groups', []):
                all_subjects.extend(group.get('subjects', []))
        elif isinstance(opt_data, list):
            # Fallback for old structure
            all_subjects.extend(opt_data)
            
    subject_pattern = None
    for sub in all_subjects:
        if sub['id'] == subject_id:
            subject_pattern = sub
            break
            
    if not subject_pattern:
        return jsonify({"error": f"Subject {subject_id} not found in pattern"}), 404
        
    if MCQ_DATA is None:
        MCQ_DATA = load_mcqs()
    if SUBJ_DATA is None:
        SUBJ_DATA = load_subjective()
        
    # Get marks and time from pattern or defaults
    exam_pattern = pattern.get('paper_pattern', {})
    obj_pattern = exam_pattern.get('objective', {"marks": 20, "time_minutes": 30})
    subj_pattern_meta = exam_pattern.get('subjective', {"marks": 80, "time_minutes": 150})
    
    # Requested paper type (if user wants specifically objective or subjective)
    requested_type = data.get('paper_type', 'all') # 'all', 'objective', 'subjective'
    default_paper_type = subject_pattern.get('type', 'objective_only' if user.exam_target == 'PPSC' else 'mixed_objective_subjective')
    if "urdu" in subject_pattern['name'].lower():
        default_paper_type = "subjective_only"
    
    # Determine which sections will actually be shown
    show_objective = (requested_type in ['all', 'objective']) and (default_paper_type in ['mixed_objective_subjective', 'objective_only'])
    show_subjective = (requested_type in ['all', 'subjective']) and (default_paper_type in ['mixed_objective_subjective', 'subjective_only'])

    # Calculate dynamic time
    total_time = 0
    if show_objective:
        total_time += obj_pattern['time_minutes']
    if show_subjective:
        total_time += subj_pattern_meta['time_minutes']
        
    # Edge case: If user forced a subjective paper on an objective-only subject (or vice versa), ensure at least some time is given
    if total_time == 0:
        total_time = obj_pattern['time_minutes'] if requested_type == 'objective' else subj_pattern_meta['time_minutes']

    generated_paper = {
        "test_id": None,
        "subject_id": subject_id,
        "subject_name": subject_pattern['name'],
        "sections": [],
        "type": requested_type,
        "total_marks": 100,
        "total_time": total_time,
        "passing_marks": 40
    }
    
    # 1. Generate Objective
    if show_objective:
        obj_marks = 100 if default_paper_type == 'objective_only' else obj_pattern['marks']
        mcq_section = {
            "type": "objective",
            "title": "Part-I (MCQs)",
            "marks": obj_marks,
            "questions": []
        }
        
        import re
        base_subject = re.sub(r'\(.*?\)', '', subject_pattern['name']).split('/')[0].strip().lower()
        
        filtered_mcqs = [q for q in MCQ_DATA if base_subject in q.get('subject', '').lower() or base_subject in q.get('topic', '').lower()]
        
        if not filtered_mcqs:
            # Try a broader search if absolutely nothing found
            filtered_mcqs = [q for q in MCQ_DATA if any(word in q.get('subject', '').lower() for word in base_subject.split())]
            
        if not filtered_mcqs:
            return jsonify({"error": f"No MCQs found for subject: {subject_pattern['name']}"}), 404
            
        # Select questions (if less than 20, take all available)
        count_to_pick = min(20, len(filtered_mcqs))
        selected_mcqs = random.sample(filtered_mcqs, count_to_pick)
        
        for idx, q in enumerate(selected_mcqs):
            mcq_section['questions'].append({
                "id": idx + 1,
                "text": q.get('question'),
                "options": q.get('options'),
                "correct": q.get('correct'),
                "explanation": q.get('explanation')
            })
            
        generated_paper['sections'].append(mcq_section)
        
    # 2. Generate Subjective
    if show_subjective:
        subj_marks = 100 if default_paper_type == 'subjective_only' or requested_type == 'subjective' else subj_pattern_meta.get('marks', 80)
        subj_section = {
            "type": "subjective",
            "title": "Part-II (Subjective)",
            "marks": subj_marks,
            "questions": []
        }
        
        import re
        base_subject = re.sub(r'\(.*?\)', '', subject_pattern['name']).split('/')[0].strip().lower()
        
        filtered_subj = [
            q for q in SUBJ_DATA 
            if base_subject in q.get('subject', '').lower() or 
               base_subject in q.get('source_file', '').lower() or
               subject_id.split('_')[0].lower() in q.get('source_file', '').lower()
        ]
        
        if not filtered_subj:
            return jsonify({"error": f"No subjective questions found for subject: {subject_pattern['name']}"}), 404
            
        count = min(7, len(filtered_subj))
        selected_subj = random.sample(filtered_subj, count)
        
        for idx, q in enumerate(selected_subj):
            subj_section['questions'].append({
                "id": idx + 1,
                "text": q.get('question_text', q.get('question', '')),
                "marks": q.get('marks', 20)
            })
            
        generated_paper['sections'].append(subj_section)
        
    try:
        new_test = MockTest(
            user_id=user.id,
            exam_target=user.exam_target or "CSS", # Fallback if not set
            paper_data=json.dumps(generated_paper)
        )
        db.session.add(new_test)
        db.session.commit()
        
        generated_paper['test_id'] = new_test.id
        return jsonify(generated_paper), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": f"Database error during generation: {str(e)}"}), 500

def generate_ppsc_mix_paper(user, pattern, data):
    """Generate a PPSC mix paper with MCQs from all sections"""
    global MCQ_DATA
    
    if MCQ_DATA is None:
        MCQ_DATA = load_mcqs()
    
    requested_type = data.get('paper_type', 'objective')
    
    # Get PPSC pattern metadata
    paper_pattern = pattern.get('paper_pattern', {})
    total_mcqs = paper_pattern.get('total_mcqs', 100)
    total_marks = paper_pattern.get('total_marks', 100)
    time_minutes = paper_pattern.get('time_minutes', 90)
    
    generated_paper = {
        "test_id": None,
        "subject_id": "ppsc_mix_paper",
        "subject_name": "Mix Paper - All Sections MCQs",
        "sections": [],
        "type": "objective",
        "total_marks": total_marks,
        "total_time": time_minutes,
        "passing_marks": 40
    }
    
    # Get all sections
    sections = pattern.get('sections', [])
    
    # Collect MCQs from all sections proportionally
    section_mcq_distribution = {}
    total_questions_distributed = 0
    
    for section in sections:
        section_mcqs = section.get('mcqs', 0)
        section_mcq_distribution[section['id']] = {
            'name': section['name'],
            'requested_mcqs': section_mcqs,
            'questions': []
        }
        total_questions_distributed += section_mcqs
    
    # Generate MCQs for each section
    for section_id, section_info in section_mcq_distribution.items():
        section_name = section_info['name']
        requested_count = section_info['requested_mcqs']
        
        # Filter MCQs by section
        section_name_lower = section_name.lower()
        filtered_mcqs = [q for q in MCQ_DATA if section_name_lower in q.get('subject', '').lower()]
        
        # If not enough MCQs found, get all available
        if len(filtered_mcqs) < requested_count:
            filtered_mcqs = MCQ_DATA
        
        # Select random MCQs
        selected_count = min(requested_count, len(filtered_mcqs))
        selected_mcqs = random.sample(filtered_mcqs, selected_count) if filtered_mcqs else []
        
        for idx, q in enumerate(selected_mcqs):
            section_info['questions'].append({
                "id": idx + 1,
                "text": q.get('question'),
                "options": q.get('options'),
                "correct": q.get('correct'),
                "explanation": q.get('explanation')
            })
        
        # Add section to paper
        mcq_section = {
            "type": "objective",
            "title": f"{section_name}",
            "marks": section_info['requested_mcqs'],
            "questions": section_info['questions']
        }
        generated_paper['sections'].append(mcq_section)
    
    try:
        new_test = MockTest(
            user_id=user.id,
            exam_target="PPSC",
            paper_data=json.dumps(generated_paper)
        )
        db.session.add(new_test)
        db.session.commit()
        
        generated_paper['test_id'] = new_test.id
        return jsonify(generated_paper), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": f"Database error during generation: {str(e)}"}), 500

@mocktest_bp.route('/submit', methods=['POST'])
def submit_mock_test():
    user = get_user_from_token(request.headers.get('Authorization'))
    if not user:
        return jsonify({"error": "Unauthorized"}), 401
        
    data = request.json
    test_id = data.get('test_id')
    score_objective = data.get('score_objective')
    user_answers = data.get('user_answers') # JSON string or dict
    
    try:
        test = MockTest.query.filter_by(id=test_id, user_id=user.id).first()
        if not test:
            return jsonify({"error": f"Test ID {test_id} not found in your records."}), 404
            
        test.score_objective = score_objective
        if user_answers:
            test.user_answers = json.dumps(user_answers) if isinstance(user_answers, dict) else user_answers
            
        # Log performance for dashboard
        try:
            paper_data = json.loads(test.paper_data)
            # Find the objective section to get its max marks
            obj_sec = next((s for s in paper_data.get('sections', []) if s['type'] == 'objective'), None)
            max_obj_marks = obj_sec['marks'] if obj_sec else 100
            
            log = PerformanceLog(
                user_id=user.id,
                topic_id=f"Mock MCQ: {paper_data.get('subject_name', 'General')}",
                subject_id=paper_data.get('subject_name', 'General'),
                score=float(score_objective) / max_obj_marks if max_obj_marks > 0 else 0,
                question_type='MCQ'
            )
            db.session.add(log)
        except Exception as log_err:
            print(f"Logging error: {log_err}")

        db.session.commit()
        return jsonify({"message": "Objective score and answers saved"}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": f"Database error during submission: {str(e)}"}), 500

@mocktest_bp.route('/evaluate-ai', methods=['POST'])
def evaluate_ai():
    user = get_user_from_token(request.headers.get('Authorization'))
    if not user:
        return jsonify({"error": "Unauthorized"}), 401
        
    data = request.json
    test_id = data.get('test_id')
    
    test = MockTest.query.filter_by(id=test_id, user_id=user.id).first()
    if not test:
        return jsonify({"error": "Test not found"}), 404
        
    if not test.user_answers:
        return jsonify({"error": "No answers found for this test"}), 400
        
    from app.services.evaluator_service import AnswerEvaluator
    evaluator = AnswerEvaluator()
    
    paper_data = json.loads(test.paper_data)
    user_answers = json.loads(test.user_answers)
    
    results = []
    total_subj_score = 0
    
    # Evaluate each subjective question
    for sec in paper_data.get('sections', []):
        if sec['type'] == 'subjective':
            for q in sec['questions']:
                q_id = str(q['id'])
                ans = user_answers.get(q_id, '')
                if ans:
                    eval_text = evaluator.evaluate(q['text'], ans)
                    results.append({
                        "question_id": q['id'],
                        "question_text": q['text'],
                        "evaluation": eval_text
                    })
                    # Extract marks if possible (Format: PREDICTED MARKS: X/20)
                    try:
                        if "PREDICTED MARKS:" in eval_text:
                            marks_str = eval_text.split("PREDICTED MARKS:")[1].split("/")[0].strip()
                            total_subj_score += float(marks_str)
                    except:
                        pass
    
    test.ai_feedback = json.dumps(results)
    test.score_subjective = total_subj_score
    
    # Log performance for dashboard
    try:
        log = PerformanceLog(
            user_id=user.id,
            topic_id=f"Mock Subj: {paper_data.get('subject_name', 'General')}",
            subject_id=paper_data.get('subject_name', 'General'),
            score=float(total_subj_score) / paper_data.get('total_marks', 100) if paper_data.get('total_marks', 100) > 0 else 0,
            question_type='Subjective'
        )
        db.session.add(log)
    except Exception as log_err:
        print(f"Logging error: {log_err}")
        
    db.session.commit()
    
    return jsonify({
        "message": "AI Evaluation complete",
        "results": results,
        "total_subjective_score": total_subj_score
    }), 200

@mocktest_bp.route('/details/<int:test_id>', methods=['GET'])
def get_test_details(test_id):
    user = get_user_from_token(request.headers.get('Authorization'))
    if not user:
        return jsonify({"error": "Unauthorized"}), 401
        
    test = MockTest.query.filter_by(id=test_id, user_id=user.id).first()
    if not test:
        return jsonify({"error": "Test not found"}), 404
        
    return jsonify({
        "id": test.id,
        "paper_data": json.loads(test.paper_data),
        "user_answers": json.loads(test.user_answers) if test.user_answers else {},
        "ai_feedback": json.loads(test.ai_feedback) if test.ai_feedback else None,
        "score_objective": test.score_objective,
        "score_subjective": test.score_subjective
    }), 200

@mocktest_bp.route('/evaluate', methods=['POST'])
def evaluate_mock_test():
    user = get_user_from_token(request.headers.get('Authorization'))
    if not user:
        return jsonify({"error": "Unauthorized"}), 401
        
    data = request.json
    test_id = data.get('test_id')
    score_subjective = data.get('score_subjective')
    
    test = MockTest.query.filter_by(id=test_id, user_id=user.id).first()
    if not test:
        return jsonify({"error": "Test not found"}), 404
    # Save result to DB
    test.score_subjective = total_score
    test.ai_feedback = json.dumps(results_list)
    
    # Log performance for dashboard (Weak Topic Detection)
    from app.models.models import PerformanceLog
    log = PerformanceLog(
        user_id=user.id,
        topic_id="Mock Final",
        subject_id=test_data.get('subject_name', 'General'),
        score=total_score / 20.0, # Normalize to 0-1
        question_type='Subjective'
    )
    db.session.add(log)
    
    db.session.commit()
    return jsonify({"message": "Subjective score saved"}), 200

@mocktest_bp.route('/result/<int:test_id>', methods=['GET'])
def get_mock_result(test_id):
    user = get_user_from_token(request.headers.get('Authorization'))
    if not user:
        return jsonify({"error": "Unauthorized"}), 401
        
    test = MockTest.query.filter_by(id=test_id, user_id=user.id).first()
    if not test:
        return jsonify({"error": "Test not found"}), 404
        
    return jsonify({
        "id": test.id,
        "paper_data": json.loads(test.paper_data),
        "user_answers": json.loads(test.user_answers) if test.user_answers else {},
        "score_objective": test.score_objective,
        "score_subjective": test.score_subjective,
        "ai_feedback": test.ai_feedback, # This could be JSON or text
        "created_at": test.created_at.isoformat()
    }), 200

@mocktest_bp.route('/history', methods=['GET'])
def get_mock_history():
    user = get_user_from_token(request.headers.get('Authorization'))
    if not user:
        return jsonify({"error": "Unauthorized"}), 401
        
    tests = MockTest.query.filter_by(user_id=user.id).order_by(MockTest.created_at.desc()).all()
    res = []
    for t in tests:
        try:
            paper = json.loads(t.paper_data)
            has_objective = any(sec['type'] == 'objective' for sec in paper.get('sections', [])) if 'sections' in paper else False
            res.append({
                "id": t.id,
                "subject_name": paper.get('subject_name', paper.get('subject_id', 'Unknown')),
                "created_at": t.created_at.isoformat(),
                "score_objective": t.score_objective,
                "score_subjective": t.score_subjective,
                "has_objective": has_objective,
                "is_evaluated": t.score_subjective is not None
            })
        except Exception as e:
            print(f"Error parsing test {t.id}: {e}")
            continue
    return jsonify(res), 200

@mocktest_bp.route('/pending', methods=['GET'])
def get_pending_evaluations():
    user = get_user_from_token(request.headers.get('Authorization'))
    if not user:
        return jsonify({"error": "Unauthorized"}), 401
        
    # Find tests that have subjective part but no score_subjective
    tests = MockTest.query.filter_by(user_id=user.id, score_subjective=None).all()
    res = []
    for t in tests:
        paper = json.loads(t.paper_data)
        has_subjective = any(sec['type'] == 'subjective' for sec in paper.get('sections', []))
        if has_subjective:
            res.append({
                "id": t.id,
                "subject_name": paper.get('subject_name'),
                "created_at": t.created_at.isoformat()
            })
    return jsonify(res), 200
