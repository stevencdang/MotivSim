# Definition of a simulated tutor managing internal state
# Add project root to python path
import sys
sys.path.append('..')

import logging
import uuid
import random
import datetime as dt
from . import action
from log_db.tutor_log import TutorInput, SessionStart, SessionEnd
from log_db import mongo

logger = logging.getLogger(__name__)

class Tutor:

    def __init__(self, curric, stu_id):
        self._id = uuid.uuid4()
        self.curric = curric
        self.stu_id = stu_id
        self.mastery_thres = 0.95
        self.state = None
        self.session = None

        # Initialize connection to database
        self.db_params = mongo.get_db_params()
        self.db = mongo.connect(self.db_params['url'], 
                          self.db_params['port'], 
                          self.db_params['name'], 
                          self.db_params['user'], 
                          self.db_params['pswd'])




    def start_new_session(self, time=None):
        logger.debug("Attempting Starting new session")
        if self.session is not None:
            if self.session.is_logged_in():
                logger.error("Can't start new session when user session already exists")
            else:
                self.session = Session()
                self.session.login(time)
                self.log_login()
                logger.debug("Created session and logged user in")
        else:
            self.session = Session()
            self.session.login(time)
            self.log_login()
            logger.debug("Created session and logged user in")


    def end_session(self, time=None):
        logger.debug("Attempting end session")
        if self.session is not None:
            if not self.session.is_logged_in():
                logger.error("Can't end session because user has not logged in yet")
            else:
                logger.debug("Logging user out of  session")
                self.session.logout(time)
                self.log_logout()
        else:
            logger.error("Can't end session because no session exists")

    def init_student_model(self):
        pass

    def log_login(self):
        logger.debug("Logging start of new session")
        tx = SessionStart(self.session.login_time)
        tx._id = self.db.tutor_events.insert_one(tx.__dict__)
        logger.info("session start: %s" % str(tx.__dict__))

    def log_logout(self):
        logger.debug("Logging end of session")
        tx = SessionEnd(self.session.logout_time)
        tx._id = self.db.tutor_events.insert_one(tx.__dict__)
        logger.info("session end: %s" % str(tx.__dict__))




