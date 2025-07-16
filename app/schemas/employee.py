from marshmallow import Schema, fields, validate, ValidationError, post_load
import time

class EmployeeCreateSchema(Schema):
    """Schema for employee creation validation."""
    name = fields.String(
        required=True, 
        validate=validate.Length(min=1, max=100),
        error_messages={'required': 'Name is required'}
    )
    email = fields.Email(
        required=True, 
        validate=validate.Length(min=1, max=255),
        error_messages={'required': 'Email is required', 'invalid': 'Invalid email format'}
    )
    projects = fields.List(
        fields.String(), 
        load_default=[], 
        allow_none=True,
        validate=validate.Length(max=50)  # Reasonable limit on number of projects
    )
    invited = fields.Integer(
        allow_none=True,
        validate=validate.Range(min=0),
        error_messages={'invalid': 'Invited timestamp must be a positive integer (milliseconds)'}
    )
    
    @post_load
    def process_projects(self, data, **kwargs):
        """Ensure projects is a list and remove duplicates."""
        if 'projects' in data and data['projects'] is not None:
            data['projects'] = list(set(data['projects']))  # Remove duplicates
        return data

class EmployeeUpdateSchema(Schema):
    """Schema for employee update validation."""
    name = fields.String(
        validate=validate.Length(min=1, max=100),
        error_messages={'invalid': 'Name must be between 1 and 100 characters'}
    )
    email = fields.Email(
        validate=validate.Length(min=1, max=255),
        error_messages={'invalid': 'Invalid email format'}
    )
    projects = fields.List(
        fields.String(), 
        allow_none=True,
        validate=validate.Length(max=50)
    )
    invited = fields.Integer(
        allow_none=True,
        validate=validate.Range(min=0),
        error_messages={'invalid': 'Invited timestamp must be a positive integer (milliseconds)'}
    )
    deactivated = fields.Integer(
        allow_none=True,
        validate=validate.Range(min=0),
        error_messages={'invalid': 'Deactivated timestamp must be a positive integer (milliseconds)'}
    )
    
    @post_load
    def process_projects(self, data, **kwargs):
        """Ensure projects is a list and remove duplicates."""
        if 'projects' in data and data['projects'] is not None:
            data['projects'] = list(set(data['projects']))  # Remove duplicates
        return data

class EmployeeResponseSchema(Schema):
    """Schema for employee response serialization."""
    id = fields.String(dump_only=True)
    name = fields.String(dump_only=True)
    email = fields.String(dump_only=True)
    projects = fields.List(fields.String(), dump_only=True)
    deactivated = fields.Integer(dump_only=True, allow_none=True)
    invited = fields.Integer(dump_only=True, allow_none=True)
    created_at = fields.Integer(dump_only=True)
    updated_at = fields.Integer(dump_only=True)

class EmployeeListSchema(Schema):
    """Schema for employee list queries."""
    active_only = fields.Boolean(load_default=False)
    search = fields.String(validate=validate.Length(max=100))

class ProjectOperationSchema(Schema):
    """Schema for adding/removing projects from employee."""
    project_id = fields.String(
        required=True,
        validate=validate.Length(min=1, max=100),
        error_messages={'required': 'Project ID is required'}
    ) 