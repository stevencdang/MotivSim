# Class for managing logging during simulations
# Author: Steven Dang stevencdang.com

import logging
import sys

from pymongo import MongoClient
from os import mkdir, listdir, path
from collections.abc import Iterable


from log_db import mongo
from log_db.learner_log import *


logger = logging.getLogger(__name__)

class SimLogger:

    def __init__(self, stu, tutor):
        # Initialize connection to database
        db_params = mongo.get_db_params()
        self.db = mongo.connect(db_params['url'], 
                              db_params['port'], 
                              db_params['name'], 
                              db_params['user'], 
                              db_params['pswd'])
        self.student = stu
        self.tutor = tutor

        # self.state = {}

        self.max_queue = 1000

        self.decisions = []
        self.actions = []
        self.transactions = []
        self.sessions = []


    def log_decision(self, d):
        logger.debug("Logging decision: %s" % str(d.to_dict()))
        # self.db.decisions.insert_one(d.to_dict())
        self.decisions.append(d)
        if len(self.decisions) > self.max_queue:
            logger.info("***** Writing Decision queue to db *****")
            self.db.decisions.insert_many([dec.to_dict() for dec in self.decisions])
            # Reset queue
            self.decisions = []


    def log_action(self, d, cntxt):
        logger.debug("Return action: %s" % str(d))
        logged_action = LoggedAction(self.student, d, cntxt.time)
        logger.debug("Logged action: %s" % str(logged_action.to_dict()))
        # self.db.actions.insert_one(logged_action.to_dict())
        self.actions.append(d)
        if len(self.actions) > self.max_queue:
            logger.info("***** Writing Action queue to db *****")
            self.db.actions.insert_many([act.to_dict() for act in self.actions])
            # Reset queue
            self.actions = []


    def log_transaction(self, d):
        logger.debug("Logging transaction: {d.to_dict()}")
        # self.db.tutor_events.insert_one(d.to_dict())
        self.transactions.append(d)
        if len(self.transactions) > self.max_queue:
            logger.info("***** Writing Transaction queue to db *****")
            self.db.tutor_events.insert_many([tx.to_dict() for tx in self.transactions])
            # Reset queue
            self.transactions = []


    def log_session(self, d):
        logger.debug("Logging session: {d.__dict__}")
        # self.db.class_sessions.insert_one(d.__dict__)
        self.sessions.append(d)
        if len(self.sessions) > self.max_queue:
            logger.info("***** Writing Sessions queue to db *****")
            self.db.sessions.insert_many([ses.__dict__ for ses in self.sessions])
            # Reset queue
            self.sessions = []


    def write_to_db(self):
        logger.info("Dumping all queues to db")
        
        self.db.sessions.insert_many([ses.__dict__ for ses in self.sessions])
        # Reset queue
        self.sessions = []

        self.db.tutor_events.insert_many([tx.to_dict() for tx in self.transactions])
        # Reset queue
        self.transactions = []

        self.db.actions.insert_many([act.to_dict() for act in self.actions])
        # Reset queue
        self.actions = []

        self.db.decisions.insert_many([dec.to_dict() for dec in self.decisions])
        # Reset queue
        self.decisions = []



