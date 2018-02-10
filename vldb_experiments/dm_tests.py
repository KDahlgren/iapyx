# dm_tests.py

import logging, os, sys
import experiment_workflow

# ------------------------------------------------------ #
# import iapyx packages HERE!!!
if not os.path.abspath( __file__ + "/../../src" ) in sys.path :
  sys.path.append( os.path.abspath( __file__ + "/../../src" ) )

from drivers import iapyx
# ------------------------------------------------------ #


################
#  DM SIMPLOG  #
################
def dm_simplog( PRINT_STOP, molly_path, table_path, type_path ) :

  logging.info( "  DM SIMPLOG : running test..." )
  experiment_workflow.clean_dirs()

  program_path  = os.getcwd() + "/tmp_data/iapyx_program.olg"
  metrics_path  = "./metrics_data/metrics.data"
  tmp_path      = "./tmp_data/"

  # define parameters
  driver_path   = "./dedalus_drivers/simplog_driver.ded"
  crashes       = "0"
  node_list_str = [ "a", "b", "c" ]
  eot           = "4"
  eff           = "2"
  evaluator     = "c4"
  settings_path = "./settings_files/settings_dm.ini"

  argDict = {  "file"      : driver_path, \
               "crashes"   : crashes, \
               "nodes"     : node_list_str, \
               "EOT"       : eot, \
               "EFF"       : eff, \
               "evaluator" : evaluator, \
               "settings"  : settings_path }

  experiment_workflow.experiment_workflow( molly_path, \
                                           program_path, \
                                           table_path, \
                                           type_path, \
                                           metrics_path, \
                                           tmp_path, \
                                           driver_path, \
                                           crashes, \
                                           node_list_str, \
                                           eot, \
                                           eff, \
                                           evaluator, \
                                           settings_path, \
                                           argDict, \
                                           PRINT_STOP )

  logging.info( "  DM SIMPLOG : ...done." )


##############
#  DM RDLOG  #
##############
def dm_rdlog() :

  logging.info( "  DM RDLOG : running test..." )
  logging.info( "  DM RDLOG : ...done." )

  return None


###############
#  DM REPLOG  #
###############
def dm_replog() :

  logging.info( "  DM REPLOG : running test..." )
  logging.info( "  DM REPLOG : ...done." )

  return None


#########
#  EOF  #
#########
