# Definition of a simulated tutor managing internal state

import logging
import uuid
import datetime as dt

logger = logging.getLogger(__name__)

class Tutor:

    def __init__(self, curric, stu_id):
        self._id = uuid.uuid4()
        self.curric = curric
        self.stu_id = stu_id
        self.mastery_thres = 0.9
        self.state = None
        self.session = None

    def start_new_session(self, time=None):
        if (self.session is None) or (self.session.:
            pass
        else:
            if 


class SimpleTutor(Tutor):

    def 


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

    def update_last_input(self, time=None):
        if time is None:
            self.last_input_time = dt.datetime.now()
        else:
            if type(time) == dt.datetime:
                self.last_input_time = time
            else:
                raise TypeError("time must be of type datetime not '%s'" % str(type(time)))

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
        if (self.login_time is not None) and (self.logout_time is not None):
                return True
        else:
            return False
    def is_logged_out(


class SimpleTutorState:

    def __init__(self):
        # Tracking completed content in curriculum
        self.completed = {}
        # Tracking mastery of all skills within domain
        self.mastery = {}
        self.unit = None
        self.section = None
        self.prob = None
        self.step = None
        self.hints_avail = None
        self.hints_used = None

    def has_started(self):
        if self.prob == None:
            return False
        else:
            return True

