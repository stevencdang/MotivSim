# Class for supporting generating domains and curriculums

import logging
import uuid
import random

from .cogtutor_curriculum import CogTutorCurriculum
from .domain import Domain, ContKCDomain

logger = logging.getLogger(__name__)

class CurriculumFactory:

    def gen_curriculum(domain_params, curric_params):
        # Define an empty domain with hyperparamters
        if 'm_l0_sd' in domain_params:
            domain = ContKCDomain()
        else:
            domain = Domain()

        domain.set_kc_hyperparams(**domain_params)

        # Generate Curriculum
        # Generating the Curriculum and domain together
        curric = CogTutorCurriculum(domain)
        curric.generate(**curric_params)

        return domain, curric



