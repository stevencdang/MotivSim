# Add project root to python path
import sys
sys.path.append('..')

import logging
import random
from datetime import datetime as dt

from tutor.domain import Domain
from .simulation import Simulation
from tutor.tutor import SimpleTutor
from learner.modular_learner import ModularLearner
from tutor.action import Attempt, HintRequest
from context.context import SimpleTutorContext
from log_db import mongo
from log_db.learner_log import *
from log_db.curriculum_mapper import DB_Curriculum_Mapper

logger = logging.getLogger(__name__)

class ModLearnerSimulation(Simulation):
    
    def __init__(self, domain=None, curric=None, student=None, mastery_thres=0.90):
        super().__init__(domain, curric)
        if student is None:
            logger.warning("No student given. Creating a new student to use in simulation")
            self.student = ModLearnerLearner(domain)
        else:
            self.student = student
        self.tutor = SimpleTutor(self.curric, self.student._id, mastery_thres)
        self.has_started = False

    def next(self):
        # Update Context
        cntxt = SimpleTutorContext(self.tutor.state, self.student.get_state(), self.tutor.session)

        # self.student.update_context(context)

        # Simulate Learner decision & action
        choice, decision = self.student.choose_action(cntxt)
        
        logger.debug("Logging decision: %s" % str(decision.to_dict()))
        logger.debug("******************************************************")
        self.db.decisions.insert_one(decision.to_dict())

        action = self.student.perform_action(choice, cntxt)
        
        logger.debug("Return action: %s" % str(action))
        logged_action = LoggedAction(self.student, action, cntxt.time)
        logger.debug("Logged action: %s" % str(logged_action.to_dict()))
        self.db.actions.insert_one(logged_action.to_dict())

        # Simulate Learning interaction with tutor
        feedback, tx = self.tutor.process_input(action)
        
        if feedback is not None:
            self.student.process_feedback(feedback)
            self.db.tutor_events.insert_one(tx.to_dict())

        # Return true for completing iteration
        return self.tutor.has_more()


    def run(self):
        self.start(dt.now())
        has_next = self.next()
        while has_next:
            has_next = self.next()
        self.end()


