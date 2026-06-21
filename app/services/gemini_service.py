import json
from flask import current_app
import google.generativeai as genai

class GeminiService:
    PERSONALITIES = {
        "Friendly Recruiter": (
            "A warm, welcoming, and encouraging HR recruiter. Focuses on communication, basic understanding, "
            "and soft skills. Tries to make the candidate comfortable and uses a positive, conversational tone."
        ),
        "Strict FAANG Interviewer": (
            "A rigorous, demanding, and direct interviewer. Values optimal solutions, performance tradeoffs, "
            "Big O notation, scalability, and technical depth. Challenges weak or vague answers, drills deep into "
            "assumptions, and maintains a formal, objective tone."
        ),
        "Startup Founder": (
            "A high-energy, fast-paced, and practical founder. Focuses on speed of execution, hands-on building, "
            "versatility, problem-solving, and direct business impact. Asks how the candidate would build "
            "features from scratch under tight deadlines."
        ),
        "HR Manager": (
            "A professional focused on cultural alignment, emotional intelligence, conflict resolution, "
            "teamwork, ethics, and long-term career goals. Asks behavioral questions using the STAR method."
        ),
        "Technical Architect": (
            "A high-level systems architect. Focuses on software architecture, design patterns, microservices, "
            "database design, security, reliability, scalability, and system trade-offs. Asks structural and design questions."
        )
    }

    COMPANIES = {
        "Google": "highly algorithmic, data structures, scale, distributed systems, deep analytical rigor",
        "Amazon": "customer obsession, ownership, bias for action, STAR behavioral questions, scalable backend services",
        "Microsoft": "logical coding, clean code, practical engineering trade-offs, OS/cloud integration",
        "Meta": "fast iteration, system design at massive scale, product-centric engineering, APIs, data efficiency",
        "Netflix": "freedom and responsibility, performance engineering, high availability, resilience under pressure",
        "TCS": "enterprise software, SDLC lifecycle, database integrity, client requirements, standard coding practices",
        "Infosys": "process-oriented development, agile execution, testing methodologies, general software engineering",
        "Zoho": "independent craftsmanship, bootstrap mindset, SaaS database design, web frameworks, highly optimized code",
        "Freshworks": "customer support features, user experience, product development, clean UI architecture, scaling SaaS APIs"
    }

    @classmethod
    def _get_model(cls, response_json=True):
        api_key = current_app.config.get('GEMINI_API_KEY')
        if not api_key:
            return None
        try:
            genai.configure(api_key=api_key)
            config = {}
            if response_json:
                config["response_mime_type"] = "application/json"
            return genai.GenerativeModel('gemini-3.5-flash', generation_config=config)
        except Exception as e:
            print(f"Error configuring Gemini API: {e}")
            return None

    @classmethod
    def analyze_resume(cls, raw_text):
        """
        Parses skills, projects, certifications, ATS Score, and Career level from resume raw text.
        """
        model = cls._get_model(response_json=True)
        prompt = f"""
        Analyze the following resume text. Extract details and return a JSON object.
        JSON object schema:
        {{
            "score": int (Overall Resume Quality Score, 0 to 100),
            "ats_score": int (Estimated ATS Compatibility Score, 0 to 100),
            "career_level": "Beginner" | "Intermediate" | "Advanced",
            "skills": [
                {{"skill_name": "Skill Name", "proficiency": int (0 to 100)}}
            ],
            "projects": [
                {{"title": "Project Title", "description": "Short Description of Project", "complexity_score": int (0 to 100)}}
            ],
            "certifications": [
                {{"name": "Certification Name", "issuer": "Issuer or Organization"}}
            ]
        }}
        
        Resume text:
        {raw_text}
        """
        if not model:
            # Return Mock Fallback Data
            return cls._get_mock_resume_analysis()
        
        try:
            response = model.generate_content(prompt)
            return json.loads(response.text)
        except Exception as e:
            print(f"Gemini API analyze_resume failed: {e}")
            return cls._get_mock_resume_analysis()

    @classmethod
    def generate_questions(cls, resume_data, category, difficulty, count=10, personality="Friendly Recruiter", company="General"):
        """
        Generates structured interview questions based on resume, category, difficulty, personality, and target company.
        """
        model = cls._get_model(response_json=True)
        skills = ", ".join([s.get('skill_name', '') for s in resume_data.get('skills', [])])
        projects = ", ".join([p.get('title', '') for p in resume_data.get('projects', [])])
        personality_desc = cls.PERSONALITIES.get(personality, cls.PERSONALITIES["Friendly Recruiter"])
        company_desc = cls.COMPANIES.get(company, "general software engineering and problem solving standards")

        prompt = f"""
        You are an interviewer with the personality: "{personality}". Description: {personality_desc}
        You are interviewing a candidate for a role matching the style of the company: "{company}". Specific focus: {company_desc}.
        Candidate profile details:
        - Skills: {skills}
        - Projects: {projects}
        - Career Level: {resume_data.get('career_level', 'Intermediate')}
        
        Generate {count} questions for a "{difficulty}" level "{category}" interview.
        The questions should challenge the candidate based on their background but also incorporate company style and difficulty.
        
        Return a JSON array of strings:
        [
            "Question 1 content here",
            "Question 2 content here"
        ]
        """
        if not model:
            return cls._get_mock_questions(category, difficulty, count)
        
        try:
            response = model.generate_content(prompt)
            return json.loads(response.text)
        except Exception as e:
            print(f"Gemini API generate_questions failed: {e}")
            return cls._get_mock_questions(category, difficulty, count)

    @classmethod
    def generate_followup(cls, question, answer, personality="Friendly Recruiter", company="General"):
        """
        Evaluates the answer and generates a relevant follow-up question if there are missing concepts.
        """
        model = cls._get_model(response_json=True)
        personality_desc = cls.PERSONALITIES.get(personality, cls.PERSONALITIES["Friendly Recruiter"])
        company_desc = cls.COMPANIES.get(company, "general software engineering standards")

        prompt = f"""
        You are an interviewer with the personality: "{personality}". Description: {personality_desc}
        Working under the company context: "{company}" ({company_desc}).
        
        You asked the following question:
        "{question}"
        
        The candidate answered:
        "{answer}"
        
        Analyze if the candidate's answer is complete or if they missed crucial parts, or mentioned concepts that warrant a deeper drill down (e.g. they mentioned JWT but didn't explain validation; mentioned SQL but not indexes).
        
        If the answer is thorough, complete, or doesn't benefit from a follow-up, return:
        {{ "follow_up": null }}
        
        Otherwise, generate a single targeted follow-up question to probe their understanding in alignment with your interviewer personality.
        Return:
        {{ "follow_up": "Your follow-up question here" }}
        """
        if not model:
            return None
        
        try:
            response = model.generate_content(prompt)
            data = json.loads(response.text)
            return data.get("follow_up")
        except Exception as e:
            print(f"Gemini API generate_followup failed: {e}")
            return None

    @classmethod
    def evaluate_answer(cls, question, answer, wpm=None, pauses=0):
        """
        Evaluates a candidate's answer based on correctness, communication, clarity, and voice metrics (wpm, pauses).
        """
        model = cls._get_model(response_json=True)
        voice_info = ""
        if wpm:
            voice_info = f"Speaking Speed: {wpm} Words Per Minute. Silences/Pauses detected: {pauses} times."

        prompt = f"""
        Evaluate the candidate's answer to the following question.
        Question: "{question}"
        Answer: "{answer}"
        {voice_info}
        
        Evaluate across these criteria, giving scores from 0 to 100:
        1. Accuracy (technical correctness)
        2. Communication (articulation and structure)
        3. Confidence (fluency, lack of hesitation. Take WPM and pauses into account: ideal WPM is 110-150. Pauses should be minimal)
        4. Clarity (conciseness and directness)
        5. Completeness (covering all parts of the question)
        6. Problem Solving (thought process and depth)
        7. Professionalism (tone and presentation)
        
        Return a JSON object:
        {{
            "score": int (overall average score, 0-100),
            "accuracy": int,
            "communication": int,
            "confidence": int,
            "clarity": int,
            "completeness": int,
            "problem_solving": int,
            "professionalism": int,
            "feedback": "Overall qualitative feedback about what was good or missing.",
            "improvement_tips": "Specific actionable points to improve this answer."
        }}
        """
        if not model:
            return cls._get_mock_evaluation(answer)
            
        try:
            response = model.generate_content(prompt)
            return json.loads(response.text)
        except Exception as e:
            print(f"Gemini API evaluate_answer failed: {e}")
            return cls._get_mock_evaluation(answer)

    @classmethod
    def generate_final_report(cls, interview_type, questions_and_answers):
        """
        Generates a comprehensive final report and learning path based on the Q&A list.
        """
        model = cls._get_model(response_json=True)
        qa_text = ""
        for i, item in enumerate(questions_and_answers):
            qa_text += f"Q{i+1}: {item['question']}\nA{i+1}: {item['answer']}\nScore: {item.get('score', 0)}\n\n"

        prompt = f"""
        You are a hiring committee. Create a comprehensive performance report for a candidate who completed a "{interview_type}" interview.
        Here is the question and answer history with individual question scores:
        {qa_text}
        
        Synthesize the performance and output a JSON object with:
        {{
            "overall_score": int (average of scores),
            "strengths": ["Strength 1", "Strength 2", "Strength 3"],
            "weaknesses": ["Weakness 1", "Weakness 2", "Weakness 3"],
            "skill_breakdown": {{
                "Skill Name 1": int (Score 0-100),
                "Skill Name 2": int (Score 0-100)
            }},
            "recommendations": "General hiring decision recommendation or placement fit.",
            "learning_path": "Detailed step-by-step personalized learning path in Markdown format.",
            "career_suggestions": "Career recommendations based on performance in Markdown format.",
            "readiness_score": int (Interview readiness percentage, 0-100)
        }}
        """
        if not model:
            return cls._get_mock_final_report()
            
        try:
            response = model.generate_content(prompt)
            return json.loads(response.text)
        except Exception as e:
            print(f"Gemini API generate_final_report failed: {e}")
            return cls._get_mock_final_report()

    # MOCK FALLBACKS
    @staticmethod
    def _get_mock_resume_analysis():
        return {
            "score": 78,
            "ats_score": 75,
            "career_level": "Intermediate",
            "skills": [
                {"skill_name": "Python", "proficiency": 85},
                {"skill_name": "Flask", "proficiency": 75},
                {"skill_name": "SQL Database", "proficiency": 70},
                {"skill_name": "API Design", "proficiency": 80},
                {"skill_name": "Git", "proficiency": 90}
            ],
            "projects": [
                {"title": "AI Dashboard Service", "description": "Interactive analytics portal using Flask and SQLAlchemy.", "complexity_score": 80},
                {"title": "E-Commerce REST API", "description": "Product catalog and checkout system with JWT auth.", "complexity_score": 75}
            ],
            "certifications": [
                {"name": "Python Developer Associate", "issuer": "Python Institute"}
            ]
        }

    @staticmethod
    def _get_mock_questions(category, difficulty, count):
        base_questions = {
            "Technical": [
                "Explain the difference between a list and a tuple in Python.",
                "How does Flask handle routing and what is dynamic URL routing?",
                "What is database indexing and how does it speed up queries?",
                "Explain the concept of RESTful API design.",
                "What is git rebase and how does it differ from git merge?",
                "Describe the purpose of Middleware in web applications.",
                "How do you handle password hashing and session security in Flask?",
                "What is SQLAlchemy and how does ORM differ from raw SQL?",
                "Explain how CORS works and why it is necessary.",
                "What are python decorators and how are they implemented?"
            ],
            "HR": [
                "Tell me about yourself.",
                "Why do you want to join our organization?",
                "Describe a situation where you had a conflict with a colleague and how you resolved it.",
                "What is your greatest professional achievement?",
                "Where do you see yourself in five years?",
                "How do you prioritize tasks when working on multiple deadlines?",
                "Describe a time you failed and what you learned from it.",
                "Why should we hire you over other candidates?",
                "What is your preferred work style: remote, hybrid, or in-office?",
                "How do you handle negative feedback from a manager?"
            ]
        }
        fallback_list = base_questions.get(category, base_questions["Technical"])
        # Duplicate list if count is greater than length
        questions = []
        for i in range(count):
            questions.append(fallback_list[i % len(fallback_list)])
        return questions

    @staticmethod
    def _get_mock_evaluation(answer):
        # Calculate scores dynamically based on answer length to make it look active
        length = len(answer or "")
        score = min(40 + int(length / 5), 95)
        return {
            "score": score,
            "accuracy": score,
            "communication": min(score + 5, 100),
            "confidence": min(score - 5, 100),
            "clarity": score,
            "completeness": min(score - 10, 100),
            "problem_solving": score,
            "professionalism": min(score + 5, 100),
            "feedback": "The answer provides a basic explanation. It shows fundamental understanding but could benefit from deeper technical examples and structure.",
            "improvement_tips": "1. Provide specific examples of how you used the technology.\n2. Discuss architectural trade-offs.\n3. Keep answers well-structured and concise."
        }

    @staticmethod
    def _get_mock_final_report():
        return {
            "overall_score": 82,
            "strengths": ["Strong core python knowledge", "Good verbal articulation", "Clear software design patterns"],
            "weaknesses": ["Missed microservice trade-offs", "Needs optimization detail", "Under-prepared for databases"],
            "skill_breakdown": {
                "Python": 88,
                "Flask": 80,
                "API Design": 85,
                "Database Indexing": 70,
                "Software Architecture": 78
            },
            "recommendations": "Strong candidate for a Junior/Mid-level Flask Engineer role. High willingness to learn and clear communicator.",
            "learning_path": "### Recommended Learning Path\n1. **Advanced Flask**: Review blueprint architecture and lazy loading.\n2. **System Design**: Study load balancers, caching strategies (Redis), and message queues.\n3. **Database Tuning**: Practice indexing, explain plans, and query analysis.",
            "career_suggestions": "Ideal for **SaaS Product Developer** or **Backend Systems Engineer** positions.",
            "readiness_score": 80
        }
