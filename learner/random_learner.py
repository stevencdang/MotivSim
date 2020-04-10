# Class for a test student that makes decisions randomly
# Add project root to python path
import sys
sys.path.append('..')

import logging
import random
import inspect

from .learner import Learner
from tutor.action import Attempt, HintRequest

logger = logging.getLogger(__name__)

class RandomLearner(Learner):

    def __init__(self, domain):
        super().__init__(domain)

        self.skills = {skill._id: random.choices([True, False], weights=[skill.pl0, (1-skill.pl0)])[0] for skill in domain.kcs}

    def choose_action(self, actions, context):
        choice = random.choice(actions)
        logger.debug("Choosing action: %s" % str(choice))
        return choice

    def perform_action(self, action, context):
        kc = context.kc
        time = random.gauss(kc.m_time, kc.sd_time)
        logger.debug("Action is %s" % str(action))
        if action == Attempt:
            logger.debug("Aciton is attempt")
            if self.skills[kc._id]:
                weights = [(1 - kc.ps), kc.ps]
            else:
                weights = [kc.pg, (1 - kc.pg)]
            is_correct = random.choices([True, False], weights=weights, k=1)[0]
            # Make is_correct default to True to change later
            act = Attempt(time, is_correct)
            
        elif action == HintRequest:
            logger.debug("Aciton is HintRequest")
            act = HintRequest(time)
        else:
            logger.debug("Action is %s" % str(action))
            act = None


        if context.attempt == 0:
            logger.debug("Skill to update: %s" % str(kc))
            self.practice_skill(kc)

        return act

    def update_state(self):
        pass

    def calc_expectancy(self, action, context):
        pass

    def calc_value(self, action, context):
        pass
