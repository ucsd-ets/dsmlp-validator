from collections.abc import Mapping
from dataclasses import dataclass
from os import path
from typing import List, TypedDict, Dict

from dacite import from_dict

from dsmlp.plugin.awsed import AwsedClient,  ListTeamsResponse, UserResponse
from dsmlp.plugin.kube import KubeClient, Namespace, NotFound
from dsmlp.plugin.logger import Logger


class FakeAwsedClient(AwsedClient):
    def __init__(self):
        self.teams: Dict[str, ListTeamsResponse] = {}
        self.users: Dict[str, UserResponse] = {}

    def list_user_teams(self, username: str) -> ListTeamsResponse:
        return self.teams[username]

    def describe_user(self, username: str) -> UserResponse:
        return self.users[username]

    def add_user(self, username, user: UserResponse):
        self.users[username] = user

    def add_teams(self, username, teams: ListTeamsResponse):
        self.teams[username] = teams


class FakeKubeClient(KubeClient):
    def __init__(self):
        self.namespaces: TypedDict[str, Namespace] = {}

    def get_namespace(self, name: str) -> Namespace:
        return self.namespaces[name]

    def add_namespace(self, name: str, namespace: Namespace):
        self.namespaces[name] = namespace


class FakeLogger(Logger):
    def __init__(self) -> None:
        self.messages = []

    def log(self, message):
        self.messages.append(message)
