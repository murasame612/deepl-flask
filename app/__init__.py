import os
import flask
from .route import apr

def create_app():
    app = flask.Flask(__name__)
    app.secret_key='avsdfasf-absdfasf-1234'
    app.config['UPLOAD_FOLDER'] = 'uploads/'
    app.config['ALLOWED_EXTENSIONS'] = {'png', 'jpg', 'jpeg', 'gif'}
    app.register_blueprint(apr)
    return app

if __name__ == '__main__':
    project_root = os.path.abspath(os.path.dirname(__file__))
    print(project_root)