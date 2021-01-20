# Class for a P(correct) skill learner cognition module
# This module respresents learner skill as a probability of correctness
# Learning is modelled as a linear increase in P(cor) given practice opportunity

import uuid
import logging
import random

from log_db import mongo
from tutor.action import *
from tutor.feedback import *

from .modular_learner_state import ModularLearnerState
from .cognition import Cognition


logger = logging.getLogger(__name__)

class PCorSkillCognition(Cognition):

    def __init__(self, domain):
        super().__init__(domain)
        logger.debug("Init P(correct) Skill Cognition")
        self.init_skills(domain)


    def init_skills(self, domain):
        def get_skill_level(skl):
            # Use default if domain model doesn't specific variance of pl0
            if hasattr(skill, "pl0_sd"):
                skl_sd = skill.pl0_sd
            else:
                skl_sd = 0.1
            while not ((pl0 >=0) and (pl0 <=1)):
                pl0 = random.normalvariate(skill.pl0, skl_sd)
            return pl0

        for skill in domain.kcs:
            self.skills[skill._id] = get_skill_level(skill)

            
    def practice_skill(self, skill):
        # Update skill
        if self.is_skill_mastered(skill):
            logger.debug("Skill is already mastered. No update necessary")
        else:
            # Treating pt as the linear slope coefficient
            plt1 = self.skills[skill._id] + skill.pt
            if plt1 > 1:
                self.skills[skill._id] = 1
            else:
                self.skills[skill._id] = plt1

                
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
        if self.skills[skill._id] == 1:
            return True
        else:
            return False

