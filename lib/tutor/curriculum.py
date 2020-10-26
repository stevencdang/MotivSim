# Class definitions to support defining a curriculum

import logging
import uuid
import random
import math

logger = logging.getLogger(__name__)

class Curriculum:

    def __init__(self,
                 domain):
        self._id = str(uuid.uuid4())
        self.domain = domain
        self.domain_id = domain._id
        self.units = []

    def to_db_object(self):
        return {'_id': self._id,
                'domain_id': self.domain_id,
                'units': [unit._id for unit in self.units]
               }



class Unit:

    def __init__(self,
                 domain_id,
                 curric_id):
        self._id = str(uuid.uuid4())
        self.curric_id = curric_id
        self.domain_id = domain_id
        self.sections = []
        self.kcs = []

    def to_db_object(self):
        return {'_id': self._id,
                'domain_id': self.domain_id,
                'curric_id': self.curric_id,
                'sections': [section._id for section in self.sections],
                'kcs': [kc._id for kc in self.kcs]
               }


class Section:

    def __init__(self,
                 domain_id,
                 curric_id,
                 unit_id,
                 m_steps=4,
                 sd_steps=2,
                 ):
        self._id = str(uuid.uuid4())
        self.domain_id = domain_id
        self.curric_id = curric_id
        self.unit_id = unit_id
        self.problems = []
        self.kcs = []
        # Distribution of steps per problem
        self.m_steps=m_steps
        self.sd_steps=sd_steps

    def to_db_object(self):
        return {'_id': self._id,
                'domain_id': self.domain_id,
                'curric_id': self.curric_id,
                'unit_id': self.unit_id,
                'problems': [problem._id for problem in self.problems],
                'kcs': [kc._id for kc in self.kcs],
                'm_steps': self.m_steps,
                'sd_steps': self.sd_steps
               }

class Problem:

    def __init__(self,
                 domain_id,
                 curric_id,
                 unit_id,
                 section_id,
                 ):
        self._id = str(uuid.uuid4())
        self.domain_id = domain_id
        self.curric_id = curric_id
        self.unit_id = unit_id
        self.section_id = section_id
        self.steps = []
        self.kcs = []

    def to_db_object(self):
        return {'_id': self._id,
                'domain_id': self.domain_id,
                'curric_id': self.curric_id,
                'unit_id': self.unit_id,
                'section_id': self.section_id,
                'steps': [step._id for step in self.steps],
                'kcs': [kc._id for kc in self.kcs],
               }

class Step:

    def __init__(self,
                 domain_id,
                 curric_id,
                 unit_id,
                 section_id,
                 prob_id,
                 m_time=None,
                 sd_time=None,
                 hints=3,
                 ):
        self._id = str(uuid.uuid4())
        self.domain_id = domain_id
        self.curric_id = curric_id
        self.unit_id = unit_id
        self.section_id = section_id
        self.prob_id = prob_id
        self.kcs = []
        self.hints_avail = hints
        # Distribution of time to solve this step
        self.m_time = m_time
        self.sd_time = sd_time

    def to_db_object(self):
        return {'_id': self._id,
                'domain_id': self.domain_id,
                'curric_id': self.curric_id,
                'unit_id': self.unit_id,
                'section_id': self.section_id,
                'prob_id': self.prob_id,
                'kcs': [kc._id for kc in self.kcs],
                'hints_avail': self.hints_avail,
                'm_time': self.m_time,
                'sd_time': self.sd_time
               }



