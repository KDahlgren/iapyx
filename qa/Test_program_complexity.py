#!/usr/bin/env python

'''
Test_program_complexity.py
'''

#############
#  IMPORTS  #
#############
# standard python packages
import inspect, logging, os, re, string, sqlite3, sys, unittest
import program_analysis_tools as pat

# ------------------------------------------------------ #
# import sibling packages HERE!!!
if not os.path.abspath( __file__ + "/../../src" ) in sys.path :
  sys.path.append( os.path.abspath( __file__ + "/../../src" ) )

from dedt  import dedt
from utils import tools
from evaluators import c4_evaluator

# ------------------------------------------------------ #


# LATEST FULL TEST SUITE TOTAL RUNTIME :
#  3615.768s


#############################
#  TEST PROGRAM COMPLEXITY  #
#############################
class Test_program_complexity( unittest.TestCase ) :

  logging.basicConfig( format='%(levelname)s:%(message)s', level=logging.DEBUG )
  #logging.basicConfig( format='%(levelname)s:%(message)s', level=logging.INFO )
  #logging.basicConfig( format='%(levelname)s:%(message)s', level=logging.WARNING )

  PRINT_STOP = False
  DM_RUNS    = True
  COMBO_RUNS = True
  MOLLY_RUNS = True

  ###########
  #  KAFKA  #
  ###########
  def test_kafka( self ) :

    MOLLY_EVAL = True
    COMBO_EVAL = True
    DM_EVAL    = False # dm conversion takes forever, but does hit the c4 stall eventually.

    # --------------------------------------------------------------- #
    # run kafka_molly

    if self.MOLLY_RUNS :
      test_id        = "program_complexity_kafka_molly"
      test_file_name = "kafka"
  
      print " >>> RUNNING " + test_id + " <<<"
  
      input_file                  = "./molly_progs/" + test_file_name + ".olg"
      argDict                     = self.getArgDict( input_file )
      argDict[ 'data_save_path' ] = "./data/" + test_id + "/"
  
      eval_molly = self.run_workflow( test_id, argDict, input_file, "molly", MOLLY_EVAL )

    # --------------------------------------------------------------- #
    # run kafka_combo

    if self.COMBO_RUNS :
      test_id        = "program_complexity_kafka_combo"
      test_file_name = "kafka_driver_program_complexity"

      print " >>> RUNNING " + test_id + " <<<"

      input_file                   = "./dedalus_drivers/" + test_file_name + ".ded"
      argDict                      = self.getArgDict( input_file )
      argDict[ 'data_save_path' ]  = "./data/" + test_id + "/"
      argDict[ 'EOT' ]             = 9
      argDict[ 'nodes' ]          = [ "a", "b", "c", "C", "d" ]
      argDict[ 'neg_writes' ]      = "combo"

      eval_combo = self.run_workflow( test_id, argDict, input_file, "combo", COMBO_EVAL )

    # --------------------------------------------------------------- #
    # run kafka_dm

    if self.DM_RUNS :
      test_id        = "program_complexity_kafka_dm"
      test_file_name = "kafka_driver_program_complexity"
  
      print " >>> RUNNING " + test_id + " <<<"
  
      input_file                  = "./dedalus_drivers/" + test_file_name + ".ded"
      argDict                     = self.getArgDict( input_file )
      argDict[ 'data_save_path' ] = "./data/" + test_id + "/"
      argDict[ 'EOT' ]            = 9
      argDict[ 'nodes' ]          = [ "a", "b", "c", "C", "d" ]
  
      eval_dm = self.run_workflow( test_id, argDict, input_file, "dm", DM_EVAL )

    if self.MOLLY_RUNS and self.DM_RUNS and self.COMBO_RUNS and \
       MOLLY_EVAL and DM_EVAL and COMBO_EVAL :
      self.check_results_alignment( eval_molly, eval_dm, eval_combo )

    # molly and combo only
    elif self.MOLLY_RUNS and self.COMBO_RUNS and \
       MOLLY_EVAL and COMBO_EVAL :
      self.check_results_alignment( eval_molly, [], eval_combo )


  ############
  #  3PC 97  #
  ############
  def test_3pc_97( self ) : 

    MOLLY_EVAL = True
    COMBO_EVAL = True
    DM_EVAL    = False # dm conversion takes forever, but hits c4 stall eventually.

    # --------------------------------------------------------------- #
    # run 3pc_molly

    if self.MOLLY_RUNS :
      test_id        = "program_complexity_3pc_97_molly"
      test_file_name = "3pc_97"
  
      print " >>> RUNNING " + test_id + " <<<"
  
      input_file                  = "./molly_progs/" + test_file_name + ".olg"
      argDict                     = self.getArgDict( input_file )
      argDict[ 'data_save_path' ] = "./data/" + test_id + "/"
  
      eval_molly = self.run_workflow( test_id, argDict, input_file, "molly", MOLLY_EVAL )

    # --------------------------------------------------------------- #
    # run 3pc_97_combo

    if self.COMBO_RUNS :
      test_id        = "program_complexity_3pc_97_combo"
      test_file_name = "3pc_driver_program_complexity"

      print " >>> RUNNING " + test_id + " <<<"

      input_file                   = "./dedalus_drivers/" + test_file_name + ".ded"
      argDict                      = self.getArgDict( input_file )
      argDict[ 'data_save_path' ]  = "./data/" + test_id + "/"
      argDict[ 'EOT' ]             = 9
      argDict[ 'nodes' ]           = [ "a", "b", "C", "d" ]
      argDict[ 'neg_writes' ]      = "combo"

      eval_combo = self.run_workflow( test_id, argDict, input_file, "combo", COMBO_EVAL )

    # --------------------------------------------------------------- #
    # run 3pc_97_dm

    if self.DM_RUNS :
      test_id        = "program_complexity_3pc_97_dm"
      test_file_name = "3pc_driver_program_complexity"
  
      print " >>> RUNNING " + test_id + " <<<"
  
      input_file                  = "./dedalus_drivers/" + test_file_name + ".ded"
      argDict                     = self.getArgDict( input_file )
      argDict[ 'data_save_path' ] = "./data/" + test_id + "/"
      argDict[ 'EOT' ]            = 9
      argDict[ 'nodes' ]          = [ "a", "b", "C", "d" ]
  
      eval_dm = self.run_workflow( test_id, argDict, input_file, "dm", DM_EVAL )

    if self.MOLLY_RUNS and self.DM_RUNS and self.COMBO_RUNS and \
       MOLLY_EVAL and DM_EVAL and COMBO_EVAL :
      self.check_results_alignment( eval_molly, eval_dm, eval_combo )

    # molly and combo only
    elif self.MOLLY_RUNS and self.COMBO_RUNS and \
       MOLLY_EVAL and COMBO_EVAL :
      self.check_results_alignment( eval_molly, [], eval_combo )


  ############
  #  3PC 80  #
  ############
  def test_3pc_80( self ) :

    MOLLY_EVAL = True
    COMBO_EVAL = True
    DM_EVAL    = False # dm conversion takes forever, but hits c4 stall eventually.

    # --------------------------------------------------------------- #
    # run 3pc_80_molly

    if self.MOLLY_RUNS :
      test_id        = "program_complexity_3pc_80_molly"
      test_file_name = "3pc_80"
  
      print " >>> RUNNING " + test_id + " <<<"
  
      input_file                  = "./molly_progs/" + test_file_name + ".olg"
      argDict                     = self.getArgDict( input_file )
      argDict[ 'data_save_path' ] = "./data/" + test_id + "/"
  
      eval_molly = self.run_workflow( test_id, argDict, input_file, "molly", MOLLY_EVAL )

    # --------------------------------------------------------------- #
    # run 3pc_80_combo

    if self.COMBO_RUNS :
      test_id        = "program_complexity_3pc_80_combo"
      test_file_name = "3pc_driver_program_complexity"

      print " >>> RUNNING " + test_id + " <<<"

      input_file                   = "./dedalus_drivers/" + test_file_name + ".ded"
      argDict                      = self.getArgDict( input_file )
      argDict[ 'data_save_path' ]  = "./data/" + test_id + "/"
      argDict[ 'EOT' ]             = 6
      argDict[ 'nodes' ]           = [ "a", "b", "C", "d" ]
      argDict[ 'neg_writes' ]      = "combo"

      eval_combo = self.run_workflow( test_id, argDict, input_file, "combo", COMBO_EVAL )

    # --------------------------------------------------------------- #
    # run 3pc_80_dm

    if self.DM_RUNS :
      test_id        = "program_complexity_3pc_80_dm"
      test_file_name = "3pc_driver_program_complexity"
  
      print " >>> RUNNING " + test_id + " <<<"
  
      input_file                  = "./dedalus_drivers/" + test_file_name + ".ded"
      argDict                     = self.getArgDict( input_file )
      argDict[ 'data_save_path' ] = "./data/" + test_id + "/"
      argDict[ 'EOT' ]            = 6
      argDict[ 'nodes' ]          = [ "a", "b", "C", "d" ]
  
      eval_dm = self.run_workflow( test_id, argDict, input_file, "dm", DM_EVAL )

    if self.MOLLY_RUNS and self.DM_RUNS and self.COMBO_RUNS and \
       MOLLY_EVAL and DM_EVAL and COMBO_EVAL :
      self.check_results_alignment( eval_molly, eval_dm, eval_combo )

    # molly and combo only
    elif self.MOLLY_RUNS and self.COMBO_RUNS and \
       MOLLY_EVAL and COMBO_EVAL :
      self.check_results_alignment( eval_molly, [], eval_combo )


  #############
  #  2PC CTP  #
  #############
  def test_2pc_ctp( self ) :

    MOLLY_EVAL = True
    COMBO_EVAL = True
    DM_EVAL    = False # dm conversion takes forever, but hits c4 eval stall eventually.

    # --------------------------------------------------------------- #
    # run 2pc_ctp_molly

    if self.MOLLY_RUNS :
      test_id        = "program_complexity_2pc_ctp_molly"
      test_file_name = "2pc_ctp"
  
      print " >>> RUNNING " + test_id + " <<<"
  
      input_file                  = "./molly_progs/" + test_file_name + ".olg"
      argDict                     = self.getArgDict( input_file )
      argDict[ 'data_save_path' ] = "./data/" + test_id + "/"
  
      eval_molly = self.run_workflow( test_id, argDict, input_file, "molly", MOLLY_EVAL )

    # --------------------------------------------------------------- #
    # run 2pc_ctp_combo

    if self.COMBO_RUNS :
      test_id        = "program_complexity_2pc_timout_optimist_combo"
      test_file_name = "2pc_ctp_driver_program_complexity"

      print " >>> RUNNING " + test_id + " <<<"

      input_file                   = "./dedalus_drivers/" + test_file_name + ".ded"
      argDict                      = self.getArgDict( input_file )
      argDict[ 'data_save_path' ]  = "./data/" + test_id + "/"
      argDict[ 'EOT' ]             = 6
      argDict[ 'nodes' ]           = [ "a", "b", "C", "d" ]
      argDict[ 'neg_writes' ]      = "combo"

      eval_combo = self.run_workflow( test_id, argDict, input_file, "combo", COMBO_EVAL )

    # --------------------------------------------------------------- #
    # run 2pc_ctp_dm

    if self.DM_RUNS :
      test_id        = "program_complexity_2pc_ctp_dm"
      test_file_name = "2pc_ctp_driver_program_complexity"
  
      print " >>> RUNNING " + test_id + " <<<"
  
      input_file                  = "./dedalus_drivers/" + test_file_name + ".ded"
      argDict                     = self.getArgDict( input_file )
      argDict[ 'data_save_path' ] = "./data/" + test_id + "/"
      argDict[ 'EOT' ]            = 6
      argDict[ 'nodes' ]          = [ "a", "b", "C", "d" ]
  
      eval_dm = self.run_workflow( test_id, argDict, input_file, "dm", DM_EVAL )

    if self.MOLLY_RUNS and self.DM_RUNS and self.COMBO_RUNS and \
       MOLLY_EVAL and DM_EVAL and COMBO_EVAL :
      self.check_results_alignment( eval_molly, eval_dm, eval_combo )

    # molly and combo only
    elif self.MOLLY_RUNS and self.COMBO_RUNS and \
       MOLLY_EVAL and COMBO_EVAL :
      self.check_results_alignment( eval_molly, [], eval_combo )


  #################
  #  2PC TIMEOUT  #
  #################
  def test_2pc_timeout( self ) :

    MOLLY_EVAL = True
    COMBO_EVAL = True
    DM_EVAL    = False # stalls at c4 eval

    # --------------------------------------------------------------- #
    # run 2pc_timeout_molly

    if self.MOLLY_RUNS :
      test_id        = "program_complexity_2pc_timeout_molly"
      test_file_name = "2pc_timeout"
  
      print " >>> RUNNING " + test_id + " <<<"
  
      input_file                  = "./molly_progs/" + test_file_name + ".olg"
      argDict                     = self.getArgDict( input_file )
      argDict[ 'data_save_path' ] = "./data/" + test_id + "/"
  
      eval_molly = self.run_workflow( test_id, argDict, input_file, "molly", MOLLY_EVAL )

    # --------------------------------------------------------------- #
    # run 2pc_timeout_combo

    if self.COMBO_RUNS :
      test_id        = "program_complexity_2pc_timout_optimist_combo"
      test_file_name = "2pc_timeout_driver_program_complexity"

      print " >>> RUNNING " + test_id + " <<<"

      input_file                   = "./dedalus_drivers/" + test_file_name + ".ded"
      argDict                      = self.getArgDict( input_file )
      argDict[ 'data_save_path' ]  = "./data/" + test_id + "/"
      argDict[ 'EOT' ]             = 6
      argDict[ 'nodes' ]           = [ "a", "b", "C", "d" ]
      argDict[ 'neg_writes' ]      = "combo"

      eval_combo = self.run_workflow( test_id, argDict, input_file, "combo", COMBO_EVAL )

    # --------------------------------------------------------------- #
    # run 2pc_timeout_dm

    if self.DM_RUNS :
      test_id        = "program_complexity_2pc_timeout_dm"
      test_file_name = "2pc_timeout_driver_program_complexity"
  
      print " >>> RUNNING " + test_id + " <<<"
  
      input_file                  = "./dedalus_drivers/" + test_file_name + ".ded"
      argDict                     = self.getArgDict( input_file )
      argDict[ 'data_save_path' ] = "./data/" + test_id + "/"
      argDict[ 'EOT' ]            = 6
      argDict[ 'nodes' ]          = [ "a", "b", "C", "d" ]
  
      eval_dm = self.run_workflow( test_id, argDict, input_file, "dm", DM_EVAL )

    if self.MOLLY_RUNS and self.DM_RUNS and self.COMBO_RUNS and \
       MOLLY_EVAL and DM_EVAL and COMBO_EVAL :
      self.check_results_alignment( eval_molly, eval_dm, eval_combo )

    # molly and combo only
    elif self.MOLLY_RUNS and self.COMBO_RUNS and \
       MOLLY_EVAL and COMBO_EVAL :
      self.check_results_alignment( eval_molly, [], eval_combo )


  ##########################
  #  2PC TIMEOUT OPTIMIST  #
  ##########################
  def test_2pc_timeout_optimist( self ) :

    MOLLY_EVAL = True
    COMBO_EVAL = True
    DM_EVAL    = False # stalls on c4 eval

    # --------------------------------------------------------------- #
    # run 2pc_timeout_optimist_molly

    if self.MOLLY_RUNS :
      test_id        = "program_complexity_2pc_timeout_optimist_molly"
      test_file_name = "2pc_timeout_optimist"
  
      print " >>> RUNNING " + test_id + " <<<"
  
      input_file                  = "./molly_progs/" + test_file_name + ".olg"
      argDict                     = self.getArgDict( input_file )
      argDict[ 'data_save_path' ] = "./data/" + test_id + "/"
  
      eval_molly = self.run_workflow( test_id, argDict, input_file, "molly", MOLLY_EVAL )

    # --------------------------------------------------------------- #
    # run 2pc_timeout_optimist_combo

    if self.COMBO_RUNS :
      test_id        = "program_complexity_2pc_timout_optimist_combo"
      test_file_name = "2pc_timeout_optimist_driver_program_complexity"

      print " >>> RUNNING " + test_id + " <<<"

      input_file                   = "./dedalus_drivers/" + test_file_name + ".ded"
      argDict                      = self.getArgDict( input_file )
      argDict[ 'data_save_path' ]  = "./data/" + test_id + "/"
      argDict[ 'EOT' ]             = 6
      argDict[ 'nodes' ]           = [ "a", "b", "C", "d" ]
      argDict[ 'neg_writes' ]      = "combo"

      eval_combo = self.run_workflow( test_id, argDict, input_file, "combo", COMBO_EVAL )

    # --------------------------------------------------------------- #
    # run 2pc_timeout_optimist_dm

    if self.DM_RUNS :
      test_id        = "program_complexity_2pc_timeout_optimist_dm"
      test_file_name = "2pc_timeout_optimist_driver_program_complexity"
  
      print " >>> RUNNING " + test_id + " <<<"
  
      input_file                  = "./dedalus_drivers/" + test_file_name + ".ded"
      argDict                     = self.getArgDict( input_file )
      argDict[ 'data_save_path' ] = "./data/" + test_id + "/"
      argDict[ 'EOT' ]            = 6
      argDict[ 'nodes' ]          = [ "a", "b", "C", "d" ]
  
      eval_dm = self.run_workflow( test_id, argDict, input_file, "dm", DM_EVAL )

    if self.MOLLY_RUNS and self.DM_RUNS and self.COMBO_RUNS and \
       MOLLY_EVAL and DM_EVAL and COMBO_EVAL :
      self.check_results_alignment( eval_molly, eval_dm, eval_combo )

    # molly and combo only
    elif self.MOLLY_RUNS and self.COMBO_RUNS and \
       MOLLY_EVAL and COMBO_EVAL :
      self.check_results_alignment( eval_molly, [], eval_combo )


  ##################
  #  2PC OPTIMIST  #
  ##################
  def test_2pc_optimist( self ) :

    MOLLY_EVAL = True
    COMBO_EVAL = True
    DM_EVAL    = False # stalls on c4 eval

    # --------------------------------------------------------------- #
    # run 2pc_optimist_molly

    if self.MOLLY_RUNS :
      test_id        = "program_complexity_2pc_optimist_molly"
      test_file_name = "2pc_optimist"
  
      print " >>> RUNNING " + test_id + " <<<"
  
      input_file                  = "./molly_progs/" + test_file_name + ".olg"
      argDict                     = self.getArgDict( input_file )
      argDict[ 'data_save_path' ] = "./data/" + test_id + "/"
  
      eval_molly = self.run_workflow( test_id, argDict, input_file, "molly", MOLLY_EVAL )

    # --------------------------------------------------------------- #
    # run 2pc_optimist_combo

    if self.COMBO_RUNS :
      test_id        = "program_complexity_2pc_optimist_combo"
      test_file_name = "2pc_optimist_driver_program_complexity"

      print " >>> RUNNING " + test_id + " <<<"

      input_file                   = "./dedalus_drivers/" + test_file_name + ".ded"
      argDict                      = self.getArgDict( input_file )
      argDict[ 'data_save_path' ]  = "./data/" + test_id + "/"
      argDict[ 'EOT' ]             = 6
      argDict[ 'nodes' ]           = [ "a", "b", "C", "d" ]
      argDict[ 'neg_writes' ]      = "combo"

      eval_combo = self.run_workflow( test_id, argDict, input_file, "combo", COMBO_EVAL )

    # --------------------------------------------------------------- #
    # run 2pc_optimist_dm

    if self.DM_RUNS :
      test_id        = "program_complexity_2pc_optimist_dm"
      test_file_name = "2pc_optimist_driver_program_complexity"
  
      print " >>> RUNNING " + test_id + " <<<"
  
      input_file                  = "./dedalus_drivers/" + test_file_name + ".ded"
      argDict                     = self.getArgDict( input_file )
      argDict[ 'data_save_path' ] = "./data/" + test_id + "/"
      argDict[ 'EOT' ]            = 6
      argDict[ 'nodes' ]          = [ "a", "b", "C", "d" ]
  
      eval_dm = self.run_workflow( test_id, argDict, input_file, "dm", DM_EVAL )

    if self.MOLLY_RUNS and self.DM_RUNS and self.COMBO_RUNS and \
       MOLLY_EVAL and DM_EVAL and COMBO_EVAL :
      self.check_results_alignment( eval_molly, eval_dm, eval_combo )

    # molly and combo only
    elif self.MOLLY_RUNS and self.COMBO_RUNS and \
       MOLLY_EVAL and COMBO_EVAL :
      self.check_results_alignment( eval_molly, [], eval_combo )

  ############
  #  2PC 63  #
  ############
  def test_2pc_63( self ) :

    MOLLY_EVAL = True
    COMBO_EVAL = True
    DM_EVAL    = False # stalls on c4 eval

    # --------------------------------------------------------------- #
    # run 2pc_63_molly

    if self.MOLLY_RUNS :
      test_id        = "program_complexity_2pc_63_molly"
      test_file_name = "2pc_63"
  
      print " >>> RUNNING " + test_id + " <<<"
  
      input_file                  = "./molly_progs/" + test_file_name + ".olg"
      argDict                     = self.getArgDict( input_file )
      argDict[ 'data_save_path' ] = "./data/" + test_id + "/"
  
      eval_molly = self.run_workflow( test_id, argDict, input_file, "molly", MOLLY_EVAL )

    # --------------------------------------------------------------- #
    # run 2pc_63_combo

    if self.COMBO_RUNS :
      test_id        = "program_complexity_2pc_63_combo"
      test_file_name = "2pc_driver_program_complexity"

      print " >>> RUNNING " + test_id + " <<<"

      input_file                   = "./dedalus_drivers/" + test_file_name + ".ded"
      argDict                      = self.getArgDict( input_file )
      argDict[ 'data_save_path' ]  = "./data/" + test_id + "/"
      argDict[ 'EOT' ]             = 6
      argDict[ 'nodes' ]           = [ "a", "b", "C", "d" ]
      argDict[ 'neg_writes' ]      = "combo"

      eval_combo = self.run_workflow( test_id, argDict, input_file, "combo", COMBO_EVAL )

    # --------------------------------------------------------------- #
    # run 2pc_63_dm

    if self.DM_RUNS :
      test_id        = "program_complexity_2pc_63_dm"
      test_file_name = "2pc_driver_program_complexity"
  
      print " >>> RUNNING " + test_id + " <<<"
  
      input_file                  = "./dedalus_drivers/" + test_file_name + ".ded"
      argDict                     = self.getArgDict( input_file )
      argDict[ 'data_save_path' ] = "./data/" + test_id + "/"
      argDict[ 'EOT' ]            = 6
      argDict[ 'nodes' ]          = [ "a", "b", "C", "d" ]
  
      eval_dm = self.run_workflow( test_id, argDict, input_file, "dm", DM_EVAL )

    if self.MOLLY_RUNS and self.DM_RUNS and self.COMBO_RUNS and \
       MOLLY_EVAL and DM_EVAL and COMBO_EVAL :
      self.check_results_alignment( eval_molly, eval_dm, eval_combo )

    # molly and combo only
    elif self.MOLLY_RUNS and self.COMBO_RUNS and \
       MOLLY_EVAL and COMBO_EVAL :
      self.check_results_alignment( eval_molly, [], eval_combo )


  ############
  #  2PC 73  #
  ############
  def test_2pc_73( self ) :

    MOLLY_EVAL = True
    DM_EVAL    = False # stalls on c4 eval
    COMBO_EVAL = True

    # --------------------------------------------------------------- #
    # run 2pc_73_molly

    if self.MOLLY_RUNS :
      test_id        = "program_complexity_2pc_73_molly"
      test_file_name = "2pc_73"
  
      print " >>> RUNNING " + test_id + " <<<"
  
      input_file                  = "./molly_progs/" + test_file_name + ".olg"
      argDict                     = self.getArgDict( input_file )
      argDict[ 'data_save_path' ] = "./data/" + test_id + "/"
  
      eval_molly = self.run_workflow( test_id, argDict, input_file, "molly", MOLLY_EVAL )

    # --------------------------------------------------------------- #
    # run 2pc_73_combo

    if self.COMBO_RUNS :
      test_id        = "program_complexity_2pc_73_combo"
      test_file_name = "2pc_driver_program_complexity"

      print " >>> RUNNING " + test_id + " <<<"

      input_file                   = "./dedalus_drivers/" + test_file_name + ".ded"
      argDict                      = self.getArgDict( input_file )
      argDict[ 'data_save_path' ]  = "./data/" + test_id + "/"
      argDict[ 'EOT' ]             = 7
      argDict[ 'nodes' ]           = [ "a", "b", "C", "d" ]
      argDict[ 'neg_writes' ]      = "combo"

      eval_combo = self.run_workflow( test_id, argDict, input_file, "combo", COMBO_EVAL )

    # --------------------------------------------------------------- #
    # run 2pc_73_dm

    if self.DM_RUNS :
      test_id        = "program_complexity_2pc_73_dm"
      test_file_name = "2pc_driver_program_complexity"
  
      print " >>> RUNNING " + test_id + " <<<"
  
      input_file                  = "./dedalus_drivers/" + test_file_name + ".ded"
      argDict                     = self.getArgDict( input_file )
      argDict[ 'data_save_path' ] = "./data/" + test_id + "/"
      argDict[ 'EOT' ]            = 7
      argDict[ 'nodes' ]          = [ "a", "b", "C", "d" ]
      argDict[ 'neg_writes' ]      = "dm"
      argDict[ 'settings' ]       = "settings_files/settings_dm.ini"
  
      eval_dm = self.run_workflow( test_id, argDict, input_file, "dm", DM_EVAL )

    if self.MOLLY_RUNS and self.DM_RUNS and self.COMBO_RUNS and \
       MOLLY_EVAL and DM_EVAL and COMBO_EVAL :
      self.check_results_alignment( eval_molly, eval_dm, eval_combo )

    # molly and combo only
    elif self.MOLLY_RUNS and self.COMBO_RUNS and \
       MOLLY_EVAL and COMBO_EVAL :
      self.check_results_alignment( eval_molly, [], eval_combo )

  ############
  #  ACK RB  #
  ############
  def test_ack_rb( self ) :

    MOLLY_EVAL = True
    COMBO_EVAL = True
    DM_EVAL    = True

    # --------------------------------------------------------------- #
    # run ack_rb_molly

    if self.MOLLY_RUNS :
      test_id        = "program_complexity_ack_rb_molly"
      test_file_name = "ack_rb"
  
      print " >>> RUNNING " + test_id + " <<<"
  
      input_file                  = "./molly_progs/" + test_file_name + ".olg"
      argDict                     = self.getArgDict( input_file )
      argDict[ 'data_save_path' ] = "./data/" + test_id + "/"
  
      eval_molly = self.run_workflow( test_id, argDict, input_file, "molly", MOLLY_EVAL )

    # --------------------------------------------------------------- #
    # run ack_rb_combo

    if self.COMBO_RUNS :
      test_id        = "program_complexity_ack_rb_combo"
      test_file_name = "ack_rb_driver"

      print " >>> RUNNING " + test_id + " <<<"

      input_file                   = "./dedalus_drivers/" + test_file_name + ".ded"
      argDict                      = self.getArgDict( input_file )
      argDict[ 'data_save_path' ]  = "./data/" + test_id + "/"
      argDict[ 'EOT' ]             = 6
      argDict[ 'nodes' ]           = [ "a", "b", "c" ]
      argDict[ 'neg_writes' ]      = "combo"

      eval_combo = self.run_workflow( test_id, argDict, input_file, "combo", COMBO_EVAL )

    # --------------------------------------------------------------- #
    # run ack_rb_dm

    if self.DM_RUNS :
      test_id        = "program_complexity_ack_rb_dm"
      test_file_name = "ack_rb_driver"
  
      print " >>> RUNNING " + test_id + " <<<"
  
      input_file                  = "./dedalus_drivers/" + test_file_name + ".ded"
      argDict                     = self.getArgDict( input_file )
      argDict[ 'data_save_path' ] = "./data/" + test_id + "/"
      argDict[ 'EOT' ]            = 6
      argDict[ 'nodes' ]          = [ "a", "b", "c" ]
      argDict[ 'neg_writes' ]      = "dm"
      argDict[ 'settings' ]       = "settings_files/settings_dm.ini"
  
      eval_dm = self.run_workflow( test_id, argDict, input_file, "dm", DM_EVAL )

    if self.MOLLY_RUNS and self.DM_RUNS and MOLLY_EVAL and DM_EVAL and COMBO_EVAL :
      self.check_results_alignment( eval_molly, eval_dm, eval_combo )

    # molly and combo only
    elif self.MOLLY_RUNS and self.COMBO_RUNS and \
       MOLLY_EVAL and COMBO_EVAL :
      self.check_results_alignment( eval_molly, [], eval_combo )

  ################
  #  CLASSIC RB  #
  ################
  def test_classic_rb( self ) :

    MOLLY_EVAL = True
    COMBO_EVAL = True
    DM_EVAL    = True

    # --------------------------------------------------------------- #
    # run classic_rb_molly

    if self.MOLLY_RUNS :
      test_id        = "program_complexity_classic_rb_molly"
      test_file_name = "classic_rb"
  
      print " >>> RUNNING " + test_id + " <<<"
  
      input_file                  = "./molly_progs/" + test_file_name + ".olg"
      argDict                     = self.getArgDict( input_file )
      argDict[ 'data_save_path' ] = "./data/" + test_id + "/"
  
      eval_molly = self.run_workflow( test_id, argDict, input_file, "molly", MOLLY_EVAL )

    # --------------------------------------------------------------- #
    # run classic_rb_combo

    if self.COMBO_RUNS :
      test_id        = "program_complexity_classic_rb_combo"
      test_file_name = "classic_rb_driver"
  
      print " >>> RUNNING " + test_id + " <<<"
  
      input_file                   = "./dedalus_drivers/" + test_file_name + ".ded"
      argDict                      = self.getArgDict( input_file )
      argDict[ 'data_save_path' ]  = "./data/" + test_id + "/"
      argDict[ 'EOT' ]             = 6
      argDict[ 'nodes' ]           = [ "a", "b", "c" ]
      argDict[ 'neg_writes' ]      = "combo"
  
      eval_combo = self.run_workflow( test_id, argDict, input_file, "combo", COMBO_EVAL )

    # --------------------------------------------------------------- #
    # run classic_rb_dm

    if self.DM_RUNS :
      test_id        = "program_complexity_classic_rb_dm"
      test_file_name = "classic_rb_driver"
  
      print " >>> RUNNING " + test_id + " <<<"
  
      input_file                  = "./dedalus_drivers/" + test_file_name + ".ded"
      argDict                     = self.getArgDict( input_file )
      argDict[ 'data_save_path' ] = "./data/" + test_id + "/"
      argDict[ 'EOT' ]            = 6
      argDict[ 'nodes' ]          = [ "a", "b", "c" ]
      argDict[ 'neg_writes' ]     = "dm"
      argDict[ 'settings' ]       = "settings_files/settings_dm.ini"
  
      eval_dm = self.run_workflow( test_id, argDict, input_file, "dm", DM_EVAL )

    if self.MOLLY_RUNS and self.DM_RUNS and MOLLY_EVAL and DM_EVAL and COMBO_EVAL :
      self.check_results_alignment( eval_molly, eval_dm, eval_combo )

  ############
  #  REPLOG  #
  ############
  def test_replog( self ) :

    MOLLY_EVAL = True
    COMBO_EVAL = True
    DM_EVAL    = True

    # --------------------------------------------------------------- #
    # run replog_molly

    if self.MOLLY_RUNS :
      test_id        = "program_complexity_replog_molly"
      test_file_name = "replog"
  
      print " >>> RUNNING " + test_id + " <<<"
  
      input_file                  = "./molly_progs/" + test_file_name + ".olg"
      argDict                     = self.getArgDict( input_file )
      argDict[ 'data_save_path' ] = "./data/" + test_id + "/"
  
      eval_molly = self.run_workflow( test_id, argDict, input_file, "molly", MOLLY_EVAL )

    # --------------------------------------------------------------- #
    # run replog_combo

    if self.COMBO_RUNS :
      test_id        = "program_complexity_replog_combo"
      test_file_name = "replog_driver"
  
      print " >>> RUNNING " + test_id + " <<<"
  
      input_file                   = "./dedalus_drivers/" + test_file_name + ".ded"
      argDict                      = self.getArgDict( input_file )
      argDict[ 'data_save_path' ]  = "./data/" + test_id + "/"
      argDict[ 'EOT' ]             = 6
      argDict[ 'nodes' ]           = [ "a", "b", "c" ]
      argDict[ 'neg_writes' ]      = "combo"
  
      eval_combo = self.run_workflow( test_id, argDict, input_file, "combo", COMBO_EVAL )

    # --------------------------------------------------------------- #
    # run replog_dm

    if self.DM_RUNS :
      test_id        = "program_complexity_replog_dm"
      test_file_name = "replog_driver"
  
      print " >>> RUNNING " + test_id + " <<<"
  
      input_file                  = "./dedalus_drivers/" + test_file_name + ".ded"
      argDict                     = self.getArgDict( input_file )
      argDict[ 'data_save_path' ] = "./data/" + test_id + "/"
      argDict[ 'EOT' ]            = 6
      argDict[ 'nodes' ]          = [ "a", "b", "c" ]
      argDict[ 'neg_writes' ]     = "dm"
      argDict[ 'settings' ]       = "settings_files/settings_dm.ini"
  
      eval_dm = self.run_workflow( test_id, argDict, input_file, "dm", DM_EVAL )

    if self.MOLLY_RUNS and self.DM_RUNS and MOLLY_EVAL and DM_EVAL and COMBO_EVAL :
      self.check_results_alignment( eval_molly, eval_dm, eval_combo )

  ###########
  #  RDLOG  #
  ###########
  def test_rdlog( self ) :

    MOLLY_EVAL = True
    COMBO_EVAL = True
    DM_EVAL    = True

    # --------------------------------------------------------------- #
    # run rdlog_molly

    if self.MOLLY_RUNS :
      test_id        = "program_complexity_rdlog_molly"
      test_file_name = "rdlog"
  
      print " >>> RUNNING " + test_id + " <<<"
  
      input_file                  = "./molly_progs/" + test_file_name + ".olg"
      argDict                     = self.getArgDict( input_file )
      argDict[ 'data_save_path' ] = "./data/" + test_id + "/"
  
      eval_molly = self.run_workflow( test_id, argDict, input_file, "molly", MOLLY_EVAL )

    # --------------------------------------------------------------- #
    # run rdlog_combo

    if self.COMBO_RUNS :
      test_id        = "program_complexity_rdlog_combo"
      test_file_name = "rdlog_driver"
  
      print " >>> RUNNING " + test_id + " <<<"
  
      input_file                   = "./dedalus_drivers/" + test_file_name + ".ded"
      argDict                      = self.getArgDict( input_file )
      argDict[ 'data_save_path' ]  = "./data/" + test_id + "/"
      argDict[ 'EOT' ]             = 6
      argDict[ 'nodes' ]           = [ "a", "b", "c" ]
      argDict[ 'neg_writes' ]      = "combo"
  
      eval_combo = self.run_workflow( test_id, argDict, input_file, "combo", COMBO_EVAL )

    # --------------------------------------------------------------- #
    # run rdlog_dm

    if self.DM_RUNS :
      test_id        = "program_complexity_rdlog_dm"
      test_file_name = "rdlog_driver"
  
      print " >>> RUNNING " + test_id + " <<<"
  
      input_file                  = "./dedalus_drivers/" + test_file_name + ".ded"
      argDict                     = self.getArgDict( input_file )
      argDict[ 'data_save_path' ] = "./data/" + test_id + "/"
      argDict[ 'EOT' ]            = 6
      argDict[ 'nodes' ]          = [ "a", "b", "c" ]
      argDict[ 'neg_writes' ]     = "dm"
      argDict[ 'settings' ]       = "settings_files/settings_dm.ini"
  
      eval_dm = self.run_workflow( test_id, argDict, input_file, "dm", DM_EVAL )

    if self.MOLLY_RUNS and self.DM_RUNS and MOLLY_EVAL and DM_EVAL and COMBO_EVAL :
      self.check_results_alignment( eval_molly, eval_dm, eval_combo )

  #############
  #  SIMPLOG  #
  #############
  def test_simplog( self ) :

    MOLLY_EVAL = True
    COMBO_EVAL = True
    DM_EVAL    = True

    # --------------------------------------------------------------- #
    # run simplog_molly

    if self.MOLLY_RUNS :
      test_id        = "program_complexity_simplog_molly"
      test_file_name = "simplog"
  
      print " >>> RUNNING " + test_id + " <<<"
  
      input_file                  = "./molly_progs/" + test_file_name + ".olg"
      argDict                     = self.getArgDict( input_file )
      argDict[ 'data_save_path' ] = "./data/" + test_id + "/"
  
      eval_molly = self.run_workflow( test_id, argDict, input_file, "molly", MOLLY_EVAL )

    # --------------------------------------------------------------- #
    # run simplog_combo

    if self.COMBO_RUNS :
      test_id        = "program_complexity_simplog_combo"
      test_file_name = "simplog_driver"
  
      print " >>> RUNNING " + test_id + " <<<"
  
      input_file                  = "./dedalus_drivers/" + test_file_name + ".ded"
      argDict                     = self.getArgDict( input_file )
      argDict[ 'data_save_path' ] = "./data/" + test_id + "/"
      argDict[ 'EOT' ]            = 6
      argDict[ 'nodes' ]          = [ "a", "b", "c" ]
      argDict[ 'neg_writes' ]     = "combo"
  
      eval_combo = self.run_workflow( test_id, argDict, input_file, "combo", COMBO_EVAL )

    # --------------------------------------------------------------- #
    # run simplog_dm

    if self.DM_RUNS :
      test_id        = "program_complexity_simplog_dm"
      test_file_name = "simplog_driver"
  
      print " >>> RUNNING " + test_id + " <<<"
  
      input_file                  = "./dedalus_drivers/" + test_file_name + ".ded"
      argDict                     = self.getArgDict( input_file )
      argDict[ 'data_save_path' ] = "./data/" + test_id + "/"
      argDict[ 'EOT' ]            = 6
      argDict[ 'nodes' ]          = [ "a", "b", "c" ]
      argDict[ 'neg_writes' ]     = "dm"
      argDict[ 'settings' ]       = "settings_files/settings_program_complexity.ini"
  
      eval_dm = self.run_workflow( test_id, argDict, input_file, "dm", DM_EVAL )

    if self.MOLLY_RUNS and self.DM_RUNS and MOLLY_EVAL and DM_EVAL and COMBO_EVAL :
      self.check_results_alignment( eval_molly, eval_dm, eval_combo )


  #############################
  #  CHECK RESULTS ALIGNMENT  #
  #############################
  def check_results_alignment( self, eval_molly, eval_dm, eval_combo ) :

