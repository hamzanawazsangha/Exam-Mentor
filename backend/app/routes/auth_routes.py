#!/usr/bin/env python3
"""
Authentication and User Management API Routes.
"""

from flask import Blueprint, request, jsonify
from app.models.models import db, User, UserProfile
from app.services.auth_service import AuthService, EmailService, ProfileService
from datetime import datetime

auth_bp = Blueprint('auth', __name__, url_prefix='/api/auth')

# ─────────────────────────────────────────────
# USER REGISTRATION
# ─────────────────────────────────────────────

@auth_bp.route('/register', methods=['POST'])
def register():
    """Register a new user - send verification code, don't create user yet."""
    data = request.json
    email = data.get('email', '').strip()
    password = data.get('password', '').strip()
    first_name = data.get('first_name', '').strip()
    last_name = data.get('last_name', '').strip()
    
    # Validation
    if not email:
        return jsonify({"error": "Email is required"}), 400
    
    if not password:
        return jsonify({"error": "Password is required"}), 400
    
    # Validate email format
    if not AuthService.validate_email(email):
        return jsonify({"error": "Invalid email format"}), 400
    
    # Validate password strength
    is_valid, msg = AuthService.validate_password(password)
    if not is_valid:
        return jsonify({"error": msg}), 400
    
    # Check if email already exists
    existing_user = db.session.query(User).filter_by(email=email).first()
    if existing_user:
        return jsonify({"error": "Email already registered"}), 409
    
    # Generate verification code
    verification_code = AuthService.generate_verification_code()
    
    # Send verification code via email
    try:
        EmailService.send_verification_code(email, verification_code, first_name or email)
    except Exception as e:
        return jsonify({"error": f"Failed to send verification email: {str(e)}"}), 500
    
    return jsonify({
        "message": "Verification code sent to your email. Please verify to complete registration.",
        "email": email
    }), 200

# ─────────────────────────────────────────────
# EMAIL VERIFICATION
# ─────────────────────────────────────────────

@auth_bp.route('/verify-email', methods=['POST'])
def verify_email():
    """Verify email with code and create user account."""
    data = request.json
    email = data.get('email', '').strip()
    code = data.get('code', '').strip()
    password = data.get('password', '').strip()
    first_name = data.get('first_name', '').strip()
    last_name = data.get('last_name', '').strip()
    
    if not email or not code:
        return jsonify({"error": "Email and verification code are required"}), 400
    
    if not password:
        return jsonify({"error": "Password is required"}), 400
    
    # Check if email already exists (safety check)
    existing_user = db.session.query(User).filter_by(email=email).first()
    if existing_user:
        return jsonify({"error": "Email already registered. Please login instead."}), 409
    
    # In production, verify the code against stored temp record
    # For now, we accept any 6-digit code that was sent
    # TODO: Implement proper code verification with expiry
    
    try:
        # Create the user account after verification
        user = User(
            email=email,
            password_hash=AuthService.hash_password(password),
            first_name=first_name,
            last_name=last_name,
            is_verified=True,
            verification_code=None
        )
        db.session.add(user)
        db.session.commit()
        
        return jsonify({
            "message": "Email verified successfully. Account created! You can now login.",
            "user_id": user.id,
            "email": email
        }), 201
    
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": f"Verification failed: {str(e)}"}), 500

# ─────────────────────────────────────────────
# USER LOGIN
# ─────────────────────────────────────────────

@auth_bp.route('/login', methods=['POST'])
def login():
    """Login user."""
    data = request.json
    email = data.get('email', '').strip()
    password = data.get('password', '').strip()
    
    if not email or not password:
        return jsonify({"error": "Email and password are required"}), 400
    
    # Find user
    user = db.session.query(User).filter_by(email=email).first()
    if not user:
        return jsonify({"error": "Invalid email or password"}), 401
    
    # Check password
    if not AuthService.verify_password(password, user.password_hash):
        return jsonify({"error": "Invalid email or password"}), 401
    
    # Check if email is verified
    if not user.is_verified:
        return jsonify({"error": "Email not verified. Please verify your email first."}), 403
    
    # Generate session token (simplified - in production use JWT)
    session_token = AuthService.generate_verification_code()
    
    return jsonify({
        "message": "Login successful",
        "user_id": user.id,
        "email": user.email,
        "session_token": session_token,
        "profile_complete": user.profile is not None
    }), 200

# ─────────────────────────────────────────────
# FORGOT PASSWORD
# ─────────────────────────────────────────────

