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
        self._id = uuid.uuid4()
        self.domain_id = did
        self.pl0 = pl0
        self.pt = pt
        self.ps = ps
        self.pg = pg
        self.m_time = m_time
        self.sd_time = sd_time


class Domain:

    def __init__(self):
        self._id = uuid.uuid4()
        self.kcs = []

    def generate_kcs(self, n, 
                     m_l0=0.3, 
                     sd_l0=0.1,
                     m_t=0.07,
                     sd_t=0.03,
                     m_s=0.35,
                     sd_s=0.03,
                     m_g=0.2,
                     sd_g=0.03,
                     m_mt=15,
                     sd_mt=5,
                     ):
        # Generate n kcs
        logger.debug("generate kcs for domain: %s" % self._id)
        for i in range(n):
            logger.debug("Generating kc #%i" % i)
            pl0 = random.gauss(m_l0, sd_l0)
            pt = random.gauss(m_t, sd_t)
            ps = random.gauss(m_s, sd_s)
            pg = random.gauss(m_g, sd_g)
            m_time = random.gauss(15, 5)
            sd_time = m_time/4
            kc = KC(self._id, pl0, pt, ps, pg, m_time, sd_time)
            logger.debug("KC: pl0: %f\tpt: %f\tpg: %f\tps: %f\tmtime: %f\t sdtime: %f" % (kc.pl0, kc.pt, kc.ps, kc.pg, kc.m_time, kc.sd_time))
            self.kcs.append(kc)

        logger.debug("generated %i kcs" % len(self.kcs))
