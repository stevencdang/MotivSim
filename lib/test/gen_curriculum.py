# Script to generate a new curriculum
# Add project root to python path
import sys
sys.path.append('..')

import logging

from tutor.domain import Domain
from tutor.simple_curriculum import SimpleCurriculum

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger("main")

def check_simple_curric(curric):
    logger.info("Curriculum id: %s" % curric._id)
    logger.info("Number of units: %i" % len(curric.units))
    logger.info("Number of kcs in the domain: %i" % len(curric.domain.kcs))
    for unit in curric.units:
        logger.info("****** Unit with id, %s, has %i sections ******" % (unit._id, len(unit.sections)))
        logger.info("Number of kcs: %i" % len(unit.kcs))
        for section in unit.sections:
            logger.info("** Section with id, %s, has %i problems **" % (section._id, len(section.problems)))
            logger.info("Number of kcs: %i" % len(section.kcs))




if __name__ == "__main__":
    logger.info("**** Generating a new curriculum ****")
    logger.info("Generating a new domain")
    domain = Domain()
    domain_size = 3000
    domain.generate_kcs(domain_size)

    logger.info("Generating Curriculum with domain")
    curric = SimpleCurriculum(domain)
    curric.generate(20, 5, 30)
    check_simple_curric(curric)
