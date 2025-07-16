from marshmallow import Schema, fields, validate, validates_schema, ValidationError
from marshmallow.validate import Length, OneOf


class TaskCreateSchema(Schema):
    """Schema for creating a new task."""
    name = fields.Str(required=True, validate=Length(min=1, max=255))
    project_id = fields.Str(required=True, validate=Length(min=1))
    description = fields.Str(missing=None, allow_none=True)
    status = fields.Str(missing='pending', validate=OneOf(['pending', 'in_progress', 'completed', 'cancelled']))
    priority = fields.Str(missing='medium', validate=OneOf(['low', 'medium', 'high', 'urgent']))
    labels = fields.Str(missing=None, allow_none=True, validate=Length(max=255))
    billable = fields.Bool(missing=False)
    deadline = fields.Int(missing=None, allow_none=True, validate=validate.Range(min=0))


class TaskUpdateSchema(Schema):
    """Schema for updating an existing task."""
    name = fields.Str(validate=Length(min=1, max=255))
    description = fields.Str(allow_none=True)
    status = fields.Str(validate=OneOf(['pending', 'in_progress', 'completed', 'cancelled']))
    priority = fields.Str(validate=OneOf(['low', 'medium', 'high', 'urgent']))
    labels = fields.Str(allow_none=True, validate=Length(max=255))
    billable = fields.Bool()
    deadline = fields.Int(allow_none=True, validate=validate.Range(min=0))
    # Note: project_id and employees are not directly updatable


class TaskResponseSchema(Schema):
    """Schema for task response data."""
    id = fields.Str()
    name = fields.Str()
    project_id = fields.Str()
    description = fields.Str()
    status = fields.Str()
    priority = fields.Str()
    labels = fields.Str()
    billable = fields.Bool()
    employees = fields.List(fields.Str())
    deadline = fields.Int()
    created_at = fields.Int()
    updated_at = fields.Int()


class TaskListSchema(Schema):
    """Schema for task list query parameters."""
    project_id = fields.Str()
    status = fields.Str(validate=OneOf(['pending', 'in_progress', 'completed', 'cancelled']))
    priority = fields.Str(validate=OneOf(['low', 'medium', 'high', 'urgent']))
    billable = fields.Bool()
    search = fields.Str()
    employee_id = fields.Str()  # filter by employee assignment 