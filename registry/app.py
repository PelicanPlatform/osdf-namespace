import os
import pathlib

import flask
from flask import Flask
from flask_migrate import Migrate
from flask_smorest import Api

from registry.models import db, Namespace, NamespaceSchema
from registry.views import namespace_blp
from registry.logger import configure_logging

import sqlalchemy

THIS_FILE = pathlib.Path(__file__)
INSTANCE_DIR = THIS_FILE.parent.parent / "instance"
LOG_DIR = INSTANCE_DIR / "log"

def load_config(app: flask.Flask) -> None:
    app.config.from_pyfile('config.py')
    app.config['API_TITLE'] = 'Namespace Management API'
    app.config['API_VERSION'] = 'v1'
    app.config['OPENAPI_VERSION'] = '3.0.2'
    app.config['OPENAPI_URL_PREFIX'] = '/'
    app.config['OPENAPI_SWAGGER_UI_PATH'] = '/swagger-ui'
    app.config["OPENAPI_SWAGGER_UI_URL"] = "https://cdn.jsdelivr.net/npm/swagger-ui-dist/"
    app.config['OPENAPI_SWAGGER_UI_CONFIG'] = {'deepLinking': True, 'supportedSubmitMethods': ['get', 'post', 'delete']}


def create_db(app: flask.Flask) -> None:

    app.logger.info("Creating DB")

    # Setup database configurations and create directories if they don't exist

    os.makedirs(INSTANCE_DIR / app.config['DB_DIR'], exist_ok=True)
    db_path = os.path.join(INSTANCE_DIR / app.config['DB_DIR'], 'app.db')
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + db_path
    # Initialize SQLAlchemy and Migrate
    db.app = app
    db.init_app(app)

    migrate = Migrate(app, db)
   
    try:
        db.create_all()
    except (sqlalchemy.exc.InterfaceError, sqlalchemy.exc.DatabaseError) as error:
        app.logger.debug(f"Could not connect to the SQLite database: {error}")
    app.logger.info("DB Created")
    
def create_app() -> flask.Flask:

    app = Flask(__name__)

    load_config(app)
    configure_logging(LOG_DIR / "registry.log")
    
    with app.app_context():
        create_db(app)
        api = Api(app)
        api.register_blueprint(namespace_blp)

    return app

# Run the application
if __name__ == "__main__":
    app = create_app()
    app.run(debug=True, host="0.0.0.0", port=5007)