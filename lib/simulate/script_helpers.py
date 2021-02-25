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

from learner.decider import *
from learner.cognition import *
from learner.modular_learner import *

from tutor.tutor import SimpleTutor

from simulate.simulation import *
from simulate.modlearner_simulation import *

logger = logging.getLogger(__name__)


class SimHelper:

    def __init__(self, db):
        self.db = db
   
    def gen_students(self, num_students, domain, curric, 
		     cog_mod, cog_params, dec_mod, dec_params):
        stus = []
        for i in range(num_students):
            cp = cog_params()
            cog = cog_mod(domain, **cp)
            dp = dec_params()
            dec = dec_mod(**dp)
            ### Tmp double off-task value ###
            dec.values['off task'] = 5*dec.values['off task']
            decider = DiligentDecider(dec)
            stu = ModularLearner(domain, cog, decider)
            stus.append(stu)
            
        return stus

    def simulate_students(self, curric, students, batch):    
	
        env = simpy.Environment()

        mastery_thres = 0.95
        m_ses_len = 45
        sd_ses_len = 8
        max_ses_len = 60
        sim_start = dt.datetime.now()

        mod = round(len(students) / 10)
        for i, stu in enumerate(students):
            if i % mod == 0:
                logger.info("Simulating student #%i" % i)
            # Create associated tutor
            tutor = SimpleTutor(curric, stu._id, mastery_thres)

            # Initialize simulation processes
            sim = SingleStudentSim(self.db, env, sim_start, stu, tutor,
                                   num_sessions, m_ses_len, sd_ses_len, max_ses_len)
            batch.add_sim(sim)

            env.process(sim.run())

        env.run()
                    
        logger.info("Inserting %i simulated students to db" % len(students))
        result = self.db.finalsimstudents.insert_many([stu.to_dict() for stu in students])
        logger.info("Db insert success: %s" % result.acknowledged)

        logger.info("Inserting simulation batch to db")
        result = self.db.simbatches.insert_one(batch.to_dict())
        logger.info("Db insert success: %s" % result.acknowledged)

        return batch, students

