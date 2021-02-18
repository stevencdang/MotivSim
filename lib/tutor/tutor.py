# Definition of a simulated tutor managing internal state
# Add project root to python path
import sys
sys.path.append('..')

import logging
import uuid
import random
import datetime as dt

from . import action
from .session import Session
from .feedback import *
from log_db.tutor_log import TutorInput, SessionStart, SessionEnd
from log_db import mongo

logger = logging.getLogger(__name__)
# logger.setLevel(logging.DEBUG)

class Tutor:

    def __init__(self, curric, stu_id, mastery_thres=0.9):
        self._id = str(uuid.uuid4())
        self.curric = curric
        self.stu_id = stu_id
        self.mastery_thres = mastery_thres
        self.state = None

        self.init_student_model()
        self.init_tutor()


    def init_student_model(self):
        pass

    def init_tutor(self):
        pass

    def login(self, session, time):
        logger.debug(f"Logging start of new session: {time}")
        tx = SessionStart(stu_id=self.stu_id, session_id=session._id, time=time)
        logger.debug(f"session start: {str(tx.to_dict())}")
        return tx

    def logout(self, session, time):
        logger.debug("Logging end of session")
        tx = SessionEnd(stu_id=self.stu_id, session_id=session._id, time=time)
        logger.debug(f"session end: {tx.__dict__}")
        return tx

    def process_input(self, inpt, time):
        if isinstance(inpt, action.Attempt) or isinstance(inpt, action.Guess):
            return self.process_attempt(inpt, time)
        elif isinstance(inpt, action.HintRequest):
            return self.process_hint(inpt, time)
        elif isinstance(inpt, action.OffTask) or isinstance(inpt, action.FailedAttempt):
            logger.debug(f"Processing student action: {inpt.type}")
            return None, None
        else:
            raise IOError("Unable to process input of type: %s" % str(type(inpt)))

    def has_more(self):
        # this method should evaluate the current tutor state to return True if the tutor has more practice available for the student
        pass
    
    def process_attempt(self, inpt, time):
        pass

    def process_hint(self, inpt, time):
        pass