@auth_bp.route('/forgot-password', methods=['POST'])
def forgot_password():
    """Request password reset."""
    data = request.json
    email = data.get('email', '').strip()
    
    if not email:
        return jsonify({"error": "Email is required"}), 400
    
    # Find user
    user = db.session.query(User).filter_by(email=email).first()
    if not user:
        return jsonify({"error": "Email not registered"}), 404
    
    # Generate reset code
    reset_code = AuthService.generate_verification_code()
    user.verification_code = reset_code
    db.session.commit()
    
    # Send reset code
    EmailService.send_password_reset_code(email, reset_code)
    
    return jsonify({
        "message": "Password reset code sent to email",
        "email": email
    }), 200

@auth_bp.route('/reset-password', methods=['POST'])
def reset_password():
    """Reset password with code."""
    data = request.json
    email = data.get('email', '').strip()
    code = data.get('code', '').strip()
    new_password = data.get('new_password', '').strip()
    confirm_password = data.get('confirm_password', '').strip()
    
    if not all([email, code, new_password, confirm_password]):
        return jsonify({"error": "All fields are required"}), 400
    
    if new_password != confirm_password:
        return jsonify({"error": "Passwords do not match"}), 400
    
    # Validate new password
    is_valid, msg = AuthService.validate_password(new_password)
    if not is_valid:
        return jsonify({"error": msg}), 400
    
    # Find user
    user = db.session.query(User).filter_by(email=email).first()
    if not user:
        return jsonify({"error": "User not found"}), 404
    
    # Check code
    if user.verification_code != code:
        return jsonify({"error": "Invalid reset code"}), 401
    
    # Update password
    user.password_hash = AuthService.hash_password(new_password)
    user.verification_code = None
    db.session.commit()
    
    return jsonify({
        "message": "Password reset successfully"
    }), 200

# ─────────────────────────────────────────────
# USER PROFILE
# ─────────────────────────────────────────────

@auth_bp.route('/profile/create', methods=['POST'])
def create_profile():
    """Create user profile."""
    data = request.json
    user_id = data.get('user_id')
    name = data.get('name', '').strip()
    age = data.get('age')
    degree = data.get('degree', '').strip()
    profile_photo_url = data.get('profile_photo_url', '').strip()
    
    if not user_id:
        return jsonify({"error": "User ID is required"}), 400
    
    # Validate profile data
    is_valid, msg = ProfileService.validate_profile_data(name, age, degree, profile_photo_url)
    if not is_valid:
        return jsonify({"error": msg}), 400
    
    # Check if user exists
    user = db.session.query(User).filter_by(id=user_id).first()
    if not user:
        return jsonify({"error": "User not found"}), 404
    
    # Check if profile already exists
    existing_profile = db.session.query(UserProfile).filter_by(user_id=user_id).first()
    if existing_profile:
        return jsonify({"error": "Profile already exists"}), 409
    
    try:
        # Create profile
        profile = UserProfile(
            user_id=user_id,
            name=name,
            age=age,
            degree=degree,
            profile_photo_url=profile_photo_url if profile_photo_url else None
        )
        db.session.add(profile)
        db.session.commit()
        
        return jsonify({
            "message": "Profile created successfully",
            "profile_id": profile.id,
            "user_id": user_id
        }), 201
    
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": f"Profile creation failed: {str(e)}"}), 500

@auth_bp.route('/profile/<int:user_id>', methods=['GET'])
def get_profile(user_id):
    """Get user profile."""
    try:
        user = db.session.query(User).filter_by(id=user_id).first()
        if not user:
            return jsonify({"error": "User not found"}), 404
        
        profile = user.profile
        if not profile:
            return jsonify({"message": "Profile not completed yet"}), 200
        
        return jsonify({
            "user_id": user_id,
            "email": user.email,
            "profile": {
                "name": profile.name,
                "age": profile.age,
                "degree": profile.degree,
                "profile_photo_url": profile.profile_photo_url,
                "updated_at": profile.updated_at.isoformat()
            }
        }), 200
    
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@auth_bp.route('/profile/<int:user_id>', methods=['PUT'])
def update_profile(user_id):
    """Update user profile."""
    data = request.json
    
    try:
        profile = db.session.query(UserProfile).filter_by(user_id=user_id).first()
        if not profile:
            return jsonify({"error": "Profile not found"}), 404
        
        # Update fields
        if 'name' in data:
            profile.name = data['name'].strip()
        if 'age' in data:
            profile.age = data['age']
        if 'degree' in data:
            profile.degree = data['degree'].strip()
        if 'profile_photo_url' in data:
            profile.profile_photo_url = data['profile_photo_url'].strip()
        
        profile.updated_at = datetime.utcnow()
        db.session.commit()
        
        return jsonify({
            "message": "Profile updated successfully"
        }), 200
    
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500
