# Class for a student that makes decisions using primarily self-efficacy
# Add project root to python path
import sys
sys.path.append('..')

import logging
import random
import numpy as np

from .learner import Learner, LearnerState
from tutor.action import *
from tutor.feedback import *
from log_db.learner_log import *

logger = logging.getLogger(__name__)

class SelfEfficacyLearner(Learner):

    def __init__(self, domain, self_eff=None):
        super().__init__(domain)

        # State Parameters
        self.state['off_task'] = False
        self.state['attempted'] = False
        self.state['total_attempts'] = 0
        self.state['total_success'] = 0

        # Student Parameters
        self.attributes['min_off_task'] = 30 # 30 sec
        self.attributes['max_off_task'] = 1200 # 20 minutes
        self.attributes['mean_hint_time'] = 3 # seconds
        self.attributes['sd_hint_time'] = 1 # seconds
        self.attributes['mean_guess_time'] = 3 # seconds
        self.attributes['sd_guess_time'] = 1 # seconds
        self.attributes['diligence'] = random.gauss(2,.3)
        if self.diligence <= 0:
            self.attributes['diligence'] = 0.1
        self.attributes['values'] = {}
        self.attributes['self_eff'] = 0

        # Call initialization methods
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

        self.attributes['self_eff'] = se


    def choose_action(self, cntxt):
        actions = cntxt.get_actions()
        action_evs = {str(action): {'expectancy': self.calc_expectancy(action, cntxt),
                            'value': self.calc_value(action)
                            }
              for action in actions
        }
        action_evs = {}
        for action in actions:
            exp = self.calc_expectancy(action, cntxt)
            val = self.calc_value(action)
            # Diligence Multiplier
            if self.is_diligent(action):
                action_evs[action.__name__] = self.attributes['diligence'] * exp*val  
            else:
                action_evs[action.__name__] = exp*val

        total_ev = np.sum([val for val in action_evs.values()])
        pev = [action_evs[action.__name__]/total_ev for action in actions]
        logger.debug(str(pev))

        choice = random.choices(actions, weights=pev, k=1)[0]
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
            self.attempted = True
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

    def process_feedback(self, fdbk):
        if isinstance(fdbk, AttemptResponse):
            logger.debug("Processing Attempt response: %s" % str(fdbk))
            self.state['total_attempts'] = self.state['total_attempts'] + 1
            if fdbk.is_correct:
                self.state['total_success'] = self.state['total_success'] + 1
        if isinstance(fdbk, HintResponse):
            logger.debug("Processing Hint Request response: %s" % str(fdbk))

    def calc_expectancy(self, action, cntxt):
        logger.debug("Calculating expectancy for action: %s" % str(action))
        if action == Attempt:
            self_eff = self.calc_self_eff()
            # Adjust expectancy for each hint
            total_hints = cntxt.hints_used + cntxt.hints_avail
            hint_exp = cntxt.hints_used / total_hints
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
            return self.attributes['values']['attempt']
        elif action == Guess:
            if cntxt.learner_kc_knowledge:
                return self.attributes['values']['guess']
            else:
                return 2*self.attributes['values']['guess']
        elif action == HintRequest:
            if cntxt.learner_kc_knowledge:
                return 0.25*self.attributes['values']['hint request']
            else:
                return self.attributes['values']['hint request']
        elif action == OffTask:
            return self.attributes['values']['off task']
        else:
            return 0

    def calc_self_eff(self):
        ''' 
        Self-efficacy is [0,1]. Self-efficacy is calculated as the success rate on prior attempts.
        An initial self-efficacy ratio is defined per student and is comparable to a success rate
        over the past 100 prior attempts

        '''
        init_attempts = 1000
        init_success = self.attributes['self_eff'] * init_attempts
        self_eff = (init_success + self.state['total_success']) / (init_attempts + self.state['total_attempts'])
        return self_eff

    def is_off_task(self):
        return self.state['off_task']

    def has_attempted(self):
        return self.state['attempted']

    def is_diligent(self, action):
        if action == Attempt:
            return True
        elif action == Guess:
            return False
        elif action == HintRequest:
            return True
        elif action == OffTask:
            return False


