from abc import ABCMeta, abstractmethod
from dataclasses import dataclass
from typing import List


@dataclass
class TeamJson:
    gid: int


@dataclass
class ListTeamsResponse:
    teams: List[TeamJson]


@dataclass
class UserResponse:
    uid: int


class AwsedClient(metaclass=ABCMeta):
    @abstractmethod
    def list_user_teams(self, username: str) -> ListTeamsResponse:
        """Return the groups of a course"""
        pass

    @abstractmethod
    def describe_user(self, username: str) -> UserResponse:
        pass
