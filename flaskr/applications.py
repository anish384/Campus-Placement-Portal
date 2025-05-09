import functools
from flask import (
    Blueprint, flash, g, redirect, render_template, request, session, url_for, jsonify
)
from werkzeug.exceptions import abort
from bson.objectid import ObjectId
import datetime

from flaskr.db import get_db
from flaskr.auth import login_required, recruiter_required, student_required
from flaskr.jobs import get_job

bp = Blueprint('applications', __name__, url_prefix='/applications')

@bp.route('/job/<job_id>')
@recruiter_required
def job_applications(job_id):
    """View all applications for a specific job."""
    job = get_job(job_id)
    
    # Check if the current user is the creator of this job listing
    if g.user['_id'] != job['recruiter_id']:
        abort(403)
    
    db = get_db()
    applications = list(db['applications'].find({'job_id': ObjectId(job_id)}).sort('created_at', -1))
    
    return render_template('applications/job_applications.html', job=job, applications=applications)

@bp.route('/view/<application_id>')
@recruiter_required
def view_application(application_id):
    """View detailed application with integrated PDF viewer."""
    db = get_db()
    
    # Get the application
    application = db['applications'].find_one({'_id': ObjectId(application_id)})
    if application is None:
        abort(404)
    
    # Get the job
    job = db['jobs'].find_one({'_id': application['job_id']})
    if job is None:
        abort(404)
    
    # Check if the current user is the creator of this job listing
    if g.user['_id'] != job['recruiter_id']:
        abort(403)
    
    return render_template('applications/application_view.html', application=application, job=job)

@bp.route('/view-pdf/<application_id>')
@recruiter_required
def view_pdf(application_id):
    """View dedicated PDF viewer for an application's resume."""
    db = get_db()
    
    # Get the application
    application = db['applications'].find_one({'_id': ObjectId(application_id)})
    if application is None:
        abort(404)
    
    # Get the job
    job = db['jobs'].find_one({'_id': application['job_id']})
    if job is None:
        abort(404)
    
    # Check if the current user is the creator of this job listing
    if g.user['_id'] != job['recruiter_id']:
        abort(403)
    
    return render_template('applications/pdf_viewer.html', 
                           application_id=application_id,
                           student_id=application['student_id'],
                           student_name=application['student_name'])

@bp.route('/<application_id>/update-status', methods=('POST',))
@recruiter_required
def update_status(application_id):
    """Update the status of an application."""
    db = get_db()
    
    # Get the application
    application = db['applications'].find_one({'_id': ObjectId(application_id)})
    if application is None:
        abort(404)
    
    # Get the job
    job = db['jobs'].find_one({'_id': application['job_id']})
    if job is None:
        abort(404)
    
    # Check if the current user is the creator of this job listing
    if g.user['_id'] != job['recruiter_id']:
        abort(403)
    
    # Get the new status from the form
    new_status = request.form.get('status')
    if not new_status:
        flash('Status is required.', 'error')
        return redirect(url_for('applications.job_applications', job_id=str(job['_id'])))
    
    # Update the application status
    db['applications'].update_one(
        {'_id': ObjectId(application_id)},
        {'$set': {
            'status': new_status,
            'status_updated_at': datetime.datetime.now(),
            'status_updated_by': g.user['_id']
        }}
    )
    
    # Add a notification for the student
    db['notifications'].insert_one({
        'user_id': application['student_id'],
        'title': f'Application Status Updated',
        'message': f'Your application for {job["title"]} at {job["company_name"]} has been updated to: {new_status}',
        'read': False,
        'created_at': datetime.datetime.now()
    })
    
    flash('Application status updated successfully!', 'success')
    return redirect(url_for('applications.job_applications', job_id=str(job['_id'])))

