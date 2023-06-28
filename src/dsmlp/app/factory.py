from dsmlp.ext.awsed import DefaultAwsedClient
from dsmlp.ext.console import StdoutConsole
from dsmlp.ext.course import EnvVarConfigProvider
from dsmlp.ext.kube import DefaultKubeClient


class AppFactory:
    def __init__(self):
        self.awsed_client = DefaultAwsedClient()
        self.kube_client = DefaultKubeClient()
        self.course_provider = EnvVarConfigProvider('COURSE_IDS')
        self.console = StdoutConsole()
