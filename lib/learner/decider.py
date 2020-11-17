# Base class for a learner dicision-making module
# This module is responsible for simulating student decision processse

import uuid
import logging
import random
import numpy as np

from log_db import mongo

from tutor.action import *
from tutor.feedback import *
from log_db.learner_log import *

from .modular_learner_state import ModularLearnerState


logger = logging.getLogger(__name__)

class Decider:

    def __init__(self):
        self.type = "Base Decider"

    def choose(self, choices, state, context):
        pass

    def to_dict(self):
        out = self.__dict__
        return out


class EVDecider(Decider):

    def __init__(self):
        self.type = "EV Decider"
        self.values = {}
        self.self_eff = 0.5
        self.init_values()

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


    def choose(self, choices, state, context):
        # Calc choice distribution
        choice_evs = self.calc_ev(choices, state, context)
        total_ev = np.sum([val['ev'] for val in choice_evs.values()])
        pev = [choice_evs[choice.__name__]['ev']/total_ev for choice in choices]
        
        # Make choice
        choice = random.choices(choices, weights=pev, k=1)[0]

        return choice, {"choice_evs": choice_evs, "pev": pev}

    def calc_ev(self, choices, state, context):
        choice_evs = {choice.__name__:
                      {'expectancy': self.calc_expectancy(choice, state, context),
                       'value': self.calc_value(choice, state, context),
                       'ev': self.calc_expectancy(choice, state, context),
                      }
              for choice in choices
        }
        return choice_evs


    def calc_expectancy(self, action, state, context):
        logger.debug("Calculating expectancy for action: %s" % str(action))
        if action == Attempt:
            self_eff = self.calc_self_eff(state, context)
            # Adjust expectancy for each hint
            total_hints = context.hints_used + context.hints_avail
            hint_exp = context.hints_used / total_hints
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

    def calc_value(self, action, state, context):
        logger.debug("Calculating value for action: %s" % str(action))
        if action == Attempt:
            return self.values['attempt']
        elif action == Guess:
            if context.learner_kc_knowledge:
                return self.values['guess']
            else:
                return 2*self.values['guess']
        elif action == HintRequest:
            if context.learner_kc_knowledge:
                return 0.25*self.values['hint request']
            else:
                return self.values['hint request']
        elif action == OffTask:
            return self.values['off task']
        else:
            return 0

    def calc_self_eff(self, state, context):
        ''' 
        Self-efficacy is [0,1]. Self-efficacy is calculated as the success rate on prior attempts.
        An initial self-efficacy ratio is defined per student and is comparable to a success rate
        over the past 100 prior attempts

        '''
        init_attempts = 1000
        init_success = self.self_eff * init_attempts
        self_eff = (init_success + state.total_success) / (init_attempts + state.total_attempts)
        return self_eff

    
    def to_dict(self):
        out = super().to_dict()
        out['values'] = self.values
        out['self_eff'] = self.self_eff
        return out

class DiligentDecider(Decider):

    def __init__(self, ev_decider, dil=None):
        self.type = "Diligent EV Decider"
        self.ev_decider = ev_decider
        if dil is None:
            self.diligence = random.gauss(2,.3)
            if self.diligence <= 0:
                self.diligence = 0.1
        else:
            self.diligence = dil

    def choose(self, choices, state, context):
        # Get base choice distribution
        choice_evs = self.ev_decider.calc_ev(choices, state, context)
        # Adjust ev for diligent actions
        for choice in choices:
            if self.is_diligent(choice):
                choice_evs[choice.__name__]['ev'] = self.diligence * choice_evs[choice.__name__]['ev']

        # Calc choice distribution
        total_ev = np.sum([val['ev'] for val in choice_evs.values()])
        pev = [choice_evs[choice.__name__]['ev']/total_ev for choice in choices]
        
        choice = random.choices(choices, weights=pev, k=1)[0]

        return choice, {"choice_evs": choice_evs, "pev": pev}


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
        out = self.ev_decider.to_dict()
        out['diligence'] = self.diligence
        return out

