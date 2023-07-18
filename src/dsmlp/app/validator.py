from dataclasses import dataclass
import json
from typing import List, Optional

from dataclasses_json import dataclass_json
from dsmlp.plugin.awsed import AwsedClient, UnsuccessfulRequest
from dsmlp.plugin.console import Console
from dsmlp.plugin.course import ConfigProvider
from dsmlp.plugin.kube import KubeClient, NotFound
import jsonify

from dsmlp.plugin.logger import Logger


@dataclass_json
@dataclass
class SecurityContext:
    runAsUser: Optional[int] = None


@dataclass_json
@dataclass
class Container:
    securityContext: Optional[SecurityContext] = None


@dataclass_json
@dataclass
class PodSecurityContext:
    runAsUser: Optional[int] = None


@dataclass_json
@dataclass
class Spec:
    containers: List[Container]
    securityContext: Optional[PodSecurityContext] = None


@dataclass_json
@dataclass
class Object:
    spec: Spec


@dataclass_json
@dataclass
class Request:
    namespace: str


@dataclass_json
@dataclass
class AdmissionReview:
    request: Request
    object: Object


class UidValidator:
    def evaluate(self, review: AdmissionReview):
        pass


class Validator:
    def __init__(self, awsed: AwsedClient, kube: KubeClient, logger: Logger) -> None:
        self.awsed = awsed
        self.kube = kube
        self.logger = logger

    def validate_request(self, request):
        self.logger.debug("request=" + json.dumps(request, indent=2))
        review: AdmissionReview = AdmissionReview.from_dict(request)
        namespace_name = review.request.namespace
        username = namespace_name
        self.logger.info(f"Validating request namespace={namespace_name}")

        try:
            namespace = self.kube.get_namespace(namespace_name)
        except UnsuccessfulRequest:
            return self.admission_response(False, f"Denied request username={username} namespace={namespace_name}")

        labels = namespace.labels
        if not 'k8s-sync' in labels:
            self.logger.info(f"Allowed namespace={namespace_name}")
            return self.admission_response(True, "Allowed")

        user = self.awsed.describe_user(username)
        user_uid = user.uid

        namespace = self.kube.get_namespace(username)
        spec = review.object.spec
        uid = spec.securityContext.runAsUser

        if user_uid != uid:
            self.logger.info(
                f"Denied request username={username} namespace={namespace_name} uid={user_uid} spec.securityContext.runAsUser={uid}")
            return self.admission_response(False, f"{username} is not allowed to use uid {uid}")

        container_uids = [container.securityContext.runAsUser for container in spec.containers
                          if container.securityContext is not None and container.securityContext.runAsUser is not None]
        print(container_uids)
        for uid in container_uids:
            if user_uid != uid:
                self.logger.info(
                    "Denied request username=user2 namespace=user2 uid=2 spec.containers[0].securityContext.runAsUser=3")
                return self.admission_response(False, f"{username} is not allowed to use uid {uid}")

        return self.admission_response(True, "Allowed")

    def admission_response(self, allowed, message):
        return {"response": {"allowed": allowed, "status": {"message": message}}}
