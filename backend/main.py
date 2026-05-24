from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
from app.models.models import db, User, UserProgress, PerformanceLog, Essay, ScheduleTask, MockTest, UserSubject
from app.services.essay_service import EssayGenerator
from app.services.evaluator_service import AnswerEvaluator
from app.services.vector_store import VectorStore
from app.services.openai_service import OpenAIService
from app.api.routers.auth import auth_bp
from app.api.routers.prep import prep_bp
from app.api.routers.mocktest import mocktest_bp
import requests
import os
from dotenv import load_dotenv

load_dotenv()
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
OLLAMA_URL = "http://localhost:11434/api/chat"
OLLAMA_MODEL = "mistral:7b-instruct"

app = Flask(__name__, 
            template_folder='../frontend', 
            static_folder='../frontend/assets',
            static_url_path='/assets')
CORS(app)

# Path Discovery
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ROOT_DIR = os.path.dirname(BASE_DIR)

# Automatic Ollama Check & Startup
def ensure_ollama():
    import subprocess
    import requests
    import time
    try:
        # Check if Ollama is responsive
        requests.get("http://localhost:11434/api/tags", timeout=2)
        print("✅ Ollama is already running.")
    except:
        print("⏳ Ollama not detected. Attempting to start Ollama server...")
        try:
            # Start Ollama in a separate process
            subprocess.Popen(["ollama", "serve"], 
                             stdout=subprocess.DEVNULL, 
                             stderr=subprocess.DEVNULL,
                             creationflags=subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0)
            time.sleep(5) # Give it time to bind to port
            print("✅ Ollama startup command sent.")
        except Exception as e:
            print(f"❌ Failed to auto-start Ollama: {e}")

ensure_ollama()

# Database Configuration
app.config['SQLALCHEMY_DATABASE_URI'] = f"sqlite:///{os.path.join(ROOT_DIR, 'portal.db')}"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db.init_app(app)

# Initialize Services (RAG vector store shared across all services)
vs = VectorStore(db_path=os.path.join(ROOT_DIR, "chroma_db_v2"))
essay_gen = EssayGenerator()
evaluator = AnswerEvaluator()
mentor_chat = OpenAIService()

app.register_blueprint(auth_bp, url_prefix='/api/auth')
app.register_blueprint(prep_bp, url_prefix='/api/prep')
app.register_blueprint(mocktest_bp, url_prefix='/api/mocktest')

# ─────────────────────────────────────────────
# PAGES
# ─────────────────────────────────────────────

@app.route('/')
def home_page():
    return render_template('Index/index.html')

@app.route('/about')
def about_page():
    return render_template('Index/about.html')

@app.route('/past-papers')
def past_papers_landing():
    return render_template('Index/past-papers.html')

@app.route('/login')
def login_page():
    return render_template('login.html')

@app.route('/dashboard')
def dashboard():
    return render_template('dashboard.html')

@app.route('/preparation')
def preparation():
    return render_template('preparation.html')

@app.route('/syllabus-tracker')
def syllabus_tracker():
    return render_template('syllabus-tracker.html')

@app.route('/exam-hall')
def exam_hall():
    return render_template('exam-hall.html')

@app.route('/mock-tests')
def mock_tests():
    return render_template('mock-tests.html')

@app.route('/essay-studio')
def essay_studio():
    return render_template('essay-studio.html')

@app.route('/answer-evaluator')
def answer_evaluator():
    return render_template('answer-evaluator.html')

@app.route('/past-papers-repo')
def past_papers_repo():
    return render_template('past-papers.html')

@app.route('/profile')
def profile():
    return render_template('profile.html')

@app.route('/view-results.html')
def view_results():
    return render_template('view-results.html')

@app.route('/exam.html')
def exam_page():
    return render_template('exam.html')

# ─────────────────────────────────────────────
# API: CHAT (Mistral via Ollama + RAG)
# ─────────────────────────────────────────────

