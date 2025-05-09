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
        # Create compound unique index for email and username
        db['users'].create_index([('email', 1)], unique=True)
        db['users'].create_index([('username', 1)], unique=True)
        # Add sparse index for phone numbers (only indexes documents that have the field)
        db['users'].create_index([('phone', 1)], unique=True, sparse=True)
        # Add index for frequently queried fields
        db['users'].create_index([('email', 1), ('password', 1)])

@bp.route('/')
def index():
    return render_template('index.html')

@bp.route('/register', methods=('GET', 'POST'))
def register():
    if request.method == 'POST':
        username = request.form.get('username', '')
        email = request.form.get('email', '')
        password = request.form.get('password', '')
        confirm_password = request.form.get('confirm_password', '')
        phone = request.form.get('phone', '')
        db = get_db()
        error = None

        # Email format validation
        email_regex = r"^[\w\.-]+@[\w\.-]+\.\w+$"
        # Password strength: at least 8 chars, 1 uppercase, 1 lowercase, 1 digit
        password_regex = r"^(?=.*[a-z])(?=.*[A-Z])(?=.*\d).{8,}$"
        # Phone number validation: exactly 10 digits
        phone_regex = r"^\d{10}$"

        if not username:
            error = 'Username is required.'
        elif not email:
            error = 'Email is required.'
        elif not re.match(email_regex, email):
            error = 'Please enter a valid email address.'
        elif not phone:
            error = 'Phone number is required.'
        elif not re.match(phone_regex, phone):
            error = 'Please enter a valid 10-digit phone number.'
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
                # Directly attempt to insert the user - let MongoDB's unique indexes handle duplicates
                result = db['users'].insert_one({
                    'username': username,
                    'email': email,
                    'phone': f"+91{phone}",  # Store phone number with country code
                    'password': generate_password_hash(password),
                    'is_admin': False,  # Default to non-admin
                    'created_at': datetime.datetime.now()  # Add creation timestamp
                })
                log_admin_event('register_success', 'User registered successfully.', user_email=email, ip=flask_request.remote_addr)
                
                # Automatically log in the user after successful registration
                session.clear()
                session['user_id'] = str(result.inserted_id)
                flash('Registration successful! You are now logged in.')
                return redirect(url_for('index'))
            except DuplicateKeyError as e:
                # Check which unique constraint was violated
                if 'email' in str(e):
                    error = "An account with this email already exists. Please use a different email."
                elif 'username' in str(e):
                    error = "This username is already taken. Please choose another."
                else:
                    error = "A user with these credentials already exists. Please try different ones."
                log_admin_event('register_fail', error, user_email=email, ip=flask_request.remote_addr)

        if error:
            log_admin_event('register_error', error, user_email=email, ip=flask_request.remote_addr)
            flash(error)
            # Store form data in session for form repopulation
            session['register_form_data'] = {
                'username': username,
                'email': email,
                'phone': phone
            }
            return redirect(url_for('auth.register'))

    # Get stored form data if it exists
    form_data = session.pop('register_form_data', {}) if request.method == 'GET' else {}
    
    return render_template('auth/register.html', form_data=form_data)



# Simple in-memory rate limiting (per session)
LOGIN_ATTEMPT_LIMIT = 5
LOGIN_ATTEMPT_WINDOW = 60  # seconds

@bp.route('/login', methods=('GET', 'POST'))
def login():
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
            user = db['users'].find_one(
                {'email': email},
                {'_id': 1, 'password': 1}
            )
            
            if user is None:
                error = 'No account found with this email.'
            elif not check_password_hash(user['password'], password):
                error = 'Incorrect password.'

        if error is None:
            session.clear()
            session['user_id'] = str(user['_id'])
            log_admin_event('login_success', 'User logged in successfully.', user_email=email, ip=flask_request.remote_addr)
            return redirect(url_for('index'))
        else:
            # Record failed attempt
            session['login_attempts'].append(now)
            session.modified = True
            log_admin_event('login_fail', error, user_email=email, ip=flask_request.remote_addr)
            flash(error)

    return render_template('auth/login.html')

@bp.before_app_request
def load_logged_in_user():
    user_id = session.get('user_id')
    if user_id is None:
        g.user = None
    else:
        db = get_db()
        # Convert string back to ObjectId when querying
        g.user = db['users'].find_one({'_id': ObjectId(user_id)})
    

@bp.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('index'))

def login_required(view):
    @functools.wraps(view)
    def wrapped_view(**kwargs):
        if g.user is None:
            return redirect(url_for('auth.login'))

        return view(**kwargs)

    return wrapped_view

