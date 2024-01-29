import inspect
from operator import contains
from dsmlp.app.validator import Validator
from dsmlp.plugin.awsed import ListTeamsResponse, TeamJson, UserResponse
from dsmlp.plugin.kube import Namespace
from hamcrest import assert_that, contains_inanyorder, equal_to, has_item
from tests.fakes import FakeAwsedClient, FakeLogger, FakeKubeClient
from dsmlp.ext.kube import DefaultKubeClient
from kubernetes.client import V1PodList, V1Pod, V1PodSpec, V1Container, V1ResourceRequirements

class FakeInternalClient:
    def read_namespace(self, name: str) -> Namespace:
        return "namespace"
    def list_namespaced_pod(self, namespace: str) -> int:
        
        try:
            return self.namespaced_pods
        except AttributeError:
            raise AttributeError("namespaced_pods not set")
    
    def set_namespaced_pods(self, pods):
        self.namespaced_pods = pods

class TestValidator:
    def setup_method(self) -> None:
        self.logger = FakeLogger()
        self.real_kube_client = DefaultKubeClient()
        
    def patch_kube_client(self, namespaced_pods):
        client = FakeInternalClient()
        client.set_namespaced_pods(namespaced_pods)
        
        self.real_kube_client.get_policy_api = lambda: client
        
        return self.real_kube_client

    def test_collect_gpus(self):
        
        k_client = self.patch_kube_client(V1PodList(
            items=[V1Pod(
                spec=V1PodSpec(
                    containers=[V1Container(
                        name="container1",
                        resources=V1ResourceRequirements(
                            requests={"nvidia.com/gpu": "1"},
                            limits={"nvidia.com/gpu": "2"}
                        )
                    )]
                )
            )]
        ))
        
        assert_that(k_client.get_gpus_in_namespace('user10'), equal_to(2))
    
    def test_no_gpus_requested(self):
        
        k_client = self.patch_kube_client(V1PodList(
            items=[V1Pod(
                spec=V1PodSpec(
                    containers=[V1Container(
                        name="container1",
                        resources=V1ResourceRequirements(
                            limits={"nvidia.com/gpu": "1"}
                        )
                    )]
                )
            )]
        ))
        
        assert_that(k_client.get_gpus_in_namespace('user10'), equal_to(1))
    
    def test_no_limits_nor_requests(self):
            
        k_client = self.patch_kube_client(V1PodList(
            items=[V1Pod(
                spec=V1PodSpec(
                    containers=[V1Container(
                        name="container1",
                        resources=V1ResourceRequirements()
                    )]
                )
            )]
        ))
        
        assert_that(k_client.get_gpus_in_namespace('user10'), equal_to(0))

    def when_validate(self, json):
        validator = Validator(self.awsed_client, self.kube_client, self.logger)
        response = validator.validate_request(json)

        return response
