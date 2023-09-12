from create_app import create_app
from dotenv import load_dotenv
import os

load_dotenv()

flask_env = os.getenv("FLASK_ENV")

app = create_app(flask_env)

debug = app.config['DEBUG']
host = app.config['HOST']
port = app.config['PORT']

if __name__ == "__main__":
    app.run(debug=debug, host=host, port=port)
