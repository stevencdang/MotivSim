# Class for a test student that makes decisions randomly
# Add project root to python path
import sys
sys.path.append('..')

import logging
import random
import inspect

from .learner import Learner
from tutor.action import *

logger = logging.getLogger(__name__)

class RandomLearner(Learner):

    def __init__(self, domain):
        super().__init__(domain)

    def choose_action(self, cntxt):
        actions = cntxt.get_actions()
        choice = random.choice(actions)
        logger.debug("Choosing action: %s" % str(choice))
        return choice

    def perform_action(self, action, cntxt):
        kc = cntxt.kc
        logger.debug("Action is %s" % str(action))
        if action == Attempt:
            logger.debug("Aciton is attempt")
            time = random.gauss(kc.m_time, kc.sd_time)
            if self.skills[kc._id]:
                weights = [(1 - kc.ps), kc.ps]
            else:
                weights = [kc.pg, (1 - kc.pg)]
            is_correct = random.choices([True, False], weights=weights, k=1)[0]
            # Make is_correct default to True to change later
            act = Attempt(time, is_correct)
            
        elif action == HintRequest:
            logger.debug("Aciton is HintRequest")
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


        if cntxt.attempt == 0:
            logger.debug("Skill to update: %s" % str(kc))
            self.practice_skill(kc)

        return act

