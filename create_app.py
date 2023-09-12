from flask import Flask, jsonify
from flask_jwt_extended import JWTManager
from flask_cors import CORS
from config.configuration import Development, Production
from api.routes.parent import parent_bp
from api.models.models import db

cors = CORS()
jwt = JWTManager()


def create_app(config_mode='development'):

    # setting app 
    app = Flask(__name__)

    # choosing dev or prod
    if config_mode == 'development':
        app.config.from_object(Development)
    elif config_mode == 'production':
        app.config.from_object(Production)
    
    # setting cors
    cors.init_app(app)


    version = app.config['VERSION']
    app.register_blueprint(parent_bp, url_prefix=f'/api/{version}')

    # jwt manager
    jwt.init_app(app)

    # init database
    app.db = db

    @app.route('/home', methods=['GET'])
    def home():
        return jsonify({'response':"welcome to the home"}), 200

    return app