from dsmlp.app import factory
from flask import Flask, request


def main():
    admission_controller = Flask(__name__)

    @admission_controller.route('/validate', methods=['POST'])
    def deployment_webhook():
        v = Validator()
        return v.validate_request(request.get_json())


if __name__ == '__main__':
    admission_controller = Flask(__name__)
    # admission_controller.run(host='0.0.0.0', port=443, ssl_context=("/server.crt", "/server.key"))
    admission_controller.run(host='0.0.0.0', port=9998)
