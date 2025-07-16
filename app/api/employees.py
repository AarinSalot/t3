from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from marshmallow import ValidationError
from sqlalchemy import or_
from app.schemas.employee import (
    EmployeeCreateSchema, EmployeeUpdateSchema, EmployeeResponseSchema,
    EmployeeListSchema, ProjectOperationSchema
)
from app.models.employee import Employee
from app.models.project import Project
from app import db
import time

employees_bp = Blueprint('employees', __name__)

# Schema instances
employee_create_schema = EmployeeCreateSchema()
employee_update_schema = EmployeeUpdateSchema()
employee_response_schema = EmployeeResponseSchema()
employees_response_schema = EmployeeResponseSchema(many=True)
employee_list_schema = EmployeeListSchema()
project_operation_schema = ProjectOperationSchema()


def _update_project_employee_relationships(employee_id, projects_to_remove, projects_to_add):
    """
    Update bidirectional employee-project relationships.
    
    Args:
        employee_id: ID of the employee
        projects_to_remove: Set of project IDs to remove employee from
        projects_to_add: Set of project IDs to add employee to
        
    Returns:
        Set of all affected project IDs
    """
    affected_projects = set()
    
    if not projects_to_remove and not projects_to_add:
        return affected_projects
    
    all_project_ids = projects_to_remove | projects_to_add
    projects = Project.query.filter(Project.id.in_(all_project_ids)).all()
    
    for project in projects:
        if project.id in projects_to_remove:
            # Remove employee from project
            if project.employees and employee_id in project.employees:
                project.employees = [emp_id for emp_id in project.employees if emp_id != employee_id]
                project.update_timestamp()
                db.session.add(project)
                affected_projects.add(project.id)
                
        elif project.id in projects_to_add:
            # Add employee to project
            if not project.employees:
                project.employees = []
            if employee_id not in project.employees:
                project.employees = project.employees + [employee_id]
                project.update_timestamp()
                db.session.add(project)
                affected_projects.add(project.id)
    
    return affected_projects


def _sync_tasks_with_projects(project_ids):
    """
    Synchronize task employee lists with their corresponding project employee lists.
    
    Args:
        project_ids: Set of project IDs whose tasks need to be synced
    """
    if not project_ids:
        return
    
    from app.models.task import Task
    
    # Get all tasks for the affected projects
    tasks = Task.query.filter(Task.project_id.in_(project_ids)).all()
    
    # Create a lookup for projects to avoid repeated queries
    projects = Project.query.filter(Project.id.in_(project_ids)).all()
    project_lookup = {project.id: project for project in projects}
    
    for task in tasks:
        project = project_lookup.get(task.project_id)
        if project:
            task.employees = project.employees or []
            task.update_timestamp()
            db.session.add(task)


def _handle_employee_project_updates(employee, new_projects):
    """
    Handle updates to an employee's project relationships and sync dependent tasks.
    
    Args:
        employee: Employee object to update
        new_projects: List of new project IDs for the employee
        
    Returns:
        Set of project IDs that were affected by the changes
    """
    old_projects = set(employee.projects or [])
    new_projects_set = set(new_projects)
    
    projects_to_remove = old_projects - new_projects_set
    projects_to_add = new_projects_set - old_projects
    
    # Update bidirectional relationships
    affected_projects = _update_project_employee_relationships(
        employee.id, projects_to_remove, projects_to_add
    )
    
    # Update employee's project list
    employee.projects = list(new_projects_set)
    
    # Sync tasks for affected projects
    if affected_projects:
        _sync_tasks_with_projects(affected_projects)
    
    return affected_projects


