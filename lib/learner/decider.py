# Base class for a learner dicision-making module
# This module is responsible for simulating student decision processse

import sys
import uuid
import logging
import random
import copy
import numpy as np


from log_db import mongo

from tutor.action import *
from tutor.feedback import *
from log_db.learner_log import *


logger = logging.getLogger(__name__)

class Decider:

    def __init__(self):
        self.type = type(self).__name__
        logger.debug(f"Init {self.type} module")

    def choose(self, choices, state, cntxt):
        pass

    def __str__(self):
        return str(self.to_dict())

    def to_dict(self):
        out = copy.deepcopy(self.__dict__)
        return out

    def start_working(self, max_t):
        # Default to start working immediately
        return 0

    @staticmethod
    def from_dict(d):
        dec_type = getattr(sys.modules[__name__], d['type'])
        out = dec_type()
        for key in d.keys():
            try:
                setattr(out, key, d[key])
            except Exception as e:
                logger.error(f"Issue setting attributes of new module isntance: {str}")
        return out

class EVDecider(Decider):

    def __init__(self):
        super().__init__()
        self.values = {}
        self.self_eff = 0.5
        self.init_values()

    def init_values(self):
        atv = 10
        gsv = 0.25*atv
        hrv = 3
        otv = 0.01

        self.values = {
            'attempt': atv,
            'guess': gsv,
            'hint request': hrv,
            'off task': otv
        }


    def choose(self, choices, state, cntxt):
        # Calc choice distribution
        choice_evs = self.calc_ev(choices, state, cntxt)
        total_ev = np.sum([val['ev'] for val in choice_evs.values()])
        pev = [choice_evs[choice.__name__]['ev']/total_ev for choice in choices]
        
        # Make choice
        choice = random.choices(choices, weights=pev, k=1)[0]

        return choice, {"choice_evs": choice_evs, "pev": pev}

    def calc_ev(self, choices, state, cntxt):
        choice_evs = {}
        for choice in choices:
            expt = self.calc_expectancy(choice, state, cntxt)
            val = self.calc_value(choice, state, cntxt)
            choice_evs[choice.__name__] = {'expectancy': expt,
                                           'value': val,
                                           'ev':  expt*val
                                          }
            # logger.info(f"Exptancy: {expt}\tVal: {val}\t EV: {expt*val}")
            # logger.info(f"Choice EVS: {choice_evs}")
        return choice_evs


    def calc_expectancy(self, action, state, cntxt):
        logger.debug("Calculating expectancy for action: %s" % str(action))
        if action == Attempt:
            self_eff = 0.5
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
            return 0.1
        elif action == HintRequest:
            if cntxt.hints_avail == 0:
                return 0
            else:
                return 1
        elif action == OffTask:
            return 1
        elif action == StopWork:
            return 1
        else:
            return 0

    def calc_value(self, action, state, cntxt):
        logger.debug("Calculating value for action: %s" % str(action))
        if action == Attempt:
            return self.values['attempt']
        elif action == Guess:
            if cntxt.learner_kc_knowledge:
                return self.values['guess']
            else:
                return 2*self.values['guess']
        elif action == HintRequest:
            if cntxt.learner_kc_knowledge:
                return 0.25*self.values['hint request']
            else:
                # Adjust value for each hint
                total_hints = cntxt.hints_used + cntxt.hints_avail
                hint_val = cntxt.hints_avail / total_hints
                return self.values['hint request'] * hint_val
        elif action == OffTask:
            return self.values['off task']
        elif action == StopWork:
            tt_end = abs((cntxt.session.end - cntxt.time).total_seconds())
            mean_stop = 3 * 60
            base_val = 1 #0.5*self.values['attempt']
            # logger.info(f"Stop Work Value: { (base_val*mean_stop)/tt_end }\tTime to end: {cntxt.session.end - cntxt.time}")
            return ((base_val*mean_stop)/tt_end) ** 2
        else:
            return 0


