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
class PodSpec:
    containers: List[Container]
    initContainers: Optional[List[Container]] = None
    securityContext: Optional[PodSecurityContext] = None


@dataclass_json
@dataclass
class Object:
    spec: PodSpec


@dataclass_json
@dataclass
class UserInfo:
    username: str


@dataclass_json
@dataclass
class Request:
    uid: str
    namespace: str
    object: Object
    userInfo: UserInfo


@dataclass_json
@dataclass
class AdmissionReview:
    request: Request


class ValidationFailure(Exception):
    def __init__(self, message: str) -> None:
        self.message = message
        super().__init__(self.message)


class Validator:
    def __init__(self, awsed: AwsedClient, logger: Logger) -> None:
        self.awsed = awsed
        self.logger = logger

    def validate_request(self, admission_review_json):
        self.logger.debug("request=" + json.dumps(admission_review_json, indent=2))
        review: AdmissionReview = AdmissionReview.from_dict(admission_review_json)

        try:
            return self.handle_request(review.request)
        except Exception as ex:
            self.logger.exception(ex)
            self.logger.info(
                f"Denied request username={review.request.userInfo.username} namespace={review.request.namespace} reason=Error uid={review.request.uid}")

            return self.admission_response(review.request.uid, False, f"Error")

    def handle_request(self, request: Request):
        self.logger.info(
            f"Validating request username={request.userInfo.username} namespace={request.namespace} uid={request.uid}")

        try:
            self.validate_pod(request)
        except ValidationFailure as ex:
            self.logger.info(
                f"Denied request username={request.userInfo.username} namespace={request.namespace} reason={ex.message} uid={request.uid}")

            return self.admission_response(request.uid, False, f"{ex.message}")

        self.logger.info(
            f"Allowed request username={request.userInfo.username} namespace={request.namespace} uid={request.uid}")
        return self.admission_response(request.uid, True, "Allowed")

    def validate_pod(self, request: Request):
        """
        Validate pods for namespaces with the 'k8s-sync' label
        """
        username = request.namespace
#        namespace = self.kube.get_namespace(request.namespace)

#        if 'k8s-sync' in namespace.labels:
        user = self.awsed.describe_user(username)
        allowed_uid = user.uid

        team_response = self.awsed.list_user_teams(username)
        allowed_gids = [team.gid for team in team_response.teams]
        allowed_gids.append(0)
        allowed_gids.append(100)

        spec = request.object.spec
        self.validate_pod_security_context(allowed_uid, allowed_gids, spec.securityContext)
        self.validate_containers(allowed_uid, allowed_gids, spec)

    def validate_pod_security_context(
            self,
            authorized_uid: int,
            allowed_teams: List[int],
            securityContext: PodSecurityContext):

        if securityContext is None:
            return

        if securityContext.runAsUser is not None and authorized_uid != securityContext.runAsUser:
            raise ValidationFailure(f"spec.securityContext: uid must be in range [{authorized_uid}]")

        if securityContext.runAsGroup is not None and securityContext.runAsGroup not in allowed_teams:
            raise ValidationFailure(f"spec.securityContext: gid must be in range {allowed_teams}")

        if securityContext.fsGroup is not None and securityContext.fsGroup not in allowed_teams:
            raise ValidationFailure(f"spec.securityContext: gid must be in range {allowed_teams}")

        if securityContext.supplementalGroups is not None:
            for sgroup in securityContext.supplementalGroups:
                if not sgroup in allowed_teams:
                    raise ValidationFailure(f"spec.securityContext: gid must be in range {allowed_teams}")

    def validate_containers(
            self,
            authorized_uid: int,
            allowed_teams: List[int],
            spec: PodSpec
    ):
        """
        Validate the security context of containers and initContainers
        """
        self.validate_security_contexts(authorized_uid, allowed_teams, spec.containers, "containers")
        self.validate_security_contexts(authorized_uid, allowed_teams, spec.initContainers, "initContainers")

    def validate_security_contexts(
            self, authorized_uid: int, allowed_teams: List[int],
            containers: List[Container],
            context: str):
        """
        Validate the security context of a container.
        """

        if containers is None:
            return

        for i, container in enumerate(containers):
            securityContext = container.securityContext
            if securityContext is None:
                continue

            self.validate_security_context(authorized_uid, allowed_teams, securityContext, f"{context}[{i}]")

    def validate_security_context(
            self,
            authorized_uid: int,
            allowed_teams: List[int],
            securityContext: SecurityContext,
            context: str):

        if securityContext.runAsUser is not None and authorized_uid != securityContext.runAsUser:
            raise ValidationFailure(
                f"spec.{context}.securityContext: uid must be in range [{authorized_uid}]")

        if securityContext.runAsGroup is not None and securityContext.runAsGroup not in allowed_teams:
            raise ValidationFailure(
                f"spec.{context}.securityContext: gid must be in range {allowed_teams}")

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
