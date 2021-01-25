# Base class for a learner cognition module
# This module is responsible for simulating student responses to questions

import uuid
import logging
import random
import copy

from log_db import mongo
from log_db.domain_mapper import DBDomainMapper

from tutor.action import *
from tutor.feedback import *


logger = logging.getLogger(__name__)

class Cognition:

    def __init__(self, domain):
        self.domain_id = domain._id
        self.type = type(self).__name__
        self.skills = {}
        self.init_skills(domain)
        logger.debug(f"Init {self.type} module")

    def init_skills(self, domain):
        pass

    def produce_answer(self):
        pass

    def practice_skill(self, skill):
        pass

    def is_skill_mastered(self, skill):
        pass

    def to_dict(self):
        d = copy.deepcopy(self.__dict__)
        return d

    def update_with_dict(self, d):
        self.domain_id = d['domain_id']
        self.type = d['type']
        self.skills = d['skills']

    @staticmethod
    def from_dict(d):
        mod_type = getattr(sys.modules[__name__], d['type'])
        out = mod_type()
        for key in d.keys():
            try:
                setattr(out, key, d[key])
            except Exception as e:
                logger.error(f"Issue setting attributes of new module isntance: {str}")
        return out


class BinarySkillCognition(Cognition):

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

                
    def produce_answer(self, action, cntxt):
        kc = cntxt.kc
        logger.debug("Action is %s" % str(action))

        if action == Attempt:
            if self.is_skill_mastered(kc):
                weights = [(1 - kc.ps), kc.ps]
            else:
                # Adjust prob(correct) depending on number of hints avail
                total_hints = cntxt.hints_used + cntxt.hints_avail
                hint_exp = cntxt.hints_used / total_hints
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


class PCorSkillCognition(Cognition):

    def __init__(self, domain):
        super().__init__(domain)

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

                
    def produce_answer(self, action, cntxt):
        kc = cntxt.kc
        logger.debug("Action is %s" % str(action))
        skllvl = self.skills[kc._id]

        if action == Attempt:
            # if self.is_skill_mastered(kc):
                # weights = [(1 - kc.ps), kc.ps]
            # else:
                # Adjust prob(correct) depending on number of hints avail
            total_hints = cntxt.hints_used + cntxt.hints_avail
            hint_exp = cntxt.hints_used / total_hints
            pcor = skllvl + (1 - skllvl) * hint_exp
            weights = [pcor, (1 - pcor)]
            
            # Same chance of producing an answer as producing a correct answer
            has_answer = random.choices([True, False], weights=weights, k=1)[0]
            if has_answer:
                is_correct = random.choices([True, False], weights=weights, k=1)[0]
            else:
                is_correct = None
                
            
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


class BiasSkillCognition(PCorSkillCognition):
    

    def __init__(self, domain, ability):
        
        # Set Ability paramter before calling super because skills are initialized in the super class
        if (ability > 1) or (ability < -1):
            raise Exception(f"ability must be a number [-1,1]. Given {ability}")
        else:
            self.ability = ability

        super().__init__(domain)

    def init_skills(self, domain):
        def get_init_skill_level(skl):
            # Use default if domain model doesn't specific variance of pl0
            if hasattr(skill, "pl0_sd"):
                skl_sd = skill.pl0_sd
            else:
                skl_sd = 0.1

            mu = skill.pl0 - self.ability * 2 * skl_sd
            
            pl0 = -1
            logger.debug(f"Initialiing skill with mean {mu} and sd {skl_sd}")
            while not ((pl0 >=0) and (pl0 <=1)):
                pl0 = random.normalvariate(mu, skl_sd)
            return pl0

        for skill in domain.kcs:
            self.skills[skill._id] = get_init_skill_level(skill)
            logger.debug(f"Initial Skill level {skill._id}:\t{self.skills[skill._id]}")

