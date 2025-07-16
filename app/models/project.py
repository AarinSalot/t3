import uuid
import time
from app import db
from app.models.employee import Employee


class Project(db.Model):
    """Project model for storing project information."""
    
    __tablename__ = 'projects'
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name = db.Column(db.String(255), nullable=False)
    description = db.Column(db.Text, nullable=True)
    archived = db.Column(db.Boolean, default=False, nullable=False)
    billable = db.Column(db.Boolean, default=False, nullable=False)
    deadline = db.Column(db.BigInteger, nullable=True)  # milliseconds timestamp
    employees = db.Column(db.JSON, default=list, nullable=False)  # list of employee IDs
    created_at = db.Column(db.BigInteger, default=lambda: int(time.time() * 1000), nullable=False)
    updated_at = db.Column(db.BigInteger, default=lambda: int(time.time() * 1000), nullable=False)
    
    def __repr__(self):
        return f'<Project {self.name}>'
    
    def update_timestamp(self):
        """Update the updated_at timestamp."""
        self.updated_at = int(time.time() * 1000)
    
    def add_employee(self, employee_id):
        """Add an employee to the project."""
        if self.employees is None:
            self.employees = []
        if employee_id not in self.employees:
            self.employees = self.employees + [employee_id]
            self.update_timestamp()
            
            # Update the employee's projects list
            employee = Employee.query.filter_by(id=employee_id).first()
            if employee:
                employee.add_project(self.id)
            
            # Sync all tasks in this project using the helper function
            self._sync_project_tasks()
    
    def remove_employee(self, employee_id):
        """Remove an employee from the project."""
        if self.employees and employee_id in self.employees:
            self.employees = [emp_id for emp_id in self.employees if emp_id != employee_id]
            self.update_timestamp()
            
            # Update the employee's projects list
            employee = Employee.query.filter_by(id=employee_id).first()
            if employee:
                employee.remove_project(self.id)
            
            # Sync all tasks in this project using the helper function
            self._sync_project_tasks()
    
    def _sync_project_tasks(self):
        """Sync all tasks for this specific project with the current employee list."""
        from app.models.task import Task
        
        tasks = Task.query.filter_by(project_id=self.id).all()
        for task in tasks:
            task.employees = self.employees or []
            task.update_timestamp()
            db.session.add(task)
    
    def archive(self):
        """Archive the project."""
        self.archived = True
        self.update_timestamp()
    
    def unarchive(self):
        """Unarchive the project."""
        self.archived = False
        self.update_timestamp()
    

    
    def to_dict(self):
        """Convert project object to dictionary."""
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'archived': self.archived,
            'billable': self.billable,
            'deadline': self.deadline,
            'employees': self.employees or [],
            'created_at': self.created_at,
            'updated_at': self.updated_at
        } 