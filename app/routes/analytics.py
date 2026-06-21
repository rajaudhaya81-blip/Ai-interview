import json
from flask import Blueprint, render_template, jsonify
from flask_login import login_required, current_user
from app.models.database import db, Interview, Achievement, ProgressHistory, Report

analytics_bp = Blueprint('analytics', __name__)

@analytics_bp.route('/history')
@login_required
def history():
    interviews = Interview.query.filter_by(user_id=current_user.id).order_by(Interview.created_at.desc()).all()
    return render_template('history.html', interviews=interviews)

@analytics_bp.route('/analytics')
@login_required
def show_analytics():
    interviews = Interview.query.filter_by(user_id=current_user.id, status='completed').order_by(Interview.created_at.asc()).all()
    
    # 1. Performance Trend (Line Chart data)
    performance_trend = []
    for idx, i in enumerate(interviews):
        performance_trend.append({
            'date': i.created_at.strftime('%Y-%m-%d'),
            'score': i.score,
            'label': f"Int #{idx+1} ({i.type})"
        })
        
    # 2. Category Distribution (Doughnut Chart data)
    category_counts = {}
    for i in interviews:
        category_counts[i.type] = category_counts.get(i.type, 0) + 1
        
    # 3. Overall stats
    total_interviews = len(interviews)
    avg_score = int(sum([i.score for i in interviews]) / total_interviews) if total_interviews > 0 else 0
    
    # Highest score
    max_score = max([i.score for i in interviews]) if total_interviews > 0 else 0
    
    return render_template(
        'analytics.html',
        interviews=interviews,
        performance_trend=json.dumps(performance_trend),
        category_counts=json.dumps(category_counts),
        total_interviews=total_interviews,
        avg_score=avg_score,
        max_score=max_score
    )

@analytics_bp.route('/gamification')
@login_required
def gamification():
    achievements = Achievement.query.filter_by(user_id=current_user.id).order_by(Achievement.earned_at.desc()).all()
    xp_history = ProgressHistory.query.filter_by(user_id=current_user.id).order_by(ProgressHistory.created_at.desc()).all()
    
    # Aggregated stats
    total_xp = sum([h.xp_gain for h in xp_history])
    streak_count = 0
    if xp_history:
        streak_count = xp_history[0].streak_count
        
    return render_template(
        'gamification.html',
        achievements=achievements,
        xp_history=xp_history,
        total_xp=total_xp,
        streak_count=streak_count
    )
