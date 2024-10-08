import inspect
from operator import contains
from dsmlp.app.validator import Validator
from dsmlp.plugin.awsed import ListTeamsResponse, TeamJson, UserResponse
from dsmlp.plugin.kube import Namespace
from hamcrest import assert_that, contains_inanyorder, equal_to, has_item
from tests.fakes import FakeAwsedClient, FakeLogger, FakeKubeClient


class TestTGPTValidator:
    def setup_method(self) -> None:
        self.logger = FakeLogger()
        self.awsed_client = FakeAwsedClient()
        self.kube_client = FakeKubeClient()

        self.awsed_client.add_user(
            'user10', UserResponse(uid=30, enrollments=[]))
        self.awsed_client.add_teams('user10', ListTeamsResponse(
            teams=[TeamJson(gid=1000)]
        ))

        self.kube_client.add_namespace('user10', Namespace(
            name='user10', labels={'k8s-sync': 'true', 'tgpt-validator': 'enabled', 'permitted-uids': '30,3000'}, gpu_quota=10))

        self.awsed_client.add_user(
            'user100', UserResponse(uid=10, enrollments=[]))
        self.awsed_client.add_teams('user10', ListTeamsResponse(
            teams=[TeamJson(gid=1000)]
        ))

        self.kube_client.add_namespace('user100', Namespace(
            name='user100', labels={'k8s-sync': 'true', 'tgpt-validator': 'disabled', 'permitted-uids': '10'}, gpu_quota=10))

    def test_good_request(self):
        self.when_validate(
            {
                "request": {
                    "uid": "705ab4f5-6393-11e8-b7cc-42010a800002",
                    "namespace": "user10",
                    "userInfo": {
                        "username": "system:kube-system"
                    },
                    "object": {
                        "metadata": {
                            "labels": {}
                        },
                        "spec": {
                            "containers": [{}],
                            "securityContext": {"runAsUser": 30},
                        },
                    }
                }
            }
        )

        assert_that(self.logger.messages, has_item(
            f"INFO Allowed request username=system:kube-system namespace=user10 uid=705ab4f5-6393-11e8-b7cc-42010a800002"))

    def test_good_request_2(self):
        self.when_validate(
            {
                "request": {
                    "uid": "705ab4f5-6393-11e8-b7cc-42010a800002",
                    "namespace": "user10",
                    "userInfo": {
                        "username": "system:kube-system"
                    },
                    "object": {
                        "metadata": {
                            "labels": {}
                        },
                        "spec": {
                            "containers": [{}],
                            "securityContext": {"runAsUser": 3000},
                        },
                    }
                }
            }
        )

        assert_that(self.logger.messages, has_item(
            f"INFO Allowed request username=system:kube-system namespace=user10 uid=705ab4f5-6393-11e8-b7cc-42010a800002"))

    def test_bad_request(self):
        self.when_validate(
            {
                "request": {
                    "uid": "705ab4f5-6393-11e8-b7cc-42010a800002",
                    "namespace": "user10",
                    "userInfo": {
                        "username": "system:kube-system"
                    },
                    "object": {
                        "metadata": {
                            "labels": {}
                        },
                        "spec": {
                            "containers": [{}],
                            "securityContext": {"runAsUser": 300},
                        },
                    }
                }
            }
        )

        assert_that(self.logger.messages, has_item(
            f"INFO Denied request username=system:kube-system namespace=user10 reason=TritonGPT Validator: user with access to UIDs ['30', '3000'] attempted to run a pod as 300. Pod denied. uid=705ab4f5-6393-11e8-b7cc-42010a800002"))
        
    def test_good_request_not_enabled_permitted_on(self):
        self.when_validate(
            {
                "request": {
                    "uid": "705ab4f5-6393-11e8-b7cc-42010a800002",
                    "namespace": "user100",
                    "userInfo": {
                        "username": "system:kube-system"
                    },
                    "object": {
                        "metadata": {
                            "labels": {}
                        },
                        "spec": {
                            "containers": [{}],
                            "securityContext": {"runAsUser": 10},
                        },
                    }
                }
            }
        )

        assert_that(self.logger.messages, has_item(
            f"INFO Allowed request username=system:kube-system namespace=user100 uid=705ab4f5-6393-11e8-b7cc-42010a800002"))

        #assert_that(self.logger.messages, has_item(
            #"INFO Allowed request username=user10 namespace=user10 uid=705ab4f5-6393-11e8-b7cc-42010a800002"))
        
    # def test_gpu_quota_request(self):
    #     self.awsed_client.add_user_gpu_quota('user10', 10)
    #     self.awsed_client.get_user_gpu_quota('user10')
        
    #     response = self.when_validate(
    #         {
    #             "request": {
    #                 "uid": "705ab4f5-6393-11e8-b7cc-42010a800002",
    #                 "namespace": "user10",
    #                 "userInfo": {
    #                     "username": "user10"
    #                 },
    #                 "object": {
    #                     "metadata": {
    #                         "labels": {}
    #                     },
    #                     "spec": {
    #                         "containers": [{}]
    #                     }
    #                 }
    #             }
    #         }
    #     )
        
    def when_validate(self, json):
        validator = Validator(self.awsed_client, self.kube_client, self.logger)
        response = validator.validate_request(json)

        return response
