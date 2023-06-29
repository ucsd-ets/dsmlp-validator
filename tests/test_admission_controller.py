import pytest
import inspect
import os
import shutil
import tempfile
import dsmlp
from dsmlp.app import factory
# from dsmlp.plugin.awsed import CourseJson
from tests.fakes import FakeAwsedClient


@pytest.mark.integration
class TestDirCreateMain:
    def setup_method(self) -> None:
        self.awsed_client = FakeAwsedClient()
        factory.awsed_client = self.awsed_client

        # teams1 = {"teams": [
        #     {
        #         "gid": 1000,
        #         "members": [
        #             {
        #                 "firstName": "string",
        #                 "lastName": "string",
        #                 "role": "string",
        #                 "uid": 0,
        #                 "username": "user1"
        #             }
        #         ],
        #         "teamName": "string"
        #     }
        # ]}

        # self.awsed_client.add_teams_for_course_from_dict('course1', teams1)

        # teams2 = {"teams": [
        #     {
        #         "gid": 2000,
        #         "members": [
        #             {
        #                 "firstName": "string",
        #                 "lastName": "string",
        #                 "role": "string",
        #                 "uid": 0,
        #                 "username": "user2"
        #             }
        #         ],
        #         "teamName": "string"
        #     }
        # ]}

        # self.awsed_client.add_teams_for_course_from_dict('course2', teams2)

        # teams3 = {"teams": [
        #     {
        #         "gid": 3000,
        #         "members": [
        #             {
        #                 "firstName": "string",
        #                 "lastName": "string",
        #                 "role": "string",
        #                 "uid": 0,
        #                 "username": "user1"
        #             }
        #         ],
        #         "teamName": "string"
        #     },
        #     {
        #         "gid": 4000,
        #         "members": [
        #             {
        #                 "firstName": "string",
        #                 "lastName": "string",
        #                 "role": "string",
        #                 "uid": 0,
        #                 "username": "user2"
        #             }
        #         ],
        #         "teamName": "string"
        #     }
        # ]}
        # self.awsed_client.add_teams_for_course_from_dict('course3', teams3)

    def test_something(self, capsys):
        pass
        # self.awsed_client.add_course(CourseJson(courseId='course1', tags=['teams-enabled']))

        # os.environ["COURSE_IDS"] = "course1"
        # os.environ["TEAM_ROOT"] = tempfile.gettempdir()
        # dsmlp.app.factory.course_provider = EnvVarConfigProvider('COURSE_IDS')
        # self.clean_dir(tempfile.gettempdir() + "/course1")
        # cdir = tempfile.gettempdir() + "/course1/string"
        # main()
        # captured = capsys.readouterr()
        # assert captured.out == "Reading course1...\n" + f"{cdir}, uid=0, gid=1000\n"
        # assert captured.out == inspect.cleandoc(
        #     f"""
        #     Reading course1...
        #     {cdir}, uid=0, gid=1000
        #     """) + "\n"

    # noinspection PyMethodMayBeStatic
    # def clean_dir(self, course_):
    #     try:
    #         shutil.rmtree(course_)
    #     except FileNotFoundError:
    #         pass
