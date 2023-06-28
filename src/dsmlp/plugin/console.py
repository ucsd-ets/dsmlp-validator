from abc import ABCMeta, abstractmethod


class Console(metaclass=ABCMeta):
    @abstractmethod
    def write(self, message):
        pass
