from abc import ABCMeta, abstractmethod


class Logger(metaclass=ABCMeta):
    @abstractmethod
    def log(self, message):
        pass
