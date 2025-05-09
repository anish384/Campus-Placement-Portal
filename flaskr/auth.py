import functools
from flask import (
    Blueprint, flash, g, redirect, render_template, request, session, url_for
)
import re
import time
import datetime
from flask import request as flask_request
from flaskr.admin_log import log_admin_event
from werkzeug.security import check_password_hash, generate_password_hash
from bson.objectid import ObjectId

from flaskr.db import get_db
from pymongo.errors import DuplicateKeyError

from flask import current_app

bp = Blueprint('auth', __name__)

def init_db_indexes(app):
    """Initialize database indexes for optimal performance"""
    with app.app_context():
        db = get_db()
        # Create indexes for students collection
        db['students'].create_index([('email', 1)], unique=True)
        db['students'].create_index([('username', 1)], unique=True)
        db['students'].create_index([('phone', 1)], unique=True, sparse=True)
        db['students'].create_index([('email', 1), ('password', 1)])
        
        # Create indexes for recruiters collection
        db['recruiters'].create_index([('email', 1)], unique=True)
        db['recruiters'].create_index([('username', 1)], unique=True)
        db['recruiters'].create_index([('phone', 1)], unique=True, sparse=True)
        db['recruiters'].create_index([('company_name', 1)])
        db['recruiters'].create_index([('email', 1), ('password', 1)])

@bp.route('/')
def index():
    return render_template('index.html')

@bp.route('/auth-select')
def auth_select():
    """Display page to select between student and recruiter authentication"""
    return render_template('auth/auth_select.html')

@bp.route('/student/register', methods=('GET', 'POST'))
def student_register():
    if request.method == 'POST':
        username = request.form.get('username', '')
        email = request.form.get('email', '')
        password = request.form.get('password', '')
        confirm_password = request.form.get('confirm_password', '')
        db = get_db()
        error = None

        # Email format validation
        email_regex = r"^[\w\.-]+@[\w\.-]+\.\w+$"
        # Password strength: at least 8 chars, 1 uppercase, 1 lowercase, 1 digit
        password_regex = r"^(?=.*[a-z])(?=.*[A-Z])(?=.*\d).{8,}$"

        if not username:
            error = 'Username is required.'
        elif not email:
            error = 'Email is required.'
        elif not re.match(email_regex, email):
            error = 'Please enter a valid email address.'
        elif not password:
            error = 'Password is required.'
        elif not confirm_password:
            error = 'Please confirm your password.'
        elif password != confirm_password:
            error = 'Passwords do not match.'
        elif not re.match(password_regex, password):
            error = 'Password must be at least 8 characters long, contain an uppercase letter, a lowercase letter, and a digit.'

        if error is None:
            try:
                # Insert student data with minimal information
                result = db['students'].insert_one({
                    'username': username,
                    'email': email,
                    'password': generate_password_hash(password),
                    'created_at': datetime.datetime.now(),
                    'updated_at': datetime.datetime.now(),
                    'profile_complete': False  # Mark profile as incomplete
                })
                
                # Log the registration
                log_admin_event(f"New student registered: {username} ({email})")
                
                # Automatically log in the new user
                session.clear()
                session['user_id'] = str(result.inserted_id)
                session['user_type'] = 'student'
                
                flash('Registration successful! Please complete your profile to apply for jobs.')
                return redirect(url_for('profile.student_profile'))
                
            except DuplicateKeyError as e:
                error_str = str(e)
                if 'email' in error_str:
                    error = f"Email {email} is already registered."
                elif 'username' in error_str:
                    error = f"Username {username} is already taken."
                else:
                    error = "An error occurred during registration. Please try again."
                    
                # Log the error
                current_app.logger.error(f"Registration error: {error_str}")
        
        flash(error)
        
        # Return form data to repopulate the form
        form_data = {
            'username': username,
            'email': email
        }
        
        return render_template('auth/student_register.html', form_data=form_data)
        
    return render_template('auth/student_register.html', form_data={}) if request.method == 'GET' else {}
    
    return render_template('auth/student_register.html', form_data=form_data)

