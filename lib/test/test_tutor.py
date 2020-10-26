# Script to test a tutor
# Add project root to python path
import sys
sys.path.append('..')

import logging
import random

from tutor.domain import Domain
from tutor.simple_curriculum import SimpleCurriculum
from tutor.tutor import SimpleTutor
from tutor.action import Attempt, HintRequest
from learner.selfeff_learner import SelfEfficacyLearner
from context.context import SimpleTutorContext

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger("main")


if __name__ == "__main__":
    logger.info("**** Generating a new curriculum ****")
    logger.info("Generating a new domain")
    domain = Domain()
    domain_size = 50
    domain.generate_kcs(domain_size)

    logger.info("Generating Curriculum with domain")
    curric = SimpleCurriculum(domain)
    curric.generate(1, 3, 20)

    logger.info("Initializing Tutor with new curriculum")
    test_stu = SelfEfficacyLearner(domain)
    mastery_thres=0.9
    tutor = SimpleTutor(curric, test_stu._id, mastery_thres)
    # Testing session login/logout
    tutor.start_new_session()
    tutor.end_session()
    tutor.end_session()
    tutor.start_new_session()
    tutor.start_new_session()
    tutor.end_session()

    # Testing domain model
    tutor.start_new_session()

    while tutor.has_more():
        context = SimpleTutorContext(tutor.state, test_stu.state, tutor.session)

        test_stu.update_context(context)

        # Simulate Learner decision & action
        action = test_stu.choose_action()
        act = test_stu.perform_action(action)
        
        # Simulate Learning interaction with tutor
        feedback = tutor.process_input(act)
        
        if feedback is not None:
            test_stu.process_feedback(feedback)

    tutor.end_session()

