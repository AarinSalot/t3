import uuid
import time
from app import db
from app.models.employee import Employee


class Task(db.Model):
    """Task model for storing task information."""
    
    __tablename__ = 'tasks'
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    status = db.Column(db.String(100), nullable=False, default='pending')
    priority = db.Column(db.String(50), nullable=False, default='medium')
    labels = db.Column(db.String(255), nullable=True)
    billable = db.Column(db.Boolean, default=False, nullable=False)
    employees = db.Column(db.JSON, default=list, nullable=False)  # list of employee IDs (synced with project)
    name = db.Column(db.String(255), nullable=False)
    project_id = db.Column(db.String(36), nullable=False, index=True)  # reference to project
    description = db.Column(db.Text, nullable=True)
    deadline = db.Column(db.BigInteger, nullable=True)  # milliseconds timestamp
    created_at = db.Column(db.BigInteger, default=lambda: int(time.time() * 1000), nullable=False)
    updated_at = db.Column(db.BigInteger, default=lambda: int(time.time() * 1000), nullable=False)
    
    def __repr__(self):
        return f'<Task {self.name} (Project: {self.project_id})>'
    
    def update_timestamp(self):
        """Update the updated_at timestamp."""
        self.updated_at = int(time.time() * 1000)
    
    def sync_employees_with_project(self):
        """Sync task employees with project employees."""
        from app.models.project import Project
        project = Project.query.filter_by(id=self.project_id).first()
        if project:
            self.employees = project.employees or []
            self.update_timestamp()
    
    def add_employee(self, employee_id):
        """Add an employee to the task (should be done via project)."""
        if self.employees is None:
            self.employees = []
        if employee_id not in self.employees:
            self.employees = self.employees + [employee_id]
            self.update_timestamp()
    
    def remove_employee(self, employee_id):
        """Remove an employee from the task (should be done via project)."""
        if self.employees and employee_id in self.employees:
            self.employees = [emp_id for emp_id in self.employees if emp_id != employee_id]
            self.update_timestamp()
    
    def to_dict(self):
        """Convert task object to dictionary."""
        return {
            'id': self.id,
            'status': self.status,
            'priority': self.priority,
            'labels': self.labels,
            'billable': self.billable,
            'employees': self.employees or [],
            'name': self.name,
            'project_id': self.project_id,
            'description': self.description,
            'deadline': self.deadline,
            'created_at': self.created_at,
            'updated_at': self.updated_at
        } 