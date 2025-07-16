from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from marshmallow import ValidationError
from sqlalchemy import or_, and_
from app.schemas.task import (
    TaskCreateSchema, TaskUpdateSchema, TaskResponseSchema,
    TaskListSchema
)
from app.models.task import Task
from app.models.project import Project
from app.models.employee import Employee
from app import db
import time

tasks_bp = Blueprint('tasks', __name__)

# Schema instances
task_create_schema = TaskCreateSchema()
task_update_schema = TaskUpdateSchema()
task_response_schema = TaskResponseSchema()
tasks_response_schema = TaskResponseSchema(many=True)
task_list_schema = TaskListSchema()

@tasks_bp.route('/', methods=['GET'])
@jwt_required()
def get_tasks():
    """Get all tasks with optional filtering."""
    try:
        # Validate query parameters
        query_data = task_list_schema.load(request.args)
    except ValidationError as err:
        return jsonify({'error': 'Invalid query parameters', 'messages': err.messages}), 400
    
    # Build query
    query = Task.query
    
    # Filter by project
    if query_data.get('project_id'):
        query = query.filter(Task.project_id == query_data['project_id'])
    
    # Filter by status
    if query_data.get('status'):
        query = query.filter(Task.status == query_data['status'])
    
    # Filter by priority
    if query_data.get('priority'):
        query = query.filter(Task.priority == query_data['priority'])
    
    # Filter by billable status
    if query_data.get('billable') is not None:
        query = query.filter(Task.billable == query_data['billable'])
    
    # Filter by employee assignment
    if query_data.get('employee_id'):
        # Tasks that have this employee in their employees list
        query = query.filter(Task.employees.contains([query_data['employee_id']]))
    
    # Search functionality
    if query_data.get('search'):
        search_term = f"%{query_data['search']}%"
        query = query.filter(
            or_(
                Task.name.ilike(search_term),
                Task.description.ilike(search_term),
                Task.labels.ilike(search_term)
            )
        )
    
    # Order by creation date (newest first)
    query = query.order_by(Task.created_at.desc())
    
    # Get all tasks (no pagination)
    tasks = query.all()
    
    return jsonify({
        'tasks': tasks_response_schema.dump(tasks)
    }), 200


@tasks_bp.route('/', methods=['POST'])
@jwt_required()
def create_task():
    """Create a new task."""
    try:
        data = task_create_schema.load(request.get_json())
    except ValidationError as err:
        return jsonify({'error': 'Validation failed', 'messages': err.messages}), 400
    
    # Validate project exists
    project = Project.query.filter_by(id=data['project_id']).first()
    if not project:
        return jsonify({'error': 'Project not found'}), 404
    
    # Create new task with project's employees
    task = Task(
        name=data['name'],
        project_id=data['project_id'],
        description=data.get('description'),
        status=data.get('status', 'pending'),
        priority=data.get('priority', 'medium'),
        labels=data.get('labels'),
        billable=data.get('billable', False),
        deadline=data.get('deadline'),
        employees=project.employees or []  # Sync with project employees
    )
    
    try:
        db.session.add(task)
        db.session.commit()
        
        return jsonify({
            'message': 'Task created successfully',
            'task': task_response_schema.dump(task)
        }), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': 'Failed to create task'}), 500


@tasks_bp.route('/<string:task_id>', methods=['GET'])
@jwt_required()
def get_task(task_id):
    """Get a specific task by ID."""
    task = Task.query.filter_by(id=task_id).first()
    
    if not task:
        return jsonify({'error': 'Task not found'}), 404
    
    return jsonify({
        'task': task_response_schema.dump(task)
    }), 200


@tasks_bp.route('/<string:task_id>', methods=['PUT'])
@jwt_required()
def update_task(task_id):
    """Update an existing task."""
    task = Task.query.filter_by(id=task_id).first()
    
    if not task:
        return jsonify({'error': 'Task not found'}), 404
    
    try:
        data = task_update_schema.load(request.get_json())
    except ValidationError as err:
        return jsonify({'error': 'Validation failed', 'messages': err.messages}), 400
    
    # Update task fields
    if 'name' in data:
        task.name = data['name']
    if 'description' in data:
        task.description = data['description']
    if 'status' in data:
        task.status = data['status']
    if 'priority' in data:
        task.priority = data['priority']
    if 'labels' in data:
        task.labels = data['labels']
    if 'billable' in data:
        task.billable = data['billable']
    if 'deadline' in data:
        task.deadline = data['deadline']
    
    # Always sync employees with project when updating
    task.sync_employees_with_project()
    
    # Update timestamp
    task.update_timestamp()
    
    try:
        db.session.commit()
        return jsonify({
            'message': 'Task updated successfully',
            'task': task_response_schema.dump(task)
        }), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': 'Failed to update task'}), 500


@tasks_bp.route('/<string:task_id>', methods=['DELETE'])
@jwt_required()
def delete_task(task_id):
    """Delete a task."""
    task = Task.query.filter_by(id=task_id).first()
    
    if not task:
        return jsonify({'error': 'Task not found'}), 404
    
    try:
        db.session.delete(task)
        db.session.commit()
        
        return jsonify({
            'message': 'Task deleted successfully'
        }), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': 'Failed to delete task'}), 500 