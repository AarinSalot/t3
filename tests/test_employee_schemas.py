import pytest
import time
from marshmallow import ValidationError
from app.schemas.employee import (
    EmployeeCreateSchema, EmployeeUpdateSchema, EmployeeResponseSchema,
    EmployeeListSchema, ProjectOperationSchema
)

class TestEmployeeSchemas:
    """Test cases for Employee schemas."""
    
    def test_employee_create_schema_valid_data(self):
        """Test EmployeeCreateSchema with valid data."""
        schema = EmployeeCreateSchema()
        data = {
            'name': 'John Doe',
            'email': 'john@example.com',
            'projects': ['proj-1', 'proj-2'],
            'invited': int(time.time() * 1000)
        }
        
        result = schema.load(data)
        assert result['name'] == 'John Doe'
        assert result['email'] == 'john@example.com'
        assert set(result['projects']) == {'proj-1', 'proj-2'}  # Use set comparison since order might change
        assert result['invited'] == data['invited']
    
    def test_employee_create_schema_minimal_data(self):
        """Test EmployeeCreateSchema with minimal required data."""
        schema = EmployeeCreateSchema()
        data = {
            'name': 'Jane Doe',
            'email': 'jane@example.com'
        }
        
        result = schema.load(data)
        assert result['name'] == 'Jane Doe'
        assert result['email'] == 'jane@example.com'
        assert result['projects'] == []
        assert 'invited' not in result
    
    def test_employee_create_schema_missing_required_fields(self):
        """Test EmployeeCreateSchema with missing required fields."""
        schema = EmployeeCreateSchema()
        
        # Missing name
        with pytest.raises(ValidationError) as exc_info:
            schema.load({'email': 'test@example.com'})
        assert 'name' in exc_info.value.messages
        
        # Missing email
        with pytest.raises(ValidationError) as exc_info:
            schema.load({'name': 'Test User'})
        assert 'email' in exc_info.value.messages
    
    def test_employee_create_schema_invalid_email(self):
        """Test EmployeeCreateSchema with invalid email."""
        schema = EmployeeCreateSchema()
        data = {
            'name': 'Test User',
            'email': 'invalid-email'
        }
        
        with pytest.raises(ValidationError) as exc_info:
            schema.load(data)
        assert 'email' in exc_info.value.messages
    
    def test_employee_create_schema_long_name(self):
        """Test EmployeeCreateSchema with name exceeding limit."""
        schema = EmployeeCreateSchema()
        data = {
            'name': 'x' * 101,  # Exceeds 100 character limit
            'email': 'test@example.com'
        }
        
        with pytest.raises(ValidationError) as exc_info:
            schema.load(data)
        assert 'name' in exc_info.value.messages
    
    def test_employee_create_schema_duplicate_projects(self):
        """Test EmployeeCreateSchema removes duplicate projects."""
        schema = EmployeeCreateSchema()
        data = {
            'name': 'Test User',
            'email': 'test@example.com',
            'projects': ['proj-1', 'proj-2', 'proj-1', 'proj-3', 'proj-2']
        }
        
        result = schema.load(data)
        assert len(result['projects']) == 3
        assert set(result['projects']) == {'proj-1', 'proj-2', 'proj-3'}
    
    def test_employee_create_schema_too_many_projects(self):
        """Test EmployeeCreateSchema with too many projects."""
        schema = EmployeeCreateSchema()
        data = {
            'name': 'Test User',
            'email': 'test@example.com',
            'projects': [f'proj-{i}' for i in range(51)]  # Exceeds 50 project limit
        }
        
        with pytest.raises(ValidationError) as exc_info:
            schema.load(data)
        assert 'projects' in exc_info.value.messages
    
    def test_employee_create_schema_invalid_invited_timestamp(self):
        """Test EmployeeCreateSchema with invalid invited timestamp."""
        schema = EmployeeCreateSchema()
        data = {
            'name': 'Test User',
            'email': 'test@example.com',
            'invited': -1  # Negative timestamp
        }
        
        with pytest.raises(ValidationError) as exc_info:
            schema.load(data)
        assert 'invited' in exc_info.value.messages
    
    def test_employee_update_schema_valid_data(self):
        """Test EmployeeUpdateSchema with valid data."""
        schema = EmployeeUpdateSchema()
        data = {
            'name': 'Updated Name',
            'email': 'updated@example.com',
            'projects': ['new-proj'],
            'invited': int(time.time() * 1000),
            'deactivated': int(time.time() * 1000)
        }
        
        result = schema.load(data)
        assert result['name'] == 'Updated Name'
        assert result['email'] == 'updated@example.com'
        assert result['projects'] == ['new-proj']
        assert result['invited'] == data['invited']
        assert result['deactivated'] == data['deactivated']
    
    def test_employee_update_schema_partial_data(self):
        """Test EmployeeUpdateSchema with partial data."""
        schema = EmployeeUpdateSchema()
        data = {'name': 'New Name Only'}
        
        result = schema.load(data)
        assert result['name'] == 'New Name Only'
        assert 'email' not in result
        assert 'projects' not in result
    
    def test_employee_update_schema_empty_data(self):
        """Test EmployeeUpdateSchema with empty data."""
        schema = EmployeeUpdateSchema()
        result = schema.load({})
        assert result == {}
    
    def test_employee_response_schema_serialization(self):
        """Test EmployeeResponseSchema serialization."""
        schema = EmployeeResponseSchema()
        current_time = int(time.time() * 1000)
        
        employee_data = {
            'id': 'test-id-123',
            'name': 'Test Employee',
            'email': 'test@example.com',
            'projects': ['proj-1', 'proj-2'],
            'deactivated': None,
            'invited': current_time,
            'created_at': current_time,
            'updated_at': current_time
        }
        
        result = schema.dump(employee_data)
        assert result['id'] == 'test-id-123'
        assert result['name'] == 'Test Employee'
        assert result['email'] == 'test@example.com'
        assert result['projects'] == ['proj-1', 'proj-2']
        assert result['deactivated'] is None
        assert result['invited'] == current_time
        assert result['created_at'] == current_time
        assert result['updated_at'] == current_time
    
    def test_employee_list_schema_default_values(self):
        """Test EmployeeListSchema with default values."""
        schema = EmployeeListSchema()
        result = schema.load({})
        
        assert result['page'] == 1
        assert result['per_page'] == 10
        assert result['active_only'] is False
        assert 'search' not in result
    
    def test_employee_list_schema_custom_values(self):
        """Test EmployeeListSchema with custom values."""
        schema = EmployeeListSchema()
        data = {
            'page': 2,
            'per_page': 25,
            'active_only': True,
            'search': 'john'
        }
        
        result = schema.load(data)
        assert result['page'] == 2
        assert result['per_page'] == 25
        assert result['active_only'] is True
        assert result['search'] == 'john'
    
    def test_employee_list_schema_invalid_pagination(self):
        """Test EmployeeListSchema with invalid pagination values."""
        schema = EmployeeListSchema()
        
        # Invalid page
        with pytest.raises(ValidationError) as exc_info:
            schema.load({'page': 0})
        assert 'page' in exc_info.value.messages
        
        # Invalid per_page (too high)
        with pytest.raises(ValidationError) as exc_info:
            schema.load({'per_page': 101})
        assert 'per_page' in exc_info.value.messages
        
        # Invalid per_page (too low)
        with pytest.raises(ValidationError) as exc_info:
            schema.load({'per_page': 0})
        assert 'per_page' in exc_info.value.messages
    
    def test_employee_list_schema_long_search_term(self):
        """Test EmployeeListSchema with search term exceeding limit."""
        schema = EmployeeListSchema()
        data = {'search': 'x' * 101}  # Exceeds 100 character limit
        
        with pytest.raises(ValidationError) as exc_info:
            schema.load(data)
        assert 'search' in exc_info.value.messages
    
    def test_project_operation_schema_valid_data(self):
        """Test ProjectOperationSchema with valid data."""
        schema = ProjectOperationSchema()
        data = {'project_id': 'project-123'}
        
        result = schema.load(data)
        assert result['project_id'] == 'project-123'
    
    def test_project_operation_schema_missing_project_id(self):
        """Test ProjectOperationSchema with missing project_id."""
        schema = ProjectOperationSchema()
        
        with pytest.raises(ValidationError) as exc_info:
            schema.load({})
        assert 'project_id' in exc_info.value.messages
    
    def test_project_operation_schema_empty_project_id(self):
        """Test ProjectOperationSchema with empty project_id."""
        schema = ProjectOperationSchema()
        data = {'project_id': ''}
        
        with pytest.raises(ValidationError) as exc_info:
            schema.load(data)
        assert 'project_id' in exc_info.value.messages
    
    def test_project_operation_schema_long_project_id(self):
        """Test ProjectOperationSchema with project_id exceeding limit."""
        schema = ProjectOperationSchema()
        data = {'project_id': 'x' * 101}  # Exceeds 100 character limit
        
        with pytest.raises(ValidationError) as exc_info:
            schema.load(data)
        assert 'project_id' in exc_info.value.messages 