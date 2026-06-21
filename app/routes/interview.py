import json
from datetime import datetime
from flask import Blueprint, request, jsonify, render_template, redirect, url_for, flash
from flask_login import login_required, current_user
from app.models.database import db, Interview, InterviewSession, QuestionBank, Answer, AIFollowup, Evaluation, Report, ReportFile, UserProfile, Resume
from app.services import GeminiService, SupabaseStorageService, PDFReportService, GamificationService

interview_bp = Blueprint('interview', __name__)

@interview_bp.route('/setup', methods=['GET', 'POST'])
@login_required
def setup():
    profile = UserProfile.query.filter_by(user_id=current_user.id).first()
    if not profile or not profile.current_resume_id:
        flash("You must upload a resume before you can practice interviews.", "warning")
        return redirect(url_for('resume.upload'))
        
    if request.method == 'POST':
        category = request.form.get('category', 'Technical')
        difficulty = request.form.get('difficulty', 'Medium')
        question_count = int(request.form.get('question_count', 10))
        time_limit = int(request.form.get('time_limit', 30))
        personality = request.form.get('personality', 'Friendly Recruiter')
        company = request.form.get('company', 'General')
        
        # Load resume data
        resume = Resume.query.get(profile.current_resume_id)
        resume_data = {
            "career_level": resume.career_level,
            "skills": [{"skill_name": s.skill_name} for s in resume.skills],
            "projects": [{"title": p.title} for p in resume.projects]
        }
        
        # Create Interview record
        new_interview = Interview(
            user_id=current_user.id,
            type=category,
            difficulty=difficulty,
            question_count=question_count,
            time_limit=time_limit,
            personality=personality,
            company=company,
            status='active'
        )
        db.session.add(new_interview)
        db.session.flush()
        
        # Generate questions
        questions = GeminiService.generate_questions(
            resume_data=resume_data,
            category=category,
            difficulty=difficulty,
            count=question_count,
            personality=personality,
            company=company
        )
        
        # Save questions to QuestionBank
        for idx, q_text in enumerate(questions):
            q_bank = QuestionBank(
                interview_id=new_interview.id,
                question_text=q_text,
                category=category,
                difficulty=difficulty,
                order_num=idx + 1
            )
            db.session.add(q_bank)
            
        # Create Session state
        session_time = time_limit * 60 if time_limit > 0 else 99999
        new_session = InterviewSession(
            user_id=current_user.id,
            interview_id=new_interview.id,
            current_question_index=0,
            remaining_time=session_time,
            status='active'
        )
        db.session.add(new_session)
        db.session.commit()
        
        return redirect(url_for('interview.room', interview_id=new_interview.id))
        
    return render_template('interview_setup.html')

@interview_bp.route('/room/<int:interview_id>')
@login_required
def room(interview_id):
    interview = Interview.query.get_or_404(interview_id)
    if interview.user_id != current_user.id:
        flash("Unauthorized access.", "danger")
        return redirect(url_for('dashboard.index'))
        
    if interview.status == 'completed':
        return redirect(url_for('interview.report_view', interview_id=interview.id))
        
    # Get active session
    session = InterviewSession.query.filter_by(interview_id=interview.id).first()
    if not session:
        # Create session fallback
        session = InterviewSession(
            user_id=current_user.id,
            interview_id=interview.id,
            current_question_index=0,
            remaining_time=interview.time_limit * 60,
            status='active'
        )
        db.session.add(session)
        db.session.commit()
        
    # Fetch questions sorted by order
    questions = QuestionBank.query.filter_by(interview_id=interview.id).order_by(QuestionBank.order_num).all()
    
    return render_template(
        'interview_room.html', 
        interview=interview, 
        session=session, 
        questions=questions
    )

@interview_bp.route('/upload-audio', methods=['POST'])
@login_required
def upload_audio():
    if 'audio' not in request.files:
        return jsonify({'success': False, 'message': 'No audio file found.'}), 400
        
    audio_file = request.files['audio']
    interview_id = request.form.get('interview_id')
    question_id = request.form.get('question_id')
    
    if not audio_file or not interview_id or not question_id:
        return jsonify({'success': False, 'message': 'Missing parameters.'}), 400
        
    audio_bytes = audio_file.read()
    filename = f"int_{interview_id}_q_{question_id}.wav"
    
    public_url = SupabaseStorageService.upload_file('audio', audio_bytes, filename, content_type='audio/wav')
    
    if public_url:
        return jsonify({'success': True, 'audio_url': public_url})
    return jsonify({'success': False, 'message': 'Failed to upload audio.'}), 500

