# Script to test a simulation
# Add project root to python path
import sys
sys.path.append('..')

import logging
import random

from tutor.domain import Domain
from tutor.curriculum import SimpleCurriculum
from tutor.tutor import SimpleTutor
from tutor.action import Attempt, HintRequest
from simulate.simple_tutor_simulation import SimpleTutorSimulation

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger("main")


if __name__ == "__main__":
    logger.info("**** Testing SimpleTutorSimulation ****")
    domain = SimpleTutorSimulation.gen_domain(30)
    curric = SimpleTutorSimulation.gen_curriculum(domain, 1, 3, 20)
    num_students = 2
    for i in range(num_students):
        logger.info("Simulating student #%i" % i)
        sim = SimpleTutorSimulation(domain, curric, None)
        sim.run()
