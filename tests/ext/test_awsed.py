import os
import requests_mock
from hamcrest import assert_that, equal_to
from dsmlp.ext.awsed import ExternalAwsedClient
from dsmlp.plugin.awsed import ListTeamsResponse, TeamJson, UserResponse


# No point testing just the API client. Leaving the imports here for reference.

# class TestAwsedClient:
#     # noinspection PyMethodMayBeStatic
#     def setup_method(self) -> None:
#         os.environ['AWSED_ENDPOINT'] = 'https://awsed.ucsd.edu/api'
#         os.environ['AWSED_API_KEY'] = "1234"

#     # noinspection PyMethodMayBeStatic
#     def teardown_method(self) -> None:
#         os.environ.pop('AWSED_ENDPOINT')
#         os.environ.pop('AWSED_API_KEY')

#     def test_describe_user(self, requests_mock):
#         """test list courses by tag"""
#         requests_mock.get('https://awsed.ucsd.edu/api/users/user1', text="""
#             {
#                 "username": "user1",
#                 "firstName": "user",
#                 "lastName": "1",
#                 "uid":1,
#                 "enrollments": ["ABC1", "ABC2"]
#             }
#             """)
#         c = ExternalAwsedClient()
#         user = c.describe_user("user1")

#         assert_that(user, equal_to(
#             UserResponse(uid=1)
#         ))

#     def test_list_user_teams(self, requests_mock):
#         """test list courses by tag"""
#         requests_mock.get('https://awsed.ucsd.edu/api/teams?username=user1', text="""
#             {
#                 "teams": [
#                     {
#                         "teamName": "string",
#                         "sanitizedTeamName": "string",
#                         "uniqueName": "string",
#                         "gid": 1,
#                         "members": [
#                             {
#                             "username": "string",
#                             "firstName": "string",
#                             "lastName": "string",
#                             "uid": 0,
#                             "role": "string"
#                             }
#                         ],
#                         "course": {
#                             "tags": [
#                             "string"
#                             ],
#                             "enrollments": [
#                             {
#                                 "username": "string",
#                                 "firstName": "string",
#                                 "lastName": "string",
#                                 "uid": 0,
#                                 "role": "string"
#                             }
#                             ],
#                             "courseId": "string",
#                             "pool": {
#                             "name": "string",
#                             "poolRootName": "string",
#                             "rule": "string",
#                             "ou": "string",
#                             "courseName": "string",
#                             "mode": "string"
#                             },
#                             "active": true,
#                             "grader": {
#                             "username": "string",
#                             "firstName": "string",
#                             "lastName": "string",
#                             "uid": 0,
#                             "role": "string"
#                             },
#                             "fileSystem": {
#                             "identifier": "string",
#                             "server": "string",
#                             "path": "string"
#                             },
#                             "snowTicket": "string",
#                             "quarter": "string",
#                             "subject": "string",
#                             "courseNumber": "string",
#                             "instructor": "string",
#                             "instructorEmail": "string"
#                         }
#                     }
#                 ]
#             }
#             """)
#         c = ExternalAwsedClient()
#         user = c.list_user_teams('user1')

#         assert_that(user, equal_to(
#             ListTeamsResponse(teams=[
#                 TeamJson(gid=1)
#             ])
#         ))
