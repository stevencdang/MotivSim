# Base class for a learner

import uuid
import logging
import random
import copy

from log_db import mongo
from tutor.feedback import *


logger = logging.getLogger(__name__)


class Learner:

    def __init__(self, domain):
        self._id = str(uuid.uuid4())
        self.domain_id = domain._id
        self.type = type(self).__name__

        self.skills = {skill._id: random.choices([True, False], weights=[skill.pl0, (1-skill.pl0)], k=1)[0] for skill in domain.kcs}

        self.state = {}
        self.attributes = {}

    def practice_skill(self, skill):
        # Update skill
        
        if self.skills[skill._id]:
            logger.debug("Skill is already mastered. No update necessary")
        else:
            learned = random.choices([True, False], weights=[skill.pt, (1-skill.pt)], k=1)[0]
            logger.debug("Probability of learning skill: %f\t learned?: %s" % (skill.pt, str(learned)))
            # Update skill if learned
            if learned:
                self.skills[skill._id] = learned

    def choose_action(self, cntxt):
        pass

    def perform_action(self, action, cntxt):
        pass

    def process_feedback(self, fdbk):
        if isinstance(fdbk, AttemptResponse):
            logger.debug("Processing Attempt response: %s" % str(fdbk))
        if isinstance(fdbk, HintResponse):
            logger.debug("Processing Hint Request response: %s" % str(fdbk))

    def get_state(self):
        pass

    def calc_expectancy(self, action):
        pass

    def calc_value(self, action):
        pass

    def to_dict(self):
        d = copy.deepcopy(self.__dict__)
        
        # Persist state variables independently
        keys = list(d['state'].keys())
        for key in keys:
            d[key] = d['state'][key]
        d['state_fields'] = keys
        d.pop('state', None)

        # Persist attribute variables as independent keys
        keys = list(d['attributes'].keys())
        for key in keys:
            d[key] = d['attributes'][key]
        d['attribute_fields'] = keys
        d.pop('attributes', None)

        # d['skills'] = {str(sid): self.skills[sid] for sid in self.skills}
        return d
