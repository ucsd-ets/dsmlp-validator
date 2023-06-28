from typing import List

from kubernetes import client, config
from kubernetes.client import CoreV1Api, V1Namespace, V1ObjectMeta
from kubernetes.client.rest import ApiException

from dsmlp.plugin.kube import KubeClient, Namespace,  NotFound


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
            labels=metadata.labels)

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
