from collections.abc import Mapping
from dataclasses import dataclass
from os import path
from typing import List, TypedDict, Dict

from dacite import from_dict

from dsmlp.plugin.awsed import AwsedClient,  ListTeamsResponse, UnsuccessfulRequest, UserResponse
from dsmlp.plugin.kube import KubeClient, Namespace, NotFound
from dsmlp.plugin.logger import Logger


class FakeAwsedClient(AwsedClient):
    def __init__(self):
        self.teams: Dict[str, ListTeamsResponse] = {}
        self.users: Dict[str, UserResponse] = {}

    def list_user_teams(self, username: str) -> ListTeamsResponse:
        try:
            return self.teams[username]
        except KeyError:
            if username in self.users:
                return ListTeamsResponse(teams=[])
            raise UnsuccessfulRequest()

    def describe_user(self, username: str) -> UserResponse:
        try:
            return self.users[username]
        except KeyError:
            return None

    def add_user(self, username, user: UserResponse):
        self.users[username] = user

    def add_teams(self, username, teams: ListTeamsResponse):
        self.teams[username] = teams


class FakeKubeClient(KubeClient):
    def __init__(self):
        self.namespaces: TypedDict[str, Namespace] = {}
        self.existing_gpus: TypedDict[str, int] = {}

    def get_namespace(self, name: str) -> Namespace:
        try:
            return self.namespaces[name]
        except KeyError:
            raise UnsuccessfulRequest()
    
    def get_gpus_in_namespace(self, name: str) -> int:
        try:
            return self.existing_gpus[name]
        except KeyError:
            return 0

    def add_namespace(self, name: str, namespace: Namespace):
        self.namespaces[name] = namespace
    
    def set_existing_gpus(self, name: str, gpus: int):
        self.existing_gpus[name] = gpus


class FakeLogger(Logger):
    def __init__(self) -> None:
        self.messages = []

    def debug(self, message):
        self.messages.append(f"DEBUG {message}")

    def info(self, message):
        self.messages.append(f"INFO {message}")

    def exception(self, exception):
        self.messages.append(f"EXCEPTION {exception}")
