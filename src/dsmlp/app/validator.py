import string
from dsmlp.plugin.awsed import AwsedClient
from dsmlp.plugin.console import Console
from dsmlp.plugin.course import ConfigProvider
from dsmlp.plugin.kube import KubeClient, NotFound
import jsonify

from dsmlp.plugin.logger import Logger


class Validator:
    def __init__(self, awsed: AwsedClient, kube: KubeClient, logger: Logger) -> None:
        self.awsed = awsed
        self.kube = kube
        self.logger = logger

    def validate_request(self, request):
        username = request['request']['object']['metadata']['namespace']
        self.logger.info(f"Validating request namespace={username}")

        namespace = self.kube.get_namespace(username)
        labels = namespace.labels
        if not 'k8s-sync' in labels:
            self.logger.info(f"Allowed namespace={username}")
            return self.admission_response(True, "Allowed")

        user = self.awsed.describe_user(username)
        # username = request['request']['userInfo']['username']
        if username.startswith('system:'):
            return self.admission_response(True, "Allowed")
        namespace = self.kube.get_namespace('user1')
        spec = request['request']['object']['spec']
        uid = spec['securityContext']['runAsUser']
        if user.uid != uid:
            self.logger.info(
                f"Denied request username={username} namespace={username} uid={user.uid} spec.securityContext.runAsUser={uid}")
            return self.admission_response(False, f"{username} is not allowed to use uid {uid}")
        # if request["request"]["object"]["metadata"]["labels"].get("allow"):
        #     return self.admission_response(True, "Allow label exists")
        return self.admission_response(True, "Allowed")

    def admission_response(self, allowed, message):
        return {"response": {"allowed": allowed, "status": {"message": message}}}
