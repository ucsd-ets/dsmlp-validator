from dsmlp.ext.awsed import DefaultAwsedClient, ExternalAwsedClient
from dsmlp.ext.kube import DefaultKubeClient


class AppFactory:
    def __init__(self):
        # self.awsed_client = DefaultAwsedClient()
        self.awsed_client = ExternalAwsedClient()
        self.kube_client = DefaultKubeClient()
