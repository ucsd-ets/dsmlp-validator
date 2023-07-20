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
    uid: str
    namespace: str
    object: Object


@dataclass_json
@dataclass
class AdmissionReview:
    request: Request


class UidValidator:
    def evaluate(self, review: AdmissionReview):
        pass


class ValidationFailure(Exception):
    # message: str

    def __init__(self, message: str) -> None:
        self.message = message
        super().__init__(self.message)


class Validator:
    def __init__(self, awsed: AwsedClient, kube: KubeClient, logger: Logger) -> None:
        self.awsed = awsed
        self.kube = kube
        self.logger = logger

    def validate_request(self, request_json):
        self.logger.debug("request=" + json.dumps(request_json, indent=2))
        review: AdmissionReview = AdmissionReview.from_dict(request_json)
        request: Request = review.request
        request_uid = request.uid
        namespace_name = review.request.namespace
        username = namespace_name
        self.logger.info(f"Validating request namespace={namespace_name}")

        try:
            namespace = self.kube.get_namespace(namespace_name)
        except UnsuccessfulRequest:
            return self.admission_response(
                request_uid, False, f"Denied request username={username} namespace={namespace_name}")

        labels = namespace.labels
        if not 'k8s-sync' in labels:
            self.logger.info(f"Allowed namespace={namespace_name}")
            return self.admission_response(request_uid, True, "Allowed")

        user = self.awsed.describe_user(username)
        user_uid = user.uid

        namespace = self.kube.get_namespace(username)
        spec = review.request.object.spec
        uid = spec.securityContext.runAsUser

        try:
            self.check_pod_security_context(user_uid, spec.securityContext)
        except ValidationFailure as ex:
            self.logger.info(
                f"Denied request username={username} namespace={namespace_name} uid={user_uid} spec.securityContext.runAsUser={uid}")
            return self.admission_response(request_uid, False, f"{ex.message}")

        try:
            self.check_security_contexts(user_uid, spec.containers)
        except ValidationFailure as ex:
            self.logger.info(
                "Denied request username=user2 namespace=user2 uid=2 spec.containers[0].securityContext.runAsUser=3")
            return self.admission_response(request_uid, False, f"{ex.message}")

        return self.admission_response(request_uid, True, "Allowed")

    def check_pod_security_context(self, authorized_uid: int, securityContext: PodSecurityContext):
        if authorized_uid != securityContext.runAsUser:
            raise ValidationFailure(f"invalid uid {securityContext.runAsUser}")

    def check_security_contexts(self, authorized_uid: int, containers: List[Container]):
        container_uids = [container.securityContext.runAsUser for container in containers
                          if container.securityContext is not None and container.securityContext.runAsUser is not None]

        for container_uid in container_uids:
            if authorized_uid != container_uid:
                raise ValidationFailure(f"invalid uid {container_uid}")

        return True

    def admission_response(self, uid, allowed, message):
        return {
            "apiVersion": "admission.k8s.io/v1",
            "kind": "AdmissionReview",
            "response": {
                "uid": uid,
                "allowed": allowed,
                "status": {
                    "message": message
                }
            }
        }
