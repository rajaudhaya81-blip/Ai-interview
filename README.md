# InterviewAI - AI Interview Simulator

InterviewAI is a production-ready AI Interview Simulator powered by Flask, Supabase PostgreSQL, Supabase Storage, and the Gemini API.

---

## Key Features

1. **AI Resume Analysis Engine**: Extracts skills, projects, certifications, and estimates an ATS Compatibility Score.
2. **Dynamic Questioning**: Generates technical and situational questions based on parsed resume details.
3. **Conversational Follow-ups**: Evaluates responses in real-time. If you miss core concepts, the AI interviewer will challenge your response with follow-up questions.
4. **Interviewer Personalities**: Practice with different personality profiles (e.g. Friendly Recruiter, Strict FAANG Interviewer, Startup Founder, HR Manager, Technical Architect).
5. **Company-Specific Style**: Practice interviews tailored to specific hiring criteria (Google, Amazon, Meta, Zoho, etc.).
6. **Voice Analytics & Replay**: Capture voice answers via Web Speech API. Measures Words Per Minute (WPM), speech gaps/pauses, and uploads recordings to Supabase Storage for replay.
7. **Gamification**: XP points, daily practice streaks, and achievement badges (e.g. "Python Expert", "Consistency Champion").
8. **PDF Reports**: Generates ReportLab PDFs containing visual skill distribution heatmaps (Matplotlib radar charts) uploaded directly to Supabase Storage.

---

## Project Structure

```
├── app/
│   ├── models/           # SQLAlchemy Database layer (14+ tables)
│   ├── routes/           # Blueprints (Auth, Resume, Interview, Dashboard, Analytics)
│   ├── services/         # Integrations (Gemini API, Supabase Storage, PDF generation)
│   ├── static/           # UI elements (style.css, charts.js, interview.js)
│   └── templates/        # Flask HTML layouts
├── config/               # Settings & environment parser
├── tests/                # Verification test suite
├── app.py                # App entrypoint
├── requirements.txt      # Dependencies list
├── render.yaml           # Deployment blueprint
└── .env.example          # Environment variables template
```

---

## Local Setup Instructions

### 1. Clone the repository and navigate to the folder
Ensure you are in the project folder.

### 2. Create and activate a Virtual Environment
```bash
python -m venv venv
# On Windows:
venv\Scripts\activate
# On Linux/macOS:
source venv/bin/activate
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

### 4. Create and Configure Environment Variables
Copy `.env.example` to `.env`:
```bash
cp .env.example .env
```
Fill in the configuration parameters:
- `SECRET_KEY`: A secure session key.
- `DATABASE_URL`: Your Supabase PostgreSQL database URL. (Note: URL-encode the password special characters, e.g., `@` becomes `%40`).
- `SUPABASE_URL`: Your Supabase Project API URL.
- `SUPABASE_KEY`: Your Supabase Service Role or anon key.
- `GEMINI_API_KEY`: Your Google Gemini API key.

*Note: If no `DATABASE_URL` is provided, the application will automatically fall back to a local SQLite database (`sqlite:///interview.db`) for testing.*

### 5. Supabase Storage buckets
Ensure the following three buckets are created in your Supabase storage page:
1. `resume`
2. `audio`
3. `reports`

### 6. Run the Application
```bash
python app.py
```
Open your browser and navigate to `http://127.0.0.1:5000`.

---

## Running Verification Tests
```bash
python -m unittest discover tests
```

---

## Render Deployment Guide

1. Log in to Render and click **New > Blueprint**.
2. Select your repository containing the codebase.
3. Render will parse `render.yaml` and set up the services automatically.
4. Input the following Environment Variables in the Render dashboard:
   - `DATABASE_URL`
   - `SUPABASE_URL`
   - `SUPABASE_KEY`
   - `GEMINI_API_KEY`
5. Click **Deploy**.
