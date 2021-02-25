

import logging

import datetime as dt
import pandas as pd

from .featurization import TransactionAnnotator

logger = logging.getLogger(__name__)


class TransactionCalculator:

    def __init__(self, db):
        self.db = db


    def get_decisions(self, tx):
        lblr = TransactionAnnotator(self.db)

