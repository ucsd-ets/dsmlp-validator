from typing import List

from kubernetes import client, config
from kubernetes.client import CoreV1Api, V1Namespace, V1ObjectMeta
from kubernetes.client.rest import ApiException

from dsmlp.plugin.kube import KubeClient, Namespace,  NotFound

from dsmlp.app.config import *


class DefaultKubeClient(KubeClient):
    """
    See https://github.com/kubernetes-client/python/blob/master/kubernetes/README.md
    """

    def get_namespace(self, name: str) -> Namespace:
        api = self.get_policy_api()
        v1namespace: V1Namespace = api.read_namespace(name=name)
        metadata: V1ObjectMeta = v1namespace.metadata

        gpu_quota = 1
        if metadata is not None and metadata.annotations is not None and GPU_LIMIT_ANNOTATION in metadata.annotations:
            gpu_quota = int(metadata.annotations[GPU_LIMIT_ANNOTATION])

        return Namespace(
            name=metadata.name,
            labels=metadata.labels,
            gpu_quota=gpu_quota)

    def get_gpus_in_namespace(self, name: str) -> int:
        api = self.get_policy_api()
        V1Namespace: V1Namespace = api.read_namespace(name=name)
        pods = api.list_namespaced_pod(namespace=name)

        gpu_count = 0
        for pod in pods.items:
            for container in pod.spec.containers:
                requested, limit = 0, 0
                try:
                    requested = int(container.resources.requests[GPU_LABEL])
                except (KeyError, AttributeError, TypeError):
                    pass
                try:
                    limit = int(container.resources.limits[GPU_LABEL])
                except (KeyError, AttributeError, TypeError):
                    pass

                gpu_count += max(requested, limit)

        return gpu_count

    def get_tgpt_label(self, namespace) -> str:
        return namespace.labels.get("tgt-validator","")

    # TODO: make arbitrary function of getting namespace labels.
    def get_tgpt_uids(self, namespace) -> str:

        # should be comma delimited, i.e. 2000,100,2,20
        return namespace.labels.get("permitted-uids", "").split(',')

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
