import logging
import os
from dsmlp.app import factory
from flask import Flask, request
from flask.logging import default_handler
from dsmlp.app.validator import Validator

from logging.config import dictConfig

from dsmlp.ext.logger import PythonLogger


def create_app(test_config=None):
    app = Flask(__name__)

    logging.getLogger('waitress').setLevel(logging.INFO)
    logging.getLogger('dsmlp').setLevel(logging.DEBUG)
    logger = PythonLogger(None)
    validator = Validator(factory.awsed_client, factory.kube_client, logger)

    @app.route('/validate', methods=['POST'])
    def validate_request():
        return validator.validate_request(request.get_json())

    @app.route('/healthz', methods=['GET'])
    def health():
        return 'OK'

    app.config.from_mapping(
        SECRET_KEY=os.getenv('SECRET_KEY')
    )

    if test_config is None:
        app.config.from_pyfile('config.py', silent=True)
    else:
        app.config.from_mapping(test_config)

    return app
