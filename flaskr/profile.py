from flask import (Blueprint, flash, g, redirect, render_template, request, session, url_for, send_file, current_app)
from werkzeug.exceptions import abort
from werkzeug.utils import secure_filename
from bson.objectid import ObjectId
import re
import datetime
import os
import uuid
from flaskr.auth import login_required, student_required, recruiter_required
from flaskr.db import get_db

bp = Blueprint('profile', __name__, url_prefix='/profile')

# Configure upload folder
UPLOAD_FOLDER = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'uploads')
RESUME_FOLDER = os.path.join(UPLOAD_FOLDER, 'resumes')
ALLOWED_EXTENSIONS = {'pdf'}
MAX_CONTENT_LENGTH = 5 * 1024 * 1024  # 5MB

# Create upload directories if they don't exist
os.makedirs(RESUME_FOLDER, exist_ok=True)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

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
    """Display appropriate user profile based on user type"""
    if g.user['user_type'] == 'student':
        return redirect(url_for('profile.student_view'))
    elif g.user['user_type'] == 'recruiter':
        return redirect(url_for('profile.recruiter_view'))
    return render_template('prof/user.html')

@bp.route('/student/view')
@bp.route('/student/view/<student_id>')
@login_required
def student_view(student_id=None):
    """Display student profile view"""
    db = get_db()
    
    # If student_id is provided, load that student's profile
    # Only recruiters can view other students' profiles
    if student_id and g.user['user_type'] == 'recruiter':
        student = db['students'].find_one({'_id': ObjectId(student_id)})
        if not student:
            flash('Student not found', 'error')
            return redirect(url_for('index'))
    elif g.user['user_type'] == 'student':
        # Students can only view their own profile
        student = g.user
    else:
        flash('You do not have permission to view this profile', 'error')
        return redirect(url_for('index'))
    
    return render_template('prof/student_view.html', student=student)

@bp.route('/recruiter/view')
@recruiter_required
def recruiter_view():
    """Display recruiter profile view"""
    return render_template('prof/recruiter_view.html', recruiter=g.user)

@bp.route('/resume/<student_id>')
@login_required
def download_resume(student_id):
    """Download a student's resume"""
    db = get_db()
    
    # Get the student
    student = db['students'].find_one({'_id': ObjectId(student_id)})
    
    if not student or not student.get('resume_url'):
        flash('Resume not found', 'error')
        return redirect(url_for('index'))
    
    # Security check: Only allow recruiters or the student themselves to view the resume
    if g.user['user_type'] != 'recruiter' and str(g.user['_id']) != str(student['_id']):
        flash('You do not have permission to view this resume', 'error')
        return redirect(url_for('index'))
    
    # Get the resume file path
    resume_path = os.path.join(RESUME_FOLDER, student['resume_url'])
    
    if not os.path.exists(resume_path):
        flash('Resume file not found', 'error')
        return redirect(url_for('index'))
    
    # Generate a display filename
    display_filename = f"{student['full_name'].replace(' ', '_')}_Resume.pdf"
    
    # Return the file
    return send_file(resume_path, as_attachment=True, download_name=display_filename)

@bp.route('/resume/view/<student_id>')
@login_required
def view_resume(student_id):
    """View a student's resume inline (not as download)"""
    db = get_db()
    student = db['students'].find_one({'_id': ObjectId(student_id)})
    
    if not student or not student.get('resume_url'):
        flash('Resume not found', 'error')
        return redirect(url_for('index'))
    
    # Check if the current user is the student or a recruiter
    if g.user['user_type'] != 'recruiter' and str(g.user['_id']) != str(student['_id']):
        flash('You do not have permission to view this resume', 'error')
        return redirect(url_for('index'))
    
    resume_path = os.path.join(RESUME_FOLDER, student['resume_url'])
    
    if not os.path.exists(resume_path):
        flash('Resume file not found', 'error')
        return redirect(url_for('index'))
    
    # Return the file for inline viewing (not as attachment)
    return send_file(resume_path, mimetype='application/pdf')

