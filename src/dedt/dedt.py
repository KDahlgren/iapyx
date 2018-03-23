#!/usr/bin/env python

'''
dedt.py
   Define the functionality for converting parsed Dedalus into 
   SQL relations (the intermediate representation).


IR SCHEMA:

  Fact         ( fid text, name text,     timeArg text                                                )
  FactData     ( fid text, dataID int,    data text,        dataType text                             )
  Rule         ( rid text, goalName text, goalTimeArg text, rewritten text                            )
  GoalAtt      ( rid text, attID int,     attName text,     attType text                              )
  Subgoals     ( rid text, sid text,      subgoalName text, subgoalPolarity text, subgoalTimeArg text )
  SubgoalAtt   ( rid text, sid text,      attID int,        attName text,         attType text        )
  Equation     ( rid text, eid text,      eqn text                                                    )
  EquationVars ( rid text, eid text,      varID int,        var text                                  )
  Clock        ( src text, dest text,     sndTime int,      delivTime int,        simInclude text     )
  NextClock    ( src text, dest text,     sndTime int,      delivTime int,        simInclude text     )

'''

import copy, inspect, logging, os, pydot, string, sqlite3, sys

# ------------------------------------------------------ #
# import sibling packages HERE!!!
if not os.path.abspath( __file__ + "/../.." ) in sys.path :
  sys.path.append( os.path.abspath( __file__ + "/../.." ) )
if not os.path.abspath( __file__ + "/../translators" ) in sys.path :
  sys.path.append( os.path.abspath( __file__ + "/../translators" ) )
if not os.path.abspath( __file__ + "/../../dm" ) in sys.path :
  sys.path.append( os.path.abspath( __file__ + "/../../dm" ) )
if not os.path.abspath( __file__ + "/../../iedb_rewrites" ) in sys.path :
  sys.path.append( os.path.abspath( __file__ + "/../../iedb_rewrites" ) )
if not os.path.abspath( __file__ + "/../../rewrite_wildcards" ) in sys.path :
  sys.path.append( os.path.abspath( __file__ + "/../../rewrite_wildcards" ) )

from utils       import dumpers, extractors, globalCounters, setTypes, tools, parseCommandLineInput
from translators import c4_translator, dumpers_c4

import dm, iedb_rewrites, rewrite_wildcards

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

RELAX_SUBGOAL_TYPE_REQ = True

aggOps   = [ "min", "max", "sum", "count", "avg" ]
arithOps = [ "+", "-", "/", "*" ]


##########################
#  GLOBAL COUNTER RESET  #
##########################
# reset global counters for a new execution of the 
# dedt module
def globalCounterReset() :
  globalCounters.fidCounter      = -1
  globalCounters.ridCounter      = -1
  globalCounters.sidCounter      = -1
  globalCounters.eidCounter      = -1
  globalCounters.provRuleCounter = -1


###############
#  DED TO IR  #
###############
# input raw ded file
# store intermediate representation in SQL database
# output nothing
def dedToIR( filename, cursor, settings_path ) :

  parsedLines = []
  parsedLines = dedalusParser.parseDedalus( filename, settings_path ) # program exits here if file cannot be opened.

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
      #fid = tools.getID()
      fid = tools.getIDFromCounters( "fid" )

      logging.debug( "  DED TO IR : fid = " + str( fid ) )

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
      #rid = tools.getID()
      rid = tools.getIDFromCounters( "rid" )

      logging.debug( "  DED TO IR : rid = " + str( rid ) )

      # save rule goal info
      newRule = Rule.Rule( rid, ruleData, cursor )

      # save rule metadata (aka object)
      ruleMeta.append( newRule )

  return [ factMeta, ruleMeta ]


###################
#  STARTER CLOCK  #
###################
# input cursor and cmdline args, assume IR successful
# create the initial clock relation in SQL database
# output nothing
def starterClock( cursor, argDict ) :
  logging.debug( "  STARTER CLOCK : running process..." )
  clockRelation.initClockRelation( cursor, argDict )
  logging.debug( "  STARTER CLOCK : ...done." )


