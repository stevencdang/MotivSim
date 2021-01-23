# Base classes for running a data simulation
# Add project root to python path
import sys
sys.path.append('..')

import logging
import uuid
import random
import numpy as np
import math
import datetime as dt
# from datetime import datetime as dt

import simpy

from log_db import mongo
from log_db.learner_log import *
from tutor.domain import Domain
from tutor.simple_curriculum import SimpleCurriculum
from tutor.tutor import Tutor
from tutor.session import ClassSession

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

        # Initialize connection to database
        self.db_params = mongo.get_db_params()
        self.db = mongo.connect(self.db_params['url'], 
                          self.db_params['port'], 
                          self.db_params['name'], 
                          self.db_params['user'], 
                          self.db_params['pswd'])


    def start(self, time=None):
        if not self.has_started:
            logger.info("Starting simulation. Logging student into new session")
            if time is None:
                time = dt.datetime.now()
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
    

class TimedSimulation:
    # Base Class

    def __init__(self, env, start):
        self._id = str(uuid.uuid4())
        # Simpy environment
        self.env = env
        # Datetime stamp associated with 0 in simulation time
        self.start = start
        
        # Initialize connection to database
        db_params = mongo.get_db_params()
        self.db = mongo.connect(db_params['url'], 
                              db_params['port'], 
                              db_params['name'], 
                              db_params['user'], 
                              db_params['pswd'])

    def run(self):
        """
        Main process for running the simulation with simpy

        """
        pass


    def get_sim_time(self, t=None):
        """
        Get the a time-stamp associated with the current time in the simulation

        """
        if t is None:
            t = self.env.now
        return start + dt.timedelta(seconds=t)



class SingleStudentSim(TimedSimulation):

    def __init__(self, env, start,
                 student, tutor,
                 num_sessions, m_ses_len, sd_ses_len,
                 max_ses_len
                ):
        super().__init__(env, start)
        self.student = student
        self.tutor = tutor
        self.num_sessions = num_sessions
        self.m_ses_len = m_ses_len
        self.sd_ses_len = sd_ses_len
        self.max_ses_len = max_ses_len

        self.state = {'session_num': 0,
                      'classes': []}

        self.class_start = None

        self.set_class_start()




    def set_class_start(self):
        """
        Set the regular class start time to some random time in a school day

        """
        school_start = 7
        school_end = 12+2.5 
        steps = 0.25 # 15 minute class start intervals
        day_intervals = np.arange(school_start, school_end - 1, steps)
        class_start = random.choice(day_intervals)
        
        start_hour = math.floor(class_start)
        start_min = int((class_start - start_hour)*60)
        logger.info(f"Class start hour: {start_hour}\tminute: {start_min}")
        self.class_start = dt.time(hour=start_hour, minute=start_min)

        
    def get_next_class_session(self, length=None):
        """
        Returns an data object describing the next class session
        
        """
        # Calculate the first class datetime
        first_class = dt.datetime(year=self.start.year, month=self.start.month, day=self.start.day, 
                               hour=self.class_start.hour, minute=self.class_start.minute)
        # Check that first class is after start of simulation
        if (self.start - first_class).total_seconds() > 0:
            first_class = first_class + dt.timedelta(days=1)

        # Add days for every completed session
        next_class = first_class + dt.timedelta(days=self.state['session_num'])

        # Randomly determine class length, l
        if length is None:
            length = -1
            while (length <= 0) or (length > self.max_ses_len):
                length = random.gauss(self.m_ses_len, self.sd_ses_len)

        session = ClassSession(start=next_class,
                               end=next_class+dt.timedelta(minutes=length),
                               students=[self.student._id]
                              )

        return session


    def run(self):
        logger.info("Running Sim")
        for i in range(self.num_sessions):
            # Start a new session and wait to start work
            session = self.get_next_class_session()
            logger.info(f"Simulating session #{i} start at {session.start} and end at {session.end}")
            yield self.env.timeout(session.length())


            # Login to tutor
            
            # work on tutor until end of session or end of tutor

            # Logout of Tutor

            # Log session & update simulation state
            self.db.class_sessions.insert_one(session.__dict__)
            logger.debug("Logged class session: {session}")
            self.state['session_num'] += 1
        
        


class SimulationBatch:

    def __init__(self, desc):
        self._id = str(uuid.uuid4())
        self.run_time = dt.datetime.now()
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


