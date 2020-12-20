# Classes that define feedback from tutor to learner
import logging
import uuid

logger = logging.getLogger(__name__)

class Feedback:

    def __init__(self, action):
        self.type = type(self).__name__
        self.action = action
        self.msg = None

    def __str__(self):
        return str(self.to_dict())

    def to_dict(self):
        return self.__dict__


class AttemptResponse(Feedback):

    def __init__(self, action, is_correct, msg=""):
        super().__init__(action)
        # self.type = "Attempt Response"
        self.is_correct = is_correct
        self.msg = msg


class HintResponse(Feedback):

    def __init__(self, action, hint_num, hint_remain, msg=""):
        super().__init__(action)
        # self.type = "Hint Response"
        self.hint_num = hint_num
        self.hint_remain = hint_remain
        self.msg = msg

