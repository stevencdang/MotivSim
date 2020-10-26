# Add project root to python path
import sys
sys.path.append('..')

import logging
import random
from datetime import datetime as dt

from tutor.domain import Domain
from .simulation import Simulation
from tutor.tutor import SimpleTutor
from learner.random_learner import RandomLearner
from tutor.action import OffTask
from context.context import SimpleTutorContext
from log_db import mongo
from log_db.curriculum_mapper import DB_Curriculum_Mapper

logger = logging.getLogger(__name__)

class SimpleTutorSimulation(Simulation):
    
    def __init__(self, domain=None, curric=None, student=None):
        super().__init__(domain, curric)
        if student is None:
            self.student = RandomLearner(domain)
        else:
            self.student = student
        self.tutor = SimpleTutor(self.curric, self.student._id)
        self.has_started = False

    def next(self):
        # Simulate updating tutor state for input
        logger.debug("*************** Getting next problem *************")
        has_prob = self.tutor.get_next_prob()
        if not has_prob:
            logger.debug("############ ************* Getting next section ************* ############")
            has_section = self.tutor.set_next_section()
            if not has_section:
                logger.debug("$$$$$$$$$$$$$$$$$$ ************* Getting next unit ************* $$$$$$$$$$$$$$$$$$$$")
                has_unit = self.tutor.set_next_unit()
                if not has_unit:
                    # No additional content to simulate
                    logger.debug("No additional content to simulate")
                    return False

        # Update Context
        context = SimpleTutorContext(self.tutor.state, self.student.state, self.tutor.session)

        self.student.update_context(context)

        # Simulate Learner decision
        action = self.student.choose_action()
        act = self.student.perform_action(action)
        
        # Simulate Learning interaction with tutor
        self.tutor.process_input(act)
        has_prob = self.tutor.get_next_prob()

        # Return true for completing iteration
        return True


    def run(self):
        self.start(dt.now())
        has_next = self.next()
        while has_next:
            has_next = self.next()
        self.end()


