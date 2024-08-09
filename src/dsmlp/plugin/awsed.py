from abc import ABCMeta, abstractmethod
from dataclasses import dataclass
from typing import List, Dict, Any


@dataclass
class TeamJson:
    gid: int


@dataclass
class ListTeamsResponse:
    teams: List[TeamJson]


@dataclass
class UserResponse:
    uid: int
    enrollments: List[str]

@dataclass
class Quota:
    user: str
    resources: Dict[str, Any]
    
@dataclass
class UserQuotaResponse:
    quota: Quota

class AwsedClient(metaclass=ABCMeta):
    @abstractmethod
    def list_user_teams(self, username: str) -> ListTeamsResponse:
        # Return the groups of a course
        pass

    @abstractmethod
    def describe_user(self, username: str) -> UserResponse:
        pass
    
    @abstractmethod
    def get_user_gpu_quota(self, username: str) -> UserQuotaResponse:
        # Return the quota (DICT) of a user
        pass

class UnsuccessfulRequest(Exception):
    pass
