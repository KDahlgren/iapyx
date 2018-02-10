#!/usr/bin/env python

# **************************************** #

# experiment_driver.py

import logging, os, sys
import demos, original_tests, dm_tests, combo_tests, sc_tests

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

PRINT_STOP = False

DEMOS          = True
ORIGINAL_TESTS = False
DM_TESTS       = False
COMBO_TESTS    = False
SC_TESTS       = False

#######################
#  EXPERIMENT DRIVER  #
#######################
def experiment_driver( molly_path ) :

  logging.basicConfig( format='%(levelname)s:%(message)s', level=logging.DEBUG )

  table_path    = os.getcwd() + "/tmp_data/iapyx_tables.data" # filename hard-coded in molly
  type_path     = os.getcwd() + "/tmp_data/iapyx_types.data"  # filename hard-coded in molly

  # ------------------- #
  #        DEMOS        #
  # ------------------- #

  if DEMOS :

    demos.demo_0( PRINT_STOP, molly_path, table_path, type_path )
    #demos.dm_demo_1( PRINT_STOP, molly_path, table_path, type_path )

  # ---------------------------- #
  #        ORIGINAL TESTS        #
  # ---------------------------- #

  if ORIGINAL_TESTS :

    original_tests.original_simplog( PRINT_STOP, molly_path, table_path, type_path )
    #original_tests.original_rdlog( molly_path, table_path, type_path ) # need to implement crash table!
    #original_tests.original_replog( molly_path, table_path, type_path )

  # ---------------------- #
  #        DM TESTS        #
  # ---------------------- #

  if DM_TESTS :

    dm_tests.dm_simplog( PRINT_STOP, molly_path, table_path, type_path )
    #dm_tests.dm_rdlog()
    #dm_tests.dm_replog()

  # ------------------------- #
  #        COMBO TESTS        #
  # ------------------------- #

  if COMBO_TESTS :

    combo_tests.combo_simplog()
    combo_tests.combo_rdlog()
    combo_tests.combo_replog()

  # ---------------------- #
  #        SC TESTS        #
  # ---------------------- #

  if SC_TESTS :

    sc_tests.sc_simplog()
    sc_tests.sc_rdlog()
    sc_tests.sc_replog()


#########################
#  THREAD OF EXECUTION  #
#########################
if __name__ == '__main__' :

  logging.basicConfig( format='%(levelname)s:%(message)s', level=logging.DEBUG )

  # ---------------------- #
  # pass path to molly at command line
  # ( replace this after making the hacked molly branch a dependency )
  molly_path = sys.argv[1]
  
  experiment_driver( molly_path )


#########
#  EOF  #
#########
