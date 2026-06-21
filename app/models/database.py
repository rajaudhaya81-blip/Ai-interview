from datetime import datetime
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash

db = SQLAlchemy()

class User(db.Model, UserMixin):
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    full_name = db.Column(db.String(150), nullable=False)
    email = db.Column(db.String(150), unique=True, nullable=False)
    phone = db.Column(db.String(20), nullable=True)
    password_hash = db.Column(db.String(256), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_login = db.Column(db.DateTime, nullable=True)
    
    # Relationships
    profile = db.relationship('UserProfile', backref='user', uselist=False, cascade="all, delete-orphan")
    resumes = db.relationship('Resume', backref='user', cascade="all, delete-orphan")
    interviews = db.relationship('Interview', backref='user', cascade="all, delete-orphan")
    sessions = db.relationship('InterviewSession', backref='user', cascade="all, delete-orphan")
    achievements = db.relationship('Achievement', backref='user', cascade="all, delete-orphan")
    progress_history = db.relationship('ProgressHistory', backref='user', cascade="all, delete-orphan")
    notifications = db.relationship('Notification', backref='user', cascade="all, delete-orphan")
    settings = db.relationship('Setting', backref='user', uselist=False, cascade="all, delete-orphan")
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
        
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)


class UserProfile(db.Model):
    __tablename__ = 'user_profiles'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    bio = db.Column(db.Text, nullable=True)
    target_role = db.Column(db.String(100), nullable=True)
    target_company = db.Column(db.String(100), nullable=True)
    current_resume_id = db.Column(db.Integer, nullable=True)


class Resume(db.Model):
    __tablename__ = 'resumes'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    raw_text = db.Column(db.Text, nullable=False)
    score = db.Column(db.Integer, default=0)  # Resume score (0-100)
    ats_score = db.Column(db.Integer, default=0)  # ATS score (0-100)
    career_level = db.Column(db.String(50), nullable=True)  # Beginner, Intermediate, Advanced
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    skills = db.relationship('ResumeSkill', backref='resume', cascade="all, delete-orphan")
    projects = db.relationship('Project', backref='resume', cascade="all, delete-orphan")
    certifications = db.relationship('Certification', backref='resume', cascade="all, delete-orphan")


class ResumeSkill(db.Model):
    __tablename__ = 'resume_skills'
    
    id = db.Column(db.Integer, primary_key=True)
    resume_id = db.Column(db.Integer, db.ForeignKey('resumes.id', ondelete='CASCADE'), nullable=False)
    skill_name = db.Column(db.String(100), nullable=False)
    proficiency = db.Column(db.Integer, default=50)  # 0-100


class Project(db.Model):
    __tablename__ = 'projects'
    
    id = db.Column(db.Integer, primary_key=True)
    resume_id = db.Column(db.Integer, db.ForeignKey('resumes.id', ondelete='CASCADE'), nullable=False)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=True)
    complexity_score = db.Column(db.Integer, default=50)  # 0-100


class Certification(db.Model):
    __tablename__ = 'certifications'
    
    id = db.Column(db.Integer, primary_key=True)
    resume_id = db.Column(db.Integer, db.ForeignKey('resumes.id', ondelete='CASCADE'), nullable=False)
    name = db.Column(db.String(200), nullable=False)
    issuer = db.Column(db.String(200), nullable=True)


class Interview(db.Model):
    __tablename__ = 'interviews'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    type = db.Column(db.String(50), nullable=False)  # Technical, HR, Project Viva, System Design, Aptitude, Mixed
    difficulty = db.Column(db.String(20), nullable=False)  # Easy, Medium, Hard, Expert
    question_count = db.Column(db.Integer, default=10)
    time_limit = db.Column(db.Integer, default=30)  # in minutes
    score = db.Column(db.Integer, default=0)  # overall interview score
    status = db.Column(db.String(20), default='active')  # active, paused, completed, abandoned
    personality = db.Column(db.String(50), default='Friendly Recruiter')
    company = db.Column(db.String(50), default='General')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    questions = db.relationship('QuestionBank', backref='interview', cascade="all, delete-orphan")
    answers = db.relationship('Answer', backref='interview', cascade="all, delete-orphan")
    report = db.relationship('Report', backref='interview', uselist=False, cascade="all, delete-orphan")
    session = db.relationship('InterviewSession', backref='interview', uselist=False, cascade="all, delete-orphan")


