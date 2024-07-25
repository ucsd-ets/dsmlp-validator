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

    def __init__(self, awsed: AwsedClient, kube: KubeClient, logger: Logger) -> None:
        self.awsed = awsed
        self.kube = kube
        self.logger = logger

    def get_ultilized_gpu(self, request: Request):
        # Calculate the number of GPUs requested for kube client
        utilized_gpus = 0
        for container in request.object.spec.containers:
            requested, limit = 0, 0
            try:
                requested = int(container.resources.requests[GPU_LABEL])
            except (KeyError, AttributeError, TypeError):
                pass
            try:
                limit = int(container.resources.limits[GPU_LABEL])
            except (KeyError, AttributeError, TypeError):
                pass
            
            utilized_gpus += max(requested, limit)
        
        # Short circuit if no GPUs requested (permits overcap) or return
        if utilized_gpus == 0:
            raise ValueError("Error: No GPUs requested.")
        return utilized_gpus
    
    def get_gpu_quota(self, awsed_quota, kube_client_quota):
        """
        Use AWSED GPU quota if it is not None and greater than 0 
        else use namespace GPU quota if it is not None and greater than 0 
        else use 1 as default
        """
        
        default_gpu_quota = 1
        if awsed_quota is not None and awsed_quota > 0:
            default_gpu_quota = awsed_quota
        elif kube_client_quota is not None and kube_client_quota > 0:
            default_gpu_quota = kube_client_quota
        return default_gpu_quota

    def validate_pod(self, request: Request):
        """
        Validate pods for namespaces with the 'k8s-sync' label
        """

        # Low priority pods pass through
        priority = request.object.spec.priorityClassName
        if priority is not None and priority == LOW_PRIORITY_CLASS:
            return
        
        # initialized namespace, gpu_quota from awsed, and curr_gpus
        namespace = self.kube.get_namespace(request.namespace)
        curr_gpus = self.kube.get_gpus_in_namespace(request.namespace)
        awsed_gpu_quota = self.awsed.get_user_gpu_quota(request.namespace)
        
        # check ultilized gpu
        utilized_gpus = self.get_ultilized_gpu(request=request)
        
        # request gpu_quota from method
        gpu_quota = self.get_gpu_quota(awsed_gpu_quota, namespace.gpu_quota)
        
        # Check if the total number of utilized GPUs exceeds the GPU quota
        if utilized_gpus + curr_gpus > gpu_quota:
            raise ValidationFailure(
                f"GPU quota exceeded. Wanted {utilized_gpus} but with {curr_gpus} already in use, "
                f"the quota of {gpu_quota} would be exceeded.")