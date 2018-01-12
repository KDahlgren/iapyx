# comno_tests.py

import logging, os, sys
import experiment_workflow

# ------------------------------------------------------ #
# import iapyx packages HERE!!!
if not os.path.abspath( __file__ + "/../../src" ) in sys.path :
  sys.path.append( os.path.abspath( __file__ + "/../../src" ) )

from drivers import iapyx
# ------------------------------------------------------ #


###################
#  COMBO SIMPLOG  #
###################
def combo_simplog() :

  logging.info( "  COMBO SIMPLOG : running test..." )
  logging.info( "  COMBO SIMPLOG : ...done." )

  return None


#################
#  COMBO RDLOG  #
#################
def combo_rdlog() :

  logging.info( "  COMBO RDLOG : running test..." )
  logging.info( "  COMBO RDLOG : ...done." )

  return None


##################
#  COMBO REPLOG  #
##################
def combo_replog() :

  logging.info( "  COMBO REPLOG : running test..." )
  logging.info( "  COMBO REPLOG : ...done." )

  return None



#########
#  EOF  #
#########