@app.route('/api/chat', methods=['POST'])
def chat():
    data = request.json
    query = data.get('query', '').strip()
    if not query:
        return jsonify({"error": "Query is required"}), 400

    # Retrieve relevant context from ChromaDB
    results = vs.search(query, n_results=3)
    context = "\n\n".join(results.get('documents', [[]])[0])

    # Build a grounded prompt for Phi-3
    prompt = (
        f"You are an AI mentor for CSS and PPSC exam preparation. "
        f"Answer the student's question using ONLY the provided context. "
        f"If the context does not contain the answer, say so honestly.\n\n"
        f"CONTEXT:\n{context[:1500]}\n\n"
        f"STUDENT QUESTION: {query}\n\n"
        f"ANSWER:"
    )

    try:
        payload = {
            "model": OLLAMA_MODEL,
            "messages": [
                {"role": "system", "content": "You are an AI mentor for CSS and PPSC exam preparation. Answer using only the provided context."},
                {"role": "user", "content": prompt}
            ],
            "stream": False,
            "options": {"temperature": 0.5, "num_ctx": 2048, "num_predict": 350}
        }
        resp = requests.post(OLLAMA_URL, json=payload, timeout=300)
        resp.raise_for_status()
        answer = resp.json().get("message", {}).get("content", "No response from model.")
    except requests.exceptions.ConnectionError:
        answer = "⚠️ Ollama is not running. Please start it with: `ollama serve`"
    except Exception as e:
        answer = f"[Chat Error: {e}]"

    return jsonify({"answer": answer, "context_sources": results.get('metadatas', [[]])[0]})

# ─────────────────────────────────────────────
# API: EXPERT MENTOR CHAT (Mistral)
# ─────────────────────────────────────────────

@app.route('/api/mentor/chat', methods=['POST'])
def mentor_chat_api():
    data = request.json
    query = data.get('query', '').strip()
    history = data.get('history', [])
    
    if not query:
        return jsonify({"error": "Query is required"}), 400
        
    answer = mentor_chat.chat_expert(query, history)
    return jsonify({"answer": answer})

# ─────────────────────────────────────────────
# API: ESSAY GENERATION
# ─────────────────────────────────────────────

@app.route('/api/generate-essay', methods=['POST'])
def generate_essay():
    data = request.json
    topic = data.get('topic', '').strip()
    if not topic:
        return jsonify({"error": "Topic is required"}), 400

    content = essay_gen.generate_essay(topic)

    # Persist essay to database
    new_essay = Essay(topic=topic, content=content)
    db.session.add(new_essay)
    db.session.commit()

    return jsonify({"topic": topic, "content": content, "word_count": len(content.split())})

# ─────────────────────────────────────────────
# API: ANSWER EVALUATION
# ─────────────────────────────────────────────

@app.route('/api/evaluate', methods=['POST'])
def evaluate():
    data = request.json
    question = data.get('question', '').strip()
    answer = data.get('answer', '').strip()
    if not question or not answer:
        return jsonify({"error": "Both question and answer are required"}), 400

    result = evaluator.evaluate(question, answer)

    # Log performance to DB for weak topic detection
    auth_header = request.headers.get('Authorization')
    user_id = None
    if auth_header and auth_header.startswith('Bearer '):
        try:
            token = auth_header.split(' ')[1]
            payload = jwt.decode(token, JWT_SECRET, algorithms=["HS256"])
            user_id = payload['user_id']
        except:
            pass

    topic_id = data.get('topic_id', 'unknown')
    subject_id = data.get('subject_id', 'unknown')
    try:
        score = float(data.get('score', 0.5))
    except ValueError:
        score = 0.5
        
    log = PerformanceLog(user_id=user_id, topic_id=topic_id, subject_id=subject_id, score=score, question_type='Subjective')
    db.session.add(log)
    db.session.commit()

    return jsonify({"evaluation": result})

# ─────────────────────────────────────────────
# API: SYLLABUS TRACKER + WEAK TOPIC DETECTION
# ─────────────────────────────────────────────

