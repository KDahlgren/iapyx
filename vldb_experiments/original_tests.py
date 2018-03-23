# original_tests.py

import logging, os, sys
import experiment_workflow

# ------------------------------------------------------ #
# import iapyx packages HERE!!!
if not os.path.abspath( __file__ + "/../../src" ) in sys.path :
  sys.path.append( os.path.abspath( __file__ + "/../../src" ) )

from drivers import iapyx
# ------------------------------------------------------ #


######################
#  ORIGINAL SIMPLOG  #
######################
def original_simplog( PRINT_STOP, molly_path, table_path, type_path ) :

  logging.info( "  ORIGINAL SIMPLOG : running test..." )
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
  settings_path = "./settings_files/settings_regular.ini"

  argDict = {  "file"            : driver_path, \
               "crashes"         : crashes, \
               "nodes"           : node_list_str, \
               "EOT"             : eot, \
               "EFF"             : eff, \
               "evaluator"       : evaluator, \
               "settings"        : settings_path, \
               "data_save_path"  : tmp_path }

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

  logging.info( "  ORIGINAL SIMPLOG : ...done." )


####################
#  ORIGINAL RDLOG  #
####################
def original_rdlog( molly_path, table_path, type_path ) :

  logging.info( "  ORIGINAL RDLOG : running test..." )
  experiment_workflow.clean_dirs()

  program_path  = os.getcwd() + "/tmp_data/iapyx_program.olg"
  if os.path.exists( program_path ) :
    os.remove( program_path )

  metrics_path  = "./metrics_data/metrics.data"
  if os.path.exists( metrics_path ) :
    os.remove( metrics_path )

  tmp_path      = "./tmp_data/"
  if os.path.exists( tmp_path ) :
    os.system( "rm -rf " + tmp_path )
    os.system( "mkdir " + tmp_path )

  # define parameters
  driver_path   = "./dedalus_drivers/rdlog_driver.ded"
  crashes       = "1"
  node_list_str = [ "a", "b", "c" ]
  eot           = "4"
  eff           = "2"
  evaluator     = "c4"
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

  logging.info( "  ORIGINAL RDLOG : ...done." )


#####################
#  ORIGINAL REPLOG  #
#####################
def original_replog( molly_path, table_path, type_path ) :

  logging.info( "  ORIGINAL REPLOG : running test..." )
  experiment_workflow.clean_dirs()

  program_path  = os.getcwd() + "/tmp_data/iapyx_program.olg"
  metrics_path  = "./metrics_data/metrics.data"
  tmp_path      = "./tmp_data/"

  # define parameters
  driver_path   = "./dedalus_drivers/replog_driver.ded"
  crashes       = "0"
  node_list_str = [ "a", "b", "c" ]
  eot           = "4"
  eff           = "2"
  evaluator     = "c4"
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

  logging.info( "  ORIGINAL REPLOG : ...done." )


#########
#  EOF  #
#########
