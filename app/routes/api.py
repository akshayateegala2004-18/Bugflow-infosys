from flask import Blueprint, jsonify, request, render_template
from app.models import db, Issue, AuditLog
from datetime import datetime, timedelta
import re

api_bp = Blueprint('api', __name__, url_prefix='/api/v1')

@api_bp.route('/analytics/quality-metrics', methods=['GET'])
def quality_metrics():
    issues = Issue.query.all()
    total = len(issues)
    if total == 0:
        return jsonify({"fix_rate_percentage": 0, "mean_time_to_resolution_hours": 0, "defect_leakage_rate": 0, "backlog_health_score": 100})

    resolved_closed = sum(1 for i in issues if i.status in ['RESOLVED', 'CLOSED'])
    fix_rate = round((resolved_closed / total) * 100, 2)

    # MTTR calculation
    resolution_times = []
    for i in issues:
        if i.resolved_at and i.created_at:
            diff = (i.resolved_at - i.created_at).total_seconds() / 3600
            resolution_times.append(diff)
    mttr = round(sum(resolution_times) / len(resolution_times), 1) if resolution_times else 0.0

    # Defect Leakage Rate
    prod_bugs = sum(1 for i in issues if i.environment == 'Production')
    leakage_rate = round((prod_bugs / total) * 100, 2)

    # Backlog Health Score
    score = 100
    for i in issues:
        if i.status not in ['RESOLVED', 'CLOSED']:
            if i.severity == 'CRITICAL':
                score -= 10
            elif i.severity == 'MAJOR':
                score -= 5
            else:
                score -= 2
    health_score = max(score, 0)

    return jsonify({
        "fix_rate_percentage": fix_rate,
        "mean_time_to_resolution_hours": mttr,
        "defect_leakage_rate": leakage_rate,
        "backlog_health_score": health_score
    })

@api_bp.route('/analytics/defect-trends', methods=['GET'])
def defect_trends():
    # Generate last 14 days dummy or real trend data
    dates = []
    new_bugs = []
    resolved_bugs = []
    
    for i in range(13, -1, -1):
        d = datetime.utcnow() - timedelta(days=i)
        dates.append(d.strftime('%b %d'))
        # Count created on this day (or mock for presentation demo)
        new_bugs.append(2 + (i % 3))
        resolved_bugs.append(1 + (i % 4))

    return jsonify({
        "dates": dates,
        "new_bugs": new_bugs,
        "resolved_bugs": resolved_bugs
    })

@api_bp.route('/webhooks/git', methods=['POST'])
def git_webhook():
    data = request.get_json() or {}
    commit_message = data.get('commit_message', '')
    commit_id = data.get('commit_id', 'unknown')

    # Regex to match fixes #2, closes #5, etc.
    match = re.search(r"(?:fixes|fix|closes|close|resolves|resolve)\s+#(\d+)", commit_message, re.IGNORECASE)
    if not match:
        return jsonify({"success": False, "message": "No bug reference found in commit message."}), 400

    bug_id = int(match.group(1))
    issue = Issue.query.get(bug_id)
    if not issue:
        return jsonify({"success": False, "message": f"Bug #{bug_id} not found."}), 404

    old_status = issue.status
    issue.status = 'QA_VERIFICATION'

    # Create Audit Log
    log = AuditLog(
        issue_id=issue.id,
        actor="System / Git Webhook",
        action="STATUS_CHANGED",
        old_value=old_status,
        new_value="QA_VERIFICATION",
        commit_id=commit_id
    )
    db.session.add(log)
    db.session.commit()

    return jsonify({
        "success": True,
        "issue_id": issue.id,
        "old_status": old_status,
        "new_status": "QA_VERIFICATION",
        "message": f"Bug #{issue.id} automatically moved to QA_VERIFICATION"
    })