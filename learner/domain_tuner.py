# Class for a student that always attempts problems to support tuning domain parameters
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

class DomainTuner(Learner):

    def __init__(self, domain):
        super().__init__(domain)
        self.type = "Domain Tuner Learner"
        self.state = DomainTunerLearnerState()
        self.state.skills = self.skills
        self.min_off_task = 30 # 30 sec
        self.max_off_task = 1200 # 20 minutes
        self.mean_hint_time = 3 # seconds
        self.sd_hint_time = 1 # seconds
        self.mean_guess_time = 3 # seconds
        self.sd_guess_time = 1 # seconds
        self.diligence = 2

    def choose_action(self):
        actions = self.cur_context.get_actions()
        if Attempt in actions:
            choice = Attempt
        else:
            choice = actions[0]
            logger.warning("Attempt is not a possible action. Only: %s\nChoosing %s instead" % (str(actions), str(choice)))
        # Dummy values
        action_evs = {}
        pev = []
        decision = Decision(self, choice.__name__, self.cur_context.time, action_evs, pev, self.cur_context)
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
            # Lazy fiz to truncate gaussian
            if time < 0:
                logger.debug("Action performed was less than 0 secs, channging to 0 sec")
                time = 0

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
            time = random.gauss(self.mean_hint_time, self.sd_hint_time)
            # Lazy fiz to truncate gaussian
            if time < 0:
                logger.debug("Action performed was less than 0 secs, channging to 0 sec")
                time = 0

            act = HintRequest(time)
        elif action == Guess:
            logger.debug("Action is Guess")
            weights = [0.01, 0.99]
            is_correct = random.choices([True, False], weights=weights, k=1)[0]
            time = random.gauss(self.mean_guess_time, self.sd_guess_time)
            # Lazy fiz to truncate gaussian
            if time < 0:
                logger.debug("Action performed was less than 0 secs, channging to 0 sec")
                time = 0

            if time < 0.25:
                time = 0.25 
            act = Guess(time, is_correct)
        elif action == OffTask:
            logger.debug("Action is %s" % str(action))
            time = random.uniform(self.min_off_task, self.max_off_task)
            # Lazy fiz to truncate gaussian
            if time < 0:
                logger.debug("Action performed was less than 0 secs, channging to 0 sec")
                time = 0

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

        logger.debug("Logged action: %s" % str(logged_action.to_dict()))
        self.db.actions.insert_one(logged_action.to_dict())

        return act

    def update_state(self):
        pass

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


class DomainTunerLearnerState(LearnerState):

    def __init__(self):
        self.off_task = False
        self.attempted = False
        self.skills = None

    def is_off_task(self):
        return self.off_task

    def has_attempted(self):
        return attempted



