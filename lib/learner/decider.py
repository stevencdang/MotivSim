# Base class for a learner dicision-making module
# This module is responsible for simulating student decision processse

import sys
import uuid
import logging
import random
import copy
import numpy as np
import pickle


from log_db import mongo

from tutor.action import *
from tutor.feedback import *
from log_db.learner_log import *


logger = logging.getLogger(__name__)
# logger.setLevel(logging.DEBUG)

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


class EVDecider(Decider):

    def __init__(self, attr={}, values={}, exp={}, constructs=[]):
        super().__init__()
        self.attr = attr

        if 'mean_start' not in attr:
            self.attr['mean_start'] = 5*60 # 5 minutes
        if 'start_sd' not in attr:
            self.attr['start_sd'] = 300

        self.constructs = {type(c): c for c in constructs}
        self.values = {}
        self.exps = {}
        self.init_values(values)
        self.init_expectancies(exp)

    def init_values(self, values):
        req_vals = {Attempt: lambda s,c: 10,
                    Guess: lambda s,c: 2.5,
                    HintRequest: lambda s,c: 3,
                    OffTask: lambda s,c: 0.05,
                    StopWork: self.get_stop_work_value
                   }

        # Setup required values with defaults if not given
        for v in req_vals:
            if v in values:
                self.values[v] = values[v]
            else:
                self.values[v] = req_vals[v]
       
        # Add all other given values
        for v in values:
            if v not in req_vals:
                self.values[v] = values[v]

    def init_expectancies(self, exp):
        req_exp = {Attempt: lambda s,c: 0.5, 
                   Guess: lambda s,c: 1, 
                   HintRequest: lambda s,c: 1, 
                   OffTask: lambda s,c: 1,
                   StopWork: lambda s,c: 1
                  }
        # Setup required expectancies  with defaults if not given
        for e in req_exp:
            if e in exp:
                self.exps[e] = exp[e]
            else:
                self.exps[e] = req_exp[e]
       
        # Add all other given expectancies
        for e in exp:
            if e not in req_exp:
                self.exps[e] = exp[e]

    def choose(self, choices, state, cntxt):
        # Calc choice distribution
        choice_evs = self.calc_ev(choices, state, cntxt)
        pev = []

        if np.sum([v['ev'] > 0 for v in choice_evs.values()]) > 0:
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
        base_exp = self.exps[action](state, cntxt)
        for c in self.constructs.values():
            base_exp = c.calc_base_exp(base_exp, action, state, cntxt)
        weighted_exp = base_exp
        for c in self.constructs.values():
            weighted_exp = c.calc_weighted_exp(weighted_exp, action, state, cntxt)
        total_exp = weighted_exp
        for c in self.constructs.values():
            total_exp = c.calc_total_exp(total_exp, action, state, cntxt)
        return total_exp
    

    def calc_value(self, action, state, cntxt):
        logger.debug("Calculating value for action: %s" % str(action))
        base = self.values[action](state, cntxt)
        for c in self.constructs.values():
            base = c.calc_base_val(base, action, state, cntxt)
        weighted = base
        for c in self.constructs.values():
            weighted = c.calc_weighted_val(weighted, action, state, cntxt)
        total = weighted
        for c in self.constructs.values():
            total = c.calc_total_val(total, action, state, cntxt)
        return total
    
    def start_working(self, max_t):
        mean_start = self.attr['mean_start']
        if max_t*60 < mean_start:
            mean_start = max_t
        
        w = 1
        for c in self.constructs.values():
            if hasattr(c, 'get_start_speed'):
                w = c.get_start_speed(w)

        mu = mean_start * w
        if mu < 1:
            mu = 1
        sd = self.attr['start_sd']

        delay = -1
        while (delay < 0) or (delay > max_t):
            delay = np.random.normal(mu, sd)

        return delay

    def get_offtask_time(self, attr):
        w = 1
        for c in self.constructs.values():
            if hasattr(c, 'get_offtask_delay'):
                w = c.get_offtask_delay(w)

        ot_min = attr['min_off_task'] * w
        ot_max = attr['max_off_task'] * w
        ot_mean = attr['mean_off_task' ] * w
        ot_sd = (ot_max - ot_mean) / 3
        time = -1
        while (time < ot_min) or (time > ot_max):
            time = random.gauss(ot_mean, ot_sd)
        return time


    def get_stop_work_value(self, state, cntxt):
        tt_end = abs((cntxt.session.end - cntxt.time).total_seconds())
        mean_stop = 3 * 60
        base_val = 1 #0.5*self.values['attempt']
        # logger.info(f"Stop Work Value: { (base_val*mean_stop)/tt_end }\tTime to end: {cntxt.session.end - cntxt.time}")
        return ((base_val*mean_stop)/tt_end) ** 2

    def to_dict(self):
        obj = super().to_dict()
        # do not return expectancies and values as output dict
        del obj["exps"]
        del obj["values"]
        obj['constructs'] = {k.__name__: c.to_dict() for k,c in obj['constructs'].items()}
        obj['construct_attrs'] = []
        for k,c in self.constructs.items():
            for attr, val in vars(c).items():
                name = k.__name__ + "__" + attr
                obj['construct_attrs'].append(name)
                obj[name] = val

        return obj


