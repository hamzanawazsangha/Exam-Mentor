from flask import Blueprint, request, jsonify
from werkzeug.security import generate_password_hash, check_password_hash
import jwt
import datetime
import random
import string
import os
from dotenv import load_dotenv
import smtplib
from email.mime.text import MIMEText

from app.models.models import db, User, PendingRegistration

base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
env_path = os.path.join(base_dir, '..', '.env')
load_dotenv(env_path)

auth_bp = Blueprint('auth', __name__)

JWT_SECRET = os.getenv('JWT_SECRET', 'exammentor_secure_jwt_secret_key_2026_pk_css_pms_8899')

def send_verification_email(to_email, code):
    try:
        email_body = f"""
Welcome to ExamMentor: PPSC & CSS Preparation and Guidance Portal!

Hello Aspirant,

You have taken the first step towards a successful career in civil services. To secure your account and access our AI-powered guidance tools, please use the verification code below:

Verification Code: {code}

Next Steps:
1. Enter this code in your portal to activate your account.
2. Complete your profile to receive personalized syllabus tracking.
3. Start your first mock test or explore the Essay Studio.

ExamMentor is designed to provide you with RAG-based precision learning and real-time LLM feedback. We are committed to your success in CSS, PMS, and PPSC examinations.

If you did not request this code, please ignore this email or contact our support team.

Best Regards,
The ExamMentor Team
Guidance | Preparation | Success
"""
        msg = MIMEText(email_body)
        msg['Subject'] = 'Verify Your ExamMentor Account'
        msg['From'] = f"ExamMentor Portal <{os.getenv('SMTP_FROM_EMAIL')}>"
        msg['To'] = to_email

        server = smtplib.SMTP(os.getenv('SMTP_HOST'), int(os.getenv('SMTP_PORT', 587)))
        if os.getenv('SMTP_USE_TLS', 'true').lower() == 'true':
            server.starttls()
        
        server.login(os.getenv('SMTP_USERNAME'), os.getenv('SMTP_PASSWORD'))
        server.send_message(msg)
        server.quit()
        return True
    except Exception as e:
        print(f"Failed to send email: {e}")
        return False

@auth_bp.route('/register', methods=['POST'])
def register():
    data = request.json
    email = data.get('email')
    password = data.get('password')
    first_name = data.get('first_name')
    last_name = data.get('last_name')
    
    if not email or not password or not first_name or not last_name:
        return jsonify({"error": "All fields are required"}), 400
    
    # Check if email is already registered in User table
    if User.query.filter_by(email=email).first():
        return jsonify({"error": "Email already registered"}), 400
    
    # Check if email already has a pending registration
    pending = PendingRegistration.query.filter_by(email=email).first()
    if pending:
        # Delete old pending registration and create new one
        db.session.delete(pending)
        db.session.commit()
    
    # Generate verification code
    code = ''.join(random.choices(string.digits, k=6))
    
    # Create pending registration (NOT a user yet)
    pending_user = PendingRegistration(
        email=email,
        password_hash=generate_password_hash(password),
        first_name=first_name,
        last_name=last_name,
        verification_code=code
    )
    
    db.session.add(pending_user)
    db.session.commit()
    
    # Send verification email
    send_verification_email(email, code)
    
    return jsonify({"message": "Registration successful. Please verify your email."}), 201

@auth_bp.route('/verify-email', methods=['POST'])
def verify_email():
    data = request.json
    email = data.get('email')
    code = data.get('code')
    
    # Check if there's a pending registration
    pending = PendingRegistration.query.filter_by(email=email).first()
    if not pending:
        return jsonify({"error": "No pending registration found. Please register first"}), 404
    
    # Verify the code
    if pending.verification_code != code:
        return jsonify({"error": "Invalid verification code"}), 400
    
    # Create the actual user account
    new_user = User(
        email=pending.email,
        password_hash=pending.password_hash,
        first_name=pending.first_name,
        last_name=pending.last_name,
        is_verified=True  # User is verified upon creation
    )
    
    db.session.add(new_user)
    
    # Delete the pending registration
    db.session.delete(pending)
    
    db.session.commit()
    
    return jsonify({"message": "Email verified successfully. Your account is now active."}), 200

