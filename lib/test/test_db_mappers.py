# Script to test a simulation
# Add project root to python path
import sys
sys.path.append('..')

import logging
import random
import uuid

from tutor.domain import Domain
from tutor.curriculum_factory import CurriculumFactory
from tutor.simple_curriculum import SimpleCurriculum
from tutor.tutor import SimpleTutor
from tutor.action import Attempt, HintRequest

from learner.selfeff_learner import SelfEfficacyLearner
from learner.modular_learner import ModularLearner
from learner.binary_skill_cog import BinarySkillCognition
from learner.decider import *

from simulate.simple_tutor_simulation import SimpleTutorSimulation
from simulate.self_eff_simulation import SelfEffSimulation
from simulate.modlearner_simulation import ModLearnerSimulation

from log_db import mongo
from log_db.mongo import get_db_params, connect
from log_db.curriculum_mapper import DB_Curriculum_Mapper
from log_db.domain_mapper import DBDomainMapper
from log_db.learner_mapper import DBLearnerMapper


logging.basicConfig(level=logging.DEBUG)
# logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("main")

def get_db():
    db_params = get_db_params()
    db = connect(db_params['url'], 
                 db_params['port'], 
                 db_params['name'], 
                 db_params['user'], 
                 db_params['pswd'])

    return db


def test_domain_mapper():
    db = get_db()
    obj = db.domains.find_one()
    logger.info(f"Retrieved random test domain from db with id: {obj['_id']}")
    mapper = DBDomainMapper(db)
    domain = mapper.get_from_db(obj['_id'])
    logger.info(f"Retrieved domain: {str(domain)}")


def test_learner_mapper():
    db = get_db()
    obj = db.students.find_one()
    logger.info(f"Retrieved random student from db with id: {obj['_id']}")
    mapper = DBLearnerMapper(db)
    mapper.get_modlearner_from_db(obj['_id'])



if __name__ == "__main__":
    # test_domain_mapper()
    test_learner_mapper()
