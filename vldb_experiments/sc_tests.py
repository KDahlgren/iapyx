# sc_tests.py

import logging, os, sys
import experiment_workflow

# ------------------------------------------------------ #
# import iapyx packages HERE!!!
if not os.path.abspath( __file__ + "/../../src" ) in sys.path :
  sys.path.append( os.path.abspath( __file__ + "/../../src" ) )

from drivers import iapyx
# ------------------------------------------------------ #


################
#  SC SIMPLOG  #
################
def sc_simplog() :

  logging.info( "  SC SIMPLOG : running test..." )
  logging.info( "  SC SIMPLOG : ...done." )

  return None


##############
#  SC RDLOG  #
##############
def sc_rdlog() :

  logging.info( "  SC RDLOG : running test..." )
  logging.info( "  SC RDLOG : ...done." )

  return None


###############
#  SC REPLOG  #
###############
def sc_replog() :

  logging.info( "  SC REPLOG : running test..." )
  logging.info( "  SC REPLOG : ...done." )

  return None


#########
#  EOF  #
#########
