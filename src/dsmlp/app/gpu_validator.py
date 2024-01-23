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


class GPUValidator(ComponentValidator):
    
    def __init__(self, kube: KubeClient, logger: Logger) -> None:
        self.kube = kube
        self.logger = logger
    
    def validate_pod(self, request: Request):
        """
        Validate pods for namespaces with the 'k8s-sync' label
        """
        
        # Low priority pods pass through
        priority = request.object.spec.priorityClassName
        if priority is not None and priority == LOW_PRIORITY_CLASS:
            return
        
        namespace = self.kube.get_namespace(request.namespace)
        curr_gpus = self.kube.get_gpus_in_namespace(request.namespace)
        
        requested_gpus = 0
        for container in request.object.spec.containers:
            if container.resources is not None and GPU_LABEL in container.resources.requests:
                requested_gpus += container.resources.requests[GPU_LABEL]
            
        if requested_gpus + curr_gpus > namespace.gpu_quota:
            raise ValidationFailure(f"GPU quota exceeded. Requested {requested_gpus} but with {curr_gpus} already in use, the quota of {namespace.gpu_quota} would be exceeded.")