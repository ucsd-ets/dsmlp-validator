from abc import ABCMeta, abstractmethod


class Logger(metaclass=ABCMeta):
    @abstractmethod
    def debug(self, message: str):
        pass

    @abstractmethod
    def info(self, message: str):
        pass
