from flask import jsonify, Blueprint, request, current_app
from werkzeug.security import check_password_hash, generate_password_hash
from flask_jwt_extended import create_access_token, create_refresh_token
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail
import random
import datetime
from dotenv import load_dotenv
from flask_jwt_extended import jwt_required, get_jwt_identity
import os
import time

load_dotenv()

auth_bp = Blueprint('auth_bp', __name__)


@auth_bp.route('/register', methods=['POST'])
def register():
    try:
        db = current_app.db
        # get data
        data = request.get_json()
        username = data.get('username', None)
        email = data.get('email', None)
        password = data.get('password', None)
        repeat_password = data.get('repeatPassword', None)

        if not any([email, data, username, password]):
            return jsonify({"message": "Error", "error":"missing required data"}), 400

        # check if password match
        if password != repeat_password:
            return jsonify({"message": "Error", 'error':"passwords do not match"}), 400 

        # check if user exists
        user_email = db.users.find_one({'personal_info.email': email})
        if user_email:
            return jsonify({"message": "Error", "error":"email already exists"}), 400
        user_name = db.users.find_one({"personal_info.username": username})
        if user_name:
            return jsonify({"message": "Error", "error":"username already exists"}), 400

        # create default token count
        tokens = 100

        # generate password hash
        hashed_password = generate_password_hash(password)

        # generate a confirmation code
        confirmation_code = ''.join(random.choices('0123456789', k=6))

        new_user_ob = {
            "personal_info": {
                "username": username,
                "email": email,
            },
            "authentication": {
                "password": hashed_password,
                "confirmedRegistration": False,
                "confirmationCode": confirmation_code,
                "lastLoginDate": None,
                "accountStatus": "active"
            },
            "user_progress": {
                "introCompleted": False
            }, 
            "financial": {
                "tokenCount": tokens,
            }, 
            "preferences": {
                "defaultLocation":None, 
                "defaultDuration":None, 
                "defaultRadius": None, 
                "defaultIntensity":None
            }
        }    

        new_user = db.users.insert_one(new_user_ob)
        user_id = new_user.inserted_id

        # send email with the confirmation code using SendGrid
        message = Mail(
            from_email='dev.works.apps@gmail.com', # Change this to your sending email
            to_emails=email,
            subject='Confirmation Code',
            plain_text_content=f'Your confirmation code is: {confirmation_code}')
        
        sg = SendGridAPIClient(os.environ.get('SENDGRID_API_KEY'))
        response = sg.send(message)

        return jsonify({"message": 'Success', "response": 'successfully created new user', "user": str(user_id)}), 201
    
    except Exception as e:
        current_app.logger.error(f"Error during registration: {e}")
        return jsonify({"message": "Error", "error": "An unexpected server error occurred. Please try again."}), 500



@auth_bp.route('/login', methods=['POST'])
def login():
    # Init database
    db = current_app.db

    try:
        # Get POST data
        data = request.get_json()
        email = data.get('email')
        password = data.get('password')

        # Check if all required data is provided
        if not email or not password:
            return jsonify({"message": "Error", "error": "Email or password not provided. Please try again with both required fields."}), 400

        # Query for the user
        user = db.users.find_one({'personal_info.email': email})

        # Check if user exists
        if not user:
            return jsonify({"message": "Error", "error": "User with the provided email does not exist"}), 400

        # Check if the user has confirmed their registration
        if not user["authentication"]["confirmedRegistration"]:
            return jsonify({"message": "Error", "error": "Please confirm your registration before logging in"}), 403

        # Check if password matches the hash in the database
        if not check_password_hash(user["authentication"]["password"], password):
            return jsonify({"message": "Error", "error": "Incorrect password. Please check your password and try again."}), 401

        # Update the last login date for the user
        db.users.update_one({'_id': user['_id']}, {"$set": {"authentication.lastLoginDate": datetime.datetime.utcnow()}})

        # Extract user token count and other properties
        token_count = user["financial"]["tokenCount"]
        confirmed_registration = user["authentication"]["confirmedRegistration"]
        intro_completed = user["user_progress"]["introCompleted"]
        username = user["personal_info"]["username"]
        email = user["personal_info"]["email"]
        preferences = user['preferences']
        # Generate JWT tokens
        token = create_access_token(identity=str(user["_id"]))
        refresh_token = create_refresh_token(identity=str(user["_id"]))

        # Prepare response
        response = {
            "message": "Success",
            "data": {
                "token": token,
                "refreshToken": refresh_token,
                "tokenCount": token_count,
                "confirmedRegistration": confirmed_registration,
                "introCompleted": intro_completed,
                "username": username,
                "email": email, 
                "preferences": preferences
            }
        }

        return jsonify(response), 200

    except Exception as e:
        current_app.logger.error(f"Error during login: {e}")
        return jsonify({"message": "Error", "error": "An unexpected server error occurred."}), 500


