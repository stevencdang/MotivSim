# Add project root to python path
import sys
sys.path.append('..')

import logging
import random
from datetime import datetime as dt

from tutor.domain import Domain
from .simulation import Simulation
from tutor.tutor import SimpleTutor
from learner.selfeff_learner import SelfEfficacyLearner
from learner.random_learner import RandomLearner
from tutor.action import Attempt, HintRequest
from context.context import SimpleTutorContext
from log_db import mongo
from log_db.curriculum_mapper import DB_Curriculum_Mapper

logger = logging.getLogger(__name__)

class SelfEffSimulation(Simulation):
    
    def __init__(self, domain=None, curric=None, student=None, mastery_thres=0.90):
        super().__init__(domain, curric)
        if student is None:
            logger.warning("No student given. Creating a new student to use in simulation")
            self.student = SelfEfficacyLearner(domain)
        else:
            self.student = student
        self.tutor = SimpleTutor(self.curric, self.student._id, mastery_thres)
        self.has_started = False

    def next(self):
        # Update Context
        context = SimpleTutorContext(self.tutor.state, self.student.state, self.tutor.session)

        self.student.update_context(context)

        # Simulate Learner decision & action
        action = self.student.choose_action()
        act = self.student.perform_action(action)
        
        # Simulate Learning interaction with tutor
        feedback = self.tutor.process_input(act)
        
        if feedback is not None:
            self.student.process_feedback(feedback)

        # Return true for completing iteration
        return self.tutor.has_more()


    def run(self):
        self.start(dt.now())
        has_next = self.next()
        while has_next:
            has_next = self.next()
        self.end()