#    print
#    print "MOLLY:"
#    for i in eval_molly[ "post" ] :
#      print i
#    print
#    print "DM:"
#    for i in eval_dm[ "post" ] :
#      print i
#    print
#    print "COMBO:"
#    for i in eval_combo[ "post" ] :
#      print i
#    #sys.exit( "blah" )

    print
    print "<><><><><><><><><><><><><><><><><><>"
    print "<>   CHECKING TUPLE ALIGNMENTS    <>"

    if len( eval_molly ) < 1 :
      print "skipping eval comparison b/c no molly results."
      return

    if len( eval_dm ) > 0 :
      # check dm
      logging.debug( "ooooooooooooooooooooooooooooooooooooooooooooooo" )
      logging.debug( "  checking results for dm v. molly:" )
      for rel in eval_molly :
        if "_prov" in rel :
          continue
        else :
  
          # check for extra molly tups
          extra_molly_tups = []
          for molly_tup in eval_molly[ rel ] :
            if not molly_tup in eval_dm[ rel ] :
              extra_molly_tups.append( molly_tup )
  
          # check for extra dm tups
          extra_dm_tups = []
          for dm_tup in eval_dm[ rel ] :
            if not dm_tup in eval_molly[ rel ] :
              extra_dm_tups.append( dm_tup )
  
          if len( extra_molly_tups ) > 0 or len( extra_dm_tups ) > 0 :
            print ">>>> alignment inconsistencies for relation '" + rel + "' :"
  
          if len( extra_molly_tups ) > 0 :
            print "> tuples found in molly and not in dm for relation '" + rel.upper() + " :"
            for tup in extra_molly_tups :
              print ",".join( tup )
          if len( extra_dm_tups ) > 0 :
            print "> tuples found in dm and not in molly for relation '" + rel.upper() + " :"
            for tup in extra_dm_tups :
              print ",".join( tup )
          if len( extra_molly_tups ) > 0 or len( extra_dm_tups ) > 0 :
            print "<<<<"
    else :
      print "skipping dm comparison b/c no eval results..."

    if len( eval_combo ) > 0 :
      # combo check
      logging.debug( "ooooooooooooooooooooooooooooooooooooooooooooooo" )
      logging.debug( "  checking results for combo v. molly:" )
      for rel in eval_molly :
        if "_prov" in rel :
          continue
        else :
  
          # check for extra molly tups
          extra_molly_tups = []
          for molly_tup in eval_molly[ rel ] :
            if not molly_tup in eval_combo[ rel ] :
              extra_molly_tups.append( molly_tup )
  
          # check for extra combo tups
          extra_combo_tups = []
          for combo_tup in eval_combo[ rel ] :
            if not combo_tup in eval_molly[ rel ] :
              extra_combo_tups.append( combo_tup )
  
          if len( extra_molly_tups ) > 0 or len( extra_combo_tups ) > 0 :
            print ">>>> alignment inconsistencies for relation '" + rel + "' :"
  
          if len( extra_molly_tups ) > 0 :
            print "> tuples found in molly and not in combo for relation '" + rel.upper() + " :"
            for tup in extra_molly_tups :
              print ",".join( tup )
          if len( extra_combo_tups ) > 0 :
            print "> tuples found in combo and not in molly for relation '" + rel.upper() + " :"
            for tup in extra_combo_tups :
              print ",".join( tup )
          if len( extra_molly_tups ) > 0 or len( extra_combo_tups ) > 0 :
            print "<<<<"
    else :
      print "skipping combo comparison b/c no eval results..."
  
      print
      print "<><><><><><><><><><><><><><><><><><>"


  ##################
  #  RUN WORKFLOW  #
  ##################
  # generate program (if applicable), run dm program, collect results, analyze results.
  def run_workflow( self, test_id, argDict, input_file, eval_type, RUN_EVAL=True ) :

    # --------------------------------------------------------------- #

    # check if dedalus
    if input_file.endswith( ".ded" ) :
      IS_DED = True
    elif input_file.endswith( ".olg" ) :
      IS_DED = False
    else :
      raise Exception( "INVALID FILE TYPE : make sure the input file is either .ded or .olg" )

    # --------------------------------------------------------------- #

    # make sure data dir exists
    if not os.path.exists( argDict[ "data_save_path" ] ) :
      self.make_data_dir( argDict[ "data_save_path" ], test_id )

    # --------------------------------------------------------------- #

    if not IS_DED :

      # extract program string
      program    = self.extract_program_array( input_file )
      table_list = self.extract_table_list( program )

      program_data = [ program, table_list ]

      # run program with c4 wrapper
      if RUN_EVAL :
        eval_results_dict = self.run_program_c4( program_data, argDict )
      else :
        eval_results_dict = []

    # --------------------------------------------------------------- #

    else :
  
      # --------------------------------------------------------------- #
      # set up IR data
  
      test_db = argDict[ "data_save_path" ] + "/IR_" + test_id + ".db"
  
      if os.path.exists( test_db ) :
        os.remove( test_db )
  
      IRDB   = sqlite3.connect( test_db )
      cursor = IRDB.cursor()
  
      dedt.createDedalusIRTables(cursor)
      dedt.globalCounterReset()

      # --------------------------------------------------------------- #

      # run translator
      # grab only the program lines and table list.
      program_data = dedt.translateDedalus( argDict, cursor )[0]
  
      # run program in c4
      if RUN_EVAL :
        eval_results_dict = self.run_program_c4( program_data, argDict )
      else :
        eval_results_dict = []

    # --------------------------------------------------------------- #

    # run analysis
    analysis_results_dict = self.run_analysis( program_data, eval_results_dict, IS_DED )

    print
    print "======================================"
    print "========== ANALYSIS RESULTS for " + eval_type + " ==========" 
    print
    for res in analysis_results_dict :
      print res + " => " + str( analysis_results_dict[ res ] )
    print
    print "======================================"
    print

    # --------------------------------------------------------------- #

    # save analysis data to file
    self.save_analysis_data_to_file( analysis_results_dict, test_id, argDict )

    return eval_results_dict


  ################################
  #  SAVE ANALYSIS DATA TO FILE  #
  ################################
  def save_analysis_data_to_file( self, analysis_results_dict, test_id, argDict ) :

    save_file_name = argDict[ "data_save_path" ] + \
                     "/" + test_id + "_analysis_results.txt"

    fo = open( save_file_name, "w" )
    for metric in analysis_results_dict :
      fo.write( metric + "=>" + str( analysis_results_dict[ metric ] ) + "\n" )
    fo.close()


  ##################
  #  RUN ANALYSIS  #
  ##################
  def run_analysis( self, program_data, eval_results_dict, IS_DED ) :

    # --------------------------------------------------------------- #
    # gather data about the programs

    analysis_results_dict = {}
    program_lines         = program_data[0]
    program_tables        = program_data[1]

    analysis_results_dict[ "num_lines_total" ]    = len( program_lines )
    analysis_results_dict[ "num_tables_total" ]   = len( program_tables )
    analysis_results_dict[ "num_idb_rules" ]      = len( [ x for x in program_lines \
                                                             if ":-" in x ] )
    analysis_results_dict[ "num_edb_statements" ] = len( [ x for x in program_lines \
                                                     if not x.startswith( "define(") and \
                                                        not ":-" in x ] )

    subgoal_data = pat.get_subgoal_per_rule_data( program_lines )
    analysis_results_dict[ "avg_num_subgoals_per_rule" ] = subgoal_data[0]
    analysis_results_dict[ "max_num_subgoals_per_rule" ] = subgoal_data[1]
    analysis_results_dict[ "min_num_subgoals_per_rule" ] = subgoal_data[2]

    if len( eval_results_dict ) > 0 :
      assert( len( program_data[1] ) == len( eval_results_dict ) )

    # --------------------------------------------------------------- #
    # gather dm-specific data
    # observe all ded programs run through this process are programs
    # generated via dm or combo.

    if IS_DED :

      analysis_results_dict[ "num_dom_rules" ]     = pat.get_num_rules( program_lines, "dom_" )
      analysis_results_dict[ "num_domcomp_rules" ] = pat.get_num_rules( program_lines, "domcomp_" )
      analysis_results_dict[ "num_dom_rules" ]     = pat.get_num_rules( program_lines, "dom_" )
      analysis_results_dict[ "num_adom_rules" ]    = pat.get_num_rules( program_lines, "adom_" )

    # --------------------------------------------------------------- #
    # gather data about the evaluation results

    if len( eval_results_dict ) > 0 :
      eval_meta_data = pat.get_eval_meta_data( eval_results_dict )
      analysis_results_dict[ "eval_tups_total" ]              = eval_meta_data[0]
      analysis_results_dict[ "eval_tups_total_per_relation" ] = eval_meta_data[1]

    return analysis_results_dict


  ####################
  #  RUN PROGRAM C4  #
  ####################
  # return evaluation results dictionary.
  def run_program_c4( self, program_data, argDict ) :

    # run c4 evaluation
    results_array = c4_evaluator.runC4_wrapper( program_data, argDict )
    parsedResults = tools.getEvalResults_dict_c4( results_array )

    return parsedResults


  ########################
  #  EXTRACT TABLE LIST  #
  ########################
  def extract_table_list( self, program_array ) :
    table_list = []
    for line in program_array :
      if not line.startswith( "define(" ) :
        break
      else :
        line        = line.replace( "define(", "" )
        comma_index = line.find( "," )
        table_name  = line[ : comma_index ]
        table_list.append( table_name )
    return table_list


  ###########################
  #  EXTRACT PROGRAM ARRAY  #
  ###########################
  def extract_program_array( self, input_olg_file ) :

    if os.path.exists( input_olg_file ) :
      program_array = []
      fo = open( input_olg_file )
      for line in fo :
        program_array.append( line.rstrip() )
      fo.close()
      return program_array

    else :
      raise Exception( "FILE NOT FOUND : " + input_olg_file )


  ###################
  #  MAKE DATA DIR  #
  ###################
  def make_data_dir( self, data_save_path, test_id ) :
    logging.debug( "  TEST " + test_id.upper() + \
                   " : data save path not found : " + \
                   data_save_path )

    dir_list = data_save_path.split( "/" )
    complete_str = "./"
    for this_dir in dir_list :
      if this_dir == "./" :
        complete_str += this_dir
      else :
        complete_str += this_dir + "/"
        if not os.path.exists( complete_str ) :
          cmd = "mkdir " + complete_str
          logging.debug( "  TEST " + test_id.upper() + " : running cmd = " + cmd )
          os.system( cmd )


  ##################
  #  GET ARG DICT  #
  ##################
  def getArgDict( self, inputfile ) :
    argDict = {}
    argDict[ 'file' ]       = inputfile
    argDict[ 'evaluator' ]  = "c4"
    argDict[ 'neg_writes' ] = ""

    # this settings file is fine for running both the dm and molly progs
    # b/c c4 only needs the C4_HOME_PATH option.
    argDict[ 'settings' ] = "./settings_files/settings_program_complexity.ini"

    return argDict


##############################
#  MAIN THREAD OF EXECUTION  #
##############################
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
