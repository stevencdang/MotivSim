# Class for a student that makes decisions using primarily self-efficacy
# Add project root to python path
import sys
sys.path.append('..')

import logging
import random
import inspect
import numpy as np

from .learner import Learner, LearnerState
from tutor.action import *
from log_db.learner_log import *

logger = logging.getLogger(__name__)

class SelfEfficacyLearner(Learner):

    def __init__(self, domain):
        super().__init__(domain)
        self.type = "Self Efficacy Learner"
        self.state = SelfEfficacyLearnerState()
        self.min_off_task = 30 # 30 sec
        self.max_off_task = 1200 # 20 minutes
        self.mean_guess_time = 3 # seconds
        self.sd_guess_time = 1 # seconds
        self.diligence = 2

    def choose_action(self):
        actions = self.cur_context.get_actions()
        action_evs = {str(action): {'expectancy': self.calc_expectancy(action),
                            'value': self.calc_value(action)
                            }
              for action in actions
        }
        action_evs = {}
        for action in actions:
            exp = self.calc_expectancy(action)
            val = self.calc_value(action)
            # Diligence Multiplier
            if self.is_diligent(action):
                action_evs[action.__name__] = self.diligence * exp*val  
            else:
                action_evs[action.__name__] = exp*val

        total_ev = np.sum([val for val in action_evs.values()])
        pev = [action_evs[action.__name__]/total_ev for action in actions]
        logger.debug(str(pev))

        choice = random.choices(actions, weights=pev, k=1)[0]
        decision = Decision(self, choice.__name__, self.cur_context.time, action_evs, pev)
        logger.debug("Logging decision: %s" % str(decision.to_dict()))
        logger.debug("******************************************************")
        self.db.decisions.insert_one(decision.to_dict())


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
            self.state.attempted = True
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
            time = random.gauss(self.mean_guess_time, self.sd_guess_time)
            if time < 0.25:
                time = 0.25 
            act = Guess(time, is_correct)
        elif action == OffTask:
            logger.debug("Action is %s" % str(action))
            time = random.uniform(self.min_off_task, self.max_off_task)
            act = OffTask(time)
        else:
            logger.debug("Action is %s" % str(action))
            logger.debug("******Action is none************")
            act = None


        if self.cur_context.attempt == 0:
            logger.debug("Skill to update: %s" % str(kc))
            self.practice_skill(kc)

        self.new_context = False
        logger.debug("Return action: %s" % str(act))
        logged_action = LoggedAction(self, act, self.cur_context.time)
        logger.debug("**************************************************")
        logger.debug("**************************************************")

        logger.debug("Logged action: %s" % str(logged_action.to_dict()))
        self.db.actions.insert_one(logged_action.to_dict())
        logger.debug("**************************************************")
        logger.debug("**************************************************")

        return act

    def update_state(self):
        pass

    def calc_expectancy(self, action):
        logger.debug("Calculating expectancy for action: %s" % str(action))
        if action == Attempt:
            return 0.2
        elif action == Guess:
            return 0.01
        elif action == HintRequest:
            return 1
        elif action == OffTask:
            return 1
        else:
            return 0

    def calc_value(self, action):
        logger.debug("Calculating value for action: %s" % str(action))
        if action == Attempt:
            return 1
        elif action == Guess:
            return 0.5
        elif action == HintRequest:
            return 0.1
        elif action == OffTask:
            return 0.05
        else:
            return 0

    def is_off_task(self):
        return self.state.is_off_task()

    def is_diligent(self, action):
        if action == Attempt:
            return True
        elif action == Guess:
            return False
        elif action == HintRequest:
            return True
        elif action == OffTask:
            return False

    def to_dict(self):
        result = super().to_dict()
        result['min_off_task'] = self.min_off_task
        result['max_off_task'] = self.max_off_task
        result['mean_guess_time'] = self.mean_guess_time
        result['sd_guess_time'] = self.sd_guess_time
        result['diligence'] = self.diligence
        return result


class SelfEfficacyLearnerState(LearnerState):

    def __init__(self):
        self.off_task = False
        self.attempted = False

    def is_off_task(self):
        return self.off_task

    def has_attempted(self):
        return attempted
