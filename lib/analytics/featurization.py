# Class to support featurizing transactions for analysis
# Author: Steven Dang stevencdang.com

import logging

from typing import Final

import datetime as dt
import pandas as pd
import copy

from CanonicalAutocorrelationAnalysis.model.caa import *
from CanonicalAutocorrelationAnalysis.model.caaObject import *
from CanonicalAutocorrelationAnalysis.model.utils import l1Norm, l2Norm, r2Compute

logger = logging.getLogger(__name__)
# logger.setLevel(logging.DEBUG)


class CAEPreprocessor:


    def __init__(self, tx):
        self.set_data(tx)
        self.type = type(self).__name__
        

    def convert_to_one_hot(self, cols):
        for col in cols:
            logger.debug(f"One-hot encoding column: {col}")
            vals = self.tx[col].unique()
            new_cols = pd.get_dummies(self.tx[col], drop_first=True)
            orig_shape = self.tx.shape
            self.tx = pd.concat([self.tx, new_cols], axis=1)
            concat_shape = self.tx.shape
            self.tx.drop(columns=[col], inplace=True)
            drop_shape = self.tx.shape
            logger.debug(f"Added {len(vals)} columns to Orig shape: {orig_shape}\t \
                                Concated shape: {concat_shape}\t dropped col shape: {drop_shape}")

    def process_data(self):
        pass

    def set_data(self, d):
        dtype = type(d)
        logger.debug(f"Type of data to set: {dtype}")
        if dtype != pd.DataFrame:
            raise TypeError("Must set data of type dataframe, not {dtype}")
        else:
            self.tx = d

    @classmethod
    def config_from_dict(cls, d):
        obj = cls(pd.DataFrame())
        # WARNING: this does not set the originl raw data. 
        return obj

    def to_dict(self):
        obj = copy.deepcopy(self.__dict__)
        # Don't persists the raw data only configuration 
        obj.pop('tx')
        return obj



class SimpleCAEPreprocessor(CAEPreprocessor):

    BASE_CAE_COLS: Final = ["duration", 
                            "outcome", 
                            "plt", 
                            "plt1", 
                            "hints_used", 
                            "hints_avail", 
                            "attempt"
                           ]
    
    ONE_HOT_COLS: Final = ['outcome'
                          ]

    
    def process_data(self):
        # drop all but necessary data columns
        logger.debug(f"Processing transactions for calculating CAE. Original data shape: {self.tx.shape}")
        self.tx = self.tx.loc[:, self.BASE_CAE_COLS]

        # One-hot encode categorical columns 
        self.convert_to_one_hot(self.ONE_HOT_COLS)

        logger.debug(f"Final data shape: {self.tx.shape}")

        return self.tx


    @classmethod
    def config_from_dict(cls, d):
        obj = super(SimpleCAEPreprocessor, cls).config_from_dict(d)
        # WARNING: this does not set the originl raw data. 
        return obj


class Detector:

    def __init__(self, db):
        self.db = db


    def get_kc_long_cutoff(self, tx, thres=0.9):
            if 'kc' not in tx.columns:
                tx['kc'] = tx.explode('kcs')['kcs'].apply(lambda x: x['_id'])
            kc_stats = tx.groupby('kc')['duration'].apply(lambda x: np.quantile(x, thres)).to_dict()
            return kc_stats

    def get_kc_short_cutoff(self, tx, thres=0.05):
            if 'kc' not in tx.columns:
                tx['kc'] = tx.explode('kcs')['kcs'].apply(lambda x: x['_id'])
            kc_stats = tx.groupby('kc')['duration'].apply(lambda x: np.quantile(x, thres)).to_dict()
            return kc_stats


    def is_off_task(self, tx, thres=30, kc_stats=None):
        """
        Detect off-task transactions as long transactions

        """

        if kc_stats is None:
            d = tx.apply(lambda x: x['duration'] > thres, axis=1)
            return d
        else:

            if 'kc' not in tx.columns:
                tx['kc'] = tx.explode('kcs')['kcs'].apply(lambda x: x['_id'])

            d = tx.apply(lambda x: x['duration'] > (kc_stats[x['kc']]), axis=1)
            return d

    def is_guess(self, tx, thres=2, kc_stats=None):
        if kc_stats is None:
            d = tx.apply(lambda x: x['duration'] <= thres, axis=1)
            return d
        else:
            if 'kc' not in tx.columns:
                tx['kc'] = tx.explode('kcs')['kcs'].apply(lambda x: x['_id'])
            d = tx.apply(lambda x: (x['outcome'] == 'Incorrect') & (x['duration'] <= (kc_stats[x['kc']])), axis=1)

            return d


class TransactionAnnotator:

    def __init__(self, db):
        self.db = db

    def get_tx_actions(self, tx):
        d = tx.explode('action_ids').rename(columns={'action_ids': 'action_id'})
        actions = pd.DataFrame(self.db.actions.find({"_id": {"$in": d['action_id'].tolist()}}))
        actions['action_type'] = actions.apply(lambda x: x['action']['type'], axis=1)
        actions.rename(columns={"_id": "action_id"}, inplace=True)
        d = pd.merge(d[['_id', 'action_id']], actions, on='action_id', how='outer')
        return d

    def get_tx_decisions(self, tx, get_actions=True):
        actions = self.get_tx_actions(tx)
        decisions = pd.DataFrame(self.db.decisions.find({"_id": {"$in": actions['decision_id'].tolist()}}))
        decisions.rename(columns={"_id": "decision_id"}, inplace=True)
        if get_actions:
            return decisions, actions
        else:
            return decisions

    def merge_decisions(self, tx, actions, decisions):

        # Need to remove "_id" from index because some transactions will be duplicated
        tx.index = range(tx.shape[0])
        actions.drop(columns=['time'], inplace=True)
        d = pd.merge(tx, actions, how='outer', on='_id')
        drop_cols = ['hints_avail', 'hints_used', 'attempt', 'student_id', 'kc']
        decisions.drop(columns=drop_cols, inplace=True)
        decisions.rename(columns={"time": "action_time"}, inplace=True)
        d = pd.merge(d, decisions, how='outer', on='decision_id')
        return d

 
    def label_offtask_tx(self, tx):
        d = self.get_tx_actions(tx)
        return d.groupby("_id")['action_type'].apply(lambda x: "OffTask" in x.tolist())


    def label_guess_tx(self, tx):
        d = self.get_tx_actions(tx)
        return d.groupby("_id")['action_type'].apply(lambda x: "Guess" in x.tolist())

    def label_nondil_tx(self, tx):
        detector = Detector(self.db) 
	
        kc_long_tx = detector.get_kc_long_cutoff(tx)
        kc_short_tx = detector.get_kc_short_cutoff(tx)

        # Add Ground truth labels (using global db var)

        is_offtask = self.label_offtask_tx(tx).rename('is_offtask')
        is_guess = self.label_guess_tx(tx).rename('is_guess')
        result = pd.concat([is_offtask, is_guess], axis=1)

        # Add detector labels
        result['detect_offtask'] = detector.is_off_task(tx, kc_stats=kc_long_tx)
        result['detect_guess'] = detector.is_guess(tx, kc_stats=kc_short_tx)
        return result





