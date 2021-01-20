# Script to generate a new curriculum
# Add project root to python path
import sys
sys.path.append('..')

import logging

from tutor.domain import Domain
from tutor.simple_curriculum import SimpleCurriculum
from tutor.curriculum_factory import CurriculumFactory

from log_db import mongo
from log_db.curriculum_mapper import DB_Curriculum_Mapper

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger("main")


def init_db():
    # Setting up db connection
    data_path = "../test/data/gen_curric"
    logger.info("Writing simulation results to directory: %s" % data_path)
    db_name = "motivsim"
    db_params  = mongo.get_db_params(db_name, "../../mongo_settings.cfg")
    logger.info("got db params: %s" % str(db_params))
    db_util = mongo.Data_Utility(data_path, db_params)
    db = db_util.db
    logger.info("Clearing database")
    db_util.clear_db()
    return db, db_util, db_params


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



def gen_cont_curric():
    db, db_util, db_params = init_db()

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

def gen_simple_curric():
    logger.info("**** Generating a new curriculum ****")
    logger.info("Generating a new domain")
    domain = Domain()
    domain_size = 3000
    domain.generate_kcs(domain_size)

    logger.info("Generating Curriculum with domain")
    curric = SimpleCurriculum(domain)
    curric.generate(20, 5, 30)
    check_simple_curric(curric)


if __name__ == "__main__":

    #gen_simple_curric()
    gen_cont_curric()
