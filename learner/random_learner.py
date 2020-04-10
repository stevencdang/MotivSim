# Class for a test student that makes decisions randomly

from .learner import Learner


class RandomLearner(Learner):

    def __init__(self, domain):
        super().__init__(domain)