@auth_bp.route('/login', methods=['POST'])
def login():
    data = request.json
    email = data.get('email')
    password = data.get('password')
    
    user = User.query.filter_by(email=email).first()
    if not user or not check_password_hash(user.password_hash, password):
        return jsonify({"error": "Invalid email or password"}), 401
        
    if not user.is_verified:
        return jsonify({"error": "Please verify your email first"}), 401
        
    token = jwt.encode({
        'user_id': user.id,
        'exp': datetime.datetime.utcnow() + datetime.timedelta(days=7)
    }, JWT_SECRET, algorithm="HS256")
    
    return jsonify({
        "token": token,
        "user": {
            "id": user.id,
            "email": user.email,
            "first_name": user.first_name,
            "last_name": user.last_name,
            "photo_url": user.photo_url,
            "degree": user.degree,
            "exam_target": user.exam_target,
            "exam_date": user.exam_date.isoformat() if user.exam_date else None
        }
    }), 200

@auth_bp.route('/forget-password', methods=['POST'])
def forget_password():
    data = request.json
    email = data.get('email')
    user = User.query.filter_by(email=email).first()
    
    if not user:
        return jsonify({"error": "User not found"}), 404
        
    code = ''.join(random.choices(string.digits, k=6))
    user.verification_code = code
    db.session.commit()
    
    send_verification_email(email, code)
    return jsonify({"message": "Reset code sent to email"}), 200

@auth_bp.route('/reset-password', methods=['POST'])
def reset_password():
    data = request.json
    email = data.get('email')
    code = data.get('code')
    new_password = data.get('new_password')
    
    user = User.query.filter_by(email=email).first()
    if not user or user.verification_code != code:
        return jsonify({"error": "Invalid code or user"}), 400
        
    user.password_hash = generate_password_hash(new_password)
    user.verification_code = None
    db.session.commit()
    
    return jsonify({"message": "Password reset successful"}), 200

@auth_bp.route('/profile', methods=['POST'])
def update_profile():
    auth_header = request.headers.get('Authorization')
    if not auth_header or not auth_header.startswith('Bearer '):
        return jsonify({"error": "Missing token"}), 401
        
    token = auth_header.split(' ')[1]
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=["HS256"])
        user = User.query.get(payload['user_id'])
        if not user:
            raise ValueError()
    except Exception:
        return jsonify({"error": "Invalid token"}), 401
        
    data = request.json
    user.first_name = data.get('first_name', user.first_name)
    user.last_name = data.get('last_name', user.last_name)
    user.age = data.get('age', user.age)
    user.degree = data.get('degree', user.degree)
    user.photo_url = data.get('photo_url', user.photo_url)
    
    db.session.commit()
    
    return jsonify({"message": "Profile updated successfully", "user": {
        "first_name": user.first_name,
        "last_name": user.last_name,
        "age": user.age,
        "degree": user.degree,
        "photo_url": user.photo_url
    }}), 200

@auth_bp.route('/profile/photo', methods=['POST'])
def upload_photo():
    auth_header = request.headers.get('Authorization')
    if not auth_header or not auth_header.startswith('Bearer '):
        return jsonify({"error": "Missing token"}), 401
        
    token = auth_header.split(' ')[1]
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=["HS256"])
        user = User.query.get(payload['user_id'])
    except Exception:
        return jsonify({"error": "Invalid token"}), 401

    if 'photo' not in request.files:
        return jsonify({"error": "No file uploaded"}), 400
        
    file = request.files['photo']
    if file.filename == '':
        return jsonify({"error": "No file selected"}), 400
        
    if file:
        from werkzeug.utils import secure_filename
        filename = secure_filename(f"user_{user.id}_{file.filename}")
        upload_folder = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))), 'frontend', 'assets', 'uploads')
        if not os.path.exists(upload_folder):
            os.makedirs(upload_folder)
        
        file.save(os.path.join(upload_folder, filename))
        user.photo_url = f"/assets/uploads/{filename}"
        db.session.commit()
        
        return jsonify({"message": "Photo uploaded", "photo_url": user.photo_url}), 200
