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
