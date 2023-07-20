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
    """Each Container has a SecurityContext"""
    runAsUser: Optional[int] = None
    runAsGroup: Optional[int] = None


@dataclass_json
@dataclass
class Container:
    securityContext: Optional[SecurityContext] = None


@dataclass_json
@dataclass
class PodSecurityContext:
    """Each Pod has a SecurityContext"""
    runAsUser: Optional[int] = None
    runAsGroup: Optional[int] = None
    fsGroup: Optional[int] = None
    supplementalGroups: Optional[List[int]] = None


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
        try:
            self.logger.debug("request=" + json.dumps(request_json, indent=2))
            review: AdmissionReview = AdmissionReview.from_dict(request_json)
            request: Request = review.request
            request_uid = request.uid
            namespace_name = review.request.namespace
            username = namespace_name
            self.logger.info(f"Validating request namespace={namespace_name}")

            namespace = self.kube.get_namespace(namespace_name)

            labels = namespace.labels
            if not 'k8s-sync' in labels:
                self.logger.info(f"Allowed namespace={namespace_name}")
                return self.admission_response(request_uid, True, "Allowed")

            user = self.awsed.describe_user(username)
            user_uid = user.uid

            team_response = self.awsed.list_user_teams(username)
            allowed_teams = [team.gid for team in team_response.teams]
            allowed_teams.append(0)
            allowed_teams.append(100)

            namespace = self.kube.get_namespace(username)
            spec = review.request.object.spec

            if spec.securityContext is not None:
                self.check_pod_security_context(user_uid, allowed_teams, spec.securityContext)

            self.check_security_contexts(user_uid, allowed_teams, spec.containers)

            return self.admission_response(request_uid, True, "Allowed")
        except ValidationFailure as ex:
            self.logger.info(f"Denied request username={username} namespace={namespace_name} reason={ex.message}")
            return self.admission_response(request_uid, False, f"{ex.message}")
        except Exception as ex:
            self.logger.exception(ex)
            self.logger.info(f"Denied request username={username} namespace={namespace_name} reason=Error")
            return self.admission_response(request_uid, False, f"Error")

    def check_pod_security_context(
            self, authorized_uid: int, allowed_teams: List[int],
            securityContext: PodSecurityContext):
        if securityContext.runAsUser is not None and authorized_uid != securityContext.runAsUser:
            raise ValidationFailure(f"spec.securityContext: invalid uid {securityContext.runAsUser}")

        if securityContext.runAsGroup is not None and securityContext.runAsGroup not in allowed_teams:
            raise ValidationFailure(f"spec.securityContext: invalid gid {securityContext.runAsGroup}")

        if securityContext.fsGroup is not None and securityContext.fsGroup not in allowed_teams:
            raise ValidationFailure(f"spec.securityContext: invalid gid {securityContext.fsGroup}")

        if securityContext.supplementalGroups is not None:
            for sgroup in securityContext.supplementalGroups:
                if not sgroup in allowed_teams:
                    raise ValidationFailure(f"spec.securityContext: invalid gid {sgroup}")

    def check_security_contexts(self, authorized_uid: int,  allowed_teams: List[int], containers: List[Container]):
        for container in containers:
            securityContext = container.securityContext
            if securityContext is None:
                return

            if securityContext.runAsUser is not None and authorized_uid != securityContext.runAsUser:
                raise ValidationFailure(f"spec.containers.securityContext: invalid uid {securityContext.runAsUser}")

            if securityContext.runAsGroup is not None and securityContext.runAsGroup not in allowed_teams:
                raise ValidationFailure(f"spec.containers.securityContext: invalid gid {securityContext.runAsGroup}")

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
