# Base class for a module based learner

import uuid
import logging
import random

from log_db import mongo

from .learner import Learner
from tutor.action import *
from tutor.feedback import *
from log_db.learner_log import *


logger = logging.getLogger(__name__)


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
        self.attributes['min_off_task'] = 30 # 30 sec
        self.attributes['max_off_task'] = 1800 # 30 minutes
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
            time = random.gauss(kc.m_time, kc.sd_time)
            # Lazy fiz to truncate gaussian
            if time < 0.25:
                logger.debug("Action performed was less than 0.25 secs, channging to 0.25 sec")
                time = 0.25 

            is_correct = self.cog.produce_answer(action, cntxt)
            self.state['attempted'] = True
            # Make is_correct default to True to change later
            act = Attempt(time, is_correct)
            
        elif action == HintRequest:
            time = random.gauss(self.attributes['mean_hint_time'], self.attributes['sd_hint_time'])
            # Lazy fiz to truncate gaussian
            if time < 0.25:
                logger.debug("Action performed was less than 0.25 secs, channging to 0.25 sec")
                time = 0.25 

            act = HintRequest(time)
        elif action == Guess:
            is_correct = self.cog.produce_answer(action, cntxt)
            time = random.gauss(self.attributes['mean_guess_time'], self.attributes['sd_guess_time'])
            # Lazy fiz to truncate gaussian
            if time < 0.25:
                logger.debug("Action performed was less than 0.25 secs, channging to 0.25 sec")
                time = 0.25 
            act = Guess(time, is_correct)
        elif action == OffTask:
            time = random.uniform(self.attributes['min_off_task'], self.attributes['max_off_task'])
            act = OffTask(time)
        elif action == StopWork:
            time = 0
            act = StopWork(time)
        else:
            act = None


        if cntxt.attempt == 0:
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

    def to_dict(self):
        # self.skills = copy.deepcopy(self.cog.skills)
        d = super().to_dict()
        d['cog'] = self.cog.to_dict()
        d['decider'] = self.decider.to_dict()
        # self.skills = self.cog.skills

        return d
    
