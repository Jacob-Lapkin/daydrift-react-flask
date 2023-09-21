from flask import Blueprint, jsonify, request, current_app
from flask_jwt_extended import jwt_required, get_jwt_identity
from dotenv import load_dotenv
import datetime
from bson import ObjectId, errors
from ...utils.drift_utils.drift import DayDrift
from ...utils.location_util.location import get_location
import pymongo

load_dotenv()

drifts_bp = Blueprint("drifts_bp", __name__)

@drifts_bp.route('/drifts', methods=["POST"])
@jwt_required()
def drifts():
    try:
        db = current_app.db
        # get query parameters
        data = request.get_json()
        longitude = data.get('longitude', None)
        latitude = data.get('latitude', None)
        duration = data.get("duration", None)
        radius = data.get("radius", None)
        intensity = data.get("intensity", None)
        model = data.get('model', 'gpt-3.5-turbo')
        
        # get current user
        user = get_jwt_identity()

        # check credit count
        get_user = db.users.find_one({"_id":ObjectId(user)})
        credit_count = get_user["financial"]['creditCount']

        if credit_count < 1:
            return jsonify({"message":"Error", "error":"No more credits found for this account. Please purchase more to continue."}), 402
        
        if not all([longitude, latitude, duration, radius, intensity]):
            return jsonify({"message":"Error", "error":"required fields missing from requested json. Please supply longitude, latitude, duration, radius, intensity"}), 400
        
        # get address for location
        address = get_location(longitude, latitude)
        if address == None:
            return jsonify({"message":"Error", "error":"There was an error in generating an address for the coordinates provided"}), 400
        # initialize day drift
        day_drift = DayDrift(location=address, duration=duration, radius=radius, intensity=intensity, text_temp=0.2, model=model)

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

        # decrease credit count and get credit count 
        credit_count -= 1
        db.users.update_one({"_id": ObjectId(user)}, {"$set": {"financial.creditCount": credit_count}})

        adventure = {
            "title": title,
            "adventureList": adventure_list,
            "totalCalories":total_calories, 
            "duration": duration, 
            "waterQuantity":water_quantity, 
            "safetyPrecautions":safety_precautions, 
            "location": location_parsed, 
            "creditCount":credit_count
        }

        adventure_copy = adventure.copy()
        adventure_copy['userId'] = user
        adventure_copy['timestamp'] = datetime.datetime.now()
        # insert into database
        new_drift = db.drifts.insert_one(adventure_copy)
        drift_id = new_drift.inserted_id

        # add resource to response 
        drift_string = str(drift_id)
        adventure['driftId'] = drift_string
        response = {
            "message": "Success",
            "adventure":adventure 
        }

        return jsonify(response), 200

    except Exception as e:
        current_app.logger.error(f"Error during drifts retrieval: {e}")
        return jsonify({"message": "Error", "error": "An unexpected server error occurred."}), 500


@drifts_bp.route('/drifts/save', methods=["POST"])
@jwt_required()
def save_drift():
    try:
        # get current user and db 
        db = current_app.db 
        user = get_jwt_identity()

        # get id to save
        data = request.get_json()
        drift_id = data.get("driftId", None)

        # check if id is provided 
        if not drift_id:
            return jsonify({"message":"error", "error":"You must provide the drift id to save item."}), 400

        # check if drift exists:
        find_drift = db.drifts.find_one({"_id":ObjectId(drift_id)})
        if not find_drift:
            return jsonify({"message":"Error", "error":"Drift id does not exist in the database"}), 400

        # check if the drift is already saved for the user
        user_data = db.users.find_one({"_id": ObjectId(user)})
        if drift_id in user_data.get("savedDrifts", []):
            return jsonify({"message": "Error", "error": "Drift is already saved."}), 400

        # if not already saved, then save it
        insert_saved = db.users.update_one({"_id":ObjectId(user)},
                             {"$push":{"savedDrifts":drift_id}}
                              )
        response = {
            "message": "Success",
            "savedResource": drift_id
        }
        return jsonify(response), 200

    except Exception as e:
        current_app.logger.error(f'Error during saving drift: {e}')
        return jsonify({"message":"Error", "error":"An unexpected server error occurred."}), 500

    
@drifts_bp.route('/drifts/unsave', methods=["POST"])
@jwt_required()
def unsave_drift():
    try:
        # get current user and db
        db = current_app.db 
        user = get_jwt_identity()

        # get id to unsave
        data = request.get_json()
        drift_id = data.get("driftId", None)

        # check if id is provided
        if not drift_id:
            return jsonify({"message": "error", "error": "You must provide the drift id to unsave item."}), 400

        # remove drift from user's saved drifts
        result = db.users.update_one(
            {"_id": ObjectId(user)}, 
            {"$pull": {"savedDrifts": drift_id}}
        )

        # if nothing was modified, it means the drift was not found in savedDrifts
        if result.modified_count == 0:
            return jsonify({"message": "error", "error": "The drift was not found in the user's saved drifts."}), 400

        response = {
            "message": "Success",
            "unsavedResource": drift_id
        }
        return jsonify(response), 200

    except Exception as e:
        current_app.logger.error(f'Error during unsaving drift: {e}')
        return jsonify({"message": "Error", "error": "An unexpected server error occurred."}), 500


@drifts_bp.route("/drifts", methods=["GET"])
@jwt_required()
def get_drifts():

    # get db instance
    db = current_app.db
    user = get_jwt_identity()
    try:
        # obtain query parameters
        data = request.args
        limit = int(data.get('limit', 10))
        sort = data.get('sort', 'recent')
        drift_id = data.get('driftId', None)
        
        # get the drifts whether by id or by sorting and filter
        if drift_id:
            try:
                drift = db.drifts.find_one({"_id": ObjectId(drift_id), "userId": user})
                if not drift:
                    return jsonify({"message": "Error", "error": "There is no drift with the following id"}), 400
                drift["_id"] = str(drift["_id"])
                return jsonify({"message": "Success", "drift": drift}), 200
            except errors.InvalidId:
                return jsonify({"message": "Error", "error": "Invalid drift ID format"}), 400
        else:
            if sort == 'recent':
                drifts = db.drifts.find({"userId":user}).sort("timestamp", pymongo.DESCENDING).limit(limit)
            else:
                drifts = db.drifts.find({"userId":user}).sort("timestamp", pymongo.ASCENDING).limit(limit)
            
            drifts = list(drifts)

            for drift in drifts:
                    drift["_id"] = str(drift["_id"])

            if not drifts:
                    return jsonify({"message":"Error", "error":"No drifts were found for this user"}), 400
            response = {
                        "message":"Success", 
                        "drifts":list(drifts)
                        }
            return jsonify(response), 200
    
    except Exception as e:
        return jsonify({"message":"Error", "error":f"An unexpected server error occurred{e}"}), 500