from typing import List

from kubernetes import client, config
from kubernetes.client import CoreV1Api, V1Namespace, V1ObjectMeta
from kubernetes.client.rest import ApiException

from dsmlp.plugin.kube import KubeClient, Namespace,  NotFound

GPU_LABEL = "nvidia.com/gpu"
GPU_LIMIT_ANNOTATION = 'gpu-limit'


class DefaultKubeClient(KubeClient):
    """
    See https://github.com/kubernetes-client/python/blob/master/kubernetes/README.md
    """

    def get_namespace(self, name: str) -> Namespace:
        api = self.get_policy_api()
        v1namespace: V1Namespace = api.read_namespace(name=name)
        metadata: V1ObjectMeta = v1namespace.metadata
        return Namespace(
            name=metadata.name,
            labels=metadata.labels,
            gpu_quota=metadata.annotations[GPU_LIMIT_ANNOTATION])
    
    def get_gpus_in_namespace(self, name: str) -> int:
        api = self.get_policy_api()
        V1Namespace: V1Namespace = api.read_namespace(name=name)
        pods = api.list_namespaced_pod(namespace=name)
        
        gpu_count = 0
        for pod in pods.items:
            gpu_count += pod.spec.containers.resources.limits['GPU_LABEL']
        
        return gpu_count
        

    # noinspection PyMethodMayBeStatic
    def get_policy_api(self) -> CoreV1Api:
        try:
            config.load_incluster_config()
        except config.ConfigException:
            try:
                config.load_kube_config()
            except config.ConfigException:
                raise Exception("Could not configure kubernetes python client")

        coreapi = client.CoreV1Api()
        return coreapi
