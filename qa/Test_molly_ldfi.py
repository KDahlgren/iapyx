#!/usr/bin/env python

'''
Test_molly_ldfi.py
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


#####################
#  TEST MOLLY LDFI  #
#####################
class Test_molly_ldfi( unittest.TestCase ) :

  logging.basicConfig( format='%(levelname)s:%(message)s', level=logging.DEBUG )
  #logging.basicConfig( format='%(levelname)s:%(message)s', level=logging.INFO )
  #logging.basicConfig( format='%(levelname)s:%(message)s', level=logging.WARNING )

  PRINT_STOP   = False
  SKIP_ASSERTS = True

  MOLLY_PATH = os.getcwd() + "/../lib/molly/"
  TABLE_PATH = os.getcwd() + "/tmp_data/iapyx_tables.data" # filename hard-coded in molly
  TYPE_PATH  = os.getcwd() + "/tmp_data/iapyx_types.data"  # filename hard-coded in molly

  ####################
  #  SMALLER DEMO 2  #
  ####################
  #@unittest.skip( "working on different example." )
  def test_smaller_demo_2( self ) :

    test_id    = "smaller_demo_2"
    input_file = "smaller_demo_2.ded"

    logging.debug( "  TEST MOLLY LDFI : running " + test_id )

    program_path  = os.getcwd() + "/tmp_data/iapyx_program.olg"
    metrics_path  = "./metrics_data/metrics.data"
    tmp_path      = "./tmp_data/"

    # define parameters
    driver_path   = "./testFiles/" + input_file
    crashes       = "0"
    node_list     = [ "noaa", "myapp", "sunny" ]
    eot           = "3"
    eff           = "2"
    evaluator     = "c4"
    settings_path = "./settings_files/settings_smaller_demo_dm.ini"

    argDict = {  "file"           : driver_path, \
                 "crashes"        : crashes, \
                 "nodes"          : node_list, \
                 "EOT"            : eot, \
                 "EFF"            : eff, \
                 "evaluator"      : evaluator, \
                 "settings"       : settings_path, \
                 "data_save_path" : "./data" }

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

  ###################
  #  TCP HANDSHAKE  #
  ###################
  #@unittest.skip( "working on different example." )
  def test_tcp_handshake( self ) :

    test_id    = "tcp_handshake"
    input_file = "tcp_handshake.ded"

    logging.debug( "  TEST MOLLY LDFI : running " + test_id )

    program_path  = os.getcwd() + "/tmp_data/iapyx_program.olg"
    metrics_path  = "./metrics_data/metrics.data"
    tmp_path      = "./tmp_data/"

    # define parameters
    driver_path   = "./testFiles/" + input_file
    crashes       = "0"
    node_list     = [ "a", "b" ]
    eot           = "3"
    eff           = "3"
    evaluator     = "c4"
    settings_path = "./settings_files/settings_tcp_handshake.ini"

    argDict = {  "file"           : driver_path, \
                 "crashes"        : crashes, \
                 "nodes"          : node_list, \
                 "EOT"            : eot, \
                 "EFF"            : eff, \
                 "evaluator"      : evaluator, \
                 "settings"       : settings_path, \
                 "data_save_path" : "./data" }

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


  #####################
  #  KAFKA FAIL CASE  #
  #####################
  #@unittest.skip( "working on different example." )
  def test_kafka_failcase( self ) :

    test_id    = "kafka_failcase"
    input_file = "kafka_driver.ded"

    logging.debug( "  TEST MOLLY LDFI : running " + test_id )

    program_path  = os.getcwd() + "/tmp_data/iapyx_program.olg"
    metrics_path  = "./metrics_data/metrics.data"
    tmp_path      = "./tmp_data/"

    # define parameters
    driver_path   = "./testFiles/" + input_file
    crashes       = "1"
    node_list     = [ "a", "b", "c", "C", "Z" ]
    eot           = "7"
    eff           = "4"
    evaluator     = "c4"
    settings_path = "./settings_files/settings_kafka.ini"

    argDict = {  "file"      : driver_path, \
                 "crashes"   : crashes, \
                 "nodes"     : node_list, \
                 "EOT"       : eot, \
                 "EFF"       : eff, \
                 "evaluator" : evaluator, \
                 "settings"  : settings_path }

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


  ###########
  #  KAFKA  #
  ###########
  #@unittest.skip( "working on different example." )
  def test_kafka( self ) :

    test_id    = "kafka"
    input_file = "kafka_driver.ded"

    logging.debug( "  TEST MOLLY LDFI : running " + test_id )

    program_path  = os.getcwd() + "/tmp_data/iapyx_program.olg"
    metrics_path  = "./metrics_data/metrics.data"
    tmp_path      = "./tmp_data/"

    # define parameters
    driver_path   = "./testFiles/" + input_file
    crashes       = "0"
    node_list     = [ "a", "b", "c", "C", "Z" ]
    eot           = "7"
    eff           = "4"
    evaluator     = "c4"
    settings_path = "./settings_files/settings_kafka.ini"

    argDict = {  "file"      : driver_path, \
                 "crashes"   : crashes, \
                 "nodes"     : node_list, \
                 "EOT"       : eot, \
                 "EFF"       : eff, \
                 "evaluator" : evaluator, \
                 "settings"  : settings_path }

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


  ##########
  #  3 PC  #
  ##########
  @unittest.skip( "working on different example." )
  def test_3pc( self ) :
    test_id = "test_3pc"
    logging.debug( "  TEST MOLLY LDFI : running " + test_id )

    program_path  = os.getcwd() + "/tmp_data/iapyx_program.olg"
    metrics_path  = "./metrics_data/metrics.data"
    tmp_path      = "./tmp_data/"

    # define parameters
    driver_path   = "./testFiles/3pc_driver.ded"
    crashes       = "0"
    node_list     = [ "a", "b", "C", "d" ]
    eot           = "4"
    eff           = "2"
    evaluator     = "c4"
    settings_path = "./settings_files/settings_setTypes.ini"

    argDict = {  "file"      : driver_path, \
                 "crashes"   : crashes, \
                 "nodes"     : node_list, \
                 "EOT"       : eot, \
                 "EFF"       : eff, \
                 "evaluator" : evaluator, \
                 "settings"  : settings_path }

    self.experiment_workflow( program_path, \
                              metrics_path, \
                              tmp_path, \
                              driver_path, \
                              argDict )

    if not self.SKIP_ASSERTS :

      # insert asserts here:
      actual_json_results_path   = self.MOLLY_PATH + "output/runs.json"
      expected_json_results_path = os.getcwd() + "/testFiles/runs_kafka.json"

      actual_num_iterations, actual_conclusion     = self.get_molly_results( actual_json_results_path )
      expected_num_iterations, expected_conclusion = self.get_molly_results( expected_json_results_path )

      self.assertEqual( actual_num_iterations, expected_num_iterations )
      self.assertEqual( actual_conclusion, expected_conclusion )

    logging.debug( "  TEST MOLLY LDFI : " + test_id + " ...done." )


  #####################
  #  EXAMPLE THING 1  #
  #####################
  #@unittest.skip( "working on different example." )
  def test_example_thing_1( self ) :
    test_id = "example_thing_1"
    logging.debug( "  TEST MOLLY LDFI : running " + test_id )

    program_path  = os.getcwd() + "/tmp_data/iapyx_program.olg"
    metrics_path  = "./metrics_data/metrics.data"
    tmp_path      = "./tmp_data/"

    # define parameters
    driver_path   = "./testFiles/example_thing_1.ded"
    crashes       = "0"
    node_list     = [ "astring0", "astring1", "astring2" ]
    eot           = "2"
    eff           = "0"
    evaluator     = "c4"
    settings_path = "./settings_files/settings_dm.ini"

    argDict = {  "file"      : driver_path, \
                 "crashes"   : crashes, \
                 "nodes"     : node_list, \
                 "EOT"       : eot, \
                 "EFF"       : eff, \
                 "evaluator" : evaluator, \
                 "settings"  : settings_path, \
                 "data_save_path"  : "./data" }

    self.experiment_workflow( program_path, \
                              metrics_path, \
                              tmp_path, \
                              driver_path, \
                              argDict )

    if not self.SKIP_ASSERTS :

      # insert asserts here:
      actual_json_results_path   = self.MOLLY_PATH + "output/runs.json"
      expected_json_results_path = os.getcwd() + "/testFiles/runs_example_thing_1.json"
  
      actual_num_iterations, actual_conclusion     = self.get_molly_results( actual_json_results_path )
      expected_num_iterations, expected_conclusion = self.get_molly_results( expected_json_results_path )
  
      self.assertEqual( actual_num_iterations, expected_num_iterations )
      self.assertEqual( actual_conclusion, expected_conclusion )

    logging.debug( "  TEST MOLLY LDFI : " + test_id + " ...done." )


  ##############
  #  TOY 2 V2  #
  ##############
  #@unittest.skip( "working on different example." )
  def test_toy2_v2( self ) :
    test_id = "test_toy2_v2"
    logging.debug( "  TEST MOLLY LDFI : running " + test_id )

    program_path  = os.getcwd() + "/tmp_data/iapyx_program.olg"
    metrics_path  = "./metrics_data/metrics.data"
    tmp_path      = "./tmp_data/"

    # define parameters
    driver_path   = "./testFiles/toy2_v2.ded"
    crashes       = "0"
    node_list     = [ "a", "b", "c" ]
    eot           = "2"
    eff           = "0"
    evaluator     = "c4"
    settings_path = "./settings_files/settings_use_aggs.ini"

    argDict = {  "file"      : driver_path, \
                 "crashes"   : crashes, \
                 "nodes"     : node_list, \
                 "EOT"       : eot, \
                 "EFF"       : eff, \
                 "evaluator" : evaluator, \
                 "settings"  : settings_path }

    self.experiment_workflow( program_path, \
                              metrics_path, \
                              tmp_path, \
                              driver_path, \
                              argDict )

    if not self.SKIP_ASSERTS :

      # insert asserts here:
      actual_json_results_path   = self.MOLLY_PATH + "output/runs.json"
      expected_json_results_path = os.getcwd() + "/testFiles/runs_toy2_v2.json"
  
      actual_num_iterations, actual_conclusion     = self.get_molly_results( actual_json_results_path )
      expected_num_iterations, expected_conclusion = self.get_molly_results( expected_json_results_path )
  
      self.assertEqual( actual_num_iterations, expected_num_iterations )
      self.assertEqual( actual_conclusion, expected_conclusion )

    logging.debug( "  TEST MOLLY LDFI : " + test_id + " ...done." )


  ##########################################
  #  PAPER DEMO V3 FIX WILDS FAIL CASE DM  #
  ##########################################
  #@unittest.skip( "stuck in datalog set types." )
  def test_paper_demo_v3_fix_wilds_failcase_dm( self ) :

    test_id    = "paper_demo_v3_failcase_fix_wilds_dm"
    input_file = "paper_demo_v3_fix_wilds.ded"

    logging.debug( "  TEST MOLLY LDFI : running " + test_id )

    program_path  = os.getcwd() + "/tmp_data/iapyx_program.olg"
    metrics_path  = "./metrics_data/metrics.data"
    tmp_path      = "./tmp_data/"

    # define parameters
    driver_path   = "./testFiles/" + input_file
    crashes       = "0"
    node_list     = [ "a", "jobscheduler" ]
    eot           = "5"
    eff           = "4"
    evaluator     = "c4"
    settings_path = "./settings_files/settings_dm.ini"

    argDict = {  "file"            : driver_path, \
                 "crashes"         : crashes, \
                 "nodes"           : node_list, \
                 "EOT"             : eot, \
                 "EFF"             : eff, \
                 "evaluator"       : evaluator, \
                 "settings"        : settings_path, \
                 "data_save_path"  : "./data" }

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


  ################################
  #  PAPER DEMO V3 FAIL CASE DM  #
  ################################
  #@unittest.skip( "stuck in datalog set types." )
  def test_paper_demo_v3_failcase_dm( self ) :

    test_id    = "paper_demo_v3_failcase"
    input_file = "paper_demo_v3.ded"

    logging.debug( "  TEST MOLLY LDFI : running " + test_id )

    program_path  = os.getcwd() + "/tmp_data/iapyx_program.olg"
    metrics_path  = "./metrics_data/metrics.data"
    tmp_path      = "./tmp_data/"

    # define parameters
    driver_path   = "./testFiles/" + input_file
    crashes       = "0"
    node_list     = [ "a", "jobscheduler" ]
    eot           = "5"
    eff           = "4"
    evaluator     = "c4"
    settings_path = "./settings_files/settings_dm.ini"

    argDict = {  "file"      : driver_path, \
                 "crashes"   : crashes, \
                 "nodes"     : node_list, \
                 "EOT"       : eot, \
                 "EFF"       : eff, \
                 "evaluator" : evaluator, \
                 "settings"  : settings_path }

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


  #######################################
  #  PAPER DEMO V3 FIX WILDS FAIL CASE  #
  #######################################
  #@unittest.skip( "stuck in datalog set types." )
  def test_paper_demo_v3_fix_wilds_failcase( self ) :

    test_id    = "paper_demo_v3_failcase_fix_wilds"
    input_file = "paper_demo_v3_fix_wilds.ded"

    logging.debug( "  TEST MOLLY LDFI : running " + test_id )

    program_path  = os.getcwd() + "/tmp_data/iapyx_program.olg"
    metrics_path  = "./metrics_data/metrics.data"
    tmp_path      = "./tmp_data/"

    # define parameters
    driver_path   = "./testFiles/" + input_file
    crashes       = "0"
    node_list     = [ "a", "jobscheduler" ]
    eot           = "5"
    eff           = "4"
    evaluator     = "c4"
    settings_path = "./settings_files/settings_regular.ini"

    argDict = {  "file"      : driver_path, \
                 "crashes"   : crashes, \
                 "nodes"     : node_list, \
                 "EOT"       : eot, \
                 "EFF"       : eff, \
                 "evaluator" : evaluator, \
                 "settings"  : settings_path }

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


  #############################
  #  PAPER DEMO V3 FAIL CASE  #
  #############################
  #@unittest.skip( "stuck in datalog set types." )
  def test_paper_demo_v3_failcase( self ) :

    test_id    = "paper_demo_v3_failcase"
    input_file = "paper_demo_v3.ded"

    logging.debug( "  TEST MOLLY LDFI : running " + test_id )

    program_path  = os.getcwd() + "/tmp_data/iapyx_program.olg"
    metrics_path  = "./metrics_data/metrics.data"
    tmp_path      = "./tmp_data/"

    # define parameters
    driver_path   = "./testFiles/" + input_file
    crashes       = "0"
    node_list     = [ "a", "jobscheduler" ]
    eot           = "5"
    eff           = "4"
    evaluator     = "c4"
    settings_path = "./settings_files/settings_regular.ini"

    argDict = {  "file"      : driver_path, \
                 "crashes"   : crashes, \
                 "nodes"     : node_list, \
                 "EOT"       : eot, \
                 "EFF"       : eff, \
                 "evaluator" : evaluator, \
                 "settings"  : settings_path }

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


  ######################
  #  PAPER DEMO V3 DM  #
  ######################
  #@unittest.skip( "stuck in datalog set types." )
  def test_paper_demo_v3_dm( self ) :

    test_id    = "paper_demo_v3_dm"
    input_file = "paper_demo_v3_fix_wilds.ded"

    logging.debug( "  TEST MOLLY LDFI : running " + test_id )

    program_path  = os.getcwd() + "/tmp_data/iapyx_program.olg"
    metrics_path  = "./metrics_data/metrics.data"
    tmp_path      = "./tmp_data/"

    # define parameters
    driver_path   = "./testFiles/" + input_file
    crashes       = "0"
    #node_list     = [ "a", "c", "job1", "jobscheduler" ] # failure-free case
    node_list     = [ "a", "job1", "jobscheduler" ]  # fail case Set(MessageLoss(a,jobscheduler,1))
    eot           = "5"
    eff           = "4"
    evaluator     = "c4"
    settings_path = "./settings_files/settings_dm.ini"

    argDict = {  "file"           : driver_path, \
                 "crashes"        : crashes, \
                 "nodes"          : node_list, \
                 "EOT"            : eot, \
                 "EFF"            : eff, \
                 "evaluator"      : evaluator, \
                 "settings"       : settings_path, \
                 "data_save_path" : "./data" }

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


  ###################
  #  PAPER DEMO V3  #
  ###################
  #@unittest.skip( "stuck in datalog set types." )
  def test_paper_demo_v3( self ) :

    test_id    = "paper_demo_v3"
    input_file = test_id + ".ded"

    logging.debug( "  TEST MOLLY LDFI : running " + test_id )

    program_path  = os.getcwd() + "/tmp_data/iapyx_program.olg"
    metrics_path  = "./metrics_data/metrics.data"
    tmp_path      = "./tmp_data/"

    # define parameters
    driver_path   = "./testFiles/" + input_file
    crashes       = "0"
    #node_list     = [ "a", "c", "job1", "jobscheduler" ] # failure-free case
    node_list     = [ "a", "job1", "jobscheduler" ]  # fail case Set(MessageLoss(a,jobscheduler,1))
    eot           = "5"
    eff           = "4"
    evaluator     = "c4"
    settings_path = "./settings_files/settings_regular.ini"

    argDict = {  "file"           : driver_path, \
                 "crashes"        : crashes, \
                 "nodes"          : node_list, \
                 "EOT"            : eot, \
                 "EFF"            : eff, \
                 "evaluator"      : evaluator, \
                 "settings"       : settings_path, \
                 "data_save_path" : "./data" }

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


  ################
  #  DM SIMPLOG  #
  ################
  #@unittest.skip( "working on different example." )
  def test_dm_simplog( self ) :
    test_id = "test_dm_simplog"
    logging.debug( "  TEST MOLLY LDFI : running " + test_id )
    logging.debug( "  TEST MOLLY LDFI : " + test_id + " ...done." )
    return None


  #############
  #  SIMPLOG  #
  #############
  #@unittest.skip( "working on different example." )
  def test_simplog( self ) :
    test_id = "test_simplog"
    logging.debug( "  TEST MOLLY LDFI : running " + test_id )

    program_path  = os.getcwd() + "/tmp_data/iapyx_program.olg"
    metrics_path  = "./metrics_data/metrics.data"
    tmp_path      = "./tmp_data/"
  
    # define parameters
    driver_path   = "./testFiles/simplog_driver.ded"
    crashes       = "0"
    node_list     = [ "a", "b", "c" ]
    eot           = "4"
    eff           = "2"
    evaluator     = "c4"
    settings_path = "./settings_files/settings_regular.ini"
 
    argDict = {  "file"      : driver_path, \
                 "crashes"   : crashes, \
                 "nodes"     : node_list, \
                 "EOT"       : eot, \
                 "EFF"       : eff, \
                 "evaluator" : evaluator, \
                 "settings"  : settings_path }
 
    self.experiment_workflow( program_path, \
                              metrics_path, \
                              tmp_path, \
                              driver_path, \
                              argDict )

    # insert asserts here:
    actual_json_results_path   = self.MOLLY_PATH + "output/runs.json"
    expected_json_results_path = os.getcwd() + "/testFiles/runs_simplog.json"

    actual_num_iterations, actual_conclusion     = self.get_molly_results( actual_json_results_path )
    expected_num_iterations, expected_conclusion = self.get_molly_results( expected_json_results_path )

    self.assertEqual( actual_num_iterations, expected_num_iterations )
    self.assertEqual( actual_conclusion, expected_conclusion )

    logging.debug( "  TEST MOLLY LDFI : " + test_id + " ...done." )
    return None


  ###############
  #  DM DEMO 1  #
  ###############
  #@unittest.skip( "working on different example." )
  def test_dm_demo_1( self ) :
    test_id = "test_dm_demo_1"
    logging.debug( "  TEST MOLLY LDFI : running " + test_id )

    program_path = os.getcwd() + "/tmp_data/dm_demo_1.olg"
    metrics_path = "./metrics_data/metrics.data"
    tmp_path     = "./tmp_data/"

    # define parameters
    driver_path   = "./testFiles/demo_1_vldb_version.ded"
    crashes       = "0"
    node_list     = [ "a", "b", "c" ]
    eot           = "4"
    eff           = "1"
    evaluator     = "c4"
    settings_path = "./settings_files/settings_dm.ini"

    argDict = {  "file"      : driver_path, \
                 "crashes"   : crashes, \
                 "nodes"     : node_list, \
                 "EOT"       : eot, \
                 "EFF"       : eff, \
                 "evaluator" : evaluator, \
                 "settings"  : settings_path }

    self.experiment_workflow( program_path, \
                              metrics_path, \
                              tmp_path, \
                              driver_path, \
                              argDict )

    # insert asserts here :
    actual_json_results_path   = self.MOLLY_PATH + "output/runs.json"
    expected_json_results_path = os.getcwd() + "/testFiles/runs_dm_demo_1_vldb_version.json"

    actual_num_iterations, actual_conclusion     = self.get_molly_results( actual_json_results_path )
    expected_num_iterations, expected_conclusion = self.get_molly_results( expected_json_results_path )

    self.assertEqual( actual_num_iterations, expected_num_iterations )
    self.assertEqual( actual_conclusion, expected_conclusion )

    logging.debug( "  TEST MOLLY LDFI : " + test_id + " ...done." )
    return None


  ############
  #  DEMO 1  #
  ############
  #@unittest.skip( "working on different example." )
  def test_demo_1( self ) :
    test_id = "test_demo_1"
    logging.debug( "  TEST MOLLY LDFI : running " + test_id )

    program_path = os.getcwd() + "/tmp_data/demo_1.olg"
    metrics_path = "./metrics_data/metrics.data"
    tmp_path     = "./tmp_data/"

    # define parameters
    driver_path   = "./testFiles/demo_1_vldb_version.ded"
    crashes       = "0"
    node_list     = [ "a", "b", "c" ]
    eot           = "4"
    eff           = "1"
    evaluator     = "c4"
    settings_path = "./settings_files/settings_regular.ini"

    argDict = {  "file"      : driver_path, \
                 "crashes"   : crashes, \
                 "nodes"     : node_list, \
                 "EOT"       : eot, \
                 "EFF"       : eff, \
                 "evaluator" : evaluator, \
                 "settings"  : settings_path }
 
    self.experiment_workflow( program_path, \
                              metrics_path, \
                              tmp_path, \
                              driver_path, \
                              argDict )

    # insert asserts here :
    actual_json_results_path   = self.MOLLY_PATH + "output/runs.json"
    expected_json_results_path = os.getcwd() + "/testFiles/runs_demo_1_vldb_version.json"

    actual_num_iterations, actual_conclusion     = self.get_molly_results( actual_json_results_path )
    expected_num_iterations, expected_conclusion = self.get_molly_results( expected_json_results_path )

    self.assertEqual( actual_num_iterations, expected_num_iterations )
    self.assertEqual( actual_conclusion, expected_conclusion )

    logging.debug( "  TEST MOLLY LDFI : " + test_id + " ...done." )


  ############
  #  DEMO 0  #
  ############
  #@unittest.skip( "working on different example." )
  def test_demo_0( self ) :
    test_id = "test_demo_0"
    logging.debug( "  TEST MOLLY LDFI : running " + test_id )

    program_path = os.getcwd() + "/tmp_data/demo_0.olg"
    metrics_path = "./metrics_data/metrics.data"
    tmp_path     = "./tmp_data/"
  
    # define parameters
    driver_path   = "./testFiles/demo_0.ded"
    crashes       = "0"
    node_list     = [ "a", "b", "c" ]
    eot           = "4"
    eff           = "1"
    evaluator     = "c4"
    settings_path = "./settings_files/settings_regular.ini"
  
    argDict = {  "file"      : driver_path, \
                 "crashes"   : crashes, \
                 "nodes"     : node_list, \
                 "EOT"       : eot, \
                 "EFF"       : eff, \
                 "evaluator" : evaluator, \
                 "settings"  : settings_path }
  
    self.experiment_workflow( program_path, \
                              metrics_path, \
                              tmp_path, \
                              driver_path, \
                              argDict )

    # insert asserts here :
    actual_json_results_path   = self.MOLLY_PATH + "output/runs.json" 
    expected_json_results_path = os.getcwd() + "/testFiles/runs_demo_0.json" 

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
  
    allProgramData = iapyx.iapyx_driver( argDict )
  
    # collect program data
    program_array = allProgramData[0]
    table_array   = allProgramData[1]
  
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
  	#--negative-support \
  
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
    argDict[ 'negative_support' ]         = True
    argDict[ 'strategy' ]                 = None
    argDict[ 'file' ]                     = inputfile
    argDict[ 'EOT' ]                      = 4
    argDict[ 'find_all_counterexamples' ] = False
    argDict[ 'nodes' ]                    = [ "a", "b", "c" ]
    argDict[ 'evaluator' ]                = "c4"
    argDict[ 'EFF' ]                      = 2
    argDict[ 'data_save_path' ]           = "./data"

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
