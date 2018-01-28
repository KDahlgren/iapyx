# dm_tests.py

import logging, os, sys
import experiment_workflow

# ------------------------------------------------------ #
# import iapyx packages HERE!!!
if not os.path.abspath( __file__ + "/../../src" ) in sys.path :
  sys.path.append( os.path.abspath( __file__ + "/../../src" ) )

from drivers import iapyx
# ------------------------------------------------------ #


###############
#  DM DEMO 1  #
###############
def dm_demo_1( molly_path, table_path, type_path ) :

  logging.info( "  DM DEMO 1 : running test..." )
  experiment_workflow.clean_dirs()

  program_path  = os.getcwd() + "/tmp_data/dm_demo_1.olg"
  metrics_path  = "./metrics_data/metrics.data"
  tmp_path      = "./tmp_data/"

  # define parameters
  driver_path   = "./demo_1.ded"
  crashes       = "0"
  node_list_str = [ "a", "b", "c" ]
  eot           = "2"
  eff           = "1"
  evaluator     = "c4"
  #settings_path = "./settings_files/settings_dm.ini"
  settings_path = "./settings_files/settings_regular.ini"

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
                                           argDict )

  logging.info( "  DM DEMO 1 : ...done." )


#########
#  EOF  #
#########
