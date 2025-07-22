"""
This module defines the database models for a mini GitHub-like Flask application using SQLAlchemy and Flask-Login.

Models:

1. User:
   - Represents a registered user.
   - Fields: username, email, password_hash, bio, created_at, etc.
   - Methods: set_password() and check_password() for secure password handling.
   - Relationships:
     - Owns multiple repositories.
     - Can create issues.
     - Has an activity log of actions performed.

2. Repository:
   - Represents a Git repository.
   - Fields: name, description, visibility (private/public), timestamps.
   - Relationship: linked to an owner (User), issues, and collaborators.
   - Property: full_name returns "username/repo_name".
   - Constraint: one repository name per owner (unique_owner_repo).

3. Collaborator:
   - Represents a user who has access to a repository with specific permissions (read, write, admin).
   - Links a user to a repository.
   - Ensures each user-repo pair is unique.

4. Issue:
   - Represents a bug/task report on a repository.
   - Fields: title, body, status (open/closed), author, timestamps.
   - Linked to both the repository and the user who created it.

5. Activity:
   - Represents an action performed by a user (e.g., "created_repo", "pushed_commit").
   - Fields: action, description, user, repository (optional), created_at.
   - Linked to both User and Repository for activity tracking.

Additional Notes:
- Uses Flask-Login's UserMixin for session support in User model.
- Passwords are hashed using Werkzeug utilities.
- Relationships use lazy loading and cascades for cleanup.
- Tables are explicitly named with __tablename__ for clarity.
- Foreign key constraints ensure relational integrity between models.

This setup enables core functionality for user authentication, repository management, collaboration, issue tracking, and activity logging.
"""

from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash

db = SQLAlchemy()

class User(UserMixin, db.Model):
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False, index=True)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    full_name = db.Column(db.String(100), nullable=True)
    bio = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    is_active = db.Column(db.Boolean, default=True)
    
    # Relationships
    repositories = db.relationship('Repository', backref='owner', lazy=True, cascade='all, delete-orphan')
    issues = db.relationship('Issue', backref='author', lazy=True)
    activities = db.relationship('Activity', backref='user', lazy=True)
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
    
    def __repr__(self):
        return f'<User {self.username}>'

class Repository(db.Model):
    __tablename__ = 'repositories'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False, index=True)
    description = db.Column(db.Text, nullable=True)
    is_private = db.Column(db.Boolean, default=False)
    owner_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    issues = db.relationship('Issue', backref='repository', lazy=True, cascade='all, delete-orphan')
    collaborators = db.relationship('Collaborator', backref='repository', lazy=True, cascade='all, delete-orphan')
    
    @property
    def full_name(self):
        return f"{self.owner.username}/{self.name}"
    
    def __repr__(self):
        return f'<Repository {self.full_name}>'
    
    __table_args__ = (db.UniqueConstraint('owner_id', 'name', name='unique_owner_repo'),)

class Collaborator(db.Model):
    __tablename__ = 'collaborators'
    
    id = db.Column(db.Integer, primary_key=True)
    repository_id = db.Column(db.Integer, db.ForeignKey('repositories.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    permission = db.Column(db.String(20), default='read')  # read, write, admin
    added_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    user = db.relationship('User', backref='collaborations')
    
    __table_args__ = (db.UniqueConstraint('repository_id', 'user_id', name='unique_repo_collaborator'),)

class Issue(db.Model):
    __tablename__ = 'issues'
    
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    body = db.Column(db.Text, nullable=True)
    status = db.Column(db.String(20), default='open')  # open, closed
    repository_id = db.Column(db.Integer, db.ForeignKey('repositories.id'), nullable=False)
    author_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f'<Issue #{self.id}: {self.title}>'

class Activity(db.Model):
    __tablename__ = 'activities'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    action = db.Column(db.String(50), nullable=False)  # created_repo, pushed_commit, etc.
    description = db.Column(db.String(200), nullable=False)
    repository_id = db.Column(db.Integer, db.ForeignKey('repositories.id'), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    repository = db.relationship('Repository', backref='activities')