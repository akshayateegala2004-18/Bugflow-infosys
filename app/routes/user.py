import os
from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename
from app.models import Issue, Project, User, Sprint, Comment, Attachment, AuditLog, Notification, db
from app.utils import calculate_priority_score, log_activity
from app.matcher import recommend_developers

user_bp = Blueprint('user', __name__, url_prefix='/user')

@user_bp.route('/dashboard')
@login_required
def dashboard():
    issues = Issue.query.all()
    projects = Project.query.all()
    users = User.query.all()
    return render_template('user/dashboard.html', issues=issues, projects=projects, users=users)

@user_bp.route('/projects')
@login_required
def projects():
    all_projects = Project.query.all()
    return render_template('user/project.html', projects=all_projects)

@user_bp.route('/analytics')
@login_required
def analytics():
    issues = Issue.query.all()
    total_issues = len(issues)
    resolved_count = len([i for i in issues if i.status == 'RESOLVED'])
    open_count = len([i for i in issues if i.status in ['OPEN', 'REPORTED', 'TRIAGED']])
    in_progress_count = len([i for i in issues if i.status == 'IN_PROGRESS'])
    
    critical_count = len([i for i in issues if i.priority and i.priority.upper() in ['CRITICAL', 'URGENT']])
    major_count = len([i for i in issues if i.priority and i.priority.upper() == 'MAJOR'])
    minor_count = len([i for i in issues if i.priority and i.priority.upper() == 'MINOR'])
    trivial_count = len([i for i in issues if i.priority and i.priority.upper() in ['TRIVIAL', 'LOW']])

    return render_template('user/analytics.html', 
                           total_issues=total_issues, 
                           resolved_count=resolved_count, 
                           open_count=open_count, 
                           in_progress_count=in_progress_count, 
                           critical_count=critical_count,
                           major_count=major_count,
                           minor_count=minor_count,
                           trivial_count=trivial_count,
                           issues=issues)

@user_bp.route('/reports')
@login_required
def reports():
    issues = Issue.query.all()
    return render_template('user/analytics.html', issues=issues)

@user_bp.route('/logout')
@login_required
def logout():
    return redirect(url_for('auth.logout'))

@user_bp.route('/create-issue', methods=['GET', 'POST'])
@login_required
def create_issue():
    projects = Project.query.all()
    assignees = User.query.all()
    
    if request.method == 'POST':
        title = request.form.get('title')
        description = request.form.get('description')
        category = request.form.get('category')
        severity = request.form.get('severity')
        project_id = request.form.get('project_id')
        environment = request.form.get('environment')
        affected_module = request.form.get('affected_module')
        reproduction_steps = request.form.get('reproduction_steps')
        manual_assignee_id = request.form.get('developer_id')
        user_priority_override = request.form.get('priority')
        
        score, level = calculate_priority_score(severity, category)
        final_priority = user_priority_override if user_priority_override else level
        
        if manual_assignee_id:
            assigned_dev_id = manual_assignee_id
        else:
            developers_only = [u for u in assignees if u.role and u.role.upper() == 'DEVELOPER']
            recs = recommend_developers(f"{title} {description} {affected_module}", developers_only)
            assigned_dev_id = recs[0]['developer'].id if recs else None

        new_issue = Issue(
            title=title,
            description=description,
            category=category,
            severity=severity,
            priority=final_priority,
            priority_score=score,
            project_id=project_id,
            reporter_id=current_user.id,
            developer_id=assigned_dev_id,
            environment=environment,
            affected_module=affected_module,
            reproduction_steps=reproduction_steps,
            status='REPORTED'
        )
        
        db.session.add(new_issue)
        db.session.commit()
        log_activity(f"User created Bug #{new_issue.id}: {title}", current_user.id)
        flash('Issue created successfully with automated triage!', 'success')
        return redirect(url_for('user.dashboard'))
        
    return render_template('user/create_issue.html', projects=projects, developers=assignees)

@user_bp.route('/sprints-workflow', methods=['GET', 'POST'])
@login_required
def sprints_workflow():
    if request.method == 'POST':
        name = request.form.get('name')
        if name:
            goal = request.form.get('goal')
            status = request.form.get('status', 'PLANNING')
            
            sprint = Sprint(
                name=name,
                goal=goal,
                status=status
            )
            db.session.add(sprint)
            db.session.commit()
            log_activity(f"User created Sprint '{sprint.name}' with status {status}", current_user.id)
            flash('Sprint created successfully!', 'success')
        else:
            issue_id = request.form.get('issue_id')
            new_status = request.form.get('status')
            if issue_id and new_status:
                issue = Issue.query.get(issue_id)
                if issue:
                    old_status = issue.status
                    issue.status = new_status
                    db.session.commit()
                    log_activity(f"User changed Bug #{issue.id} status from {old_status} to {new_status}", current_user.id)
                    flash(f"Bug #{issue.id} status updated to {new_status}", 'success')
                    
        return redirect(url_for('user.sprints_workflow'))

    sprints = Sprint.query.all()
    backlog_issues = Issue.query.filter_by(sprint_id=None).all()
    active_issues = Issue.query.filter(Issue.status != 'CLOSED').all()
    audit_logs = AuditLog.query.order_by(AuditLog.timestamp.desc()).limit(10).all()
    
    return render_template('user/sprints_workflow.html', 
                           sprints=sprints, 
                           backlog_issues=backlog_issues, 
                           active_issues=active_issues,
                           audit_logs=audit_logs)

