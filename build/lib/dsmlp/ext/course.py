import os
from typing import List

from dsmlp.plugin.course import ConfigProvider, AppConfig


class StaticConfigProvider(ConfigProvider):
    def __init__(self, config: AppConfig):
        self.config = config

    def get_config(self) -> AppConfig:
        return self.config

    def list_courses(self) -> List[str]:
        return self.config.courses


class EnvVarConfigProvider(ConfigProvider):
    def __init__(self, name):
        self.var_name = name
        team_root = os.environ.get('TEAM_ROOT')
        courses = os.environ.get(self.var_name)
        if courses is not None:
            courses.split(",")
        self.config = AppConfig(team_root=team_root, courses=[])

    def get_config(self) -> AppConfig:
        return self.config

    # reads list of courses from env var
    def list_courses(self) -> List[str]:
        return os.environ.get(self.var_name).split(",")
