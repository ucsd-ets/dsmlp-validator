import logging
import os
from dsmlp.app import factory
from flask import Flask, request
from flask.logging import default_handler
from dsmlp.app.validator import Validator

from logging.config import dictConfig

from dsmlp.ext.logger import PythonLogger
# def main():
# admission_controller = Flask(__name__)

#     admission_controller = Flask(__name__)


# @admission_controller.route('/validate', methods=['POST'])
# def deployment_webhook():
#     v = Validator()
#     return v.validate_request(request.get_json())


# if __name__ == '__main__':
#     admission_controller = Flask(__name__)
#     # admission_controller.run(host='0.0.0.0', port=443, ssl_context=("/server.crt", "/server.key"))
#     admission_controller.run(host='0.0.0.0', port=8080)

def create_app(test_config=None):
    dictConfig({
        'version': 1,
        'formatters': {'default': {
            'format': '[%(asctime)s] %(levelname)s in %(module)s: %(message)s',
        }},
        'handlers': {'wsgi': {
            'class': 'logging.StreamHandler',
            'stream': 'ext://flask.logging.wsgi_errors_stream',
            'formatter': 'default'
        }},
        'root': {
            'level': 'INFO',
            'handlers': ['wsgi']
        }
    })
    app = Flask(__name__)
    root = logging.getLogger()
    root.addHandler(default_handler)
    # root.addHandler(mail_handler)
    # for logger in (
    #     app.logger,
    #     logging.getLogger('dsmlp'),
    # ):
    #     logger.addHandler(default_handler)

    logging.getLogger('dsmlp').setLevel('DEBUG')
    logger = PythonLogger(None)
    logger.info("starting flask")
    validator = Validator(factory.awsed_client, factory.kube_client, logger)

    @app.route('/validate', methods=['POST'])
    def validate_request():
        return validator.validate_request(request.get_json())

    # create and configure the app
    # app = flask(__name__, instance_relative_config=True)
    app.config.from_mapping(
        SECRET_KEY=os.getenv('SECRET_KEY')
        # DATABASE=os.path.join(app.instance_path, 'flaskr.sqlite'),
    )

    if test_config is None:
        # load the instance config, if it exists, when not testing
        app.config.from_pyfile('config.py', silent=True)
    else:
        # load the test config if passed in
        app.config.from_mapping(test_config)

    # # ensure the instance folder exists
    # try:
    #     os.makedirs(app.instance_path)
    # except OSError:
    #     pass

    # a simple page that says hello
    # @app.route('/hello')
    # def hello():
    #     return 'Hello, World!'

    return app