@interview_bp.route('/submit-answer', methods=['POST'])
@login_required
def submit_answer():
    data = request.json
    interview_id = data.get('interview_id')
    question_index = int(data.get('question_index', 0))
    answer_text = data.get('answer_text', '').strip()
    audio_url = data.get('audio_url')
    wpm = data.get('wpm')
    pauses = int(data.get('pauses', 0))
    remaining_time = int(data.get('remaining_time', 0))
    
    interview = Interview.query.get_or_404(interview_id)
    session = InterviewSession.query.filter_by(interview_id=interview.id).first()
    
    if not session or session.status != 'active':
        return jsonify({'success': False, 'message': 'Interview session is not active.'}), 400
        
    # Update time left in session
    session.remaining_time = remaining_time
    
    # Get the current question
    questions = QuestionBank.query.filter_by(interview_id=interview.id).order_by(QuestionBank.order_num).all()
    if question_index >= len(questions):
        return jsonify({'success': False, 'message': 'Invalid question index.'}), 400
        
    question = questions[question_index]
    
    # Check if answer already exists to prevent duplicate submissions
    existing_answer = Answer.query.filter_by(interview_id=interview.id, question_id=question.id).first()
    if existing_answer:
        db.session.delete(existing_answer)
        db.session.flush()

    # Save new Answer
    new_answer = Answer(
        interview_id=interview.id,
        question_id=question.id,
        answer_text=answer_text,
        audio_url=audio_url
    )
    db.session.add(new_answer)
    db.session.flush()
    
    # Evaluate Answer using Gemini
    evaluation_data = GeminiService.evaluate_answer(
        question=question.question_text,
        answer=answer_text,
        wpm=wpm,
        pauses=pauses
    )
    
    # Save Evaluation
    new_evaluation = Evaluation(
        answer_id=new_answer.id,
        score=evaluation_data.get('score', 0),
        accuracy=evaluation_data.get('accuracy', 0),
        communication=evaluation_data.get('communication', 0),
        confidence=evaluation_data.get('confidence', 0),
        clarity=evaluation_data.get('clarity', 0),
        completeness=evaluation_data.get('completeness', 0),
        problem_solving=evaluation_data.get('problem_solving', 0),
        professionalism=evaluation_data.get('professionalism', 0),
        feedback=evaluation_data.get('feedback', ''),
        improvement_tips=evaluation_data.get('improvement_tips', '')
    )
    db.session.add(new_evaluation)
    
    # AI Follow-up Logic: Check if we should ask a follow-up question
    # personality & company are loaded to customize follow-up tone
    followup_text = GeminiService.generate_followup(
        question=question.question_text,
        answer=answer_text,
        personality=interview.personality,
        company=interview.company
    )
    
    if followup_text:
        # Create follow-up record
        new_followup = AIFollowup(
            answer_id=new_answer.id,
            follow_up_question_text=followup_text
        )
        db.session.add(new_followup)
        db.session.commit()
        return jsonify({
            'success': True,
            'status': 'follow_up',
            'follow_up_question': followup_text
        })
        
    # If no follow-up needed, increment question index
    session.current_question_index += 1
    
    if session.current_question_index >= interview.question_count:
        # Interview complete! Generate report.
        cls_report_url = complete_interview_internal(interview, session)
        return jsonify({
            'success': True,
            'status': 'completed',
            'redirect_url': url_for('interview.report_view', interview_id=interview.id)
        })
        
    db.session.commit()
    return jsonify({
        'success': True,
        'status': 'next',
        'next_question_index': session.current_question_index
    })

