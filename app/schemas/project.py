from marshmallow import Schema, fields, validate, post_load

class ProjectCreateSchema(Schema):
    """Schema for project creation validation."""
    name = fields.String(
        required=True, 
        validate=validate.Length(min=1, max=255),
        error_messages={'required': 'Name is required'}
    )
    description = fields.String(
        allow_none=True,
        validate=validate.Length(max=2000)
    )
    archived = fields.Boolean(load_default=False)
    billable = fields.Boolean(load_default=False)
    deadline = fields.Integer(
        allow_none=True,
        validate=validate.Range(min=0),
        error_messages={'invalid': 'Deadline must be a positive integer (milliseconds)'}
    )
    employees = fields.List(
        fields.String(), 
        load_default=[], 
        allow_none=True,
        validate=validate.Length(max=100)  # Reasonable limit on number of employees
    )
    
    @post_load
    def process_employees(self, data, **kwargs):
        """Ensure employees is a list and remove duplicates."""
        if 'employees' in data and data['employees'] is not None:
            data['employees'] = list(set(data['employees']))  # Remove duplicates
        return data

class ProjectUpdateSchema(Schema):
    """Schema for project update validation."""
    name = fields.String(
        validate=validate.Length(min=1, max=255),
        error_messages={'invalid': 'Name must be between 1 and 255 characters'}
    )
    description = fields.String(
        allow_none=True,
        validate=validate.Length(max=2000)
    )
    archived = fields.Boolean()
    billable = fields.Boolean()
    deadline = fields.Integer(
        allow_none=True,
        validate=validate.Range(min=0),
        error_messages={'invalid': 'Deadline must be a positive integer (milliseconds)'}
    )
    employees = fields.List(
        fields.String(), 
        allow_none=True,
        validate=validate.Length(max=100)
    )
    
    @post_load
    def process_employees(self, data, **kwargs):
        """Ensure employees is a list and remove duplicates."""
        if 'employees' in data and data['employees'] is not None:
            data['employees'] = list(set(data['employees']))  # Remove duplicates
        return data

class ProjectResponseSchema(Schema):
    """Schema for project response serialization."""
    id = fields.String(dump_only=True)
    name = fields.String(dump_only=True)
    description = fields.String(dump_only=True, allow_none=True)
    archived = fields.Boolean(dump_only=True)
    billable = fields.Boolean(dump_only=True)
    deadline = fields.Integer(dump_only=True, allow_none=True)
    employees = fields.List(fields.String(), dump_only=True)
    created_at = fields.Integer(dump_only=True)
    updated_at = fields.Integer(dump_only=True)

class ProjectListSchema(Schema):
    """Schema for project list queries."""
    archived_only = fields.Boolean(load_default=False)
    active_only = fields.Boolean(load_default=False)  # Not archived
    billable_only = fields.Boolean(load_default=False)
    search = fields.String(validate=validate.Length(max=100))

class ProjectEmployeeOperationSchema(Schema):
    """Schema for adding/removing employees from project."""
    employee_id = fields.String(
        required=True,
        validate=validate.Length(min=1, max=36),
        error_messages={'required': 'Employee ID is required'}
    ) 