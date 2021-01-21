# Base classes for running a data simulation
# Add project root to python path
import sys
sys.path.append('..')

import logging
import uuid
import random
from datetime import datetime as dt

import simpy

from tutor.domain import Domain
from tutor.simple_curriculum import SimpleCurriculum
from tutor.tutor import Tutor

logger = logging.getLogger(__name__)

class Simulation:
    # Base class

    def __init__(self, domain=None, curric=None):
        self._id = str(uuid.uuid4())
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
    @staticmethod
    def gen_domain(size=50):
        logger.info("Generating a new domain")
        domain = Domain()
        domain.generate_kcs(size)
        return domain
   
    #Static
    @staticmethod
    def gen_curriculum(domain, num_units=1, num_sections=1, num_practice=20):
        logger.info("Generating Curriculum with given domain")
        curric = SimpleCurriculum(domain)
        curric.generate(num_units, num_sections, num_practice)
        return curric


class TimedSimulation:
    # Base Class

    def __init__(self, env):
        self._id = str(uuid.uuid4())
        self.env = env

    def run(self):
        pass


class SingleStudentSim(TimedSimulation):

    def __init__(self, env, student, tutor,
                 num_sessions, m_ses_len, sd_ses_len,
                 max_ses_len):
        super().__init__(env)
        self.student = student
        self.tutor = tutor
        self.num_sessions = num_sessions
        self.m_ses_len = m_ses_len
        self.sd_ses_len = sd_ses_len
        self.max_ses_len = max_ses_len

    def create_session(self):
        l = -1
        while (l <= 0) or (l > self.max_ses_len):
            l = random.gauss(self.m_ses_len, self.sd_ses_len)

        start = self.env.now

        ses_params = {"length": l,
                      "start": start
                     }
        return ses_params


    def run(self):
        logger.info("Running Sim")
        for i in range(self.num_sessions):
            ses_params = self.create_session()
            logger.info(f"Simulating session #{i} start at {ses_params['start']}")
            yield self.env.timeout(ses_params['length'])
        
        


class SimulationBatch:

    def __init__(self, desc):
        self._id = str(uuid.uuid4())
        self.run_time = dt.now()
        # For now, just track the list of students
        self.student_ids = set()
        self.desc = desc

    def add_sim(self, sim):
        sim_stu = sim.student
        sid = sim.student._id
        if sid not in self.student_ids:
            self.student_ids.add(sid)
    
    def to_dict(self):
        out = {'_id': self._id,
               'run_time': self.run_time,
               'desc': self.desc,
               'student_ids': list(self.student_ids)
               }
        return out
    
    @classmethod
    def from_dict(cls, d):
        result = cls(d['desc'])
        result._id = d['_id']
        result.run_time = d['run_time']
        result.student_ids = set(d['student_ids'])
        return result


