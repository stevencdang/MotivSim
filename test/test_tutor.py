# Script to test a tutor
# Add project root to python path
import sys
sys.path.append('..')

import logging
import random

from tutor.domain import Domain
from tutor.curriculum import SimpleCurriculum
from tutor.tutor import SimpleTutor
from tutor.action import Attempt, HintRequest

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
    test_stu = "test_id"
    tutor = SimpleTutor(curric, test_stu)
    # Testing session login/logout
    tutor.start_new_session()
    tutor.end_session()
    tutor.end_session()
    tutor.start_new_session()
    tutor.start_new_session()
    tutor.end_session()

    # Testing domain model
    tutor.start_new_session()
    has_unit = tutor.set_next_unit()
    unum = 0
    while has_unit:
    
        logger.debug("$$$$$$$$$$$$$$$$$$$$$********** Unit %i *********$$$$$$$$$$$$$$$$$$$$$$" % unum)
        has_section = tutor.set_next_section() 
        snum = 0
        while has_section:
            logger.debug("##########********** Section %i *********###########" % snum)
            has_prob = tutor.get_next_prob()
            pnum = 0
            while has_prob:
                logger.debug("********** Problem input %i *********" % pnum)
                # action = 
                # tutor.process_input(action)
                # tutor.process_input(action)
                # tutor.process_input(action)
                # tutor.process_input(action)
                kc = tutor.state.step.kcs[0]
                plt = tutor.state.mastery[kc]
                result = random.choices([True, False], weights=[plt, (1-plt)], k=1)
                if result:
                    action = Attempt(12, result)
                else:
                    a1 = Attempt(12, result)
                    a2 = HintRequest(15)
                logger.debug("User action is correct?: %s" % str(result))
                tutor.process_input(action)
                has_prob = tutor.get_next_prob()
                pnum = pnum + 1
            has_section = tutor.set_next_section()
            snum = snum + 1
        has_unit = tutor.set_next_unit()
        unum = unum + 1

    tutor.end_session()

