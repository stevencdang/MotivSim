# Base class for a learner

import uuid
import logging
import random

from log_db import mongo


logger = logging.getLogger(__name__)


class Learner:

    def __init__(self, domain):
        self._id = uuid.uuid4()
        self.domain_id = domain._id
        self.cur_context = None
        self.new_context = False
        self.state = LearnerState()
        self.type = "Generic Learner"

        self.skills = {skill._id: random.choices([True, False], weights=[skill.pl0, (1-skill.pl0)], k=1)[0] for skill in domain.kcs}

        # Initialize connection to database
        self.db_params = mongo.get_db_params()
        self.db = mongo.connect(self.db_params['url'], 
                          self.db_params['port'], 
                          self.db_params['name'], 
                          self.db_params['user'], 
                          self.db_params['pswd'])


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

    def update_context(self, context):
        self.cur_context = context
        self.new_context = True

    def choose_action(self):
        pass

    def perform_action(self):
        pass

    def update_state(self):
        pass

    def calc_expectancy(self, action):
        pass

    def calc_value(self, action):
        pass

    def to_dict(self):
        return {'_id': str(self._id),
                'domain_id': str(self.domain_id),
                'type': self.type,
                'skills': {str(sid): self.skills[sid] for sid in self.skills}
                }


class LearnerState:

    def is_off_task(self):
        return False 

