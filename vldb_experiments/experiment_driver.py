# experiment_driver.py

import logging, os, sys

# ------------------------------------------------------ #
# import iapyx packages HERE!!!
if not os.path.abspath( __file__ + "/../../src" ) in sys.path :
  sys.path.append( os.path.abspath( __file__ + "/../../src" ) )

from drivers import iapyx
# ------------------------------------------------------ #

'''
TODO:
  Debug molly type derivation.
  Need a way to collect fault conclusions from Molly.
  Collect metrics on iapyx runs using the appmetrics python package: 'pip install appmetrics'
'''

#######################
#  EXPERIMENT DRIVER  #
#######################
def experiment_driver( molly_path ) :

  logging.basicConfig( format='%(levelname)s:%(message)s', level=logging.DEBUG )

  # ----------------------- #
  #        DML TESTS        #
  # ----------------------- #

  dml_path      = "../src/drivers/iapyx.py"
  program_path  = os.getcwd() + "/tmp_data/program_dml.olg"
  table_path    = os.getcwd() + "/tmp_data/iapyx_tables.data" # filename hard-coded in molly
  type_path     = os.getcwd() + "/tmp_data/iapyx_types.data"  # filename hard-coded in molly
  metrics_path  = "./metrics_data/metrics.data"
  tmp_path      = "./tmp_data/"

  # ----------------------------------- #
  # simplog

  # define parameters
  driver_path   = "./dedalus_drivers/simplog_driver.ded"
  crashes       = "0"
  node_list_str = [ "a", "b", "c" ]
  eot           = "4"
  eff           = "2"
  evaluator     = "c4"
  #settings_path = "./settings_files/settings_regular.ini"
  settings_path = "./settings_files/settings_dml.ini"

  argDict = {  "file"      : driver_path, \
               "crashes"   : crashes, \
               "nodes"     : node_list_str, \
               "EOT"       : eot, \
               "EFF"       : eff, \
               "evaluator" : evaluator, \
               "settings"  : settings_path }

#  # run experiment
#  allProgramData = iapyx.iapyx_driver( argDict )
#
#  # collect program data
#  program_array = allProgramData[0]
#  table_array   = allProgramData[1]
#
#  # collect type lists per relation
#  type_map = {}
#  for line in program_array :
#    if line.startswith( "define(" ) :
#      line = line.replace( "define(", "" )
#      line = line.replace( ")", "" )
#      line = line.replace( ";", "" )
#      line = line.replace( "{", "" )
#      line = line.replace( "}", "" )
#      line = line.split( "," )
#      type_map[ line[0] ] = ",".join( line[1:] ) + ";"
#
#  # save program and table data to files
#  # saving program lines...
#  f = open( program_path,'w' )
#  for line in program_array :
#
#    # comment out all defines, crashes, and clocks
#    if line.startswith( "define(" ) or \
#       line.startswith( "crash(" ) or \
#       line.startswith( "clock(" )  :
#      f.write( "//" + line + "\n" )
#    else :
#      f.write( line + "\n" )
#
#  f.close()
#
#  # saving table list...
#  f = open( table_path,'w' )
#  for table in table_array :
#    f.write( table + "," )
#  f.close()
#
#  # saving type lists...
#  f = open( type_path,'w' )
#  for tp in type_map :
#    f.write( tp + "," + str( type_map[ tp ] ) )
#  f.close()

  # run the hacked molly branch on the program files
  # step 1. copy over tables for this experiment 
  #         (necc. b/c saving eval results per 
  #         LDFI iteration).
  # step 2. cd into the specified molly clone.
  # step 3. run molly on the generated and 
  #         pre-processed iapyx file.
  os.system( '\
    cp ' + table_path + ' ' + molly_path + ' ; \
    cp ' + type_path  + ' ' + molly_path + ' ; \
    cd ' + molly_path + ' ; \
    sbt "run-main edu.berkeley.cs.boom.molly.SyncFTChecker \
	' + program_path + ' \
	--EOT 4 \
	--EFF 2 \
	--nodes a,b,c \
	--crashes 0 \
	--prov-diagrams"' )

  # save metrics to file
  #

  # ----------------------------------- #
  # rdlog

  # ----------------------------------- #
  # replog


  # ------------------------- #
  #        COMBO TESTS        #
  # ------------------------- #

  # ----------------------------------- #
  # simplog

  # ----------------------------------- #
  # rdlog

  # ----------------------------------- #
  # replog




#########################
#  THREAD OF EXECUTION  #
#########################
if __name__ == '__main__' :

  # pass path to molly at command line
  # ( replace this after making the hacked molly branch a dependency )
  molly_path = sys.argv[1]
  
  experiment_driver( molly_path )


#########
#  EOF  #
#########
