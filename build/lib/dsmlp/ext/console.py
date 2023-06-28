from dsmlp.plugin.console import Console


class LoggingConsole(Console):
    def __init__(self):
        self.messages = []

    def write(self, message):
        self.messages.append(message)

    def output(self):
        return "\n".join(self.messages)


class StdoutConsole(Console):
    def write(self, message):
        print(message)
