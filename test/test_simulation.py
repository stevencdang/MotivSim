# Script to test a simulation
# Add project root to python path
import sys
sys.path.append('..')

import logging
import random
import uuid

from tutor.domain import Domain
from tutor.curriculum import SimpleCurriculum
from tutor.tutor import SimpleTutor
from tutor.action import Attempt, HintRequest
from learner.selfeff_learner import SelfEfficacyLearner
from simulate.simple_tutor_simulation import SimpleTutorSimulation
from simulate.self_eff_simulation import SelfEffSimulation
from log_db import mongo
from log_db.curriculum_mapper import DB_Curriculum_Mapper

logging.basicConfig(level=logging.DEBUG)
# logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("main")

def test_simple_tutor():
    logger.info("**** Testing SimpleTutorSimulation ****")

    # Setting up db connection
    data_path = "../test/data/sim-%s" % str(uuid.uuid4())
    logger.info("Writing simulation results to directory: %s" % data_path)
    db_name = "motivsim"
    db_params  = mongo.get_db_params(db_name)
    logger.info("got db params: %s" % str(db_params))
    db_util = mongo.Data_Utility(data_path, db_params)
    db = db_util.db
    logger.info("Clearing database")
    db_util.clear_db()

    # Generating domain
    domain = SimpleTutorSimulation.gen_domain(30)
    db.kcs.insert_many([kc.__dict__ for kc in domain.kcs])
    curric = SimpleTutorSimulation.gen_curriculum(domain, 1, 3, 20)
    curric_util = DB_Curriculum_Mapper(db_params)
    curric_util.write_to_db(curric)
    # db.curriculum.insert(domain.kcs)
    num_students = 2
    for i in range(num_students):
        logger.info("Simulating student #%i" % i)
        sim = SimpleTutorSimulation(domain, curric, stu)
        sim.run()
    logger.info("Finished simulation. Dumping db to file")

    db_util.dump_db()
    curric_util.get_from_db(curric._id)

def test_selfeff_learner():
    logger.info("**** Testing SelfEffSimulation ****")

    # Setting up db connection
    data_path = "../test/data/sim-%s" % str(uuid.uuid4())
    logger.info("Writing simulation results to directory: %s" % data_path)
    db_name = "motivsim"
    db_params  = mongo.get_db_params(db_name)
    logger.info("got db params: %s" % str(db_params))
    db_util = mongo.Data_Utility(data_path, db_params)
    db = db_util.db
    logger.info("Clearing database")
    db_util.clear_db()

    # Generating domain
    domain = SelfEffSimulation.gen_domain(30)
    db.kcs.insert_many([kc.__dict__ for kc in domain.kcs])
    curric = SelfEffSimulation.gen_curriculum(domain, 1, 3, 20)
    curric_util = DB_Curriculum_Mapper(db_params)
    curric_util.write_to_db(curric)
    # db.curriculum.insert(domain.kcs)
    num_students = 2
    for i in range(num_students):
        stu = SelfEfficacyLearner(domain)
        logger.debug("inserting new student to db: %s" % str(stu.to_dict()))
        db.students.insert_one(stu.to_dict())
        logger.info("Simulating student #%i" % i)
        sim = SelfEffSimulation(domain, curric, stu)
        sim.run()
    logger.info("Finished simulation. Dumping db to file")

    db_util.dump_db()
    curric_util.get_from_db(curric._id)




if __name__ == "__main__":
    # test_simple_tutor()
    test_selfeff_learner()
