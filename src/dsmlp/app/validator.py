from dataclasses import dataclass
import json
from typing import Dict, List, Optional

from dataclasses_json import dataclass_json
from dsmlp.plugin.awsed import AwsedClient, UnsuccessfulRequest
from dsmlp.plugin.console import Console
from dsmlp.plugin.course import ConfigProvider
from dsmlp.plugin.kube import KubeClient, NotFound
import jsonify

from dsmlp.plugin.logger import Logger
from abc import ABCMeta, abstractmethod
from dsmlp.app.id_validator import IDValidator
from dsmlp.app.gpu_validator import GPUValidator
from dsmlp.app.tritongpt_validator import TritonGPTValidator
from dsmlp.app.types import *
from dsmlp.app.config import *

class Validator:
    def __init__(self, awsed: AwsedClient, kube: KubeClient, logger: Logger) -> None:
        self.awsed = awsed
        self.logger = logger
        self.kube = kube
        self.component_validators = [IDValidator(awsed, logger), GPUValidator(awsed, kube, logger)]

    def validate_request(self, admission_review_json):
        self.logger.debug("request=" + json.dumps(admission_review_json, indent=2))
        review: AdmissionReview = AdmissionReview.from_dict(admission_review_json)

        try:
            return self.handle_request(review.request)
        except Exception as ex:
            self.logger.exception(ex)
            self.logger.info(
                f"Denied request username={review.request.userInfo.username} namespace={review.request.namespace} reason=Error uid={review.request.uid}")

            return self.admission_response(review.request.uid, False, f"Error")

    def handle_request(self, request: Request):
        self.logger.info(
            f"Validating request username={request.userInfo.username} namespace={request.namespace} uid={request.uid}")

        try:
            self.validate_pod(request)
        except ValidationFailure as ex:
            self.logger.info(
                f"Denied request username={request.userInfo.username} namespace={request.namespace} reason={ex.message} uid={request.uid}")

            return self.admission_response(request.uid, False, f"{ex.message}")

        self.logger.info(
            f"Allowed request username={request.userInfo.username} namespace={request.namespace} uid={request.uid}")
        return self.admission_response(request.uid, True, "Allowed")

    def validate_pod(self, request: Request):

        ### if tgpt-validator == enabled
        ### run special tritongpt validator that gets permitted UIDs from namespace instead of sicad
        try:
            namespace = self.kube.get_namespace(request.namespace)

            if(self.kube.get_tgpt_label(namespace) == "enabled"):
                self.logger.info("Triton GPT Mode Activated. Only running TritonGPT Validator.")
                TritonGPTValidator(self.kube, self.logger).validate_pod(request)
                return
        except Exception as err:
            self.logger.exception(err)

        for component_validator in self.component_validators:
            component_validator.validate_pod(request)

    def admission_response(self, uid, allowed, message):
        return {
            "apiVersion": "admission.k8s.io/v1",
            "kind": "AdmissionReview",
            "response": {
                "uid": uid,
                "allowed": allowed,
                "status": {
                    "message": message
                }
            }
        }
