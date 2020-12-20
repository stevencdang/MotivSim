# Base class for a learner cognition module
# This module is responsible for simulating student responses to questions

import uuid
import logging
import random

from log_db import mongo
from log_db.domain_mapper import DBDomainMapper

from tutor.feedback import *

from .modular_learner_state import ModularLearnerState


logger = logging.getLogger(__name__)

class Cognition:

    def __init__(self, domain):
        self.domain_id = domain._id
        self.type = type(self).__name__
        self.skills = {skl._id: None for skl in domain.kcs}
        logger.debug("Init base Cognition")

    def produce_answer(self):
        pass

    def practice_skill(self, skill):
        pass

    def is_skill_mastered(self, skill):
        pass

    def to_dict(self):
        return self.__dict__

    def update_with_dict(self, d):
        self.domain_id = d['domain_id']
        self.type = d['type']
        self.skills = d['skills']