@bp.route('/<application_id>/schedule-interview', methods=('GET', 'POST'))
@recruiter_required
def schedule_interview(application_id):
    """Schedule an interview for an application."""
    db = get_db()
    
    # Get the application
    application = db['applications'].find_one({'_id': ObjectId(application_id)})
    if application is None:
        abort(404)
    
    # Get the job
    job = db['jobs'].find_one({'_id': application['job_id']})
    if job is None:
        abort(404)
    
    # Check if the current user is the creator of this job listing
    if g.user['_id'] != job['recruiter_id']:
        abort(403)
    
    if request.method == 'POST':
        interview_date = request.form.get('interview_date')
        interview_time = request.form.get('interview_time')
        interview_location = request.form.get('interview_location')
        interview_type = request.form.get('interview_type')
        interview_details = request.form.get('interview_details')
        
        error = None
        
        if not interview_date:
            error = 'Interview date is required.'
        elif not interview_time:
            error = 'Interview time is required.'
        elif not interview_location:
            error = 'Interview location is required.'
        elif not interview_type:
            error = 'Interview type is required.'
        
        if error is None:
            # Create a datetime object from the date and time
            interview_datetime = datetime.datetime.strptime(f'{interview_date} {interview_time}', '%Y-%m-%d %H:%M')
            
            # Create the interview
            interview_id = db['interviews'].insert_one({
                'application_id': ObjectId(application_id),
                'job_id': job['_id'],
                'student_id': application['student_id'],
                'recruiter_id': g.user['_id'],
                'interview_datetime': interview_datetime,
                'interview_location': interview_location,
                'interview_type': interview_type,
                'interview_details': interview_details,
                'status': 'Scheduled',
                'created_at': datetime.datetime.now()
            }).inserted_id
            
            # Update the application status
            db['applications'].update_one(
                {'_id': ObjectId(application_id)},
                {'$set': {
                    'status': 'Interview Scheduled',
                    'interview_id': interview_id,
                    'status_updated_at': datetime.datetime.now(),
                    'status_updated_by': g.user['_id']
                }}
            )
            
            # Add a notification for the student
            db['notifications'].insert_one({
                'user_id': application['student_id'],
                'title': f'Interview Scheduled',
                'message': f'An interview has been scheduled for your application to {job["title"]} at {job["company_name"]}. Date: {interview_date}, Time: {interview_time}',
                'read': False,
                'created_at': datetime.datetime.now()
            })
            
            flash('Interview scheduled successfully!', 'success')
            return redirect(url_for('applications.job_applications', job_id=str(job['_id'])))
        
        flash(error, 'error')
    
    # Get interview types for the form
    interview_types = [
        'In-person',
        'Phone',
        'Video',
        'Technical',
        'HR',
        'Group Discussion'
    ]
    
    return render_template('applications/schedule_interview.html', 
                          application=application, 
                          job=job, 
                          interview_types=interview_types)

@bp.route('/interviews')
@login_required
def interviews():
    """View all interviews for the current user."""
    db = get_db()
    
    if g.user['user_type'] == 'student':
        # Get all interviews for the student
        interviews = list(db['interviews'].find({'student_id': g.user['_id']}).sort('interview_datetime', 1))
    else:
        # Get all interviews created by the recruiter
        interviews = list(db['interviews'].find({'recruiter_id': g.user['_id']}).sort('interview_datetime', 1))
    
    # Get job and application details for each interview
    for interview in interviews:
        job = db['jobs'].find_one({'_id': interview['job_id']})
        if job:
            interview['job'] = job
        
        application = db['applications'].find_one({'_id': interview['application_id']})
        if application:
            interview['application'] = application
            
            # If recruiter, get student details
            if g.user['user_type'] == 'recruiter':
                student = db['students'].find_one({'_id': application['student_id']})
                if student:
                    interview['student'] = student
    
    return render_template('applications/interviews.html', interviews=interviews)

@bp.route('/interview/<interview_id>/update-result', methods=('POST',))
@recruiter_required
def update_interview_result(interview_id):
    """Update the result of an interview."""
    db = get_db()
    
    # Get the interview
    interview = db['interviews'].find_one({'_id': ObjectId(interview_id)})
    if interview is None:
        abort(404)
    
    # Check if the current user is the creator of this interview
    if g.user['_id'] != interview['recruiter_id']:
        abort(403)
    
    # Get the application
    application = db['applications'].find_one({'_id': interview['application_id']})
    if application is None:
        abort(404)
    
    # Get the job
    job = db['jobs'].find_one({'_id': interview['job_id']})
    if job is None:
        abort(404)
    
    # Get the result from the form
    result = request.form.get('result')
    feedback = request.form.get('feedback', '')
    
    if not result:
        flash('Result is required.', 'error')
        return redirect(url_for('applications.interviews'))
    
    # Update the interview status
    db['interviews'].update_one(
        {'_id': ObjectId(interview_id)},
        {'$set': {
            'status': 'Completed',
            'result': result,
            'feedback': feedback,
            'completed_at': datetime.datetime.now(),
            'completed_by': g.user['_id']
        }}
    )
    
    # Update the application status based on the result
    new_status = 'Selected' if result == 'Pass' else 'Rejected'
    
    db['applications'].update_one(
        {'_id': interview['application_id']},
        {'$set': {
            'status': new_status,
            'status_updated_at': datetime.datetime.now(),
            'status_updated_by': g.user['_id']
        }}
    )
    
    # Add a notification for the student
    db['notifications'].insert_one({
        'user_id': application['student_id'],
        'title': f'Interview Result: {result}',
        'message': f'Your interview for {job["title"]} at {job["company_name"]} has been marked as {result}. {feedback}',
        'read': False,
        'created_at': datetime.datetime.now()
    })
    
    flash('Interview result updated successfully!', 'success')
    return redirect(url_for('applications.interviews'))

@bp.route('/notifications')
@login_required
def notifications():
    """View all notifications for the current user."""
    db = get_db()
    
    # Get all notifications for the user
    notifications = list(db['notifications'].find({'user_id': g.user['_id']}).sort('created_at', -1))
    
    # Mark all unread notifications as read
    db['notifications'].update_many(
        {'user_id': g.user['_id'], 'read': False},
        {'$set': {'read': True}}
    )
    
    return render_template('applications/notifications.html', notifications=notifications)
