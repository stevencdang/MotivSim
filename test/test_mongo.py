# Script to test a tutor
# Add project root to python path
import sys
sys.path.append('..')

from log_db.mongo import *

data_path = "../test/data"
db_name = "motivsim"
db_params  = get_db_params(db_name)
logger.info("got db params: %s" % str(db_params))
util = Data_Utility(data_path, db_params)
util.peak()
# util.sample_doc(3)
# util.clear_db()
