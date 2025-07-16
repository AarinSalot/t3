# Flask API with Blueprints and Schema Validation

A well-structured Flask application featuring modular blueprints, schema validation with Marshmallow, JWT authentication, and SQLAlchemy ORM.

## Features

- **Modular Blueprint Architecture**: Organized API endpoints using Flask blueprints
- **Schema Validation**: Request/response validation using Marshmallow
- **JWT Authentication**: Secure token-based authentication with refresh tokens
- **Database ORM**: SQLAlchemy for database operations with migrations
- **CORS Support**: Cross-origin request handling
- **Configuration Management**: Environment-based configuration
- **Password Hashing**: Secure password storage using bcrypt

## Project Structure

```
t3/
├── app/
│   ├── __init__.py              # Flask app factory
│   ├── api/                     # API blueprints
│   │   ├── __init__.py
│   │   ├── auth.py              # Authentication endpoints
│   │   ├── users.py             # User management endpoints
│   │   └── main.py              # General API endpoints
│   ├── models/                  # Database models
│   │   ├── __init__.py
│   │   └── user.py              # User model
│   ├── schemas/                 # Marshmallow schemas
│   │   ├── __init__.py
│   │   ├── auth.py              # Auth validation schemas
│   │   └── user.py              # User validation schemas
│   └── utils/                   # Utility functions
├── config.py                    # Configuration settings
├── requirements.txt             # Python dependencies
├── run.py                      # Application entry point
├── .env.example                # Environment variables example
└── README.md                   # This file
```

## Installation

1. **Clone the repository and navigate to the project directory**

2. **Create a virtual environment**:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

4. **Set up environment variables**:
   ```bash
   cp .env.example .env
   # Edit .env with your configuration
   ```

5. **Initialize the database**:
   ```bash
   python run.py
   # Database tables will be created automatically on first run
   ```

## Usage

### Running the Application

```bash
python run.py
```

The API will be available at `http://127.0.0.1:5000`

### Environment Variables

Configure the following variables in your `.env` file:

- `FLASK_ENV`: Environment (development/production)
- `SECRET_KEY`: Flask secret key
- `JWT_SECRET_KEY`: JWT signing key
- `DEV_DATABASE_URL`: Development database URL
- `DATABASE_URL`: Production database URL
- `HOST`: Server host (default: 127.0.0.1)
- `PORT`: Server port (default: 5000)

## API Endpoints

### Health Check
- `GET /health` - API health status

### Authentication
- `POST /api/auth/register` - User registration
- `POST /api/auth/login` - User login
- `POST /api/auth/refresh` - Refresh access token
- `GET /api/auth/me` - Get current user info

### Users
- `GET /api/users/` - List all users (requires auth)
- `GET /api/users/<id>` - Get user by ID (requires auth)
- `PUT /api/users/<id>` - Update user (requires auth)
- `DELETE /api/users/<id>` - Delete user (requires auth)

### Employees
- `GET /api/v1/employee/` - List all employees with optional filtering (requires auth)
- `POST /api/v1/employee/` - Create new employee (requires auth)
- `GET /api/v1/employee/<id>` - Get employee by ID (requires auth)
- `PUT /api/v1/employee/<id>` - Update employee (name, email, projects, etc.) (requires auth)
- `POST /api/v1/employee/deactivate/<id>` - Deactivate employee (requires auth)

**Notes**: 
- Employees are never permanently deleted. Use the deactivate endpoint instead.
- Project management (add/remove) is handled through the PUT endpoint.
- To reactivate an employee, use the PUT endpoint to set `deactivated: null`.

### Projects
- `GET /api/v1/project/` - List all projects with optional filtering (requires auth)
- `POST /api/v1/project/` - Create new project (requires auth)
- `GET /api/v1/project/<id>` - Get project by ID (requires auth)
- `PUT /api/v1/project/<id>` - Update project (name, description, employees, etc.) (requires auth)
- `DELETE /api/v1/project/<id>` - Delete project (requires auth)
- `POST /api/v1/project/<id>/employees` - Add employee to project (requires auth)
- `DELETE /api/v1/project/<id>/employees/<employee_id>` - Remove employee from project (requires auth)

