from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from app.models import db, Issue

developer_bp = Blueprint('developer', __name__, url_prefix='/developer')

@developer_bp.route('/dashboard')
@login_required
def developer_dashboard():
    # Safely check whether your database model maps via developer_id or assignee_id
    if hasattr(Issue, 'developer_id'):
        assigned_issues = Issue.query.filter_by(developer_id=current_user.id).all()
    elif hasattr(Issue, 'assignee_id'):
        assigned_issues = Issue.query.filter_by(assignee_id=current_user.id).all()
    else:
        assigned_issues = []
    
    total_assigned = len(assigned_issues)
    in_progress_count = sum(1 for issue in assigned_issues if issue.status and issue.status == 'IN_PROGRESS')
    resolved_count = sum(1 for issue in assigned_issues if issue.status and issue.status in ['RESOLVED', 'CLOSED'])
    open_count = sum(1 for issue in assigned_issues if issue.status and issue.status in ['OPEN', 'REPORTED', 'ASSIGNED'])
    
    resolution_rate = round((resolved_count / total_assigned * 100), 1) if total_assigned > 0 else 0.0

    return render_template(
        'developer/dashboard.html',
        assigned_issues=assigned_issues,
        total_assigned=total_assigned,
        in_progress_count=in_progress_count,
        resolved_count=resolved_count,
        open_count=open_count,
        resolution_rate=resolution_rate
    )

@developer_bp.route('/issues/<int:id>/update_status', methods=['POST'])
@login_required
def update_status(id):
    issue = Issue.query.get_or_404(id)
    new_status = request.form.get('status')
    
    if new_status in ['OPEN', 'IN_PROGRESS', 'RESOLVED', 'CLOSED']:
        old_status = issue.status
        issue.status = new_status
        db.session.commit()
        
        flash(f'Status updated from {old_status} to {new_status}!', 'success')
    
    return redirect(url_for('developer.developer_dashboard'))