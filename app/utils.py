from app.models import AuditLog, db

def calculate_priority_score(severity, category):
    severity_weights = {
        'CRITICAL': 4,
        'MAJOR': 3,
        'MINOR': 2,
        'TRIVIAL': 1
    }
    
    cat_lower = category.lower() if category else ""
    
    if any(k in cat_lower for k in ['security', 'database', 'sql']):
        urgency_weight = 3
    elif any(k in cat_lower for k in ['api', 'backend', 'auth']):
        urgency_weight = 2
    else:
        urgency_weight = 1

    sev_weight = severity_weights.get(severity.upper(), 1) if severity else 1
    score = float(sev_weight * urgency_weight)

    if score >= 10:
        level = 'URGENT'
    elif score >= 7:
        level = 'HIGH'
    elif score >= 4:
        level = 'MEDIUM'
    else:
        level = 'LOW'

    return score, level

def recommend_developers(issue_text, developers):
    recommendations = []
    text_lower = issue_text.lower()
    
    for dev in developers:
        score = 0
        dev_skills = dev.skills.lower().split(',') if dev.skills else []
        for skill in dev_skills:
            skill = skill.strip()
            if skill and skill in text_lower:
                score += 5
        
        active_workload = len([i for i in dev.issues_assigned if i.status != 'CLOSED'])
        match_score = max(1, score + 10 - (active_workload * 2))
        
        recommendations.append({
            'developer': dev,
            'match': match_score,
            'workload': active_workload
        })
        
    recommendations.sort(key=lambda x: x['match'], reverse=True)
    return recommendations

def log_activity(action_text, user_id=None):
    log = AuditLog(action=action_text, user_id=user_id)
    db.session.add(log)
    db.session.commit()