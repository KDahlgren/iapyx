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
  # 1. build c4 datalog program                                      #
  # ---------------------------------------------------------------- #

  allProgramData = dedalus_to_datalog( starterFile, cursor )

  print allProgramData

  # ----------------------------------------------- #
  # 2. evaluate                                     #
  # ----------------------------------------------- #

  # use c4 wrapper 
  #parsedResults = evaluate( allProgramData )


########################
#  DEDALUS TO DATALOG  #
########################
# translate all input dedalus files into a single datalog program
def dedalus_to_datalog( starterFile, cursor ) :

  logging.debug( "  : running process..." )

  # ----------------------------------------------------------------- #
  # create tables
  dedt.createDedalusIRTables( cursor )
  logging.debug( "  TRANSLATE DEDALUS : created IR tables" )

  # ----------------------------------------------------------------- #
  # get all input files

  fileList    = tools.get_all_include_file_paths( starterFile )

  logging.debug( "  TRANSLATE DEDALUS : fileList = " + str( fileList ) )

  allProgramData = []

  # TO DO : concat all lines into a single file, then translate
  for fileName in fileList :
    logging.debug( "  RUN TRANSLATOR : running process..." )
    logging.warning( "  RUN TRANSLATOR : WARNING : need to fix file includes to run translator once. need to know all program lines to derive data types for program." )
  
    # ----------------------------------------------------------------- #
    #                            PARSE
    # ----------------------------------------------------------------- #

    meta     = dedt.dedToIR( fileName, cursor )
    factMeta = meta[0]
    ruleMeta = meta[1]
  
    logging.debug( "  RUN TRANSLATOR : len( ruleMeta ) = " + str( len( ruleMeta ) ) )
  
    # ------------------------------------------------------------- #
    # generate the first clock
  
#    logging.debug( "  RUN TRANSLATOR : building starter clock..." )
#  
#    dedt.starterClock( cursor, argDict )
#  
#    logging.debug( "  RUN TRANSLATOR : ...done building starter clock." )
  
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
#    # wilcard rewrites
#  
#  #  logging.debug( "  REWRITE : calling wildcard rewrites..." )
#  #
#  #  try :
#  #    rewriteWildcards = tools.getConfig( "DEFAULT", "REWRITE_WILDCARDS", bool )
#  #    if rewriteWildcards :
#  #      rewriteNegativeSubgoalsWithWildcards.rewriteNegativeSubgoalsWithWildcards( cursor )
#  #
#  #  except ConfigParser.NoOptionError :
#  #    print "WARNING : no 'REWRITE_WILDCARDS' defined in 'DEFAULT' section of settings.ini ...running without wildcard rewrites."
#  #    pass
#  
#    # ----------------------------------------------------------------------------- #
#    # negative rewrites
#  
#  #  logging.debug( "  REWRITE : calling negative rewrites..." )
#  #
#  #  NEGPROV = tools.getConfig( "DEFAULT", "NEGPROV", bool )
#  #  if NEGPROV :
#  #    newDMRuleMeta = negativeWrites.negativeWrites( EOT, original_prog, cursor )
#  #    ruleMeta.extend( newDMRuleMeta )
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
  
    logging.debug( "  RUN TRANSLATOR : launching c4 evaluation..." )
  
    allProgramData.extend( c4_translator.c4datalog( cursor ) )
  
    logging.debug( "  RUN TRANSLATOR : ...done with c4 evaluation." )
  
    # ------------------------------------------------------------- #
  
  return allProgramData


##############
#  EVALUATE  #
##############
# evaluate the datalog program using some datalog evaluator
# return some data structure or storage location encompassing the evaluation results.
def evaluate( self, allProgramData ) :

  # make table list here?
  sys.exit( "need table list" )
  results_array = c4_evaluator.runC4_wrapper( allProgramData )

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
    if DEBUG :
      print line

    # output to file
    f.write( line + "\n" )

  f.close()
 

run_workflow()

#########
#  EOF  #
#########
