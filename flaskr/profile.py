from flask import (Blueprint, flash, g, redirect, render_template, request, session, url_for)
from werkzeug.exceptions import abort
from bson.objectid import ObjectId
import re
import datetime
from flaskr.auth import login_required, student_required, recruiter_required
from flaskr.db import get_db

bp = Blueprint('profile', __name__, url_prefix='/profile')

@bp.route('/')
@login_required
def index():
    """Redirect to the appropriate profile page based on user type"""
    if g.user['user_type'] == 'student':
        return redirect(url_for('profile.student_profile'))
    elif g.user['user_type'] == 'recruiter':
        return redirect(url_for('profile.recruiter_profile'))
    return redirect(url_for('index'))

@bp.route('/user')
@login_required
def user():
    """Display user profile"""
    return render_template('prof/user.html')

@bp.route('/student', methods=('GET', 'POST'))
@student_required
def student_profile():
    """Handle student profile completion and updates"""
    db = get_db()
    student = g.user
    
    if request.method == 'POST':
        # Get form data
        full_name = request.form.get('full_name', '').strip()
        phone = request.form.get('phone', '').strip()
        college = request.form.get('college', '').strip()
        branch = request.form.get('branch', '').strip()
        cgpa = request.form.get('cgpa', '').strip()
        graduation_year = request.form.get('graduation_year', '').strip()
        
        error = None
        
        # Phone number validation: exactly 10 digits
        phone_regex = r"^\d{10}$"
        
        if not full_name:
            error = 'Full name is required.'
        elif not phone:
            error = 'Phone number is required.'
        elif not re.match(phone_regex, phone):
            error = 'Please enter a valid 10-digit phone number.'
        elif not college:
            error = 'College name is required.'
        elif not branch:
            error = 'Branch is required.'
        elif not cgpa:
            error = 'CGPA is required.'
        elif not graduation_year:
            error = 'Graduation year is required.'
            
        if error is None:
            # Update student profile
            db['students'].update_one(
                {'_id': ObjectId(student['_id'])},
                {'$set': {
                    'full_name': full_name,
                    'phone': f"+91{phone}",
                    'college': college,
                    'branch': branch,
                    'cgpa': float(cgpa),
                    'graduation_year': int(graduation_year),
                    'profile_complete': True,
                    'updated_at': datetime.datetime.now()
                }}
            )
            
            flash('Profile updated successfully!')
            return redirect(url_for('index'))
            
        flash(error)
    
    # Pre-populate form with existing data if available
    return render_template('prof/student_profile.html', student=student)

@bp.route('/recruiter', methods=('GET', 'POST'))
@recruiter_required
def recruiter_profile():
    """Handle recruiter profile completion and updates"""
    db = get_db()
    recruiter = g.user
    
    if request.method == 'POST':
        # Get form data
        full_name = request.form.get('full_name', '').strip()
        phone = request.form.get('phone', '').strip()
        company_name = request.form.get('company_name', '').strip()
        company_website = request.form.get('company_website', '').strip()
        industry = request.form.get('industry', '').strip()
        designation = request.form.get('designation', '').strip()
        
        error = None
        
        # Phone number validation: exactly 10 digits
        phone_regex = r"^\d{10}$"
        
        if not full_name:
            error = 'Full name is required.'
        elif not phone:
            error = 'Phone number is required.'
        elif not re.match(phone_regex, phone):
            error = 'Please enter a valid 10-digit phone number.'
        elif not company_name:
            error = 'Company name is required.'
        elif not industry:
            error = 'Industry is required.'
        elif not designation:
            error = 'Your designation is required.'
            
        if error is None:
            # Update recruiter profile
            db['recruiters'].update_one(
                {'_id': ObjectId(recruiter['_id'])},
                {'$set': {
                    'full_name': full_name,
                    'phone': f"+91{phone}",
                    'company_name': company_name,
                    'company_website': company_website,
                    'industry': industry,
                    'designation': designation,
                    'profile_complete': True,
                    'updated_at': datetime.datetime.now()
                }}
            )
            
            flash('Profile updated successfully!')
            return redirect(url_for('index'))
            
        flash(error)
    
    # Pre-populate form with existing data if available
    return render_template('prof/recruiter_profile.html', recruiter=recruiter)
