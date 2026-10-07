# app/matcher.py
from app.models import User, Issue

def recommend_developers(arg1, arg2=None):
    """
    Intelligently matches an issue to developers, prioritizing core skill 
    relevance with a minimal workload adjustment.
    """
    if isinstance(arg2, list):
        text = str(arg1).lower()
        developers = arg2
    elif isinstance(arg2, str):
        text = f"{arg1} {arg2}".lower()
        developers = User.query.filter_by(role='DEVELOPER').all()
    else:
        text = str(arg1).lower()
        developers = User.query.filter_by(role='DEVELOPER').all()

    recommendations = []
    
    frontend_triggers = ['dashboard', 'chart', 'alignment', 'ui', 'css', 'html', 'react', 'button', 'display', 'view', 'frontend', 'lag', 'loading']
    backend_triggers = ['api', 'database', 'sql', 'login', 'auth', 'server', 'query', 'backend', 'endpoint', 'crash']

    is_frontend_bug = any(t in text for t in frontend_triggers)
    is_backend_bug = any(t in text for t in backend_triggers)

    for dev in developers:
        dev_skills = [s.strip().lower() for s in (getattr(dev, 'skills', '') or "").split(',') if s.strip()]
        dev_skills_str = " ".join(dev_skills)
        
        # High base score for relevant skill alignment
        base_score = 75
        
        if is_frontend_bug and any(fs in dev_skills_str for fs in ['frontend', 'react', 'css', 'html', 'javascript', 'ui']):
            base_score = 95
        elif is_backend_bug and any(bs in dev_skills_str for bs in ['backend', 'python', 'flask', 'sql', 'api', 'database']):
            base_score = 95
        else:
            matched_skills = [skill for skill in dev_skills if skill in text]
            if matched_skills:
                base_score = min(90, 75 + (len(matched_skills) * 10))

        # Minimal workload penalty (only 1 point per task, capped at 5 points max)
        active_tasks = Issue.query.filter(
            Issue.developer_id == dev.id,
            Issue.status.in_(['Open', 'OPEN', 'ASSIGNED', 'IN_PROGRESS', 'TRIAGED', 'REPORTED', 'resolved'])
        ).count()
        
        workload_penalty = min(5, active_tasks * 1)
        final_score = max(70, min(98, base_score - workload_penalty))
        
        recommendations.append({
            "developer": dev,
            "match_percentage": int(final_score),
            "match": int(final_score),
            "active_tasks": active_tasks,
            "skills": getattr(dev, 'skills', 'General Engineering') or "General Engineering"
        })
        
    recommendations.sort(key=lambda x: x["match_percentage"], reverse=True)
    return recommendations[:3]