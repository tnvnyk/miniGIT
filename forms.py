"""
This module defines various Flask-WTF forms used in the web application. These forms handle user input for
authentication, registration, repository creation, file uploads, and issue reporting. Each form includes 
fields with validation logic to ensure data integrity.

Imports:
- FlaskForm: Base class for all forms.
- FileField, FileAllowed, FileRequired: Used for file upload validation.
- Standard form fields: StringField, TextAreaField, PasswordField, BooleanField, SelectField.
- Validators: DataRequired, Length, Email, EqualTo, ValidationError for input validation.
- User and Repository models: Used to check for existing entries during validation.

Forms Defined:

1. LoginForm:
   - Fields: username, password, remember_me (checkbox).
   - Used for logging users into the system.
   - Validates presence and appropriate length of username and password.

2. RegisterForm:
   - Fields: username, email, full_name, password, password2.
   - Used for registering new users.
   - Validators:
     - `validate_username`: Ensures the username is unique (queries database).
     - `validate_email`: Ensures the email is not already registered.
     - `EqualTo`: Ensures both passwords match.

3. RepositoryForm:
   - Fields: name (required), description (optional), is_private (checkbox).
   - Used to create a new repository.
   - Custom validator `validate_name`:
     - Ensures the repository name contains only letters, digits, underscores, or hyphens.

4. FileUploadForm:
   - Fields: files (required file input), commit_message (required text input).
   - Used for uploading multiple files to a repository along with a commit message.
   - `render_kw={"multiple": True}` allows selecting multiple files.

5. IssueForm:
   - Fields: title (required), body (optional).
   - Used to report or create issues within a repository.
   - Ensures title is present and within the maximum length.

Each form integrates well with Flask’s templating engine and supports CSRF protection automatically via Flask-WTF.
"""

from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileAllowed, FileRequired
from wtforms import StringField, TextAreaField, PasswordField, BooleanField, SelectField, SubmitField
from wtforms.validators import DataRequired, Length, Email, EqualTo, ValidationError
from models import User, Repository
from wtforms.validators import DataRequired, Length, Email, EqualTo, Optional
class LoginForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired(), Length(min=3, max=80)])
    password = PasswordField('Password', validators=[DataRequired()])
    #remember_me = BooleanField('Remember Me')
    submit = SubmitField('Login')

class RegisterForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired(), Length(min=3, max=80)])
    email = StringField('Email', validators=[DataRequired(), Email()])
    full_name = StringField('Full Name', validators=[Length(max=100)])
    password = PasswordField('Password', validators=[DataRequired(), Length(min=6)])
    password2 = PasswordField('Repeat Password', validators=[
        DataRequired(), EqualTo('password', message='Passwords must match')

    ])
    submit = SubmitField('Register')
    
    def validate_username(self, username):
        user = User.query.filter_by(username=username.data).first()
        if user:
            raise ValidationError('Username already exists.')
    
    def validate_email(self, email):
        user = User.query.filter_by(email=email.data).first()
        if user:
            raise ValidationError('Email already registered.')

class RepositoryForm(FlaskForm):
    name = StringField('Repository Name', validators=[
        DataRequired(), 
        Length(min=1, max=100)
    ])
    description = TextAreaField('Description', validators=[Length(max=500)])
    is_private = BooleanField('Private Repository')
    initialize_readme = BooleanField('Initialize with README') 
    
    def validate_name(self, name):
        # Check for valid repository name (alphanumeric, hyphens, underscores)
        import re
        if not re.match(r'^[a-zA-Z0-9_-]+$', name.data):
            raise ValidationError('Repository name can only contain letters, numbers, hyphens, and underscores.')

class FileUploadForm(FlaskForm):
    files = FileField('Files', validators=[FileRequired()], render_kw={"multiple": True})
    commit_message = StringField('Commit Message', validators=[DataRequired(), Length(max=200)])
    target_directory = StringField(
            'Target Directory', 
            validators=[Optional()],  # Use DataRequired() if this field is mandatory
            description='Directory where files will be uploaded',
            render_kw={"placeholder": "e.g., /uploads or leave empty for root"})
    overwrite_existing = BooleanField(
        'Overwrite existing files',
        description='Check this box to overwrite files with the same name'
    )
    submit = SubmitField('Upload')

class IssueForm(FlaskForm):
    title = StringField('Title', validators=[DataRequired(), Length(max=200)])
    body = TextAreaField('Description')