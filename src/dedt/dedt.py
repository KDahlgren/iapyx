#!/usr/bin/env python

'''
dedt.py
   Define the functionality for converting parsed Dedalus into 
   SQL relations (the intermediate representation).
'''

'''
IR SCHEMA:

  Fact         ( fid text, name text,     timeArg text                                                )
  FactData     ( fid text, attID int,     attName text,     attType text                              )
  Rule         ( rid text, goalName text, goalTimeArg text, rewritten text                            )
  GoalAtt      ( rid text, attID int,     attName text,     attType text                              )
  Subgoals     ( rid text, sid text,      subgoalName text, subgoalPolarity text, subgoalTimeArg text )
  SubgoalAtt   ( rid text, sid text,      attID int,        attName text,         attType text        )
  Equation     ( rid text, eid text,      eqn text                                                    )
  EquationVars ( rid text, eid text,      varID int,        var text                                  )
  Clock        ( src text, dest text,     sndTime int,      delivTime int,        simInclude text     )

'''

import inspect, logging, os, string, sqlite3, sys

# ------------------------------------------------------ #
# import sibling packages HERE!!!
if not os.path.abspath( __file__ + "/../.." ) in sys.path :
  sys.path.append( os.path.abspath( __file__ + "/../.." ) )
if not os.path.abspath( __file__ + "/../translators" ) in sys.path :
  sys.path.append( os.path.abspath( __file__ + "/../translators" ) )
if not os.path.abspath( __file__ + "/../../negativeWrites" ) in sys.path :
  sys.path.append( os.path.abspath( __file__ + "/../../negativeWrites" ) )

from utils          import dumpers, extractors, tools, parseCommandLineInput
from translators    import c4_translator, dumpers_c4
#from negativeWrites import negativeWrites, evaluate

import negativeWrites, rewriteNegativeSubgoalsWithWildcards

import clockRelation
import dedalusParser
import dedalusRewriter
import provenanceRewriter
import Fact, Rule
import ConfigParser

# ------------------------------------------------------ #


#############
#  GLOBALS  #
#############
DEDT_DEBUG  = tools.getConfig( "DEDT", "DEDT_DEBUG", bool )
DEDT_DEBUG1 = tools.getConfig( "DEDT", "DEDT_DEBUG1", bool )


###############
#  DED TO IR  #
###############
# input raw ded file
# store intermediate representation in SQL database
# output nothing
def dedToIR( filename, cursor ) :

  parsedLines = []
  parsedLines = dedalusParser.parseDedalus( filename ) # program exits here if file cannot be opened.

  logging.debug( "  DED TO IR : parsedLines = " + str( parsedLines ) )

  # collect fact and rule metadata for future dumping.
  # these are lists of object pointers.
  factMeta = []
  ruleMeta = []

  # ----------------------------------------------- #
  #                     FACTS                       #
  # ----------------------------------------------- #
  # process facts first to establish 
  # all fact data types.

  # iterate over parsed lines
  for line in parsedLines :

    if line[0] == "fact" :

      logging.debug( ">> PROCESSING FACT : " + str( line ) )

      # get data for fact
      factData = line[1]

      # generate random ID for fact
      fid = tools.getID()

      # save fact data in persistent DB using IR
      newFact = Fact.Fact( fid, factData, cursor )

      # save fact metadata (aka object)
      factMeta.append( newFact )

  # ----------------------------------------------- #
  #                     RULES                       #
  # ----------------------------------------------- #
  # process rules after consuming all facts

  # iterate over parsed lines
  for line in parsedLines :

    if line[0] == "rule" : # save rules

      logging.debug( ">> PROCESSING RULE : " + str( line ) )

      # get data for rule
      ruleData = line[1]

      # generate a random ID for the rule
      rid = tools.getID()

      # save rule goal info
      newRule = Rule.Rule( rid, ruleData, cursor )

  # ------------------------------------------- #
  #                 DERIVE TYPES                #
  # ------------------------------------------- #
  # all rules now exist in the IR database.
  # fire the logic for deriving data types for all
  # goals and subgoals per rule.

  setTypes( cursor )

  return [ factMeta, ruleMeta ]


###############
#  SET TYPES  #
###############
# update the IR database to assign data types
# to all goal and subgoal attrbutes in all rules.
def setTypes( cursor ) :

  # ---------------------------------------------------- #
  # PASS 1 : populate data types for edb subgoals

  # grab all rule ids

  # grab all subgoal ids per rule

  # if subgoal is edb, grab the types

  # ---------------------------------------------------- #
  # PASS 2 : populate data types for idb subgoals 
  #          (and a subset of idb goals in the process)

  #
  return None


###################
#  STARTER CLOCK  #
###################
# input cursor and cmdline args, assume IR successful
# create the initial clock relation in SQL database
# output nothing
def starterClock( cursor, argDict ) :
  clockRelation.initClockRelation( cursor, argDict )


