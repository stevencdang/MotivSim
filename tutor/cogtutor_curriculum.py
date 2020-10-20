# Class definitions to support defining a simple curriculum for testing

import logging
import uuid
from numpy import random as nprand
import random
import math
from .curriculum import *

import numpy as np

logger = logging.getLogger(__name__)

class CogTutorCurriculum(Curriculum):

    def generate(self,
                 num_units=60, 
                 mean_sections=4,
                 stdev_sections=1.76,
                 mean_unit_kcs=22,
                 stdev_unit_kcs=23,
                 section_kcs_lambda=4,
                 num_practice=100,
                 mean_steps=10,
                 stdev_steps=4,
                 mean_prob_kcs=6,
                 stdev_prob_kcs=3,
                 mastery_thres=0.9
                 ):
        logger.debug("Generating curriculum for %s" % type(self))

        self.gen_units(num_units, mean_sections, stdev_sections, mean_unit_kcs, stdev_unit_kcs, section_kcs_lambda, mastery_thres)
        logger.info("Generated %i units with with a total of %i kcs" % (len(self.units), len(self.domain.kcs)))

        for unit in self.units:
            for section in unit.sections:
                self.gen_section_problems(section, num_practice)

        # self.gen_sections(num_sections)

        # for i, unit in enumerate(self.units):
            # for j, section in enumerate(unit.sections):
                # problems = self.gen_problems(section, num_practice)

                # logger.debug("Section problems before add: %i" % len(unit.sections[j].problems))
                # section.problems = problems
                # logger.debug("Section problems after add: %i" % len(unit.sections[j].problems))


       
    def gen_units(self, num_units, mean_sections, stdev_sections, mean_unit_kcs, stdev_unit_kcs, section_kcs_lambda, mastery_thres):
        for i in range(num_units):
            num_sections = round(random.gauss(mean_sections, stdev_sections))
            if num_sections < 1:
                num_sections = 1
            logger.debug("Generating unit #%i with %i sections" % (i, num_sections))
            
            
            unit = Unit(self.domain_id, self._id)
	 
            for j in range(num_sections):
                num_kcs = round(nprand.exponential(section_kcs_lambda))
                if num_kcs < 1:
                    num_kcs = 1
                
                logger.debug("Generating section #%i with %i kcs" % (j, num_kcs))
                section = Section(self.domain_id, self._id, unit._id)
                kcs = self.domain.generate_kcs(num_kcs, mastery_thres)
                unit.kcs.extend(kcs)
                section.kcs.extend(kcs)
                unit.sections.append(section)
                logger.debug("Section has %i kcs" % len(section.kcs))
            
            self.units.append(unit)
            logger.debug("Generated unit #%i with %i sections with a total of %i kcs" % (i, num_sections, num_kcs))

        logger.debug("********************************** done generating units ******************************")


    def gen_section_problems(self, section, num_practice):
        logger.debug("Generating %i practice opportunities per kc for section, %s" % (num_practice, section._id))

        practice_counts = {kc: 0 for kc in section.kcs}
        max_kcs = len(section.kcs)
        while max_kcs > np.sum([count >= num_practice for count in practice_counts.values()]):
            num_steps = round(random.gauss(section.m_steps, section.sd_steps))
            if num_steps < 1:
                num_steps = 1
            num_kcs = round(random.triangular(1, num_steps, num_steps))
            if num_kcs > max_kcs:
                num_kcs = max_kcs
            # logger.debug("Generating problem with %i steps and %i kcs" % (num_steps, num_kcs))
            
            prob = Problem(self.domain_id, self._id, section.unit_id, section._id)
            prob.kcs = random.sample(section.kcs, num_kcs)
            if num_kcs == num_steps:
                step_kcs = prob.kcs
            else:
                # Assign kcs to steps so that all kcs are assigned
                all_assigned = False
                while not all_assigned:
                    # logger.debug("Attempting to assign kcs")
                    step_kcs = [random.choice(prob.kcs) for i in range(num_steps)]
                    all_assigned = len(prob.kcs) == np.sum([kc in step_kcs for kc in prob.kcs])

            for step_kc in step_kcs:
                m_time = round(random.gauss(step_kc.m_time, step_kc.sd_time))
                sd_time = round(m_time / 4)
                step = Step(self.domain_id, self._id, 
                            section.unit_id, section._id, prob._id, 
                            m_time, sd_time)
                step.kcs = [step_kc]
                prob.steps.append(step)
                practice_counts[step_kc] = practice_counts[step_kc] + 1
            section.problems.append(prob)
            logger.debug("Added problem with %i steps and %i kcs" % (len(prob.steps), len(prob.kcs)))
            logger.debug("Number of problems: %i" % len(section.problems))

            logger.debug("Total kcs: %i\tkcs with completed practice:\n %s" % (len(section.kcs), str(practice_counts)))