class SimpleTutor(Tutor):

    def __init__(self, curric, stu_id, mastery_thres=0.9):
        super().__init__(curric, stu_id, mastery_thres)

    def init_student_model(self):
        self.state = SimpleTutorState()
        stu_mdl = {kc: kc.pl0 for kc in self.curric.domain.kcs}
        self.state.mastery = stu_mdl

    def init_tutor(self):
        try:
            self.set_next_unit()
        except Exception as e:
            logger.warning(f"Error while initializing tutor: {str(e)}")
       
    def login(self, session, time):
        tx = super().login(session, time)
        self.state.last_tx_time = time
        return tx

    def process_attempt(self, inpt, time):
        logger.debug("Processing student attempt and updating kc specific pL0")
        kc = self.state.step.kcs[0]
        plt = self.state.mastery[kc]

        if self.state.attempt == 0:
            logger.debug("Is first attempt. updating skill")
            self.update_skill(kc, inpt.is_correct)
        else:
            logger.debug("Is not first attempt")

        plt1 = self.state.mastery[kc]
        tx = self.log_input(time, inpt, plt, plt1)
        self.state.attempt = self.state.attempt + 1
        
        # Increment step or problem if problem is complete
        if inpt.is_correct:
            self.update_state()

        fdbk = AttemptResponse(inpt.name, inpt.is_correct)
        return fdbk, tx

    def process_hint(self, inpt, time):
        logger.debug("Processing student hint request")
        logger.debug("Hints avail: %i\tHints use: %s" % (self.state.hints_avail, self.state.hints_used))

        kc = self.state.step.kcs[0]
        plt = self.state.mastery[kc]

        if self.state.attempt == 0:
            logger.debug("Is first attempt. updating skill")
            self.update_skill(kc, False) # Treat hint request as an incorrect on first attempt
        else:
            logger.debug("Is not first attempt")

        plt1 = self.state.mastery[kc]
        tx = self.log_input(time, inpt, plt, plt1)
        self.state.attempt = self.state.attempt + 1

        if self.state.hints_avail > 0: 
            self.state.hints_used = self.state.hints_used + 1
            self.state.hints_avail = self.state.hints_avail - 1
        else:
            logger.debug("No additional hints available")
        
        hint_msg = "Hint #%i" % self.state.hints_used
        fdbk = HintResponse(inpt.name, self.state.hints_used, self.state.hints_avail, hint_msg)
        return fdbk, tx

    def update_state(self):
        ### Update the tutor after completing a problem-step
        
        # Mark step as completed
        self.state.completed[self.state.unit][self.state.section][self.state.problem][self.state.step] = True
        # Increment step or problem if problem is complete
        completed_steps = self.state.completed[self.state.unit][self.state.section][self.state.problem]
        avail_steps = [step for step in self.state.problem.steps if step not in completed_steps]
        if len(avail_steps) > 0:
            self.set_next_step()
        else:
            try:
                self.set_next_prob()
                return
            except Exception as e:
                logger.debug(e)

            try:
                self.set_next_section()
                return
            except Exception as e:
                logger.debug(e)

            try:
                self.set_next_unit()
                return
            except Exception as e:
                logger.debug(e)
                logger.debug("Completed last unit. No more units in curriculum")
                self.state.is_done = True


    def has_more(self):
        # Returns true if there is mroe content for student to practice
        # There is always an unsolved step set if there is more practice available
        # if self.state.completed[self.state.unit][self.state.section][self.state.problem][self.state.step] == False:
        if not self.state.is_done:
            # Current step is not complete
            return True
        else:
            return False
        

    def set_next_unit(self):
        # logger.info("Beginning next unit")
        compl_units = self.state.completed.keys()
        avail_units = [unit for unit in self.curric.units if unit not in compl_units]
        logger.debug("available units: %s" % str(avail_units))
        if len(avail_units) > 0:
            next_unit = avail_units[0]
            self.state.unit = next_unit
            self.state.section = None
            self.state.problem = None
            self.state.step = None
            self.state.completed[next_unit] = {} 
            self.set_next_section()
            return True
        else:
            raise Exception("No additional units available")
            return False

    def set_next_section(self):
        # if self.state.unit == None:
            # logger.debug("No unit currently set. Setting unit before setting section")
            # self.set_next_unit()
        compl_sections = self.state.completed[self.state.unit].keys()
        # logger.debug(f"Num of sections: {len(compl_sections)}")
        avail_sections = [sect for sect in self.state.unit.sections if sect not in compl_sections]
        # logger.debug(f"Num of avail sections: {len(avail_sections)}")
        while len(avail_sections) > 0:
            next_sect = avail_sections[0]
            self.state.section = next_sect
            self.state.problem = None
            self.state.step = None
            self.state.completed[self.state.unit][self.state.section] = {}
            try:
                self.set_next_prob()
                return
            except Exception as e:
                logger.debug("Next section has no problems to complete")
                compl_sections = self.state.completed[self.state.unit].keys()
                avail_sections = [sect for sect in self.state.unit.sections if sect not in compl_sections]

        raise Exception("No additional sections available in this unit")

    def set_next_prob(self):
        sect_kcs = self.state.get_section_kc_mastery()
        avail_kcs = self.get_unmastered_kcs()
        if len( avail_kcs) > 0:
            target_kc = random.choice(list(avail_kcs.keys()))
            logger.debug("Total section kcs: %i\tUnmastered kcs: %i\ttarget kc: %s" % (len(sect_kcs), len(avail_kcs), str(target_kc._id)))
        else:
            raise Exception("Mastered all kcs. No additional problems to complete for this section")
            return False
                    
        avail_probs = [prob for prob in self.state.section.problems if ((target_kc in prob.kcs) and (prob not in self.state.completed[self.state.unit][self.state.section]))]
        logger.debug("Current have %i available problems" % len(avail_probs))
        if len(avail_probs) > 0:
            prob = random.choice(avail_probs)
            self.state.problem = prob
            self.state.step = None
            self.state.completed[self.state.unit][self.state.section][self.state.problem] = {}
            logger.debug("Selected problem: %s" % str(prob))
            self.set_next_step()
            return True
        else:
            logger.debug("Finished with section. Advancing to next section")
            raise Exception("No additional problems available in this section")
            # self.set_next_section()
            return False


    def set_next_step(self):
        if self.state.problem is not None:
            avail_steps = [step for step in self.state.problem.steps if step not in self.state.completed[self.state.unit][self.state.section][self.state.problem]]
            if len(avail_steps) > 0:
                # Steps are in order of expected completion, so set the next step in the list by default
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
            logger.error("Cannot get list of mastered kcs because section is not specified")
            raise Exception("Cannot get list of mastered kcs because section is not specified")


    def update_skill(self, kc, is_correct):
        plt = self.state.mastery[kc]
        if plt < self.mastery_thres:
            if is_correct:
                plt1_cond = plt * (1 - kc.ps) / ((plt * (1 - kc.ps)) + (1 - plt) * kc.pg)
            else:
                plt1_cond = plt * kc.ps / ((plt * kc.ps) + (1 - plt) * (1 -kc.pg))
            plt1 = plt1_cond + (1 - plt1_cond) * kc.pt
            self.state.mastery[kc] = plt1
            logger.debug("Outcome: %s\tPrior plt: %f\t updated plt: %f" % (str(is_correct), plt, plt1))
        else:
            # Hack for mastery learning to not allow student regression
            logger.debug("Not updating skill because already past mastery threshold")


    def log_input(self, time, inpt, plt, plt1):
        if isinstance(inpt, action.Attempt) or isinstance(inpt, action.Guess):
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
        duration = (time - self.state.last_tx_time).total_seconds()
        tx = TutorInput(time=time,
                        curric_id=self.curric._id,
                        unit_id=self.state.unit._id,
                        section_id=self.state.section._id,
                        prob_id=self.state.problem._id,
                        step_id=self.state.step._id,
                        stu_id=self.stu_id,
                        duration=duration,
                        outcome=outcome,
                        kcs=self.state.step.kcs,
                        plt=plt,
                        plt1=plt1,
                        hints_used=self.state.hints_used,
                        hints_avail=self.state.hints_avail,
                        attempt=self.state.attempt
                 )

        # Set last tx time to current time
        self.state.last_tx_time = time
            
        # tx._id = self.db.tutor_events.insert_one(tx.to_dict()).inserted_id
        logger.debug("User Transaction: %s" % tx)

        return tx
 


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
        self.is_done = False
        self.last_tx_time = None

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

    def __str__(self):
        return str(self.__dict__)