########################
#  REWRITE TO DATALOG  #
########################
# input cursor, assume IR successful
# output nothing
def rewrite( EOT, ruleMeta, cursor ) :

  logging.debug( "  REWRITE : running process..." )

  #sys.exit( "hit rewrite" )

  # ----------------------------------------------------------------------------- #
  # dedalus rewrite
  # extract all info from dedalus rules into IR database

  dedalusRewriter.rewriteDedalus( cursor )

  # ----------------------------------------------------------------------------- #
  # rewrite negated subgoals with wildcards

  try :
    rewriteWildcards = tools.getConfig( "DEFAULT", "REWRITE_WILDCARDS", bool )
    if rewriteWildcards :
      rewriteNegativeSubgoalsWithWildcards.rewriteNegativeSubgoalsWithWildcards( cursor )

  except ConfigParser.NoOptionError :
    print "WARNING : no 'REWRITE_WILDCARDS' defined in 'DEFAULT' section of settings.ini ...running without wildcard rewrites."
    pass

  original_prog = c4_translator.c4datalog( cursor ) # assumes c4 evaluator

  # ----------------------------------------------------------------------------- #
  # negative writes

  NEGPROV = tools.getConfig( "DEFAULT", "NEGPROV", bool )
  if NEGPROV :
    newDMRuleMeta = negativeWrites.negativeWrites( EOT, original_prog, cursor )
    ruleMeta.extend( newDMRuleMeta )

  # ----------------------------------------------------------------------------- #
  # provenance rewrite
  # add provenance rules

  #print ":::::::::::::::::::::::::::::::::"
  #print ":: STARTING PROVENANCE REWRITE ::"
  #print ":::::::::::::::::::::::::::::::::"

  provenanceRewriter.rewriteProvenance( ruleMeta, cursor )

  return original_prog


####################
#  RUN TRANSLATOR  #
####################
# input db cursor, name of raw dedalus file, cmdline args, and path to datalog savefile
# convert ded files to IR
# use IR or cmdline args to create clock relation
# use IR and clock relation to create equivalent datalog program
# output nothing
def runTranslator( cursor, dedFile, argDict, evaluator ) :

  # ------------------------------------------------------------- #
  # ded to IR

  meta     = dedToIR( dedFile, cursor )
  ruleMeta = meta[1] # observe fact meta not used.

  # ------------------------------------------------------------- #
  # generate the first clock

  starterClock( cursor, argDict )

  # ------------------------------------------------------------- #
  # apply all rewrites to generate final IR version

  rewrite( argDict[ "EOT" ], ruleMeta, cursor )
  #logging.debug( dumpers.programDump( cursor ) )

  # ------------------------------------------------------------- #
  # translate IR into datalog

  if evaluator == "c4" :
    allProgramLines = c4_translator.c4datalog( cursor ) # <- here.

  elif evaluator == "pyDatalog" :
    allProgramLines = pydatalog_translator.getPyDatalogProg( cursor )

  # ------------------------------------------------------------- #

  #print allProgramLines

  return allProgramLines


##############################
#  CREATE DEDALUS IR TABLES  #
##############################
def createDedalusIRTables( cursor ) :
  cursor.execute('''CREATE TABLE IF NOT EXISTS Fact       (fid text, name text, timeArg text)''')    # fact names
  cursor.execute('''CREATE TABLE IF NOT EXISTS FactData   (fid text, dataID int, data text, dataType text)''')   # fact attributes list
  cursor.execute('''CREATE TABLE IF NOT EXISTS Rule       (rid text, goalName text, goalTimeArg text, rewritten text)''')
  cursor.execute('''CREATE TABLE IF NOT EXISTS GoalAtt    (rid text, attID int, attName text, attType text)''')
  cursor.execute('''CREATE TABLE IF NOT EXISTS Subgoals   (rid text, sid text, subgoalName text, subgoalPolarity text, subgoalTimeArg text)''')
  cursor.execute('''CREATE TABLE IF NOT EXISTS SubgoalAtt (rid text, sid text, attID int, attName text, attType text)''')
  cursor.execute('''CREATE TABLE IF NOT EXISTS Equation  (rid text, eid text, eqn text)''')
  cursor.execute('''CREATE TABLE IF NOT EXISTS EquationVars  (rid text, eid text, varID int, var text)''')
  cursor.execute('''CREATE TABLE IF NOT EXISTS Clock (src text, dest text, sndTime int, delivTime int, simInclude text)''')
  cursor.execute('''CREATE UNIQUE INDEX IF NOT EXISTS IDX_Clock ON Clock(src, dest, sndTime, delivTime, simInclude)''') # make all rows unique
  cursor.execute('''CREATE TABLE IF NOT EXISTS Crash (src text, dest text, sndTime int, delivTime int, simInclude text)''')
  cursor.execute('''CREATE UNIQUE INDEX IF NOT EXISTS IDX_Crash ON Crash(src, dest, sndTime, delivTime, simInclude)''') # make all rows unique


##############
#  CLEAN UP  #
##############
def cleanUp( IRDB, saveDB ) :
  IRDB.close()        # close db
  os.remove( saveDB ) # delete the IR file to clean up


#######################
#  TRANSLATE DEDALUS  #
#######################
# input command line arguments
# output abs path to datalog program
def translateDedalus( argDict, cursor ) :

  logging.debug( "  TRANSLATE DEDALUS : running process..." )

  # ----------------------------------------------------------------- #
  # create tables
  createDedalusIRTables( cursor )
  logging.debug( "  TRANSLATE DEDALUS : created IR tables" )

  # ----------------------------------------------------------------- #
  # get all input files

  starterFile = argDict[ 'file' ]
  fileList    = tools.get_all_include_file_paths( starterFile )

  logging.debug( "  TRANSLATE DEDALUS : fileList = " + str( fileList ) )

  # ----------------------------------------------------------------- #
  # parse each file

  evaluator      = argDict[ 'evaluator' ] # flavor of datalog depends upon user's choice of evaluator.
  allProgramData = []

  for fileName in fileList :
    logging.debug( "  TRANSLATE DEDALUS : fileName = " + fileName )
    allProgramData.extend( runTranslator( cursor, fileName, argDict, evaluator ) )


  sys.exit( "wut" )

  logging.debug( dumpers.factDump( cursor ) )
  logging.debug( dumpers.ruleDump( cursor ) )
  logging.debug( dumpers.clockDump( cursor ) )

  # ----------------------------------------------------------------- #

  return allProgramData


#########
#  EOF  #
#########