@bp.route('/recruiter/register', methods=('GET', 'POST'))
def recruiter_register():
    if request.method == 'POST':
        username = request.form.get('username', '')
        email = request.form.get('email', '')
        password = request.form.get('password', '')
        confirm_password = request.form.get('confirm_password', '')
        
        db = get_db()
        error = None

        # Email format validation
        email_regex = r"^[\w\.-]+@[\w\.-]+\.\w+$"
        # Password strength: at least 8 chars, 1 uppercase, 1 lowercase, 1 digit
        password_regex = r"^(?=.*[a-z])(?=.*[A-Z])(?=.*\d).{8,}$"

        if not username:
            error = 'Username is required.'
        elif not email:
            error = 'Email is required.'
        elif not re.match(email_regex, email):
            error = 'Please enter a valid email address.'
        elif not password:
            error = 'Password is required.'
        elif not confirm_password:
            error = 'Please confirm your password.'
        elif password != confirm_password:
            error = 'Passwords do not match.'
        elif not re.match(password_regex, password):
            error = 'Password must be at least 8 characters long, contain an uppercase letter, a lowercase letter, and a digit.'

        if error is None:
            try:
                # Insert recruiter data with minimal information
                result = db['recruiters'].insert_one({
                    'username': username,
                    'email': email,
                    'password': generate_password_hash(password),
                    'verified': False,  # Recruiters need verification
                    'created_at': datetime.datetime.now(),
                    'updated_at': datetime.datetime.now(),
                    'profile_complete': False  # Mark profile as incomplete
                })
                
                # Log the registration
                log_admin_event(f"New recruiter registered: {username} ({email})")
                
                # Automatically log in the new user
                session.clear()
                session['user_id'] = str(result.inserted_id)
                session['user_type'] = 'recruiter'
                
                flash('Registration successful! Please complete your profile with company details to post jobs.')
                return redirect(url_for('profile.recruiter_profile'))
                
            except DuplicateKeyError as e:
                error_str = str(e)
                if 'email' in error_str:
                    error = f"Email {email} is already registered."
                elif 'username' in error_str:
                    error = f"Username {username} is already taken."
                else:
                    error = "An error occurred during registration. Please try again."
                    
                # Log the error
                current_app.logger.error(f"Registration error: {error_str}")
        
        flash(error)
        
        # Return form data to repopulate the form
        form_data = {
            'username': username,
            'email': email
        }
        
        return render_template('auth/recruiter_register.html', form_data=form_data)
        
    return render_template('auth/recruiter_register.html', form_data={}) if request.method == 'GET' else {}
    
    return render_template('auth/recruiter_register.html', form_data=form_data)



# Simple in-memory rate limiting (per session)
LOGIN_ATTEMPT_LIMIT = 5
LOGIN_ATTEMPT_WINDOW = 60  # seconds

@bp.route('/student/login', methods=('GET', 'POST'))
def student_login():
    if 'login_attempts' not in session:
        session['login_attempts'] = []

    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        db = get_db()
        error = None

        # Email format validation
        email_regex = r"^[\w\.-]+@[\w\.-]+\.\w+$"
        if not email:
            error = 'Email is required.'
        elif not re.match(email_regex, email):
            error = 'Please enter a valid email address.'
        elif not password:
            error = 'Password is required.'

        # Rate limiting logic
        now = time.time()
        attempts = [t for t in session['login_attempts'] if now - t < LOGIN_ATTEMPT_WINDOW]
        if len(attempts) >= LOGIN_ATTEMPT_LIMIT:
            error = f'Too many login attempts. Please try again in {int(LOGIN_ATTEMPT_WINDOW - (now - attempts[0]))} seconds.'
        else:
            session['login_attempts'] = attempts

        if error is None:
            # Use projection to only fetch required fields
            user = db['students'].find_one(
                {'email': email},
                {'_id': 1, 'password': 1}
            )
            
            if user is None:
                error = 'No student account found with this email.'
            elif not check_password_hash(user['password'], password):
                error = 'Incorrect password.'

        if error is None:
            session.clear()
            session['user_id'] = str(user['_id'])
            session['user_type'] = 'student'
            return redirect(url_for('index'))
        
        flash(error)
    
    return render_template('auth/student_login.html')

@bp.route('/recruiter/login', methods=('GET', 'POST'))
def recruiter_login():
    """Handle recruiter login."""
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        db = get_db()
        error = None
        
        if not email:
            error = 'Email is required.'
        elif not password:
            error = 'Password is required.'
        
        if error is None:
            user = db['recruiters'].find_one({'email': email})
            
            if user is None:
                error = 'Incorrect email.'
            elif not check_password_hash(user['password'], password):
                error = 'Incorrect password.'
            elif not user.get('verified', False):
                error = 'Your account is pending verification. Please wait for approval.'
        
        if error is None:
            session.clear()
            session['user_id'] = str(user['_id'])
            session['user_type'] = 'recruiter'
            return redirect(url_for('index'))
        
        flash(error)
    
    return render_template('auth/recruiter_login.html')

@bp.before_app_request
def load_logged_in_user():
    """Load the logged-in user's data before each request."""
    user_id = session.get('user_id')
    user_type = session.get('user_type')

    if user_id is None or user_type is None:
        g.user = None
    else:
        db = get_db()
        if user_type == 'student':
            g.user = db['students'].find_one({'_id': ObjectId(user_id)})
        elif user_type == 'recruiter':
            g.user = db['recruiters'].find_one({'_id': ObjectId(user_id)})
        
        if g.user:
            g.user['user_type'] = user_type

@bp.route('/logout')
def logout():
    """Log out the current user."""
    session.clear()
    return redirect(url_for('index'))

def login_required(view):
    """Decorator to require login for views."""
    @functools.wraps(view)
    def wrapped_view(**kwargs):
        if g.user is None:
            return redirect(url_for('auth.auth_select'))
        return view(**kwargs)
    return wrapped_view

def student_required(view):
    """Decorator to require student login for views."""
    @functools.wraps(view)
    def wrapped_view(**kwargs):
        if g.user is None or g.user.get('user_type') != 'student':
            flash('You must be logged in as a student to access this page.')
            return redirect(url_for('auth.auth_select'))
        return view(**kwargs)
    return wrapped_view

def recruiter_required(view):
    """Decorator to require recruiter login for views."""
    @functools.wraps(view)
    def wrapped_view(**kwargs):
        if g.user is None or g.user.get('user_type') != 'recruiter':
            flash('You must be logged in as a recruiter to access this page.')
            return redirect(url_for('auth.auth_select'))
        return view(**kwargs)
    return wrapped_view
