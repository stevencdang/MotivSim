# Base class for a learner

import uuid


class Learner:

    def __init__(self, domain):
        self._id = uuid.uuid4()
        self.domain_id = domain._id
