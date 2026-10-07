from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required
from app.models import Sprint, Issue, db

sprint_bp = Blueprint('sprint', __name__, url_prefix='/sprints')

@sprint_bp.route('/board')
@login_required
def board():
    sprints = Sprint.query.all()
    backlog_issues = Issue.query.filter_by(sprint_id=None).all()
    return render_template('sprint/board.html', sprints=sprints, backlog=backlog_issues)

@sprint_bp.route('/create', methods=['POST'])
@login_required
def create_sprint():
    name = request.form.get('name')
    goal = request.form.get('goal')
    
    new_sprint = Sprint(name=name, goal=goal, status='PLANNING')
    db.session.add(new_sprint)
    db.session.commit()
    flash('Sprint created successfully!', 'success')
    return redirect(url_for('sprint.board'))

@sprint_bp.route('/add-issue/<int:sprint_id>/<int:issue_id>', methods=['POST'])
@login_required
def add_issue_to_sprint(sprint_id, issue_id):
    issue = Issue.query.get_or_404(issue_id)
    issue.sprint_id = sprint_id
    db.session.commit()
    return jsonify({'status': 'success', 'message': f'Issue #{issue.id} added to sprint.'})

@sprint_bp.route('/analytics')
@login_required
def analytics():
    total_issues = Issue.query.count()
    resolved_count = Issue.query.filter_by(status='RESOLVED').count()
    open_count = Issue.query.filter_by(status='OPEN').count()
    in_progress_count = Issue.query.filter_by(status='IN_PROGRESS').count()
    
    # Priority counts for the bar chart
    critical_count = Issue.query.filter_by(priority='Critical').count()
    major_count = Issue.query.filter_by(priority='Major').count()
    minor_count = Issue.query.filter_by(priority='Minor').count()
    trivial_count = Issue.query.filter_by(priority='Trivial').count()
    
    # Completed sprints for the velocity tracker table
    completed_sprints = Sprint.query.filter_by(status='COMPLETED').all()
    
    return render_template(
        'reports/analytics.html',
        total_issues=total_issues,
        open_count=open_count,
        in_progress_count=in_progress_count,
        resolved_count=resolved_count,
        critical_count=critical_count,
        major_count=major_count,
        minor_count=minor_count,
        trivial_count=trivial_count,
        completed_sprints=completed_sprints
    )

@sprint_bp.route('/<int:sprint_id>/complete', methods=['POST'])
@login_required
def complete_sprint(sprint_id):
    sprint = Sprint.query.get_or_404(sprint_id)
    
    if sprint.status == 'COMPLETED':
        flash('This sprint is already completed.', 'warning')
        return redirect(url_for('sprint.board'))
        
    resolved_issues_count = sum(
        1 for issue in sprint.issues if issue.status in ['RESOLVED', 'CLOSED']
    )
    
    sprint.status = 'COMPLETED'
    
    if hasattr(sprint, 'velocity'):
        sprint.velocity = resolved_issues_count
        
    db.session.commit()
    
    flash(f'Sprint "{sprint.name}" completed! Team Velocity (Bugs Resolved): {resolved_issues_count}', 'success')
    return redirect(url_for('sprint.board'))