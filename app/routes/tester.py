from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from app.models import Issue, db

tester_bp = Blueprint('tester', __name__, url_prefix='/tester')

@tester_bp.route('/dashboard')
@login_required
def dashboard():
    issues = Issue.query.all()
    return render_template('tester/dashboard.html', issues=issues)

@tester_bp.route('/verify/<int:issue_id>', methods=['POST'])
@login_required
def verify_issue(issue_id):
    issue = Issue.query.get_or_404(issue_id)
    issue.status = 'VERIFIED'
    issue.tester_id = current_user.id
    db.session.commit()
    flash(f'Issue #{issue.id} verified successfully.', 'success')
    return redirect(url_for('tester.dashboard'))