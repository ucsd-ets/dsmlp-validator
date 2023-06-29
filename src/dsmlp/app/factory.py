from dsmlp.ext.awsed import DefaultAwsedClient
from dsmlp.ext.kube import DefaultKubeClient


class AppFactory:
    def __init__(self):
        self.awsed_client = DefaultAwsedClient()
        self.kube_client = DefaultKubeClient()
