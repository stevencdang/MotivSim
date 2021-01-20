# Class for mapping domain object from db entry
# Author: Steven Dang stevencdang.com

import logging
from pymongo import MongoClient
from os import mkdir, listdir, path
from collections.abc import Iterable

from .mongo import get_db_params, connect
from tutor.domain import Domain, KC

logger = logging.getLogger(__name__)

class DBDomainMapper:


    def __init__(self, db):
        self.db = db


    def get_from_db(self, _id):
        logger.debug(f"Retrieving domain from database with id: {_id}")
        obj = self.db.domains.find_one({'_id': _id})
        logger.debug(str(obj))
        kcs = [kc for kc in self.db.kcs.find({"_id": {"$in": obj['kcs']}})]
        out = Domain()
        out._id = obj['_id']
        if 'kc_hyperparams' in obj:
            out.kc_hyperparams = obj['kc_hyperparams']
        out.kcs = [self.kc_from_dict(kc) for kc in kcs]

        return out


    def kc_from_dict(self, d):
        kc = KC(d['domain_id'])
        kc._id = d['_id']
        kc.pl0 = d['pl0']
        kc.pt = d['pt']
        kc.ps = d['ps']
        kc.pg = d['pg']
        kc.m_time = d['m_time']
        kc.sd_time = d['sd_time']

        return kc

        



