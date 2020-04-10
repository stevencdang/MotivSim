# classes to support logging for simulated tutor
import uuid
from collections.abc import Iterable
import logging

logger = logging.getLogger(__name__)

class Transaction:

    def __init__(self, time):
        self._id = uuid.uuid4()
        self.type = None
        self.time = time
        

class SessionStart(Transaction):
    
    def __init__(self, time):
        super().__init__(time)
        self.type = "Session Start"


class SessionEnd(Transaction):
    
    def __init__(self, time):
        super().__init__(time)
        self.type = "Session End"


class TutorInput(Transaction):
    
    def __init__(self, time,
                 curric_id,
                 unit_id, 
                 section_id,
                 prob_id,
                 step_id,
                 stu_id,
                 duration,
                 outcome,
                 kcs,
                 plt,
                 plt1,
                 hints_used,
                 hints_avail,
                 attempt
                 ):
        super().__init__(time)
        self.type = "Tutor Input"
        self.curric_id = curric_id
        self.unit_id = unit_id
        self.section_id = section_id
        self.prob_id = prob_id
        self.step_id = step_id
        self.stu_id = stu_id
        self.duration = duration
        self.outcome = outcome
        if isinstance(kcs, Iterable):
            logger.debug("Kcs is iterable: %s" % str(kcs))
            self.kcs = kcs
        elif kcs is None:
            logger.debug("Kcs is None: %s" % str(kcs))
            self.kcs = []
        else:
            logger.debug("Kcs is not iterable: %s" % str(kcs))
            self.kcs = [kcs]
        
        self.plt = plt
        self.plt1 = plt1
        self.hints_used = hints_used
        self.hints_avail = hints_avail
        self.attempt = attempt

