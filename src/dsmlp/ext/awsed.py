import os

import requests
from dacite import from_dict

from dsmlp.plugin.awsed import AwsedClient, ListTeamsResponse, UserResponse


class DefaultAwsedClient(AwsedClient):
    def __init__(self):
        self.endpoint = os.environ.get('AWSED_ENDPOINT')
        self.awsed_api_key = os.environ.get('AWSED_API_KEY')

    def describe_user(self, username: str) -> UserResponse:
        return self.dataclass_request(UserResponse, f"/users/{username}")

    def list_user_teams(self, username: str) -> ListTeamsResponse:
        return self.dataclass_request(ListTeamsResponse, f"/teams?username={username}")

    def json_request(self, url):
        result = requests.get(self.endpoint + url, headers=self.auth())

        return result.json()

    def dataclass_request(self, data_class, url):
        result = requests.get(self.endpoint + url, headers=self.auth())

        return from_dict(data_class=data_class, data=result.json())

    def auth(self):
        headers = {'Authorization': 'AWSEd api_key=' + self.awsed_api_key}
        return headers
