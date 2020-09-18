# Class that defines learner actions
import logging
import uuid

logger = logging.getLogger(__name__)

class Action:

    def __init__(self, time):
        self.name = None
        self.time = time

    def __str__(self):
        return self.name


class Attempt(Action):

    def __init__(self, time, is_correct):
        super().__init__(time)
        self.name = "Attempt"
        self.is_correct = is_correct


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
