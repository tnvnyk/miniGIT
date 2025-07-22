# MiniGitHub

A simplified GitHub-like web application that allows users to create accounts, upload repositories, browse and view public projects, and more.

## Features

- User registration and login
- Repository management
- File upload
- Markdown rendering for README files
- File browsing within uploaded repositories
- Clean UI: Built with Bootstrap 5 components (cards, modals, navbar, forms)
  

## Tech Stack

- Flask -Python
- PostgreSQL
- HTML/CSS (Bootstrap)
- Git (integration and repository handling)
- JavaScript

## Getting Started

### Prerequisites

- Python 3.8+
- PostgreSQL
- Git
- Virtualenv (recommended)

### Installation

1. Clone the repository:

   ```bash
   git clone https://github.com/yourusername/minigithub.git
   cd minigithub
2. Set up and activate a virtual environment:
   ```bash
    python -m venv venv
    source venv/bin/activate   # On Windows: venv\Scripts\activate
3. Install dependencies:
   ```bash
    pip install -r requirements.txt
4. Configure environment variables:
   Create a .env file in the root directory with the following:
   ```bash
    DATABASE_URL=postgresql://<db_user>:<db_password>@localhost:5432/<db_name>
    SECRET_KEY=your-secret-key
    FLASK_ENV=development
    REPOS_PATH=./repos
    UPLOAD_FOLDER=./static/uploads
    MAX_CONTENT_LENGTH=16777216
5  Initialize the database:
6. Run the app:

     ```bash
      flask run

### Future Work

-  Commit history view
-  Managing collaborators 
-  Issues & comments 
-  Download repo as ZIP
       
