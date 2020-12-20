# Class for a binary skill learner cognition module
# This module is responsible for simulating student responses to questions

import uuid
import logging
import random

from log_db import mongo
from tutor.action import *
from tutor.feedback import *

from .modular_learner_state import ModularLearnerState
from .cognition import Cognition


logger = logging.getLogger(__name__)

class BinarySkillCognition(Cognition):

    def __init__(self, domain):
        super().__init__(domain)
        logger.debug("Init Binary Skill Cognition")
        self.init_skills(domain)


    def init_skills(self, domain):
        for skill in domain.kcs:
            self.skills[skill._id] = random.choices([True, False], weights=[skill.pl0, (1-skill.pl0)], k=1)[0]

            
    def practice_skill(self, skill):
        # Update skill
        if self.is_skill_mastered(skill):
            logger.debug("Skill is already mastered. No update necessary")
        else:
            learned = random.choices([True, False], weights=[skill.pt, (1-skill.pt)], k=1)[0]
            logger.debug("Probability of learning skill: %f\t learned?: %s" % (skill.pt, str(learned)))
            # Update skill if learned
            if learned:
                self.skills[skill._id] = learned

                
    def produce_answer(self, action, context):
        kc = context.kc
        logger.debug("Action is %s" % str(action))

        if action == Attempt:
            if self.is_skill_mastered(kc):
                weights = [(1 - kc.ps), kc.ps]
            else:
                # Adjust prob(correct) depending on number of hints avail
                total_hints = context.hints_used + context.hints_avail
                hint_exp = context.hints_used / total_hints
                pg = kc.pg + (1 - kc.pg) * hint_exp
                weights = [pg, (1 - pg)]
            is_correct = random.choices([True, False], weights=weights, k=1)[0]
            
        elif action == Guess:
            weights = [0.01, 0.99]
            is_correct = random.choices([True, False], weights=weights, k=1)[0]

        else:
            raise Exception(f"Can't produce answer for action: {action.__name__}")

        return is_correct


    def is_skill_mastered(self, skill):
        return self.skills[skill._id] 

