import inspect
from operator import contains
from dsmlp.app.validator import Validator
from dsmlp.plugin.awsed import ListTeamsResponse, TeamJson, UserResponse
from dsmlp.plugin.kube import Namespace
from hamcrest import assert_that, contains_inanyorder, equal_to, has_item
from tests.fakes import FakeAwsedClient, FakeLogger, FakeKubeClient


class TestLogs:
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

    def test_log_request_details(self):
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
                            "containers": [{}]
                        },
                    }
                }
            }
        )

        assert_that(self.logger.messages, has_item(
            "INFO Allowed request username=system:kube-system namespace=user10 uid=705ab4f5-6393-11e8-b7cc-42010a800002"))

    def test_failures_are_logged(self):
        self.awsed_client.add_user(
            'user2', UserResponse(uid=2, enrollments=[]))

        response = self.when_validate(
            {
                "request": {
                    "uid": "705ab4f5-6393-11e8-b7cc-42010a800002",
                    "userInfo": {
                        "username": "user2"
                    },
                    "namespace": "user2",
                    "object": {
                        "metadata": {
                            "labels": {}
                        },
                        "spec": {
                            "containers": [],
                            "securityContext": {"runAsUser": 3}},
                    }}})

        assert_that(self.logger.messages, has_item(
            f"INFO Denied request username=user2 namespace=user2 reason={response['response']['status']['message']} uid=705ab4f5-6393-11e8-b7cc-42010a800002"))

    def test_log_allowed_requests(self):
        self.when_validate(
            {
                "request": {
                    "uid": "705ab4f5-6393-11e8-b7cc-42010a800002",
                    "userInfo": {
                        "username": "user10"
                    },
                    "namespace": "user10",
                    "object": {
                        "metadata": {
                            "labels": {}
                        },
                        "spec": {
                            "containers": [{}]
                        }
                    }
                }
            }
        )

        assert_that(self.logger.messages, has_item(
            "INFO Allowed request username=user10 namespace=user10 uid=705ab4f5-6393-11e8-b7cc-42010a800002"))
        
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