@app.route('/api/tracker', methods=['GET'])
def get_tracker():
    from flask import request
    import jwt
    from app.api.routers.auth import JWT_SECRET
    
    # Try to get user from token
    auth_header = request.headers.get('Authorization')
    user_id = None
    if auth_header and auth_header.startswith('Bearer '):
        token = auth_header.split(' ')[1]
        try:
            payload = jwt.decode(token, JWT_SECRET, algorithms=["HS256"])
            user_id = payload['user_id']
        except:
            pass

    # Calculate completion from ScheduleTask if user_id is available
    if user_id:
        total_tasks = ScheduleTask.query.filter_by(user_id=user_id).count()
        completed_tasks = ScheduleTask.query.filter_by(user_id=user_id, is_completed=True).count()
        overall = (completed_tasks / total_tasks * 100) if total_tasks > 0 else 0
        
        # Still get weak topics from performance log
        weak_topics = (db.session.query(PerformanceLog.topic_id, PerformanceLog.subject_id)
                       .filter(PerformanceLog.user_id == user_id)
                       .filter(PerformanceLog.score < 0.5)
                       .distinct()
                       .limit(5)
                       .all())
    else:
        # Fallback for anonymous or failed auth
        overall = 0
        weak_topics = []

    weak_topic_list = [{"topic": t[0], "subject": t[1]} for t in weak_topics]

    return jsonify({
        "overall_completion": round(overall, 1),
        "weak_topics": weak_topic_list
    })

# ─────────────────────────────────────────────
# API: OFFLINE NOTES SEARCH
# ─────────────────────────────────────────────

@app.route('/api/notes', methods=['GET'])
def get_notes():
    query = request.args.get('q', '').strip()
    if not query:
        return jsonify({"error": "Query parameter 'q' is required"}), 400
    results = vs.search(query, n_results=5)
    docs = results.get('documents', [[]])[0]
    metas = results.get('metadatas', [[]])[0]
    notes = [{"content": d, "meta": m} for d, m in zip(docs, metas)]
    return jsonify({"notes": notes})

# ─────────────────────────────────────────────
# API: PAST PAPERS
# ─────────────────────────────────────────────

@app.route('/api/past-papers', methods=['GET'])
def get_past_papers():
    import os
    import re
    exam_type_query = request.args.get('exam_type')
    
    directories = []
    if exam_type_query == 'CSS':
        directories.append(("CSS", os.path.join(ROOT_DIR, "CSS_Banks")))
    elif exam_type_query == 'PMS':
        directories.append(("PMS", os.path.join(ROOT_DIR, "PMS")))
    else:
        directories.append(("CSS", os.path.join(ROOT_DIR, "CSS_Banks")))
        directories.append(("PMS", os.path.join(ROOT_DIR, "PMS")))
        
    papers = []
    for exam_type, folder in directories:
        if not os.path.exists(folder):
            continue
        for filename in os.listdir(folder):
            if filename.endswith(".pdf"):
                # Try to extract year (4 digits)
                year_match = re.search(r'(20\d{2})', filename)
                year = year_match.group(1) if year_match else "Unknown"
                
                # Clean subject name
                name = filename.replace(".pdf", "")
                name = re.sub(r'20\d{2}', '', name)
                name = name.replace("-past-paper", "").replace("-css-", "").replace("css-", "").replace("-", " ").replace("_", " ")
                name = name.replace("past paper", "").replace("PMS", "").strip().title()
                
                papers.append({
                    "id": filename,
                    "filename": filename,
                    "subject": name or "General",
                    "year": year,
                    "exam_type": exam_type
                })
                
    return jsonify(papers)

@app.route('/api/past-papers/view/<path:filename>')
def view_past_paper(filename):
    from flask import send_from_directory
    import os
    
    css_path = os.path.join(ROOT_DIR, "CSS_Banks")
    if os.path.exists(os.path.join(css_path, filename)):
        return send_from_directory(css_path, filename)
        
    pms_path = os.path.join(ROOT_DIR, "PMS")
    if os.path.exists(os.path.join(pms_path, filename)):
        return send_from_directory(pms_path, filename)
        
    return "File not found", 404

# ─────────────────────────────────────────────
# STARTUP
# ─────────────────────────────────────────────

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    print("✅  PPSC & CSS AI Portal running at http://127.0.0.1:5000")
    app.run(debug=True, port=5000)
