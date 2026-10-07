from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from app.models import User, Project, Issue, db

admin_bp = Blueprint('admin', __name__, url_prefix='/admin')

@admin_bp.route('/dashboard')
@login_required
def dashboard():
    if current_user.role != 'ADMIN':
        flash('Access denied.', 'danger')
        return redirect(url_for('auth.login'))
        
    users = User.query.all()
    projects = Project.query.all()
    issues = Issue.query.all()
    return render_template('admin/dashboard.html', users=users, projects=projects, issues=issues)

@admin_bp.route('/users/add', methods=['POST'])
@login_required
def add_user():
    if current_user.role != 'ADMIN':
        return redirect(url_for('auth.login'))
        
    username = request.form.get('username')
    email = request.form.get('email')
    password = request.form.get('password')
    role = request.form.get('role')
    skills = request.form.get('skills')
    
    user = User(username=username, email=email, role=role, skills=skills)
    user.set_password(password)
    db.session.add(user)
    db.session.commit()
    
    flash('User created successfully!', 'success')
    return redirect(url_for('admin.dashboard'))