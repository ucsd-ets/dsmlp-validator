from dataclasses import dataclass
import json
from typing import List, Optional, Dict

from dataclasses_json import dataclass_json
from dsmlp.plugin.awsed import AwsedClient, UnsuccessfulRequest
from dsmlp.plugin.console import Console
from dsmlp.plugin.course import ConfigProvider
from dsmlp.plugin.kube import KubeClient, NotFound
import jsonify

from dsmlp.plugin.logger import Logger
from abc import ABCMeta, abstractmethod

@dataclass_json
@dataclass
class SecurityContext:
    """Each Container has a SecurityContext"""
    runAsUser: Optional[int] = None
    runAsGroup: Optional[int] = None

@dataclass_json
@dataclass
class ResourceRequirements:
    requests: Optional[Dict[str, int]] = None
    limits: Optional[Dict[str, int]] = None

@dataclass_json
@dataclass
class Container:
    securityContext: Optional[SecurityContext] = None
    resources: Optional[ResourceRequirements] = None

@dataclass_json
@dataclass
class PodSecurityContext:
    """Each Pod has a SecurityContext"""
    runAsUser: Optional[int] = None
    runAsGroup: Optional[int] = None
    fsGroup: Optional[int] = None
    supplementalGroups: Optional[List[int]] = None


@dataclass_json
@dataclass
class PodSpec:
    containers: List[Container]
    initContainers: Optional[List[Container]] = None
    securityContext: Optional[PodSecurityContext] = None


@dataclass_json
@dataclass
class Object:
    spec: PodSpec


@dataclass_json
@dataclass
class UserInfo:
    username: str


@dataclass_json
@dataclass
class Request:
    uid: str
    namespace: str
    object: Object
    userInfo: UserInfo


@dataclass_json
@dataclass
class AdmissionReview:
    request: Request

class ValidationFailure(Exception):
    def __init__(self, message: str) -> None:
        self.message = message
        super().__init__(self.message)
        
class ComponentValidator:
    @abstractmethod
    def validate_pod(self, request: Request):
        pass