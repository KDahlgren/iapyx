#!/usr/bin/env python

'''
iapyx.py
'''

# **************************************** #


#############
#  IMPORTS  #
#############
# standard python packages
import logging, inspect, os, sqlite3, sys, time

# ------------------------------------------------------ #
# import sibling packages HERE!!!

import Core

if not os.path.abspath( __file__ + "/../.." ) in sys.path :
  sys.path.append( os.path.abspath( __file__ + "/../.." ) )

from utils import parseCommandLineInput, tools

# **************************************** #


#############
#  GLOBALS  #
#############
C4_DUMP_SAVEPATH  = os.path.abspath( __file__ + "/../../.." ) + "/save_data/c4Output/c4dump.txt"
TABLE_LIST_PATH   = os.path.abspath( __file__ + "/../.."    ) + "/evaluators/programFiles/" + "tableListStr.data"

# remove files from previous runs or else suffer massive file collections.
os.system( "rm " + os.path.abspath( __file__ + "/../../.." ) + "/save_data/graphOutput/*.png" )

###################
#  IAPYX  DRIVER  #
###################
def iapyx_driver( argDict ) :

  logging.debug( "  IAPYX DRIVER : running process..." )

  os.system( "rm IR.db" ) # delete db from previous run, if appicable

  # instantiate IR database
  saveDB = os.getcwd() + "/IR.db"
  IRDB   = sqlite3.connect( saveDB ) # database for storing IR, stored in running script dir
  cursor = IRDB.cursor()

  # initialize core
  c = Core.Core( argDict, cursor )

  # run iapyx on given spec (in file provided in argDict)
  c.run_workflow()
  program_array = c.program_array
  table_array   = c.table_array

  os.system( "rm IR.db" ) # delete db from previous run, if appicable

  logging.info( "PROGRAM ENDED SUCESSFULLY." )

  return [ program_array, table_array ]


###########
#  IAPYX  #
###########
def iapyx() :

  logging.basicConfig( format='%(levelname)s:%(message)s', level=logging.DEBUG )

  # get dictionary of commandline arguments.
  # exits here if user provides invalid inputs.
  argDict = parseCommandLineInput.parseCommandLineInput( )  # get dictionary of arguments.

  data = iapyx_driver( argDict )

  # output program to file for sanity check
  program_array = data[0]
  tables_array  = data[1]
  fo = open( "iapyx_prog_from_driver.olg", "w")
  for line in program_array :
    fo.write( line + "\n" )
  fo.close()


#########################
#  THREAD OF EXECUTION  #
#########################
if __name__ == '__main__' :
  iapyx()


#########
#  EOF  #
#########
