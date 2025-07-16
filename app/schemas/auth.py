from marshmallow import Schema, fields, validate, ValidationError

class LoginSchema(Schema):
    """Schema for user login validation."""
    email = fields.Email(required=True, validate=validate.Length(min=1, max=255))
    password = fields.String(required=True, validate=validate.Length(min=6, max=255))

class RegisterSchema(Schema):
    """Schema for user registration validation."""
    name = fields.String(required=True, validate=validate.Length(min=1, max=100))
    email = fields.Email(required=True, validate=validate.Length(min=1, max=255))
    password = fields.String(
        required=True,
        validate=validate.Length(min=6, max=255),
        error_messages={'required': 'Password is required', 'invalid': 'Password must be at least 6 characters'}
    )
    confirm_password = fields.String(required=True)
    
    def validate_passwords_match(self, data, **kwargs):
        """Validate that password and confirm_password match."""
        if data.get('password') != data.get('confirm_password'):
            raise ValidationError('Passwords do not match')
        return data 