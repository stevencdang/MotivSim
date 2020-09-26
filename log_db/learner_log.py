# classes to support logging for simulated learner
import uuid
from collections.abc import Iterable
import logging
import copy
import json
from uuid import UUID

logger = logging.getLogger(__name__)

class Decision:

    def __init__(self, student, choice, time, action_evs, pev):
        self._id = str(uuid.uuid4())
        self.student_id = student._id
        self.choice = choice
        self.time = time
        self.action_evs = action_evs
        self.pev = pev # Probability of each expectant-value for each action

    def to_dict(self):
        return self.__dict__
        

class LoggedAction:

    def __init__(self, student, action, time):
        self._id = str(uuid.uuid4())
        self.student_id = student._id
        self.action = action
        self.time = time

    def to_dict(self):
        result = copy.deepcopy(self.__dict__)
        result['action'] = self.action.to_dict()
        # result['action'] = self.action.to_dict()
        return result
        


