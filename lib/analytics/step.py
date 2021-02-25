
import logging

import datetime as dt
import pandas as pd

logger = logging.getLogger(__name__)


class StepCalculator:

    def __init__(self, db):
        self.db = db

    def rollup_tx(self, tx):
        
        # Count outcomes
        outcomes = tx.pivot_table(index=['stu_id', 'unit_id', 'section_id', 'prob_id', 'step_id'], columns=['outcome'], values='duration', aggfunc=len, fill_value=0)
        # Count actions
        actions = tx.pivot_table(index=['stu_id', 'unit_id', 'section_id', 'prob_id', 'step_id'], columns=['action_type'], values='duration', aggfunc=len, fill_value=0)
        # Sum Time
        duration = tx.groupby(['stu_id', 'unit_id', 'section_id', 'prob_id', 'step_id'])['duration'].sum()
        # Count Attempts
        attempts = tx.groupby(['stu_id', 'unit_id', 'section_id', 'prob_id', 'step_id'])['duration'].count().rename("Attempts")
        # Add Plt
        plt = tx.groupby(['stu_id', 'unit_id', 'section_id', 'prob_id', 'step_id'])['plt'].agg(lambda x: x.min())
        # Plt1
        plt1 = tx.groupby(['stu_id', 'unit_id', 'section_id', 'prob_id', 'step_id'])['plt1'].agg(lambda x: x.max())
        # Learner Knowledge changes after first attempt. 
        lk = tx.groupby(['stu_id', 'unit_id', 'section_id', 'prob_id', 'step_id'])['learner_knowledge'].agg(lambda x: x.iloc[0])
        # Get time stamp for last tx
        time = tx.groupby(['stu_id', 'unit_id', 'section_id', 'prob_id', 'step_id'])['time'].agg(lambda x: x.sort_values().iloc[-1])

        steps = pd.concat([outcomes, actions, duration, attempts, plt, plt1, lk, time], axis=1)

        # Get kc
        steps = pd.merge(steps, tx.loc[:, ['stu_id', 'unit_id', 'section_id', 'prob_id', 'step_id', 'kc' ]].drop_duplicates(), on=['stu_id', 'unit_id', 'section_id', 'prob_id', 'step_id'], how='inner')

        steps = steps.sort_values(by="time")
        return steps


    def label_knowledge(self, d, know_lvls=None):
        if know_lvls is None:
            know_lvls = {'low_knowledge': (0, 0.2),
                         'low-mid_knowledge': (0.3, 0.5), 
                         'mid_knowledge': (0.5, 0.7), 
                         'mid-high_knowledge': (0.7, 0.9),
                         'high_knowledge': (0.9, 1)
                        }

        def get_label(x):
            for k in know_lvls:
                if (x <= know_lvls[k][1]) & (x > know_lvls[k][0]):
                    return k

        result = d['learner_knowledge'].apply(get_label).rename('knowledge_level')
        d = pd.concat([result, pd.get_dummies(result)], axis=1)
        return d

    def count_practice_challenge(self, steps, know_lvls=None):
        
        if know_lvls is None:
            know_lvls = {'low_knowledge': (0, 0.2),
                         'low-mid_knowledge': (0.3, 0.5), 
                         'mid_knowledge': (0.5, 0.7), 
                         'mid-high_knowledge': (0.7, 0.9),
                         'high_knowledge': (0.9, 1)
                        }

        # Count opportunities at each knowledge level
        kc_prac = steps.groupby('stu_id')['low_knowledge'].sum()

        for col in know_lvls:
            if col != 'low_knowledge':
                kc_prac = pd.concat([kc_prac, steps.groupby('stu_id')[col].sum()], axis=1)

        return kc_prac

