# Script to generate a new domain
# Add project root to python path
import sys
sys.path.append('..')

import logging

from tutor.domain import Domain

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger("main")


if __name__ == "__main__":
    logger.info("Generating a new domain")
    domain = Domain()
    domain_size = 100
    domain.generate_kcs(domain_size)
