import inspect
from operator import contains
from dsmlp.app.validator import Validator
from dsmlp.plugin.awsed import ListTeamsResponse, TeamJson, UserResponse
from dsmlp.plugin.kube import Namespace
from hamcrest import assert_that, contains_inanyorder, equal_to, has_item
from dsmlp.ext.console import LoggingConsole
# from dsmlp.plugin.awsed import CourseJson
from tests.fakes import FakeAwsedClient, FakeKubeClient, FakeLogger


class TestDirCreate:
    def setup_method(self) -> None:
        self.awsed_client = FakeAwsedClient()
        self.kube = FakeKubeClient()
        self.console = LoggingConsole()

        self.awsed_client.add_user('user1', UserResponse(uid=1))
        self.awsed_client.add_user('user2', UserResponse(uid=2))

        self.awsed_client.add_teams('user1', ListTeamsResponse(
            teams=[TeamJson(gid=1)]
        ))

        self.kube.add_namespace('user1', Namespace(name='user1', labels={'k8s-sync': 'set'}))
        self.kube.add_namespace('user2', Namespace(name='user2', labels={'k8s-sync': 'set'}))
        self.kube.add_namespace('kube-system', Namespace(name='kube-system', labels={}))
        self.logger = FakeLogger()
        # self.kube.add_namespace('user1', Namespace(name='user1', labels={'k8s-sync': 'set'}))

    def test_user_allowed_to_run_pod_in_their_namespace(self):
        response = self.when_validate(
            {
                "request": {
                    # "userInfo": {"username": "user1"},
                    "object": {
                        "kind": "Pod",
                        "metadata": {"namespace": "user1"},
                        "spec": {
                            "securityContext": {
                                "runAsUser": 1
                            }
                        },
                    }
                }
            })

        assert_that(response, equal_to({"response": {"allowed": True, "status": {"message": "Allowed"}}}))
        assert_that(self.logger.messages, contains_inanyorder("INFO Validating request namespace=user1"))

    def test_user_not_allowed_to_run_pod_with_different_uid(self):
        response = self.when_validate(
            {
                "request": {
                    # "userInfo": {"username": "user1"},
                    "object": {
                        "kind": "Pod",
                        "metadata": {"namespace": "user2"},
                        "spec": {"securityContext": {"runAsUser": 3}},
                    }
                }
            })

        assert_that(response, equal_to({"response": {"allowed": False, "status": {
                    "message": "user2 is not allowed to use uid 3"}}}))
        assert_that(self.logger.messages, has_item(
            "INFO Denied request username=user2 namespace=user2 uid=2 spec.securityContext.runAsUser=3"))

    def test_system_can_use_any_uid(self):
        response = self.when_validate(
            {
                "request": {
                    # "userInfo": {"username": "system:serviceaccount:jupyterhub:default"},
                    "object": {
                        "kind": "Pod",
                        "metadata": {"namespace": "kube-system"},
                        "spec": {"securityContext": {"runAsUser": 2}},
                    }
                }
            })

        assert_that(response, equal_to({"response": {"allowed": True, "status": {
                    "message": "Allowed"}}}))
        assert_that(self.logger.messages, has_item(
            "INFO Allowed namespace=kube-system"))

    def when_validate(self, json):
        validator = Validator(self.awsed_client, self.kube, self.logger)
        response = validator.validate_request(json)

        return response
