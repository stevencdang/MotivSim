# Script to generate a new curriculum
# Add project root to python path
import sys
sys.path.append('..')

import logging

from tutor.domain import Domain
from tutor.curriculum import SimpleCurriculum

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
    curric.generate(3, 2, 20)
