import pytest
import json
import time
from app.models.employee import Employee
from app import db

class TestEmployeeAPI:
    """Test cases for Employee API endpoints."""
    
    def test_get_employees_empty(self, client, auth_headers, clean_db):
        """Test getting employees when none exist."""
        response = client.get('/api/employees/', headers=auth_headers)
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['employees'] == []
        assert data['pagination']['total'] == 0
    
    def test_get_employees_with_data(self, client, auth_headers, created_employee):
        """Test getting employees with existing data."""
        response = client.get('/api/employees/', headers=auth_headers)
        assert response.status_code == 200
        data = json.loads(response.data)
        assert len(data['employees']) == 1
        assert data['employees'][0]['name'] == 'John Doe'
        assert data['employees'][0]['email'] == 'john.doe@example.com'
    
    def test_get_employees_pagination(self, client, auth_headers, app, clean_db):
        """Test employee pagination."""
        with app.app_context():
            # Create multiple employees
            for i in range(15):
                employee = Employee(
                    name=f'Employee {i}',
                    email=f'employee{i}@example.com'
                )
                db.session.add(employee)
            db.session.commit()
        
        # Test first page
        response = client.get('/api/employees/?page=1&per_page=10', headers=auth_headers)
        assert response.status_code == 200
        data = json.loads(response.data)
        assert len(data['employees']) == 10
        assert data['pagination']['total'] == 15
        assert data['pagination']['pages'] == 2
        assert data['pagination']['has_next'] is True
        
        # Test second page
        response = client.get('/api/employees/?page=2&per_page=10', headers=auth_headers)
        assert response.status_code == 200
        data = json.loads(response.data)
        assert len(data['employees']) == 5
        assert data['pagination']['has_next'] is False
    
    def test_get_employees_search(self, client, auth_headers, app, clean_db):
        """Test employee search functionality."""
        with app.app_context():
            # Create test employees
            emp1 = Employee(name='John Smith', email='john@example.com')
            emp2 = Employee(name='Jane Doe', email='jane@company.com')
            emp3 = Employee(name='Bob Johnson', email='bob@example.com')
            db.session.add_all([emp1, emp2, emp3])
            db.session.commit()
        
        # Search by name
        response = client.get('/api/employees/?search=John', headers=auth_headers)
        assert response.status_code == 200
        data = json.loads(response.data)
        assert len(data['employees']) == 2  # John Smith and Bob Johnson
        
        # Search by email domain
        response = client.get('/api/employees/?search=example.com', headers=auth_headers)
        assert response.status_code == 200
        data = json.loads(response.data)
        assert len(data['employees']) == 2  # john@example.com and bob@example.com
    
    def test_get_employees_active_only(self, client, auth_headers, app, clean_db):
        """Test filtering active employees only."""
        with app.app_context():
            # Create active and deactivated employees
            active_emp = Employee(name='Active Employee', email='active@example.com')
            deactivated_emp = Employee(name='Deactivated Employee', email='deactivated@example.com')
            deactivated_emp.deactivate()
            db.session.add_all([active_emp, deactivated_emp])
            db.session.commit()
        
        # Get all employees
        response = client.get('/api/employees/', headers=auth_headers)
        assert response.status_code == 200
        data = json.loads(response.data)
        assert len(data['employees']) == 2
        
        # Get active employees only
        response = client.get('/api/employees/?active_only=true', headers=auth_headers)
        assert response.status_code == 200
        data = json.loads(response.data)
        assert len(data['employees']) == 1
        assert data['employees'][0]['name'] == 'Active Employee'
    
    def test_create_employee_success(self, client, auth_headers, clean_db):
        """Test successful employee creation."""
        employee_data = {
            'name': 'New Employee',
            'email': 'new@example.com',
            'projects': ['proj-1', 'proj-2'],
            'invited': int(time.time() * 1000)
        }
        
        response = client.post('/api/employees/', 
                             headers=auth_headers,
                             data=json.dumps(employee_data),
                             content_type='application/json')
        
        assert response.status_code == 201
        data = json.loads(response.data)
        assert data['message'] == 'Employee created successfully'
        assert data['employee']['name'] == 'New Employee'
        assert data['employee']['email'] == 'new@example.com'
        assert data['employee']['projects'] == ['proj-1', 'proj-2']
    
    def test_create_employee_validation_error(self, client, auth_headers, clean_db):
        """Test employee creation with validation errors."""
        # Missing required fields
        response = client.post('/api/employees/', 
                             headers=auth_headers,
                             data=json.dumps({}),
                             content_type='application/json')
        
        assert response.status_code == 400
        data = json.loads(response.data)
        assert 'error' in data
        assert 'messages' in data
    
    def test_create_employee_duplicate_email(self, client, auth_headers, created_employee):
        """Test creating employee with duplicate email."""
        employee_data = {
            'name': 'Another Employee',
            'email': 'john.doe@example.com'  # Same as created_employee
        }
        
        response = client.post('/api/employees/', 
                             headers=auth_headers,
                             data=json.dumps(employee_data),
                             content_type='application/json')
        
        assert response.status_code == 409
        data = json.loads(response.data)
        assert data['error'] == 'Email already exists'
    
    def test_get_employee_success(self, client, auth_headers, created_employee):
        """Test getting a specific employee."""
        response = client.get(f'/api/employees/{created_employee.id}', headers=auth_headers)
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['employee']['id'] == created_employee.id
        assert data['employee']['name'] == created_employee.name
        assert data['employee']['email'] == created_employee.email
    
    def test_get_employee_not_found(self, client, auth_headers, clean_db):
        """Test getting non-existent employee."""
        response = client.get('/api/employees/non-existent-id', headers=auth_headers)
        
        assert response.status_code == 404
        data = json.loads(response.data)
        assert data['error'] == 'Employee not found'
    
    def test_update_employee_success(self, client, auth_headers, created_employee):
        """Test successful employee update."""
        update_data = {
            'name': 'Updated Name',
            'email': 'updated@example.com',
            'projects': ['new-project']
        }
        
        response = client.put(f'/api/employees/{created_employee.id}',
                            headers=auth_headers,
                            data=json.dumps(update_data),
                            content_type='application/json')
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['message'] == 'Employee updated successfully'
        assert data['employee']['name'] == 'Updated Name'
        assert data['employee']['email'] == 'updated@example.com'
        assert data['employee']['projects'] == ['new-project']
    
    def test_update_employee_not_found(self, client, auth_headers, clean_db):
        """Test updating non-existent employee."""
        update_data = {'name': 'New Name'}
        
        response = client.put('/api/employees/non-existent-id',
                            headers=auth_headers,
                            data=json.dumps(update_data),
                            content_type='application/json')
        
        assert response.status_code == 404
        data = json.loads(response.data)
        assert data['error'] == 'Employee not found'
    
    def test_update_employee_duplicate_email(self, client, auth_headers, app, clean_db):
        """Test updating employee with duplicate email."""
        with app.app_context():
            # Create two employees
            emp1 = Employee(name='Employee 1', email='emp1@example.com')
            emp2 = Employee(name='Employee 2', email='emp2@example.com')
            db.session.add_all([emp1, emp2])
            db.session.commit()
            
            # Try to update emp1 with emp2's email
            update_data = {'email': 'emp2@example.com'}
            
            response = client.put(f'/api/employees/{emp1.id}',
                                headers=auth_headers,
                                data=json.dumps(update_data),
                                content_type='application/json')
            
            assert response.status_code == 409
            data = json.loads(response.data)
            assert data['error'] == 'Email already in use'
    
    def test_delete_employee_success(self, client, auth_headers, created_employee):
        """Test successful employee deletion."""
        response = client.delete(f'/api/employees/{created_employee.id}', headers=auth_headers)
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['message'] == 'Employee deleted successfully'
        
        # Verify employee is actually deleted
        get_response = client.get(f'/api/employees/{created_employee.id}', headers=auth_headers)
        assert get_response.status_code == 404
    
    def test_delete_employee_not_found(self, client, auth_headers, clean_db):
        """Test deleting non-existent employee."""
        response = client.delete('/api/employees/non-existent-id', headers=auth_headers)
        
        assert response.status_code == 404
        data = json.loads(response.data)
        assert data['error'] == 'Employee not found'
    
    def test_add_project_to_employee(self, client, auth_headers, created_employee):
        """Test adding project to employee."""
        project_data = {'project_id': 'new-project-id'}
        
        response = client.post(f'/api/employees/{created_employee.id}/projects',
                             headers=auth_headers,
                             data=json.dumps(project_data),
                             content_type='application/json')
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['message'] == 'Project added successfully'
        assert 'new-project-id' in data['employee']['projects']
    
    def test_add_duplicate_project_to_employee(self, client, auth_headers, created_employee):
        """Test adding duplicate project to employee."""
        # created_employee already has 'project-1'
        project_data = {'project_id': 'project-1'}
        
        response = client.post(f'/api/employees/{created_employee.id}/projects',
                             headers=auth_headers,
                             data=json.dumps(project_data),
                             content_type='application/json')
        
        assert response.status_code == 409
        data = json.loads(response.data)
        assert data['error'] == 'Project already assigned to employee'
    
    def test_remove_project_from_employee(self, client, auth_headers, created_employee):
        """Test removing project from employee."""
        # created_employee has 'project-1'
        response = client.delete(f'/api/employees/{created_employee.id}/projects/project-1',
                               headers=auth_headers)
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['message'] == 'Project removed successfully'
        assert 'project-1' not in data['employee']['projects']
    
    def test_remove_non_existent_project_from_employee(self, client, auth_headers, created_employee):
        """Test removing non-existent project from employee."""
        response = client.delete(f'/api/employees/{created_employee.id}/projects/non-existent-project',
                               headers=auth_headers)
        
        assert response.status_code == 404
        data = json.loads(response.data)
        assert data['error'] == 'Project not assigned to employee'
    
    def test_deactivate_employee(self, client, auth_headers, created_employee):
        """Test deactivating employee."""
        response = client.post(f'/api/employees/{created_employee.id}/deactivate',
                             headers=auth_headers)
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['message'] == 'Employee deactivated successfully'
        assert data['employee']['deactivated'] is not None
    
    def test_deactivate_already_deactivated_employee(self, client, auth_headers, app, clean_db):
        """Test deactivating already deactivated employee."""
        with app.app_context():
            employee = Employee(name='Test Employee', email='test@example.com')
            employee.deactivate()
            db.session.add(employee)
            db.session.commit()
            
            response = client.post(f'/api/employees/{employee.id}/deactivate',
                                 headers=auth_headers)
            
            assert response.status_code == 409
            data = json.loads(response.data)
            assert data['error'] == 'Employee is already deactivated'
    
    def test_reactivate_employee(self, client, auth_headers, app, clean_db):
        """Test reactivating employee."""
        with app.app_context():
            employee = Employee(name='Test Employee', email='test@example.com')
            employee.deactivate()
            db.session.add(employee)
            db.session.commit()
            
            response = client.post(f'/api/employees/{employee.id}/reactivate',
                                 headers=auth_headers)
            
            assert response.status_code == 200
            data = json.loads(response.data)
            assert data['message'] == 'Employee reactivated successfully'
            assert data['employee']['deactivated'] is None
    
    def test_reactivate_active_employee(self, client, auth_headers, created_employee):
        """Test reactivating already active employee."""
        response = client.post(f'/api/employees/{created_employee.id}/reactivate',
                             headers=auth_headers)
        
        assert response.status_code == 409
        data = json.loads(response.data)
        assert data['error'] == 'Employee is not deactivated'
    
    def test_unauthorized_access(self, client, clean_db):
        """Test accessing employee endpoints without authentication."""
        # Test various endpoints without auth headers
        endpoints = [
            ('GET', '/api/employees/'),
            ('POST', '/api/employees/'),
            ('GET', '/api/employees/some-id'),
            ('PUT', '/api/employees/some-id'),
            ('DELETE', '/api/employees/some-id'),
            ('POST', '/api/employees/some-id/projects'),
            ('DELETE', '/api/employees/some-id/projects/proj-id'),
            ('POST', '/api/employees/some-id/deactivate'),
            ('POST', '/api/employees/some-id/reactivate'),
        ]
        
        for method, endpoint in endpoints:
            response = getattr(client, method.lower())(endpoint)
            assert response.status_code == 401 