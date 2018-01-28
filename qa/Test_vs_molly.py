#!/usr/bin/env python

'''
Test_vs_molly.py
'''

#############
#  IMPORTS  #
#############
# standard python packages
import inspect, logging, os, re, string, sqlite3, sys, unittest

# ------------------------------------------------------ #
# import sibling packages HERE!!!
if not os.path.abspath( __file__ + "/../../src" ) in sys.path :
  sys.path.append( os.path.abspath( __file__ + "/../../src" ) )

from dedt  import dedt, dedalusParser, clockRelation, dedalusRewriter
from utils import dumpers, globalCounters, tools

# ------------------------------------------------------ #


#############################################################################
#                                                                           #
#  NOTE!!!!                                                                 #
#                                                                           #
#    iapyx vs. molly comparisons ignore clock and crash fact differences.   #
#                                                                           #
#############################################################################

eqnOps = [ "==", "!=", ">=", "<=", ">", "<" ]

###################
#  TEST VS MOLLY  #
###################
class Test_vs_molly( unittest.TestCase ) :

  #logging.basicConfig( format='%(levelname)s:%(message)s', level=logging.DEBUG )
  #logging.basicConfig( format='%(levelname)s:%(message)s', level=logging.INFO )
  logging.basicConfig( format='%(levelname)s:%(message)s', level=logging.WARNING )

  PRINT_STOP = False

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
  #@unittest.skip( "working on another example." )
  def test_tokens( self ) :

    # specify input and output paths
    inputfile           = os.getcwd() + "/testFiles/tokens_driver.ded"
    expected_iapyx_path = "./testFiles/tokens_iapyx.olg"
    molly_path          = "./testFiles/tokens_molly.olg"

    self.comparison_workflow( inputfile, expected_iapyx_path, molly_path, "_tokens_" )


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
    molly_path          = "./testFiles/test_deliv_molly.olg"

    self.comparison_workflow( inputfile, expected_iapyx_path, molly_path, "_deliv_" )


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
    molly_path          = "./testFiles/test_ack_molly.olg"

    self.comparison_workflow( inputfile, expected_iapyx_path, molly_path, "_ack_" )


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
    molly_path          = "./testFiles/test2_molly.olg"

    self.comparison_workflow( inputfile, expected_iapyx_path, molly_path, "_test2_" )


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
    molly_path          = "./testFiles/register__molly.olg"

    self.comparison_workflow( inputfile, expected_iapyx_path, molly_path, "_register_" )


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
    molly_path          = "./testFiles/real_kafka_molly.olg"

    self.comparison_workflow( inputfile, expected_iapyx_path, molly_path, "_real_kafka_" )


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
    molly_path          = "./testFiles/real_chord_molly.olg"

    self.comparison_workflow( inputfile, expected_iapyx_path, molly_path, "_real_chord_" )


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
    molly_path          = "./testFiles/pipeline_molly.olg"

    self.comparison_workflow( inputfile, expected_iapyx_path, molly_path, "_pipeline_" )


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
  #@unittest.skip( "working on another example." )
  def test_paxos_synod( self ) :

    # specify input and output paths
    inputfile           = os.getcwd() + "/testFiles/paxos_synod_driver.ded"
    expected_iapyx_path = "./testFiles/paxos_synod_iapyx.olg"
    molly_path          = "./testFiles/paxos_synod_molly.olg"

    self.comparison_workflow( inputfile, expected_iapyx_path, molly_path, "_paxos_synod_" )


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
    molly_path          = "./testFiles/orc2_molly.olg"

    self.comparison_workflow( inputfile, expected_iapyx_path, molly_path, "_orc2_" )


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
    molly_path          = "./testFiles/orc_molly.olg"

    self.comparison_workflow( inputfile, expected_iapyx_path, molly_path, "_orc_" )


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
    molly_path          = "./testFiles/negative_support_test_molly.olg"

    self.comparison_workflow( inputfile, expected_iapyx_path, molly_path, "_negative_support_test_" )


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
    molly_path          = "./testFiles/kafka_molly.olg"

    self.comparison_workflow( inputfile, expected_iapyx_path, molly_path, "_kafka_" )


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
    molly_path          = "./testFiles/chain_replication_molly.olg"

    self.comparison_workflow( inputfile, expected_iapyx_path, molly_path, "_chain_replication_" )


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
    molly_path          = "./testFiles/barrier_test_molly.olg"

    self.comparison_workflow( inputfile, expected_iapyx_path, molly_path, "_barrier_test_" )


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
    molly_path          = "./testFiles/ramp_molly.olg"

    self.comparison_workflow( inputfile, expected_iapyx_path, molly_path, "_ramp_" )


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
    molly_path          = "./testFiles/raft_molly.olg"

    self.comparison_workflow( inputfile, expected_iapyx_path, molly_path, "_raft_" )


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
    molly_path          = "./testFiles/gstore_molly.olg"

    self.comparison_workflow( inputfile, expected_iapyx_path, molly_path, "_gstore_" )


  ##################################
  #  EXAMPLE FLUX PARTITION PAIRS  #
  ##################################
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
    molly_path          = "./testFiles/flux_partitionpairs_molly.olg"

    self.comparison_workflow( inputfile, expected_iapyx_path, molly_path, "_flux_partitionpairs_" )


  ################################
  #  EXAMPLE FLUX CLUSTER PAIRS  #
  ################################
  #
  # sbt "run-main edu.berkeley.cs.boom.molly.SyncFTChecker \
  # 	src/test/resources/examples_ft/flux/flux_clusterpairs.ded \
  # 	--EOT 4 \
  # 	--EFF 2 \
  # 	--nodes a,b,c \
  # 	--crashes 0 \
  # 	--prov-diagrams"
  #
  #@unittest.skip( "working on another example." )
  def test_flux_clusterpairs( self ) :

    # specify input and output paths
    inputfile           = os.getcwd() + "/testFiles/flux_clusterpairs_driver.ded"
    expected_iapyx_path = "./testFiles/flux_clusterpairs_iapyx.olg"
    molly_path          = "./testFiles/flux_clusterpairs_molly.olg"

    self.comparison_workflow( inputfile, expected_iapyx_path, molly_path, "_flux_clusterpairs_" )


  ###########################
  #  EXAMPLE 3 PC OPTIMIST  #
  ###########################
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
  #@unittest.skip( "working on different example" )
  def test_3pc_optimist( self ) :

    # specify input and output paths
    inputfile           = os.getcwd() + "/testFiles/3pc_optimist_driver.ded"
    expected_iapyx_path = "./testFiles/3pc_optimist_iapyx.olg"
    molly_path          = "./testFiles/3pc_optimist_molly.olg"

    self.comparison_workflow( inputfile, expected_iapyx_path, molly_path, "_3pc_optimist_" )


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
  #@unittest.skip( "working on different example" )
  def test_3pc( self ) :

    # specify input and output paths
    inputfile           = os.getcwd() + "/testFiles/3pc_driver.ded"
    expected_iapyx_path = "./testFiles/3pc_iapyx.olg"
    molly_path          = "./testFiles/3pc_molly.olg"

    self.comparison_workflow( inputfile, expected_iapyx_path, molly_path, "_3pc_" )


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
  #@unittest.skip( "working on different example" )
  def test_2pc_ctp_optimist( self ) :

    # specify input and output paths
    inputfile           = os.getcwd() + "/testFiles/2pc_ctp_optimist_driver.ded"
    expected_iapyx_path = "./testFiles/2pc_ctp_optimist_iapyx.olg"
    molly_path          = "./testFiles/2pc_ctp_optimist_molly.olg"

    self.comparison_workflow( inputfile, expected_iapyx_path, molly_path, "_2pc_ctp_optimist_" )


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
  #@unittest.skip( "working on different example" )
  def test_2pc_ctp( self ) :

    # specify input and output paths
    inputfile           = os.getcwd() + "/testFiles/2pc_ctp_driver.ded"
    expected_iapyx_path = "./testFiles/2pc_ctp_iapyx.olg"
    molly_path          = "./testFiles/2pc_ctp_molly.olg"

    self.comparison_workflow( inputfile, expected_iapyx_path, molly_path, "_2pc_ctp_" )


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
  #@unittest.skip( "working on different example" )
  def test_2pc_optimist( self ) :

    # specify input and output paths
    inputfile           = os.getcwd() + "/testFiles/2pc_optimist_driver.ded"
    expected_iapyx_path = "./testFiles/2pc_optimist_iapyx.olg"
    molly_path          = "./testFiles/2pc_optimist_molly.olg"

    self.comparison_workflow( inputfile, expected_iapyx_path, molly_path, "_2pc_optimist_" )


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
  #@unittest.skip( "working on different example" )
  def test_2pc( self ) :

    # specify input and output paths
    inputfile = os.getcwd() + "/testFiles/2pc_driver.ded"
    expected_iapyx_path = "./testFiles/2pc_iapyx.olg"
    molly_path          = "./testFiles/2pc_molly.olg"

    self.comparison_workflow( inputfile, expected_iapyx_path, molly_path, "_2pc_" )


  ####################
  #  EXAMPLE ACK RB  #
  ####################
  # tests ded to c4 datalog for ack reliable broadcast
  #@unittest.skip( "working on different example" )
  def test_ack_rb( self ) :

    # specify input and output paths
    inputfile           = os.getcwd() + "/testFiles/ack_rb_driver.ded"
    expected_iapyx_path = "./testFiles/ack_rb_iapyx.olg"
    molly_path          = "./testFiles/ack_rb_molly.olg"

    self.comparison_workflow( inputfile, expected_iapyx_path, molly_path, "_ack_rb_" )


  ########################
  #  EXAMPLE CLASSIC RB  #
  ########################
  # tests ded to c4 datalog for classic rb
  #@unittest.skip( "working on different example" )
  def test_classic_rb( self ) :

    # specify input and output paths
    inputfile           = os.getcwd() + "/testFiles/classic_rb_driver.ded"
    expected_iapyx_path = "./testFiles/classic_rb_iapyx.olg"
    molly_path          = "./testFiles/classic_rb_molly.olg"

    self.comparison_workflow( inputfile, expected_iapyx_path, molly_path, "_classic_rb_" )


  ####################
  #  EXAMPLE REPLOG  #
  ####################
  # tests ded to c4 datalog for replog
  #@unittest.skip( "working on different example" )
  def test_replog( self ) :

    # specify input and output paths
    inputfile           = os.getcwd() + "/testFiles/replog_driver.ded"
    expected_iapyx_path = "./testFiles/replog_iapyx.olg"
    molly_path          = "./testFiles/replog_molly.olg"

    self.comparison_workflow( inputfile, expected_iapyx_path, molly_path, "_replog_" )


  ####################
  #  EXAMPLE RDLOG  #
  ####################
  # tests ded to c4 datalog for rdlog
  #@unittest.skip( "working on different example" )
  def test_rdlog( self ) :

    # specify input and output paths
    inputfile           = os.getcwd() + "/testFiles/rdlog_driver.ded"
    expected_iapyx_path = "./testFiles/rdlog_iapyx.olg"
    molly_path          = "./testFiles/rdlog_molly.olg"

    self.comparison_workflow( inputfile, expected_iapyx_path, molly_path, "_rdlog_" )


  #####################
  #  EXAMPLE SIMPLOG  #
  #####################
  # tests ded to c4 datalog for simplog
  #@unittest.skip( "working on different example" )
  def test_simplog( self ) :

    # specify input and output paths
    inputfile           = os.getcwd() + "/testFiles/simplog_driver.ded"
    expected_iapyx_path = "./testFiles/simplog_iapyx.olg"
    molly_path          = "./testFiles/simplog_molly.olg"

    self.comparison_workflow( inputfile, expected_iapyx_path, molly_path, "_simplog_" )


  #########################
  #  COMPARISON WORKFLOW  #
  #########################
  # defines iapyx vs molly comparison workflow
  def comparison_workflow( self, inputfile, expected_iapyx_path, molly_path, db_name_append ) :

    # --------------------------------------------------------------- #
    # testing set up.

    if os.path.isfile( "./IR*.db*" ) :
      logging.debug( "  COMPARISON WORKFLOW : removing rogue IR*.db* files." )
      os.remove( "./IR*.db*" )

    testDB = "./IR" + db_name_append + ".db"
    IRDB    = sqlite3.connect( testDB )
    cursor  = IRDB.cursor()

    # --------------------------------------------------------------- #
    # reset counters for new test

    dedt.globalCounterReset()

    # --------------------------------------------------------------- #

    # specify input file path
    #inputfile = os.getcwd() + "/testFiles/simplog_driver.ded"

    # get argDict
    argDict = self.getArgDict( inputfile )

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
    #
    #expected_iapyx_path    = "./testFiles/simplog_iapyx.olg"
    expected_iapyx_results = None
    with open( expected_iapyx_path, 'r' ) as expectedFile :
      expected_iapyx_results = expectedFile.read()

    self.assertEqual( iapyx_results, expected_iapyx_results )

    # ========================================================== #
    # MOLLY COMPARISON
    #
    # grab expected output results as a string
    #
    #molly_path    = "./testFiles/simplog_molly.olg"
    molly_results = None
    with open( molly_path, 'r' ) as mollyFile :
      molly_results = mollyFile.read()

    #print "iapyx_results"
    #print iapyx_results
    #print "molly_results"
    #print molly_results

    match_elements_flag_iapyx, match_elements_flag_molly = self.compareIapyxAndMolly( iapyx_results, molly_results )

    self.assertEqual( True, match_elements_flag_iapyx )
    self.assertEqual( True, match_elements_flag_molly )

    # --------------------------------------------------------------- #
    #clean up testing
    IRDB.close()
    os.remove( testDB )


  #############################
  #  COMPARE IAPYX AND MOLLY  #
  #############################
  # compare programs minus all whitespace.
  # ignore clock and crash facts.
  def compareIapyxAndMolly( self, iapyx_results, molly_results ) :

    # ----------------------------------------------------- #
    # grab relevant substring from iapyx results
    iapyx_substring  = iapyx_results.split( "\nclock", 1 )                  # remove all clock facts (and crash facts)
    iapyx_substring  = iapyx_substring[0]
    iapyx_substring  = iapyx_substring.replace( "\n", "" )                  # remove all newlines
    iapyx_substring  = iapyx_substring.translate( None, string.whitespace ) # remove all whitespace
    iapyx_line_array = iapyx_substring.split( ";" )

    # ----------------------------------------------------- #
    # grab relevant substring from molly results
    molly_substring  = molly_results.split( "\nclock", 1 )                  # remove all clock facts
    molly_substring  = molly_substring[0]
    molly_substring  = molly_substring.replace( "\n", "" )                  # remove all newlines
    molly_substring  = molly_substring.translate( None, string.whitespace ) # remove all whitespace
    molly_line_array = molly_substring.split( ";" )

    # ----------------------------------------------------- #

    # NOTE!!! this is a bad condition test because molly doesn't remove
    #         duplicate lines before translation.

    # make sure lists contain all and only the same elements
    # (except wrt clock and crash facts)

    #if not len( iapyx_line_array ) == len( molly_line_array ) :
    #  error_msg = "  COMPARE IAPYX AND MOLLY : inconsistent number of program statements."
    #  if len( iapyx_line_array ) > len( molly_line_array ) :
    #    error_msg += " iapyx program contains _more_ lines than molly program."
    #  else :
    #    error_msg += " iapyx program contains _fewer_ lines than molly program."
    #  logging.debug( error_msg )
    #  return False

    # -------------------------------------------------------------------------------- #
    # make sure all lines in the iapyx program have a match in the molly program
    match_elements_flag_iapyx = False
    for iapyx_line in iapyx_line_array :

      logging.debug( "  COMPARE IAPYX AND MOLLY : iapyx_line = " + iapyx_line )

      # skip all crash facts from iapyx.
      if iapyx_line.startswith( 'crash("' ) :
        pass

      # skip all next_clock facts from iapyx.
      elif iapyx_line.startswith( 'next_clock("' ) :
        pass

      # skip all defines since molly's using some weird rule to 
      # order goal atts in prov rules.
      elif iapyx_line.startswith( "define(" ) and iapyx_line.endswith( "})" ) :
        pass

      else : # next question : does a matching line exist in the molly program?

        # if line is a rule, need a smarter comparison method
        if self.isRule( iapyx_line ) :

          logging.debug( "  COMPARE IAPYX AND MOLLY : iapyx_line = " + iapyx_line )

          if iapyx_line in molly_line_array :
            match_elements_flag_iapyx = True

          elif not self.matchExists( iapyx_line, molly_line_array ) :
            logging.debug( "  COMPARE IAPYX AND MOLLY (1) : iapyx_line '" + iapyx_line + "' not found in molly program." )
            match_elements_flag_iapyx = False

        # otherwise, line is a fact, so checking existence is sufficient.
        else :
          if not iapyx_line in molly_line_array :
            logging.debug( "  COMPARE IAPYX AND MOLLY (2) : iapyx_line '" + iapyx_line+ "' not found in molly program." )
            match_elements_flag_iapyx = False

    # -------------------------------------------------------------------------------- #
    # make sure all lines in the molly program have a match in the iapyx program
    match_elements_flag_molly = False
    for molly_line in molly_line_array :

      # skip all defines since molly's using some weird rule to 
      # order goal atts in prov rules.
      if molly_line.startswith( "define(" ) and molly_line.endswith( "})" ) :
        pass

      else : # next question : does a matching line exist in the iapyx program?

        # if line is a rule, need a smarter comparison method
        if self.isRule( molly_line ) :

          if molly_line in iapyx_line_array :
            match_elements_flag_molly = True

          elif not self.matchExists( molly_line, iapyx_line_array ) :
            logging.debug( "  COMPARE IAPYX AND MOLLY (1) : molly_line '" + molly_line + "' not found in iapyx program." )
            match_elements_flag = False

        # otherwise, line is a fact, so checking existence is sufficient.
        else :
          if not molly_line in iapyx_line_array :
            logging.debug( "  COMPARE IAPYX AND MOLLY (2) : molly_line '" + molly_line+ "' not found in iapyx program." )
            match_elements_flag_molly = False

    logging.debug( "  COMPARE IAPYX AND MOLLY : match_elements_flag_iapyx = " + str( match_elements_flag_iapyx ) )
    logging.debug( "  COMPARE IAPYX AND MOLLY : match_elements_flag_molly = " + str( match_elements_flag_molly ) )
    return match_elements_flag_iapyx, match_elements_flag_molly


  ##################
  #  MATCH EXISTS  #
  ##################
  # check if the iapyx_rule appears in the molly_line_array
  def matchExists( self, iapyx_rule, molly_line_array ) :

    logging.debug( "-------------------------------------------------------------" )
    logging.debug( "  MATCH EXISTS : iapyx_rule        = " + iapyx_rule )

    iapyx_goalName    = self.getGoalName( iapyx_rule )
    iapyx_goalAttList = self.getGoalAttList( iapyx_rule )
    iapyx_body        = self.getBody( iapyx_rule )

    logging.debug( "  MATCH EXISTS : iapyx_goalName    = " + iapyx_goalName )
    logging.debug( "  MATCH EXISTS : iapyx_goalAttList = " + str( iapyx_goalAttList ) )
    logging.debug( "  MATCH EXISTS : iapyx_body        = " + iapyx_body )

    for line in molly_line_array :

      if self.isRule( line ) :

        molly_goalName    = self.getGoalName( line )
        molly_goalAttList = self.getGoalAttList( line )
        molly_body        = self.getBody( line )
 
        logging.debug( "  MATCH EXISTS : molly_goalName    = " + molly_goalName )
        logging.debug( "  MATCH EXISTS : molly_goalAttList = " + str( molly_goalAttList ) )
        logging.debug( "  MATCH EXISTS : molly_body        = " + molly_body )

        # goal names and bodies match 
        if self.sameName( iapyx_goalName, molly_goalName ) :

          logging.debug( "  MATCH EXISTS : identical goalNames." )

          if self.sameBodies( iapyx_body, molly_body ) :

            logging.debug( "  MATCH EXISTS : identical goalNames." )

            # make sure all iapyx atts appear in the molly att list
            iapyx_match = False
            for iapyx_att in iapyx_goalAttList :
              if iapyx_att in molly_goalAttList :
                iapyx_match = True

            # make sure all molly atts appear in the iapyx att list
            molly_match = False
            for molly_att in molly_goalAttList :
              if molly_att in iapyx_goalAttList :
                molly_match = True

            if iapyx_match or molly_match :
              logging.debug( "  MATCH EXISTS : returning True" )
              return True

          else :
            logging.debug( "  MATCH EXISTS : different bodies : iapyx_body = " + iapyx_body + ", molly_body = " + molly_body  )

        else :
          logging.debug( "  MATCH EXISTS : different goalNames (sans _prov# appends) : iapyx_goalName = " + iapyx_goalName + ", molly_goalName = " + molly_goalName  )


    logging.debug( "  MATCH EXISTS : returning False" )
    return False


  #################
  #  SAME BODIES  #
  #################
  # separate subgoals and eqns in to separate lists.
  # make sure all elements appear in both lists.
  def sameBodies( self, body1, body2 ) :

    # compare eqn lists
    eqnList1 = self.getEqnList( body1 )
    eqnList2 = self.getEqnList( body2 )

    if len( eqnList1 ) == len( eqnList2 ) :
      eqnListLen = True
    else :
      eqnListLen = False

    sameEqns = False
    if eqnList1 == eqnList2 :
      sameEqns = True
    else :
      for e1 in eqnList1 :
        if e1 in eqnList2 :
          sameEqns = True

    # compare subgoal lists
    subgoalList1 = self.getSubgoalList( body1, eqnList1 )
    subgoalList2 = self.getSubgoalList( body2, eqnList2 )

    if len( subgoalList1 ) == len( subgoalList2 ) :
      subListLen = True
    else :
      subListLen = False

    sameSubgoals = False
    for e1 in subgoalList1 :
      if e1 in subgoalList2 :
        sameSubgoals = True

    logging.debug( "  SAME BODIES : eqnList1     = " + str( eqnList1 ) )
    logging.debug( "  SAME BODIES : eqnList2     = " + str( eqnList2 ) )
    logging.debug( "  SAME BODIES : subgoalList1 = " + str( subgoalList1 ) )
    logging.debug( "  SAME BODIES : subgoalList2 = " + str( subgoalList2 ) )
    logging.debug( "  SAME BODIES : subListLen   = " + str( subListLen ) )
    logging.debug( "  SAME BODIES : sameSubgoals = " + str( sameSubgoals ) )
    logging.debug( "  SAME BODIES : eqnListLen   = " + str( eqnListLen ) )
    logging.debug( "  SAME BODIES : sameEqns     = " + str( sameEqns ) )

    if subListLen and sameSubgoals and eqnListLen and sameEqns :
      return True
    else :
      return False


  ######################
  #  GET SUBGOAL LIST  #
  ######################
  # extract the list of subgoals from the given rule body
  def getSubgoalList( self, body, eqnList ) :

    # ========================================= #
    # replace eqn instances in line
    for eqn in eqnList :
      body = body.replace( eqn, "" )
  
    body = body.replace( ",,", "," )
  
    # ========================================= #
    # grab subgoals
  
    # grab indexes of commas separating subgoals
    indexList = self.getCommaIndexes( body )
  
    #print indexList
  
    # replace all subgoal-separating commas with a special character sequence
    tmp_body = ""
    for i in range( 0, len( body ) ) :
      if not i in indexList :
        tmp_body += body[i]
      else :
        tmp_body += "___SPLIT___HERE___"
    body = tmp_body
  
    # generate list of separated subgoals by splitting on the special
    # character sequence
    subgoalList = body.split( "___SPLIT___HERE___" )

    # remove empties
    tmp_subgoalList = []
    for sub in subgoalList :
      if not sub == "" :
        tmp_subgoalList.append( sub )
    subgoalList = tmp_subgoalList

    return subgoalList


  ##################
  #  GET EQN LIST  #
  ##################
  # extract the list of equations in the given rule body
  def getEqnList( self, body ) :

    body = body.split( "," )
  
    # get the complete list of eqns from the rule body
    eqnList = []
    for thing in body :
      if self.isEqn( thing ) :
        eqnList.append( thing )

    return eqnList


  #######################
  #  GET COMMA INDEXES  #
  #######################
  # given a rule body, get the indexes of commas separating subgoals.
  def getCommaIndexes( self, body ) :
  
    underscoreStr = self.getCommaIndexes_helper( body )
  
    indexList = []
    for i in range( 0, len( underscoreStr ) ) :
      if underscoreStr[i] == "," :
        indexList.append( i )
  
    return indexList
  
  
  ##############################
  #  GET COMMA INDEXES HELPER  #
  ##############################
  # replace all paren contents with underscores
  def getCommaIndexes_helper( self, body ) :
  
    # get the first occuring paren group
    nextParenGroup = "(" + re.search(r'\((.*?)\)',body).group(1) + ")"
  
    # replace the group with the same number of underscores in the body
    replacementStr = ""
    for i in range( 0, len(nextParenGroup)-2 ) :
      replacementStr += "_"
    replacementStr = "_" + replacementStr + "_" # use underscores to replace parentheses
  
    body = body.replace( nextParenGroup, replacementStr )
  
    # BASE CASE : no more parentheses
    if not "(" in body :
      return body
  
    # RECURSIVE CASE : yes more parentheses
    else :
      return self.getCommaIndexes_helper( body )


  ############
  #  IS EQN  #
  ############
  # check if input contents from the rule body is an equation
  def isEqn( self, sub ) :
  
    flag = False
    for op in eqnOps :
      if op in sub :
        flag = True
  
    return flag
  
  
  ###############
  #  SAME NAME  #
  ###############
  # extract the core name, without the '_prov' append, and compare
  # if rule name is an _vars#_prov, cut off at the end of the _vars append
  def sameName( self, name1, name2 ) :

    # extract the core name for the first input name
    if self.isAggsProvRewrite( name1 ) :
      endingStr = re.search( '(.*)_prov(.*)', name1 )
      coreName1 = name1.replace( endingStr.group(1), "" )
    elif self.isProvRewrite( name1 ) :
      coreName1 = name1.split( "_prov" )
      coreName1 = coreName1[:-1]
      coreName1 = "".join( coreName1 )
    else :
      coreName1 = name1

    # extract the core name for the second input name
    if self.isAggsProvRewrite( name2 ) :
      endingStr = re.search( '(.*)_prov(.*)', name2 )
      coreName2 = name1.replace( endingStr.group(1), "" )
    elif self.isProvRewrite( name2 ) :
      coreName2 = name2.split( "_prov" )
      coreName2 = coreName2[:-1]
      coreName2 = "".join( coreName2 )
    else :
      coreName2 = name2

    logging.debug( "  SAME NAME : coreName1 = " + coreName1 )
    logging.debug( "  SAME NAME : coreName2 = " + coreName2 )

    if coreName1 == coreName2 :
      logging.debug( "  SAME NAME : returning True" )
      return True
    else :
      logging.debug( "  SAME NAME : returning False" )
      return False


  ##########################
  #  IS AGGS PROV REWRITE  #
  ##########################
  # check if the input relation name is indicative of an aggregate provenance rewrite
  def isAggsProvRewrite( self, relationName ) :

    middleStr = re.search( '_vars(.*)_prov', relationName )

    if middleStr :
      if middleStr.group(1).isdigit() :
        if relationName.endswith( middleStr.group(1) ) :
          return True
        else :
          return False
      else :
        return False
    else :
      return False


  #####################
  #  IS PROV REWRITE  #
  #####################
  # check if the input relation name is indicative of an aggregate provenance rewrite
  def isProvRewrite( self, relationName ) :

    endingStr = re.search( '_prov(.*)', relationName )

    if endingStr :
      if endingStr.group(1).isdigit() :
        if relationName.endswith( endingStr.group(1) ) :
          return True
        else :
          return False
      else :
        return False
    else :
      return False


  ###################
  #  GET GOAL NAME  #
  ###################
  # extract the goal name from the input rule.
  def getGoalName( self, rule ) :

    logging.debug( "  GET GOAL NAME : rule     = " + rule )

    goalName = rule.split( "(", 1 )
    goalName = goalName[0]

    logging.debug( "  GET GOAL NAME : goalName = " + goalName )
    return goalName


  #######################
  #  GET GOAL ATT LIST  #
  #######################
  # extract the goal attribute list.
  def getGoalAttList( self, rule ) :

    attList = rule.split( ")", 1 )
    attList = attList[0]
    attList = attList.split( "(", 1 )
    attList = attList[1]
    attList = attList.split( "," )

    return attList


  ##############
  #  GET BODY  #
  ##############
  # extract the rule body.
  def getBody( self, rule ) :

    body = rule.split( ":-" )
    body = body[1]

    return body


  #############
  #  IS RULE  #
  #############
  # check if input program line denotes a rule
  def isRule( self, line ) :
    if ":-" in line :
      return True
    else :
      return False


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

    return argDict


if __name__ == "__main__" :
  unittest.main()
  if os.path.exists( "./IR*.db*" ) :
    os.remove( "./IR*.db*" )

#########
#  EOF  #
#########
