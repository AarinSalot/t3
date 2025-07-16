import pytest
import time
from app import create_app, db
from app.models.user import User
from app.models.employee import Employee
from flask_jwt_extended import create_access_token
import bcrypt

@pytest.fixture(scope='session')
def app():
    """Create and configure a new app instance for each test session."""
    app = create_app('testing')
    
    with app.app_context():
        # Create all database tables
        db.create_all()
        yield app
        # Clean up
        try:
            db.drop_all()
        except Exception:
            pass
        finally:
            db.session.close()

@pytest.fixture(scope='function')
def client(app):
    """Create a test client for the Flask app."""
    return app.test_client()

@pytest.fixture(scope='function')
def clean_db(app):
    """Clean database for each test."""
    with app.app_context():
        # Clean up any existing data
        try:
            db.session.query(Employee).delete()
            db.session.query(User).delete()
            db.session.commit()
        except Exception:
            db.session.rollback()
        
        yield db
        
        # Clean up after test
        try:
            db.session.query(Employee).delete()
            db.session.query(User).delete()
            db.session.commit()
        except Exception:
            db.session.rollback()
        finally:
            db.session.close()

@pytest.fixture
def test_user(app, clean_db):
    """Create a test user for authentication."""
    with app.app_context():
        password_hash = bcrypt.hashpw('testpassword'.encode('utf-8'), bcrypt.gensalt())
        user = User(
            email='test@example.com',
            name='Test User',
            password_hash=password_hash
        )
        db.session.add(user)
        db.session.commit()
        return user.id  # Return just the ID to avoid session issues

@pytest.fixture
def auth_headers(app, test_user):
    """Create authentication headers for testing protected endpoints."""
    with app.app_context():
        access_token = create_access_token(identity=str(test_user))  # Convert ID to string
        return {'Authorization': f'Bearer {access_token}'}

@pytest.fixture
def sample_employee_data():
    """Sample employee data for testing."""
    return {
        'name': 'John Doe',
        'email': 'john.doe@example.com',
        'projects': ['project-1', 'project-2'],
        'invited': int(time.time() * 1000)
    }

@pytest.fixture
def created_employee(app, clean_db, sample_employee_data):
    """Create a test employee in the database."""
    with app.app_context():
        employee = Employee(**sample_employee_data)
        db.session.add(employee)
        db.session.commit()
        # Return a fresh copy to avoid session issues
        employee_id = employee.id
        db.session.expunge_all()  # Clear session
        # Get fresh instance
        fresh_employee = db.session.get(Employee, employee_id)
        return fresh_employee 