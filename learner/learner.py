# Base class for a learner

import uuid
import logging
import random


logger = logging.getLogger(__name__)


class Learner:

    def __init__(self, domain):
        self._id = uuid.uuid4()
        self.domain_id = domain._id
        self.skills = None

    def practice_skill(self, skill):
        # Update skill
        if self.skills[skill._id]:
            logger.debug("Skill is already mastered. No update necessary")
        else:
            learned = random.choices([True, False], weights=[skill.pt, (1-skill.pt)], k=1)
            logger.debug("Probability of learning skill: %f\t learned?: %s" % (skill.pt, str(learned)))
            # Update skill if learned
            if learned:
                self.skills[skill._id] = learned

    def choose_action(self, actions, context):
        pass

    def perform_action(self, action, context):
        pass

    def update_state(self):
        pass

    def calc_expectancy(self, action, context):
        pass

    def calc_value(self, action, context):
        pass
