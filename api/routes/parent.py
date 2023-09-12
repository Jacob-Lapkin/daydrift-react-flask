from flask import Blueprint
from .users.auth import auth_bp
from .drifts.drifts_blueprint import drifts_bp

parent_bp = Blueprint("parent_bp", __name__)

# Register the auth_bp blueprint
parent_bp.register_blueprint(auth_bp)
parent_bp.register_blueprint(drifts_bp)
