from flask import Blueprint, jsonify, request, current_app
from flask_jwt_extended import jwt_required, get_jwt_identity
from dotenv import load_dotenv
from ...utils.drift_utils.drift import DayDrift

load_dotenv()

drifts_bp = Blueprint("drifts_bp", __name__)

@drifts_bp.route('/drifts', methods=["GET"])
@jwt_required()
def drifts():
    try:
        # get query parameters
        data = request.args
        location = data.get("location", "90272")
        duration = data.get("duration", 2)
        radius = data.get("radius", 5)
        intensity = data.get("intensity", 99)
        model = data.get('model', 'gpt-3.5-turbo')

        # initialize day drift
        day_drift = DayDrift(location=location, duration=duration, radius=radius, intensity=intensity, text_temp=0.2, model=model)

        # check if all parameters exist
        if not all([location, duration, radius]):
            return jsonify({"message": "Error", "error": "Missing parameters required"}), 400

        result = day_drift.create_drift()

        # get parsed data
        title = result.title
        adventure_subtitles = result.adventureSubtitles
        adventures = result.adventures
        total_calories = result.totalCalories
        duration = result.duration
        water_quantity = result.waterQuantity
        safety_precautions = result.safetyPrecautions
        location_parsed = result.location
        if len(adventure_subtitles) != len(adventures):
            return jsonify({"message": "Error", "error": "Server could not load adventure details"}), 500

        if not all([title, adventure_subtitles, adventures, total_calories, duration, water_quantity, safety_precautions]):
            return jsonify({"message": "Error", "error": "We were unable to process an adventure based on the provided parameters. Adventure creation server error."}), 500

        adventure_info = zip(adventure_subtitles, adventures)
        adventure_list = [{"adventureSubtitle": i[0], "adventureDescription": i[1]} for i in adventure_info]
        adventure = {
            "title": title,
            "adventureList": adventure_list,
            "totalCalories":total_calories, 
            "duration": duration, 
            "waterQuantity":water_quantity, 
            "safetyPrecautions":safety_precautions, 
            "location": location_parsed
        }

        response = {
            "message": "Success",
            "adventure":adventure 
        }

        return jsonify(response), 200

    except Exception as e:
        current_app.logger.error(f"Error during drifts retrieval: {e}")
        return jsonify({"message": "Error", "error": "An unexpected server error occurred."}), 500