class DiligentDecider(EVDecider):

    # def __init__(self, ev_decider, dil=None, ot_min_sd=60, ot_max_sd=300, ot_mean_sd=20):
    def __init__(self, attr={}, values={}, exp={}, constructs=[]):
        super().__init__(attr, values, exp, constructs)
        # self.ev_decider = ev_decider

        # Initialize diligence construct if not provided
        if sum([type(c) == Diligence for c in constructs]) == 0:
            if Diligence not in constructs:
                logger.info("Adding Diligence Construct to learner")
                self.constructs[Diligence] = Diligence()
                # self.attr['diligence'] = random.gauss(0,1)

    def get_focus(self, cntxt):
        return 1 - self.constructs[Diligence].diligence / 12
    

class DecisionConstruct:

    def __init__(self, attrs={}):
        for key in attrs:
            setattr(self, key, attrs[key])

    def calc_base_exp(self, val, action, state, cntxt):
        return val

    def calc_weighted_exp(self, val, action, state, cntxt):
        return val

    def calc_total_exp(self, val, action, state, cntxt):
        return val

    def calc_base_val(self, val, action, state, cntxt):
        return val

    def calc_weighted_val(self, val, action, state, cntxt):
        return val

    def calc_total_val(self, val, action, state, cntxt):
        return val

    def to_dict(self):
        out = copy.deepcopy(self.__dict__)
        return out


class Diligence(DecisionConstruct):

    def __init__(self, attrs={}):
        super().__init__(attrs)
        if 'diligence' not in attrs:
            setattr(self, 'diligence',random.gauss(0,1))

    def calc_weighted_val(self, val, action, state, cntxt):
        if action == StopWork:
            dil = self.diligence
            w = dil + 1 if dil > 0 else dil - 1
            w = 1 - (w / 25)
            return w * val
        else:
            if self.is_diligent(action, state, cntxt):
                dil = self.diligence
                w = dil + 1 if dil > 0 else dil - 1
                w = 1 + (w / 10)
                return w * val
            else:
                return val

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
        else:
            return False

    def get_start_speed(self, w):
        return w * (1 + self.diligence / 10)

    def get_offtask_delay(self, w):
        return w * (1 - self.diligence / 16)


class DomainSelfEff(DecisionConstruct):

    def __init__(self, attrs={}):
        super().__init__(attrs)
        if 'self_eff' not in attrs:
            setattr(self, 'self_eff',random.gauss(0,1))

    def calc_weighted_exp(self, val, action, state, cntxt):
        if action == Attempt:
            # w = dil + 1 if dil > 0 else dil - 1
            w = 1 + (self.self_eff / 5)
            new_val = w * val
            if new_val > 1:
                new_val = 1
            return new_val
        else:
            return val


