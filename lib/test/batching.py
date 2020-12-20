# Script to test data batching classes
# Add project root to python path
import sys
sys.path.append('..')

import logging
import random
import uuid

from sklearn.cluster import DBSCAN

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
from simulate.simulation import SimulationBatch

from log_db import mongo
from log_db.curriculum_mapper import DB_Curriculum_Mapper
from log_db.learner_mapper import DBLearnerMapper

from analytics.batch import *
from analytics.featurization import *
from analytics.cae import *

logging.basicConfig(level=logging.DEBUG)
# logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("main")


sim_batch_desc = "Test BIRT Batch"

def init_db():
    # Setting up db connection
    data_path = "../test/data/sim-%s" % str(uuid.uuid4())
    logger.info("Writing simulation results to directory: %s" % data_path)
    db_name = "motivsim"
    db_params  = mongo.get_db_params(db_name, "../../mongo_settings.cfg")
    logger.info("got db params: %s" % str(db_params))
    db_util = mongo.Data_Utility(data_path, db_params)
    db = db_util.db
    db_util.peak()
    return db, db_util, db_params

def gen_test_curric(db, db_params):
    domain_params = {'m_l0': 0.45,
                     'sd_l0': 0.155,
                     'm_t': 0.25,
                     'sd_t': 0.13,#0.03,
                     'm_s': 0.155,
                     'sd_s': 0.055,
                     'm_g': 0.15,#0.6,
                     'sd_g': 0.105
                    }
    curric_params = {'num_units': 2,
                     'mean_sections': 4,
                     'stdev_sections': 2,
                     'mean_unit_kcs': 22,
                     'stdev_unit_kcs': 23,
                     'section_kcs_lambda': 6,
                     'mean_steps': 10,
                     'stdev_steps': 4,
                     'mean_prob_kcs': 6,
                     'stdev_prob_kcs': 3,
                     'num_practice': 100
                    }

    domain, curric = CurriculumFactory.gen_curriculum(domain_params, curric_params)
    db.domains.insert_one(domain.to_dict())
    db.kcs.insert_many([kc.__dict__ for kc in domain.kcs])
    curric_util = DB_Curriculum_Mapper(db_params)
    curric_util.write_to_db(curric)

    return domain, curric

def gen_students(num_students, domain, curric, persist=True):
    stus = []
    for i in range(num_students):
        cog = BinarySkillCognition(domain)
        ev_decider = EVDecider()
        decider = DiligentDecider(ev_decider)
        stu = ModularLearner(domain, cog, decider)
        stus.append(stu)

    return stus

def sim_students(db, num_students, domain, curric):
    students = gen_students(num_students, domain, curric)
    logger.info(f"Persisting {len(students)} initialized students to db")
    db.students.insert_many([stu.to_dict() for stu in students])
    # Init simulation batch
    batch = SimulationBatch(sim_batch_desc)

    # Simulate Students
    for i, stu in enumerate(students):
        logger.info("Simulating student #%i" % i)
        sim = ModLearnerSimulation(domain, curric, stu)
        batch.add_sim(sim)
        sim.run()

    logger.info("Inserting %i simulated students to db" % len(students))
    result = db.finalsimstudents.insert_many([stu.to_dict() for stu in students])
    logger.info("Db insert success: %s" % result.acknowledged)

    logger.info("Inserting simulation batch to db")
    result = db.simbatches.insert_one(batch.to_dict())
    logger.info("Db insert success: %s" % result.acknowledged)

    return batch, students


def test_get_full_range(db, col, fields, base_query=None):

    logger.info("Testing getting full range from db")
    db_col = db[col]
    logger.info(f"DB collection, {col} has {db_col.estimated_document_count()} documents")
    if base_query is None:
        drange = Segmenter.get_collection_range(db_col, fields)
    else:
        drange = Segmenter.get_collection_range(db_col, fields, base_query)
    logger.info(f"number of unique entries: {drange.shape}")


def get_segment_by_students(db, col, fields, students):
    logger.info("Testing getting segments of tx for each student")
    db_col = db[col]
    logger.info(f"DB collection, {col} has {db_col.estimated_document_count()} documents")
        # logger.info(f"Getting segment for student: {stu._id}")
        # base_query = {"stu_id": stu._id,
                      # "type": "TutorInput"}
    base_query = {"stu_id": {"$in": [stu._id for stu in students]},
                  "type": "TutorInput"
                 }

    logger.info(f"{col} collection has {db_col.count_documents(base_query)} documents associated with {len(students)} students")
    segmenter = Segmenter(db[col], base_query)
    idx_fields = ['stu_id']
    batches = segmenter.get_batches(idx_fields, 1)
    for query, batch in batches:
        logger.info(f"Got batch with shape {batch.shape} using query: {str(query)}")

def compute_cae(d, data_proc, data_idx, penalty1=0.35, penalty2=0.35):
    logger.info("Computing embedding")
    logger.info(f"shape of data: {d.shape}")
    logger.info(d.head())
    caa = CAAComputation(d.to_numpy(), penalty1, penalty2)
    caa = CAAModel.from_caa_obj(caa, data_proc, data_idx)
    # logger.info(f"Iterating though {len(caa.projections)} projections")
    # for i, proj in enumerate(caa.projections):
        # logger.info(f"Projection #{i}")
        # logger.info("---- U ----")
        # for col, val in zip(d.columns, proj.u.tolist()[0]):
            # logger.info(f"Column: {col}\t{val}")
                    
        # logger.info("---- V ----")
        # for col, val in zip(d.columns, proj.v.tolist()[0]):
            # logger.info(f"Column: {col}\t{val}")

    return caa

