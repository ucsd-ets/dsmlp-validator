
from dataclasses import dataclass
from typing import List, Optional, Dict
from dataclasses_json import dataclass_json
from abc import ABCMeta, abstractmethod

# Kubernetes API types

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
    priorityClassName: Optional[str] = None

@dataclass_json
@dataclass
class ObjectMeta:
    labels: Dict[str, str]


@dataclass_json
@dataclass
class Object:
    metadata: ObjectMeta
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