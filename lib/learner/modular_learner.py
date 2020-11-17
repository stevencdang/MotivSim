# Base class for a module based learner

import uuid
import logging
import random

from log_db import mongo
from tutor.feedback import *

from .learner import Learner
from .modular_learner_state import ModularLearnerState
from tutor.action import *
from tutor.feedback import *
from log_db.learner_log import *


logger = logging.getLogger(__name__)


class ModularLearner(Learner):

    def __init__(self, domain, cog, decider):
        super().__init__(domain)
        self.state = ModularLearnerState()
        self.state.skills = self.skills
        self.type = "Modular Learner"
       
        # Cognitive Module
        self.cog = cog
        
        # Motivation/Decision-making model
        self.decider = decider

        # Learner Specific attributes
        self.min_off_task = 30 # 30 sec
        self.max_off_task = 1200 # 20 minutes
        self.mean_hint_time = 3 # seconds
        self.sd_hint_time = 1 # seconds
        self.mean_guess_time = 3 # seconds
        self.sd_guess_time = 1 # seconds


    def practice_skill(self, skill):
        # Override base skill practice to force cog module to manage skills
        # Update skill
        self.cog.practice_skill(skill)
        self.skills = self.cog.skills
        
    def choose_action(self):
        actions = self.cur_context.get_actions()
        choice, choice_criteria = self.decider.choose(actions, self.state, self.cur_context)
        decision = Decision(self, choice.__name__, self.cur_context.time, choice_criteria['choice_evs'], choice_criteria['pev'], self.cur_context)

        logger.debug("Logging decision: %s" % str(decision.to_dict()))
        logger.debug("******************************************************")
        self.db.decisions.insert_one(decision.to_dict())

        logger.debug("Choosing action: %s" % str(choice))
        return choice


    def perform_action(self, action):
        kc = self.cur_context.kc
        logger.debug("Action is %s" % str(action))
        if action == Attempt:
            time = random.gauss(kc.m_time, kc.sd_time)
            # Lazy fiz to truncate gaussian
            if time < 0:
                logger.debug("Action performed was less than 0 secs, channging to 0 sec")
                time = 0

            is_correct = self.cog.produce_answer(action, self.cur_context)
            self.state.attempted = True
            # Make is_correct default to True to change later
            act = Attempt(time, is_correct)
            
        elif action == HintRequest:
            time = random.gauss(self.mean_hint_time, self.sd_hint_time)
            # Lazy fiz to truncate gaussian
            if time < 0:
                logger.debug("Action performed was less than 0 secs, channging to 0 sec")
                time = 0

            act = HintRequest(time)
        elif action == Guess:
            is_correct = self.cog.produce_answer(action, self.cur_context)
            time = random.gauss(self.mean_guess_time, self.sd_guess_time)
            # Lazy fiz to truncate gaussian
            if time < 0:
                logger.debug("Action performed was less than 0 secs, channging to 0 sec")
                time = 0

            if time < 0.25:
                time = 0.25 
            act = Guess(time, is_correct)
        elif action == OffTask:
            time = random.uniform(self.min_off_task, self.max_off_task)
            # Lazy fiz to truncate gaussian
            if time < 0:
                logger.debug("Action performed was less than 0 secs, channging to 0 sec")
                time = 0

            act = OffTask(time)
        else:
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


    def to_dict(self):
        result = super().to_dict()
        result['min_off_task'] = self.min_off_task
        result['max_off_task'] = self.max_off_task
        result['mean_guess_time'] = self.mean_guess_time
        result['sd_guess_time'] = self.sd_guess_time

        result['cog'] = self.cog.to_dict()
        result['decider'] = self.decider.to_dict()

        result['total_attempts'] = self.state.total_attempts
        result['total_success'] = self.state.total_success
        return result