def get_test_data_batch(desc, num_students=2):
    logger.info(f"Getting batch info for test data")
    db, db_util, db_params = init_db()

    simbatch = db.simbatches.find_one({"desc": desc})
    if simbatch is None:
        logger.info("Generating new simulation. None found in db")
            
        # generate simualted data for test
        domain, curric = gen_test_curric(db, db_params)
        batch, students = sim_students(db, num_students, domain, curric)
        return batch, students
    else:
        logger.info(f"Found simulation batch: {str(simbatch)}")
        lmapper = DBLearnerMapper(db)
        students = [lmapper.get_modlearner_from_db(sid) for sid in simbatch['student_ids']]
        batch = SimulationBatch.from_dict(simbatch)
        return batch, students

def clear_db():
    logger.info(f"Clearing full db")
    db, db_util, db_params = init_db()
    db_util.clear_db()

def clear_test_data_batches(desc):
    logger.info(f"Clearing simulation batches with description: {desc}")
    db, db_util, db_params = init_db()
    batches = db.simbatches.find({"desc": desc})
    batchids = [batch['_id'] for batch in batches]
    logger.info(f"Removing batches with ids: {batchids}")
    db.simbatches.delete_many({"_id": {"$in": batchids}})
    batches = [b for b in db.simbatches.find({"desc": sim_batch_desc})]
    if len(batches) > 0:
        logger.error(f"ERROR: Found {len(batches)} batches after attempting to remove all corresponding batches")

def test_base_segmenter(students):
    # num_students = 2

    logger.info("Testing base segmenting class")
    db, db_util, db_params = init_db()
	
    batch_calc = BatchCalculator()

    # Test full range with segmenter
    logger.info("Testing segmenting transactions to retrieve full set of student ids in collection")
    col = "tutor_events"
    args = (db, col, ["stu_id"])
    # result, runtime = batch_calc.time_calc(test_get_full_range, args)
    # logger.info(f"Runtime: {runtime} seconds")

    # Test full range with segmenter
    logger.info("Testing segmenting transactions to retrieve subset of student ids in collection")
    col = "tutor_events"
    base_query = {"stu_id": {"$in": [stu._id for stu in students]},
                  "type": "TutorInput"
                 }
    #Test segment tx by student
    args = (db, col, ["stu_id"], base_query)
    result, runtime = batch_calc.time_calc(test_get_full_range, args)
    logger.info(f"Runtime: {runtime} seconds")

    logger.info("Testing segmenting transactions by student")
    col = "tutor_events"
    args = (db, col, ["_id"], students)
    result, runtime = batch_calc.time_calc(get_segment_by_students, args)
    logger.info(f"Runtime: {runtime} seconds")

def test_build_CAE(students):
    logger.info("Testing workflow for building CAA embedding for each data segment")
    db, db_util, db_params = init_db()
	
    batch_calc = BatchCalculator()

    col = "tutor_events"
    base_query = {"stu_id": {"$in": [stu._id for stu in students]},
                  "type": "TutorInput"
                 }
    logger.info(f"{col} collection has {db[col].count_documents(base_query)} documents associated with {len(students)} students using query: {base_query}")
    segmenter = Segmenter(db[col], base_query)
    idx_fields = ['stu_id']
    batches = segmenter.get_batches(idx_fields, 1)
    caa_mdls = []
    col_names = []
    caa_batch = CAABatch("Test CAA Embedding", col_names)
    for query, batch in batches:
        logger.info(f"Got batch with shape {batch.shape} using query: {str(query)}")
        data_proc = SimpleCAEPreprocessor(batch)
        d = data_proc.process_data()
        if len(col_names) == 0:
            col_names = d.columns.tolist()
        logger.info(f"computing cae on dataframe: {d.shape}")
        caa = compute_cae(d, data_proc, batch['_id'])
        caa_batch.add(caa)
    caa_batch.col_names = col_names

    # logger.debug("*****Inspecting caa object******")
    # mdl = caa_batch.mdls[0]
    # logger.debug(f"us type: {type(mdl.US[0].tolist())}\tprojection utype: {type(mdl.projections[0].u.tolist())}")
    # logger.debug(f"mean type: {type(mdl.mean)}\tstd type: {type(mdl.std)}")
    # mdl_dict = mdl.to_dict()
    # for key in mdl_dict:
        # logger.debug(f"field: {key}\t type: {type(mdl_dict[key])}")

    db.caa_models.insert_many([mdl.to_dict() for mdl in caa_batch.mdls])
    db.caa_batches.insert_one(caa_batch.to_dict())

    logger.info("**** Testing CAA Batch Operations ****")
    logger.debug(f"Projection index: {caa_batch.get_index()}")

    m = caa_batch.get_distances()
    logger.debug(f"cae distances: {m.to_numpy()}")

    # Test clustering
    X = m.to_numpy()
    clusterer = DBSCAN(metric="precomputed")
    clusters = clusterer.fit(X)
    labels = clusters.labels_
    n_clusters_ = len(set(labels)) - (1 if -1 in labels else 0)
    n_noise_ = list(labels).count(-1)
    print('Estimated number of clusters: %d' % n_clusters_)
    print('Estimated number of noise points: %d' % n_noise_)
    logger.debug(f"Cluster labels: {clusters.labels_}")




    
		

if __name__ == "__main__":
    # Enable appropriate lines based on what you want to test
    # init_db()
    # clear_db()    

    # clear_test_data_batches(sim_batch_desc)
    batch, students = get_test_data_batch(sim_batch_desc, 2)
    # test()
    # test_base_segmenter(students)
    test_build_CAE(students)


