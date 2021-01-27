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
from log_db.sim_logger import *
from tutor.domain import Domain
from context.context import *
from tutor.simple_curriculum import SimpleCurriculum
from tutor.tutor import Tutor
from tutor.session import ClassSession

logger = logging.getLogger(__name__)
# logger.setLevel(logging.DEBUG)

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
        return self.start + dt.timedelta(seconds=t)

    def convert_to_sim_time(self, t):
        """
        Convert a given datetime to sim time

        """
        delta = (t - self.start).total_seconds()
        if delta < 0:
            logger.warning("Provided datetime, {t} is before start of simulation, \
                           {self.start}")
        return delta



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

        self.log = SimLogger(self.student, self.tutor)

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
        logger.debug(f"Class start hour: {start_hour}\tminute: {start_min}")
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
                               sim_id=self._id,
                               students=[self.student._id]
                              )

        return session

    def wait_for_class_start(self, session):
        """
        Pause simulation process until session start

        """
        sim_time = self.convert_to_sim_time(session.start)
        delay = sim_time - self.env.now
        return self.env.timeout(delay)

    def study(self, session):
        try:
            while self.tutor.has_more():
                t = self.get_sim_time()
                cntxt = ClassSessionContext(self.tutor.state, self.student.get_state(), session, t)
                choice, decision = self.student.choose_action(cntxt)
                self.log.log_decision(decision)
                
                # logger.debug("Logging decision: %s" % str(decision.to_dict()))
                # self.db.decisions.insert_one(decision.to_dict())

                action = self.student.perform_action(choice, cntxt)
                self.log.log_action(action, cntxt)
                
                # logger.debug("Return action: %s" % str(action))
                # logged_action = LoggedAction(self.student, action, cntxt.time)
                # logger.debug("Logged action: %s" % str(logged_action.to_dict()))
                # self.db.actions.insert_one(logged_action.to_dict())

                if isinstance(action, StopWork):
                    logger.info(f"Student with diligence {self.student.decider.diligence} \
                                is stopping work {session.end - t} till end and {t - session.start} from start")
                    # logger.info(f"Student, {self.student._id} wiht diligence {self.student.decider.diligence} is stopping work at time: {t}\nstart: {session.start}\tEnd of class: {session.end}")
                    raise simpy.Interrupt("Student chose to stop working")

                # Simulate Learning interaction with tutor
                feedback, tx = self.tutor.process_input(action, t)
                
                if feedback is not None:
                    self.student.process_feedback(feedback)
                    self.log.log_transaction(tx)
                    # self.db.tutor_events.insert_one(tx.to_dict())

                yield self.env.timeout(action.time)
        except simpy.Interrupt as i:
            logger.debug(f"***** Studying was interrupted by: {i} *****")
            return

        logger.debug("***** STudent completed studying all tutor content *****")



        


    def run(self):
        try:
            logger.info(f"Starting Sim for student {self.student._id}")
            for i in range(self.num_sessions):
                # Start a new session and wait to start work
                session = self.get_next_class_session()
                logger.debug(f"Student {self.student._id}\nSimulating session #{i} start at {session.start}, sim time {self.get_sim_time()} and end at {session.end}")
                yield self.wait_for_class_start(session)
                logger.debug(f"Student {self.student._id} Session starting: {self.get_sim_time()}\tscheduled start: {session.start}")

                # Start working
                delay = self.student.start_working(session.length())
                logger.debug(f"Starting work in {delay/60} minutes")
                yield self.env.timeout(delay)

                # Login to tutor
                tx = self.tutor.login(session, self.get_sim_time())
                self.log.log_transaction(tx)
                # self.db.tutor_events.insert_one(tx.__dict__)
                
                # work on tutor until end of session or end of tutor
                studying = self.env.process(self.study(session))
                end_of_class = self.env.timeout(session.length())
                yield studying | end_of_class

                # Interrupt studying if necessary
                if not studying.triggered:
                    studying.interrupt("End of Class")
                else:
                    # Wait until end of class if studening was finished first
                    yield end_of_class

                # Logout of Tutor
                tx = self.tutor.logout(session, self.get_sim_time())
                self.log.log_transaction(tx)
                # self.db.tutor_events.insert_one(tx.__dict__)

                # Log session & update simulation state
                self.log.log_session(session)
                # self.db.class_sessions.insert_one(session.__dict__)
                # logger.debug(f"Logged class session: {session}")
                self.state['session_num'] += 1
                logger.debug(f"Class session ending at current time {self.get_sim_time()}")

        except simpy.Interrupt as i:
            logger.warning("Process was interrupted")
        # Write all log to db at end of simulation
        self.log.write_to_db()
        
        


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


