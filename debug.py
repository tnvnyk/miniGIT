from app import app
from models import db
from forms import LoginForm, RegisterForm
from sqlalchemy import text

import sys
import platform
import os

def test_config():
    print("=== Testing Configuration ===")
    try:
        assert app.config['SQLALCHEMY_DATABASE_URI']
        assert app.config['SECRET_KEY']
        print("✓ Configuration loaded")
        print(f"✓ Database URI configured: {app.config['SQLALCHEMY_DATABASE_URI'][:40]}...")
        print("✓ Secret key configured")
    except Exception as e:
        print("✗ Configuration error:", e)
        raise

def test_forms():
    print("\n=== Testing Forms ===")
    try:
        with app.app_context():
            login_form = LoginForm()
            register_form = RegisterForm()
            print("✓ Forms imported and initialized successfully")
    except Exception as e:
        print("✗ Forms error:", e)
        raise

def test_database_connection():
    print("\n=== Testing Database Connection ===")
    try:
        with app.app_context():
            with db.engine.connect() as conn:
                conn.execute(text("SELECT 1"))
        print("✓ Database connected successfully")
    except Exception as e:
        print("✗ Database error:", e)
        raise

if __name__ == '__main__':
    print("✓ Successfully imported modules")
    print("=== MiniGitHub Debug Script ===")
    print(f"Python version: {sys.version}")
    print(f"Working directory: {os.getcwd()}")

    tests_passed = 0
    total_tests = 3

    try:
        test_config()
        tests_passed += 1
    except:
        pass

    try:
        test_forms()
        tests_passed += 1
    except:
        pass

    try:
        test_database_connection()
        tests_passed += 1
    except:
        pass

    print("\n=== Results ===")
    print(f"Tests passed: {tests_passed}/{total_tests}")
    if tests_passed == total_tests:
        print("✓ All tests passed!")
    else:
        print("✗ Some tests failed. Please check the errors above.")
