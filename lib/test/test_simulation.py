# Script to test a simulation
# Add project root to python path
import sys
sys.path.append('..')

import logging
import random
import uuid
import datetime as dt

import simpy

from tutor.domain import Domain
from tutor.curriculum_factory import CurriculumFactory
from tutor.simple_curriculum import SimpleCurriculum
from tutor.tutor import SimpleTutor
from tutor.action import Attempt, HintRequest

from learner.selfeff_learner import SelfEfficacyLearner
from learner.modular_learner import ModularLearner
from learner.cognition import *
from learner.decider import *

from simulate.simple_tutor_simulation import SimpleTutorSimulation
from simulate.self_eff_simulation import SelfEffSimulation
from simulate.modlearner_simulation import ModLearnerSimulation
from simulate.simulation import *

from log_db import mongo
from log_db.curriculum_mapper import DB_Curriculum_Mapper

# logging.basicConfig(level=logging.DEBUG)
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("main")


def init_db():
    # Setting up db connection
    data_path = "../test/data/sim-%s" % str(uuid.uuid4())
    logger.info("Writing simulation results to directory: %s" % data_path)
    db_name = "motivsim"
    db_params  = mongo.get_db_params(db_name, "../../mongo_settings.cfg")
    logger.info("got db params: %s" % str(db_params))
    db_util = mongo.Data_Utility(data_path, db_params)
    db = db_util.db
    logger.info("Clearing database")
    db_util.clear_db()
    return db, db_util, db_params


def gen_curriculum(db, db_params):
    # Generating domain
    domain_params = {'m_l0': 0.45,
                     'sd_l0': 0.155,
                     'm_t': 0.35,
                     'sd_t': 0.13,#0.03,
                     'm_s': 0.105,
                     'sd_s': 0.055,
                     'm_g': 0.45,#0.6,
                     'sd_g': 0.105 
    }
    curric_params = {'num_units': 1,
                     'mean_sections': 4,
                     'stdev_sections': 2,
                     'mean_unit_kcs': 22,
                     'stdev_unit_kcs': 23,
                     'section_kcs_lambda': 6,
                     'mean_steps': 10,
                     'stdev_steps': 4,
                     'mean_prob_kcs': 6,
                     'stdev_prob_kcs': 3,
                     'num_practice': 400
    }

    domain, curric = CurriculumFactory.gen_curriculum(domain_params, curric_params)
    db.domains.insert_one(domain.to_dict())
    db.kcs.insert_many([kc.__dict__ for kc in domain.kcs])
    curric_util = DB_Curriculum_Mapper(db_params)
    curric_util.write_to_db(curric)

    return domain, curric

def gen_cont_curric(db, db_params):

    # Generating domain
    domain_params = {'m_l0': 0.45,
                     'sd_l0': 0.155,
		     'm_l0_sd': 0.1,
		     'sd_l0_sd': 0.03,
                     'm_t': 0.35,
                     'sd_t': 0.13,#0.03,
                     'm_s': 0.105,
                     'sd_s': 0.055,
                     'm_g': 0.45,#0.6,
                     'sd_g': 0.105 
    }
    curric_params = {'num_units': 5,
                     'mean_sections': 4,
                     'stdev_sections': 2,
                     'mean_unit_kcs': 22,
                     'stdev_unit_kcs': 23,
                     'section_kcs_lambda': 6,
                     'mean_steps': 10,
                     'stdev_steps': 4,
                     'mean_prob_kcs': 6,
                     'stdev_prob_kcs': 3,
                     'num_practice': 400
    }

    domain, curric = CurriculumFactory.gen_curriculum(domain_params, curric_params)
    db.domains.insert_one(domain.to_dict())
    db.kcs.insert_many([kc.__dict__ for kc in domain.kcs])
    curric_util = DB_Curriculum_Mapper(db_params)
    curric_util.write_to_db(curric)

    return domain, curric

