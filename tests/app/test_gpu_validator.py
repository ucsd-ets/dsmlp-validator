import inspect
from operator import contains
from dsmlp.app.types import ValidationFailure
from dsmlp.app.validator import Validator
from dsmlp.plugin.awsed import ListTeamsResponse, TeamJson, UserResponse
from dsmlp.plugin.kube import Namespace
from hamcrest import assert_that, contains_inanyorder, equal_to, has_item
from tests.fakes import FakeAwsedClient, FakeLogger, FakeKubeClient
from dsmlp.ext.kube import DefaultKubeClient
from dsmlp.app.gpu_validator import GPUValidator
from tests.app.utils import gen_request, try_val_with_component


class TestGPUValidator:
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
        self.kube_client.set_existing_gpus('user10', 0)

    def test_no_gpus_requested(self):
        self.try_validate(
            gen_request(), expected=True, message="Allowed"
        )

    def test_quota_not_reached(self):

        self.try_validate(
            gen_request(gpu_req=10), expected=True, message="Allowed"
        )

    def test_quota_exceeded(self):

        self.try_validate(
            gen_request(gpu_req=11), expected=False, message="GPU quota exceeded. Wanted 11 but with 0 already in use, the quota of 10 would be exceeded."
        )

    def test_sum_exceeded(self):
        self.kube_client.set_existing_gpus('user10', 5)

        self.try_validate(
            gen_request(gpu_req=6), expected=False, message="GPU quota exceeded. Wanted 6 but with 5 already in use, the quota of 10 would be exceeded."
        )

    def test_low_priority(self):
        self.kube_client.set_existing_gpus('user10', 5)

        self.try_validate(
            gen_request(gpu_req=6, low_priority=True), expected=True
        )

    # Should respond to limit as well as request
    def test_limit_exceeded(self):
        self.kube_client.set_existing_gpus('user10', 5)

        self.try_validate(
            gen_request(gpu_lim=6), expected=False, message="GPU quota exceeded. Wanted 6 but with 5 already in use, the quota of 10 would be exceeded."
        )

    def try_validate(self, json, expected: bool, message: str = None):
        try_val_with_component(GPUValidator(
            self.kube_client, self.logger), json, expected, message)