class RandValDecider(EVDecider):
    
    def __init__(self, attr={}, values={}):
        super().__init__(attr, values)

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
    
    def __init__(self, attr={}, values={}):
        super().__init__(attr, values)
        if 'self_eff' not in attr:
            raise KeyError("'self_eff' key not provided in attr dictionary")
        self.self_eff = 0.5
        self.init_self_eff(attr['self_eff'])

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

    # def calc_expectancy(self, action, state, cntxt):
        # logger.debug("Calculating expectancy for action: %s" % str(action))
        # if action == Attempt:
            # b = 0.5
            # se = b * (1 - self.self_eff)
            # self_eff = cntxt.learner_kc_knowledge * se
            # # Adjust expectancy for each hint
            # total_hints = cntxt.hints_used + cntxt.hints_avail
            # hint_exp = cntxt.hints_used / total_hints
            # exp = self_eff + (1 - self_eff) * hint_exp
            # return exp
        # else:
            # return super().calc_expectancy(action, state, cntxt)

    def calc_value(self, action, state, cntxt):
        att_thres = 0.7
        if action == Attempt:
            # E(w) = 3/8, so multiply by inverse so mean attempt value is the same as base model
            se = self.self_eff
            low_se_val = (1-se) * self.values['attempt']
            skl = cntxt.learner_kc_knowledge
            high_se_val = se * (se + 0.5) * self.values['attempt']
            # high_se_val = se * ((1+ 4*(skl-att_thres)/att_thres)*0.5 * self.values['attempt'] + (1+4*(att_thres-skl)/att_thres)*0.5 * self.values['hint request'])
            # if high_se_val < 0:
                # high_se_val = 0
            return low_se_val + high_se_val
        if action == HintRequest:
            se = self.self_eff
            low_se_val = (1-se) * self.values['hint request']
            skl = cntxt.learner_kc_knowledge
            # high_se_val = se * ((1+ 4*(skl-att_thres)/att_thres)*0.5 * self.values['hint request'] + (1+4*(att_thres-skl)/att_thres)*0.5 * self.values['attempt'])
            # if high_se_val < 0:
                # high_se_val = 0
            high_se_val = se * (1.5 - se) * self.values['hint request']
            return low_se_val + high_se_val
        else:
            return super().calc_value(action, state, cntxt)


    def get_stop_work_value(self, state, cntxt):
        tt_end = abs((cntxt.session.end - cntxt.time).total_seconds())
        mean_stop = 3 * 60
        base_val = 1 #0.5*self.values['attempt']
        # logger.info(f"Stop Work Value: { (base_val*mean_stop)/tt_end }\tTime to end: {cntxt.session.end - cntxt.time}")
        return ((base_val*mean_stop)/tt_end) ** 2
        
    # def get_start_speed(self):
        # speed = 1 - self.self_eff / 3
        # return speed

    @staticmethod
    def from_dict(d):
        dec_type = getattr(sys.modules[__name__], d['type'])
        attr = {'self_eff': d['self_eff']}
        out = dec_type(attr=attr)
        for key in d.keys():
            try:
                setattr(out, key, d[key])
            except Exception as e:
                logger.error(f"Issue setting attributes of new module isntance: {str}")
        return out



class MathInterestDecider(EVDecider):

    def __init__(self, attr={}, values={}):
        super().__init__(attr, values)
        if 'interest' in attr:
            self.interest = attr['interest']
        else:
            self.interest = random.gauss(0, 1)
        w = 1 + self.interest / 8
        self.values['attempt'] = self.values['attempt'] * w
        self.values['hint request'] = self.values['hint request'] * w

    def get_start_speed(self):
        speed = 1 - self.interest / 3
        return speed

    def get_offtask_delay(self):
        delay = 1 - self.interest / 3
        return delay

    @staticmethod
    def from_dict(d):
        dec_type = getattr(sys.modules[__name__], d['type'])
        attr = {'interest': d['interest']}
        out = dec_type(attr=attr)
        for key in d.keys():
            try:
                setattr(out, key, d[key])
            except Exception as e:
                logger.error(f"Issue setting attributes of new module isntance: {str}")
        return out



class MathIntSelfEffDecider(MathInterestDecider, DomainSelfEffDecider):


    def __init__(self, attr={}, values={}):
        super().__init__(attr, values)

    def get_start_speed(self):
        speed = 1 - (self.self_eff + self.interest) / 5
        return speed

    def calc_value(self, action, state, cntxt):
        att_thres = 0.7
        if action == Attempt:
            # E(w) = 3/8, so multiply by inverse so mean attempt value is the same as base model
            se = self.self_eff
            low_se_val = (1-se) * self.values['attempt']
            skl = cntxt.learner_kc_knowledge
            high_se_val = se * (se + 0.5) * self.values['attempt']
            # high_se_val = se * ((1+ 4*(skl-att_thres)/att_thres)*0.5 * self.values['attempt'] + (1+4*(att_thres-skl)/att_thres)*0.5 * self.values['hint request'])
            # if high_se_val < 0:
                # high_se_val = 0
            return low_se_val + high_se_val
        if action == HintRequest:
            se = self.self_eff
            low_se_val = (1-se) * self.values['hint request']
            skl = cntxt.learner_kc_knowledge
            # high_se_val = se * ((1+ 4*(skl-att_thres)/att_thres)*0.5 * self.values['hint request'] + (1+4*(att_thres-skl)/att_thres)*0.5 * self.values['attempt'])
            # if high_se_val < 0:
                # high_se_val = 0
            high_se_val = se * (1.5 - se) * self.values['hint request']
            return low_se_val + high_se_val
        else:
            return super().calc_value(action, state, cntxt)

    @staticmethod
    def from_dict(d):
        dec_type = getattr(sys.modules[__name__], d['type'])
        attr = {'interest': d['interest'], 'self_eff': d['self_eff']}
        out = dec_type(attr=attr)
        for key in d.keys():
            try:
                setattr(out, key, d[key])
            except Exception as e:
                logger.error(f"Issue setting attributes of new module isntance: {str}")
        return out




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

