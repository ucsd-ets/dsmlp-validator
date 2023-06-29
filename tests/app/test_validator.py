import inspect
from operator import contains
from dsmlp.app.validator import Validator
from dsmlp.plugin.awsed import ListTeamsResponse, TeamJson, UserResponse
from dsmlp.plugin.kube import Namespace
from hamcrest import assert_that, contains_inanyorder, equal_to, has_item
from tests.fakes import FakeAwsedClient, FakeKubeClient, FakeLogger


class TestDirCreate:
    def setup_method(self) -> None:
        self.awsed_client = FakeAwsedClient()
        self.kube = FakeKubeClient()

        self.awsed_client.add_teams('user1', ListTeamsResponse(
            teams=[TeamJson(gid=1)]
        ))

        self.logger = FakeLogger()

    def test_pod_security_context(self):
        self.awsed_client.add_user('user1', UserResponse(uid=1))
        self.kube.add_namespace('user1', Namespace(name='user1', labels={'k8s-sync': 'set'}))

        response = self.when_validate(
            {
                "request": {
                    "namespace": "user1",
                    "object": {
                        "spec": {
                            "securityContext": {
                                "runAsUser": 1
                            },
                            "containers": []
                        },
                    }
                }
            })

        assert_that(response, equal_to({"response": {"allowed": True, "status": {"message": "Allowed"}}}))
        assert_that(self.logger.messages, has_item("INFO Validating request namespace=user1"))

    def test_security_context(self):
        self.awsed_client.add_user('user1', UserResponse(uid=1))
        self.kube.add_namespace('user1', Namespace(name='user1', labels={'k8s-sync': 'set'}))

        response = self.when_validate(
            {
                "request": {
                    "namespace": "user1",
                    "object": {
                        "spec": {
                            "securityContext": {
                                "runAsUser": 1
                            },
                            "containers": [
                                {
                                    "securityContext": {
                                        "runAsUser": 1
                                    }
                                }
                            ]
                        }
                    }
                }
            })

        assert_that(response, equal_to({"response": {"allowed": True, "status": {"message": "Allowed"}}}))
        assert_that(self.logger.messages, has_item("INFO Validating request namespace=user1"))

    def test_deny_security_context(self):
        self.awsed_client.add_user('user2', UserResponse(uid=2))
        self.kube.add_namespace('user2', Namespace(name='user2', labels={'k8s-sync': 'set'}))

        response = self.when_validate(
            {
                "request": {
                    "namespace": "user2",
                    "object": {
                        "spec": {"securityContext": {"runAsUser": 3}},
                    }
                }
            })

        assert_that(response, equal_to({"response": {"allowed": False, "status": {
                    "message": "user2 is not allowed to use uid 3"}}}))
        assert_that(self.logger.messages, has_item(
            "INFO Denied request username=user2 namespace=user2 uid=2 spec.securityContext.runAsUser=3"))

    def test_deny_pod_security_context(self):
        self.awsed_client.add_user('user2', UserResponse(uid=2))
        self.kube.add_namespace('user2', Namespace(name='user2', labels={'k8s-sync': 'set'}))

        response = self.when_validate(
            {
                "request": {
                    "namespace": "user2",
                    "object": {
                        "kind": "Pod",
                        "spec": {
                            "securityContext": {"runAsUser": 2},
                            "containers": [
                                {
                                    "securityContext": {"runAsUser": 3}
                                }
                            ]
                        }
                    }
                }
            })

        assert_that(response, equal_to({"response": {"allowed": False, "status": {
                    "message": "user2 is not allowed to use uid 3"}}}))
        assert_that(self.logger.messages, has_item(equal_to(
            "INFO Denied request username=user2 namespace=user2 uid=2 spec.containers[0].securityContext.runAsUser=3")))

    def test_unlabelled_namespace_can_use_any_uid(self):
        self.kube.add_namespace('kube-system', Namespace(name='kube-system', labels={}))

        response = self.when_validate(
            {
                "request": {
                    "namespace": "kube-system"
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