@user_bp.route('/sprints/<int:sprint_id>/add-issue/<int:issue_id>', methods=['POST'])
@login_required
def add_issue_to_sprint(sprint_id, issue_id):
    issue = Issue.query.get_or_404(issue_id)
    sprint = Sprint.query.get_or_404(sprint_id)
    issue.sprint_id = sprint.id
    db.session.commit()
    log_activity(f"Added Bug #{issue.id} to Sprint '{sprint.name}'", current_user.id)
    flash(f"Bug #{issue.id} moved into {sprint.name}", 'success')
    return redirect(url_for('user.sprints_workflow'))

@user_bp.route('/developer/dashboard')
@login_required
def developer_dashboard():
    role = current_user.role.upper() if current_user.role else ''
    if role == 'ADMIN':
        assigned_issues = Issue.query.all()
    else:
        assigned_issues = Issue.query.filter_by(developer_id=current_user.id).all()
        if not assigned_issues:
            assigned_issues = Issue.query.all()
            
    total_assigned = len(assigned_issues)
    open_count = len([i for i in assigned_issues if i.status in ['OPEN', 'REPORTED', 'TRIAGED']])
    in_progress_count = len([i for i in assigned_issues if i.status == 'IN_PROGRESS'])
    resolved_count = len([i for i in assigned_issues if i.status == 'RESOLVED'])
    resolution_rate = round((resolved_count / total_assigned * 100), 1) if total_assigned > 0 else 0.0

    # Query notifications for the logged-in user
    notifications = Notification.query.filter_by(user_id=current_user.id).all()

    return render_template('user/developer_dashboard.html', 
                           issues=assigned_issues,
                           total_assigned=total_assigned,
                           open_count=open_count,
                           in_progress_count=in_progress_count,
                           resolution_rate=resolution_rate,
                           notifications=notifications)

@user_bp.route('/tester/dashboard')
@login_required
def tester_dashboard():
    role = current_user.role.upper() if current_user.role else ''
    if role not in ['TESTER', 'ADMIN']:
        flash('Access restricted to testers.', 'danger')
        return redirect(url_for('user.dashboard'))
    resolved_issues = Issue.query.filter(Issue.status.in_(['RESOLVED', 'QA_VERIFICATION'])).all()
    return render_template('user/tester_dashboard.html', issues=resolved_issues)

@user_bp.route('/issues/<int:id>/update-status', methods=['POST'])
@login_required
def update_issue_status(id):
    issue = Issue.query.get_or_404(id)
    new_status = request.form.get('status')
    if new_status:
        old_status = issue.status
        issue.status = new_status
        db.session.commit()
        log_activity(f"Updated Bug #{issue.id} status from {old_status} to {new_status}", current_user.id)
        flash(f"Bug #{issue.id} status updated to {new_status}", 'success')
    return redirect(request.referrer or url_for('user.dashboard'))

@user_bp.route('/issues/<int:id>', methods=['GET'])
@login_required
def issue_detail(id):
    issue = Issue.query.get_or_404(id)
    comments = Comment.query.filter_by(issue_id=id).all()
    attachments = Attachment.query.filter_by(issue_id=id).all()
    audit_logs = AuditLog.query.filter_by(issue_id=id).order_by(AuditLog.timestamp.desc()).all()
    
    return render_template('user/issue_detail.html', 
                           issue=issue, 
                           comments=comments, 
                           attachments=attachments, 
                           audit_logs=audit_logs)

@user_bp.route('/issues/<int:id>/comment', methods=['POST'])
@login_required
def add_comment(id):
    content = request.form.get('comment_content')
    parent_id = request.form.get('parent_id')
    issue = Issue.query.get_or_404(id)
    
    if content:
        comment = Comment(
            content=content,
            issue_id=id,
            user_id=current_user.id,
            parent_id=parent_id if parent_id else None
        )
        db.session.add(comment)
        
        recipient_id = issue.developer_id if current_user.id != issue.developer_id else issue.reporter_id
        if recipient_id and recipient_id != current_user.id:
            notification = Notification(
                user_id=recipient_id,
                message=f"{current_user.username} commented on issue #{issue.id}"
            )
            db.session.add(notification)
            
        db.session.commit()
        log_activity(f"{current_user.username} commented on Bug #{issue.id}", current_user.id)
        flash('Comment posted!', 'success')
        
    return redirect(url_for('user.issue_detail', id=id))