########################
#  REWRITE TO DATALOG  #
########################
# input cursor, assume IR successful
# output nothing
def rewrite_to_datalog( argDict, factMeta, ruleMeta, cursor ) :

  logging.debug( "  REWRITE : running process..." )

  settings_path = argDict[ "settings" ]
  EOT           = argDict[ "EOT" ]

  for rule in ruleMeta :
    rid = rule.rid
    cursor.execute( "SELECT attID,attName FROM GoalAtt WHERE rid=='" + str( rid ) + "'" )
    goal_atts = cursor.fetchall()
    logging.debug( "  DEDT : len( goal_atts ) = " + str( len( goal_atts )) )
    goal_atts = tools.toAscii_multiList( goal_atts )
    logging.debug( "  DEDT : len( goal_atts ) = " + str( len( goal_atts )) )
    logging.debug( "  DEDT : goal_atts (0) = " + str( goal_atts ) )
    logging.debug( "  DEDT : r = " + dumpers.reconstructRule( rid, cursor ) )

  # ----------------------------------------------------------------------------- #
  # dedalus rewrite

  logging.debug( "  REWRITE : calling dedalus rewrites..." )

  allMeta  = dedalusRewriter.rewriteDedalus( argDict, factMeta, ruleMeta, cursor )
  factMeta = allMeta[0]
  ruleMeta = allMeta[1]

  # be sure to fill in all the type info for the new rule definitions
  #setTypes.setTypes( cursor, argDict )

  for rule in ruleMeta :
    rid = rule.rid
    cursor.execute( "SELECT attID,attName FROM GoalAtt WHERE rid=='" + str( rid ) + "'" )
    goal_atts = cursor.fetchall()
    goal_atts = tools.toAscii_multiList( goal_atts )
    logging.debug( "  DEDT : goal_atts (1) = " + str( goal_atts ) )

  # ----------------------------------------------------------------------------- #
  # dm rewrites

  # be sure to fill in all the type info for the new rule definitions
  setTypes.setTypes( cursor, argDict )

  try :
    RUN_DM = tools.getConfig( settings_path, "DEFAULT", "DM", bool )
    if RUN_DM :

      factMeta, ruleMeta = dm.dm( factMeta, ruleMeta, cursor, argDict ) # returns new ruleMeta

      # be sure to fill in all the type info for the new rule definitions
      setTypes.setTypes( cursor, argDict )

  except ConfigParser.NoOptionError :
    logging.warning( "WARNING : no 'DM' defined in 'DEFAULT' section of settings file ...running without dm rewrites" )
    pass

  for rule in ruleMeta :
    rid = rule.rid
    cursor.execute( "SELECT attID,attName FROM GoalAtt WHERE rid=='" + str( rid ) + "'" )
    goal_atts = cursor.fetchall()
    goal_atts = tools.toAscii_multiList( goal_atts )
    logging.debug( "  DEDT : goal_atts (2) = " + str( goal_atts ) )

  # ----------------------------------------------------------------------------- #
  # iedb rewrites 
  # ^ need to happen AFTER dm rewrites or else get wierd c4 eval results???
  #   weird, dude.

  try :
    RUN_IEDB_REWRITES = tools.getConfig( settings_path, "DEFAULT", "IEDB_REWRITES", bool )
    if RUN_IEDB_REWRITES :

      factMeta, ruleMeta = iedb_rewrites.iedb_rewrites( factMeta, ruleMeta, cursor, settings_path ) # returns new ruleMeta

      for rule in ruleMeta :
        rid = rule.rid
        cursor.execute( "SELECT attID,attName FROM GoalAtt WHERE rid=='" + str( rid ) + "'" )
        goal_atts = cursor.fetchall()
        goal_atts = tools.toAscii_multiList( goal_atts )
        logging.debug( "  DEDT : goal_atts (3) = " + str( goal_atts ) )

      # be sure to fill in all the type info for the new rule definitions
      setTypes.setTypes( cursor, argDict )

  except ConfigParser.NoOptionError :
    logging.info( "WARNING : no 'IEDB_REWRITES' defined in 'DEFAULT' section of settings file ...running without iedb rewrites" )
    pass

  # ----------------------------------------------------------------------------- #
  # provenance rewrites

  logging.debug( "  REWRITE : before prov dump :" )
  for rule in ruleMeta :
    logging.debug( "  REWRITE : (0) r = " + printRuleWithTypes( rule.rid, cursor ) )
  #sys.exit( "blah2" )

  logging.debug( "  REWRITE : calling provenance rewrites..." )

  # add the provenance rules to the existing rule set
  ruleMeta.extend( provenanceRewriter.rewriteProvenance( ruleMeta, cursor, argDict ) )

  for rule in ruleMeta :
    #logging.debug( "rule.ruleData = " + str( rule.ruleData ) )
    logging.debug( "  REWRITE : (1) r = " + dumpers.reconstructRule( rule.rid, rule.cursor ) )
  #sys.exit( "blah2" )

  # be sure to fill in all the type info for the new rule definitions
  setTypes.setTypes( cursor, argDict )

  # ----------------------------------------------------------------------------- #
  # wilcard rewrites

  logging.debug( "  REWRITE : calling wildcard rewrites..." )

  try :
    rewriteWildcards = tools.getConfig( settings_path, "DEFAULT", "WILDCARD_REWRITES", bool )
    if rewriteWildcards :
      ruleMeta = rewrite_wildcards.rewrite_wildcards( ruleMeta, cursor )

  except ConfigParser.NoOptionError :
    logging.warning( "WARNING : no 'WILDCARD_REWRITES' defined in 'DEFAULT' section of settings.ini ...running without wildcard rewrites." )
    pass

  # be sure to fill in all the type info for the new rule definitions
  setTypes.setTypes( cursor, argDict )

  # ----------------------------------------------------------------------------- #

  for rule in ruleMeta :
    logging.debug( "rule.ruleData = " + str( rule.ruleData ) )
    logging.debug( "  REWRITE : (2) r = " + dumpers.reconstructRule( rule.rid, rule.cursor ) )