@bp.route('/student', methods=('GET', 'POST'))
@student_required
def student_profile():
    """Handle student profile completion and updates"""
    db = get_db()
    student = g.user
    
    if request.method == 'POST':
        # Get form data - Personal Information
        full_name = request.form.get('full_name', '').strip()
        phone = request.form.get('phone', '').strip()
        dob = request.form.get('dob', '').strip()
        gender = request.form.get('gender', '').strip()
        address = request.form.get('address', '').strip()
        
        # Get form data - Academic Information
        college = request.form.get('college', '').strip()
        branch = request.form.get('branch', '').strip()
        degree = request.form.get('degree', '').strip()
        current_year = request.form.get('current_year', '').strip()
        graduation_year = request.form.get('graduation_year', '').strip()
        cgpa = request.form.get('cgpa', '').strip()
        tenth_marks = request.form.get('tenth_marks', '').strip()
        twelfth_marks = request.form.get('twelfth_marks', '').strip()
        backlogs = request.form.get('backlogs', '0').strip()
        
        # Get form data - Skills & Qualifications
        technical_skills = request.form.get('technical_skills', '').strip()
        soft_skills = request.form.get('soft_skills', '').strip()
        certifications = request.form.get('certifications', '').strip()
        
        # Get resume file
        resume_file = request.files.get('resume')
        
        error = None
        
        # Phone number validation: exactly 10 digits
        phone_regex = r"^\d{10}$"
        
        # Validate required fields
        if not full_name:
            error = 'Full name is required.'
        elif not phone:
            error = 'Phone number is required.'
        elif not re.match(phone_regex, phone):
            error = 'Please enter a valid 10-digit phone number.'
        elif not dob:
            error = 'Date of birth is required.'
        elif not gender:
            error = 'Gender is required.'
        elif not address:
            error = 'Address is required.'
        elif not college:
            error = 'College name is required.'
        elif not branch:
            error = 'Branch is required.'
        elif not degree:
            error = 'Degree is required.'
        elif not current_year:
            error = 'Current year is required.'
        elif not graduation_year:
            error = 'Graduation year is required.'
        elif not cgpa:
            error = 'CGPA is required.'
        # Resume validation - required if not already uploaded
        elif not student.get('resume_url') and (not resume_file or resume_file.filename == ''):
            error = 'Resume is required. Please upload your resume in PDF format.'
        elif resume_file and resume_file.filename != '' and not allowed_file(resume_file.filename):
            error = 'Only PDF files are allowed for resume upload.'
            
        if error is None:
            try:
                # Convert date string to datetime object
                dob_date = datetime.datetime.strptime(dob, '%Y-%m-%d')
                
                # Prepare update data
                update_data = {
                    # Personal Information
                    'full_name': full_name,
                    'phone': f"+91{phone}",
                    'dob': dob_date,
                    'gender': gender,
                    'address': address,
                    
                    # Academic Information
                    'college': college,
                    'branch': branch,
                    'degree': degree,
                    'current_year': current_year,
                    'graduation_year': int(graduation_year),
                    'cgpa': float(cgpa),
                    'profile_complete': True,
                    'updated_at': datetime.datetime.now()
                }
                
                # Add optional fields if provided
                if tenth_marks:
                    update_data['tenth_marks'] = float(tenth_marks)
                if twelfth_marks:
                    update_data['twelfth_marks'] = float(twelfth_marks)
                if backlogs:
                    update_data['backlogs'] = int(backlogs)
                
                # Add skills and qualifications
                update_data['technical_skills'] = technical_skills
                update_data['soft_skills'] = soft_skills
                update_data['certifications'] = certifications
                
                try:
                    # Check if phone number already exists for another user
                    phone_with_code = f"+91{phone}"
                    existing_user = db['students'].find_one({
                        '_id': {'$ne': ObjectId(student['_id'])},
                        'phone': phone_with_code
                    })
                    
                    if existing_user:
                        error = 'This phone number is already registered with another account.'
                        flash(error, 'error')
                        return render_template('prof/student_profile.html', student=student)
                    
                    # Handle resume upload if file is provided
                    if resume_file and resume_file.filename != '':
                        # Generate unique filename for the resume
                        filename = secure_filename(resume_file.filename)
                        unique_filename = f"{uuid.uuid4().hex}_{filename}"
                        file_path = os.path.join(RESUME_FOLDER, unique_filename)
                        
                        # Save the file
                        resume_file.save(file_path)
                        
                        # Delete old file if exists
                        old_resume = student.get('resume_url')
                        if old_resume and os.path.exists(os.path.join(RESUME_FOLDER, old_resume)):
                            try:
                                os.remove(os.path.join(RESUME_FOLDER, old_resume))
                            except Exception as e:
                                print(f"Error removing old resume: {e}")
                        
                        # Add resume data to update
                        update_data['resume_url'] = unique_filename
                        update_data['resume_filename'] = filename
                        update_data['resume_updated_at'] = datetime.datetime.now()
                
                    # Update student profile
                    db['students'].update_one(
                        {'_id': ObjectId(student['_id'])},
                        {'$set': update_data}
                    )
                    
                    # Update the session user data
                    g.user.update(update_data)
                    
                    flash('Profile updated successfully!', 'success')
                    return redirect(url_for('index'))
                except DuplicateKeyError:
                    error = 'This phone number is already registered with another account.'
                    flash(error, 'error')
                    return render_template('prof/student_profile.html', student=student)
            except Exception as e:
                error = f'An error occurred: {str(e)}'
                flash(error, 'error')
        else:
            flash(error, 'error')
    
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
        linkedin_url = request.form.get('linkedin_url', '').strip()
        industry = request.form.get('industry', '').strip()
        designation = request.form.get('designation', '').strip()
        
        # Get eligibility criteria
        default_min_cgpa = request.form.get('default_min_cgpa', '')
        default_eligible_branches = request.form.getlist('default_eligible_branches')
        default_skills = request.form.get('default_skills', '').strip()
        
        # Get job details
        default_job_role = request.form.get('default_job_role', '').strip()
        default_job_type = request.form.get('default_job_type', '').strip()
        
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
            # Check if phone number is already used by another recruiter
            formatted_phone = f"+91{phone}"
            existing_phone = db['recruiters'].find_one({
                '_id': {'$ne': ObjectId(recruiter['_id'])},  # Not the current user
                'phone': formatted_phone
            })
            
            if existing_phone:
                error = 'This phone number is already registered by another recruiter.'
            else:
                try:
                    # Convert CGPA to float if provided
                    if default_min_cgpa:
                        try:
                            default_min_cgpa = float(default_min_cgpa)
                        except ValueError:
                            default_min_cgpa = None
                    else:
                        default_min_cgpa = None
                        
                    # Create update data dictionary
                    update_data = {
                        'full_name': full_name,
                        'phone': formatted_phone,
                        'company_name': company_name,
                        'company_website': company_website,
                        'linkedin_url': linkedin_url,
                        'industry': industry,
                        'designation': designation,
                        'default_min_cgpa': default_min_cgpa,
                        'default_eligible_branches': default_eligible_branches,
                        'default_skills': default_skills,
                        'default_job_role': default_job_role,
                        'default_job_type': default_job_type,
                        'profile_complete': True,
                        'updated_at': datetime.datetime.now()
                    }
                    
                    # Update recruiter profile in database
                    db['recruiters'].update_one(
                        {'_id': ObjectId(recruiter['_id'])},
                        {'$set': update_data}
                    )
                    
                    # Update the session user data
                    g.user.update(update_data)
                except Exception as e:
                    error = f'An error occurred while updating your profile: {str(e)}'
            
            if error is None:
                flash('Profile updated successfully!', 'success')
                return redirect(url_for('profile.recruiter_view'))
            
        flash(error)
    
    # Pre-populate form with existing data if available
    return render_template('prof/recruiter_profile.html', recruiter=recruiter)
