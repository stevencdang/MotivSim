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
import datetime as dt
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
from learner.cognition import *
from learner.decider import *

from simulate.modlearner_simulation import ModLearnerSimulation
from simulate.simulation import SimulationBatch

from .featurization import TransactionAnnotator

from log_db import mongo
from log_db.curriculum_mapper import DB_Curriculum_Mapper

logger = logging.getLogger(__name__)


class StudentStatCalc:

    def __init__(self, db):
        self.db = db

    def get_stu_parameters(self, sids):
        sim_students = self.get_stu_attributes(sids)
        sim_students = pd.concat([sim_students, self.get_mastery(sids)], axis=1)
        return sim_students

    def get_stu_attributes(self, sids):
        keep_state_fields = []
        keep_attr_fields = []
        drop_cols = ['domain_id', 'type', 'skills', 'values', 'cog', 'decider', 'state_fields', 'attribute_fields']

        # Get sample for reviewing available fields
        sample = pd.Series(self.db.students.find_one({"_id": {'$in':  sids}}))
        drop_cols.extend([col for col in sample['state_fields'] if col not in keep_state_fields])
        drop_cols.extend([col for col in sample['attribute_fields'] if col not in keep_attr_fields])
        
        sample = pd.Series(self.db.students.find_one({"_id": {'$in':  sids}}))
        sim_students = pd.DataFrame(self.db.students.find({"_id": {'$in':  sids}}))
        logger.debug("sim students: %s" % str(sim_students.shape))
        
        # Extract Values from decider module (to be removed at the end)
        sim_students['values'] = sim_students.apply(lambda x: x['decider']['values'], axis=1)
        for val_type in sim_students['values'][0].keys():
            sim_students[f"{val_type}_value"] = sim_students.apply(lambda x: x['values'][val_type], axis=1)

        sim_students['diligence'] = sim_students.apply(lambda x: x['decider']['diligence'], axis=1)
        

        # Pull attributes out of modules
        cog_attr = ['ability']
        dec_attr = ['self_eff', 'interest']
        for attr in cog_attr:
           if attr in sample['cog'].keys():
            sim_students[f"cog_{attr}"] = sim_students.apply(lambda x: x['cog'][attr], axis=1)
        for attr in dec_attr:
           if attr in sample[ 'decider'].keys():
            sim_students[f"dec_{attr}"] = sim_students.apply(lambda x: x['decider'][attr], axis=1)

        # Drop unnecessary columns
        sim_students.index = sim_students['_id']
        sim_students.drop(['_id'], axis=1, inplace=True)
        sim_students.drop(drop_cols, axis=1, inplace=True)
        
        return sim_students

    def get_mastery(self, stus, mastery_thres=0.9):
        val = list(stus['skills'].iloc[0].values())[0] # Arbitrary skill parameter
        is_not_binary = (type(val) == int) or (type(val) == float)
        if is_not_binary:
            # Continuous skill
            out = pd.DataFrame(index=stus.index, columns=['total mastery', 'total skill'])
            out['total mastery'] = stus.apply(lambda x: np.sum([1 if d >= mastery_thres else 0 for d in list(x['skills'].values())]), axis=1)
            out['total skill'] = stus.apply(lambda x: np.sum(list(x['skills'].values())), axis=1)
        else:
            # Binary skill
            logger.warning("************* type is binary skills ***********")
            out = pd.DataFrame(index=stus.index, columns=['total mastery'])
            out['total mastery'] = stus.apply(lambda x: np.sum(list(x['skills'].values())), axis=1)
            

        return out

    def calc_student_learning(self, presim, finalsim):
        d = pd.DataFrame(index=presim.index, columns=['pres-sim total mastery', 'final-sim total mastery'])
        d['pre-sim total mastery'] = presim['total mastery']
        d['final-sim total mastery'] = finalsim['total mastery']
        d['total mastered'] = finalsim['total mastery'] - presim['total mastery'] 
        d['total skills'] = presim.apply(lambda x: len(list(x['skills'].values())), axis=1)
        d['pre-sim pct mastery'] = d.apply(lambda x: x['pre-sim total mastery'] / x['total skills'], axis=1)
        d['final-sim pct mastery'] = d.apply(lambda x: x['final-sim total mastery'] / x['total skills'], axis=1)
        d['final-sim total unmastered'] = d['total skills'] - d['final-sim total mastery']


        if 'total skill' in presim.columns:
            logger.debug("Students have skill and mastery columns. Calculating change in total skill")
            d['pre-sim total skill'] = presim['total skill']
            d['final-sim total skill'] = finalsim['total skill']
            d['total learning'] = d['final-sim total skill'] - d['pre-sim total skill'] 

        return d
        
    # def get_mastery(self, sids, mastery_thres=0.9):
        # keep_state_fields = []
        # keep_attr_fields = []
        # drop_cols = ['domain_id', 'type', 'skills', 'cog', 'decider', 'state_fields', 'attribute_fields']

        # sample = pd.Series(self.db.students.find_one({"_id": {'$in':  sids}}))
        # drop_cols.extend([col for col in sample['state_fields'] if col not in keep_state_fields])
        # drop_cols.extend([col for col in sample['attribute_fields'] if col not in keep_attr_fields])
        
        # presim_students = pd.DataFrame(self.db.students.find({"_id": {'$in':  sids}}))
        # sim_students = pd.DataFrame(self.db.finalsimstudents.find({"_id": {'$in':  sids}}))
        # sim_students.rename(columns={'skills': 'final skills', 
                                     # 'total_attempts': 'final total attempts',
                                     # 'total_success': 'final total success'}, inplace=True)
        # logger.debug("pre-sim students: %s" % str(presim_students.shape))
        # logger.debug("post-sim students: %s" % str(sim_students.shape))

        # sim_students = presim_students.merge(sim_students[['_id', 'final skills', 'final total attempts', 'final total success']], how='right', on=['_id'])
        
        # val = list(sample['skills'].values())[0]
        # is_not_binary = (type(val) == int) or (type(val) == float)
        # if is_not_binary:
            # # Continuous skill
            # sim_students['pre-sim total mastery'] = sim_students.apply(lambda x: np.sum([1 if d >= mastery_thres else 0 for d in list(x['skills'].values())]), axis=1)
            # sim_students['pre-sim total skill'] = sim_students.apply(lambda x: np.sum(list(x['skills'].values())), axis=1)
            # sim_students['final-sim total mastery'] = sim_students.apply(lambda x: np.sum([1 if d >= mastery_thres else 0 for d in list(x['final skills'].values())]), axis=1)
            # sim_students['final-sim total skill'] = sim_students.apply(lambda x: np.sum(list(x['final skills'].values())), axis=1)
            # sim_students['total learning'] = sim_students['final-sim total skill'] - sim_students['pre-sim total skill'] 
            # sim_students['total mastered'] = sim_students['final-sim total mastery'] - sim_students['pre-sim total mastery'] 
        # else:
            # # Binary skill
            # logger.warning("************* type is binary skills ***********")
            # sim_students['pre-sim total mastery'] = sim_students.apply(lambda x: np.sum(list(x['skills'].values())), axis=1)
            # sim_students['final-sim total mastery'] = sim_students.apply(lambda x: np.sum(list(x['final skills'].values())), axis=1)

        # sim_students['total skills'] = sim_students.apply(lambda x: len(list(x['skills'].values())), axis=1)
        # sim_students['pre-sim pct mastery'] = sim_students.apply(lambda x: x['pre-sim total mastery'] / x['total skills'], axis=1)
        # sim_students['final-sim pct mastery'] = sim_students.apply(lambda x: x['final-sim total mastery'] / x['total skills'], axis=1)
        # sim_students['final-sim total unmastered'] = sim_students.apply(lambda x: x['total skills'] - x['final-sim total mastery'], axis=1)

        # sim_students.index = sim_students['_id']
        # sim_students.drop(['_id'], axis=1, inplace=True)
        # sim_students.drop(drop_cols, axis=1, inplace=True)

        # return sim_students

    def decision_stats(self, sids):
        decisions = pd.DataFrame(self.db.decisions.find({"student_id": {'$in': sids}}))
        decisions['learner_knowledge'] = decisions['learner_knowledge'].apply(lambda x: x[0] if isinstance(x, Iterable) else x)
        decisions['kcid'] = decisions['kc'].apply(lambda x: x['_id'])

        return decisions

    def get_action_counts(self, sids):
        actions = pd.DataFrame(self.db.actions.find({"student_id": {'$in': sids}}))
        actions['type'] = actions.apply(lambda x: x['action']['type'], axis=1)
        actions['duration'] = actions.apply(lambda x: x['action']['time'], axis=1)
        logger.debug(f"Number of actions: {actions.shape}")

        action_dist = actions.groupby('student_id')['type'].value_counts().reset_index(name="count")
        action_dist = action_dist.pivot_table(index='student_id', columns='type', values='count', fill_value=0)
        action_dist['total actions'] = action_dist.sum(axis=1)
        for col in action_dist.columns:
            if col != 'total actions':
                action_dist['Pct %s' % col] = action_dist.apply(lambda x: x[col]/x['total actions'], axis=1)
                action_dist.head()

        return action_dist


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
        d = tx.groupby(['stu_id','outcome'])['_id'].count().reset_index().pivot_table(
                index='stu_id', columns='outcome', values='_id', fill_value=0)

        # Prorporation of each outcome
        stu_stats = pd.concat([stu_stats, d], axis=1)
        stu_stats['Pct Correct'] = stu_stats['Correct'] / stu_stats['Total Tx']
        stu_stats['Pct Hint'] = stu_stats['Hint'] / stu_stats['Total Tx']
        stu_stats['Pct Incorrect'] = stu_stats['Incorrect'] / stu_stats['Total Tx']

        return stu_stats

    def get_stu_prob_stats(self, tx):
        step_stats = tx.groupby(['stu_id', 'unit_id', 'section_id', 'prob_id', 'step_id'])['duration'].agg(['sum', 'count']).reset_index()
        stu_prob_stats = step_stats.groupby('stu_id')['count'].describe()
        stu_prob_stats.columns = ["Step Attempt %s" % col for col in stu_prob_stats.columns]
        d = step_stats.groupby('stu_id')['sum'].describe()
        d.columns = ["Step Duration %s" % col for col in d.columns]
        stu_prob_stats = pd.concat([stu_prob_stats, d], axis=1)

        return stu_prob_stats

    def get_kc_stats(self, tx):
        # Calculates total time, activity, and proportions of outcomes
        # kc_stats = tx[['stu_id', 'kc', 'step_id']].drop_duplicates().groupby(['stu_id', 'kc']).count()
        stu_kc_stats = tx[['stu_id', 'kc', 'step_id']].drop_duplicates().groupby(['stu_id', 'kc']).count().reset_index()
        stu_kc_stats.rename(columns={'step_id': 'kc opportunities'}, inplace=True)
        kc_stats = stu_kc_stats.groupby('kc').describe()
        return kc_stats

    # def get_stu_prob_stats(self, sids):
        # # Calculates total time, activity, and proportions of outcomes
        # tx = pd.DataFrame(self.db.tutor_events.find({"stu_id": {'$in': sids}, 'type': "TutorInput"}))
        # # Add kc field that reduces list of kcs to 1 kc
        # tx['kc'] = tx.apply(lambda x: x['kcs'][0]['_id'], axis=1)

        # step_stats = tx.groupby(['stu_id', 'unit_id', 'section_id', 'prob_id', 'step_id'])['duration'].agg(['sum', 'count']).reset_index()
        # stu_prob_stats = step_stats.groupby('stu_id')['count'].describe()
        # stu_prob_stats.columns = ["Step Attempt %s" % col for col in stu_prob_stats.columns]
        # d = step_stats.groupby('stu_id')['sum'].describe()
        # d.columns = ["Step Duration %s" % col for col in d.columns]
        # stu_prob_stats = pd.concat([stu_prob_stats, d], axis=1)

        # return stu_prob_stats

    # def stu_kc_stats(self, sids):
        # # Calculates total time, activity, and proportions of outcomes
        # tx = pd.DataFrame(self.db.tutor_events.find({"stu_id": {'$in': sids}, 'type': "TutorInput"}))
        # # Add kc field that reduces list of kcs to 1 kc
        # tx['kc'] = tx.apply(lambda x: x['kcs'][0]['_id'], axis=1)

        # # kc_stats = tx[['stu_id', 'kc', 'step_id']].drop_duplicates().groupby(['stu_id', 'kc']).count()
        # stu_kc_stats = tx[['stu_id', 'kc', 'step_id']].drop_duplicates().groupby(['stu_id', 'kc']).count().reset_index()
        # stu_kc_stats.rename(columns={'step_id': 'kc opportunities'}, inplace=True)

        # return stu_kc_stats


    def calc_detected_offtask(self, tx):
        tx_proc = TransactionAnnotator(self.db)
        if "detect_offtask" not in tx.columns:
            tx = pd.concat([tx, tx_proc.lbl_nondil_tx(tx)], axis=1)
        # Student-level off-task vs detected off-task
        d = tx.groupby("stu_id")['detect_offtask'].mean()

        d.rename("mean_detect_offtask", inplace=True)
        return d

    def calc_detected_guess(self, tx):
        tx_proc = TransactionAnnotator(self.db)
        if "detect_guess" not in tx.columns:
            tx = pd.concat([tx, tx_proc.lbl_nondil_tx(tx)], axis=1)
        # Student-level off-task vs detected off-task
        d = tx.groupby("stu_id")['detect_guess'].mean()

        d.rename("mean_detect_guess", inplace=True)
        return d

    def calc_time_on_task(self, tx):
        d = tx.pivot_table(index="stu_id", columns="is_offtask", values="duration", fill_value=0, aggfunc=np.sum).reset_index()
        d.index = d['stu_id']
        d.rename(columns={False: "time_on_task", True: "time_off_task"}, inplace=True)
        d.drop(columns=['stu_id'], inplace=True)
        d['time_on_task'] = d['time_on_task'] / 3600
        d['time_off_task'] = d['time_off_task'] / 3600
        return d

    def count_offtask(self, sids):
        tx = pd.DataFrame(self.db.tutor_events.find({"stu_id": {'$in': sids}, 'type': "TutorInput"}))
        tx.index = tx['_id']
        annotator = TransactionAnnotator(self.db)
        tx['is_offtask'] = annotator.label_off_task_tx(tx)
        return tx.groupby("stu_id")['is_offtask'].count()

    def calc_avg_work_rate(self, steps):
        d = steps.groupby('stu_id')['duration'].agg(['count', 'sum']).rename(columns={'count': 'total_steps', 'sum': 'total_step_time'})
        work_rate = (d['total_step_time'] / d['total_steps']).rename('avg_time_per_step')
        return work_rate

    def count_offtask(sids):
        """
        Count and sum time for ground truth of actual off-task

        """
        tx = pd.DataFrame(self.db.tutor_events.find({"stu_id": {'$in': sids}, 'type': "TutorInput"}))
        tx.index = tx['_id']
        annotator = TransactionAnnotator(self.db)
        tx['is_offtask'] = annotator.label_offtask_tx(tx)
        counts = tx.groupby("stu_id")['is_offtask'].count()
        counts.name = 'is_offtask_count'
        time = tx.groupby(["stu_id", 'is_offtask'])['duration'].sum().reset_index(
                name="total_time").pivot_table(index="stu_id", columns="is_offtask", values="total_time", fill_value=0)
        time.columns = [f"{time.columns.name}_{col}" for col in time.columns]
        return pd.concat([counts, time], axis=1)