@interview_bp.route('/submit-followup', methods=['POST'])
@login_required
def submit_followup():
    data = request.json
    interview_id = data.get('interview_id')
    question_index = int(data.get('question_index', 0))
    followup_answer_text = data.get('followup_answer_text', '').strip()
    remaining_time = int(data.get('remaining_time', 0))
    
    interview = Interview.query.get_or_404(interview_id)
    session = InterviewSession.query.filter_by(interview_id=interview.id).first()
    
    if not session or session.status != 'active':
        return jsonify({'success': False, 'message': 'Session not active.'}), 400
        
    session.remaining_time = remaining_time
    
    # Get current question
    questions = QuestionBank.query.filter_by(interview_id=interview.id).order_by(QuestionBank.order_num).all()
    question = questions[question_index]
    
    # Find existing answer
    answer = Answer.query.filter_by(interview_id=interview.id, question_id=question.id).first()
    if not answer:
        return jsonify({'success': False, 'message': 'Original answer not found.'}), 404
        
    # Get last followup record
    followup = AIFollowup.query.filter_by(answer_id=answer.id).order_by(AIFollowup.created_at.desc()).first()
    if not followup:
        return jsonify({'success': False, 'message': 'Followup question not found.'}), 404
        
    followup.user_response_text = followup_answer_text
    
    # Re-evaluate combined answers
    combined_answer = f"Original: {answer.answer_text}\nFollowup Question: {followup.follow_up_question_text}\nFollowup Response: {followup_answer_text}"
    
    eval_data = GeminiService.evaluate_answer(
        question=question.question_text,
        answer=combined_answer
    )
    
    # Update evaluation scores
    evaluation = Evaluation.query.filter_by(answer_id=answer.id).first()
    if evaluation:
        evaluation.score = eval_data.get('score', 0)
        evaluation.accuracy = eval_data.get('accuracy', 0)
        evaluation.communication = eval_data.get('communication', 0)
        evaluation.confidence = eval_data.get('confidence', 0)
        evaluation.clarity = eval_data.get('clarity', 0)
        evaluation.completeness = eval_data.get('completeness', 0)
        evaluation.problem_solving = eval_data.get('problem_solving', 0)
        evaluation.professionalism = eval_data.get('professionalism', 0)
        evaluation.feedback = eval_data.get('feedback', '')
        evaluation.improvement_tips = eval_data.get('improvement_tips', '')
        
    # Proceed to next question
    session.current_question_index += 1
    
    if session.current_question_index >= interview.question_count:
        complete_interview_internal(interview, session)
        return jsonify({
            'success': True,
            'status': 'completed',
            'redirect_url': url_for('interview.report_view', interview_id=interview.id)
        })
        
    db.session.commit()
    return jsonify({
        'success': True,
        'status': 'next',
        'next_question_index': session.current_question_index
    })

@interview_bp.route('/pause', methods=['POST'])
@login_required
def pause():
    data = request.json
    interview_id = data.get('interview_id')
    remaining_time = int(data.get('remaining_time', 0))
    
    session = InterviewSession.query.filter_by(interview_id=interview_id).first()
    if session:
        session.status = 'paused'
        session.remaining_time = remaining_time
        
        interview = Interview.query.get(interview_id)
        if interview:
            interview.status = 'paused'
            
        db.session.commit()
        return jsonify({'success': True})
    return jsonify({'success': False, 'message': 'Session not found.'}), 404

@interview_bp.route('/resume', methods=['POST'])
@login_required
def resume():
    data = request.json
    interview_id = data.get('interview_id')
    
    session = InterviewSession.query.filter_by(interview_id=interview_id).first()
    if session:
        session.status = 'active'
        
        interview = Interview.query.get(interview_id)
        if interview:
            interview.status = 'active'
            
        db.session.commit()
        return jsonify({'success': True})
    return jsonify({'success': False, 'message': 'Session not found.'}), 404

@interview_bp.route('/abandon/<int:interview_id>', methods=['POST'])
@login_required
def abandon(interview_id):
    interview = Interview.query.get_or_404(interview_id)
    if interview.user_id != current_user.id:
        return jsonify({'success': False, 'message': 'Unauthorized'}), 403
        
    interview.status = 'abandoned'
    session = InterviewSession.query.filter_by(interview_id=interview.id).first()
    if session:
        session.status = 'abandoned'
        
    db.session.commit()
    return redirect(url_for('dashboard.index'))

