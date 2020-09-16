# classes to support logging for simulated tutor
import uuid
from collections.abc import Iterable
import logging
import copy
import json
from uuid import UUID

logger = logging.getLogger(__name__)

class Transaction:

    def __init__(self, time):
        self._id = uuid.uuid4()
        self.type = None
        self.time = time

    def to_dict(self):
        return self.__dict__
        

class TransactionEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, UUID):
            # if the obj is uuid, we simply return the value of uuid
            return obj.hex
        elif hasattr(obj, 'isoformat'):
            return obj.isoformat() 
        else:
            return json.JSONEncoder.default(self, obj)


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


    def __str__(self):
        out = copy.deepcopy(self.__dict__)
        out['kcs'] = [str(kc) for kc in out['kcs']]
        return str(self.to_dict())


    def to_dict(self):
        out = copy.deepcopy(self.__dict__)

        # logger.info(out['kcs'])
        # logger.info(type(out['kcs'][0].__dict__))
        # logger.info(str(out['kcs'][0].__dict__))
        out['kcs'] = [kc.__dict__ for kc in out['kcs']]
        return out




