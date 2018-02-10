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
  Need a way to collect fault conclusions from Molly.
  Collect metrics on iapyx runs using the appmetrics python package: 'pip install appmetrics'?
  How to collect metric from molly?
'''

#########################
#  EXPERIMENT WORKFLOW  #
#########################
# input experiment parameters and 
# run the test.
def experiment_workflow( molly_path, \
                         program_path, \
                         table_path, \
                         type_path, \
                         metrics_path, \
                         tmp_path, \
                         driver_path, \
                         crashes, \
                         node_list, \
                         eot, \
                         eff, \
                         evaluator, \
                         settings_path, \
                         argDict, \
                         PRINT_STOP ) :

  # ----------------------------------- #
  # generate the iapyx program

  allProgramData = iapyx.iapyx_driver( argDict )

  # collect program data
  program_array = allProgramData[0]
  table_array   = allProgramData[1]

  if PRINT_STOP :
    logging.debug( "  EXPERIMENT WORKFLOW : program_array :" )
    for line in program_array :
      logging.debug( "    " + line )
    logging.debug( "  EXPERIMENT WORKFLOW : table_array :" )
    for table in table_array :
      logging.debug( "    " + table )


  # ----------------------------------- #
  # collect type lists per relation

  type_map = {}
  for line in program_array :
    if line.startswith( "define(" ) :
      line = line.replace( "define(", "" )
      line = line.replace( ")", "" )
      line = line.replace( ";", "" )
      line = line.replace( "{", "" )
      line = line.replace( "}", "" )
      line = line.split( "," )
      type_map[ line[0] ] = ",".join( line[1:] ) + ";"

  # ----------------------------------- #
  # save program and table data to files

  # saving program lines...
  f = open( program_path,'w' )
  for line in program_array :

    # comment out all defines, crashes, and clocks
    if line.startswith( "define(" ) or \
       line.startswith( "crash(" )  or \
       line.startswith( "clock(" )  or \
       line.startswith( "next_clock(" )  :
      f.write( "//" + line + "\n" )
    else :
      f.write( line + "\n" )

  f.close()

  # saving table list...
  f = open( table_path,'w' )
  for table in table_array :
    f.write( table + "," )
  f.close()

  # saving type lists...
  f = open( type_path,'w' )
  for tp in type_map :
    f.write( tp + "," + str( type_map[ tp ] ) )
  f.close()

  if PRINT_STOP :

    logging.debug( "  EXPERIMENT WORKFLOW : program_path '" + program_path + "'" )
    fo = open( program_path, "r" )
    for line in fo :
      logging.debug( "    " + line.strip( "\n" ) )
    fo.close()

    logging.debug( "  EXPERIMENT WORKFLOW : table_path '" + table_path + "'" )
    fo = open( table_path, "r" )
    for line in fo :
      logging.debug( "    " + line.strip( "\n" ) )
    fo.close()

    logging.debug( "  EXPERIMENT WORKFLOW : type_path '" + type_path + "'" )
    fo = open( type_path, "r" )
    for line in fo :
      logging.debug( "    " + line.strip( "\n" ) )
    fo.close()

    sys.exit()

  # ---------------------------------------------------- #
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
	--EOT ' + str( eot ) + ' \
	--EFF ' + str( eff ) + '  \
	--nodes ' + ",".join( node_list ) + ' \
	--crashes ' + str( crashes ) + ' \
	--ignore-prov-nodes domcomp_,dom_ \
	--prov-diagrams"' )

  # ----------------------------------- #
  # save metrics to file
  #


################
#  CLEAN DIRS  #
################
# remove leftover data from previous tests
def clean_dirs() :

  # ---------------------- #
  # create a clean tmp_data/

  if os.path.exists( "./tmp_data/" ) :
    logging.debug( "rm -rf ./tmp_data/" )
    os.system( "rm -rf ./tmp_data/" )

  logging.debug( "mkdir ./tmp_data/" )
  os.system( "mkdir ./tmp_data/" )

  # ---------------------- #
  # remove rogue IR files

  if os.path.exists( "./IR*" ) :
    logging.debug( "rm -rf ./IR.db" )
    os.system( "rm -rf ./IR.db" )



#########
#  EOF  #
#########
