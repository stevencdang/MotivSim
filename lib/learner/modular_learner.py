# Base class for a module based learner

import uuid
import logging
import random
import pickle
import dill

import pandas as pd

from log_db import mongo

from .learner import Learner
from tutor.action import *
from tutor.feedback import *
from log_db.learner_log import *


logger = logging.getLogger(__name__)
# logger.setLevel(logging.DEBUG)


class ModularLearner(Learner):

    def __init__(self, domain, cog, decider):
        super().__init__(domain)

        # State variables
        self.state['off_task'] = False
        self.state['attempted'] = False
        self.state['total_attempts'] = 0
        self.state['total_success'] = 0
       
        # Cognitive Module
        self.cog = cog
        # Overrride skills attribute to referece to skills within cognitive module
        self.skills = self.cog.skills
        
        # Motivation/Decision-making model
        self.decider = decider

        # Learner Specific attributes
        self.attributes['min_off_task'] = 90 # 30 sec
        self.attributes['max_off_task'] = 600 # 10 minutes
        self.attributes['mean_off_task'] = 300
        self.attributes['mean_hint_time'] = 5 # seconds
        self.attributes['sd_hint_time'] = 1.5 # seconds
        self.attributes['mean_guess_time'] = 3 # seconds
        self.attributes['sd_guess_time'] = 1 # seconds


    def practice_skill(self, skill):
        # Override base skill practice to force cog module to manage skills
        # Update skill
        self.cog.practice_skill(skill)
        # self.skills = self.cog.skills
        
    def choose_action(self, cntxt):
        actions = cntxt.get_actions()
        choice, choice_criteria = self.decider.choose(actions, self.state, cntxt) ########## Review this line for self.state ############
        decision = Decision(self, choice.__name__, cntxt.time, choice_criteria['choice_evs'], choice_criteria['pev'], cntxt)

        # logger.debug("Logging decision: %s" % str(decision.to_dict()))
        # logger.debug("******************************************************")
        # self.db.decisions.insert_one(decision.to_dict())

        logger.debug("Choosing action: %s" % str(choice))
        return choice, decision

    def perform_action(self, action, cntxt):
        kc = cntxt.kc
        logger.debug("Action is %s" % str(action))
        if action == Attempt:
            act = self.make_attempt(cntxt)
        elif action == HintRequest:
            time = 0
            m = cntxt.kc.m_time / 2
            sd = cntxt.kc.sd_time / 2
            loops = 0
            while (time < 1) and (loops < 50):
                time = random.gauss(m, sd)
                loops += 1
                if loops == 50:
                    time = 1
            act = HintRequest(time)
        elif action == Guess:
            is_correct = self.cog.produce_answer(action, cntxt)
            time = 0
            m = cntxt.kc.m_time / 4
            sd = cntxt.kc.sd_time / 4
            loops = 0
            while (time <  1) and (loops < 50):
                time = random.gauss(m, sd)
                loops += 1
                if loops == 50:
                    time = 1
            act = Guess(time, is_correct)
        elif action == OffTask:
            act = self.go_offtask(cntxt)
        elif action == StopWork:
            time = 0
            act = StopWork(time)
        else:
            act = None


        if isinstance(act, Attempt):
            if act.is_correct:
                logger.debug("Skill to update: %s" % str(kc))
                self.practice_skill(kc)

        # logger.debug("Return action: %s" % str(act))
        # logged_action = LoggedAction(self, act, cntxt.time)

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

    def start_working(self, max_t):
        return self.decider.start_working(max_t)

    def make_attempt(self, cntxt):
        time = 0
        loops = 0
        kc = cntxt.kc
        if hasattr(self.decider, 'get_focus'):
            focus = self.decider.get_focus(cntxt)
        else:
            focus = 1

        if hasattr(self.cog, 'get_speed'):
            speed = self.cog.get_speed(cntxt)
        else:
            speed = 1
        while time < 0.25:
            m = kc.m_time #* focus * speed
            time = random.gauss(m, kc.sd_time)
            loops += 1
            if loops > 50:
                logger.debug(f"Setting time to 0.25\tDuration of action mu: {kc.m_time}\tsd: {kc.sd_time}")
                time = 0.25

        is_correct = self.cog.produce_answer(Attempt, cntxt)
        self.state['attempted'] = True

        if is_correct is not None:
            # Make is_correct default to True to change later
            act = Attempt(time, is_correct)
        else:
            act = FailedAttempt(time)

        return act
            

    def go_offtask(self, cntxt):
        if hasattr(self.decider, 'get_offtask_time'):
            time = self.decider.get_offtask_time(self.attributes)
            return OffTask(time)
        else:
            time = -1
            ot_sd = (self.attributes['max_off_task'] - self.attributes['mean_off_task'])/3
            while (time < self.attributes['min_off_task']) or (time > self.attributes['max_off_task']):
                time = random.gauss(self.attributes['mean_off_task'], ot_sd)
            return OffTask(time)
            

    def to_dict(self):
        d = super().to_dict()
        d['cog'] = self.cog.to_dict()
        d['decider'] = self.decider.to_dict()
        d['pickle'] = dill.dumps(self)

        return  d

    def to_dataframe(self, get_state_fields=False, get_attr_fields=False):
        d = self.to_dict()
        # Get decider attributes as student attributes
        for attr in d['decider']['construct_attrs']:
            d[attr] = d['decider'][attr]
       
        # Add cognition attribute as student attribute
        if 'ability' in d['cog'].keys():
            d['cog_ability'] = d['cog']['ability']

        if not get_state_fields:
            for f in d['state_fields']:
                del d[f]
            del d['state_fields']

        if not get_attr_fields:
            for f in d['attribute_fields']:
                del d[f]
            del d['attribute_fields']


        # Remove unnecessary fields
        del d['pickle']
        del d['cog']
        del d['decider']

        return pd.Series(d, name=d['_id'])

    
    @staticmethod
    def from_dict(d):
        return dill.loads(d['pickle'])
