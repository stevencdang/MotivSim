# Class for mapping learner objects from db entry
# Author: Steven Dang stevencdang.com

import logging
import sys

from pymongo import MongoClient
from os import mkdir, listdir, path
from collections.abc import Iterable

from .domain_mapper import DBDomainMapper
from learner.modular_learner import ModularLearner
from learner.decider import *
from learner.cognition import *

logger = logging.getLogger(__name__)

class DBLearnerMapper:


    def __init__(self, db):
        self.db = db


    def get_modlearner_from_db(self, _id):
        logger.debug("Retrieving ModularLearner from database with id: %s" % _id)
        obj  = self.db.students.find_one({'_id': _id})
        logger.debug(f"Retrieved student {str(obj)}")

        # Retrieve domain
        domain = DBDomainMapper(self.db).get_from_db(obj['domain_id'])

        # Create Cog Module
        cog_mod = self.get_cog_module(obj['cog'])
        cog_mod.skills = obj['skills']

        # Create Decider Module
        decider_mod = self.get_decider_module(obj['decider'])

        stu = ModularLearner(domain, cog_mod, decider_mod)
        stu._id = _id
        stu.skill = obj['skills']
        stu.state.skills = obj['skills']
        stu.min_off_task =  obj['min_off_task'] 
        stu.max_off_task = obj['max_off_task'] 
        stu.mean_guess_time = obj['mean_guess_time']
        stu.sd_guess_time = obj['sd_guess_time']

        stu.state.total_attempts = obj['total_attempts']
        stu.state.total_success = obj['total_success']
        return stu 


    def get_decider_module(self, d):
        # Return decider module from object

        # Determine type of cog module to use
        dectype = getattr(sys.modules[__name__], d['type'])
        # Initialize from dict
        out = dectype.from_dict(d)
        # out.state.skills = out.skills
        logger.debug(f"Recovered Decider: {str(out)}")

        # Determine if module is wrapped with diligence learner
        if 'diligence' in d:
            logger.debug("Initializing a diligent decider module wrapper")
            return DiligentDecider(out, d['diligence'])
        else:
            return out


    def get_cog_module(self, d):
        # Return decider module from object

        # Determine type of cog module to use
        modtype = getattr(sys.modules[__name__], d['type'])
        domain = DBDomainMapper(self.db).get_from_db(d['domain_id'])

        # Initialize from dict
        out = modtype.from_dict(d)

        logger.debug(f"Recovered Cog Module: {str(out)}")

        return out

