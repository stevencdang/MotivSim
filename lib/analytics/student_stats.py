# Modele for methods for performing analytics
# Author: Steven Dang stevencdang.com

import logging
import sys
import math
import random
import uuid
import os
import copy
from collections.abc import Iterable
from datetime import datetime as dt
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

from pymongo import MongoClient
from os import mkdir, listdir, path
from collections.abc import Iterable

from tutor.domain import Domain
from tutor.curriculum_factory import CurriculumFactory
from tutor.simple_curriculum import SimpleCurriculum
from tutor.tutor import SimpleTutor
from tutor.action import Attempt, HintRequest

from learner.selfeff_learner import SelfEfficacyLearner
from learner.modular_learner import ModularLearner
from learner.binary_skill_cog import BinarySkillCognition
from learner.decider import *

from simulate.modlearner_simulation import ModLearnerSimulation
from simulate.simulation import SimulationBatch

from log_db import mongo
from log_db.curriculum_mapper import DB_Curriculum_Mapper

logger = logging.getLogger(__name__)


class StudentStatCalc:

    def __init__(self, db):
        self.db = db


    def get_stu_parameters(self, sids):
        presim_students = pd.DataFrame(self.db.students.find({"_id": {'$in':  sids}}))
        sim_students = pd.DataFrame(self.db.finalsimstudents.find({"_id": {'$in':  sids}}))
        sim_students.rename(columns={'skills': 'final skills', 
                                     'total_attempts': 'final total attempts',
                                     'total_success': 'final total success'}, inplace=True)
        logger.debug("pre-sim students: %s" % str(presim_students.shape))
        logger.debug("post-sim students: %s" % str(sim_students.shape))

        sim_students = presim_students.merge(sim_students[['_id', 'final skills', 'final total attempts', 'final total success']], how='right', on=['_id'])
        sim_students['pre-sim total mastery'] = sim_students.apply(lambda x: np.sum(list(x['skills'].values())), axis=1)
        sim_students['final-sim total mastery'] = sim_students.apply(lambda x: np.sum(list(x['final skills'].values())), axis=1)
        sim_students['total skills'] = sim_students.apply(lambda x: len(list(x['skills'].values())), axis=1)
        sim_students['pre-sim pct mastery'] = sim_students.apply(lambda x: x['pre-sim total mastery'] / x['total skills'], axis=1)
        sim_students['final-sim pct mastery'] = sim_students.apply(lambda x: x['final-sim total mastery'] / x['total skills'], axis=1)
        sim_students['final-sim total unmastered'] = sim_students.apply(lambda x: x['total skills'] - x['final-sim total mastery'], axis=1)
        sim_students['pct success'] = sim_students.apply(lambda x: x['final total success'] / x['final total attempts'], axis=1)

        sim_students['values'] = sim_students.apply(lambda x: x['decider']['values'], axis=1)
        sim_students['diligence'] = sim_students.apply(lambda x: x['decider']['diligence'], axis=1)
        sim_students['cog_ability'] = sim_students.apply(lambda x: x['cognition']['ability'], axis=1)
        sim_students.index = sim_students['_id']
        sim_students.drop(['_id'], axis=1, inplace=True)
        return sim_students

    def decision_stats(self, sids):
        decisions = pd.DataFrame(self.db.decisions.find({"student_id": {'$in': sids}}))
        decisions['learner_knowledge'] = decisions['learner_knowledge'].apply(lambda x: x[0] if isinstance(x, Iterable) else x)
        decisions['kcid'] = decisions['kc'].apply(lambda x: x['_id'])

        return decisions

    def action_stats(self, sids):
        actions = pd.DataFrame(self.db.actions.find({"student_id": {'$in': sids}}))
        actions['type'] = actions.apply(lambda x: x['action']['name'], axis=1)
        actions['duration'] = actions.apply(lambda x: x['action']['time'], axis=1)
        logger.debug(f"Number of actions: {actions.shape}")

        action_dist = actions.groupby('student_id')['type'].value_counts().reset_index(name="count")
        action_dist = action_dist.pivot(index='student_id', columns='type', values='count')
        action_dist['total actions'] = action_dist.sum(axis=1)
        for col in action_dist.columns:
            if col != 'total actions':
                action_dist['Pct %s' % col] = action_dist.apply(lambda x: x[col]/x['total actions'], axis=1)
                action_dist.head()
        return action_dist

    def total_tx_stats(self, sids):
        # Calculates total time, activity, and proportions of outcomes
        tx = pd.DataFrame(self.db.tutor_events.find({"stu_id": {'$in': sids}, 'type': "TutorInput"}))
        # Add kc field that reduces list of kcs to 1 kc
        tx['kc'] = tx.apply(lambda x: x['kcs'][0]['_id'], axis=1)

        # Total Transaction counts
        stu_stats = tx.groupby('stu_id').agg({'_id': 'count', 
                                              'duration': np.sum,
                                             })
        stu_stats.rename(columns={'_id': "Total Tx",
                                  'duration': 'Total Time'}, 
                                  inplace = True)
        stu_stats['Total Time(hours)'] = stu_stats['Total Time'].apply(lambda x: x / 3600)
        logger.debug("Number of students: %i" % stu_stats.shape[0])
        logger.debug(stu_stats["Total Tx"].describe())

        # Total of each outcome
        d = tx.groupby(['stu_id','outcome'])['_id'].count().reset_index().pivot(
                index='stu_id', columns='outcome', values='_id')

        # Prorporation of each outcome
        stu_stats = pd.concat([stu_stats, d], axis=1)
        stu_stats['Pct Correct'] = stu_stats['Correct'] / stu_stats['Total Tx']
        stu_stats['Pct Hint'] = stu_stats['Hint'] / stu_stats['Total Tx']
        stu_stats['Pct Incorrect'] = stu_stats['Incorrect'] / stu_stats['Total Tx']

        return stu_stats

    def stu_prob_stats(self, sids):
        # Calculates total time, activity, and proportions of outcomes
        tx = pd.DataFrame(db.tutor_events.find({"stu_id": {'$in': sids}, 'type': "Tutor Input"}))
        # Add kc field that reduces list of kcs to 1 kc
        tx['kc'] = tx.apply(lambda x: x['kcs'][0]['_id'], axis=1)

        step_stats = tx.groupby(['stu_id', 'unit_id', 'section_id', 'prob_id', 'step_id'])['duration'].agg(['sum', 'count']).reset_index()
        stu_prob_stats = step_stats.groupby('stu_id')['count'].describe()
        stu_prob_stats.columns = ["Step Attempt %s" % col for col in stu_prob_stats.columns]
        d = step_stats.groupby('stu_id')['sum'].describe()
        d.columns = ["Step Duration %s" % col for col in d.columns]
        stu_prob_stats = pd.concat([stu_prob_stats, d], axis=1)

        return stu_prob_stats

    def stu_kc_stats(self, sids):
        # Calculates total time, activity, and proportions of outcomes
        tx = pd.DataFrame(db.tutor_events.find({"stu_id": {'$in': sids}, 'type': "Tutor Input"}))
        # Add kc field that reduces list of kcs to 1 kc
        tx['kc'] = tx.apply(lambda x: x['kcs'][0]['_id'], axis=1)

        # kc_stats = tx[['stu_id', 'kc', 'step_id']].drop_duplicates().groupby(['stu_id', 'kc']).count()
        stu_kc_stats = tx[['stu_id', 'kc', 'step_id']].drop_duplicates().groupby(['stu_id', 'kc']).count().reset_index()
        stu_kc_stats.rename(columns={'step_id': 'kc opportunities'}, inplace=True)

        return stu_kc_stats

