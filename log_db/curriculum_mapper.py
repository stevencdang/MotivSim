
# Author: Steven Dang stevencdang.com

import logging
from pymongo import MongoClient
from os import mkdir, listdir, path
from collections.abc import Iterable

from .mongo import get_db_params, connect

logger = logging.getLogger(__name__)


class DB_Curriculum_Mapper:

    def __init__(self, db_params):
        self.db_params = db_params
        self.db = connect(self.db_params['url'], 
                          self.db_params['port'], 
                          self.db_params['name'], 
                          self.db_params['user'], 
                          self.db_params['pswd'])

    def write_to_db(self, curric):
        logger.info("Writing curriculum with id, %s, to db" % curric._id)
        self.write(curric, 'curriculums')
        units = curric.units
        self.write(units, 'units')
        problems = []
        steps = []
        for unit in units:
            self.write(unit.sections, 'sections')
            sections = unit.sections
            for section in sections:
                problems.extend(section.problems)
                sect_probs = section.problems
                for problem in sect_probs:
                    steps.extend(problem.steps)
        logger.info("Writing %i problem to db" % len(problems))
        self.write(problems, 'problems')
        logger.info("Writing %i steps to db" % len(steps))
        self.write(steps, 'steps')

    def write(self, objs, col):
        if isinstance(objs, Iterable):
            db_objs = [obj.to_db_object() for obj in objs]
            if len(objs) > 10:
                logger.debug("IDs before writing: %s..." % str([obj._id for obj in objs[:10]]))
            else:
                logger.debug("IDs before writing: %s" % str([obj._id for obj in objs]))
            result = self.db[col].insert_many(db_objs)

            if result.acknowledged:
                if len(result.inserted_ids) > 10:
                    logger.debug("Successfully written to db collection, '%s', with ids: %s..." % (col, result.inserted_ids[:10]))
                else:
                    logger.debug("Successfully written to db collection, '%s', with ids: %s" % (col, result.inserted_ids))
            else:
                logger.warning("Not successfully written to db")
        else:
            db_obj = objs.to_db_object()
            logger.debug("ID before writing: %s" % str(objs._id))
            result = self.db[col].insert_one(db_obj)

            if result.acknowledged:
                logger.debug("Successfully written to db collection, '%s', with id: %s" % (col, result.inserted_id))
            else:
                logger.warning("not successfully written to db")

    def get_from_db(self, curric_id):
        logger.info("Retrieving curriculum from database with id: %s" % curric_id)
        obj = self.db.curriculums.find_one({'_id': curric_id})
        logger.info(str(obj))



