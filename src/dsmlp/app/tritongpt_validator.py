from dataclasses import dataclass
import json
from typing import List, Optional

from dataclasses_json import dataclass_json
from dsmlp.plugin.awsed import AwsedClient, UnsuccessfulRequest
from dsmlp.plugin.console import Console
from dsmlp.plugin.course import ConfigProvider
from dsmlp.plugin.kube import KubeClient, NotFound
import jsonify

from dsmlp.plugin.logger import Logger
from dsmlp.app.types import *
from dsmlp.app.config import *

# used in order to bypass awsed for tritonGPT while still maintaining UID security.
class TritonGPTValidator(ComponentValidator):

    def __init__(self, kube: KubeClient, logger: Logger) -> None:
        self.kube = kube
        self.logger = logger

    def validate_pod(self, request: Request):

        permitted_uids = self.kube.get_tgpt_uids()
        requested_uid = request.object.spec.securityContext.runAsUser

        # if request.uid is not in kube.get_tgpt_uids
        # return validationfailure
        if requested_uid not in permitted_uids:
            raise ValidationFailure(f"TritonGPT Validator: user with {permitted_uids} attempted to run a pod as {requested_uid}. Pod denied.")
