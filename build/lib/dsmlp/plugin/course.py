from abc import ABCMeta, abstractmethod
from dataclasses import dataclass
from typing import List


@dataclass
class AppConfig:
    team_root: str
    courses: List[str]


class ConfigProvider(metaclass=ABCMeta):
    @abstractmethod
    def list_courses(self) -> List[str]:
        """All active courses"""
        pass

    @abstractmethod
    def get_config(self) -> AppConfig:
        pass
