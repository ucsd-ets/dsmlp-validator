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

        self.awsed_client.add_user('user10', UserResponse(uid=10))
        self.kube.add_namespace('user10', Namespace(name='user10', labels={'k8s-sync': 'set'}))
        self.awsed_client.add_teams('user10', ListTeamsResponse(
            teams=[TeamJson(gid=1000)]
        ))
        self.kube.add_namespace('kube-system', Namespace(name='kube-system', labels={}))

        self.logger = FakeLogger()

    def test_log_request_details(self):
        response = self.when_validate(
            {
                "request": {
                    "uid": "705ab4f5-6393-11e8-b7cc-42010a800002",
                    "namespace": "user10",
                    "userInfo": {
                        "username": "system:kube-system"
                    },
                    "object": {
                        "spec": {
                            "containers": [{}]
                        },
                    }
                }
            }
        )

        assert_that(self.logger.messages, has_item(
            "INFO Validating request username=system:kube-system namespace=user10"))

    def test_pod_security_context(self):
        self.awsed_client.add_user('user1', UserResponse(uid=1))
        self.kube.add_namespace('user1', Namespace(name='user1', labels={'k8s-sync': 'set'}))

        response = self.when_validate(
            {
                "request": {
                    "uid": "705ab4f5-6393-11e8-b7cc-42010a800002",
                    "userInfo": {
                        "username": "user1"
                    },
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
            }
        )

        assert_that(response, equal_to({
            "apiVersion": "admission.k8s.io/v1",
            "kind": "AdmissionReview",
            "response": {
                "uid": "705ab4f5-6393-11e8-b7cc-42010a800002",
                "allowed": True,
                "status": {
                    "message": "Allowed"
                }}}))

    def test_security_context(self):
        self.awsed_client.add_user('user1', UserResponse(uid=1))
        self.kube.add_namespace('user1', Namespace(name='user1', labels={'k8s-sync': 'set'}))

        response = self.when_validate(
            {
                "request": {
                    "uid": "705ab4f5-6393-11e8-b7cc-42010a800002",
                    "userInfo": {
                        "username": "user1"
                    },
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
            }
        )

        assert_that(response, equal_to({
            "apiVersion": "admission.k8s.io/v1",
            "kind": "AdmissionReview",
            "response": {
                "uid": "705ab4f5-6393-11e8-b7cc-42010a800002",
                "allowed": True,
                "status": {"message": "Allowed"}}}))

    def test_deny_security_context(self):
        """
        The user is launching a Pod,
        but the PodSecurityContext.runAsUser doesn't belong to them.
        Deny the request.
        """
        self.awsed_client.add_user('user2', UserResponse(uid=2))
        self.kube.add_namespace('user2', Namespace(name='user2', labels={'k8s-sync': 'set'}))

        response = self.when_validate(
            {
                "request": {
                    "uid": "705ab4f5-6393-11e8-b7cc-42010a800002",
                    "userInfo": {
                        "username": "user2"
                    },
                    "namespace": "user2",
                    "object": {
                        "spec": {
                            "securityContext": {"runAsUser": 3},
                            "containers": []
                        }
                    }
                }})

        assert_that(response, equal_to({
            "apiVersion": "admission.k8s.io/v1",
            "kind": "AdmissionReview",
            "response": {
                "uid": "705ab4f5-6393-11e8-b7cc-42010a800002",
                "allowed": False,
                "status": {
                    "message": "spec.securityContext: uid must be in range [2]"
                }}}))

    def test_failures_are_logged(self):
        self.awsed_client.add_user('user2', UserResponse(uid=2))
        self.kube.add_namespace('user2', Namespace(name='user2', labels={'k8s-sync': 'set'}))

        response = self.when_validate(
            {
                "request": {
                    "uid": "705ab4f5-6393-11e8-b7cc-42010a800002",
                    "userInfo": {
                        "username": "user2"
                    },
                    "namespace": "user2",
                    "object": {
                        "spec": {
                            "containers": [],
                            "securityContext": {"runAsUser": 3}},
                    }}})

        assert_that(self.logger.messages, has_item(
            f"INFO Denied request username=user2 namespace=user2 reason={response['response']['status']['message']}"))

    def test_deny_unknown_user(self):
        response = self.when_validate(
            {
                "request": {
                    "uid": "705ab4f5-6393-11e8-b7cc-42010a800002",
                    "userInfo": {
                        "username": "user2"
                    },
                    "namespace": "user2",
                    "object": {
                        "spec": {
                            "containers": [],
                            "securityContext": {"runAsUser": 3}},
                    }}})

        assert_that(response, equal_to({
            "apiVersion": "admission.k8s.io/v1",
            "kind": "AdmissionReview",
            "response": {
                "uid": "705ab4f5-6393-11e8-b7cc-42010a800002",
                "allowed": False,
                "status": {
                    "message": "Error"
                }}}))

    def test_deny_pod_security_context(self):
        self.awsed_client.add_user('user2', UserResponse(uid=2))
        self.kube.add_namespace('user2', Namespace(name='user2', labels={'k8s-sync': 'set'}))

        response = self.when_validate(
            {
                "request": {
                    "uid": "705ab4f5-6393-11e8-b7cc-42010a800002",
                    "userInfo": {
                        "username": "user2"
                    },
                    "namespace": "user2",
                    "object": {
                        "kind": "Pod",
                        "spec": {
                            "securityContext": {"runAsUser": 2},
                            "containers": [
                                {},
                                {
                                    "securityContext": {"runAsUser": 3}
                                }
                            ]
                        }
                    }
                }})

        assert_that(response, equal_to({
            "apiVersion": "admission.k8s.io/v1",
            "kind": "AdmissionReview",
            "response": {
                "uid": "705ab4f5-6393-11e8-b7cc-42010a800002",
                "allowed": False, "status": {
                    "message": "spec.containers[1].securityContext: uid must be in range [2]"
                }}}))

    def test_deny_init_container(self):
        """
        The user is launching a Pod with an Init Container,
        but the uid doesn't belong to them.
        Deny the request.
        """
        self.awsed_client.add_user('user2', UserResponse(uid=2))
        self.kube.add_namespace('user2', Namespace(name='user2', labels={'k8s-sync': 'set'}))

        response = self.when_validate(
            {
                "request": {
                    "uid": "705ab4f5-6393-11e8-b7cc-42010a800002",
                    "userInfo": {
                        "username": "user2"
                    },
                    "namespace": "user2",
                    "object": {
                        "kind": "Pod",
                        "spec": {
                            "containers": [{}],
                            "initContainers": [
                                {},
                                {
                                    "securityContext": {"runAsUser": 99}
                                }
                            ]
                        }
                    }
                }})

        assert_that(response, equal_to({
            "apiVersion": "admission.k8s.io/v1",
            "kind": "AdmissionReview",
            "response": {
                "uid": "705ab4f5-6393-11e8-b7cc-42010a800002",
                "allowed": False,
                "status": {
                    "message": "spec.initContainers[1].securityContext: uid must be in range [2]"
                }}}))

    def test_deny_pod_security_context2(self):
        """
        The Pod doesn't have any security contexts.
        It should be launched.
        """

        response = self.when_validate(
            {
                "request": {
                    "uid": "705ab4f5-6393-11e8-b7cc-42010a800002",
                    "userInfo": {
                        "username": "user10"
                    },
                    "namespace": "user10",
                    "object": {
                        "kind": "Pod",
                        "spec": {
                            "containers": [{}]
                        }
                    }
                }})

        assert_that(response, equal_to({
            "apiVersion": "admission.k8s.io/v1",
            "kind": "AdmissionReview",
            "response": {
                "uid": "705ab4f5-6393-11e8-b7cc-42010a800002",
                "allowed": True, "status": {
                    "message": "Allowed"
                }}}))

    # check podSecurityContext.runAsGroup
    def test_deny_team_gid(self):
        response = self.when_validate(
            {
                "request": {
                    "uid": "705ab4f5-6393-11e8-b7cc-42010a800002",
                    "userInfo": {
                        "username": "user10"
                    },
                    "namespace": "user10",
                    "object": {
                        "kind": "Pod",
                        "spec": {
                            "securityContext": {"runAsGroup": 2},
                            "containers": [{}]
                        }
                    }
                }}
        )

        assert_that(response, equal_to({
            "apiVersion": "admission.k8s.io/v1",
            "kind": "AdmissionReview",
            "response": {
                "uid": "705ab4f5-6393-11e8-b7cc-42010a800002",
                "allowed": False, "status": {
                    "message": "spec.securityContext: gid must be in range [1000, 0, 100]"
                }}}))

    # check podSecurityContext.fsGroup
    def test_deny_pod_fsGroup(self):
        response = self.when_validate(
            {
                "request": {
                    "uid": "705ab4f5-6393-11e8-b7cc-42010a800002",
                    "userInfo": {
                        "username": "user10"
                    },
                    "namespace": "user10",
                    "object": {
                        "kind": "Pod",
                        "spec": {
                            "securityContext": {"fsGroup": 2},
                            "containers": [{}]
                        }
                    }
                }}
        )

        assert_that(response, equal_to({
            "apiVersion": "admission.k8s.io/v1",
            "kind": "AdmissionReview",
            "response": {
                "uid": "705ab4f5-6393-11e8-b7cc-42010a800002",
                "allowed": False, "status": {
                    "message": "spec.securityContext: gid must be in range [1000, 0, 100]"
                }}}))

    # check podSecurityContext.supplementalGroups
    def test_deny_pod_supplemental_groups(self):
        response = self.when_validate(
            {
                "request": {
                    "uid": "705ab4f5-6393-11e8-b7cc-42010a800002",
                    "userInfo": {
                        "username": "user10"
                    },
                    "namespace": "user10",
                    "object": {
                        "kind": "Pod",
                        "spec": {
                            "securityContext": {"supplementalGroups": [2]},
                            "containers": [{}]
                        }
                    }
                }}
        )

        assert_that(response, equal_to({
            "apiVersion": "admission.k8s.io/v1",
            "kind": "AdmissionReview",
            "response": {
                "uid": "705ab4f5-6393-11e8-b7cc-42010a800002",
                "allowed": False, "status": {
                    "message": "spec.securityContext: gid must be in range [1000, 0, 100]"
                }}}))

    # check container.securityContext.runAsGroup
    def test_deny_container_run_as_group(self):
        response = self.when_validate(
            {
                "request": {
                    "uid": "705ab4f5-6393-11e8-b7cc-42010a800002",
                    "userInfo": {
                        "username": "user10"
                    },
                    "namespace": "user10",
                    "object": {
                        "kind": "Pod",
                        "spec": {
                            "containers": [
                                {
                                    "securityContext": {"runAsGroup": 2}
                                }
                            ]
                        }
                    }
                }}
        )

        assert_that(response, equal_to({
            "apiVersion": "admission.k8s.io/v1",
            "kind": "AdmissionReview",
            "response": {
                "uid": "705ab4f5-6393-11e8-b7cc-42010a800002",
                "allowed": False, "status": {
                    "message": "spec.containers[0].securityContext: gid must be in range [1000, 0, 100]"
                }}}))

    def test_allow_gid_0_and_100a(self):
        response = self.when_validate(
            {
                "request": {
                    "uid": "705ab4f5-6393-11e8-b7cc-42010a800002",
                    "userInfo": {
                        "username": "user10"
                    },
                    "namespace": "user10",
                    "object": {
                        "kind": "Pod",
                        "spec": {
                            "securityContext": {"runAsGroup": 0},
                            "containers": [
                                {
                                    "securityContext": {"runAsGroup": 100}
                                }
                            ]
                        }
                    }
                }
            }
        )

        assert_that(response, equal_to({
            "apiVersion": "admission.k8s.io/v1",
            "kind": "AdmissionReview",
            "response": {
                "uid": "705ab4f5-6393-11e8-b7cc-42010a800002",
                "allowed": True, "status": {
                    "message": "Allowed"
                }}}))

    def test_unlabelled_namespace_can_use_any_uid(self):
        self.kube.add_namespace('kube-system', Namespace(name='kube-system', labels={}))

        response = self.when_validate(
            {
                "request": {
                    "uid": "705ab4f5-6393-11e8-b7cc-42010a800002",
                    "userInfo": {
                        "username": "user10"
                    },
                    "namespace": "kube-system",
                    "object": {
                        "spec": {
                            "containers": [{}]
                        }
                    }
                }
            }
        )

        assert_that(response, equal_to({
            "apiVersion": "admission.k8s.io/v1",
            "kind": "AdmissionReview",
            "response": {
                    "uid": "705ab4f5-6393-11e8-b7cc-42010a800002",
                    "allowed": True,
                    "status": {
                        "message": "Allowed"
                    }}}))
        assert_that(self.logger.messages, has_item(
            "INFO Allowed namespace=kube-system"))

    def when_validate(self, json):
        validator = Validator(self.awsed_client, self.kube, self.logger)
        response = validator.validate_request(json)

        return response
