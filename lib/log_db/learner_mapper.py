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

        # State Variables
        fields = obj['state_fields']
        stu.state = {}
        for field in fields:
            stu.state[field] = obj[field]

        # Attribute Varibales
        fields = obj['attribute_fields']
        stu.attributes = {}
        for field in fields:
            stu.attributes[field] = obj[field]

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
        args = {'domain': domain}
        args.update(modtype.get_init_args(d))

        # Initialize from dict
        out = modtype(**args)

        logger.debug(f"Recovered Cog Module: {str(out)}")

        return out

