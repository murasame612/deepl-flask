import os
import flask
from .route import apr



def create_app():
    app = flask.Flask(__name__)
    app.secret_key='avsdfasf-absdfasf-1234'
    #注册route函数中的蓝图
    app.register_blueprint(apr)
    return app