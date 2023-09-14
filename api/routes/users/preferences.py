from flask import Blueprint, jsonify, request, current_app
from dotenv import load_dotenv
from flask_jwt_extended import get_jwt_identity, jwt_required
from bson import ObjectId

load_dotenv()

preferences_bp = Blueprint('preferences_bp', __name__)

@preferences_bp.route('/preferences', methods=["PUT"])
@jwt_required()
def preferences():
    try:
        user_id = get_jwt_identity()
        # db instance
        db = current_app.db

        # get data to update
        data = request.get_json()
        location = data.get("location", None)
        duration = data.get("duration", None)
        intensity = data.get('intensity', None)
        radius = data.get('radius', None)  # Adding radius if you need it

        # Use a dictionary to hold the fields you want to update.
        update_fields = {}

        if location:
            update_fields["preferences.defaultLocation"] = location
        if duration:
            update_fields["preferences.defaultDuration"] = duration
        if intensity:
            update_fields["preferences.defaultIntensity"] = intensity
        if radius:
            update_fields["preferences.defaultRadius"] = radius

        # Update the user in the database
        result = db.users.update_one({"_id": ObjectId(user_id)}, {"$set": update_fields})

        if result.modified_count == 1:
            return jsonify({"message": "Success", "response": "Preferences updated successfully."}), 200
        else:
            return jsonify({"message": "Error", "error": "Failed to update preferences."}), 400

    except Exception as e:
        current_app.logger.error(f"Error during updating preferences: {e}")
        return jsonify({"message": "Error", "error": "An unexpected server error occurred."}), 500
