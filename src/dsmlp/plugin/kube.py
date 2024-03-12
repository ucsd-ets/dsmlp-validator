from abc import ABCMeta, abstractmethod
from dataclasses import dataclass
from typing import List

import typing


class NotFound(Exception):
    pass

@dataclass
class Namespace:
    name: str
    labels: typing.Optional[dict]
    gpu_quota: typing.Optional[int]


class KubeClient(metaclass=ABCMeta):
    @abstractmethod
    def get_namespace(self, name: str) -> Namespace:
        """Get a namespace"""
        pass

    @abstractmethod
    def get_gpus_in_namespace(self) -> int:
        """Get # of GPUs in Namespace"""
        pass