class InterviewSession(db.Model):
    __tablename__ = 'interview_sessions'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    interview_id = db.Column(db.Integer, db.ForeignKey('interviews.id', ondelete='CASCADE'), nullable=False)
    current_question_index = db.Column(db.Integer, default=0)
    remaining_time = db.Column(db.Integer, default=1800)  # in seconds
    status = db.Column(db.String(20), default='active')  # active, paused, completed, abandoned
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class QuestionBank(db.Model):
    __tablename__ = 'question_bank'
    
    id = db.Column(db.Integer, primary_key=True)
    interview_id = db.Column(db.Integer, db.ForeignKey('interviews.id', ondelete='CASCADE'), nullable=False)
    question_text = db.Column(db.Text, nullable=False)
    category = db.Column(db.String(50), nullable=True)
    difficulty = db.Column(db.String(20), nullable=True)
    order_num = db.Column(db.Integer, nullable=False)
    
    # Relationships
    answers = db.relationship('Answer', backref='question', cascade="all, delete-orphan")


class Answer(db.Model):
    __tablename__ = 'answers'
    
    id = db.Column(db.Integer, primary_key=True)
    interview_id = db.Column(db.Integer, db.ForeignKey('interviews.id', ondelete='CASCADE'), nullable=False)
    question_id = db.Column(db.Integer, db.ForeignKey('question_bank.id', ondelete='CASCADE'), nullable=False)
    answer_text = db.Column(db.Text, nullable=True)
    audio_url = db.Column(db.String(500), nullable=True)  # Supabase storage URL
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    evaluation = db.relationship('Evaluation', backref='answer', uselist=False, cascade="all, delete-orphan")
    followups = db.relationship('AIFollowup', backref='answer', cascade="all, delete-orphan")


class AIFollowup(db.Model):
    __tablename__ = 'ai_followups'
    
    id = db.Column(db.Integer, primary_key=True)
    answer_id = db.Column(db.Integer, db.ForeignKey('answers.id', ondelete='CASCADE'), nullable=False)
    follow_up_question_text = db.Column(db.Text, nullable=False)
    user_response_text = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class Evaluation(db.Model):
    __tablename__ = 'evaluations'
    
    id = db.Column(db.Integer, primary_key=True)
    answer_id = db.Column(db.Integer, db.ForeignKey('answers.id', ondelete='CASCADE'), nullable=False)
    score = db.Column(db.Integer, default=0)
    accuracy = db.Column(db.Integer, default=0)
    communication = db.Column(db.Integer, default=0)
    confidence = db.Column(db.Integer, default=0)
    clarity = db.Column(db.Integer, default=0)
    completeness = db.Column(db.Integer, default=0)
    problem_solving = db.Column(db.Integer, default=0)
    professionalism = db.Column(db.Integer, default=0)
    feedback = db.Column(db.Text, nullable=True)
    improvement_tips = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class Report(db.Model):
    __tablename__ = 'reports'
    
    id = db.Column(db.Integer, primary_key=True)
    interview_id = db.Column(db.Integer, db.ForeignKey('interviews.id', ondelete='CASCADE'), nullable=False)
    overall_score = db.Column(db.Integer, default=0)
    strengths = db.Column(db.Text, nullable=True)  # JSON-encoded string
    weaknesses = db.Column(db.Text, nullable=True)  # JSON-encoded string
    skill_breakdown = db.Column(db.Text, nullable=True)  # JSON-encoded string
    recommendations = db.Column(db.Text, nullable=True)
    learning_path = db.Column(db.Text, nullable=True)
    career_suggestions = db.Column(db.Text, nullable=True)
    readiness_score = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    report_files = db.relationship('ReportFile', backref='report', cascade="all, delete-orphan")


class ReportFile(db.Model):
    __tablename__ = 'report_files'
    
    id = db.Column(db.Integer, primary_key=True)
    report_id = db.Column(db.Integer, db.ForeignKey('reports.id', ondelete='CASCADE'), nullable=False)
    file_url = db.Column(db.String(500), nullable=False)  # Supabase storage URL
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class Achievement(db.Model):
    __tablename__ = 'achievements'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    badge_name = db.Column(db.String(100), nullable=False)
    earned_at = db.Column(db.DateTime, default=datetime.utcnow)


class ProgressHistory(db.Model):
    __tablename__ = 'progress_history'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    xp_gain = db.Column(db.Integer, default=0)
    activity_type = db.Column(db.String(100), nullable=False)  # e.g. "Interview Completed", "Resume Uploaded"
    streak_count = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class Notification(db.Model):
    __tablename__ = 'notifications'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    message = db.Column(db.Text, nullable=False)
    is_read = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class Setting(db.Model):
    __tablename__ = 'settings'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    dark_mode = db.Column(db.Boolean, default=True)
    voice_enabled = db.Column(db.Boolean, default=True)
    interviewer_personality = db.Column(db.String(50), default='Friendly Recruiter')
    target_company = db.Column(db.String(50), default='General')
