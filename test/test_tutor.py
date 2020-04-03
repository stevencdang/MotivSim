# Script to test a tutor
# Add project root to python path
import sys
sys.path.append('..')

import logging

from tutor.domain import Domain
from tutor.curriculum import SimpleCurriculum
from tutor.tutor import SimpleTutor

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
    curric.generate(1, 1, 20)

    logger.info("Initializing Tutor with new curriculum")
    test_stu = "test_id"
    tutor = SimpleTutor(curric, test_stu)