@interview_bp.route('/report/<int:interview_id>')
@login_required
def report_view(interview_id):
    interview = Interview.query.get_or_404(interview_id)
    if interview.user_id != current_user.id:
        flash("Unauthorized access.", "danger")
        return redirect(url_for('dashboard.index'))
        
    report = Report.query.filter_by(interview_id=interview.id).first()
    
    # If completed but report is missing, force compile
    if not report and interview.status == 'completed':
        session = InterviewSession.query.filter_by(interview_id=interview.id).first()
        complete_interview_internal(interview, session)
        report = Report.query.filter_by(interview_id=interview.id).first()
        
    if not report:
        flash("Report is not available yet.", "warning")
        return redirect(url_for('dashboard.index'))
        
    # Decode stringified JSON fields for Jinja templates
    strengths = json.loads(report.strengths or '[]')
    weaknesses = json.loads(report.weaknesses or '[]')
    skill_breakdown = json.loads(report.skill_breakdown or '{}')
    
    # Fetch questions and answers for replay
    qa_data = []
    questions = QuestionBank.query.filter_by(interview_id=interview.id).order_by(QuestionBank.order_num).all()
    for q in questions:
        ans = Answer.query.filter_by(question_id=q.id).first()
        eval_item = Evaluation.query.filter_by(answer_id=ans.id).first() if ans else None
        followup = AIFollowup.query.filter_by(answer_id=ans.id).first() if ans else None
        
        qa_data.append({
            'question_text': q.question_text,
            'answer_text': ans.answer_text if ans else None,
            'audio_url': ans.audio_url if ans else None,
            'score': eval_item.score if eval_item else 0,
            'accuracy': eval_item.accuracy if eval_item else 0,
            'communication': eval_item.communication if eval_item else 0,
            'confidence': eval_item.confidence if eval_item else 0,
            'feedback': eval_item.feedback if eval_item else None,
            'improvement_tips': eval_item.improvement_tips if eval_item else None,
            'followup_question': followup.follow_up_question_text if followup else None,
            'followup_response': followup.user_response_text if followup else None
        })
        
    return render_template(
        'report.html', 
        interview=interview, 
        report=report, 
        strengths=strengths, 
        weaknesses=weaknesses, 
        skill_breakdown=skill_breakdown,
        qa_data=qa_data
    )


def complete_interview_internal(interview, session):
    """
    Shared utility function to mark interview as completed, calculate aggregated score,
    generate report, generate PDF, and award gamification XP.
    """
    interview.status = 'completed'
    if session:
        session.status = 'completed'
        
    # Gather all answers and evaluations
    questions = QuestionBank.query.filter_by(interview_id=interview.id).order_by(QuestionBank.order_num).all()
    qa_list = []
    answers_and_evals = []
    
    total_score = 0
    evaluated_count = 0
    
    for q in questions:
        ans = Answer.query.filter_by(question_id=q.id).first()
        if ans:
            eval_item = Evaluation.query.filter_by(answer_id=ans.id).first()
            score = eval_item.score if eval_item else 0
            total_score += score
            evaluated_count += 1
            
            qa_list.append({
                'question_text': q.question_text,
                'answer_text': ans.answer_text,
                'score': score,
                'accuracy': eval_item.accuracy if eval_item else 0,
                'communication': eval_item.communication if eval_item else 0,
                'confidence': eval_item.confidence if eval_item else 0,
                'feedback': eval_item.feedback if eval_item else '',
                'improvement_tips': eval_item.improvement_tips if eval_item else ''
            })
            
            answers_and_evals.append({
                'question': q.question_text,
                'answer': ans.answer_text,
                'score': score
            })
            
    avg_score = int(total_score / evaluated_count) if evaluated_count > 0 else 0
    interview.score = avg_score
    
    # Generate report with Gemini
    report_data = GeminiService.generate_final_report(interview.type, answers_and_evals)
    
    # Write Report to DB
    new_report = Report(
        interview_id=interview.id,
        overall_score=report_data.get('overall_score', avg_score),
        strengths=json.dumps(report_data.get('strengths', [])),
        weaknesses=json.dumps(report_data.get('weaknesses', [])),
        skill_breakdown=json.dumps(report_data.get('skill_breakdown', {})),
        recommendations=report_data.get('recommendations', ''),
        learning_path=report_data.get('learning_path', ''),
        career_suggestions=report_data.get('career_suggestions', ''),
        readiness_score=report_data.get('readiness_score', avg_score)
    )
    db.session.add(new_report)
    db.session.flush()
    
    # Generate PDF Report using ReportLab
    pdf_bytes = PDFReportService.generate_interview_pdf(
        candidate_name=current_user.full_name,
        email=current_user.email,
        interview=interview,
        qa_list=qa_list,
        report_data=report_data
    )
    
    # Upload PDF to Supabase Storage
    pdf_filename = f"report_{interview.id}_{int(datetime.utcnow().timestamp())}.pdf"
    pdf_url = SupabaseStorageService.upload_file('reports', pdf_bytes, pdf_filename, content_type='application/pdf')
    
    # Save ReportFile entry
    if pdf_url:
        report_file = ReportFile(
            report_id=new_report.id,
            file_url=pdf_url
        )
        db.session.add(report_file)
        
    # Process Gamification (streaks, badges, XP)
    GamificationService.process_interview_completion(current_user.id, interview.id)
    
    try:
        db.session.commit()
        return pdf_url
    except Exception as e:
        db.session.rollback()
        print(f"Error committing interview completion: {e}")
        return None
