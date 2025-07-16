from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from marshmallow import ValidationError
from sqlalchemy import or_
from app.schemas.project import (
    ProjectCreateSchema, ProjectUpdateSchema, ProjectResponseSchema, 
    ProjectListSchema
)
from app.models.project import Project
from app.models.employee import Employee
from app import db
import time

projects_bp = Blueprint('projects', __name__)

# Schema instances
project_create_schema = ProjectCreateSchema()
project_update_schema = ProjectUpdateSchema()
project_response_schema = ProjectResponseSchema()
projects_response_schema = ProjectResponseSchema(many=True)
project_list_schema = ProjectListSchema()


def _update_employee_project_relationships(project_id, employees_to_remove, employees_to_add):
    """
    Update bidirectional employee-project relationships from project side.
    
    Args:
        project_id: ID of the project
        employees_to_remove: Set of employee IDs to remove project from
        employees_to_add: Set of employee IDs to add project to
        
    Returns:
        Set of all affected employee IDs
    """
    affected_employees = set()
    
    if not employees_to_remove and not employees_to_add:
        return affected_employees
    
    all_employee_ids = employees_to_remove | employees_to_add
    employees = Employee.query.filter(Employee.id.in_(all_employee_ids)).all()
    
    for employee in employees:
        if employee.id in employees_to_remove:
            # Remove project from employee
            if employee.projects and project_id in employee.projects:
                employee.projects = [pid for pid in employee.projects if pid != project_id]
                employee.update_timestamp()
                db.session.add(employee)
                affected_employees.add(employee.id)
        elif employee.id in employees_to_add:
            # Add project to employee
            if not employee.projects:
                employee.projects = []
            if project_id not in employee.projects:
                employee.projects = employee.projects + [project_id]
                employee.update_timestamp()
                db.session.add(employee)
                affected_employees.add(employee.id)
    
    return affected_employees


def _sync_project_tasks(project_id, employee_ids):
    """
    Sync all tasks for a specific project with the given employee list.
    
    Args:
        project_id: ID of the project whose tasks need syncing
        employee_ids: List of employee IDs to sync to all tasks
    """
    from app.models.task import Task
    
    tasks = Task.query.filter_by(project_id=project_id).all()
    for task in tasks:
        task.employees = employee_ids or []
        task.update_timestamp()
        db.session.add(task)


def _handle_project_employee_updates(project, new_employee_ids, update=True):
    """
    Handle updates to a project's employee relationships and sync dependent tasks.
    
    Args:
        project: Project object to update
        new_employee_ids: List of new employee IDs for the project
        
    Returns:
        Set of employee IDs that were affected by the changes
    """
    # Validate employee IDs exist
    if new_employee_ids:
        existing_employees = Employee.query.filter(Employee.id.in_(new_employee_ids)).all()
        existing_ids = [emp.id for emp in existing_employees]
        invalid_ids = [emp_id for emp_id in new_employee_ids if emp_id not in existing_ids]
        if invalid_ids:
            raise ValueError(f'Invalid employee IDs: {invalid_ids}')
    
    # when creating a project, we need to ensure that all the employees' projects fields are
    # updated, hence 
    old_employee_ids = set((update and project.employees) or [])
    new_employee_ids_set = set(new_employee_ids or [])
    
    employees_to_remove = old_employee_ids - new_employee_ids_set
    employees_to_add = new_employee_ids_set - old_employee_ids

    print(f"Employees to remove: {employees_to_remove}")
    print(f"Employees to add: {employees_to_add}")
    print(f"new employee ids: {new_employee_ids}")
    print(f"old employee ids: {project}")
    
    # Update bidirectional relationships
    affected_employees = _update_employee_project_relationships(
        project.id, employees_to_remove, employees_to_add
    )
    # Update project's employee list
    project.employees = new_employee_ids
    
    # Sync tasks for this project
    _sync_project_tasks(project.id, new_employee_ids)
    
    return affected_employees


@projects_bp.route('/', methods=['GET'])
@jwt_required()
def get_projects():
    """Get all projects with optional filtering."""
    try:
        # Validate query parameters
        query_data = project_list_schema.load(request.args)
    except ValidationError as err:
        return jsonify({'error': 'Invalid query parameters', 'messages': err.messages}), 400
    
    # Build query
    query = Project.query
    
    # Filter by active status
    if query_data.get('active_only'):
        query = query.filter(Project.archived.is_(None))
    
    # Filter by billable status
    if query_data.get('billable_only'):
        query = query.filter(Project.billable == True)
    
    # Search functionality
    if query_data.get('search'):
        search_term = f"%{query_data['search']}%"
        query = query.filter(
            or_(
                Project.name.ilike(search_term),
                Project.description.ilike(search_term)
            )
        )
    
    # Order by creation date (newest first)
    query = query.order_by(Project.created_at.desc())
    
    # Get all projects (no pagination)
    projects = query.all()
    
    return jsonify({
        'projects': projects_response_schema.dump(projects)
    }), 200

