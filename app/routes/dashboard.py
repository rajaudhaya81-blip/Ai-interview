from flask import Blueprint, render_template, redirect, url_for
from flask_login import login_required, current_user
from app.models.database import db, UserProfile, Resume, Interview, InterviewSession, Achievement, ProgressHistory
from app.services import GamificationService

dashboard_bp = Blueprint('dashboard', __name__)

@dashboard_bp.route('/dashboard')
@login_required
def index():
    profile = UserProfile.query.filter_by(user_id=current_user.id).first()
    
    # 1. Onboarding check
    has_resume = False
    resume = None
    if profile and profile.current_resume_id:
        resume = Resume.query.get(profile.current_resume_id)
        if resume:
            has_resume = True
            
    # 2. Check for active/paused session to resume
    active_session = InterviewSession.query.filter(
        InterviewSession.user_id == current_user.id,
        InterviewSession.status.in_(['active', 'paused'])
    ).first()
    
    # Get associated interview for session if any
    resume_interview = None
    if active_session:
        resume_interview = Interview.query.get(active_session.interview_id)
        
    # 3. Get gamification info
    total_xp = GamificationService.get_total_xp(current_user.id)
    level_info = GamificationService.get_user_level(total_xp)
    streak_count = GamificationService.calculate_and_update_streak(current_user.id)
    
    # Recent achievements
    achievements = Achievement.query.filter_by(user_id=current_user.id).order_by(Achievement.earned_at.desc()).limit(5).all()
    
    # Recent completed interviews
    recent_interviews = Interview.query.filter_by(
        user_id=current_user.id,
        status='completed'
    ).order_by(Interview.created_at.desc()).limit(5).all()
    
    return render_template(
        'dashboard.html',
        has_resume=has_resume,
        resume=resume,
        active_session=active_session,
        resume_interview=resume_interview,
        level_info=level_info,
        streak_count=streak_count,
        achievements=achievements,
        recent_interviews=recent_interviews
    )
