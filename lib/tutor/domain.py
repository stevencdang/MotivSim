# Class definitions to support defining a domain model
import logging
import uuid
import random

logger = logging.getLogger(__name__)

class KC:

    def __init__(self, 
                 did, 
                 pl0=None, 
                 pt=None, 
                 ps=None, 
                 pg=None, 
                 m_time=None, 
                 sd_time=None):
        self._id = str(uuid.uuid4())
        self.domain_id = did
        self.pl0 = pl0
        self.pt = pt
        self.ps = ps
        self.pg = pg
        self.m_time = m_time
        self.sd_time = sd_time

    def __str__(self):
        return str(self.__dict__)


class Domain:

    def __init__(self):
        self._id = str(uuid.uuid4())
        self.kcs = []
        self.kc_hyperparams = {
                     'm_l0':None,
                     'sd_l0':None,
                     'm_t':None,
                     'sd_t':None,
                     'm_s':None,
                     'sd_s':None,
                     'm_g':None,
                     'sd_g':None,
                     'm_mt':None,
                     'sd_mt':None
        }
        self.set_default_hyperparams()

    def set_default_hyperparams(self):
        params = { 
                 'm_l0':0.5, 
                 'sd_l0':0.1,
                 'm_t':0.2,
                 'sd_t':0.03,
                 'm_s':0.05,
                 'sd_s':0.03,
                 'm_g':0.8,
                 'sd_g':0.15,
                 'm_mt':10,
                 'sd_mt':5
        }
        self.set_kc_hyperparams(**params)

    def set_kc_hyperparams(self, **kwargs):
        for arg,val in kwargs.items():
            logger.debug("Setting new value for kc hyperparameter: %s to %s" % (arg, val))
            self.kc_hyperparams[arg] = val
        

    def generate_kcs(self, n, mastery_thres=0.9):
        # Generate n kcs
        logger.debug("generate kcs for domain: %s" % self._id)
        kcs = []
        for i in range(n):
            logger.debug("Generating kc #%i" % i)
            pl0 = random.gauss(self.kc_hyperparams['m_l0'], 
                               self.kc_hyperparams['sd_l0'])
            if pl0 <= 0:
                pl0 = 0.01
            elif pl0 >= mastery_thres:
                pl0 = mastery_thres - 0.01

            pt = random.gauss(self.kc_hyperparams['m_t'], 
                              self.kc_hyperparams['sd_t'])
            if pt <= 0:
                pt = 0.01
            ps = random.gauss(self.kc_hyperparams['m_s'], 
                              self.kc_hyperparams['sd_s'])
            if ps <= 0:
                ps = 0.01
            pg = random.gauss(self.kc_hyperparams['m_g'], 
                              self.kc_hyperparams['sd_g'])
            if pg  <= 0:
                pg = 0.01
            elif pg >= 1:
                pg = 0.99
            m_time = random.gauss(self.kc_hyperparams['m_mt'],
                                  self.kc_hyperparams['sd_mt'])
            sd_time = m_time/4
            kc = KC(self._id, pl0, pt, ps, pg, m_time, sd_time)
            logger.debug("KC: pl0: %f\tpt: %f\tpg: %f\tps: %f\tmtime: %f\t sdtime: %f" % (kc.pl0, kc.pt, kc.ps, kc.pg, kc.m_time, kc.sd_time))
            kcs.append(kc)
            self.kcs.append(kc)

        logger.debug("generated %i kcs" % len(kcs))
        return kcs



    def to_dict(self):
        return {'_id': self._id,
                'kcs': [kc._id for kc in self.kcs]
                }


