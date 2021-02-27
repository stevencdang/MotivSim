# Class for managing logging during simulations
# Author: Steven Dang stevencdang.com

import logging
import sys
from queue import Queue

from pymongo import MongoClient
from os import mkdir, listdir, path
from collections.abc import Iterable


from log_db import mongo
from log_db.learner_log import *


logger = logging.getLogger(__name__)
# logger.setLevel(logging.DEBUG)

class SimLogger:

    def __init__(self, db, stu, tutor):
        # Initialize connection to database
        # db_params = mongo.get_db_params()
        # self.db = mongo.connect(db_params['url'], 
                              # db_params['port'], 
                              # db_params['name'], 
                              # db_params['user'], 
                              # db_params['pswd'])
        self.db = db
        self.student = stu
        self.tutor = tutor

        self.state = {
            'last_decision': [],
            'last_actions':  [],
        }

        self.max_queue = 1000

        self.decisions = []
        self.actions = []
        self.transactions = []
        self.sessions = []


    def log_decision(self, d):
        logger.debug("Logging decision: %s" % str(d.to_dict()))
        self.state['last_decision'].append(d)

        self.decisions.append(d)
        if len(self.decisions) > self.max_queue:
            logger.debug("***** Writing Decision queue to db *****")
            self.db.decisions.insert_many([dec.to_dict() for dec in self.decisions])
            # Reset queue
            self.decisions = []


    def log_action(self, d, cntxt):
        logger.debug("Return action: %s" % str(d))
        logged_action = LoggedAction(self.student, d, cntxt.time)
        logger.debug("Logged action: %s" % str(logged_action.to_dict()))
        
        # Add decision_id of most recent decision to action before logging
        last_dec = self.state['last_decision'].pop()
        logged_action.decision_id = last_dec._id

        self.state['last_actions'].append(logged_action)
        
        self.actions.append(logged_action)

        if len(self.actions) > self.max_queue:
            logger.debug("***** Writing Action queue to db *****")
            self.db.actions.insert_many([act.to_dict() for act in self.actions])
            # Reset queue
            self.actions = []


    def log_transaction(self, d):
        logger.debug(f"Logging transaction: {d.to_dict()}")
        # if d.type == "SessionStart":
            # logger.warning(f"Logging Session Start. current tx count: {len(self.transactions)}")

        # Add action_ids of most recent actions to latest transaction before logging
        action_ids = [act._id for act in self.state['last_actions']]
        d.action_ids = action_ids
        self.state['last_actions'] = []

        self.transactions.append(d)
        # if d.type == "SessionStart":
            # logger.warning(f"Appended session start. current tx count: {len(self.transactions)}")
        if len(self.transactions) > self.max_queue:
            logger.debug("***** Writing Transaction queue to db *****")
            self.db.tutor_events.insert_many([tx.to_dict() for tx in self.transactions])
            # Reset queue
            self.transactions = []


    def log_session(self, d):
        logger.debug(f"Logging session: {d.__dict__}")
        # self.db.class_sessions.insert_one(d.__dict__)
        self.sessions.append(d)
        if len(self.sessions) > self.max_queue:
            logger.debug("***** Writing Sessions queue to db *****")
            self.db.sessions.insert_many([ses.__dict__ for ses in self.sessions])
            # Reset queue
            self.sessions = []


    def write_to_db(self):
        logger.debug("Dumping all queues to db")
       
        if len(self.sessions) > 0:
            self.db.sessions.insert_many([ses.__dict__ for ses in self.sessions])
            # Reset queue
            self.sessions = []

        if len(self.transactions) > 0:
            self.db.tutor_events.insert_many([tx.to_dict() for tx in self.transactions])
            # Reset queue
            self.transactions = []
        
        if len(self.actions) > 0:
            self.db.actions.insert_many([act.to_dict() for act in self.actions])
            # Reset queue
            self.actions = []
        
        if len(self.decisions) > 0:
            self.db.decisions.insert_many([dec.to_dict() for dec in self.decisions])
            # Reset queue
            self.decisions = []



