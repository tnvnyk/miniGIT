"""
This module implements core backend logic for managing Git repositories within the MiniGitHub application.

It includes the `GitManager` class, which provides static methods to perform various repository-related tasks using the GitPython library. These tasks include:

- Creating new repositories with an initial README commit.
- Adding and committing uploaded files to an existing repository.
- Reading file content (from latest or specific commits).
- Generating the file tree structure of a repository.
- Retrieving the commit history and individual commit diffs.
- Zipping the entire repository for download, excluding the `.git` folder.

It also includes:

- `log_activity(...)`: Logs user activity (like creating or committing to a repo) in the database for history tracking.
- `get_file_language(...)`: Infers the programming language of a file based on its extension to enable proper syntax highlighting in the frontend.

Modules and Tools Used:
- `os`, `shutil`, `tempfile`, and `zipfile` for file and directory management.
- `git` (GitPython) for interfacing with the underlying Git repositories.
- `flask.current_app` for accessing runtime app configurations (like REPOS_PATH).
- `models` module for logging database activities (`Activity` model).
- `pathlib.Path` for clean file extension parsing.

This module abstracts the low-level Git operations and supports features like commits, diffs, uploads, and downloads in a way that integrates with the Flask web application.
"""

import os
import git
import shutil
from pathlib import Path
from flask import current_app
from models import Activity, db
import tempfile
import zipfile
from config import Config


