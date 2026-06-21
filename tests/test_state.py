import unittest
from app import create_app
from app.models.database import db, User, Interview, InterviewSession, QuestionBank

class StateTestCase(unittest.TestCase):
    def setUp(self):
        import os
        # Override DATABASE_URL in environment before creating app to avoid remote Supabase connections
        os.environ['DATABASE_URL'] = 'sqlite:///:memory:'
        
        self.app = create_app()
        self.app.config['TESTING'] = True
        self.client = self.app.test_client()
        
        self.app_context = self.app.app_context()
        self.app_context.push()
        
        db.create_all()
        
        # Setup mock user
        self.user = User(full_name='State User', email='state@example.com')
        self.user.set_password('Password123!')
        db.session.add(self.user)
        db.session.commit()

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.app_context.pop()

    def test_session_lifecycle(self):
        # Create an interview
        interview = Interview(
            user_id=self.user.id,
            type='Technical',
            difficulty='Medium',
            question_count=2,
            time_limit=15,
            status='active'
        )
        db.session.add(interview)
        db.session.flush()
        
        # Add questions
        q1 = QuestionBank(interview_id=interview.id, question_text="What is Flask?", order_num=1)
        q2 = QuestionBank(interview_id=interview.id, question_text="What is WSGI?", order_num=2)
        db.session.add_all([q1, q2])
        
        # Create session
        session = InterviewSession(
            user_id=self.user.id,
            interview_id=interview.id,
            current_question_index=0,
            remaining_time=900,
            status='active'
        )
        db.session.add(session)
        db.session.commit()
        
        # Verify initial states
        self.assertEqual(session.current_question_index, 0)
        self.assertEqual(session.status, 'active')
        
        # Update progress index and remaining time (simulating answer submission)
        session.current_question_index = 1
        session.remaining_time = 850
        db.session.commit()
        
        # Verify persistence
        fetched_session = InterviewSession.query.filter_by(interview_id=interview.id).first()
        self.assertEqual(fetched_session.current_question_index, 1)
        self.assertEqual(fetched_session.remaining_time, 850)
        
        # Pause session
        fetched_session.status = 'paused'
        db.session.commit()
        
        # Verify status
        refetched_session = InterviewSession.query.filter_by(interview_id=interview.id).first()
        self.assertEqual(refetched_session.status, 'paused')

if __name__ == '__main__':
    unittest.main()