def test_simple_tutor():
    logger.info("**** Testing SimpleTutorSimulation ****")

    db, db_util, db_params = init_db()
    domain, curric = gen_curriculum(db, db_params)

    num_students = 2
    for i in range(num_students):
        logger.info("Simulating student #%i" % i)
        sim = SimpleTutorSimulation(domain, curric, stu)
        sim.run()
    logger.info("Finished simulation. Dumping db to file")

    # Print new contents of db
    db_util.peak()


def test_selfeff_learner():
    logger.info("**** Testing SelfEffSimulation ****")

    db, db_util, db_params = init_db()
    domain, curric = gen_curriculum(db, db_params)
    
    num_students = 20
    for i in range(num_students):
        stu = SelfEfficacyLearner(domain)
        logger.debug("inserting new student to db: %s" % str(stu.to_dict()))
        db.students.insert_one(stu.to_dict())
        logger.info("Simulating student #%i" % i)
        sim = SelfEffSimulation(domain, curric, stu)
        sim.run()
    logger.info("Finished simulation. Dumping db to file")

    # Print new contents of db
    db_util.peak()



def test_modlearner():
    logger.info("**** Testing Modular Learner Simulation ****")

    db, db_util, db_params = init_db()
    domain, curric = gen_curriculum(db, db_params)

    num_students = 1
    for i in range(num_students):
        cog = BinarySkillCognition(domain)
        ev_decider = RandValDecider()
        decider = DiligentDecider(ev_decider)
        stu = ModularLearner(domain, cog, decider)
        logger.debug("inserting new student to db: %s" % str(stu.to_dict()))
        db.students.insert_one(stu.to_dict())
        logger.info("Simulating student #%i" % i)
        sim = ModLearnerSimulation(domain, curric, stu)
        sim.run()
    logger.info("Finished simulation")
    
    # Print new contents of db
    db_util.peak()

def test_biaslearner():
    logger.info("***** Testing Modular learning with biased cognitive module *****")

    db, db_util, db_params = init_db()
    domain, curric = gen_cont_curric(db, db_params)

    num_students = 200
    for i in range(num_students):
        ability = 0.5
        cog = BiasSkillCognition(domain, ability)
        ev_decider = EVDecider()
        decider = DiligentDecider(ev_decider)
        stu = ModularLearner(domain, cog, decider)
        logger.debug("inserting new student to db: %s" % str(stu.to_dict()))
        db.students.insert_one(stu.to_dict())
        logger.info("Simulating student #%i" % i)
        sim = ModLearnerSimulation(domain, curric, stu)
        sim.run()
    logger.info("Finished simulation")
    
    # Print new contents of db
    db_util.peak()


def test_timed_simulation():
    logger.info("***** Testing timed simulation *****")

    db, db_util, db_params = init_db()
    domain, curric = gen_cont_curric(db, db_params)

    env = simpy.Environment()

    num_students = 20
    mastery_thres = 0.9
    m_ses_len = 40
    sd_ses_len = 8
    max_ses_len = 60
    sim_start = dt.datetime.now()
    for i in range(num_students):
        # Create student
        ability = random.triangular(-1, 1)
        cog = BiasSkillCognition(domain, ability)
        ev_decider = EVDecider()
        decider = DiligentDecider(ev_decider)
        stu = ModularLearner(domain, cog, decider)
        logger.debug("inserting new student to db: %s" % str(stu.to_dict()))
        db.students.insert_one(stu.to_dict())

        # Create tutor
        tutor = SimpleTutor(curric, stu._id, mastery_thres)

        # Initialize simulation processes
        num_sessions = 20

        sim = SingleStudentSim(db, env, sim_start, stu, tutor, 
                               num_sessions, m_ses_len, sd_ses_len, max_ses_len)
        env.process(sim.run())
        
    env.run()


if __name__ == "__main__":
    # test_simple_tutor()
    #test_selfeff_learner()
    # test_modlearner()
    # test_biaslearner()
    test_timed_simulation()
