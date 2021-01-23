# Class for a student that always attempts problems to support tuning domain parameters
# Add project root to python path
import sys
sys.path.append('..')

import logging
import random
import inspect
import numpy as np

from .learner import Learner
from tutor.action import *
from log_db.learner_log import *

logger = logging.getLogger(__name__)

class DomainTuner(Learner):

    def __init__(self, domain):
        super().__init__(domain)
        
        # State variables
        self.state['off_task'] = False
        self.state['attempted'] = False

        # Student Parameters
        self.attributes['min_off_task'] = 30 # 30 sec
        self.attributes['max_off_task'] = 1200 # 20 minutes
        self.attributes['mean_hint_time'] = 3 # seconds
        self.attributes['sd_hint_time'] = 1 # seconds
        self.attributes['mean_guess_time'] = 3 # seconds
        self.attributes['sd_guess_time'] = 1 # seconds
        self.attributes['diligence'] = 2

    def choose_action(self, cntxt):
        actions = cntxt.get_actions()
        if Attempt in actions:
            choice = Attempt
        else:
            choice = actions[0]
            logger.warning("Attempt is not a possible action. Only: %s\nChoosing %s instead" % (str(actions), str(choice)))
        # Dummy values
        action_evs = {}
        pev = []
        decision = Decision(self, choice.__name__, cntxt.time, action_evs, pev, cntxt)
        # logger.debug("Logging decision: %s" % str(decision.to_dict()))
        # logger.debug("******************************************************")
        # self.db.decisions.insert_one(decision.to_dict())


        logger.debug("Choosing action: %s" % str(choice))
        return choice

    def perform_action(self, action, cntxt):
        kc = cntxt.kc
        logger.debug("Action is %s" % str(action))
        if action == Attempt:
            logger.debug("Action is attempt")
            time = random.gauss(kc.m_time, kc.sd_time)
            # Lazy fiz to truncate gaussian
            if time < 0:
                logger.debug("Action performed was less than 0 secs, channging to 0 sec")
                time = 0

            if self.skills[kc._id]:
                weights = [(1 - kc.ps), kc.ps]
            else:
                weights = [kc.pg, (1 - kc.pg)]
            is_correct = random.choices([True, False], weights=weights, k=1)[0]
            self.set_attempted()
            # Make is_correct default to True to change later
            act = Attempt(time, is_correct)
            
        elif action == HintRequest:
            logger.debug("Action is HintRequest")
            time = random.gauss(self.attributes['mean_hint_time'], self.attributes['sd_hint_time'])
            # Lazy fiz to truncate gaussian
            if time < 0:
                logger.debug("Action performed was less than 0 secs, channging to 0 sec")
                time = 0

            act = HintRequest(time)
        elif action == Guess:
            logger.debug("Action is Guess")
            weights = [0.01, 0.99]
            is_correct = random.choices([True, False], weights=weights, k=1)[0]
            time = random.gauss(self.attributes['mean_guess_time'], self.attributes['sd_guess_time'])
            # Lazy fiz to truncate gaussian
            if time < 0:
                logger.debug("Action performed was less than 0 secs, channging to 0 sec")
                time = 0

            if time < 0.25:
                time = 0.25 
            act = Guess(time, is_correct)
        elif action == OffTask:
            logger.debug("Action is %s" % str(action))
            time = random.uniform(self.attributes['min_off_task'], self.attributes['max_off_task'])
            # Lazy fiz to truncate gaussian
            if time < 0:
                logger.debug("Action performed was less than 0 secs, channging to 0 sec")
                time = 0

            act = OffTask(time)
        else:
            logger.debug("Action is %s" % str(action))
            logger.debug("******Action is none************")
            act = None


        if cntxt.attempt == 0:
            logger.debug("Skill to update: %s" % str(kc))
            self.practice_skill(kc)

        logger.debug("Return action: %s" % str(act))
        logged_action = LoggedAction(self, act, cntxt.time)

        # logger.debug("Logged action: %s" % str(logged_action.to_dict()))
        # self.db.actions.insert_one(logged_action.to_dict())

        return act

    def is_off_task(self):
        return self.state['off_task']

    def has_attempted(self):
        return self.state['attempted']

    def set_attempted(self):
        self.state['attempted'] = True

    def clear_attempted(self):
        self.state['attempted'] = False



    def is_diligent(self, action):
        if action == Attempt:
            return True
        elif action == Guess:
            return False
        elif action == HintRequest:
            return True
        elif action == OffTask:
            return False

