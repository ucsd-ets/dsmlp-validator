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
from dsmlp.app.types import *


class IDValidator(ComponentValidator):

    def __init__(self, awsed: AwsedClient, logger: Logger) -> None:
        self.awsed = awsed
        self.logger = logger

    def validate_pod(self, request: Request):
        """
        Validate pods for namespaces with the 'k8s-sync' label
        """
        username = request.namespace
#        namespace = self.kube.get_namespace(request.namespace)

#        if 'k8s-sync' in namespace.labels:
        user = self.awsed.describe_user(username)
        if not user:
            raise ValidationFailure(
                f"namespace: no AWSEd user found with username {username}")
        allowed_uid = user.uid
        allowed_courses = user.enrollments

        team_response = self.awsed.list_user_teams(username)
        allowed_gids = [team.gid for team in team_response.teams]
        allowed_gids.append(0)
        allowed_gids.append(100)

        metadata = request.object.metadata
        spec = request.object.spec

        if metadata is not None and metadata.labels is not None:
            self.validate_course_enrollment(allowed_courses, metadata.labels)

        self.validate_pod_security_context(
            allowed_uid, allowed_gids, spec.securityContext)
        self.validate_containers(allowed_uid, allowed_gids, spec)

    def validate_course_enrollment(self, allowed_courses: List[str], labels: Dict[str, str]):
        if not 'dsmlp/course' in labels:
            return
        if not labels['dsmlp/course'] in allowed_courses:
            raise ValidationFailure(
                f"metadata.labels: dsmlp/course must be in range {allowed_courses}")

    def validate_pod_security_context(
            self,
            authorized_uid: int,
            allowed_teams: List[int],
            securityContext: PodSecurityContext):

        if securityContext is None:
            return

        if securityContext.runAsUser is not None and authorized_uid != securityContext.runAsUser:
            raise ValidationFailure(
                f"spec.securityContext: uid must be in range [{authorized_uid}]")

        if securityContext.runAsGroup is not None and securityContext.runAsGroup not in allowed_teams:
            raise ValidationFailure(
                f"spec.securityContext: gid must be in range {allowed_teams}")

        if securityContext.fsGroup is not None and securityContext.fsGroup not in allowed_teams:
            raise ValidationFailure(
                f"spec.securityContext: gid must be in range {allowed_teams}")

        if securityContext.supplementalGroups is not None:
            for sgroup in securityContext.supplementalGroups:
                if not sgroup in allowed_teams:
                    raise ValidationFailure(
                        f"spec.securityContext: gid must be in range {allowed_teams}")

    def validate_containers(
            self,
            authorized_uid: int,
            allowed_teams: List[int],
            spec: PodSpec
    ):
        """
        Validate the security context of containers and initContainers
        """
        self.validate_security_contexts(
            authorized_uid, allowed_teams, spec.containers, "containers")
        self.validate_security_contexts(
            authorized_uid, allowed_teams, spec.initContainers, "initContainers")

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

            self.validate_security_context(
                authorized_uid, allowed_teams, securityContext, f"{context}[{i}]")

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
