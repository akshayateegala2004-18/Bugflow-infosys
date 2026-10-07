from app import create_app, db
from app.models import User, Project

def seed_database():
    app = create_app()
    with app.app_context():
        db.create_all()
        
        if not User.query.filter_by(username='admin').first():
            admin = User(username='admin', email='admin@bugflow.com', role='admin')
            admin.set_password('admin123')
            db.session.add(admin)
            
        if not Project.query.first():
            proj = Project(name='Core BugFlow Engine', description='Main tracking platform backend.')
            db.session.add(proj)
            
        db.session.commit()
        print("Database seeded successfully!")

if __name__ == '__main__':
    seed_database()
