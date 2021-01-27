# Class to support management of CAE-based modeling
# Author: Steven Dang stevencdang.com

import uuid
import copy
import logging


from typing import Final

import pandas as pd

# from CanonicalAutocorrelationAnalysis.model.caa import *
from CanonicalAutocorrelationAnalysis.model import caaObject
# from CanonicalAutocorrelationAnalysis.model.utils import l1Norm, l2Norm, r2Compute

from analytics.featurization import *

logger = logging.getLogger(__name__)
# logger.setLevel(logging.DEBUG)


class CAABatch:

    def __init__(self, desc, col_names):
        self._id = str(uuid.uuid4())
        self.mdls = []
        self.desc = desc
        self.col_names = col_names
        self.projections = {}

    def add(self, mdl):
        mid = mdl._id
        if mid in [mdl._id for mdl in self.mdls]:
            logger.warning("Model is already in CAA Batch. Not adding in")
        else:
            self.mdls.append(mdl)
            for proj in mdl.projections:
                self.projections[proj._id] = proj

    def to_dict(self):
        obj = copy.deepcopy(self.__dict__)
        obj['mdls'] = [mdl._id for mdl in self.mdls]
        obj['projections'] = list(self.projections.keys())
        return obj

    def get_index(self):
        return list(self.projections.keys())

    def get_distances(self, batch=None):

        if batch is None:
            m = pd.DataFrame(index=self.get_index(), columns=self.get_index())
            for i in self.get_index():
                for j in self.get_index():
                    p1 = self.projections[i]
                    p2 = self.projections[j]
                    d = CAAProjection.distance(p1, p2)
                    m.loc[i,j] = d
        else:
            rows = batch.get_index()
            cols = self.get_index()
            m = pd.DataFrame(index=rows, columns=cols)
            for i in rows:
                for j in cols:
                    p1 = batch.projections[i]
                    p2 = self.projections[j]
                    d = CAAProjection.distance(p1, p2)
                    m.loc[i,j] = d

        return m





class CAAModel(caaObject.CAA):

    def __init__(self, US, VS, DS, error, penalty1, penalty2, trainingData, data_proc, data_idx):
        super().__init__(US, VS, DS, error, penalty1, penalty2, trainingData)
        self._id = str(uuid.uuid4())
        self.data_proc = data_proc
        self.data_idx = data_idx
        self.projections = [CAAProjection.from_proj(proj, self._id) for proj in self.projections]


    @classmethod
    def from_caa_obj(cls, caa, data_proc, data_idx, *argv):
        result = cls(caa.US, caa.VS, caa.ds, caa.rs, caa.penalty1, caa.penalty2, caa.trainingData, data_proc, data_idx, *argv)
        return result

    @classmethod 
    def from_dict(cls, d, db_col):
        raw_data = pd.DataFrame(db_col.find({'_id': {'$in': d['data_idx']}}))
        data_proc_cls = getattr(sys.modules[__name__], d['data_proc']['type'])
        data_proc = data_proc_cls.config_from_dict(d['data_proc'])
        data_proc.set_data(raw_data)
        trainingData = data_proc.process_data()
        
        obj = cls(d['US'],
                  d['VS'],
                  d['DS'],
                  d['error'],
                  d['penalty1'],
                  d['penalty2'],
                  trainingData,
                  data_proc,
                  d['data_idx']
                 )
        obj._id = d['_id']
        return obj

    @staticmethod 
    def get_training_data_with_dict(d, db_col):
        raw_data = pd.DataFrame(db_col.find({'_id': {'$in': d['data_idx']}}))
        data_proc_cls = getattr(sys.modules[__name__], d['data_proc']['type'])
        data_proc = data_proc_cls.config_from_dict(d['data_proc'])
        data_proc.set_data(raw_data)

        d = data_proc.process_data()
        return d


    def to_dict(self):
        obj = copy.deepcopy(self.__dict__)
        obj.pop('trainingData')
        obj['data_proc'] = self.data_proc.to_dict()
        obj['projections'] = [proj.to_dict() for proj in obj['projections']]
        obj['US'] = [u.tolist() for u in self.US]
        obj['VS'] = [v.tolist() for v in self.VS]
        obj['ds'] = [d.tolist() for d in self.ds]
        obj['rs'] = [err.tolist() for err in self.rs]
        obj['mean'] = self.mean.tolist()
        obj['std'] = self.std.tolist()
        obj['data_idx'] = self.data_idx.tolist()

        return obj 


class CAAProjection(caaObject.Projection):

    def __init__(self, u, v, e, d, caa, mid):
        super().__init__(u, v, e, d, caa)
        self._id = str(uuid.uuid4())
        self.caa_model_id = mid

    @classmethod
    def from_proj(cls, d, mid):
        obj = cls(d.u, d.v, d.e, d.d, d.caaFather, mid)
        return obj

    def to_dict(self):
        obj = {'u': self.u.tolist(),
               'v': self.v.tolist(),
               'd': self.d.tolist(),
               'e': self.e.tolist(),
               'caa_model_id': self.caa_model_id
              }
        return obj


class StudentCAAModel(CAAModel):

    def __init__(self, US, VS, DS, error, penalty1, penalty2, trainingData, data_proc, data_idx, sid):
        super().__init__(US, VS, DS, error, penalty1, penalty2, trainingData, data_proc, data_idx)
        self.student_id = sid
