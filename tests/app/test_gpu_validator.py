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
        
        # Set gpu quota for user 10 with AWSED client
        self.awsed_client.add_user_gpu_quota('user10', 10)
        
        # Set up user11 without any quota & namespace.
        self.awsed_client.add_user(
            'user11', UserResponse(uid=11, enrollments=[]))
        self.awsed_client.add_teams('user11', ListTeamsResponse(
            teams=[TeamJson(gid=1001)]
        ))

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

    # Tests pod overcap
    def test_low_priority_overcap(self):
        self.kube_client.set_existing_gpus('user10', 11)

        self.try_validate(
            gen_request(), expected=True)

    def try_validate(self, json, expected: bool, message: str = None):
        try_val_with_component(GPUValidator(self.awsed_client,
            self.kube_client, self.logger), json, expected, message)
    
    # Test correct response for get_user_gpu_quota method
    def test_awsed_gpu_quota_correct_response(self):
        self.awsed_client.add_user_gpu_quota('user11', 5)
        user_gpu_quota = self.awsed_client.get_user_gpu_quota('user11')
        assert_that(user_gpu_quota, equal_to(5))
        
    # No quota set for user 11 from both kube and awsed, should return default value 1
    def test_gpu_validator_default_limit(self):
        self.kube_client.add_namespace('user11', Namespace(
            name='user11', labels={'k8s-sync': 'true'}, gpu_quota=0))
        
        self.kube_client.set_existing_gpus('user11', 0)
        self.try_validate(
            gen_request(gpu_req=11, username='user11'), expected=False, message="GPU quota exceeded. Wanted 11 but with 0 already in use, the quota of 1 would be exceeded."
        )
    
    # No quota set for user 11 from kube, but set from kube client, should return 5
    def test_no_awsed_gpu_quota(self):
        self.kube_client.add_namespace('user11', Namespace(
            name='user11', labels={'k8s-sync': 'true'}, gpu_quota=5))
        
        self.kube_client.set_existing_gpus('user11', 0)
        self.try_validate(
            gen_request(gpu_req=11, username='user11'), expected=False, message="GPU quota exceeded. Wanted 11 but with 0 already in use, the quota of 5 would be exceeded."
        )
    
    # Quota both set for user 11 from kube and awsed, should prioritize AWSED quota
    def test_gpu_quota_client_priority(self):
        self.kube_client.add_namespace('user11', Namespace(
            name='user11', labels={'k8s-sync': 'true'}, gpu_quota=8))
        
        self.kube_client.set_existing_gpus('user11', 3)
        self.awsed_client.add_user_gpu_quota('user11', 6)
        self.try_validate(
            gen_request(gpu_req=6, username='user11'), expected=False, message="GPU quota exceeded. Wanted 6 but with 3 already in use, the quota of 6 would be exceeded."
        )
    
    # Quota both set for user 11 from kube and awsed, should prioritize AWSED quota
    def test_gpu_quota_client_priority2(self):
        self.awsed_client.add_user_gpu_quota('user11', 18)
        self.kube_client.add_namespace('user11', Namespace(
            name='user11', labels={'k8s-sync': 'true'}, gpu_quota=12))
        
        # set existing gpu = kube client quota
        self.kube_client.set_existing_gpus('user11', 12)
        
        self.try_validate(
            gen_request(gpu_req=6, username='user11'), expected=True, message="GPU quota exceeded. Wanted 6 but with 5 already in use, the quota of 18 would be exceeded."
        )