from datetime import datetime, timedelta
from app.models.database import db, Interview, Achievement, ProgressHistory, Resume, ResumeSkill

class GamificationService:
    LEVELS = [
        {"name": "Beginner", "min_xp": 0, "max_xp": 499},
        {"name": "Intermediate", "min_xp": 500, "max_xp": 1499},
        {"name": "Advanced", "min_xp": 1500, "max_xp": 2999},
        {"name": "Expert", "min_xp": 3000, "max_xp": 4999},
        {"name": "Interview Master", "min_xp": 5000, "max_xp": 999999}
    ]

    @classmethod
    def get_user_level(cls, total_xp):
        """
        Returns the level name, current XP progress, and XP required for the next level.
        """
        for lvl in cls.LEVELS:
            if lvl["min_xp"] <= total_xp <= lvl["max_xp"]:
                current_level = lvl["name"]
                if lvl["max_xp"] == 999999:
                    progress_pct = 100
                    xp_needed = 0
                else:
                    range_xp = lvl["max_xp"] - lvl["min_xp"] + 1
                    gained_in_level = total_xp - lvl["min_xp"]
                    progress_pct = int((gained_in_level / range_xp) * 100)
                    xp_needed = lvl["max_xp"] + 1 - total_xp
                return {
                    "level": current_level,
                    "progress_pct": progress_pct,
                    "xp_needed": xp_needed,
                    "current_xp": total_xp
                }
        return {"level": "Beginner", "progress_pct": 0, "xp_needed": 500, "current_xp": 0}

    @classmethod
    def get_total_xp(cls, user_id):
        """
        Sum of all XP gained by the user.
        """
        total = db.session.query(db.func.sum(ProgressHistory.xp_gain)).filter(ProgressHistory.user_id == user_id).scalar()
        return total if total is not None else 0

    @classmethod
    def process_interview_completion(cls, user_id, interview_id):
        """
        Process badges and XP when an interview is completed.
        Returns a list of newly unlocked badge names.
        """
        new_badges = []
        
        # 1. Award base XP for interview completion
        xp_gain = 100
        activity = f"Completed Interview #{interview_id}"
        
        # 2. Check for Score Improvement
        # Get all completed interviews for this user
        completed_interviews = Interview.query.filter(
            Interview.user_id == user_id,
            Interview.status == 'completed'
        ).order_by(Interview.created_at.desc()).all()
        
        # The current completed interview is the first one in the list
        if len(completed_interviews) >= 2:
            current_score = completed_interviews[0].score or 0
            previous_score = completed_interviews[1].score or 0
            if current_score > previous_score:
                xp_gain += 50
                activity += " (with score improvement)"
        
        # 3. Calculate Streak
        streak_count = cls.calculate_and_update_streak(user_id)
        if streak_count > 1:
            xp_gain += 20
            activity += f" (streak multiplier x{streak_count})"

        # Log XP history
        history_entry = ProgressHistory(
            user_id=user_id,
            xp_gain=xp_gain,
            activity_type=activity,
            streak_count=streak_count
        )
        db.session.add(history_entry)

        # 4. Check & Award Badges
        existing_badges = {a.badge_name for a in Achievement.query.filter_by(user_id=user_id).all()}
        
        interview_count = len(completed_interviews)
        
        # Interview count badges
        if interview_count >= 1 and "First Interview" not in existing_badges:
            new_badges.append("First Interview")
        if interview_count >= 5 and "5 Interviews" not in existing_badges:
            new_badges.append("5 Interviews")
        if interview_count >= 10 and "10 Interviews" not in existing_badges:
            new_badges.append("10 Interviews")

        # Python / Flask expert badges based on parsed resumes
        latest_resume = Resume.query.filter_by(user_id=user_id).order_by(Resume.created_at.desc()).first()
        if latest_resume:
            for skill in latest_resume.skills:
                name_lower = skill.skill_name.lower()
                if "python" in name_lower and skill.proficiency >= 85 and "Python Expert" not in existing_badges:
                    new_badges.append("Python Expert")
                if "flask" in name_lower and skill.proficiency >= 85 and "Flask Expert" not in existing_badges:
                    new_badges.append("Flask Expert")
                    
        # Streak badges
        if streak_count >= 3 and "Consistency Champion" not in existing_badges:
            new_badges.append("Consistency Champion")
        if streak_count >= 7 and "Daily Streak" not in existing_badges:
            new_badges.append("Daily Streak")

        # Save new achievements
        for badge in new_badges:
            achievement = Achievement(user_id=user_id, badge_name=badge)
            db.session.add(achievement)

        try:
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            print(f"Error processing gamification: {e}")

        return new_badges

    @classmethod
    def calculate_and_update_streak(cls, user_id):
        """
        Determines current daily streak based on history logs.
        """
        # Find all history entries for user sorted by date desc
        history = ProgressHistory.query.filter_by(user_id=user_id).order_by(ProgressHistory.created_at.desc()).all()
        if not history:
            return 1
            
        today = datetime.utcnow().date()
        dates_active = sorted(list({h.created_at.date() for h in history}), reverse=True)
        
        if not dates_active:
            return 1
            
        # Check if latest activity was today or yesterday
        latest_active_date = dates_active[0]
        if latest_active_date < today - timedelta(days=1):
            # Streak broken
            return 1
            
        streak = 0
        current_check = today
        
        # If they haven't practiced today, but did yesterday, start checking from yesterday
        if dates_active[0] == today - timedelta(days=1):
            current_check = today - timedelta(days=1)
            
        for active_date in dates_active:
            if active_date == current_check:
                streak += 1
                current_check -= timedelta(days=1)
            elif active_date > current_check:
                # Same day or newer, skip duplicates
                continue
            else:
                # Gap in days, streak ends
                break
                
        return max(streak, 1)
