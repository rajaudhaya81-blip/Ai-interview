import unittest
from app import create_app
from app.models.database import db, User, Setting

class AuthTestCase(unittest.TestCase):
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

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.app_context.pop()

    def test_registration(self):
        # Register a valid user
        response = self.client.post('/register', data={
            'full_name': 'Test User',
            'email': 'test@example.com',
            'phone': '+1234567890',
            'password': 'Password123!',
            'confirm_password': 'Password123!'
        }, follow_redirects=True)
        
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Welcome back', response.data) # check redirected dashboard
        
        # Verify db entries
        user = User.query.filter_by(email='test@example.com').first()
        self.assertIsNotNone(user)
        self.assertEqual(user.full_name, 'Test User')
        
        # Check settings created
        settings = Setting.query.filter_by(user_id=user.id).first()
        self.assertIsNotNone(settings)

    def test_weak_password_registration(self):
        # Password too short and lacks special character
        response = self.client.post('/register', data={
            'full_name': 'Weak Password User',
            'email': 'weak@example.com',
            'phone': '+1234567890',
            'password': '123',
            'confirm_password': '123'
        }, follow_redirects=True)
        
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Password must be at least 8 characters long', response.data)
        
        user = User.query.filter_by(email='weak@example.com').first()
        self.assertIsNone(user)

    def test_mismatched_password_registration(self):
        response = self.client.post('/register', data={
            'full_name': 'Mismatched User',
            'email': 'mismatched@example.com',
            'phone': '+1234567890',
            'password': 'Password123!',
            'confirm_password': 'DifferentPassword123!'
        }, follow_redirects=True)
        
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Passwords do not match', response.data)

    def test_login_logout(self):
        # Create user
        user = User(full_name='Login User', email='login@example.com')
        user.set_password('SecurePassword123!')
        db.session.add(user)
        db.session.commit()
        
        # Login
        response = self.client.post('/login', data={
            'email': 'login@example.com',
            'password': 'SecurePassword123!'
        }, follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Welcome back', response.data)
        
        # Logout
        response = self.client.get('/logout', follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'logged out', response.data)

if __name__ == '__main__':
    unittest.main()
