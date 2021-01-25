# Add project root to python path
import sys
sys.path.append('..')

from tutor.action import *

class Context:

    def get_actions(self):
        pass


class SimpleTutorContext(Context):

    def __init__(self, tutor_state, learner_state, time):

        self.tutor_state = tutor_state
        self.cur_problem = tutor_state.problem
        self.cur_step = tutor_state.step
        self.hints_avail = tutor_state.hints_avail
        self.hints_used = tutor_state.hints_used
        self.kc = tutor_state.step.kcs[0]
        self.attempt = tutor_state.attempt
        
        self.learner_state = learner_state
        self.learner_off_task = learner_state['off_task']
        self.learner_kc_knowledge = learner_state['skills'][self.kc._id]

        self.time = time

    def get_actions(self):

        actions = [Attempt, Guess]
        if self.hints_avail > 0:
            actions.append(HintRequest)
        if not self.learner_off_task:
            actions.append(OffTask)
        return actions


class ClassSessionContext(SimpleTutorContext):


    def __init__(self, tutor_state, learner_state, session, time):
        super().__init__(tutor_state, learner_state, time)
        self.session = session


    def get_actions(self):
        actions = super().get_actions()
        actions.append(StopWork)
        return actions

