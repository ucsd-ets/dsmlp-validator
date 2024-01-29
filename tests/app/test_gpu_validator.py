import inspect
from operator import contains
from dsmlp.app.validator import Validator
from dsmlp.plugin.awsed import ListTeamsResponse, TeamJson, UserResponse
from dsmlp.plugin.kube import Namespace
from hamcrest import assert_that, contains_inanyorder, equal_to, has_item
from tests.fakes import FakeAwsedClient, FakeLogger, FakeKubeClient
from dsmlp.ext.kube import DefaultKubeClient

class TestValidator:
    def setup_method(self) -> None:
        self.logger = FakeLogger()
        self.awsed_client = FakeAwsedClient()
        self.kube_client = FakeKubeClient()

        self.awsed_client.add_user('user10', UserResponse(uid=10))
        self.awsed_client.add_teams('user10', ListTeamsResponse(
            teams=[TeamJson(gid=1000)]
        ))
        
        self.kube_client.add_namespace('user10', Namespace(name='user10', labels={'k8s-sync': 'true'}, gpu_quota=10))
        self.kube_client.set_existing_gpus('user10', 0)

    def test_no_gpus_requested(self):
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
                }}
        )

        assert_that(response, equal_to({
            "apiVersion": "admission.k8s.io/v1",
            "kind": "AdmissionReview",
            "response": {
                "uid": "705ab4f5-6393-11e8-b7cc-42010a800002",
                "allowed": True, "status": {
                    "message": "Allowed"
                }}}))
        
    def test_quota_not_reached(self):
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
                            "containers": [{
                                "resources": {
                                    "requests": {
                                        "nvidia.com/gpu": 10
                                    }
                                }
                            }]
                        }
                    }
                }}
        )

        assert_that(response, equal_to({
            "apiVersion": "admission.k8s.io/v1",
            "kind": "AdmissionReview",
            "response": {
                "uid": "705ab4f5-6393-11e8-b7cc-42010a800002",
                "allowed": True, "status": {
                    "message": "Allowed"
                }}}))

    def test_quota_exceeded(self):
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
                            "containers": [{
                                "resources": {
                                    "requests": {
                                        "nvidia.com/gpu": 11
                                    }
                                }
                            }]
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
                    "message": "GPU quota exceeded. Wanted 11 but with 0 already in use, the quota of 10 would be exceeded."
                }}}))
    
    def test_sum_exceeded(self):
        self.kube_client.set_existing_gpus('user10', 5)
        
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
                            "containers": [{
                                "resources": {
                                    "requests": {
                                        "nvidia.com/gpu": 6
                                    }
                                }
                            }]
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
                    "message": "GPU quota exceeded. Wanted 6 but with 5 already in use, the quota of 10 would be exceeded."
                }}}))
    
    def test_low_priority(self):
        self.kube_client.set_existing_gpus('user10', 5)
        
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
                            "containers": [{
                                "resources": {
                                    "requests": {
                                        "nvidia.com/gpu": 6
                                    }
                                }
                            }],
                            "priorityClassName": "low"
                        }
                    }
                }}
        )

        assert_that(response, equal_to({
            "apiVersion": "admission.k8s.io/v1",
            "kind": "AdmissionReview",
            "response": {
                "uid": "705ab4f5-6393-11e8-b7cc-42010a800002",
                "allowed": True, "status": {
                    "message": "Allowed"
                }}}))
    
    # Should respond to limit as well as request
    def test_limit_exceeded(self):
        self.kube_client.set_existing_gpus('user10', 5)
        
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
                            "containers": [{
                                "resources": {
                                    "limits": {
                                        "nvidia.com/gpu": 6
                                    }
                                }
                            }]
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
                    "message": "GPU quota exceeded. Wanted 6 but with 5 already in use, the quota of 10 would be exceeded."
                }}}))

    def when_validate(self, json):
        validator = Validator(self.awsed_client, self.kube_client, self.logger)
        response = validator.validate_request(json)

        return response
