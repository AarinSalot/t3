from datetime import datetime
import time
import uuid
import json
from app import db
from sqlalchemy import Text, TypeDecorator

class JSONField(TypeDecorator):
    """Custom JSON field that works with SQLite."""
    impl = Text
    cache_ok = True

    def process_bind_param(self, value, dialect):
        if value is not None:
            return json.dumps(value)
        return value

    def process_result_value(self, value, dialect):
        if value is not None:
            return json.loads(value)
        return value

class Employee(db.Model):
    """Employee model for storing employee information."""
    
    __tablename__ = 'employees'
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(255), unique=True, nullable=False, index=True)
    projects = db.Column(JSONField, nullable=False, default=lambda: [])  # Array of project IDs
    deactivated = db.Column(db.BigInteger, nullable=True)  # Timestamp in milliseconds
    invited = db.Column(db.BigInteger, nullable=True)  # Timestamp in milliseconds
    created_at = db.Column(db.BigInteger, nullable=False, default=lambda: int(time.time() * 1000))
    updated_at = db.Column(db.BigInteger, nullable=False, default=lambda: int(time.time() * 1000))
    
    def __repr__(self):
        return f'<Employee {self.name} ({self.email})>'
    
    def update_timestamp(self):
        """Update the updated_at timestamp."""
        self.updated_at = int(time.time() * 1000)
    
    def deactivate(self):
        """Mark employee as deactivated."""
        self.deactivated = int(time.time() * 1000)
        self.update_timestamp()
    
    def reactivate(self):
        """Reactivate employee."""
        self.deactivated = None
        self.update_timestamp()
    
    def add_project(self, project_id):
        """Add a project ID to the employee's projects list."""
        if self.projects is None:
            self.projects = []
        if project_id not in self.projects:
            self.projects = self.projects + [project_id]  # Create new list for SQLAlchemy to detect change
            self.update_timestamp()
            
            # Update the project's employees list (bidirectional relationship)
            from app.models.project import Project
            project = Project.query.filter_by(id=project_id).first()
            if project and (not project.employees or self.id not in project.employees):
                if project.employees is None:
                    project.employees = []
                project.employees = project.employees + [self.id]
                project.update_timestamp()
    
    def remove_project(self, project_id):
        """Remove a project ID from the employee's projects list."""
        if self.projects and project_id in self.projects:
            self.projects = [pid for pid in self.projects if pid != project_id]
            self.update_timestamp()
            
            # Update the project's employees list (bidirectional relationship)
            from app.models.project import Project
            project = Project.query.filter_by(id=project_id).first()
            if project and project.employees and self.id in project.employees:
                project.employees = [emp_id for emp_id in project.employees if emp_id != self.id]
                project.update_timestamp()
    
    def to_dict(self):
        """Convert employee object to dictionary."""
        return {
            'id': self.id,
            'name': self.name,
            'email': self.email,
            'projects': self.projects or [],
            'deactivated': self.deactivated,
            'invited': self.invited,
            'created_at': self.created_at,
            'updated_at': self.updated_at
        } 