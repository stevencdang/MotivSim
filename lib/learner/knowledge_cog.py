# Class for a knowledge-based learner cognition module 
# This module is responsible for simulating student responses to questions

import uuid
import logging
import random

from log_db import mongo
from tutor.feedback import *

from .modular_learner_state import ModularLearnerState


logger = logging.getLogger(__name__)

class Cognition:

    def __init__(self):
        logger.debug("Init base Cognition")

    def answer_question(self):
        pass