class GitManager:
    @staticmethod
    def get_repo_path(username, repo_name):
        return os.path.join(current_app.config['REPOS_PATH'], f"{username}-{repo_name}")
    
    @staticmethod
    def init_repository(username, repo_name, initialize_readme=True):
        """Initialize a new git repository"""
        repo_path = GitManager.get_repo_path(username, repo_name)

        try:
            if os.path.exists(repo_path):
                shutil.rmtree(repo_path)

            os.makedirs(repo_path, exist_ok=True)
            repo = git.Repo.init(repo_path)

            if initialize_readme:
                # Create initial README
                readme_path = os.path.join(repo_path, 'README.md')
                with open(readme_path, 'w') as f:
                    f.write(f"# {repo_name}\n\nThis is a new repository created on MiniGitHub.")

                # Initial commit
                repo.index.add(['README.md'])
                repo.index.commit("Initial commit", author=git.Actor(username, f"{username}@minigithub.local"))

            return True, "Repository initialized successfully"
        except Exception as e:
            return False, str(e)
    @staticmethod
    def delete_repository(username, repo_name):
        repo_path = os.path.join(Config.REPO_PATH, username, repo_name)
        if os.path.exists(repo_path):
            import shutil
            shutil.rmtree(repo_path)

    
    @staticmethod
    def add_files(username, repo_name, files, commit_message, user_email=None):
        """Add files to repository and commit"""
        repo_path = GitManager.get_repo_path(username, repo_name)
        
        try:
            repo = git.Repo(repo_path)
            added_files = []
            
            for file in files:
                if file.filename:
                    file_path = os.path.join(repo_path, file.filename)
                    
                    # Create directories if needed
                    os.makedirs(os.path.dirname(file_path), exist_ok=True)
                    
                    file.save(file_path)
                    repo.index.add([file.filename])
                    added_files.append(file.filename)
            
            if added_files:
                email = user_email or f"{username}@minigithub.local"
                author = git.Actor(username, email)
                repo.index.commit(commit_message, author=author)
                
                return True, f"Added {len(added_files)} files", added_files
            else:
                return False, "No files to add", []
                
        except Exception as e:
            return False, str(e), []
    
    @staticmethod
    def get_file_content(username, repo_name, file_path, commit_hash=None):
        """Get file content from repository"""
        repo_path = GitManager.get_repo_path(username, repo_name)
        
        try:
            repo = git.Repo(repo_path)
            
            if commit_hash:
                commit = repo.commit(commit_hash)
                blob = commit.tree / file_path
                return blob.data_stream.read().decode('utf-8', errors='ignore')
            else:
                full_path = os.path.join(repo_path, file_path)
                if os.path.exists(full_path) and os.path.isfile(full_path):
                    with open(full_path, 'r', encoding='utf-8', errors='ignore') as f:
                        return f.read()
                        
        except Exception as e:
            print(f"Error reading file: {e}")
            return None
    
    @staticmethod
    def get_file_tree(username, repo_name, commit_hash=None):
        """Get file tree structure"""
        repo_path = GitManager.get_repo_path(username, repo_name)
        
        try:
            repo = git.Repo(repo_path)
            
            if commit_hash:
                commit = repo.commit(commit_hash)
                tree = commit.tree
            else:
                tree = repo.head.commit.tree
            
            files = []
            
            def traverse_tree(tree_obj, path=""):
                for item in tree_obj.traverse():
                    item_path = os.path.join(path, item.name) if path else item.name
                    
                    if item.type == 'blob':  # File
                        files.append({
                            'name': item.name,
                            'path': item_path,
                            'type': 'file',
                            'size': item.size
                        })
                    elif item.type == 'tree':  # Directory
                        files.append({
                            'name': item.name,
                            'path': item_path,
                            'type': 'dir'
                        })
            
            traverse_tree(tree)
            return files
            
        except Exception as e:
            print(f"Error getting file tree: {e}")
            return []
    
    @staticmethod
    def get_commits(username, repo_name, limit=50):
        """Get commit history"""
        repo_path = GitManager.get_repo_path(username, repo_name)
        
        try:
            repo = git.Repo(repo_path)
            commits = []
            
            for commit in repo.iter_commits(max_count=limit):
                commits.append({
                    'hash': commit.hexsha,
                    'short_hash': commit.hexsha[:7],
                    'message': commit.message.strip(),
                    'author': commit.author.name,
                    'email': commit.author.email,
                    'date': commit.committed_datetime,
                    'stats': commit.stats.total
                })
                
            return commits
            
        except Exception as e:
            print(f"Error getting commits: {e}")
            return []
    
    @staticmethod
    def get_commit_diff(username, repo_name, commit_hash):
        """Get diff for a specific commit"""
        repo_path = GitManager.get_repo_path(username, repo_name)
        
        try:
            repo = git.Repo(repo_path)
            commit = repo.commit(commit_hash)
            
            if commit.parents:
                parent = commit.parents[0]
                diff = repo.git.diff(parent.hexsha, commit.hexsha, unified=3)
            else:
                # First commit
                diff = repo.git.show(commit.hexsha, format='', unified=3)
            
            return diff
            
        except Exception as e:
            print(f"Error getting commit diff: {e}")
            return ""
    
    @staticmethod
    def create_repo_zip(username, repo_name):
        """Create a zip file of the repository"""
        repo_path = GitManager.get_repo_path(username, repo_name)
        
        try:
            with tempfile.NamedTemporaryFile(suffix='.zip', delete=False) as tmp_file:
                zip_path = tmp_file.name
                
            with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
                for root, dirs, files in os.walk(repo_path):
                    # Skip .git directory
                    if '.git' in root:
                        continue
                        
                    for file in files:
                        file_path = os.path.join(root, file)
                        arc_path = os.path.relpath(file_path, repo_path)
                        zipf.write(file_path, arc_path)
            
            return zip_path
            
        except Exception as e:
            print(f"Error creating zip: {e}")
            return None
    @staticmethod
    def count_commits(username, repo_name):
        """Return the total number of commits in a repository"""
        repo_path = GitManager.get_repo_path(username, repo_name)

        try:
            repo = git.Repo(repo_path)
            return sum(1 for _ in repo.iter_commits())
        except Exception as e:
            print(f"Error counting commits: {e}")
            return 0


def log_activity(user_id, action, description, repository_id=None):
    """Log user activity"""
    activity = Activity(
        user_id=user_id,
        action=action,
        description=description,
        repository_id=repository_id
    )
    db.session.add(activity)
    db.session.commit()

def get_file_language(filename):
    """Determine file language for syntax highlighting"""
    ext_map = {
        '.py': 'python',
        '.js': 'javascript',
        '.html': 'html',
        '.css': 'css',
        '.java': 'java',
        '.cpp': 'cpp',
        '.c': 'c',
        '.php': 'php',
        '.rb': 'ruby',
        '.go': 'go',
        '.rs': 'rust',
        '.json': 'json',
        '.xml': 'xml',
        '.yml': 'yaml',
        '.yaml': 'yaml',
        '.md': 'markdown',
        '.sql': 'sql',
        '.sh': 'bash',
        '.dockerfile': 'dockerfile'
    }
    
    ext = Path(filename).suffix.lower()
    return ext_map.get(ext, 'text')