@employees_bp.route('/', methods=['GET'])
@jwt_required()
def get_employees():
    """Get all employees with optional filtering."""
    try:
        # Validate query parameters
        query_data = employee_list_schema.load(request.args)
    except ValidationError as err:
        return jsonify({'error': 'Invalid query parameters', 'messages': err.messages}), 400
    
    # Build query
    query = Employee.query
    
    # Filter by active status
    if query_data.get('active_only'):
        query = query.filter(Employee.deactivated.is_(None))
    
    # Search functionality
    if query_data.get('search'):
        search_term = f"%{query_data['search']}%"
        query = query.filter(
            or_(
                Employee.name.ilike(search_term),
                Employee.email.ilike(search_term)
            )
        )
    
    # Order by creation date (newest first)
    query = query.order_by(Employee.created_at.desc())
    
    # Get all employees (no pagination)
    employees = query.all()
    
    return jsonify({
        'employees': employees_response_schema.dump(employees)
    }), 200

@employees_bp.route('/', methods=['POST'])
@jwt_required()
def create_employee():
    """Create a new employee."""
    try:
        data = employee_create_schema.load(request.get_json())
    except ValidationError as err:
        return jsonify({'error': 'Validation failed', 'messages': err.messages}), 400
    
    # Check if email already exists
    if Employee.query.filter_by(email=data['email']).first():
        return jsonify({'error': 'Email already exists'}), 409
    
    # Create new employee
    employee = Employee(
        name=data['name'],
        email=data['email'],
        projects=data.get('projects', []),
        invited=data.get('invited')
    )
    
    try:
        db.session.add(employee)
        db.session.commit()
        
        return jsonify({
            'message': 'Employee created successfully',
            'employee': employee_response_schema.dump(employee)
        }), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': 'Failed to create employee'}), 500

@employees_bp.route('/<string:employee_id>', methods=['GET'])
@jwt_required()
def get_employee(employee_id):
    """Get a specific employee by ID."""
    employee = Employee.query.filter_by(id=employee_id).first()
    
    if not employee:
        return jsonify({'error': 'Employee not found'}), 404
    
    return jsonify({
        'employee': employee_response_schema.dump(employee)
    }), 200

@employees_bp.route('/<string:employee_id>', methods=['PUT'])
@jwt_required()
def update_employee(employee_id):
    """Update employee information."""
    employee = Employee.query.filter_by(id=employee_id).first()
    
    if not employee:
        return jsonify({'error': 'Employee not found'}), 404
    
    try:
        data = employee_update_schema.load(request.get_json())
    except ValidationError as err:
        return jsonify({'error': 'Validation failed', 'messages': err.messages}), 400
    
    # Check if email is already taken by another employee
    if 'email' in data:
        existing_employee = Employee.query.filter_by(email=data['email']).first()
        if existing_employee and existing_employee.id != employee_id:
            return jsonify({'error': 'Email already in use'}), 409
    
    # Update simple fields
    if 'name' in data:
        employee.name = data['name']
    if 'email' in data:
        employee.email = data['email']
    if 'invited' in data:
        employee.invited = data['invited']
    if 'deactivated' in data:
        employee.deactivated = data['deactivated']
    
    # Handle project relationships with bidirectional sync
    if 'projects' in data:
        _handle_employee_project_updates(employee, data['projects'])
    
    # Update timestamp
    employee.update_timestamp()
    
    try:        
        db.session.commit()
        
        return jsonify({
            'message': 'Employee updated successfully',
            'employee': employee_response_schema.dump(employee)
        }), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': 'Failed to update employee'}), 500


@employees_bp.route('/deactivate/<string:employee_id>', methods=['POST'])
@jwt_required()
def deactivate_employee(employee_id):
    """Deactivate an employee."""
    employee = Employee.query.filter_by(id=employee_id).first()
    
    if not employee:
        return jsonify({'error': 'Employee not found'}), 404
    
    if employee.deactivated:
        return jsonify({'error': 'Employee is already deactivated'}), 409
    
    try:
        employee.deactivate()
        db.session.commit()
        
        return jsonify({
            'message': 'Employee deactivated successfully',
            'employee': employee_response_schema.dump(employee)
        }), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': 'Failed to deactivate employee'}), 500

# Reactivate functionality removed - use PUT endpoint to set deactivated to null