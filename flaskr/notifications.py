import os
from twilio.rest import Client
from flask import current_app
import traceback

def send_sms(to_number, message):
    """
    Send an SMS notification to a user using Twilio.
    
    Args:
        to_number (str): The recipient's phone number in E.164 format (e.g., +1234567890)
        message (str): The message content to send
        
    Returns:
        bool: True if the message was sent successfully, False otherwise
    """
    # Print debug info
    current_app.logger.info(f"Sending SMS to: {to_number}")
    current_app.logger.info(f"Message: {message}")
    
    try:
        # Get Twilio credentials from environment variables - same as test_sms_direct.py
        account_sid = os.environ.get('TWILIO_ACCOUNT_SID')
        auth_token = os.environ.get('TWILIO_AUTH_TOKEN')
        from_number = os.environ.get('TWILIO_PHONE_NUMBER')
        
        current_app.logger.info(f"Using Twilio phone: {from_number}")
        
        # Check for missing credentials - same validation as test_sms_direct.py
        if not account_sid or account_sid == "your_account_sid_here" or not account_sid.strip():
            current_app.logger.error("ERROR: Twilio Account SID is missing or invalid in .env file")
            return False
            
        if not auth_token or auth_token == "your_auth_token_here" or not auth_token.strip():
            current_app.logger.error("ERROR: Twilio Auth Token is missing or invalid in .env file")
            return False
            
        if not from_number or from_number == "your_twilio_phone_number_here" or not from_number.strip():
            current_app.logger.error("ERROR: Twilio Phone Number is missing or invalid in .env file")
            return False
        
        # Initialize Twilio client - exactly as in test_sms_direct.py
        current_app.logger.info("Creating Twilio client...")
        client = Client(account_sid, auth_token)
        
        # Send the message - exactly as in test_sms_direct.py
        current_app.logger.info(f"Sending message from {from_number} to {to_number}")
        sms_response = client.messages.create(
            body=message,
            from_=from_number,
            to=to_number
        )
        
        # Log success
        current_app.logger.info(f"Success! SMS sent with SID: {sms_response.sid}")
        return True
        
    except Exception as e:
        # Log the full error with traceback
        current_app.logger.error(f"Failed to send SMS: {str(e)}")
        current_app.logger.error(traceback.format_exc())
        return False


def notify_student_shortlisted(student, job):
    """
    Send an SMS notification to a student when they are shortlisted for a job.
    
    Args:
        student (dict): The student document from the database
        job (dict): The job document from the database
        
    Returns:
        bool: True if the notification was sent successfully, False otherwise
    """
    if not student.get('phone'):
        current_app.logger.warning(f"Cannot send SMS notification: Student {student.get('_id')} has no phone number")
        return False
    
    # Format the phone number for Twilio (E.164 format)
    # The phone number in the database should already include the +91 prefix
    to_number = student['phone']
    
    # Create the message
    company_name = job.get('company_name', 'A company')
    job_title = job.get('title', 'a position')
    
    message = f"Congratulations! You have been shortlisted for {job_title} at {company_name}. Log in to CareerBridge to check the details and next steps."
    
    # Send the SMS
    return send_sms(to_number, message)


def notify_student_selected(student, job):
    """
    Send an SMS notification to a student when they are selected for a job.
    
    Args:
        student (dict): The student document from the database
        job (dict): The job document from the database
        
    Returns:
        bool: True if the notification was sent successfully, False otherwise
    """
    if not student.get('phone'):
        current_app.logger.warning(f"Cannot send SMS notification: Student {student.get('_id')} has no phone number")
        return False
    
    # Format the phone number for Twilio (E.164 format)
    # The phone number in the database should already include the +91 prefix
    to_number = student['phone']
    
    # Create the message
    company_name = job.get('company_name', 'A company')
    job_title = job.get('title', 'a position')
    
    message = f"Great news! You have been SELECTED for {job_title} at {company_name}. Congratulations on your success! Log in to CareerBridge for more details."
    
    # Send the SMS
    return send_sms(to_number, message)
