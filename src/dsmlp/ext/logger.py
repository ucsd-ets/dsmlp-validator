from dsmlp.plugin.logger import Logger
import logging


class PythonLogger(Logger):
    def __init__(self, logger: logging.Logger) -> None:
        # logging.basicConfig()
        self.logger = logging.getLogger('dsmlp')

    def debug(self, message: str):
        self.logger.debug(message)

    def info(self, message: str):
        self.logger.info(message)