**Notes**:
- Projects support bidirectional relationships with employees.
- When employees are added/removed from projects, both entities are automatically updated.
- Projects can be filtered by archived status, billable status, and searched by name/description.

### General
- `GET /api/` - API information
- `GET /api/status` - API status

## Example Requests

### Register a new user
```bash
curl -X POST http://127.0.0.1:5000/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "name": "John Doe",
    "email": "john@example.com",
    "password": "securepassword",
    "confirm_password": "securepassword"
  }'
```

### Login
```bash
curl -X POST http://127.0.0.1:5000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "john@example.com",
    "password": "securepassword"
  }'
```

### Access protected endpoint
```bash
curl -X GET http://127.0.0.1:5000/api/auth/me \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

### Create an employee
```bash
curl -X POST http://127.0.0.1:5000/api/v1/employee/ \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "John Doe",
    "email": "john.doe@company.com",
    "projects": ["project-1", "project-2"],
    "invited": 1640995200000
  }'
```

### Get employees with filtering
```bash
# Get all active employees
curl -X GET "http://127.0.0.1:5000/api/v1/employee/?active_only=true" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"

# Search for employees
curl -X GET "http://127.0.0.1:5000/api/v1/employee/?search=john" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

### Update employee (including projects)
```bash
# Update name and add/modify projects
curl -X PUT http://127.0.0.1:5000/api/v1/employee/EMPLOYEE_ID \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Updated Name",
    "projects": ["project-1", "project-2", "new-project"]
  }'

# Reactivate employee (set deactivated to null)
curl -X PUT http://127.0.0.1:5000/api/v1/employee/EMPLOYEE_ID \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"deactivated": null}'
```

### Deactivate employee
```bash
curl -X POST http://127.0.0.1:5000/api/v1/employee/deactivate/EMPLOYEE_ID \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

### Create a project
```bash
curl -X POST http://127.0.0.1:5000/api/v1/project/ \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Project Alpha",
    "description": "A new project for development",
    "billable": true,
    "deadline": 1672531200000,
    "employees": ["EMPLOYEE_ID_1", "EMPLOYEE_ID_2"]
  }'
```

### Get projects with filtering
```bash
# Get all active (non-archived) projects
curl -X GET "http://127.0.0.1:5000/api/v1/project/?active_only=true" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"

# Search for projects
curl -X GET "http://127.0.0.1:5000/api/v1/project/?search=Alpha" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"

# Get billable projects only
curl -X GET "http://127.0.0.1:5000/api/v1/project/?billable_only=true" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

### Update project with employee management
```bash
# Update project details and employee assignments
curl -X PUT http://127.0.0.1:5000/api/v1/project/PROJECT_ID \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "description": "Updated project description",
    "archived": false,
    "employees": ["EMPLOYEE_ID_1", "EMPLOYEE_ID_3"]
  }'
```

### Add employee to project
```bash
curl -X POST http://127.0.0.1:5000/api/v1/project/PROJECT_ID/employees \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"employee_id": "EMPLOYEE_ID"}'
```

## Development

### Flask Shell
For interactive database operations:
```bash
flask shell
# Access db and User model directly
```

### Database Migrations
If you want to use Flask-Migrate for more advanced database management:
```bash
flask db init
flask db migrate -m "Initial migration"
flask db upgrade
```

## Security Features

- Password hashing using bcrypt
- JWT tokens with configurable expiration
- Protected routes requiring authentication
- User authorization checks
- Input validation and sanitization

## Dependencies

- **Flask**: Web framework
- **Flask-SQLAlchemy**: Database ORM
- **Flask-Migrate**: Database migrations
- **Flask-CORS**: Cross-origin resource sharing
- **Flask-JWT-Extended**: JWT authentication
- **Marshmallow**: Schema validation and serialization
- **bcrypt**: Password hashing
- **python-dotenv**: Environment variable management

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## License

This project is open source and available under the MIT License.
