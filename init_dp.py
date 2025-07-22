from app import create_app
from models import db, User, Repository

def init_database():
    app = create_app()
    
    with app.app_context():
        # Drop all tables and recreate
        db.drop_all()
        db.create_all()
        
        # Create a default admin user
        admin = User(
            username='admin',
            email='admin@minigithub.local',
            full_name='Administrator',
            bio='System Administrator'
        )
        admin.set_password('admin123')
        
        db.session.add(admin)
        db.session.commit()
        
        print("Database initialized successfully!")
        print("Default admin user created:")
        print("  Username: admin")
        print("  Password: admin123")

if __name__ == '__main__':
    init_database()