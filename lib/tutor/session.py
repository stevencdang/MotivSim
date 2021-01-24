# Add project root to python path
import sys
sys.path.append('..')

import logging
import uuid
import random
import datetime as dt

from dataclasses import dataclass, field

from . import action
from .feedback import *
from learner.learner import Learner
from log_db.tutor_log import TutorInput, SessionStart, SessionEnd
from log_db import mongo

logger = logging.getLogger(__name__)


class Session:

    def __init__(self):
        self._id = uuid.uuid4()
        self.login_time = None
        self.logout_time = None
        self.last_input_time = None

    def login(self, time=None):
        if self.login_time == None:
            if time is None:
                self.login_time = dt.datetime.now()
            else:
                if type(time) == dt.datetime:
                    self.login_time = time
                else:
                    raise TypeError("time must be of type datetime not '%s'" % str(type(time)))
        else:
            logger.warning("Attempted to login to new session after already logged in")

    def logout(self, time=None):
        if self.logout_time == None:
            if time is None:
                self.logout_time = dt.datetime.now()
            else:
                if type(time) == dt.datetime:
                    self.logout_time = time
                else:
                    raise TypeError("time must be of type datetime not '%s'" % str(type(time)))
        else:
            logger.warning("Attempted to logout of session after already logged out")

    def increment_time(self, duration):
        # increment session time in seconds
        if self.is_logged_out():
            raise Exception("Can't increment time for seesion that is already logged out")
        if self.last_input_time is not None:
            time = self.last_input_time + dt.timedelta(seconds=duration)
        else:
            if self.is_logged_in():
                time = self.login_time +  dt.timedelta(seconds=duration)
            else:
                raise Exception("Can't increment time for session that is not logged in")
        self.update_last_input(time)


    def update_last_input(self, time=None):
        if time is None:
            self.last_input_time = dt.datetime.now()
        else:
            if type(time) == dt.datetime:
                self.last_input_time = time
            else:
                raise TypeError("time must be of type datetime not '%s'" % str(type(time)))
        logger.debug("Latest input time: %s" % str(self.last_input_time))

    def get_last_time(self):
        if self.logout_time is not None:
            return self.logout_time
        if self.last_input_time is not None:
            return self.last_input_time
        if self.login_time is not None:
            return self.login_time
        logger.warning("No actions in this session")
        return None

    def is_logged_in(self):
        if (self.login_time is not None) and (self.logout_time is None):
            return True
        else:
            return False

    def is_logged_out(self):
        if (self.login_time is None) or \
            ((self.login_time is not None) and (self.logout_time is not None)):
            return True
        else:
            return False


@dataclass
class ClassSession:

    start: dt.datetime
    end: dt.datetime
    sim_id: str
    _id: str = field(default_factory=lambda: str(uuid.uuid4()))
    type: str = ""
    students: list = field(default_factory=list)

    def __post_init__(self):
        self.type = type(self).__name__

    def length(self):
        return (self.end - self.start).total_seconds()