#  sys.exit( "blah2" )

  logging.debug( "  REWRITE : ...done." )

  return [ factMeta, ruleMeta ]


####################
#  RUN TRANSLATOR  #
####################
# input db cursor, name of raw dedalus file, cmdline args, and path to datalog savefile
# convert ded files to IR
# use IR or cmdline args to create clock relation
# use IR and clock relation to create equivalent datalog program
# output nothing
def runTranslator( cursor, dedFile, argDict, evaluator ) :

  logging.debug( "  RUN TRANSLATOR : running process..." )
  #logging.warning( "  RUN TRANSLATOR : WARNING : need to fix file includes to run translator once. need to know all program lines to derive data types for program." )

  # ------------------------------------------------------------- #
  # ded to IR

  meta     = dedToIR( dedFile, cursor, argDict[ "settings" ] )
  factMeta = meta[0]
  ruleMeta = meta[1]

  logging.debug( "  RUN TRANSLATOR : len( ruleMeta ) = " + str( len( ruleMeta ) ) )

  # ------------------------------------------------------------- #
  # generate the first clock

  logging.debug( "  RUN TRANSLATOR : building starter clock..." )

  starterClock( cursor, argDict )

  logging.debug( "  RUN TRANSLATOR : ...done building starter clock." )

  # ------------------------------------------------------------- #
  # apply rewrites to generate a datalog version of the IR
  # and fact/rule meta data

  allMeta  = rewrite_to_datalog( argDict, factMeta, ruleMeta, cursor )
  factMeta = allMeta[0]
  ruleMeta = allMeta[1]

  # ------------------------------------------------------------- #
  # translate IR into datalog

  if evaluator == "c4" :

    logging.debug( "  RUN TRANSLATOR : launching c4 evaluation..." )

    allProgramLines = c4_translator.c4datalog( argDict, cursor )

    logging.debug( "  RUN TRANSLATOR : ...done with c4 evaluation." )

  elif evaluator == "pyDatalog" :
    allProgramLines = pydatalog_translator.getPyDatalogProg( cursor )

  # ------------------------------------------------------------- #

  #print allProgramLines

  # save all program lines to file
  try :
    if argDict[ "data_save_path" ] :
      logging.debug( "  RUN TRANSLATOR : using data_save_path '" + argDict[ "data_save_path" ] + "'" )
      fo = open( argDict[ "data_save_path" ] + "final_initial_program.olg", "w" )
      program = allProgramLines[0]
      for line in program :
        fo.write( line + "\n" )
      fo.close()
  except KeyError :
    logging.debug( "  RUN TRANSLATOR : no data_save_path specified. skipping writing final olg program to file." )

  logging.debug( "  RUN TRANSLATOR : returning allProgramLines = " + str( allProgramLines ) )
  return [ allProgramLines, factMeta, ruleMeta ]


