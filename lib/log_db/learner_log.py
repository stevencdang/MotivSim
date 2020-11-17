# classes to support logging for simulated learner
import uuid
from collections.abc import Iterable
import logging
import copy
import json
from uuid import UUID

logger = logging.getLogger(__name__)

class Decision:

    def __init__(self, student, choice, time, action_evs, pev, context):
        self._id = str(uuid.uuid4())
        self.student_id = student._id
        self.choice = choice
        self.time = time
        self.action_evs = action_evs
        self.pev = pev # Probability of each expectant-value for each action
        self.problem = context.cur_problem._id
        self.step = context.cur_step._id
        self.kc = context.kc
        self.learner_knowledge = context.learner_kc_knowledge
        self.attempt = context.attempt
        self.hints_avail = context.hints_avail
        self.hints_used = context.hints_used
        self.learner_off_task = context.learner_off_task
        try:
            self.self_eff = student.calc_self_eff()
        except:
            self.self_eff = ''


    def to_dict(self):
        result = copy.deepcopy(self.__dict__)
        result['kc'] = copy.deepcopy(self.kc.__dict__)
        return result


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
        


