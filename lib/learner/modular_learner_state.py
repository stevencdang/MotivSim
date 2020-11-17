# Base class for a modular learner state

import uuid
import logging
import random

from log_db import mongo
from tutor.feedback import *

from .learner import LearnerState


logger = logging.getLogger(__name__)


class ModularLearnerState(LearnerState):

    def __init__(self):
        self.off_task = False
        self.attempted = False
        self.skills = None
        self.total_attempts = 0
        self.total_success = 0

    def is_off_task(self):
        return self.off_task

    def has_attempted(self):
        return attempted
