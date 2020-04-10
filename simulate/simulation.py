# Base classes for running a data simulation
# Add project root to python path
import sys
sys.path.append('..')

import logging
from datetime import datetime as dt

from tutor.domain import Domain
from tutor.curriculum import SimpleCurriculum
from tutor.tutor import Tutor

logger = logging.getLogger(__name__)

class Simulation:
    # Base class

    def __init__(self, domain=None, curric=None):
        if domain is None:
            domain = self.gen_domain()
        self.domain = domain
        
        if curric is None:
            curric = self.gen_curriculum()
        self.curric = curric

        self.student = None
        self.tutor = None
        self.has_started = False

    def start(self, time=None):
        if not self.has_started:
            logger.info("Starting simulation. Logging student into new session")
            if time is None:
                time = dt.now()
            self.tutor.start_new_session(time)
            self.has_started = True
        else:
            logger.warning("Attempting to start simulation that has already begun. Doing nothing")

    def end(self):
        if not self.has_started:
            logger.warning("Attempting to end simulation that has not started. Doing nothing")
        else:
            logger.info("Ending simulation. Logging out of active session")
            self.tutor.end_session()


    def next(self):
        pass

    def run(self):
        pass

    def build_context(self):
        pass
    
    # Static
    def gen_domain(size=50):
        logger.info("Generating a new domain")
        domain = Domain()
        domain.generate_kcs(size)
        return domain
   
    #Static
    def gen_curriculum(domain, num_units=1, num_sections=1, num_practice=20):
        logger.info("Generating Curriculum with given domain")
        curric = SimpleCurriculum(domain)
        curric.generate(num_units, num_sections, num_practice)
        return curric

