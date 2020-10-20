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
from tutor.feedback import *
from log_db.learner_log import *

logger = logging.getLogger(__name__)

class SelfEfficacyLearner(Learner):

    def __init__(self, domain, self_eff=None):
        super().__init__(domain)
        self.type = "Self Efficacy Learner"
        self.state = SelfEfficacyLearnerState()
        self.state.skills = self.skills
        self.min_off_task = 30 # 30 sec
        self.max_off_task = 1200 # 20 minutes
        self.mean_hint_time = 3 # seconds
        self.sd_hint_time = 1 # seconds
        self.mean_guess_time = 3 # seconds
        self.sd_guess_time = 1 # seconds
        self.diligence = random.gauss(2,.3)
        if self.diligence <= 0:
            self.diligence = 0.1
        self.values = {}
        self.self_eff = 0
        self.init_values()
        self.init_self_eff(self_eff)

    def init_values(self):
        atv = 0
        while atv <= 4:
            atv = random.gauss(10,1.5)
        gsv = 0
        while gsv <= 0:
            gsv = random.gauss(atv - 2, 1)
        hrv = 0
        while hrv <= 0.1:
            if gsv < 3:
                hrv = random.gauss(gsv + 1, 1)
            else:
                hrv = random.gauss(3, 1)
        otv = 0
        while otv <= 0:
            otv = random.gauss(1,3)

        self.values = {
            'attempt': atv,
            'guess': gsv,
            'hint request': hrv,
            'off task': otv
        }


    def init_self_eff(self, self_eff):
        if self_eff is not None:
            se = self_eff
        else:
            se = random.gauss(0.5, 0.15)

        if se >= 1:
            se = 0.99
        elif se <= 0:
            se = 0.01

        self.self_eff = se


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

    def process_feedback(self, fdbk):
        if isinstance(fdbk, AttemptResponse):
            logger.debug("Processing Attempt response: %s" % str(fdbk))
            self.state.total_attempts = self.state.total_attempts + 1
            if fdbk.is_correct:
                self.state.total_success = self.state.total_success + 1
        if isinstance(fdbk, HintResponse):
            logger.debug("Processing Hint Request response: %s" % str(fdbk))

    def update_state(self):
        pass

    def calc_expectancy(self, action):
        logger.debug("Calculating expectancy for action: %s" % str(action))
        if action == Attempt:
            self_eff = self.calc_self_eff()
            # Adjust expectancy for each hint
            total_hints = self.cur_context.hints_used + self.cur_context.hints_avail
            hint_exp = self.cur_context.hints_used / total_hints
            exp = self_eff + (1 - self_eff) * hint_exp
            return exp
        elif action == Guess:
            exp = random.gauss(0.10, 0.02)
            if exp < 0:
                exp = 0
            elif exp >1:
                exp = 1
            return exp
        elif action == HintRequest:
            return 1
        elif action == OffTask:
            return 1
        else:
            return 0

    def calc_value(self, action):
        logger.debug("Calculating value for action: %s" % str(action))
        if action == Attempt:
            return self.values['attempt']
        elif action == Guess:
            return self.values['guess']
        elif action == HintRequest:
            return self.values['hint request']
        elif action == OffTask:
            return self.values['off task']
        else:
            return 0

    def calc_self_eff(self):
        ''' 
        Self-efficacy is [0,1]. Self-efficacy is calculated as the success rate on prior attempts.
        An initial self-efficacy ratio is defined per student and is comparable to a success rate
        over the past 100 prior attempts

        '''
        init_attempts = 1000
        init_success = self.self_eff * init_attempts
        self_eff = (init_success + self.state.total_success) / (init_attempts + self.state.total_attempts)
        return self_eff

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
        result['self_eff'] = self.self_eff
        result['values'] = self.values
        result['total_attempts'] = self.state.total_attempts
        result['total_success'] = self.state.total_success
        return result


class SelfEfficacyLearnerState(LearnerState):

    def __init__(self):
        self.off_task = False
        self.attempted = False
        self.skills = None
        self.total_attempts = 0
        self.total_success = 0

    def is_off_task(self):
        return self.off_task

    def has_attempted(self):
        return attempted



