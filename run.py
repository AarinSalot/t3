import os
from app import create_app, db
from app.models.user import User
from app.models.employee import Employee
from app.models.project import Project
from app.models.task import Task

# Create the Flask application
app = create_app()

@app.shell_context_processor
def make_shell_context():
    """Register models for flask shell."""
    return {'db': db, 'User': User, 'Employee': Employee, 'Project': Project, 'Task': Task}

if __name__ == '__main__':
    with app.app_context():
        # Create database tables
        db.create_all()
    
    # Run the application with auto-reload enabled
    app.run(
        host=os.environ.get('HOST', '127.0.0.1'),
        port=int(os.environ.get('PORT', 5000)),
        debug=True,  # Enable debug mode for auto-reload
        use_reloader=True,  # Enable auto-reload on file changes
        use_debugger=True   # Enable interactive debugger
    ) 