class SimpleTutor(Tutor):

    def __init__(self, curric, stu_id):
        super().__init__(curric, stu_id)
        self.state = SimpleTutorState()
        self.init_student_model()


    def init_student_model(self):
        logger.debug("Initializing student model for simple list of kcs")
        stu_mdl = {kc: kc.pl0 for kc in self.curric.domain.kcs}
        self.state.mastery = stu_mdl
       
    def set_next_unit(self):
        compl_units = self.state.completed.keys()
        avail_units = [unit for unit in self.curric.units if unit not in compl_units]
        logger.debug("available units: %s" % str(avail_units))
        if len(avail_units) > 0:
            next_unit = avail_units[0]
            self.state.unit = next_unit
            self.state.completed[next_unit] = {} 
            return True
        else:
            logger.warning("No additional units available")
            return False

    def set_next_section(self):
        if self.state.unit == None:
            logger.debug("No unit currently set. Setting unit before setting section")
            self.set_next_unit()
        compl_sections = self.state.completed[self.state.unit].keys()
        avail_sections = [sect for sect in self.state.unit.sections if sect not in compl_sections]
        if len(avail_sections) > 0:
            next_sect = avail_sections[0]
            self.state.section = next_sect
            self.state.completed[self.state.unit][self.state.section] = {}
            return True
        else:
            logger.warning("No additional sections available")
            # Attempt to advance to next unit
            # self.set_next_unit()
            return False

    def get_next_prob(self):
        if self.state.section == None:
            logger.debug("No section set. Setting section before setting problem")
            self.set_next_section()
        sect_kcs = self.state.get_section_kc_mastery()
        avail_kcs = self.get_unmastered_kcs()
        if len( avail_kcs) > 0:
            target_kc = random.choice(list(avail_kcs.keys()))
            logger.debug("Total section kcs: %i\tUnmastered kcs: %i\ttarget kc: %s" % (len(sect_kcs), len(avail_kcs), str(target_kc._id)))
        else:
            logger.debug("Mastered all kcs. No additional necessary problems for this section")
            return False
        # Select random problem with target kc
        # Get list of problems with particular kc
        avail_probs = [prob for prob in self.state.section.problems if ((target_kc in prob.kcs) and (prob not in self.state.completed[self.state.unit][self.state.section]))]
        logger.debug("Current have %i available problems" % len(avail_probs))
        if len(avail_probs) > 0:
            prob = random.choice(avail_probs)
            self.state.problem = prob
            self.state.completed[self.state.unit][self.state.section][self.state.problem] = {}
            logger.debug("Selected problem: %s" % str(prob))

            # Set default first step
            self.state.step = None
            logger.debug("Selected step: %s" % str(self.state.step))
            self.get_next_step()
            logger.debug("Selected step: %s" % str(self.state.step))
            return True
        else:
            logger.debug("Finished with section. Advancing to next section")
            # self.set_next_section()
            return False

    def get_next_step(self):
        if self.state.problem is not None:
            avail_steps = [step for step in self.state.problem.steps if step not in self.state.completed[self.state.unit][self.state.section][self.state.problem]]
            if len(avail_steps) > 0:
                self.state.step = avail_steps[0]
                self.state.hints_avail = self.state.step.hints_avail
                self.state.hints_used = 0
                self.state.attempt = 0
                self.state.completed[self.state.unit][self.state.section][self.state.problem][self.state.step] = False
            else:
                raise Exception("no additional steps available")
        else:
            raise Exception("Cannot set next step if problem is not set")


    def get_unmastered_kcs(self):
        if self.state.section is not None:
            kcs = self.state.get_section_kc_mastery()
            return {kc: pl0 for kc, pl0 in kcs.items() if pl0 < self.mastery_thres}
        else:
            logger.error("Cannot get lsit of mastered kcs because section is not specified")
            raise Exception("Cannot get lsit of mastered kcs because section is not specified")

    def process_input(self, inpt):
        # Increment clock to time inpt occured
        self.session.increment_time(inpt.time)
        if isinstance(inpt, action.Attempt):
            logger.debug("Processing student attempt and updating kc specific pL0")
            kc = self.state.step.kcs[0]
            plt = self.state.mastery[kc]

            if self.state.attempt == 0:
                logger.debug("Is first attempt. updating skill")
                self.update_skill(kc, inpt.is_correct)
            else:
                logger.debug("Is not first attempt")

            plt1 = self.state.mastery[kc]
            self.log_input(inpt, plt, plt1)
            self.state.attempt = self.state.attempt + 1
            
            # Increment step or problem if problem is complete
            if inpt.is_correct:
                try:
                    self.get_next_step()
                except:
                    logger.debug("No more steps on current problem. getting next problem")
                    self.get_next_prob()

        elif isinstance(inpt, action.HintRequest):
            logger.debug("Processing student hint request")
            logger.debug("Hints avail: %i\tHints use: %s" % (self.state.hints_avail, self.state.hints_used))

            kc = self.state.step.kcs[0]
            plt = self.state.mastery[kc]

            if self.state.attempt == 0:
                logger.debug("Is first attempt. updating skill")
                self.update_skill(kc, False)
            else:
                logger.debug("Is not first attempt")

            plt1 = self.state.mastery[kc]
            self.log_input(inpt, plt, plt1)
            self.state.attempt = self.state.attempt + 1

            if self.state.hints_avail > 0: 
                self.state.hints_used = self.state.hints_used + 1
                self.state.hints_avail = self.state.hints_avail - 1
            else:
                logger.warning("No additional hints available")
        else:
            raise IOError("Unable to process input of type: %s" % str(type(inpt)))


    def update_skill(self, kc, is_correct):
        plt = self.state.mastery[kc]
        if is_correct:
            plt1_cond = plt * (1 - kc.ps) / ((plt * (1 - kc.ps)) + (1 - plt) * kc.pg)
        else:
            plt1_cond = plt * kc.ps / ((plt * kc.ps) + (1 - plt) * (1 -kc.pg))
        plt1 = plt1_cond + (1 - plt1_cond) * kc.pt
        self.state.mastery[kc] = plt1
        logger.debug("Outcome: %s\tPrior plt: %f\t updated plt: %f" % (str(is_correct), plt, plt1))


    def log_input(self, inpt, plt, plt1):
        if isinstance(inpt, action.Attempt):
            logger.debug("Logging student attempt")
            if inpt.is_correct:
                outcome = "Correct"
            else:
                outcome = "Incorrect"
        elif isinstance(inpt, action.HintRequest):
            logger.debug("Logging student hint request")
            outcome = "Hint"
        else:
            raise IOError("Unable to generate log entry for input of type: %s" % str(type(inpt)))

        kc = self.state.step.kcs[0]
        tx = TutorInput(self.session.last_input_time,
                        self.curric._id,
                        self.state.unit._id,
                        self.state.section._id,
                        self.state.problem._id,
                        self.state.step._id,
                        self.stu_id,
                        inpt.time,
                        outcome,
                        self.state.step.kcs,
                        plt,
                        plt1,
                        self.state.hints_used,
                        self.state.hints_avail,
                        self.state.attempt
             )
        
        tx._id = self.db.tutor_events.insert_one(tx.to_dict()).inserted_id
        logger.info("User Transaction: %s" % tx)
 

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


class SimpleTutorState:

    def __init__(self):
        # Tracking completed content in curriculum
        self.completed = {}
        # Tracking mastery of all skills within domain
        self.mastery = {}
        self.unit = None
        self.section = None
        self.problem = None
        self.step = None
        self.hints_avail = None
        self.hints_used = None
        self.first_attempt = None
        self.attempt = None

    def has_started(self):
        if self.prob == None:
            return False
        else:
            return True

    def get_section_kc_mastery(self):
        if self.section is not None:
            kc_mastery = {kc: self.mastery[kc] for kc in self.section.kcs}
            return kc_mastery
        else:
            logger.error("Can't get mastery of section kcs when no section is currently set")
            raise Exception("Can't get mastery of section kcs when no section is currently set")

