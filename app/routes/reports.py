from flask import Blueprint, render_template
from flask_login import login_required
from app.models import Issue

reports_bp = Blueprint('reports', __name__, url_prefix='/reports')

@reports_bp.route('/analytics')
@login_required
def analytics():
    total_issues = Issue.query.count()
    resolved = Issue.query.filter_by(status='RESOLVED').count()
    critical = Issue.query.filter_by(severity='CRITICAL').count()
    
    data = {
        'total': total_issues,
        'resolved': resolved,
        'critical': critical,
        'pending': total_issues - resolved
    }
    return render_template('reports/analytics.html', data=data)