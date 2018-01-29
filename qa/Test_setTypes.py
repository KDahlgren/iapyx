#!/usr/bin/env python

'''
Test_setTypes.py
'''

#############
#  IMPORTS  #
#############
# standard python packages
import inspect, logging, os, string, sqlite3, sys, unittest

# ------------------------------------------------------ #
# import sibling packages HERE!!!
if not os.path.abspath( __file__ + "/../../src" ) in sys.path :
  sys.path.append( os.path.abspath( __file__ + "/../../src" ) )

from dedt       import dedt, dedalusParser, Fact, Rule, clockRelation, dedalusRewriter
from utils      import dumpers, globalCounters, tools, setTypes
from evaluators import c4_evaluator

# ------------------------------------------------------ #


####################
#  TEST SET TYPES  #
####################
class Test_setTypes( unittest.TestCase ) :

  logging.basicConfig( format='%(levelname)s:%(message)s', level=logging.DEBUG )
  #logging.basicConfig( format='%(levelname)s:%(message)s', level=logging.INFO )
  #logging.basicConfig( format='%(levelname)s:%(message)s', level=logging.WARNING )

  PRINT_STOP    = False
  COMPARE_PROGS = True

  ####################
  #  EXAMPLE TOKENS  #
  ####################
  # tests ded to c4 datalog for the token example 
  #
  # sbt "run-main edu.berkeley.cs.boom.molly.SyncFTChecker \
  #     src/test/resources/examples_ft/tokens.ded \
  #     --EOT 4 \
  #     --EFF 2 \
  #     --nodes a,b,c \
  #     --crashes 0 \
  #     --prov-diagrams"
  #
  @unittest.skip( "how did this not break molly? timer_cancel is undefined." )
  def test_tokens( self ) :

    # specify input and output paths
    inputfile           = os.getcwd() + "/testFiles/tokens_driver.ded"
    expected_iapyx_path = "./testFiles/tokens_iapyx.olg"
    expected_eval_path  = "./testFiles/tokens_molly_eval_setTypes.txt"

    # get argDict
    argDict = self.getArgDict( inputfile )
    argDict[ "settings" ] = "./settings_setTypes.ini"

    self.comparison_workflow( argDict, \
                              expected_iapyx_path, \
                              expected_eval_path )


  ########################
  #  EXAMPLE TEST DELIV  #
  ########################
  # tests ded to c4 datalog for the test deliv example
  #
  # sbt "run-main edu.berkeley.cs.boom.molly.SyncFTChecker \
  #     src/test/resources/examples_ft/test_deliv.ded \
  #     --EOT 4 \
  #     --EFF 2 \
  #     --nodes a,b,c \
  #     --crashes 0 \
  #     --prov-diagrams"
  #
  @unittest.skip( "missing asserts?" )
  def test_test_deliv( self ) :

    # specify input and output paths
    inputfile           = os.getcwd() + "/testFiles/test_deliv_driver.ded"
    expected_iapyx_path = "./testFiles/test_deliv_iapyx.olg"
    expected_eval_path  = "./testFiles/test_deliv_molly_eval_setTypes.txt"

    # get argDict
    argDict = self.getArgDict( inputfile )
    argDict[ "settings" ] = "./settings_setTypes.ini"

    self.comparison_workflow( argDict, \
                              expected_iapyx_path, \
                              expected_eval_path )


  ######################
  #  EXAMPLE TEST ACK  #
  ######################
  # tests ded to c4 datalog for the test ack example
  #
  # sbt "run-main edu.berkeley.cs.boom.molly.SyncFTChecker \
  #     src/test/resources/examples_ft/test_ack.ded \
  #     --EOT 4 \
  #     --EFF 2 \
  #     --nodes a,b,c \
  #     --crashes 0 \
  #     --prov-diagrams"
  #
  @unittest.skip( "missing asserts?" )
  def test_test_ack( self ) :

    # specify input and output paths
    inputfile           = os.getcwd() + "/testFiles/test_ack_driver.ded"
    expected_iapyx_path = "./testFiles/test_ack_iapyx.olg"
    expected_eval_path  = "./testFiles/test_ack_molly_eval_setTypes.txt"

    # get argDict
    argDict = self.getArgDict( inputfile )
    argDict[ "settings" ] = "./settings_setTypes.ini"

    self.comparison_workflow( argDict, \
                              expected_iapyx_path, \
                              expected_eval_path )


  ####################
  #  EXAMPLE TEST 2  #
  ####################
  # tests ded to c4 datalog for the test2 example
  #
  # sbt "run-main edu.berkeley.cs.boom.molly.SyncFTChecker \
  #     src/test/resources/examples_ft/test2.ded \
  #     --EOT 4 \
  #     --EFF 2 \
  #     --nodes a,b,c \
  #     --crashes 0 \
  #     --prov-diagrams"
  #
  @unittest.skip( "missing asserts?" )
  def test_test2( self ) :

    # specify input and output paths
    inputfile           = os.getcwd() + "/testFiles/test2_driver.ded"
    expected_iapyx_path = "./testFiles/test2_iapyx.olg"
    expected_eval_path  = "./testFiles/test2_molly_eval_setTypes.txt"

    # get argDict
    argDict = self.getArgDict( inputfile )
    argDict[ "settings" ] = "./settings_setTypes.ini"

    self.comparison_workflow( argDict, \
                              expected_iapyx_path, \
                              expected_eval_path )


  ########################
  #  EXAMPLE REGIS(T)ER  #
  ########################
  # tests ded to c4 datalog for the regis(t)er example
  #
  # sbt "run-main edu.berkeley.cs.boom.molly.SyncFTChecker \
  #     src/test/resources/examples_ft/register.ded \
  #     --EOT 4 \
  #     --EFF 2 \
  #     --nodes a,b,c \
  #     --crashes 0 \
  #     --prov-diagrams"
  #
  @unittest.skip( "java.lang.Exception: No evidence for type of column 1 of update" )
  def test_register( self ) :

    # specify input and output paths
    inputfile           = os.getcwd() + "/testFiles/register_driver.ded"
    expected_iapyx_path = "./testFiles/register_iapyx.olg"
    expected_eval_path  = "./testFiles/register_molly_eval_setTypes.txt"

    # get argDict
    argDict = self.getArgDict( inputfile )
    argDict[ "settings" ] = "./settings_setTypes.ini"

    self.comparison_workflow( argDict, \
                              expected_iapyx_path, \
                              expected_eval_path )


  ########################
  #  EXAMPLE REAL KAFKA  #
  ########################
  # tests ded to c4 datalog for the second kafka example
  #
  # sbt "run-main edu.berkeley.cs.boom.molly.SyncFTChecker \
  #     src/test/resources/examples_ft/real_kafka.ded \
  #     --EOT 4 \
  #     --EFF 2 \
  #     --nodes a,b,c \
  #     --crashes 0 \
  #     --prov-diagrams"
  #
  @unittest.skip( "missing asserts?" )
  def test_real_kafka( self ) :

    # specify input and output paths
    inputfile           = os.getcwd() + "/testFiles/real_kafka_driver.ded"
    expected_iapyx_path = "./testFiles/real_kafka_iapyx.olg"
    expected_eval_path  = "./testFiles/real_kafka_molly_eval_setTypes.txt"

    # get argDict
    argDict = self.getArgDict( inputfile )
    argDict[ "settings" ] = "./settings_setTypes.ini"

    self.comparison_workflow( argDict, \
                              expected_iapyx_path, \
                              expected_eval_path )


  ########################
  #  EXAMPLE REAL CHORD  #
  ########################
  # tests ded to c4 datalog for the second chord example
  #
  # sbt "run-main edu.berkeley.cs.boom.molly.SyncFTChecker \
  #     src/test/resources/examples_ft/real_chord.ded \
  #     --EOT 4 \
  #     --EFF 2 \
  #     --nodes a,b,c \
  #     --crashes 0 \
  #     --prov-diagrams"
  #
  @unittest.skip( "java.lang.AssertionError: assertion failed: Conflicting evidence for type of column 3 of can_stab_prov15" )
  def test_real_chord( self ) :

    # specify input and output paths
    inputfile           = os.getcwd() + "/testFiles/real_chord_driver.ded"
    expected_iapyx_path = "./testFiles/real_chord_iapyx.olg"
    expected_eval_path  = "./testFiles/real_chord_molly_eval_setTypes.txt"

    # get argDict
    argDict = self.getArgDict( inputfile )
    argDict[ "settings" ] = "./settings_setTypes.ini"

    self.comparison_workflow( argDict, \
                              expected_iapyx_path, \
                              expected_eval_path )


  ######################
  #  EXAMPLE PIPELINE  #
  ######################
  # tests ded to c4 datalog for paxos
  #
  # sbt "run-main edu.berkeley.cs.boom.molly.SyncFTChecker \
  #     src/test/resources/examples_ft/pipeline.ded \
  #     --EOT 4 \
  #     --EFF 2 \
  #     --nodes a,b,c \
  #     --crashes 0 \
  #     --prov-diagrams"
  #
  @unittest.skip( "java.io.FileNotFoundException: src/test/resources/examples_ft/./heartbeat.ded (No such file or directory)" )
  def test_pipeline( self ) :

    # specify input and output paths
    inputfile           = os.getcwd() + "/testFiles/pipeline_driver.ded"
    expected_iapyx_path = "./testFiles/pipeline_iapyx.olg"
    expected_eval_path  = "./testFiles/pipeline_molly_eval_setTypes.txt"

    # get argDict
    argDict = self.getArgDict( inputfile )
    argDict[ "settings" ] = "./settings_setTypes.ini"

    self.comparison_workflow( argDict, \
                              expected_iapyx_path, \
                              expected_eval_path )


  #########################
  #  EXAMPLE PAXOS SYNOD  #
  #########################
  # tests ded to c4 datalog for paxos
  #
  # sbt "run-main edu.berkeley.cs.boom.molly.SyncFTChecker \
  #     src/test/resources/examples_ft/paxos_synod.ded \
  #     --EOT 4 \
  #     --EFF 2 \
  #     --nodes a,b,c \
  #     --crashes 0 \
  #     --prov-diagrams"
  #
  @unittest.skip( "how did this not break molly? timer_cancel is undefined." )
  def test_paxos_synod( self ) :

    # specify input and output paths
    inputfile           = os.getcwd() + "/testFiles/paxos_synod_driver.ded"
    expected_iapyx_path = "./testFiles/paxos_synod_iapyx.olg"
    expected_eval_path  = "./testFiles/paxos_synod_molly_eval_setTypes.txt"

    # get argDict
    argDict = self.getArgDict( inputfile )
    argDict[ "settings" ] = "./settings_setTypes.ini"

    self.comparison_workflow( argDict, \
                              expected_iapyx_path, \
                              expected_eval_path )


  ###################
  #  EXAMPLE ORC 2  #
  ###################
  # tests ded to c4 datalog for the second orc spec
  #
  # sbt "run-main edu.berkeley.cs.boom.molly.SyncFTChecker \
  #     src/test/resources/examples_ft/orc2.ded \
  #     --EOT 4 \
  #     --EFF 2 \
  #     --nodes a,b,c \
  #     --crashes 0 \
  #     --prov-diagrams"
  #
  @unittest.skip( "missing asserts?" )
  def test_orc2( self ) :

    # specify input and output paths
    inputfile           = os.getcwd() + "/testFiles/orc2_driver.ded"
    expected_iapyx_path = "./testFiles/orc2_iapyx.olg"
    expected_eval_path  = "./testFiles/orc2_molly_eval_setTypes.txt"

    # get argDict
    argDict = self.getArgDict( inputfile )
    argDict[ "settings" ] = "./settings_setTypes.ini"

    self.comparison_workflow( argDict, \
                              expected_iapyx_path, \
                              expected_eval_path )


  #################
  #  EXAMPLE ORC  #
  #################
  # tests ded to c4 datalog for orc
  #
  # sbt "run-main edu.berkeley.cs.boom.molly.SyncFTChecker \
  #     src/test/resources/examples_ft/orc.ded \
  #     --EOT 4 \
  #     --EFF 2 \
  #     --nodes a,b,c \
  #     --crashes 0 \
  #     --prov-diagrams"
  #
  @unittest.skip( "missing asserts?" )
  def test_orc( self ) :

    # specify input and output paths
    inputfile           = os.getcwd() + "/testFiles/orc_driver.ded"
    expected_iapyx_path = "./testFiles/orc_iapyx.olg"
    expected_eval_path  = "./testFiles/orc_molly_eval_setTypes.txt"

    # get argDict
    argDict = self.getArgDict( inputfile )
    argDict[ "settings" ] = "./settings_setTypes.ini"

    self.comparison_workflow( argDict, \
                              expected_iapyx_path, \
                              expected_eval_path )


  ###################################
  #  EXAMPLE NEGATIVE SUPPORT TEST  #
  ###################################
  # tests ded to c4 datalog for the negative support test
  #
  # sbt "run-main edu.berkeley.cs.boom.molly.SyncFTChecker \
  #     src/test/resources/examples_ft/negative_support_test.ded \
  #     --EOT 4 \
  #     --EFF 2 \
  #     --nodes a,b,c \
  #     --crashes 0 \
  #     --prov-diagrams"
  #
  @unittest.skip( "missing asserts?" )
  def test_negative_support_test( self ) :

    # specify input and output paths
    inputfile           = os.getcwd() + "/testFiles/negative_support_test_driver.ded"
    expected_iapyx_path = "./testFiles/negative_support_test_iapyx.olg"
    expected_eval_path  = "./testFiles/negative_support_test_molly_eval_setTypes.txt"

    # get argDict
    argDict = self.getArgDict( inputfile )
    argDict[ "settings" ] = "./settings_setTypes.ini"

    self.comparison_workflow( argDict, \
                              expected_iapyx_path, \
                              expected_eval_path )


  ###################
  #  EXAMPLE KAFKA  #
  ###################
  # tests ded to c4 datalog for kafka
  #
  # sbt "run-main edu.berkeley.cs.boom.molly.SyncFTChecker \
  #     src/test/resources/examples_ft/kafka.ded \
  #     --EOT 4 \
  #     --EFF 2 \
  #     --nodes a,b,c \
  #     --crashes 0 \
  #     --prov-diagrams"
  #
  @unittest.skip( "   SANITY CHECK SYNTAX RULE : ERROR : invalid syntax in line 'clients(Z,C)@async:-client(C),zookeeper(M,Z);' all subgoals in next and async rules must have identical first attributes.." )
  def test_kafka( self ) :

    # specify input and output paths
    inputfile           = os.getcwd() + "/testFiles/kafka_driver.ded"
    expected_iapyx_path = "./testFiles/kafka_iapyx.olg"
    expected_eval_path  = "./testFiles/karka_molly_eval_setTypes.txt"

    # get argDict
    argDict = self.getArgDict( inputfile )
    argDict[ "settings" ] = "./settings_setTypes.ini"

    self.comparison_workflow( argDict, \
                              expected_iapyx_path, \
                              expected_eval_path )


  ###############################
  #  EXAMPLE CHAIN REPLICATION  #
  ###############################
  # tests ded to c4 datalog for the chain replication example
  #
  # sbt "run-main edu.berkeley.cs.boom.molly.SyncFTChecker \
  #     src/test/resources/examples_ft/chain_replication.ded \
  #     --EOT 4 \
  #     --EFF 2 \
  #     --nodes a,b,c \
  #     --crashes 0 \
  #     --prov-diagrams"
  #
  @unittest.skip( "java.io.FileNotFoundException: src/test/resources/examples_ft/./heartbeat.ded (No such file or directory)" )
  def test_chain_replication( self ) :

    # specify input and output paths
    inputfile           = os.getcwd() + "/testFiles/chain_replication_driver.ded"
    expected_iapyx_path = "./testFiles/chain_replication_iapyx.olg"
    expected_eval_path  = "./testFiles/barrier_molly_eval_setTypes.txt"

    # get argDict
    argDict = self.getArgDict( inputfile )
    argDict[ "settings" ] = "./settings_setTypes.ini"

    self.comparison_workflow( argDict, \
                              expected_iapyx_path, \
                              expected_eval_path )


  ##########################
  #  EXAMPLE BARRIER TEST  #
  ##########################
  # tests ded to c4 datalog for the barrier test example
  #
  # sbt "run-main edu.berkeley.cs.boom.molly.SyncFTChecker \
  #     src/test/resources/examples_ft/barrier_test.ded \
  #     --EOT 4 \
  #     --EFF 2 \
  #     --nodes a,b,c \
  #     --crashes 0 \
  #     --prov-diagrams"
  #
  @unittest.skip( "missing asserts?" )
  def test_barrier_test( self ) :

    # specify input and output paths
    inputfile           = os.getcwd() + "/testFiles/barrier_test_driver.ded"
    expected_iapyx_path = "./testFiles/barrier_test_iapyx.olg"
    expected_eval_path  = "./testFiles/barrier_molly_eval_setTypes.txt"

    # get argDict
    argDict = self.getArgDict( inputfile )
    argDict[ "settings" ] = "./settings_setTypes.ini"

    self.comparison_workflow( argDict, \
                              expected_iapyx_path, \
                              expected_eval_path )


  ##################
  #  EXAMPLE RAMP  #
  ##################
  # tests ded to c4 datalog for ramp
  #
  # sbt "run-main edu.berkeley.cs.boom.molly.SyncFTChecker \
  #     src/test/resources/examples_ft/ramp/ramp.ded \
  #     --EOT 4 \
  #     --EFF 2 \
  #     --nodes a,b,c \
  #     --crashes 0 \
  #     --prov-diagrams"
  #
  @unittest.skip( "missing asserts?" )
  def test_ramp( self ) :

    # specify input and output paths
    inputfile           = os.getcwd() + "/testFiles/ramp_driver.ded"
    expected_iapyx_path = "./testFiles/ramp_iapyx.olg"
    expected_eval_path  = "./testFiles/ramp_molly_eval_setTypes.txt"

    # get argDict
    argDict = self.getArgDict( inputfile )
    argDict[ "settings" ] = "./settings_setTypes.ini"

    self.comparison_workflow( argDict, \
                              expected_iapyx_path, \
                              expected_eval_path )


  ##################
  #  EXAMPLE RAFT  #
  ##################
  # tests ded to c4 datalog for raft
  #
  # sbt "run-main edu.berkeley.cs.boom.molly.SyncFTChecker \
  #     src/test/resources/examples_ft/raft/raft.ded \
  #     --EOT 4 \
  #     --EFF 2 \
  #     --nodes a,b,c \
  #     --crashes 0 \
  #     --prov-diagrams"
  #
  @unittest.skip( "missing asserts?" )
  def test_raft( self ) :

    # specify input and output paths
    inputfile           = os.getcwd() + "/testFiles/raft_driver.ded"
    expected_iapyx_path = "./testFiles/raft_iapyx.olg"
    expected_eval_path  = "./testFiles/raft_molly_eval_setTypes.txt"

    # get argDict
    argDict = self.getArgDict( inputfile )
    argDict[ "settings" ] = "./settings_setTypes.ini"

    self.comparison_workflow( argDict, \
                              expected_iapyx_path, \
                              expected_eval_path )


  ####################
  #  EXAMPLE GSTORE  #
  ####################
  # tests ded to c4 datalog for gstore
  #
  # sbt "run-main edu.berkeley.cs.boom.molly.SyncFTChecker \
  #     src/test/resources/examples_ft/gstore/gstore.ded \
  #     --EOT 4 \
  #     --EFF 2 \
  #     --nodes a,b,c \
  #     --crashes 0 \
  #     --prov-diagrams"
  #
  @unittest.skip( "missing asserts?" )
  def test_gstore( self ) :

    # specify input and output paths
    inputfile           = os.getcwd() + "/testFiles/gstore_driver.ded"
    expected_iapyx_path = "./testFiles/gstore_iapyx.olg"
    expected_eval_path  = "./testFiles/gstore_molly_eval_setTypes.txt"

    # get argDict
    argDict = self.getArgDict( inputfile )
    argDict[ "settings" ] = "./settings_setTypes.ini"

    self.comparison_workflow( argDict, \
                              expected_iapyx_path, \
                              expected_eval_path )


  ##################################
  #  EXAMPLE FLUX PARTITION PAIRS  #
  ##################################
  # tests ded to c4 datalog for 3pc with optimistic assertions
  #
  # sbt "run-main edu.berkeley.cs.boom.molly.SyncFTChecker \
  # 	src/test/resources/examples_ft/flux/flux_partitionpairs.ded \
  # 	--EOT 4 \
  # 	--EFF 2 \
  # 	--nodes a,b,c \
  # 	--crashes 0 \
  # 	--prov-diagrams"
  #
  @unittest.skip( "SANITY CHECK SYNTAX RULE POST CHECKS : ERROR : invalid syntax in line 'pre(X):-put(_,X,_,_)@1;' line contains no negative subgoal NOT annotated with a numeric time argument." )
  def test_flux_partitionpairs( self ) :

    # specify input and output paths
    inputfile           = os.getcwd() + "/testFiles/flux_partitionpairs_driver.ded"
    expected_iapyx_path = "./testFiles/flux_partitionpairs_iapyx.olg"
    expected_eval_path  = "./testFiles/flux_partitionpairs_molly_eval_setTypes.txt"

    # get argDict
    argDict = self.getArgDict( inputfile )
    argDict[ "settings" ] = "./settings_setTypes.ini"

    self.comparison_workflow( argDict, \
                              expected_iapyx_path, \
                              expected_eval_path )


  ################################
  #  EXAMPLE FLUX CLUSTER PAIRS  #
  ################################
  # tests ded to c4 datalog for 3pc with optimistic assertions
  #
  # sbt "run-main edu.berkeley.cs.boom.molly.SyncFTChecker \
  # 	src/test/resources/examples_ft/flux/flux_clusterpairs.ded \
  # 	--EOT 4 \
  # 	--EFF 2 \
  # 	--nodes a,b,c \
  # 	--crashes 0 \
  # 	--prov-diagrams"
  #
  @unittest.skip( "how did this not break molly? del_conn is undefined." )
  def test_flux_clusterpairs( self ) :

    # specify input and output paths
    inputfile           = os.getcwd() + "/testFiles/flux_clusterpairs_driver.ded"
    expected_iapyx_path = "./testFiles/flux_clusterpairs_iapyx.olg"
    expected_eval_path  = "./testFiles/flux_clusterpairs_molly_eval_setTypes.txt"

    # get argDict
    argDict = self.getArgDict( inputfile )
    argDict[ "settings" ] = "./settings_setTypes.ini"

    self.comparison_workflow( argDict, \
                              expected_iapyx_path, \
                              expected_eval_path )


  ###########################
  #  EXAMPLE 3 PC OPTIMIST  #
  ###########################
  # tests ded to c4 datalog for 3pc with optimistic assertions
  #
  # sbt "run-main edu.berkeley.cs.boom.molly.SyncFTChecker \
  # 	src/test/resources/examples_ft/commit/3pc.ded \
  # 	src/test/resources/examples_ft/commit/2pc_assert_optimist.ded \
  # 	--EOT 4 \
  # 	--EFF 2 \
  # 	--nodes a,b,c \
  # 	--crashes 0 \
  # 	--prov-diagrams"
  #
  @unittest.skip( "working on different example" )
  def test_3pc_optimist( self ) :

    # specify input and output paths
    inputfile           = os.getcwd() + "/testFiles/3pc_optimist_driver.ded"
    expected_iapyx_path = "./testFiles/3pc_optimist_iapyx_iedb.olg"
    expected_eval_path  = "./testFiles/3pc_optimist_molly_eval_setTypes.txt"

    # get argDict
    argDict = self.getArgDict( inputfile )
    argDict[ "settings" ] = "./settings_setTypes.ini"

    self.comparison_workflow( argDict, \
                              expected_iapyx_path, \
                              expected_eval_path, \
                              "_setTypes_3pc_" )


  ##################
  #  EXAMPLE 3 PC  #
  ##################
  # tests ded to c4 datalog for 3pc
  #
  # sbt "run-main edu.berkeley.cs.boom.molly.SyncFTChecker \
  # 	src/test/resources/examples_ft/commit/3pc.ded \
  # 	src/test/resources/examples_ft/commit/2pc_assert.ded \
  # 	--EOT 4 \
  # 	--EFF 2 \
  # 	--nodes a,b,c \
  # 	--crashes 0 \
  # 	--prov-diagrams"
  #
  @unittest.skip( "working on different example" )
  def test_3pc( self ) :

    # specify input and output paths
    inputfile           = os.getcwd() + "/testFiles/3pc_driver.ded"
    expected_iapyx_path = "./testFiles/3pc_iapyx_iedb.olg"
    expected_eval_path  = "./testFiles/3pc_molly_eval_setTypes.txt"

    # get argDict
    argDict = self.getArgDict( inputfile )
    argDict[ "settings" ] = "./settings_setTypes.ini"

    self.comparison_workflow( argDict, \
                              expected_iapyx_path, \
                              expected_eval_path, \
                              "_setTypes_3pc_" )


  ###############################
  #  EXAMPLE 2 PC CTP OPTIMIST  #
  ###############################
  # tests ded to c4 datalog for 2pc conversational transaction protocol
  #
  # sbt "run-main edu.berkeley.cs.boom.molly.SyncFTChecker \
  # 	src/test/resources/examples_ft/commit/2pc_ctp.ded \
  # 	src/test/resources/examples_ft/commit/2pc_assert_optimist.ded \
  # 	--EOT 4 \
  # 	--EFF 2 \
  # 	--nodes a,b,c \
  # 	--crashes 0 \
  # 	--prov-diagrams"
  #
  @unittest.skip( "how did this not break in molly? timer_cancel is undefined." )
  def test_2pc_ctp_optimist( self ) :

    # specify input and output paths
    inputfile           = os.getcwd() + "/testFiles/2pc_ctp_optimist_driver.ded"
    expected_iapyx_path = "./testFiles/2pc_ctp_optimist_iapyx.olg"
    expected_eval_path  = "./testFiles/2pc_ctp_optimist_molly_eval_setTypes.txt"

    # get argDict
    argDict = self.getArgDict( inputfile )
    argDict[ "settings" ] = "./settings_setTypes.ini"

    self.comparison_workflow( argDict, \
                              expected_iapyx_path, \
                              expected_eval_path )


  ######################
  #  EXAMPLE 2 PC CTP  #
  ######################
  # tests ded to c4 datalog for 2pc conversational transaction protocol
  #
  # NOTES :
  #   observe both 2pc_ctp and 2pc_timeout include time_svc from utils.
  #   as a result, the molly output contains more program lines, while
  #   iapyx prevents line duplication prior to program translation.
  #
  # sbt "run-main edu.berkeley.cs.boom.molly.SyncFTChecker \
  # 	src/test/resources/examples_ft/commit/2pc_ctp.ded \
  # 	src/test/resources/examples_ft/commit/2pc_assert.ded \
  # 	--EOT 4 \
  # 	--EFF 2 \
  # 	--nodes a,b,c \
  # 	--crashes 0 \
  # 	--prov-diagrams"
  #
  @unittest.skip( "how does this not break in molly? timer_cancel is undefined." )
  def test_2pc_ctp( self ) :

    # specify input and output paths
    inputfile           = os.getcwd() + "/testFiles/2pc_ctp_driver.ded"
    expected_iapyx_path = "./testFiles/2pc_ctp_iapyx.olg"
    expected_eval_path  = "./testFiles/2pc_ctp_molly_eval_setTypes.txt"

    # get argDict
    argDict = self.getArgDict( inputfile )
    argDict[ "settings" ] = "./settings_setTypes.ini"

    self.comparison_workflow( argDict, \
                              expected_iapyx_path, \
                              expected_eval_path )


  ###########################
  #  EXAMPLE 2 PC OPTIMIST  #
  ###########################
  # tests ded to c4 datalog for optimistic 2pc
  #
  # sbt "run-main edu.berkeley.cs.boom.molly.SyncFTChecker \
  # 	src/test/resources/examples_ft/commit/2pc.ded \
  # 	src/test/resources/examples_ft/commit/2pc_assert_optimist.ded \
  # 	--EOT 4 \
  # 	--EFF 2 \
  # 	--nodes a,b,c \
  # 	--crashes 0 \
  # 	--prov-diagrams"
  #
  @unittest.skip( "working on different example" )
  def test_2pc_optimist( self ) :

    # specify input and output paths
    inputfile           = os.getcwd() + "/testFiles/2pc_optimist_driver.ded"
    expected_iapyx_path = "./testFiles/2pc_optimist_iapyx_iedb.olg"
    expected_eval_path  = "./testFiles/2pc_optimist_molly_eval_setTypes.txt"

    # get argDict
    argDict = self.getArgDict( inputfile )
    argDict[ "settings" ] = "./settings_setTypes.ini"

    self.comparison_workflow( argDict, \
                              expected_iapyx_path, \
                              expected_eval_path, \
                              "_setTypes_2pc_optimist_" )


  ##################
  #  EXAMPLE 2 PC  #
  ##################
  # tests ded to c4 datalog for 2pc
  #
  # sbt "run-main edu.berkeley.cs.boom.molly.SyncFTChecker \
  #	src/test/resources/examples_ft/commit/2pc.ded \
  #	src/test/resources/examples_ft/commit/2pc_assert.ded \
  #	--EOT 4 \
  #	--EFF 2 \
  #	--nodes a,b,c \
  #	--crashes 0 \
  #	--prov-diagrams"
  #
  @unittest.skip( "working on different example" )
  def test_2pc( self ) :

    # specify input and output paths
    inputfile = os.getcwd() + "/testFiles/2pc_driver.ded"
    expected_iapyx_path = "./testFiles/2pc_iapyx_iedb.olg"
    expected_eval_path  = "./testFiles/2pc_molly_eval_setTypes.txt"

    # get argDict
    argDict = self.getArgDict( inputfile )
    argDict[ "settings" ] = "./settings_setTypes.ini"

    self.comparison_workflow( argDict, \
                              expected_iapyx_path, \
                              expected_eval_path, \
                              "_setTypes_2pc_" )


  ####################
  #  EXAMPLE ACK RB  #
  ####################
  # tests ded to c4 datalog for ack reliable broadcast
  @unittest.skip( "working on different example" )
  def test_ack_rb( self ) :

    # specify input and output paths
    inputfile           = os.getcwd() + "/testFiles/ack_rb_driver.ded"
    expected_iapyx_path = "./testFiles/ack_rb_iapyx_iedb.olg"
    expected_eval_path  = "./testFiles/ack_rb_molly_eval_setTypes.txt"

    # get argDict
    argDict = self.getArgDict( inputfile )
    argDict[ "settings" ] = "./settings_setTypes.ini"

    self.comparison_workflow( argDict, \
                              expected_iapyx_path, \
                              expected_eval_path, \
                              "_setTypes_ack_rb_" )


  ########################
  #  EXAMPLE CLASSIC RB  #
  ########################
  # tests ded to c4 datalog for classic rb
  @unittest.skip( "working on different example" )
  def test_classic_rb( self ) :

    # specify input and output paths
    inputfile           = os.getcwd() + "/testFiles/classic_rb_driver.ded"
    expected_iapyx_path = "./testFiles/classic_rb_iapyx_iedb.olg"
    expected_eval_path  = "./testFiles/classic_rb_molly_eval_setTypes.txt"

    # get argDict
    argDict = self.getArgDict( inputfile )
    argDict[ "settings" ] = "./settings_setTypes.ini"

    self.comparison_workflow( argDict, \
                              expected_iapyx_path, \
                              expected_eval_path, \
                              "_setTypes_classic_rb_" )


  #########################
  #  SET TYPES REPLOG DM  #
  #########################
  # tests set types replog on dm
  @unittest.skip( "working on different example" )
  def test_setTypes_replog_dm( self ) :

    # specify input and output paths
    inputfile           = os.getcwd() + "/testFiles/replog_driver.ded"
    expected_iapyx_path = "./testFiles/replog_iapyx_setTypes_dm.olg"
    expected_eval_path  = "./testFiles/replog_molly_eval.txt"

    # get argDict
    argDict = self.getArgDict( inputfile )
    argDict[ "settings" ] = "./settings_setTypes_dm.ini"

    self.comparison_workflow( argDict, expected_iapyx_path, expected_eval_path, "_setTypes_replog_dm_" )


  ########################
  #  SET TYPES RDLOG DM  #
  ########################
  # tests rdlog on dm
  @unittest.skip( "working on different example" )
  def test_setTypes_rdlog_dm( self ) :

    # specify input and output paths
    inputfile           = os.getcwd() + "/testFiles/rdlog_driver.ded"
    expected_iapyx_path = "./testFiles/rdlog_iapyx_setTypes_dm.olg"
    expected_eval_path  = "./testFiles/rdlog_molly_eval.txt"

    # get argDict
    argDict = self.getArgDict( inputfile )
    argDict[ "settings" ] = "./settings_setTypes_dm.ini"

    self.comparison_workflow( argDict, expected_iapyx_path, expected_eval_path, "_setTypes_rdlog_dm_" )


  ##########################
  #  SET TYPES SIMPLOG DM  #
  ##########################
  # tests simplog on dm
  @unittest.skip( "working on different example" )
  def test_setTypes_simplog_dm( self ) :

    # specify input and output paths
    inputfile           = os.getcwd() + "/testFiles/simplog_driver.ded"
    expected_iapyx_path = "./testFiles/simplog_iapyx_setTypes_dm.olg"
    expected_eval_path  = "./testFiles/simplog_molly_eval.txt"

    # get argDict
    argDict = self.getArgDict( inputfile )
    argDict[ "settings" ] = "./settings_setTypes_dm.ini"

    self.comparison_workflow( argDict, expected_iapyx_path, expected_eval_path, "_setTypes_simplog_dm_" )


  ######################
  #  SET TYPES REPLOG  #
  ######################
  # tests replog
  @unittest.skip( "working on different example" )
  def test_setTypes_replog( self ) :

    # specify input and output paths
    inputfile           = os.getcwd() + "/testFiles/replog_driver.ded"
    expected_iapyx_path = "./testFiles/replog_iapyx_setTypes.olg"
    expected_eval_path  = "./testFiles/replog_molly_eval.txt"

    # get argDict
    argDict = self.getArgDict( inputfile )

    self.comparison_workflow( argDict, expected_iapyx_path, expected_eval_path, "_setTypes_replog_" )


  #####################
  #  SET TYPES RDLOG  #
  #####################
  # tests rdlog
  @unittest.skip( "working on different example" )
  def test_setTypes_rdlog( self ) :

    # specify input and output paths
    inputfile           = os.getcwd() + "/testFiles/rdlog_driver.ded"
    expected_iapyx_path = "./testFiles/rdlog_iapyx_setTypes.olg"
    expected_eval_path  = "./testFiles/rdlog_molly_eval.txt"

    # get argDict
    argDict = self.getArgDict( inputfile )

    self.comparison_workflow( argDict, expected_iapyx_path, expected_eval_path, "_setTypes_rdlog_" )


  #######################
  #  SET TYPES SIMPLOG  #
  #######################
  # tests simplog
  @unittest.skip( "working on different example" )
  def test_setTypes_simplog( self ) :

    # specify input and output paths
    inputfile           = os.getcwd() + "/testFiles/simplog_driver.ded"
    expected_iapyx_path = "./testFiles/simplog_iapyx_setTypes.olg"
    expected_eval_path  = "./testFiles/simplog_molly_eval.txt"

    # get argDict
    argDict = self.getArgDict( inputfile )

    self.comparison_workflow( argDict, expected_iapyx_path, expected_eval_path, "_setTypes_simplog_" )


  #########################
  #  SET TYPES EXAMPLE 1  #
  #########################
  # tests an example program
  #@unittest.skip( "working on different example" )
  def test_settypes_example_1( self ) :

    # specify input and output paths
    inputfile                    = os.getcwd() + "/testFiles/settypes_example_1.ded"
    expected_iapyx_settypes_path = "./testFiles/settypes_example_1.olg"

    # get argDict
    argDict = self.getArgDict( inputfile )

    self.comparison_workflow( argDict, expected_iapyx_settypes_path, None, "_setTypes_example_1_" )


  #########################
  #  COMPARISON WORKFLOW  #
  #########################
  # defines iapyx program comparison workflow
  def comparison_workflow( self, argDict, expected_iapyx_settypes_path, expected_eval_path, db_name_append ) :

    # --------------------------------------------------------------- #
    # testing set up.

    if os.path.isfile( "./IR*.db*" ) :
      logging.debug( "  COMPARISON WORKFLOW : removing rogue IR*.db* files." )
      os.remove( "./IR*.db*" )

    testDB = "./IR" + db_name_append + ".db"
    IRDB    = sqlite3.connect( testDB )
    cursor  = IRDB.cursor()

    if not os.path.isdir( argDict[ "data_save_path" ] ) :
      os.system( "mkdir " + argDict[ "data_save_path" ] )

    # --------------------------------------------------------------- #
    # reset counters for new test

    dedt.globalCounterReset()

    # --------------------------------------------------------------- #
    # runs through function to make sure it finishes with expected error

    # run translator
    programData = dedt.translateDedalus( argDict, cursor )

    # portray actual output program lines as a single string
    iapyx_results = self.getActualResults( programData[0] )

    if self.PRINT_STOP :
      print iapyx_results
      sys.exit( "print stop." )

    # ========================================================== #
    # IAPYX COMPARISON
    #
    # grab expected output results as a string

    if self.COMPARE_PROGS :
      expected_iapyx_results = None
      with open( expected_iapyx_settypes_path, 'r' ) as expectedFile :
        expected_iapyx_results = expectedFile.read()

      self.assertEqual( iapyx_results, expected_iapyx_results )

    # ========================================================== #
    # EVALUATION COMPARISON

    self.evaluate( programData, expected_eval_path )

    # --------------------------------------------------------------- #

    # ========================================================== #
    # CHECK TYPE MATCH

    self.typeMatch(cursor, programData )

    #clean up testing

    IRDB.close()
    os.remove( testDB )


  ##############
  #  EVALUATE  #
  ##############
  # evaluate the datalog program using some datalog evaluator
  # return some data structure or storage location encompassing the evaluation results.
  def evaluate( self, programData, expected_eval_path ) :

    noOverlap = False

    results_array = c4_evaluator.runC4_wrapper( programData )

    # ----------------------------------------------------------------- #
    # convert results array into dictionary

    eval_results_dict = tools.getEvalResults_dict_c4( results_array )

    # ----------------------------------------------------------------- #
    # collect all pos/not_ rule pairs

    rule_pairs = self.getRulePairs( eval_results_dict )

    logging.debug( "  EVALUATE : rule_pairs = " + str( rule_pairs ) )

    # ----------------------------------------------------------------- #
    # make sure tables do not overlap

    self.assertFalse( self.hasOverlap( rule_pairs, eval_results_dict ) )

    # ----------------------------------------------------------------- #
    # make sure settypes positive relation results are identical to molly
    # relation results

    if expected_eval_path :

      self.compare_evals( eval_results_dict, expected_eval_path )

  ###################
  #   TYPE MATCH    #
  ###################
  # check that subgoal types match correctly with their matching
  # rule
  def typeMatch( self, cursor, programData ) :
    # grab all rules type information
    cursor.execute("SELECT rid FROM Rule")
    rids = cursor.fetchall()
    rids = tools.toAscii_list( rids )
    ruleTypes = {}
    for rid in rids:
      r = dumpers.singleRuleAttDump( rid, cursor )
      ruleTypes[r['goalName']] = r

    # grab all facts
    cursor.execute("SELECT fid FROM Fact")
    fids = cursor.fetchall()
    fids = tools.toAscii_list( fids )
    factTypes = {}
    for fid in fids:
      continue

    # loop through and check matches between goals and subgoals
    for rid, rule in ruleTypes.iteritems():
      for subgoal in rule['subgoalAttData']:
        if subgoal[1] not in ruleTypes.keys():
          continue
        matchingGoal = ruleTypes[subgoal[1]]
        for i in range ( 0, len( subgoal[2] ) ) :
          attr = subgoal[2][i]
          matchingAttr = matchingGoal['goalAttData'][i]
          self.assertEqual( attr[2], matchingAttr[2] )


  ###################
  #  COMPARE EVALS  #
  ###################
  # compare the actual evaluation results with the 
  # expected evaluation results.
  def compare_evals( self, eval_results_dict, expected_eval_path ) :

    # ----------------------------------------------------------------- #
    # get a dictionary of the expected results

    expected_results_array = []
    fo = open( expected_eval_path )
    for line in fo :
      line = line.rstrip()
      expected_results_array.append( line )
    fo.close()

    expected_eval_results_dict = tools.getEvalResults_dict_c4( expected_results_array )

    # ----------------------------------------------------------------- #
    # compare all positive tables (not prov)

    for rel_key in eval_results_dict :

      # ----------------------------------------------------------------- #
      # skip not_ rules, _prov rules, adom_ rules

      if rel_key.startswith( "not_" ) or \
         rel_key.startswith( "domcomp_" ) or \
         rel_key.startswith( "dom_" ) or \
         rel_key.endswith( "_edb" ) or \
         rel_key == "adom_string" or \
         rel_key == "adom_int" or \
         "_prov" in rel_key or \
         "_agg" in rel_key :

        pass

      # ----------------------------------------------------------------- #

      else :

        actual_eval   = eval_results_dict[ rel_key ]
        expected_eval = expected_eval_results_dict[ rel_key ]

        flag = True
        for expected_row in expected_eval :
          if not expected_row in actual_eval :
            logging.debug( "  COMPARE_EVALS : missing row : relation = " + rel_key + "\nexpected_row = " + str( expected_row ) + "\nactual_eval = " + str( actual_eval ) )
            flag = False
            break

        self.assertTrue( flag )


  #################
  #  HAS OVERLAP  #
  #################
  # make sure pos and not_pos tables do not overlap
  def hasOverlap( self, rule_pairs, eval_results_dict ) :

    for pair in rule_pairs :

      logging.debug( "  HAS OVERLAP : pair = " + str( pair ) )

      pos_results = eval_results_dict[ pair[0] ]
      not_results = eval_results_dict[ pair[1] ]

      for pos_row in pos_results :
        if pos_row in not_results :
          logging.debug( "HAS OVERLAP : pos_row '" + str( pos_row ) + "' is in not_results:" )
          for not_row in not_results :
            logging.debug( "HAS OVERLAP : not_row " + str( not_row ) )
          return True

    return False


  ####################
  #  GET RULE PAIRS  #
  ####################
  # grab all pos/not_
  def getRulePairs( self, eval_results_dict ) :

    pair_list = []

    # pull out positive names
    for relName1 in eval_results_dict :

      if not relName1.startswith( "not_" ) and not "_prov" in relName1 :

        for relName2 in eval_results_dict :
  
          if not relName1 == relName2 :
            if relName2.startswith( "not_" ) and relName2[4:] == relName1 :
              pair_list.append( [ relName1, relName2 ] )

    return pair_list


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
    argDict[ 'settings' ]                 = "settings_settypes.ini"
    argDict[ 'negative_support' ]         = False
    argDict[ 'strategy' ]                 = None
    argDict[ 'file' ]                     = inputfile
    argDict[ 'EOT' ]                      = 4
    argDict[ 'find_all_counterexamples' ] = False
    argDict[ 'nodes' ]                    = [ "a", "b", "c" ]
    argDict[ 'evaluator' ]                = "c4"
    argDict[ 'EFF' ]                      = 2
    argDict[ 'data_save_path' ]           = "./data/"

    return argDict

if __name__ == "__main__" :
  unittest.main()
  if os.path.exists( "./IR*.db*" ) :
    os.remove( "./IR*.db*" )

#########
#  EOF  #
#########
