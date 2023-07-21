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


# class UidValidator:
#     def evaluate(self, review: AdmissionReview):
#         pass


class ValidationFailure(Exception):
    def __init__(self, message: str) -> None:
        self.message = message
        super().__init__(self.message)


class Validator:
    def __init__(self, awsed: AwsedClient, kube: KubeClient, logger: Logger) -> None:
        self.awsed = awsed
        self.kube = kube
        self.logger = logger

    def validate_request(self, admission_review_json):
        self.logger.debug("request=" + json.dumps(admission_review_json, indent=2))
        review: AdmissionReview = AdmissionReview.from_dict(admission_review_json)
        request: Request = review.request
        request_uid = request.uid
        namespace_name = review.request.namespace
        username = namespace_name
        self.logger.info(
            f"Validating request username={request.userInfo.username} namespace={namespace_name} uid={request_uid}")

        try:
            self.validate_pod(review.request)
        except ValidationFailure as ex:
            self.logger.info(f"Denied request username={username} namespace={namespace_name} reason={ex.message}")
            return self.admission_response(request_uid, False, f"{ex.message}")
        except Exception as ex:
            self.logger.exception(ex)
            self.logger.info(f"Denied request username={username} namespace={namespace_name} reason=Error")
            return self.admission_response(request_uid, False, f"Error")

        self.logger.info(
            f"Allowed request username={request.userInfo.username} namespace={namespace_name} uid={request_uid}")
        return self.admission_response(request_uid, True, "Allowed")

    def validate_pod(self, request: Request):
        username = request.namespace
        namespace = self.kube.get_namespace(request.namespace)

        if 'k8s-sync' in namespace.labels:
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
