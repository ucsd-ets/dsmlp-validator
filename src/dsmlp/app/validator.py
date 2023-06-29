import json
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
        self.logger.debug("request=" + json.dumps(request, indent=2))
        namespace_name = request['request']['object']['metadata']['namespace']
        username = namespace_name
        self.logger.info(f"Validating request namespace={namespace_name}")

        namespace = self.kube.get_namespace(namespace_name)
        labels = namespace.labels
        if not 'k8s-sync' in labels:
            self.logger.info(f"Allowed namespace={namespace_name}")
            return self.admission_response(True, "Allowed")

        user = self.awsed.describe_user(username)
        user_uid = user.uid

        namespace = self.kube.get_namespace(username)
        spec = request['request']['object']['spec']
        try:
            uid = spec['securityContext']['runAsUser']
        except KeyError:
            uid = 0

        if user_uid != uid:
            self.logger.info(
                f"Denied request username={username} namespace={namespace_name} uid={user_uid} spec.securityContext.runAsUser={uid}")
            return self.admission_response(False, f"{username} is not allowed to use uid {uid}")

        container_uids = [self.get_run_as_user(container) for container in spec['containers']]
        print(container_uids)
        for uid in container_uids:
            if user_uid != uid:
                self.logger.info(
                    "Denied request username=user2 namespace=user2 uid=2 spec.containers[0].securityContext.runAsUser=3")
                return self.admission_response(False, f"{username} is not allowed to use uid {uid}")

        return self.admission_response(True, "Allowed")

    def admission_response(self, allowed, message):
        return {"response": {"allowed": allowed, "status": {"message": message}}}

    def get_run_as_user(self, container):
        try:
            return container['securityContext']['runAsUser']
        except KeyError:
            return 0