@user_bp.route('/issues/<int:id>/upload', methods=['POST'])
@login_required
def upload_attachment(id):
    issue = Issue.query.get_or_404(id)
    if 'file' in request.files:
        file = request.files['file']
        if file and file.filename != '':
            filename = secure_filename(file.filename)
            upload_dir = os.path.join('app', 'static', 'uploads')
            os.makedirs(upload_dir, exist_ok=True)
            file_path = os.path.join(upload_dir, filename)
            file.save(file_path)
            
            relative_path = f'/static/uploads/{filename}'
            attachment = Attachment(
                file_name=filename, 
                file_url=relative_path, 
                file_path=relative_path, 
                issue_id=issue.id
            )
            db.session.add(attachment)
            db.session.commit()
            log_activity(f"Uploaded attachment {filename} to Bug #{issue.id}", current_user.id)
            flash('File attached successfully!', 'success')
    return redirect(url_for('user.issue_detail', id=issue.id))

@user_bp.route('/my-issues', methods=['GET'])
@login_required
def my_issues():
    assigned_issues = Issue.query.filter_by(developer_id=current_user.id).all()
    if not assigned_issues:
        assigned_issues = Issue.query.all()
    return render_template('user/developer_dashboard.html', issues=assigned_issues)

@user_bp.route('/resolution-assistance', methods=['GET', 'POST'])
@login_required
def resolution_assistance():
    issues = Issue.query.all()
    selected_issue = None
    recommendations = []

    if request.method == 'POST':
        issue_id = request.form.get('issue_id')
        selected_issue = Issue.query.get(issue_id)
        if selected_issue:
            developers_only = User.query.filter(User.role.ilike('%developer%') | (User.role.ilike('%admin%'))).all()
            raw_recs = recommend_developers(f"{selected_issue.title} {selected_issue.description}", developers_only)
            
            recommendations = []
            for r in raw_recs:
                dev = r.get('developer')
                match_val = r.get('match', r.get('match_percentage', 80))
                active_count = Issue.query.filter_by(developer_id=dev.id).filter(Issue.status != 'CLOSED').count() if dev else 1
                recommendations.append({
                    'name': dev.username if dev else "Unknown",
                    'skills': getattr(dev, 'skills', 'Full-Stack'),
                    'match_percentage': match_val,
                    'active_tasks': active_count
                })

    return render_template('user/resolution_assistance.html', 
                           issues=issues, 
                           selected_issue=selected_issue, 
                           recommendations=recommendations)

@user_bp.route('/api/v1/issues/triage-recommendation', methods=['POST'])
def api_triage_recommendation():
    data = request.json
    title = data.get('title', '')
    description = data.get('description', '')
    severity = data.get('severity', 'MINOR')
    category = data.get('category', 'General')
    score, level = calculate_priority_score(severity, category)
    devs = User.query.filter(User.role.ilike('%developer%')).all()
    recs = recommend_developers(f"{title} {description}", devs)
    return jsonify({
        'priority_score': score,
        'priority_level': level,
        'recommended_developers': [{'id': r['developer'].id, 'username': r['developer'].username, 'match': r['match']} for r in recs[:3]]
    })

@user_bp.route('/api/v1/collaboration/issues/<int:id>/comments', methods=['GET', 'POST'])
def api_comments(id):
    if request.method == 'POST':
        data = request.json
        comment = Comment(content=data.get('content'), issue_id=id, user_id=data.get('user_id', 1), parent_id=data.get('parent_id'))
        db.session.add(comment)
        db.session.commit()
        return jsonify({'message': 'Comment added successfully'}), 201
    comments = Comment.query.filter_by(issue_id=id).all()
    return jsonify([{'id': c.id, 'content': c.content, 'user': c.user.username if c.user else 'Unknown', 'parent_id': c.parent_id, 'created_at': c.created_at} for c in comments])

@user_bp.route('/api/v1/sprints/', methods=['GET', 'POST'])
def api_sprints():
    if request.method == 'POST':
        data = request.json
        sprint = Sprint(name=data.get('name'), goal=data.get('goal'), status=data.get('status', 'PLANNING'))
        db.session.add(sprint)
        db.session.commit()
        return jsonify({'message': 'Sprint created', 'id': sprint.id}), 201
    sprints = Sprint.query.all()
    return jsonify([{'id': s.id, 'name': s.name, 'goal': s.goal, 'status': s.status} for s in sprints])

@user_bp.route('/api/v1/sprints/<int:id>/add-issue/<int:issue_id>', methods=['POST'])
def api_add_issue_to_sprint(id, issue_id):
    issue = Issue.query.get_or_404(issue_id)
    issue.sprint_id = id
    db.session.commit()
    return jsonify({'message': f'Issue #{issue_id} added to sprint #{id}'})