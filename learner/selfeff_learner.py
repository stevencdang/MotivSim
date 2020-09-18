# Class for a student that makes decisions using primarily self-efficacy
# Add project root to python path
import sys
sys.path.append('..')

import logging
import random
import inspect

from .learner import Learner, LearnerState
from tutor.action import *

logger = logging.getLogger(__name__)

class SelfEfficacyLearner(Learner):

    def __init__(self, domain):
        super().__init__(domain)
        self.state = SelfEfficacyLearnerState()

    def choose_action(self):
        actions = self.cur_context.get_actions()
        choice = random.choice(actions)
        logger.debug("Choosing action: %s" % str(choice))
        return choice

    def perform_action(self, action):
        kc = self.cur_context.kc
        logger.debug("Action is %s" % str(action))
        if action == Attempt:
            logger.debug("Action is attempt")
            time = random.gauss(kc.m_time, kc.sd_time)
            if self.skills[kc._id]:
                weights = [(1 - kc.ps), kc.ps]
            else:
                weights = [kc.pg, (1 - kc.pg)]
            is_correct = random.choices([True, False], weights=weights, k=1)[0]
            # Make is_correct default to True to change later
            act = Attempt(time, is_correct)
            
        elif action == HintRequest:
            logger.debug("Action is HintRequest")
            time = random.gauss(kc.m_time, kc.sd_time)
            act = HintRequest(time)
        elif action == Guess:
            logger.debug("Action is Guess")
            weights = [0.01, 0.99]
            is_correct = random.choices([True, False], weights=weights, k=1)[0]
            time = random.gauss(2, 2)
            if time < 0:
                time = 0
            act = Guess(time, is_correct)
        elif action == OffTask:
            logger.debug("Action is %s" % str(action))
            time = random.gauss(300, 300)
            if time < 0:
                time = random.gauss(30, 3)
            act = OffTask(time)
        else:
            logger.debug("Action is %s" % str(action))
            act = None


        if self.cur_context.attempt == 0:
            logger.debug("Skill to update: %s" % str(kc))
            self.practice_skill(kc)

        self.new_context = False

        return act

    def update_state(self):
        pass

    def calc_expectancy(self, action, context):
        pass

    def calc_value(self, action, context):
        pass

    def is_off_task(self):
        return self.state.is_off_task()


class SelfEfficacyLearnerState(LearnerState):

    def __init__(self):
        self.off_task = False

    def is_off_task(self):
        return self.off_task

