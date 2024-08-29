import os

import requests
from dacite import from_dict

from dsmlp.plugin.awsed import AwsedClient, ListTeamsResponse, TeamJson, UnsuccessfulRequest, UserResponse, UserQuotaResponse, Quota

import awsed.client
import awsed.types
import logging
from dsmlp.plugin.logger import Logger

# added logging to check if API has an error getting GPU quota
logging.basicConfig(level=logging.ERROR, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
class ExternalAwsedClient(AwsedClient): 
    def __init__(self):
        self.client = awsed.client.DefaultAwsedClient(endpoint=os.environ.get('AWSED_ENDPOINT'),
                                                      awsed_api_key=os.environ.get('AWSED_API_KEY'))
        self.logger = logging.getLogger(__name__)  # Initialize the logger

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
    
    # Fetch user's GPU quota with AWSED Api
    def get_user_gpu_quota(self, username: str) -> int:
        try:
            usrGpuQuota = self.client.get_user_quota(username)
            self.logger.debug(f"usrGpuQuota: {usrGpuQuota}")  # Log the structure of usrGpuQuota
            if not usrGpuQuota:
                return None
            gpu_quota = usrGpuQuota.quota.resources.get("gpu", 0)  # Access the correct attribute
            quota = Quota(user=username, resources={"gpu": gpu_quota})
            response = UserQuotaResponse(quota=quota)
            return gpu_quota
        
        # Debugging
        except KeyError as e:
            self.logger.error(f"Key error: {e}")
            return None
        except ValueError as e:
            self.logger.error(f"Value error: {e}")
            return None
        except Exception as e:
            self.logger.error(f"Failed to fetch GPU quota for user {username}: {e}")
            return None
