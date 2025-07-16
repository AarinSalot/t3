import pytest
import time
from app.models.employee import Employee
from app import db

class TestEmployeeModel:
    """Test cases for Employee model."""
    
    def test_employee_creation(self, app, clean_db):
        """Test employee creation with required fields."""
        with app.app_context():
            employee = Employee(
                name='Jane Smith',
                email='jane.smith@example.com',
                projects=['proj-1']
            )
            db.session.add(employee)
            db.session.commit()
            
            assert employee.id is not None
            assert employee.name == 'Jane Smith'
            assert employee.email == 'jane.smith@example.com'
            assert employee.projects == ['proj-1']
            assert employee.deactivated is None
            assert employee.invited is None
            assert employee.created_at is not None
            assert employee.updated_at is not None
    
    def test_employee_string_representation(self, app, clean_db):
        """Test employee string representation."""
        with app.app_context():
            employee = Employee(name='John Doe', email='john@example.com')
            assert repr(employee) == '<Employee John Doe (john@example.com)>'
    
    def test_update_timestamp(self, app, clean_db):
        """Test updating timestamp functionality."""
        with app.app_context():
            employee = Employee(name='Test User', email='test@example.com')
            db.session.add(employee)
            db.session.commit()
            
            original_timestamp = employee.updated_at
            time.sleep(0.001)  # Small delay
            employee.update_timestamp()
            
            assert employee.updated_at > original_timestamp
    
    def test_deactivate_employee(self, app, clean_db):
        """Test employee deactivation."""
        with app.app_context():
            employee = Employee(name='Test User', email='test@example.com')
            db.session.add(employee)
            db.session.commit()
            
            assert employee.deactivated is None
            employee.deactivate()
            
            assert employee.deactivated is not None
            assert employee.deactivated > 0
    
    def test_reactivate_employee(self, app, clean_db):
        """Test employee reactivation."""
        with app.app_context():
            employee = Employee(name='Test User', email='test@example.com')
            employee.deactivate()
            db.session.add(employee)
            db.session.commit()
            
            assert employee.deactivated is not None
            employee.reactivate()
            
            assert employee.deactivated is None
    
    def test_add_project(self, app, clean_db):
        """Test adding projects to employee."""
        with app.app_context():
            employee = Employee(name='Test User', email='test@example.com')
            db.session.add(employee)
            db.session.commit()
            
            # Add first project
            employee.add_project('project-1')
            assert 'project-1' in employee.projects
            
            # Add second project
            employee.add_project('project-2')
            assert 'project-1' in employee.projects
            assert 'project-2' in employee.projects
            
            # Try to add duplicate project
            original_length = len(employee.projects)
            employee.add_project('project-1')
            assert len(employee.projects) == original_length
    
    def test_remove_project(self, app, clean_db):
        """Test removing projects from employee."""
        with app.app_context():
            employee = Employee(
                name='Test User', 
                email='test@example.com',
                projects=['project-1', 'project-2', 'project-3']
            )
            db.session.add(employee)
            db.session.commit()
            
            # Remove existing project
            employee.remove_project('project-2')
            assert 'project-1' in employee.projects
            assert 'project-2' not in employee.projects
            assert 'project-3' in employee.projects
            
            # Try to remove non-existent project
            original_length = len(employee.projects)
            employee.remove_project('non-existent')
            assert len(employee.projects) == original_length
    
    def test_to_dict(self, app, clean_db):
        """Test employee to_dict conversion."""
        with app.app_context():
            current_time = int(time.time() * 1000)
            employee = Employee(
                name='Test User',
                email='test@example.com',
                projects=['proj-1', 'proj-2'],
                invited=current_time
            )
            db.session.add(employee)
            db.session.commit()
            
            employee_dict = employee.to_dict()
            
            assert employee_dict['id'] == employee.id
            assert employee_dict['name'] == 'Test User'
            assert employee_dict['email'] == 'test@example.com'
            assert employee_dict['projects'] == ['proj-1', 'proj-2']
            assert employee_dict['invited'] == current_time
            assert employee_dict['deactivated'] is None
            assert employee_dict['created_at'] is not None
            assert employee_dict['updated_at'] is not None 