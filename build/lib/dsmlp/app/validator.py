import string
from dsmlp.plugin.awsed import AwsedClient
from dsmlp.plugin.console import Console
from dsmlp.plugin.course import ConfigProvider
from dsmlp.plugin.kube import KubeClient, NotFound
import jsonify


class Validator:
    def __init__(self, awsed: AwsedClient, kube: KubeClient) -> None:
        self.awsed = awsed
        self.kube = kube

    def validate_request(self, request):
        user = self.awsed.describe_user('user1')
        username = request['request']['userInfo']['username']
        if username.startswith('system:'):
            return self.admission_response(True, "Allowed")
        namespace = self.kube.get_namespace('user1')
        spec = request['request']['object']['spec']
        uid = spec['securityContext']['runAsUser']
        if user.uid != uid:
            return self.admission_response(False, f"{username} is not allowed to use uid {uid}")
        # if request["request"]["object"]["metadata"]["labels"].get("allow"):
        #     return self.admission_response(True, "Allow label exists")
        return self.admission_response(True, "Allowed")

    def admission_response(self, allowed, message):
        return {"response": {"allowed": allowed, "status": {"message": message}}}
