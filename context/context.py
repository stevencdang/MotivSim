# Add project root to python path
import sys
sys.path.append('..')

from tutor.action import Attempt, HintRequest

class Context:

    def get_actions(self):
        pass


class SimpleTutorContext(Context):

    def __init__(self, cur_prob, cur_step, hints_avail,
                 hints_used, time, kc, attempt):
        self.cur_problem = cur_prob
        self.cur_step = cur_step
        self.hints_avail = hints_avail
        self.hints_used = hints_used
        self.time = time
        self.kc = kc
        self.attempt = attempt
