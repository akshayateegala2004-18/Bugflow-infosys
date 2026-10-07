from datetime import datetime
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash

db = SQLAlchemy()

class User(UserMixin, db.Model):
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    role = db.Column(db.String(50), nullable=False, default='USER')
    skills = db.Column(db.String(255), nullable=True) # e.g., "Python,PostgreSQL,SQL"

    issues_reported = db.relationship('Issue', foreign_keys='Issue.reporter_id', backref='reporter', lazy=True)
    issues_assigned = db.relationship('Issue', foreign_keys='Issue.developer_id', backref='assignee', lazy=True)
    issues_tested = db.relationship('Issue', foreign_keys='Issue.tester_id', backref='tester', lazy=True)
    comments = db.relationship('Comment', backref='author', lazy=True)
    audit_logs = db.relationship('AuditLog', backref='user', lazy=True)

    def check_password(self, password):
        if self.password_hash == password:
            return True
        return check_password_hash(self.password_hash, password)


class Project(db.Model):
    __tablename__ = 'projects'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    status = db.Column(db.String(50), default='Active')

    issues = db.relationship('Issue', backref='project', lazy=True)


class Sprint(db.Model):
    __tablename__ = 'sprints'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    goal = db.Column(db.Text, nullable=True)
    status = db.Column(db.String(50), default='PLANNING')
    start_date = db.Column(db.DateTime, nullable=True)
    end_date = db.Column(db.DateTime, nullable=True)

    issues = db.relationship('Issue', backref='sprint', lazy=True)


class Issue(db.Model):
    __tablename__ = 'issues'
    
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=False)
    category = db.Column(db.String(50), nullable=False)
    severity = db.Column(db.String(50), nullable=False)
    priority = db.Column(db.String(50), nullable=False)
    priority_score = db.Column(db.Float, default=0.0)
    status = db.Column(db.String(50), default='REPORTED')
    
    project_id = db.Column(db.Integer, db.ForeignKey('projects.id'), nullable=False)
    reporter_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    developer_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    tester_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    sprint_id = db.Column(db.Integer, db.ForeignKey('sprints.id'), nullable=True)
    
    environment = db.Column(db.String(100), nullable=True)
    affected_module = db.Column(db.String(100), nullable=True)
    reproduction_steps = db.Column(db.Text, nullable=True)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    resolved_at = db.Column(db.DateTime, nullable=True) # Added for MTTR calculation

    comments = db.relationship('Comment', backref='issue', cascade='all, delete-orphan', lazy=True)
    attachments = db.relationship('Attachment', backref='issue', cascade='all, delete-orphan', lazy=True)
    audit_logs = db.relationship('AuditLog', backref='issue', cascade='all, delete-orphan', lazy=True)


class Comment(db.Model):
    __tablename__ = 'comments'
    
    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.Text, nullable=False)
    issue_id = db.Column(db.Integer, db.ForeignKey('issues.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    parent_id = db.Column(db.Integer, db.ForeignKey('comments.id'), nullable=True)
    
    # Self-referential relationship for nested replies
    replies = db.relationship('Comment', backref=db.backref('parent', remote_side=[id]), lazy=True)


class Attachment(db.Model):
    __tablename__ = 'attachments'
    
    id = db.Column(db.Integer, primary_key=True)
    file_name = db.Column(db.String(200), nullable=False)
    file_url = db.Column(db.String(300), nullable=True)
    file_path = db.Column(db.String(500), nullable=True)
    issue_id = db.Column(db.Integer, db.ForeignKey('issues.id'), nullable=False)
    uploaded_at = db.Column(db.DateTime, default=datetime.utcnow)


class AuditLog(db.Model):
    __tablename__ = 'audit_logs'
    
    id = db.Column(db.Integer, primary_key=True)
    action = db.Column(db.String(255), nullable=False)
    old_value = db.Column(db.Text, nullable=True)
    new_value = db.Column(db.Text, nullable=True)
    commit_id = db.Column(db.String(100), nullable=True)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    issue_id = db.Column(db.Integer, db.ForeignKey('issues.id'), nullable=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)


class Notification(db.Model):
    __tablename__ = 'notifications'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    message = db.Column(db.String(255), nullable=False)
    is_read = db.Column(db.Boolean, default=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

    recipient = db.relationship('User', backref='notifications', lazy=True)