@projects_bp.route('/', methods=['POST'])
@jwt_required()
def create_project():
    """Create a new project."""
    try:
        data = project_create_schema.load(request.get_json())
    except ValidationError as err:
        return jsonify({'error': 'Validation failed', 'messages': err.messages}), 400
    
    # Check if project name already exists
    if Project.query.filter_by(name=data['name']).first():
        return jsonify({'error': 'Project name already exists'}), 409
    
    # Create new project
    project = Project(
        name=data['name'],
        description=data.get('description'),
        employees=data.get('employees', []),
        billable=data.get('billable', False),
        deadline=data.get('deadline')
    )

    employee_ids = data.get('employees', [])

    print(f"Employee IDs: {employee_ids}")
    try:
        # First add the project and flush to get an ID
        db.session.add(project)   
        db.session.flush()  # Get the ID without committing
        
        # Now sync bidirectional relationships with employees if any were provided
        if employee_ids:
            _handle_project_employee_updates(project, employee_ids, update=False)
    
        db.session.commit()
        
        return jsonify({
            'message': 'Project created successfully',
            'project': project_response_schema.dump(project)
        }), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': 'Failed to create project'}), 500

@projects_bp.route('/<string:project_id>', methods=['GET'])
@jwt_required()
def get_project(project_id):
    """Get a specific project by ID."""
    project = Project.query.filter_by(id=project_id).first()
    
    if not project:
        return jsonify({'error': 'Project not found'}), 404
    
    return jsonify({
        'project': project_response_schema.dump(project)
    }), 200

@projects_bp.route('/<string:project_id>', methods=['PUT'])
@jwt_required()
def update_project(project_id):
    """Update project information."""
    project = Project.query.filter_by(id=project_id).first()
    
    if not project:
        return jsonify({'error': 'Project not found'}), 404
    
    try:
        data = project_update_schema.load(request.get_json())
    except ValidationError as err:
        return jsonify({'error': 'Validation failed', 'messages': err.messages}), 400
    
    # Check if project name is already taken by another project
    if 'name' in data:
        existing_project = Project.query.filter_by(name=data['name']).first()
        if existing_project and existing_project.id != project_id:
            return jsonify({'error': 'Project name already in use'}), 409
    
    # Update simple fields
    if 'name' in data:
        project.name = data['name']
    if 'description' in data:
        project.description = data['description']
    if 'archived' in data:
        project.archived = data['archived']
    if 'billable' in data:
        project.billable = data['billable']
    if 'deadline' in data:
        project.deadline = data['deadline']
    
    # Handle employee relationships with bidirectional sync and task updates
    if 'employees' in data:
        try:
            _handle_project_employee_updates(project, data['employees'])
        except ValueError as e:
            return jsonify({'error': str(e)}), 400
    
    # Update timestamp
    project.update_timestamp()
    
    try:
        db.session.commit()
        return jsonify({
            'message': 'Project updated successfully',
            'project': project_response_schema.dump(project)
        }), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': 'Failed to update project'}), 500


@projects_bp.route('/<string:project_id>', methods=['DELETE'])
@jwt_required()
def delete_project(project_id):
    """Delete a project."""
    project = Project.query.filter_by(id=project_id).first()
    
    if not project:
        return jsonify({'error': 'Project not found'}), 404
    
    try:
        # Remove project from all associated employees
        for employee_id in project.employees or []:
            employee = Employee.query.filter_by(id=employee_id).first()
            if employee:
                employee.remove_project(project.id)
        
        db.session.delete(project)
        db.session.commit()
        return jsonify({'message': 'Project deleted successfully'}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': 'Failed to delete project'}), 500

@projects_bp.route('/<string:project_id>/employees', methods=['POST'])
@jwt_required()
def add_employee_to_project(project_id):
    """Add an employee to a project."""
    project = Project.query.filter_by(id=project_id).first()
    
    if not project:
        return jsonify({'error': 'Project not found'}), 404
    
    try:
        data = request.get_json()
        if not data or 'employee_id' not in data:
            return jsonify({'error': 'employee_id is required'}), 400
    except Exception as err:
        return jsonify({'error': 'Invalid JSON'}), 400
    
    employee_id = data['employee_id']

    print(f"Employee ID: {employee_id}")
    
    # Check if employee exists
    employee = Employee.query.filter_by(id=employee_id).first()
    if not employee:
        return jsonify({'error': 'Employee not found'}), 404
    
    # Check if employee is already assigned
    if project.employees and employee_id in project.employees:
        return jsonify({'error': 'Employee already assigned to project'}), 409
    
    try:
        project.add_employee(employee_id)
        db.session.commit()
        
        return jsonify({
            'message': 'Employee added to project successfully',
            'project': project_response_schema.dump(project)
        }), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': 'Failed to add employee to project'}), 500

@projects_bp.route('/<string:project_id>/employees/<string:employee_id>', methods=['DELETE'])
@jwt_required()
def remove_employee_from_project(project_id, employee_id):
    """Remove an employee from a project."""
    project = Project.query.filter_by(id=project_id).first()
    
    if not project:
        return jsonify({'error': 'Project not found'}), 404
    
    # Check if employee is assigned
    if not project.employees or employee_id not in project.employees:
        return jsonify({'error': 'Employee not assigned to project'}), 404
    
    try:
        project.remove_employee(employee_id)
        db.session.commit()
        
        return jsonify({
            'message': 'Employee removed from project successfully',
            'project': project_response_schema.dump(project)
        }), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': 'Failed to remove employee from project'}), 500 