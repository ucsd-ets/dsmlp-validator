import os

import requests
from dacite import from_dict

from dsmlp.plugin.awsed import AwsedClient, ListTeamsResponse, TeamJson, UnsuccessfulRequest, UserResponse, UserGpuQuotaResponse

import awsed.client
import awsed.types

class ExternalAwsedClient(AwsedClient): 
    def __init__(self):
        self.client = awsed.client.DefaultAwsedClient(endpoint=os.environ.get('AWSED_ENDPOINT'),
                                                      awsed_api_key=os.environ.get('AWSED_API_KEY'))

    def describe_user(self, username: str) -> UserResponse:
        usrResultJson = self.client.describe_user(username)
        if not usrResultJson:
            return None
        return UserResponse(uid=usrResultJson.uid, enrollments=usrResultJson.enrollments)

    def list_user_teams(self, username: str) -> ListTeamsResponse:
        usrTeams = self.client.list_teams(username)
        teams = []
        
        for team in usrTeams.teams:
            teams.append(TeamJson(gid=team.gid))
            
        return ListTeamsResponse(teams=teams)
    
    # Fetch user's GPU quota with AWSED Api and assign to UserGpuQuotaResponse object
    def get_user_gpu_quota(self, username: str) -> UserGpuQuotaResponse:
        try:
            usrGpuQuota = self.client.fetch_user_gpu_quota(username)
            if not usrGpuQuota:
                return None
            return UserGpuQuotaResponse(gpu_quota=usrGpuQuota.gpuQuota)
        except:
            return None
