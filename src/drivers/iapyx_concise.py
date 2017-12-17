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

if not os.path.abspath( __file__ + "/../translators" ) in sys.path :
  sys.path.append( os.path.abspath( __file__ + "/../translators" ) )

from dedt           import dedt, dedalusParser
from translators    import c4_translator, dumpers_c4
from utils          import parseCommandLineInput, tools
from evaluators     import c4_evaluator

# **************************************** #


DEBUG = True


##################
#  RUN WORKFLOW  #
##################
def run_workflow( ) :

  if DEBUG :
   print "*******************************************************"
   print "                   RUNNING IAPYX CORE"
   print "*******************************************************"
   print


  # --------------------------------------------------------------- #
  # db setup
  db          = "./IR.db"
  IRDB        = sqlite3.connect( db )
  cursor      = IRDB.cursor()
  starterFile = sys.argv[1]

  # ---------------------------------------------------------------- #

  # allProgramData := [ allProgramLines, table_list ]
  allProgramData = dedalus_to_datalog( starterFile, cursor )

  # output c4 program to stdout
  for line in allProgramData[0] :
    print line


########################
#  DEDALUS TO DATALOG  #
########################
# translate all input dedalus files into a single datalog program
def dedalus_to_datalog( starterFile, cursor ) :

  logging.debug( "  DEDALUS TO DATALOG : running process..." )

  argDict               = {} 
  argDict[ "settings" ] = "./settings.ini" 
  argDict[ "EOT" ]      = 4
  argDict[ "nodes" ]    = ["a","b","c","d"]

  # ----------------------------------------------------------------- #
  # create tables
  dedt.createDedalusIRTables( cursor )
  logging.debug( "  DEDALUS TO DATALOG : created IR tables" )

  # ----------------------------------------------------------------- #
  # get all input files

  fileList    = tools.get_all_include_file_paths( starterFile )

  logging.debug( "  DEDALUS TO DATALOG : fileList = " + str( fileList ) )

  allProgramData = []

  # TO DO : concat all lines into a single file, then translate
  for fileName in fileList :
    logging.debug( "  DEDALUS TO DATALOG : running process..." )
    #logging.warning( "  RUN TRANSLATOR : WARNING : need to fix file includes to run translator once. need to know all program lines to derive data types for program." )
  
    # ----------------------------------------------------------------- #
    #                            PARSE
    # ----------------------------------------------------------------- #

    meta     = dedt.dedToIR( fileName, cursor )
    factMeta = meta[0]
    ruleMeta = meta[1]
  
    logging.debug( "  DEDALUS TO DATALOG: len( ruleMeta ) = " + str( len( ruleMeta ) ) )
  
    # ------------------------------------------------------------- #
    # generate the first clock
  
    logging.debug( "  RUN TRANSLATOR : building starter clock..." )
  
    dedt.starterClock( cursor, argDict )
  
    logging.debug( "  RUN TRANSLATOR : ...done building starter clock." )
  
    # ----------------------------------------------------------------- #
    #                            REWRITE
    # ----------------------------------------------------------------- #
  
    # ----------------------------------------------------------------------------- #
    # dedalus rewrite
  
#    logging.debug( "  REWRITE : calling dedalus rewrites..." )
#  
#    allMeta  = dedalusRewriter.rewriteDedalus( factMeta, ruleMeta, cursor )
#    factMeta = allMeta[0]
#    ruleMeta = allMeta[1]
#  
#    # be sure to fill in all the type info for the new rule definitions
#    setTypes( cursor )
#  
#    # ----------------------------------------------------------------------------- #
#    # provenance rewrites
#  
#    logging.debug( "  REWRITE : calling provenance rewrites..." )
#  
#    # add the provenance rules to the existing rule set
#    ruleMeta.extend( provenanceRewriter.rewriteProvenance( ruleMeta, cursor ) )
#  
#    # be sure to fill in all the type info for the new rule definitions
#    setTypes( cursor )
#  
#    # ----------------------------------------------------------------------------- #
#  
#    logging.debug( "  REWRITE : ...done." ) 
  
    # ------------------------------------------------------------- #
    # translate IR into datalog
  
    logging.debug( "  DEDALUS TO DATALOG : launching c4 translation ..." )

    allProgramData.extend( c4_translator.c4datalog( argDict, cursor ) )
  
    logging.debug( "  DEDALUS TO DATALOG : ...done with c4 translation." )
  
    # ------------------------------------------------------------- #
  
  return allProgramData


#########################
#  THREAD OF EXECUTION  #
#########################
run_workflow()


#########
#  EOF  #
#########
