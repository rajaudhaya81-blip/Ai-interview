import os
from flask import Blueprint, request, jsonify, render_template, redirect, url_for, flash, current_app
from flask_login import login_required, current_user
from app.models.database import db, Resume, ResumeSkill, Project, Certification, UserProfile, ProgressHistory
from app.services import ResumeParserService, GeminiService, SupabaseStorageService

resume_bp = Blueprint('resume', __name__)

ALLOWED_EXTENSIONS = {'pdf', 'docx'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@resume_bp.route('/upload', methods=['GET', 'POST'])
@login_required
def upload():
    if request.method == 'POST':
        # Check if file exists in request
        if 'resume' not in request.files:
            return jsonify({'success': False, 'message': 'No file uploaded.'}), 400
            
        file = request.files['resume']
        if file.filename == '':
            return jsonify({'success': False, 'message': 'No file selected.'}), 400
            
        if not allowed_file(file.filename):
            return jsonify({'success': False, 'message': 'Invalid file format. Only PDF and DOCX are allowed.'}), 400
            
        # Read file bytes
        file_bytes = file.read()
        file_size = len(file_bytes)
        
        # Check file size (10MB limit)
        if file_size > current_app.config['MAX_CONTENT_LENGTH']:
            return jsonify({'success': False, 'message': 'File size exceeds the 10 MB limit.'}), 400
            
        # Step 1: Upload to Supabase Storage (under resume/ bucket)
        filename = f"{current_user.id}_{int(os.path.getmtime(current_app.config['UPLOAD_FOLDER'])) if os.path.exists(current_app.config['UPLOAD_FOLDER']) else 1}_{file.filename}"
        filename = filename.replace(" ", "_")
        
        # We will save the file path/URL returned from storage
        public_url = SupabaseStorageService.upload_file('resume', file_bytes, filename)
        
        # Step 2: Extract Raw Text
        raw_text = ResumeParserService.extract_text(file_bytes, file.filename)
        if not raw_text:
            return jsonify({'success': False, 'message': 'Could not extract text from file. Please ensure the file is not empty or corrupted.'}), 422
            
        # Step 3: Run Gemini AI analysis
        analysis = GeminiService.analyze_resume(raw_text)
        
        try:
            # Step 4: Write to Database
            new_resume = Resume(
                user_id=current_user.id,
                raw_text=raw_text,
                score=analysis.get('score', 0),
                ats_score=analysis.get('ats_score', 0),
                career_level=analysis.get('career_level', 'Beginner')
            )
            db.session.add(new_resume)
            db.session.flush() # triggers resume id generation
            
            # Save Skills
            for skill in analysis.get('skills', []):
                new_skill = ResumeSkill(
                    resume_id=new_resume.id,
                    skill_name=skill.get('skill_name'),
                    proficiency=skill.get('proficiency', 50)
                )
                db.session.add(new_skill)
                
            # Save Projects
            for project in analysis.get('projects', []):
                new_project = Project(
                    resume_id=new_resume.id,
                    title=project.get('title'),
                    description=project.get('description'),
                    complexity_score=project.get('complexity_score', 50)
                )
                db.session.add(new_project)
                
            # Save Certifications
            for cert in analysis.get('certifications', []):
                new_cert = Certification(
                    resume_id=new_resume.id,
                    name=cert.get('name'),
                    issuer=cert.get('issuer')
                )
                db.session.add(new_cert)
                
            # Link current resume to user profile
            profile = UserProfile.query.filter_by(user_id=current_user.id).first()
            if not profile:
                profile = UserProfile(user_id=current_user.id)
                db.session.add(profile)
            profile.current_resume_id = new_resume.id
            
            # Award XP for resume upload (first time or updates)
            xp_award = ProgressHistory(
                user_id=current_user.id,
                xp_gain=50,
                activity_type="Uploaded Resume & Profile Analysis",
                streak_count=1
            )
            db.session.add(xp_award)
            
            db.session.commit()
            
            return jsonify({
                'success': True, 
                'message': 'Resume uploaded and analyzed successfully!', 
                'resume_id': new_resume.id
            })
            
        except Exception as e:
            db.session.rollback()
            print(f"Error saving resume analysis: {e}")
            return jsonify({'success': False, 'message': f'Failed to process analysis: {e}'}), 500
            
    return render_template('upload.html')

@resume_bp.route('/intel')
@login_required
def intelligence():
    profile = UserProfile.query.filter_by(user_id=current_user.id).first()
    if not profile or not profile.current_resume_id:
        flash("Please upload your resume to access the Resume Intelligence Dashboard.", "warning")
        return redirect(url_for('resume.upload'))
        
    resume = Resume.query.get(profile.current_resume_id)
    return render_template('resume_intel.html', resume=resume)
