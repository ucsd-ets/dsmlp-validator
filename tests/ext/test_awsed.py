import os
from hamcrest import assert_that, equal_to
from dsmlp.ext.awsed import DefaultAwsedClient
from dsmlp.plugin.awsed import ListTeamsResponse, TeamJson, UserResponse


class TestAwsedClient:
    # noinspection PyMethodMayBeStatic
    def setup_method(self) -> None:
        os.environ['AWSED_ENDPOINT'] = 'https://awsed.ucsd.edu/api'
        os.environ['AWSED_API_KEY'] = "1234"

    # noinspection PyMethodMayBeStatic
    def teardown_method(self) -> None:
        os.environ.pop('AWSED_ENDPOINT')
        os.environ.pop('AWSED_API_KEY')

    def test_describe_user(self, requests_mock):
        """test list courses by tag"""
        requests_mock.get('https://awsed.ucsd.edu/api/users/user1', text="""
            {
                "uid":1
            }
            """)
        c = DefaultAwsedClient()
        user = c.describe_user("user1")

        assert_that(user, equal_to(
            UserResponse(uid=1)
        ))

    def test_list_user_teams(self, requests_mock):
        """test list courses by tag"""
        requests_mock.get('https://awsed.ucsd.edu/api/teams?username=user1', text="""
            {
                "teams": [
                    {
                        "gid": 1
                    }
                ]
            }
            """)
        c = DefaultAwsedClient()
        user = c.list_user_teams('user1')

        assert_that(user, equal_to(
            ListTeamsResponse(teams=[
                TeamJson(gid=1)
            ])
        ))
