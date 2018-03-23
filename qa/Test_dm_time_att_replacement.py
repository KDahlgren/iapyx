#!/usr/bin/env python

'''
Test_dm_time_att_replacement.py
'''

#############
#  IMPORTS  #
#############
# standard python packages
import ConfigParser
import inspect, logging, json, os, re, string, sqlite3, sys, unittest

# ------------------------------------------------------ #
# import sibling packages HERE!!!
if not os.path.abspath( __file__ + "/../../src" ) in sys.path :
  sys.path.append( os.path.abspath( __file__ + "/../../src" ) )

from dedt    import dedt, dedalusParser, clockRelation, dedalusRewriter
from utils   import dumpers, globalCounters, tools
from drivers import iapyx

# ------------------------------------------------------ #


eqnOps = [ "==", "!=", ">=", "<=", ">", "<" ]


##################################
#  TEST DM TIME ATT REPLACEMENT  #
##################################
class Test_dm_time_att_replacement( unittest.TestCase ) :

  #logging.basicConfig( format='%(levelname)s:%(message)s', level=logging.DEBUG )
  logging.basicConfig( format='%(levelname)s:%(message)s', level=logging.INFO )
  #logging.basicConfig( format='%(levelname)s:%(message)s', level=logging.WARNING )

  PRINT_STOP              = False
  RUN_IAPYX               = True
  RUN_EXPERIMENT_WORKFLOW = True
  SKIP_ASSERTS            = False

  MOLLY_PATH = os.getcwd() + "/../lib/molly/"
  TABLE_PATH = os.getcwd() + "/tmp_data/iapyx_tables.data" # filename hard-coded in molly
  TYPE_PATH  = os.getcwd() + "/tmp_data/iapyx_types.data"  # filename hard-coded in molly


  #############################
  #  DM TIME ATT REPLACEMENT  #
  #############################
  #@unittest.skip( "abandoned." )
  def test_dm_time_att_replacement( self ) :

    test_id = "dm_time_att_replacement"
    logging.debug( "  TEST MOLLY LDFI : running test_" + test_id )

    program_path  = os.getcwd() + "/tmp_data/iapyx_program.olg"
    metrics_path  = "./metrics_data/metrics.data"
    tmp_path      = "./tmp_data/"

    # define parameters
    driver_path   = "./testFiles/" + test_id + ".ded"
    crashes       = "0"
    node_list     = [ "astring", "astring1", "astring2", "astring3", "astring4", "astring5" ]
    eot           = "2"
    eff           = "0"
    evaluator     = "c4"
    settings_path = "./settings_files/settings_setTypes_dm.ini"

    argDict = {  "file"           : driver_path, \
                 "crashes"        : crashes, \
                 "nodes"          : node_list, \
                 "EOT"            : eot, \
                 "EFF"            : eff, \
                 "evaluator"      : evaluator, \
                 "settings"       : settings_path, \
                 "data_save_path" : './data/' }

    if self.RUN_IAPYX :
      actual_program_array, actual_table_array, actual_cursor, actual_factMeta, actual_ruleMeta = self.run_iapyx( argDict )

      if self.PRINT_STOP :
