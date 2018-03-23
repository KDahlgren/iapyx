#!/usr/bin/env python

'''
Core.py
'''

# **************************************** #


#############
#  IMPORTS  #
#############
# standard python packages
import ast, inspect, itertools, logging, os, sqlite3, string, sys, time

# ------------------------------------------------------ #
# import sibling packages HERE!!!
if not os.path.abspath( __file__ + "/../.." ) in sys.path :
  sys.path.append( os.path.abspath( __file__ + "/../.." ) )

from dedt           import dedt, dedalusParser
from utils          import parseCommandLineInput, tools
from evaluators     import c4_evaluator

# **************************************** #


################
#  CLASS CORE  #
################
class Core :


  #################
  #  CONSTRUCTOR  #
  #################
  def __init__( self, argDict, cursor ) :
    self.argDict       = argDict  # dictionary of commaned line args
    self.cursor        = cursor   # a reference to the IR database
    self.program_array = None     # the translated datalog program as an array of program lines
    self.table_array   = None     # the array of tables in the program
    self.factMeta      = None     # the array of fact objects in the IR database
    self.ruleMeta      = None     # the array of rule objects in the IR database


  ##################
  #  RUN WORKFLOW  #
  ##################
  def run_workflow( self ) :

    logging.info( "*******************************************************" )
    logging.info( "                   RUNNING IAPYX CORE" )
    logging.info( "*******************************************************" )
    logging.info( "" )

    # ---------------------------------------------------------------- #
    # 1. build c4 datalog program                                      #
    # ---------------------------------------------------------------- #

    # allProgramData := [ allProgramLines, tableListArray ]
    allProgramData, self.factMeta, self.ruleMeta = self.dedalus_to_datalog( self.argDict, self.cursor )
    self.program_array                           = allProgramData[0]
    self.table_array                             = allProgramData[1]

    # ----------------------------------------------- #
    # 2. evaluate                                     #
    # ----------------------------------------------- #

    # use c4 wrapper 
    parsedResults = self.evaluate( self.argDict, allProgramData )


  ########################
  #  DEDALUS TO DATALOG  #
  ########################
  # translate all input dedalus files into a single datalog program
  def dedalus_to_datalog( self, argDict, cursor ) :
    return dedt.translateDedalus( argDict, cursor )
  
  
  ##############
  #  EVALUATE  #
  ##############
  # evaluate the datalog program using some datalog evaluator
  # return some data structure or storage location encompassing the evaluation results.
  def evaluate( self, argDict, allProgramData ) :

    # inject custom faults here.
    allProgramData = injectCustomFaults( argDict, allProgramData )

    results_array = c4_evaluator.runC4_wrapper( allProgramData, argDict )

    # ----------------------------------------------------------------- #
    # dump evaluation results locally
    eval_results_dump_dir = os.path.abspath( os.getcwd() ) + "/data/"

    # make sure data dump directory exists
    if not os.path.isdir( eval_results_dump_dir ) :
      print "WARNING : evalulation results file dump destination does not exist at " + eval_results_dump_dir
      print "> creating data directory at : " + eval_results_dump_dir
      os.system( "mkdir " + eval_results_dump_dir )
      if not os.path.isdir( eval_results_dump_dir ) :
        tools.bp( __name__, inspect.stack()[0][3], "FATAL ERROR : unable to create evaluation results dump directory at " + eval_results_dump_dir )
      print "...done."

    # data dump directory exists
    self.eval_results_dump_to_file( results_array, eval_results_dump_dir )

    # ----------------------------------------------------------------- #
    # parse results into a dictionary
    parsedResults = tools.getEvalResults_dict_c4( results_array )

    # ----------------------------------------------------------------- #

    return parsedResults

 
  ###############################
  #  EVAL RESULTS DUMP TO FILE  #
  ###############################
  def eval_results_dump_to_file( self, results_array, eval_results_dump_dir ) :

    eval_results_dump_file_path = eval_results_dump_dir + "eval_dump_0.txt"

    # save new contents
    f = open( eval_results_dump_file_path, "w" )

    for line in results_array :
      
      # output to stdout
      logging.debug( " EVAL RESULTS DUMP TO FILE : " + line )

      # output to file
      f.write( line + "\n" )

    f.close()
 

##########################
#  INJECT CUSTOM FAULTS  #
##########################
# example :
#   [CORE]
#   CUSTOM_FAULT = ['clock("str","str",2,2)']
# use double quotes for str data in clock tuples and single quotes around clock facts.

def injectCustomFaults( argDict, allProgramData ) :

  # grab the custom fault, which is a list of clock fact strings, with quotes,
  # to remove from full clock relation
  customFaultList = tools.getConfig( argDict[ "settings" ], "CORE", "CUSTOM_FAULT", list )

  if customFaultList :
    # delete specified clock facts from program
    faultyProgramLines = []
    programLines       = allProgramData[0][0]
    tableList          = allProgramData[0][1]
    for line in programLines :
      line = line.replace( ";", "" )
      if line in customFaultList :
        pass
      else :
        faultyProgramLines.append( line + ";" )

    return [ faultyProgramLines, tableList ]

  else :
    return allProgramData
 
#########
#  EOF  #
#########
