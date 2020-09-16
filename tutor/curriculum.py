# Class definitions to support defining a curriculum

import logging
import uuid
import random
import math

logger = logging.getLogger(__name__)

class Curriculum:

    def __init__(self,
                 domain):
        self._id = uuid.uuid4()
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
        self._id = uuid.uuid4()
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
        self._id = uuid.uuid4()
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
        self._id = uuid.uuid4()
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
        self._id = uuid.uuid4()
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



class SimpleCurriculum(Curriculum):

    def generate(self,
                 num_units=1, 
                 num_sections=1,
                 num_practice=20):
        logger.debug("Generating curriculum for %s" % type(self))

        self.gen_units(num_units)

        self.gen_sections(num_sections)

        for i, unit in enumerate(self.units):
            for j, section in enumerate(unit.sections):
                problems = self.gen_problems(section, num_practice)

                logger.debug("Section problems before add: %i" % len(unit.sections[j].problems))
                section.problems = problems
                logger.debug("Section problems after add: %i" % len(unit.sections[j].problems))


       
    def gen_units(self, num_units):
        num_kcs = len(self.domain.kcs)

        # Evenly divide kcs across units and sections
        n = math.floor(num_kcs/num_units)
        n_unit_kcs = [n if i < (num_units - 1) else num_kcs - n*(num_units-1) for i in range(num_units)]
        logger.debug("kcs by unit: %s" % str(n_unit_kcs))
        assigned_kcs = []
        for n in n_unit_kcs:
            unit = Unit(self.domain_id, self._id)

            avail_kcs = [kc for kc in self.domain.kcs if kc not in assigned_kcs]
            kcs = random.sample(avail_kcs, k=n)
            logger.debug("assigning kcs: %s" % str(kcs))
            unit.kcs = kcs
            assigned_kcs.extend(kcs)
        
            self.units.append(unit)


    def gen_sections(self, num_sections):
    
        for i, unit in enumerate(self.units):
            # divide kcs evenly across sections
            n_unit_kcs = len(unit.kcs)
            n = math.floor(n_unit_kcs/num_sections)
            n_sect_kcs = [n if i < (num_sections - 1) else n_unit_kcs - n*(num_sections-1) for i in range(num_sections)]
            logger.debug("kcs per section: %s" % str(n_sect_kcs))
            assigned_kcs = []
            for n_kcs in n_sect_kcs:
                # Set number of steps according to fixed constants
                m_steps = math.floor(random.gauss(1,0))
                if m_steps == 0:
                    m_steps = 1
                sd_steps = 0
                section = Section(self.domain_id, self._id, unit._id, m_steps, sd_steps)
                avail_kcs = [kc for kc in unit.kcs if kc not in assigned_kcs]
                sect_kcs = random.sample(avail_kcs, k=n_kcs)
                logger.debug("Assigning kcs to section: %s" % str(sect_kcs))
                section.kcs = sect_kcs
                assigned_kcs.extend(sect_kcs)
                unit.sections.append(section)
            


    def gen_problems(self, section, num_practice):

        kc_practice = {kc: 0 for kc in section.kcs}
        avail_kcs = [kc for kc in kc_practice.keys()]
        num_avail = len(avail_kcs)
        problems = []
        while len(avail_kcs) > 0:
            n_steps = round(random.gauss(section.m_steps, section.sd_steps))
            if n_steps < 1:
                n_steps = 1
            prob = Problem(self.domain_id, self._id, section.unit_id, section._id)
            prob_kcs = random.choices(avail_kcs, k=n_steps)
            prob.kcs = prob_kcs
            for kc in prob.kcs:
                kc_practice[kc] = kc_practice[kc] + 1
            avail_kcs = [kc for kc in kc_practice.keys() if kc_practice[kc] < num_practice]
            prob.steps = self.gen_steps(prob)
            problems.append(prob)
            # if num_avail > len(avail_kcs):
                # logger.debug("Available kcs: %i\tNum Problems: %i\tloop#: %i" % (num_avail, len(problems), loops))
            # num_avail = len(avail_kcs)
        return problems

    def gen_steps(self, problem):
        steps = []
        for kc in problem.kcs:
            m_time = round(random.gauss(kc.m_time, kc.sd_time))
            sd_time = round(m_time / 4)
            logger.debug("New step mean time: %f\t sd time: %f" % (m_time, sd_time))
            step = Step(self.domain_id, self._id, 
                        problem.unit_id, problem.section_id, 
                        problem._id, m_time, sd_time)
            step.kcs = [kc]
            steps.append(step)
        return steps




