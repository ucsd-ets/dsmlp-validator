import inspect
from operator import contains
from dsmlp.app.types import *
from dsmlp.app.id_validator import IDValidator
from dsmlp.app.validator import Validator
from dsmlp.plugin.awsed import ListTeamsResponse, TeamJson, UserResponse, UserQuotaResponse, Quota
from dsmlp.plugin.kube import Namespace
from hamcrest import assert_that, contains_inanyorder, equal_to, has_item
from tests.app.utils import gen_request, try_val_with_component
from tests.fakes import FakeAwsedClient, FakeLogger, FakeKubeClient


class TestIDValidator:
    def setup_method(self) -> None:
        self.logger = FakeLogger()
        self.awsed_client = FakeAwsedClient()
        self.kube_client = FakeKubeClient()

        self.awsed_client.add_user(
            'user10', UserResponse(uid=10, enrollments=[]))
        self.awsed_client.add_teams('user10', ListTeamsResponse(
            teams=[TeamJson(gid=1000)]
        ))

        self.kube_client.add_namespace('user10', Namespace(
            name='user10', labels={'k8s-sync': 'true'}, gpu_quota=10))

    def test_course_enrollment(self):
        self.awsed_client.add_user(
            'user1', UserResponse(uid=1, enrollments=["course1"]))
        self.kube_client.add_namespace('user1', Namespace(
            name='user1', labels={'k8s-sync': 'true'}, gpu_quota=10))

        self.try_validate(gen_request(
            course="course1", username="user1", run_as_user=1, has_container=False), True, "Allowed")

    def test_pod_security_context(self):
        self.awsed_client.add_user(
            'user1', UserResponse(uid=1, enrollments=[]))
        self.kube_client.add_namespace('user1', Namespace(
            name='user1', labels={'k8s-sync': 'true'}, gpu_quota=10))

        self.try_validate(gen_request(
            username="user1", run_as_user=1, has_container=False), True, "Allowed")

    def test_security_context(self):
        self.awsed_client.add_user(
            'user1', UserResponse(uid=1, enrollments=[]))
        self.kube_client.add_namespace('user1', Namespace(
            name='user1', labels={'k8s-sync': 'true'}, gpu_quota=10))

        self.try_validate(gen_request(
            username="user1", run_as_user=1, has_container=True), True, "Allowed")

    def test_deny_security_context(self):
        """
        The user is launching a Pod,
        but the PodSecurityContext.runAsUser doesn't belong to them.
        Deny the request.
        """
        self.awsed_client.add_user(
            'user2', UserResponse(uid=2, enrollments=[]))

        self.try_validate(gen_request(
            username="user2", run_as_user=3, has_container=False), False, "spec.securityContext: uid must be in range [2]")

    def test_deny_unknown_user(self):

        self.try_validate(gen_request(
            username="user2", run_as_user=2, has_container=False), False, "namespace: no AWSEd user found with username user2")

    def test_deny_course_enrollment(self):
        """
        The user is launching a Pod,
        but they are not enrolled in the course in the label "dsmlp/course".
        Deny the request.
        """
        self.awsed_client.add_user(
            'user2', UserResponse(uid=2, enrollments=[]))

        self.try_validate(gen_request(
            course="course1", username="user2", run_as_user=2, has_container=False), False, "metadata.labels: dsmlp/course must be in range []")

    def test_deny_pod_security_context(self):
        self.awsed_client.add_user(
            'user2', UserResponse(uid=2, enrollments=[]))

        self.try_validate(gen_request(
            username="user2", run_as_user=2, container_override=[Container(), Container(securityContext=SecurityContext(runAsUser=3))]), False, "spec.containers[1].securityContext: uid must be in range [2]")

    def test_deny_init_container(self):
        """
        The user is launching a Pod with an Init Container,
        but the uid doesn't belong to them.
        Deny the request.
        """
        self.awsed_client.add_user(
            'user2', UserResponse(uid=2, enrollments=[]))

        self.try_validate(gen_request(
            username="user2", run_as_user=2, container_override=[Container()], init_containers=[Container(), Container(securityContext=SecurityContext(runAsUser=99))]), False, "spec.initContainers[1].securityContext: uid must be in range [2]")

    def test_deny_pod_security_context2(self):
        """
        The Pod doesn't have any security contexts.
        It should be launched.
        """

        self.try_validate(gen_request(
            username="user10", container_override=[Container()]), True, "Allowed")

    # check podSecurityContext.runAsGroup
    def test_deny_team_gid(self):

        self.try_validate(gen_request(
            username="user10", run_as_group=2, container_override=[Container()]), False, "spec.securityContext: gid must be in range [1000, 0, 100]")

    # check podSecurityContext.fsGroup
    def test_deny_pod_fsGroup(self):

        self.try_validate(gen_request(
            username="user10", fs_group=2, container_override=[Container()]), False, "spec.securityContext: gid must be in range [1000, 0, 100]")

    # check podSecurityContext.supplementalGroups
    def test_deny_pod_supplemental_groups(self):

        self.try_validate(gen_request(
            username="user10", supplemental_groups=[2], container_override=[Container()]), False, "spec.securityContext: gid must be in range [1000, 0, 100]")

    # check container.securityContext.runAsGroup
    def test_deny_container_run_as_group(self):

        self.try_validate(gen_request(
            username="user10", container_override=[Container(securityContext=SecurityContext(runAsGroup=2))]), False, "spec.containers[0].securityContext: gid must be in range [1000, 0, 100]")

    def test_allow_gid_0_and_100a(self):

        self.try_validate(gen_request(
            username="user10", run_as_group=0, container_override=[Container(securityContext=SecurityContext(runAsGroup=100))]), True, "Allowed")

    def try_validate(self, json, expected: bool, message: str = None):
        try_val_with_component(IDValidator(
            self.awsed_client, self.logger), json, expected, message)
