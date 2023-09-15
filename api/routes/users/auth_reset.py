
from flask import jsonify, Blueprint, request, current_app
from werkzeug.security import generate_password_hash
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail
import random
from dotenv import load_dotenv
import os

load_dotenv()

auth_reset_bp = Blueprint('auth_reset_bp', __name__)



@auth_reset_bp.route('/request-password-reset', methods=['POST'])
def request_password_reset():
    try:
        db = current_app.db
        data = request.get_json()
        email = data.get('email')
        
        if not email:
            return jsonify({"message": "Error", "error": "Email not provided"}), 400

        user = db.users.find_one({'personal_info.email': email})
        if not user:
            return jsonify({"message": "Error", "error": "User not found"}), 400
        
        # generate a reset code
        reset_code = ''.join(random.choices('0123456789', k=6))
        
        # Store the reset code with the user's data (consider adding an expiry time if needed)
        db.users.update_one({'_id': user['_id']}, {"$set": {"authentication.resetCode": reset_code}})
        
        # send email with the reset code using SendGrid
        message = Mail(
            from_email='dev.works.apps@gmail.com',
            to_emails=email,
            subject='Password Reset Code',
            plain_text_content=f'Your password reset code is: {reset_code}')
        
        sg = SendGridAPIClient(os.environ.get('SENDGRID_API_KEY'))
        response = sg.send(message)
        
        return jsonify({"message": "Success", "response": "Reset code sent to email"}), 200
    
    except Exception as e:
        current_app.logger.error(f"Error requesting password reset: {e}")
        return jsonify({"message": "Error", "error": "An unexpected server error occurred. Please try again."}), 500


@auth_reset_bp.route('/reset-password', methods=['POST'])
def reset_password():
    try:
        db = current_app.db
        data = request.get_json()
        email = data.get('email')
        reset_code = data.get('resetCode')
        new_password = data.get('newPassword')
        
        if not email or not reset_code or not new_password:
            return jsonify({"message": "Error", "error": "Email, reset code, or new password not provided"}), 400
        
        user = db.users.find_one({'personal_info.email': email})
        if not user:
            return jsonify({"message": "Error", "error": "User not found"}), 400

        # Validate the reset code
        if user["authentication"].get("resetCode") != reset_code:
            return jsonify({"message": "Error", "error": "Invalid reset code"}), 400
        
        hashed_password = generate_password_hash(new_password)
        db.users.update_one({'_id': user['_id']}, {"$set": {"authentication.password": hashed_password, "authentication.resetCode": None}})
        
        return jsonify({"message": "Success", "response": "Password updated successfully"}), 200
    
    except Exception as e:
        current_app.logger.error(f"Error resetting password: {e}")
        return jsonify({"message": "Error", "error": "An unexpected server error occurred. Please try again."}), 500