##############################
#  CREATE DEDALUS IR TABLES  #
##############################
def createDedalusIRTables( cursor ) :
  cursor.execute('''CREATE TABLE IF NOT EXISTS Fact         (fid text, name text, timeArg text)''')    # fact names
  cursor.execute('''CREATE TABLE IF NOT EXISTS FactData     (fid text, dataID int, data text, dataType text)''')   # fact data list
  cursor.execute('''CREATE TABLE IF NOT EXISTS Rule         (rid text, goalName text, goalTimeArg text, rewritten text)''')
  cursor.execute('''CREATE TABLE IF NOT EXISTS GoalAtt      (rid text, attID int, attName text, attType text)''')
  cursor.execute('''CREATE TABLE IF NOT EXISTS Subgoals     (rid text, sid text, subgoalName text, subgoalPolarity text, subgoalTimeArg text)''')
  cursor.execute('''CREATE TABLE IF NOT EXISTS SubgoalAtt   (rid text, sid text, attID int, attName text, attType text)''')
  cursor.execute('''CREATE TABLE IF NOT EXISTS Equation     (rid text, eid text, eqn text)''')
  cursor.execute('''CREATE TABLE IF NOT EXISTS EquationVars (rid text, eid text, varID int, var text)''')
  cursor.execute('''CREATE TABLE IF NOT EXISTS Clock (src text, dest text, sndTime int, delivTime int, simInclude text)''')
  cursor.execute('''CREATE TABLE IF NOT EXISTS NextClock (src text, dest text, sndTime int, delivTime int, simInclude text)''')
  cursor.execute('''CREATE UNIQUE INDEX IF NOT EXISTS IDX_Clock ON Clock(src, dest, sndTime, delivTime, simInclude)''') # make all rows unique
  cursor.execute('''CREATE UNIQUE INDEX IF NOT EXISTS IDX_NextClock ON NextClock(src, dest, sndTime, delivTime, simInclude)''') # make all rows unique
  cursor.execute('''CREATE TABLE IF NOT EXISTS Crash (src text, dest text, sndTime int, NRESERVED int, simInclude text)''')
  cursor.execute('''CREATE UNIQUE INDEX IF NOT EXISTS IDX_Crash ON Crash(src, dest, sndTime, NRESERVED, simInclude)''') # make all rows unique


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

  complete_file_path = tools.compile_full_program_and_save( fileList )

  #logging.warning( "  TRANSLATE DEDALUS : translating files one at a time might be good if order matters." )
  logging.debug( "  TRANSLATE DEDALUS : complete_file_path = " + complete_file_path )
  allData = runTranslator( cursor, complete_file_path, argDict, evaluator )

  datalogLines = allData[ 0 ]
  factMeta     = allData[ 1 ]
  ruleMeta     = allData[ 2 ]

  # ----------------------------------------------------------------- #

  logging.debug( "  TRANSLATE DEDALUS : datalogLines = " + str( datalogLines ) )
  return datalogLines, factMeta, ruleMeta


###########################
#  PRINT RULE WITH TYPES  #
###########################
# output all rule goals with attnames and associated types.
def printRuleWithTypes( rid, cursor ) :

  logging.debug( "  PRINT RULE WITH TYPES : running process..." )

  printLine = ""

  # ----------------------------------------- #
  # get relation name

  cursor.execute( "SELECT goalName FROM Rule WHERE rid=='" + str( rid ) + "'" )
  goalName = cursor.fetchone()
  goalName = tools.toAscii_str( goalName )

  # ----------------------------------------- #
  # get goal att names and types

  cursor.execute( "SELECT attID,attName,attType FROM GoalAtt WHERE rid=='" + str( rid ) + "'" )
  gattData = cursor.fetchall()
  gattData = tools.toAscii_multiList( gattData )

  # build head for printing
  goal = goalName + "("
  for gatt in gattData :
    gattName = gatt[1]
    gattType = gatt[2]
    goal += "[" + gattName + "," + gattType + "]"
  goal += ")"

  printLine += goal + " :- "

  # ----------------------------------------- #
  # get all subgoal ids

  cursor.execute( "SELECT sid FROM Subgoals WHERE rid=='" + str( rid ) + "'" )
  sidList = cursor.fetchall()
  sidList = tools.toAscii_list( sidList )

  # ----------------------------------------- #
  # iterate over sids

  for sid in sidList :

    # ----------------------------------------- #
    # get subgoal name

    cursor.execute( "SELECT subgoalName FROM Subgoals WHERE rid=='" + str( rid ) + "' AND sid=='" + str( sid ) + "'" )
    subgoalName = cursor.fetchone()
    subgoalName = tools.toAscii_str( subgoalName )

    # ----------------------------------------- #
    # get subgoal att names and types

    cursor.execute( "SELECT attID,attName,attType FROM SubgoalAtt WHERE rid=='" + str( rid ) + "' AND sid=='" + str( sid ) + "'" )
    sattData = cursor.fetchall()
    sattData = tools.toAscii_multiList( sattData )

    # ----------------------------------------- #
    # build subgoal for printing

    subgoal = subgoalName + "("
    for satt in sattData :
      sattName = satt[1]
      sattType = satt[2]
      subgoal += "[" + sattName + "," + sattType + "]"
    subgoal += ")"

    printLine += subgoal + ","

  return printLine[:-1]

#########
#  EOF  #
#########
