import re
from datetime import datetime
from flask import Blueprint, render_template, redirect, url_for, request, flash
from flask_login import login_user, logout_user, login_required, current_user
from app.models.database import db, User, UserProfile, Setting

auth_bp = Blueprint('auth', __name__)

def is_valid_email(email):
    return re.match(r"[^@]+@[^@]+\.[^@]+", email) is not None

def is_strong_password(password):
    # Minimum 8 characters, at least one digit and one special character
    if len(password) < 8:
        return False
    if not any(char.isdigit() for char in password):
        return False
    if not any(char in "!@#$%^&*()-_=+[{]};:'\",<.>/?`~" for char in password):
        return False
    return True

@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard.index'))
        
    if request.method == 'POST':
        full_name = request.form.get('full_name', '').strip()
        email = request.form.get('email', '').strip().lower()
        phone = request.form.get('phone', '').strip()
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')
        
        # Validation
        if not full_name or not email or not password or not confirm_password:
            flash('All fields are required.', 'danger')
            return render_template('register.html')
            
        if not is_valid_email(email):
            flash('Invalid email format.', 'danger')
            return render_template('register.html')
            
        if phone and not re.match(r"^\+?[1-9]\d{1,14}$", phone.replace(" ", "").replace("-", "")):
            flash('Invalid phone number format.', 'danger')
            return render_template('register.html')
            
        if password != confirm_password:
            flash('Passwords do not match.', 'danger')
            return render_template('register.html')
            
        if not is_strong_password(password):
            flash('Password must be at least 8 characters long and contain at least one digit and one special character.', 'danger')
            return render_template('register.html')
            
        # Email uniqueness
        existing_user = User.query.filter_by(email=email).first()
        if existing_user:
            flash('Email address already registered.', 'danger')
            return render_template('register.html')
            
        # Create User
        try:
            new_user = User(
                full_name=full_name,
                email=email,
                phone=phone
            )
            new_user.set_password(password)
            db.session.add(new_user)
            db.session.flush() # gets user id
            
            # Create associated profile
            new_profile = UserProfile(user_id=new_user.id)
            db.session.add(new_profile)
            
            # Create default settings
            new_settings = Setting(user_id=new_user.id)
            db.session.add(new_settings)
            
            db.session.commit()
            
            # Log user in
            login_user(new_user)
            flash('Registration successful!', 'success')
            return redirect(url_for('dashboard.index'))
        except Exception as e:
            db.session.rollback()
            flash(f'An error occurred: {e}', 'danger')
            
    return render_template('register.html')

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard.index'))
        
    if request.method == 'POST':
        email = request.form.get('email', '').strip().lower()
        password = request.form.get('password')
        remember = True if request.form.get('remember') else False
        
        user = User.query.filter_by(email=email).first()
        if not user or not user.check_password(password):
            flash('Invalid email or password.', 'danger')
            return render_template('login.html')
            
        # Update last login
        user.last_login = datetime.utcnow()
        try:
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            print(f"Error updating last login: {e}")
            
        login_user(user, remember=remember)
        return redirect(url_for('dashboard.index'))
        
    return render_template('login.html')

@auth_bp.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out.', 'info')
    return redirect(url_for('landing'))