class DiligentDecider(Decider):

    def __init__(self, ev_decider, dil=None, ot_min_sd=60, ot_max_sd=300, ot_mean_sd=20):
        super().__init__()
        self.ev_decider = ev_decider
        if dil is None:
            self.diligence = random.gauss(0,2)
        else:
            self.diligence = dil

        self.ot_min_sd = ot_min_sd
        self.ot_max_sd = ot_max_sd
        self.ot_mean_sd = ot_mean_sd

    def choose(self, choices, state, cntxt):
        # Get base choice distribution
        choice_evs = self.ev_decider.calc_ev(choices, state, cntxt)
        # Adjust ev for diligent actions
        for choice in choices:
            if self.is_diligent(choice, state, cntxt):
                dil = self.diligence
                w = dil + 1 if dil > 0 else dil - 1
                w = 1 + (w / 10)
                # Diligence is a constant adjustment on desired over undesired actions. 

                # This is should be reconsidered based on theory
                choice_evs[choice.__name__]['ev'] = w * choice_evs[choice.__name__]['ev']

                # if self.diligence < 0:
                    # choice_evs[choice.__name__]['ev'] = 1/(-self.diligence) * choice_evs[choice.__name__]['ev']
                # else:
                    # choice_evs[choice.__name__]['ev'] = self.diligence * choice_evs[choice.__name__]['ev']

        pev = []

        # Calc choice distribution
        if np.sum([val['ev'] > 0 for val in choice_evs.values()]) > 0:
            # There is at least 1 postive EV, choose most valued action
            total_ev = np.sum([val['ev'] for val in choice_evs.values() if val['ev'] > 0])
            for choice in choices:
                if choice_evs[choice.__name__]['ev'] > 0:
                    pev.append(choice_evs[choice.__name__]['ev']/total_ev)
                else:
                    pev.append(0)

        else:
            # reverse order of negative costs
            logger.warning(f"Have negative costs. Diligence: {self.diligence}")
            vals = [val['ev'] for val in choice_evs.values()]
            total_ev = abs(np.sum(vals))
            ev_min  = np.min(vals)
            ev_max = np.max(vals)
            offset = ev_min + ev_max
            # for choice in choices:
                # pev.append(choice_evs[choice.__name__]['ev']/total_ev)
            pev = [(choice_evs[choice.__name__]['ev'] - offset)/total_ev for choice in choices]



        # pev = [choice_evs[choice.__name__]['ev']/total_ev if choice_evs[ for choice in choices]
        
        choice = random.choices(choices, weights=pev, k=1)[0]

        if choice == StopWork:
            logger.debug(f"Choosing to stop. Choice_EVs: {choice_evs}\tP(EV): {str(pev)}")
            # logger.warning(f"Choosing to stop. Diligence: {self.diligence}\t") 
        return choice, {"choice_evs": choice_evs, "pev": pev}


    def is_diligent(self, action, state, cntxt):
        if action == Attempt:
            return True
        elif action == Guess:
            return False
        elif action == HintRequest:
            return True
        elif action == OffTask:
            return False
        elif action == StopWork:
            return ((cntxt.session.end - cntxt.time).total_seconds() < 300) # 5 minutes

    def start_working(self, max_t):
        mean_start = 5*60 # 5 minutes
        if max_t*60 < mean_start:
            mean_start = max_t
        #Rescale diligence to standard deviations
        w = self.diligence / 2

        mu = mean_start - 2*(w * 60)
        if mu < 0.1:
            mu = 0.1
        sd = 180 - (w * 60)
        if sd <= 0.1:
            sd = 0.1
        delay = -1
        while (delay < 0) or (delay > max_t):
            delay = np.random.normal(mu, sd)

        logger.debug(f"Diligence: {self.diligence}\t max_t: {max_t/60}\tmu: {mu/60}\tsd: {sd/60}\tdelay: {delay/60}")
        return delay

    def get_offtask_time(self, attr):
        if self.diligence < 0:
            dil = self.diligence
        else:
            dil = self.diligence
        ot_min = attr['min_off_task'] - dil * self.ot_min_sd if dil < 0 else attr['min_off_task'] - dil * self.ot_min_sd /4
        if ot_min < 0:
            ot_min = 10
        ot_max = attr['max_off_task'] - dil * self.ot_max_sd if dil < 0 else attr['max_off_task'] - dil * self.ot_max_sd /4
        ot_mean = attr['mean_off_task'] - dil * self.ot_mean_sd if dil < 0 else attr['mean_off_task'] - dil * self.ot_mean_sd /4
        if ot_mean < 0:
            ot_mean = ot_min 
        ot_sd = (ot_max - ot_mean) / 3
        time = -1
        while (time < ot_min) or (time > ot_max):
            time = random.gauss(ot_mean, ot_sd)
        return time



    def to_dict(self):
        out = self.ev_decider.to_dict()
        out['diligence'] = self.diligence
        return out


class RandValDecider(EVDecider):
    
    def __init__(self):
        super().__init__()

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

class DomainSelfEffDecider(EVDecider):
    
    def __init__(self, self_eff=None):
        super().__init__()
        self.self_eff = 0.5
        self.init_self_eff(self_eff)

    def init_self_eff(self, self_eff):
        if self_eff is not None:
            se = self_eff
        else:
            se = -1
            while (se <= 0) or (se >= 1):
                se = random.gauss(0.5, 0.2)

        self.self_eff = se

    def calc_self_eff(self, state, cntxt):
        ''' 
        Self-efficacy is [0,1]. Self-efficacy is calculated as the success rate on prior attempts.
        An initial self-efficacy ratio is defined per student and is comparable to a success rate
        over the past 100 prior attempts

        '''
        init_attempts = 1000
        init_success = self.self_eff * init_attempts
        self_eff = (init_success + state['total_success']) / (init_attempts + state['total_attempts'])
        return self_eff

    def calc_expectancy(self, action, state, cntxt):
        logger.debug("Calculating expectancy for action: %s" % str(action))
        if action == Attempt:
            self_eff = self.calc_self_eff(state, cntxt)
            # Adjust expectancy for each hint
            total_hints = cntxt.hints_used + cntxt.hints_avail
            hint_exp = cntxt.hints_used / total_hints
            exp = self_eff + (1 - self_eff) * hint_exp
            return exp
        else:
            return super().calc_expectancy(action, state, cntxt)

class MathInterestDecider(DomainSelfEffDecider):

    def __init__(self, self_eff=None, interest=None):
        super().__init__(self_eff)
        if interest is not None:
            self.interest = interest
        else:
            self.interest = random.gauss(0, 1)
            w = 2
            self.values['attempt'] = self.values['attempt'] + w*self.interest


class DomainTunerDecider(EVDecider):

    def choose(self, choices, state, cntxt):
        # Calc choice distribution
        choice_evs = self.calc_ev(choices, state, cntxt)
        total_ev = np.sum([val['ev'] for val in choice_evs.values()])
        pev = [choice_evs[choice.__name__]['ev']/total_ev for choice in choices]
        
        # Force choice as attempt
        choice = Attempt
        # while choice != Attempt:
            # choice = random.choices(choices, weights=pev, k=1)[0]


        return choice, {"choice_evs": choice_evs, "pev": pev}

