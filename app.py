from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, send_file, abort
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from werkzeug.utils import secure_filename
import os
from flask_wtf.csrf import CSRFProtect
import markdown2
from datetime import datetime
import tempfile
from flask_moment import Moment
from flask import request, redirect, url_for, flash, abort, render_template
# Local imports
from config import Config
from models import db, User, Repository, Issue, Activity
from forms import LoginForm, RegisterForm, RepositoryForm, FileUploadForm, IssueForm
from utils import GitManager, log_activity, get_file_language
import markdown
from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, BooleanField, SubmitField
from wtforms.validators import DataRequired, Length

class RepositorySettingsForm(FlaskForm):
    name = StringField('Repository Name', validators=[DataRequired(), Length(min=1, max=100)])
    description = TextAreaField('Description', validators=[Length(max=500)])
    is_private = BooleanField('Private Repository')
    submit = SubmitField('Update Settings')

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)
    moment = Moment()
    moment.init_app(app)
    # Initialize extensions
    db.init_app(app)
    
    # Login manager setup
    login_manager = LoginManager()
    login_manager.init_app(app)
    login_manager.login_view = 'login'
    login_manager.login_message = 'Please log in to access this page.'
    login_manager.login_message_category = 'info'
    
    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))
    
    # Routes
    @app.route('/')
    def index():
        recent_repos = Repository.query.filter_by(is_private=False).order_by(Repository.updated_at.desc()).limit(6).all()

        user_stats = None
        if current_user.is_authenticated:
            user_repos = Repository.query.filter_by(owner_id=current_user.id).all()
            total_repos = len(user_repos)
            public_repos = sum(1 for repo in user_repos if not repo.is_private)
            private_repos = total_repos - public_repos
            total_commits = sum(GitManager.count_commits(current_user.username, repo.name) for repo in user_repos)

            user_stats = {
                'total_repos': total_repos,
                'public_repos': public_repos,
                'private_repos': private_repos,
                'total_commits': total_commits
            }

        return render_template('index.html', recent_repos=recent_repos, user_stats=user_stats)

    # Authentication routes
    @app.route('/login', methods=['GET', 'POST'])
    def login():
        if current_user.is_authenticated:
            return redirect(url_for('dashboard'))
            
        form = LoginForm()
        if form.validate_on_submit():
            user = User.query.filter_by(username=form.username.data).first()
            
            if user and user.check_password(form.password.data):
                login_user(user)
                log_activity(user.id, 'login', f'{user.username} logged in')
                
                next_page = request.args.get('next')
                if next_page:
                    return redirect(next_page)
                return redirect(url_for('dashboard'))
            else:
                flash('Invalid username or password', 'danger')
        
        return render_template('auth/login.html', form=form)
    
    @app.route('/register', methods=['GET', 'POST'])
    def register():
        if current_user.is_authenticated:
            return redirect(url_for('dashboard'))
            
        form = RegisterForm()
        if form.validate_on_submit():
            user = User(
                username=form.username.data,
                email=form.email.data,
                full_name=form.full_name.data
            )
            user.set_password(form.password.data)
            
            db.session.add(user)
            db.session.commit()
            
            log_activity(user.id, 'register', f'New user {user.username} registered')
            flash('Registration successful! Please log in.', 'success')
            return redirect(url_for('login'))
        
        return render_template('auth/register.html', form=form)
    
    @app.route('/logout')
    @login_required
    def logout():
        log_activity(current_user.id, 'logout', f'{current_user.username} logged out')
        logout_user()
        flash('You have been logged out.', 'info')
        return redirect(url_for('index'))
    
    
    @app.route('/dashboard')
    @login_required
    def dashboard():
        page = request.args.get('page', 1, type=int)
        user_repos = Repository.query.filter_by(owner_id=current_user.id)\
        .order_by(Repository.updated_at.desc())\
        .paginate(page=page, per_page=10)
        recent_activity = Activity.query.filter_by(user_id=current_user.id).order_by(Activity.created_at.desc()).limit(10).all()

        total_repos = user_repos.total
        public_repos = sum(1 for repo in user_repos if not repo.is_private)
        private_repos = total_repos - public_repos

        total_commits = sum(GitManager.count_commits(current_user.username, repo.name) for repo in user_repos)

        stats = {
            'total_repos': total_repos,
            'public_repos': public_repos,
            'private_repos': private_repos,
            'total_commits': total_commits,
        }

        return render_template('auth/dashboard.html',
                            repositories=user_repos,
                            recent_activity=recent_activity,
                            stats=stats)

    # Repository routes
    @app.route('/new', methods=['GET', 'POST'])
    @login_required
    def create():
        form = RepositoryForm()
        if form.validate_on_submit():
            # Check if repository already exists
            existing = Repository.query.filter_by(
                owner_id=current_user.id,
                name=form.name.data
            ).first()
            
            if existing:
                flash('Repository with this name already exists.', 'danger')
                return render_template('repo/create.html', form=form)
            
            # Create repository record
            repo = Repository(
                name=form.name.data,
                description=form.description.data,
                is_private=form.is_private.data,
                owner_id=current_user.id
            )
            
            db.session.add(repo)
            db.session.commit()
            
            # Initialize git repository
            #success, message = GitManager.init_repository(current_user.username, repo.name)
            init_readme = form.initialize_readme.data

            success, message = GitManager.init_repository(current_user.username, repo.name, init_readme)

            
            if success:
                log_activity(current_user.id, 'create_repo', f'Created repository {repo.name}', repo.id)
                flash('Repository created successfully!', 'success')
                return redirect(url_for('view', username=current_user.username, repo_name=repo.name))
            else:
                # Clean up database record if git init failed
                db.session.delete(repo)
                db.session.commit()
                flash(f'Failed to create repository: {message}', 'danger')
        
        return render_template('repo/create.html', form=form)
    
    @app.route('/<username>/<repo_name>')
    def view(username, repo_name):
        user = User.query.filter_by(username=username).first_or_404()
        repo = Repository.query.filter_by(owner_id=user.id, name=repo_name).first_or_404()
        print(f"[DEBUG] User: {user.username}, Repo: {repo.name}, Private: {repo.is_private}")
        # Check if user can access private repository
        if repo.is_private and (not current_user.is_authenticated or current_user.id != repo.owner_id):
            abort(404)
        
        # Get file tree
        files = GitManager.get_file_tree(username, repo_name)
        
        # Get README content if exists
        
        readme_file = GitManager.get_file_content(username, repo_name, 'README.md')
        if readme_file is not None and readme_file.strip():
            readme_content = markdown2.markdown(readme_file, extras=['fenced-code-blocks', 'tables'])
        else:
            readme_content = None
        
        # Get recent commits
        commits = GitManager.get_commits(username, repo_name, limit=5)
    # DEBUG: print each commit's content
        for i, commit in enumerate(commits):
            print(f"[DEBUG] Commit {i}: {commit}")
        return render_template('repo/view.html', 
                             repo=repo, 
                             files=files, 
                             readme_content=readme_content,
                             commits=commits)
    
    # @app.route('/<username>/<repo_name>/blob/<path:file_path>')
    # def view_file(username, repo_name, file_path):
    #     user = User.query.filter_by(username=username).first_or_404()
    #     repo = Repository.query.filter_by(owner_id=user.id, name=repo_name).first_or_404()
        
    #     if repo.is_private and (not current_user.is_authenticated or current_user.id != repo.owner_id):
    #         abort(404)
        
    #     content = GitManager.get_file_content(username, repo_name, file_path)
    #     if content is None:
    #         abort(404)
        
    #     language = get_file_language(file_path)
        
    #     return render_template('repo/file_view.html', 
    #                          repo=repo, 
    #                          file_path=file_path,
    #                          content=content,
    #                          language=language)
    @app.route('/<username>/<repo_name>/blob/<path:file_path>')
    @app.route('/repo/<int:repo_id>/blob/<path:file_path>')
    def view_file(repo_id, file_path):
        repo = Repository.query.get_or_404(repo_id)
        
        if repo.is_private and (not current_user.is_authenticated or current_user.id != repo.owner_id):
            abort(404)
        
        content = GitManager.get_file_content(repo.owner.username, repo.name, file_path)
        if content is None:
            abort(404)
        
        file_extension = file_path.split('.')[-1].lower()
        is_text_file = GitManager.is_text_file(file_path)
        is_image = file_extension in ['png', 'jpg', 'jpeg', 'gif', 'bmp']
        is_markdown = file_extension == 'md'

        # Optional extras
        file_size = len(content.encode()) if isinstance(content, str) else len(content)
        line_count = content.count('\n') if isinstance(content, str) else 0
        rendered_content = markdown.markdown(content) if is_markdown else None
        last_commit = GitManager.get_last_commit(repo.owner.username, repo.name, file_path)

        return render_template('repo/file_view.html', 
                            repo=repo,
                            file_path=file_path,
                            file_content=content,
                            file_extension=file_extension,
                            is_text_file=is_text_file,
                            is_image=is_image,
                            is_markdown=is_markdown,
                            rendered_content=rendered_content,
                            file_size=file_size,
                            line_count=line_count,
                            last_commit=last_commit)
        
    @app.route('/<username>/<repo_name>/delete', methods=['POST'])
    @login_required
    def delete_repo(username, repo_name):
        user = User.query.filter_by(username=username).first_or_404()
        repo = Repository.query.filter_by(owner_id=user.id, name=repo_name).first_or_404()
        
        if current_user.id != repo.owner_id:
            abort(403)

        # Delete the repository from the database
        db.session.delete(repo)
        db.session.commit()

        # Also delete the Git directory (optional but recommended)
        GitManager.delete_repository(username, repo_name)

        log_activity(current_user.id, 'delete_repo', f'Deleted repository {repo.name}')
        flash(f'Repository "{repo.name}" has been deleted.', 'success')

        return redirect(url_for('dashboard'))

    
    @app.route('/<username>/<repo_name>/upload', methods=['GET', 'POST'])
    @login_required
    def upload(username, repo_name):
        user = User.query.filter_by(username=username).first_or_404()
        repo = Repository.query.filter_by(owner_id=user.id, name=repo_name).first_or_404()
        
        if current_user.id != repo.owner_id:
            abort(403)
        
        form = FileUploadForm()
        if form.validate_on_submit():
            files = request.files.getlist('files')
            
            success, message, added_files = GitManager.add_files(
                username, repo_name, files, form.commit_message.data, current_user.email
            )
            
            if success:
                log_activity(current_user.id, 'push_commit', 
                           f'Pushed {len(added_files)} files to {repo.name}', repo.id)
                flash(f'Successfully uploaded {len(added_files)} files!', 'success')
                return redirect(url_for('view', username=username, repo_name=repo_name))
            else:
                flash(f'Upload failed: {message}', 'danger')
        
        return render_template('repo/upload.html', repo=repo, form=form)
    
    @app.route('/<username>/<repo_name>/commits')
    def view_commits(username, repo_name):
        user = User.query.filter_by(username=username).first_or_404()
        repo = Repository.query.filter_by(owner_id=user.id, name=repo_name).first_or_404()
        
        if repo.is_private and (not current_user.is_authenticated or current_user.id != repo.owner_id):
            abort(404)
        
        commits = GitManager.get_commits(username, repo_name, limit=50)
        
        return render_template('repo/commits.html', repository=repo, commits=commits)
    
    @app.route('/<username>/<repo_name>/commit/<commit_hash>')
    def view_commit(username, repo_name, commit_hash):
        user = User.query.filter_by(username=username).first_or_404()
        repo = Repository.query.filter_by(owner_id=user.id, name=repo_name).first_or_404()
        
        if repo.is_private and (not current_user.is_authenticated or current_user.id != repo.owner_id):
            abort(404)
        
        commits = GitManager.get_commits(username, repo_name)
        commit = next((c for c in commits if c['hash'] == commit_hash), None)
        
        if not commit:
            abort(404)
        
        diff = GitManager.get_commit_diff(username, repo_name, commit_hash)
        
        return render_template('repo/commit_detail.html', 
                             repo=repo, 
                             commit=commit, 
                             diff=diff)
    
    @app.route('/<username>/<repo_name>/settings', methods=['GET', 'POST'])
    @login_required
    def settings(username, repo_name):
        user = User.query.filter_by(username=username).first_or_404()
        repo = Repository.query.filter_by(owner_id=user.id, name=repo_name).first_or_404()
        
        if current_user.id != repo.owner_id:
            abort(403)
        
        if request.method == 'POST':
            repo.description = request.form.get('description', '')
            repo.is_private = 'is_private' in request.form
            db.session.commit()
            
            log_activity(current_user.id, 'update_repo', f'Updated settings for {repo.name}', repo.id)
            flash('Repository settings updated!', 'success')
            return redirect(url_for('repository_settings', username=username, repo_name=repo_name))
        
        return render_template('repo/settings.html', repo=repo)
    
    @app.route('/<username>/<repo_name>/download')
    @login_required
    def download_repository(username, repo_name):
        user = User.query.filter_by(username=username).first_or_404()
        repo = Repository.query.filter_by(owner_id=user.id, name=repo_name).first_or_404()
        
        if repo.is_private and current_user.id != repo.owner_id:
            abort(403)
        
        zip_path = GitManager.create_repo_zip(username, repo_name)
        if zip_path:
            log_activity(current_user.id, 'download_repo', f'Downloaded {repo.name}', repo.id)
            return send_file(zip_path, as_attachment=True, download_name=f'{repo.name}.zip')
        else:
            flash('Failed to create repository archive.', 'danger')
            return redirect(url_for('view', username=username, repo_name=repo_name))
    
    # Issues routes
    @app.route('/<username>/<repo_name>/issues')
    def view_issues(username, repo_name):
        user = User.query.filter_by(username=username).first_or_404()
        repo = Repository.query.filter_by(owner_id=user.id, name=repo_name).first_or_404()
        
        if repo.is_private and (not current_user.is_authenticated or current_user.id != repo.owner_id):
            abort(404)
        
        issues = Issue.query.filter_by(repository_id=repo.id).order_by(Issue.created_at.desc()).all()
        
        return render_template('repo/issues.html', repository=repo, issues=issues)
    
    @app.route('/<username>/<repo_name>/issues/new', methods=['GET', 'POST'])
    @login_required
    def create_issue(username, repo_name):
        user = User.query.filter_by(username=username).first_or_404()
        repo = Repository.query.filter_by(owner_id=user.id, name=repo_name).first_or_404()
        
        if repo.is_private and current_user.id != repo.owner_id:
            abort(403)
        
        form = IssueForm()
        if form.validate_on_submit():
            issue = Issue(
                title=form.title.data,
                body=form.body.data,
                repository_id=repo.id,
                author_id=current_user.id
            )
            
            db.session.add(issue)
            db.session.commit()
            
            log_activity(current_user.id, 'create_issue', f'Created issue #{issue.id} in {repo.name}', repo.id)
            flash('Issue created successfully!', 'success')
            return redirect(url_for('view_issues', username=username, repo_name=repo_name))
        
        return render_template('repo/create_issue.html', repository=repo, form=form)
    
    # API routes
    @app.route('/api/search')
    def api_search():
        query = request.args.get('q', '').strip()
        if not query:
            return jsonify([])
        
        repos = Repository.query.filter(
            Repository.name.ilike(f'%{query}%'),
            Repository.is_private == False
        ).limit(10).all()
        
        results = []
        for repo in repos:
            results.append({
                'name': repo.name,
                'full_name': repo.full_name,
                'description': repo.description,
                'owner': repo.owner.username,
                'url': url_for('view_repository', username=repo.owner.username, repo_name=repo.name)
            })
        
        return jsonify(results)
    
    # Error handlers
    @app.errorhandler(404)
    def not_found(error):
        return render_template('errors/404.html'), 404
    
    @app.errorhandler(403)
    def forbidden(error):
        return render_template('errors/403.html'), 403
    
    @app.errorhandler(500)
    def internal_error(error):
        db.session.rollback()
        return render_template('errors/500.html'), 500
    
    return app

# Create app instance
app = create_app()

if __name__ == '__main__':
    app.run(debug=True)