@auth_bp.route('/refresh-token', methods=["POST"])
@jwt_required(refresh=True)
def refresh_token():
    identity = get_jwt_identity()
    token = create_access_token(identity=identity)
    response = {'message':"Success", "token":token}
    return jsonify(response), 200

@auth_bp.route('/verify-token', methods=['GET'])
@jwt_required()   # This ensures the route is protected by JWT and the token is valid
def verify_token():
    current_user_id = get_jwt_identity()  # this gets the identity from the token
    return jsonify(isValid=True, user=current_user_id), 200


@auth_bp.route('/confirm-registration', methods=['POST'])
def confirm_registration():
    try:
        db = current_app.db
        data = request.get_json()
        email = data.get('email')
        code = data.get('code')

        if not email or not code:
            return jsonify({"message": "Error", "error": "Email or confirmation code not provided"}), 400
        
        user = db.users.find_one({'personal_info.email': email})

        if not user:
            return jsonify({"message": "Error", "error": "User not found"}), 400
        
        if user["authentication"]["confirmationCode"] != code:
            return jsonify({"message": "Error", "error": "Incorrect confirmation code"}), 400
        
        db.users.update_one({'_id': user['_id']}, {"$set": {"authentication.confirmedRegistration": True}})
        
        return jsonify({"message": "Success", "response": "Registration confirmed successfully!"}), 200

    except Exception as e:
        current_app.logger.error(f"Error during confirmation: {e}")
        return jsonify({"message": "Error", "error": "An unexpected server error occurred."}), 500



@auth_bp.route('/resend-code', methods=['POST'])
def resend_code():
    try:
        db = current_app.db
        data = request.get_json()
        email = data.get('email')
        
        if not email:
            return jsonify({"message": "Error", "error": "Email not provided"}), 400

        user = db.users.find_one({'personal_info.email': email})
        if not user:
            return jsonify({"message": "Error", "error": "User not found"}), 400
        
        # generate a new confirmation code
        confirmation_code = ''.join(random.choices('0123456789', k=6))
        
        # update the user's confirmation code in the database
        db.users.update_one({'_id': user['_id']}, {"$set": {"authentication.confirmationCode": confirmation_code}})
        
        # send email with the confirmation code using SendGrid
        message = Mail(
            from_email='dev.works.apps@gmail.com', # Change this to your sending email
            to_emails=email,
            subject='New Confirmation Code',
            plain_text_content=f'Your new confirmation code is: {confirmation_code}')
        
        sg = SendGridAPIClient(os.environ.get('SENDGRID_API_KEY'))
        response = sg.send(message)
        
        return jsonify({"message": "Success", "response": "New confirmation code sent successfully"}), 200
    
    except Exception as e:
        current_app.logger.error(f"Error resending confirmation code: {e}")
        return jsonify({"message": "Error", "error": "An unexpected server error occurred. Please try again."}), 500



@auth_bp.route('/test', methods=['POST'])
def test():
    return jsonify(message='testing'), 200
    