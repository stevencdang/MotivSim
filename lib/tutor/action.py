# Class that defines learner actions
import logging
import uuid
import datetime as dt

from dataclasses import dataclass, field

logger = logging.getLogger(__name__)


class Action:

    def __init__(self, time):
        self.name = None
        self.type = type(self).__name__
        self.time = time

    def __str__(self):
        return self.name

    def to_dict(self):
        return self.__dict__


class Attempt(Action):

    def __init__(self, time, is_correct):
        super().__init__(time)
        self.name = "Attempt"
        self.is_correct = is_correct

class FailedAttempt(Action):

    def __init__(self, time):
        super().__init__(time)
        self.name = "Failed Attempt"


class HintRequest(Action):

    def __init__(self, time):
        super().__init__(time)
        self.name = "Hint Request"


class Guess(Action):

    def __init__(self, time, is_correct):
        super().__init__(time)
        self.name = "Guess"
        self.is_correct = is_correct


class OffTask(Action):

    def __init__(self, time):
        super().__init__(time)
        self.name = "Off Task"


class StopWork(OffTask):

    def __init__(self, time):
        super().__init__(time)
        self.name = "Stop Work"