#       for rule in actual_ruleMeta :
#          print rule.ruleData[ "relationName" ] + ", " + \
#                str( rule.ruleData[ "goalAttList" ] ) + ", " + \
#                rule.rule_type
        for line in actual_program_array :
          print line
        sys.exit( "exiting on PRINT_STOP..." )

    if self.RUN_EXPERIMENT_WORKFLOW :
      self.experiment_workflow( program_path, \
                                metrics_path, \
                                tmp_path, \
                                driver_path, \
                                argDict )

    if not self.SKIP_ASSERTS :

      # insert asserts here:
      actual_json_results_path   = self.MOLLY_PATH + "output/runs.json"
      expected_json_results_path = os.getcwd() + "/testFiles/runs_" + test_id + ".json"

      actual_num_iterations, actual_conclusion     = self.get_molly_results( actual_json_results_path )
      expected_num_iterations, expected_conclusion = self.get_molly_results( expected_json_results_path )

      self.assertEqual( actual_num_iterations, expected_num_iterations )
      self.assertEqual( actual_conclusion, expected_conclusion )

    logging.debug( "  TEST MOLLY LDFI : " + test_id + " ...done." )


  #######################
  #  GET MOLLY RESULTS  #
  #######################
  # parse iteration dictionaries from input json files.
  # need to change this if molly ever changes the json output format.
  def get_molly_results( self, json_results_path ) :

    json_file = open( json_results_path )
    json_str  = json_file.read()
    json_file.close()
    json_data = json.loads( json_str )

    last_failureSpec = json_data[ -1 ][ "failureSpec" ]
    last_omissions   = last_failureSpec[ "omissions" ]

    return len( json_data ), last_omissions


  ###############
  #  RUN IAPYX  #
  ###############
  # run the iapyx translation on the given 
  # program using the given parameters
  def run_iapyx( self, argDict ) :
    self.clean_tmp()
    self.clean_dirs( argDict )
    return iapyx.iapyx_driver( argDict )


  #########################
  #  EXPERIMENT WORKFLOW  #
  #########################
  # input experiment parameters and 
  # run the test.
  def experiment_workflow( self, \
                           program_path, \
                           metrics_path, \
                           tmp_path, \
                           driver_path, \
                           argDict ) :
 
    self.clean_tmp()
    self.clean_dirs( argDict )
 
    # ----------------------------------- #
    # generate the iapyx program
  
    program_array, table_array, cursor, factMeta, ruleMeta = iapyx.iapyx_driver( argDict )
  
    if self.PRINT_STOP :
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
    f = open( self.TABLE_PATH,'w' )
    for table in table_array :
      f.write( table + "," )
    f.close()
  
    # saving type lists...
    f = open( self.TYPE_PATH,'w' )
    for tp in type_map :
      f.write( tp + "," + str( type_map[ tp ] ) )
    f.close()
  
    if self.PRINT_STOP :
  
      logging.debug( "  EXPERIMENT WORKFLOW : program_path '" + program_path + "'" )
      fo = open( program_path, "r" )
      for line in fo :
        logging.debug( "    " + line.strip( "\n" ) )
      fo.close()
  
      logging.debug( "  EXPERIMENT WORKFLOW : TABLE_PATH = '" + self.TABLE_PATH + "'" )
      fo = open( self.TABLE_PATH, "r" )
      for line in fo :
        logging.debug( "    " + line.strip( "\n" ) )
      fo.close()
  
      logging.debug( "  EXPERIMENT WORKFLOW : TYPE_PATH '" + self.TYPE_PATH + "'" )
      fo = open( self.TYPE_PATH, "r" )
      for line in fo :
        logging.debug( "    " + line.strip( "\n" ) )
      fo.close()
  
      sys.exit( "exiting on PRINT_STOP..." )
  
    # ---------------------------------------------------- #
    # run the hacked molly branch on the program files
    # step 1. copy over tables for this experiment 
    #         (necc. b/c saving eval results per 
    #         LDFI iteration).
    # step 2. cd into the specified molly clone.
    # step 3. run molly on the generated and 
    #         pre-processed iapyx file.
    os.system( '\
      cp ' + self.TABLE_PATH + ' ' + self.MOLLY_PATH + ' ; \
      cp ' + self.TYPE_PATH  + ' ' + self.MOLLY_PATH + ' ; \
      cd ' + self.MOLLY_PATH + ' ; \
      sbt "run-main edu.berkeley.cs.boom.molly.SyncFTChecker \
  	' + program_path + ' \
  	--EOT ' + str( argDict[ "EOT" ] ) + ' \
  	--EFF ' + str( argDict[ "EFF" ] ) + '  \
  	--nodes ' + ",".join( argDict[ "nodes" ] ) + ' \
  	--crashes ' + str( argDict[ "crashes" ] ) + ' \
  	--ignore-prov-nodes domcomp_,dom_ \
  	--prov-diagrams"' )
  
    # ----------------------------------- #
    # save metrics to file
    #
  
    self.clean_dirs( argDict )

  
  ###############
  #  CLEAN TMP  #
  ###############
  # remove leftover data from previous tests
  def clean_tmp( self ) :

    # ---------------------- #
    # create a clean tmp_data/
  
    if os.path.exists( "./tmp_data/" ) :
      logging.debug( "rm -rf ./tmp_data/" )
      os.system( "rm -rf ./tmp_data/" )
  
    logging.debug( "mkdir ./tmp_data/" )
    os.system( "mkdir ./tmp_data/" )

  
  ################
  #  CLEAN DIRS  #
  ################
  # remove leftover data from previous tests
  def clean_dirs( self, argDict ) :
  
    # ---------------------- #
    # remove rogue IR files
  
    if os.path.exists( "./IR*" ) :
      logging.debug( "rm -rf ./IR.db" )
      os.system( "rm -rf ./IR.db" )

    # ---------------------- #
    # clear c4 tmp files

    try :
      C4_HOME_PATH = tools.getConfig( argDict[ "settings" ], "DEFAULT", "C4_HOME_PATH", str )
      try :
        # for safety:
        C4_HOME_PATH = C4_HOME_PATH.replace( "/c4_home", "" )
        C4_HOME_PATH = C4_HOME_PATH.replace( "//", "" )

        assert( os.path.isdir( C4_HOME_PATH ) == True )
        os.system( "rm -rf " + C4_HOME_PATH + "/c4_home/*" )

      except AssertionError :
        raise AssertionError( C4_HOME_PATH + " does not exist." )

    except ConfigParser.NoOptionError as e :
      logging.info( "  FATAL ERROR : option 'C4_HOME_PATH' not set in settings file '" + argDict[ "settings" ] + "'. aborting." )
      raise e


  ###############
  #  GET ERROR  #
  ###############
  # extract error message from system info
  def getError( self, sysInfo ) :
    return str( sysInfo[1] )


  ########################
  #  GET ACTUAL RESULTS  #
  ########################
  def getActualResults( self, programLines ) :
    program_string  = "\n".join( programLines )
    program_string += "\n" # add extra newline to align with read() parsing
    return program_string


  ##################
  #  GET ARG DICT  #
  ##################
  def getArgDict( self, inputfile ) :

    # initialize
    argDict = {}

    # populate with unit test defaults
    argDict[ 'prov_diagrams' ]            = False
    argDict[ 'use_symmetry' ]             = False
    argDict[ 'crashes' ]                  = 0
    argDict[ 'solver' ]                   = None
    argDict[ 'disable_dot_rendering' ]    = False
    argDict[ 'settings' ]                 = "./settings.ini"
    argDict[ 'negative_support' ]         = False
    argDict[ 'strategy' ]                 = None
    argDict[ 'file' ]                     = inputfile
    argDict[ 'EOT' ]                      = 4
    argDict[ 'find_all_counterexamples' ] = False
    argDict[ 'nodes' ]                    = [ "a", "b", "c" ]
    argDict[ 'evaluator' ]                = "c4"
    argDict[ 'EFF' ]                      = 2
    argDict[ 'data_save_path' ]           = './data/'

    return argDict


if __name__ == "__main__" :
  if os.path.exists( "./IR*.db*" ) :
    logging.debug( "removing all ./IR*.db* files." )
    os.remove( "./IR*.db*" )
  unittest.main()
  if os.path.exists( "./IR*.db*" ) :
    logging.debug( "removing all ./IR*.db* files." )
    os.remove( "./IR*.db*" )


#########
#  EOF  #
#########
