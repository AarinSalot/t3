from marshmallow import Schema, fields, validate

class UserSchema(Schema):
    """Schema for user serialization."""
    id = fields.Integer(dump_only=True)
    name = fields.String(required=True, validate=validate.Length(min=1, max=100))
    email = fields.Email(required=True, validate=validate.Length(min=1, max=255))
    created_at = fields.DateTime(dump_only=True)
    updated_at = fields.DateTime(dump_only=True)

class UserUpdateSchema(Schema):
    """Schema for user update validation."""
    name = fields.String(validate=validate.Length(min=1, max=100))
    email = fields.Email(validate=validate.Length(min=1, max=255)) 