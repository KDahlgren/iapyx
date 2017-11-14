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

from utils          import dumpers, extractors, globalCounters, tools, parseCommandLineInput
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

  logging.debug( "  SET TYPES : running process..." )

  # ---------------------------------------------------- #
  # grab all rule ids

  cursor.execute( "SELECT rid FROM Rule" )
  ridList = cursor.fetchall()
  ridList = tools.toAscii_list( ridList )

  logging.debug( "  SET TYPES : number of rules = " + str( len( ridList ) ) )

  # ---------------------------------------------------- #
  # PASS 1 : populate data types for edb subgoals

  for rid in ridList :

    # grab all subgoal ids per rule
    cursor.execute( "SELECT sid FROM Subgoals WHERE rid=='" + rid + "'" )
    sidList = cursor.fetchall()
    sidList = tools.toAscii_list( sidList )

    logging.debug( "  SET TYPES : number of sids = " + str( len( sidList ) ) )

    for sid in sidList :

      # grab subgoal name
      cursor.execute( "SELECT subgoalName FROM Subgoals WHERE rid=='" + rid + "' AND sid=='" + sid + "'"  )
      subgoalName = cursor.fetchone()
      subgoalName = tools.toAscii_str( subgoalName )

      logging.debug( "  SET TYPES : subgoalName = " + subgoalName )

      # if subgoal is clock, then schema is trivial
      if subgoalName == "clock" :
        attIDList   = [ 0, 1, 2, 3 ]
        attTypeList = [ "string", "string", "int", "int" ]
        for i in range( 0, len( attIDList ) ) :
          attID   = attIDList[i]
          attType = attTypeList[i]
          cursor.execute( "UPDATE SubgoalAtt SET attType=='" + attType + "' WHERE rid=='" + rid + "' AND sid=='" + sid + "' AND attID=='" + str( attID ) + "'" )

      # if subgoal is edb, grab the types
      elif isEDB( subgoalName, cursor ) :

        logging.debug( "  SET TYPES : subgoal is edb." )

        # ===================================================== #
        # get the fid for facts with the target relation name

        # grab all fact relation ids and names
        cursor.execute( "SELECT fid,name FROM Fact" )
        edbRelations = cursor.fetchall()
        edbRelations = tools.toAscii_multiList( edbRelations )

        # pick one fid
        fid = None
        for rel in edbRelations :
          if rel[1] == subgoalName :
            fid = rel[0]
            break

        # ===================================================== #
        # get the schema

        cursor.execute( "SELECT dataType FROM FactData WHERE fid=='" + str( fid ) + "'" )
        attTypeList = cursor.fetchall()
        attTypeList = tools.toAscii_list( attTypeList )

        # ===================================================== #
        # grab all att ids for this subgoal

        cursor.execute( "SELECT attID FROM SubgoalAtt WHERE rid=='" + rid + "' AND sid=='" + sid + "'"  )
        attIDList = cursor.fetchall() # returns list of tuples. att id exists in the first tuple position.

        # ===================================================== #
        # update each subgoal attribute incrementally by relying on the 
        # order of attributes in the list structures

        logging.debug( "  SET TYPES : attIDList = " + str( attIDList ) + ", attTypeList = " + str( attTypeList ))

        if not len( attIDList ) == len( attTypeList ) :
          # get subgoal name
          cursor.execute( "SELECT subgoalName FROM Subgoals WHERE rid=='" + rid + "' AND sid=='" + sid + "'" )
          subgoalName = cursor.fetchone()
          subgoalName = tools.toAscii_str( subgoalName )

          # output error message
          sys.exit( "  SET TYPES : arity error in rule '" + dumpers.reconstructRule( rid, cursor ) + "' in subgoal '" + subgoalName + "'" )

        for i in range( 0, len( attIDList ) ) :
          attID   = attIDList[i][0]
          attType = attTypeList[i]
          logging.debug( "UPDATE SubgoalAtt SET attType=='" + attType + "' WHERE rid=='" + rid + "' AND sid=='" + sid + "' AND attID=='" + str( attID ) + "'"  )
          cursor.execute( "UPDATE SubgoalAtt SET attType=='" + attType + "' WHERE rid=='" + rid + "' AND sid=='" + sid + "' AND attID=='" + str( attID ) + "'" )


  # ---------------------------------------------------- #
  # PASS 2 : populate data types for idb goals in rules
  #          predicated on edbs

  setGoalTypes( cursor )

  # ---------------------------------------------------- #
  # PASS 3 : populate data types for idb subgoals 
  #          (and a subset of idb goals in the process)

  setSubgoalTypes( ridList, cursor )

  # ---------------------------------------------------- #
  # continue pattern until no untyped goal or
  # subgoal attributes exist in the IR db.
  # also, upon every iteration, make sure the number of
  # typed rules increases by at least one. otherwise,
  # the program is non-terminating.

  iterationCount                   = 0
  prev_number_of_fully_typed_rules = len( getFullyTypedRIDList( ridList, cursor ) )
  terminationFlag                  = False

  while rulesStillHaveUndefinedTypes( cursor ) :

    logging.debug( " SET TYPES : loop iteration = " + str( iterationCount ) )
    logging.debug( " SET TYPES : prev_number_of_fully_typed_rules = " + str( prev_number_of_fully_typed_rules ) )
    iterationCount += 1

    # ---------------------------------------------------- #
    # type as many goal atts as possible

    setGoalTypes( cursor )

    # ---------------------------------------------------- #
    # type as many subgoal atts as possible

    setSubgoalTypes( ridList, cursor )

    # ---------------------------------------------------- #
    # check liveness

    new_number_of_fully_typed_rules = len( getFullyTypedRIDList( ridList, cursor ) )
    logging.debug( "  SET TYPES : new_number_of_fully_typed_rules = " + str( new_number_of_fully_typed_rules ) )

    logging.debug( "  SET TYPES : preprev_number_of_fully_typed_rules v_number_of_fully_typed_rules = " + str( prev_number_of_fully_typed_rules ) )

    # define emergency termination condition
    if not new_number_of_fully_typed_rules > prev_number_of_fully_typed_rules :

      # terminate after two loop iterations with the same number of fully typed rules
      if terminationFlag :
        #print dumpers.ruleAttDump
        sys.exit( "  SET TYPES : ERROR : number of fully typed rules not increasing. program is non-terminating. aborting execution..." )

      else :
        terminationFlag = True

    # update emergency termination condition data
    prev_number_of_fully_typed_rules = len( getFullyTypedRIDList( ridList, cursor ) )

  logging.debug( "  SET TYPES : ...done." )


######################################
#  RULES STILL HAVE UNDEFINED TYPES  #
######################################
# check if any rule still has either an untyped goal att
# or an untyped subgoal att
def rulesStillHaveUndefinedTypes( cursor ) :

  ruleAttDump = dumpers.ruleAttDump( cursor )

  for rid in ruleAttDump :
    attDump        = ruleAttDump[ rid ]
    goalName       = attDump[ "goalName" ]
    goalAttData    = attDump[ "goalAttData" ]
    subgoalAttData = attDump[ "subgoalAttData" ]

    # ----------------------------------------------- #
    # check if any goal atts have undefined types

    for gatt in goalAttData :
      gattType = gatt[2]

      if gattType == "UNDEFINEDTYPE" :
        return True

    # ----------------------------------------------- #
    # check if any subgoal atts have undefined types

    for satt in subgoalAttData :
      sattType = satt[2]

      if sattType == "UNDEFINEDTYPE" :
        return True

  return False


##############################
#  GET FULLY TYPED RID LIST  #
##############################
# return the list of all rids such that
# all goal attributes and subgoal attributes
# in the associated rule are typed
#
# observe a "fully typed" rule means the types 
# for all goal and subgoal attributes in the
# rule have been successfully mapped to 
# respective data types.
def getFullyTypedRIDList( ridList, cursor ) :

  fullyTyped_ridList = []

  for rid in ridList :
    if isFullyTyped( rid, cursor ) :

      # grab the rule relation name
      cursor.execute( "SELECT goalName FROM Rule WHERE rid=='" + rid + "'" )
      goalName = cursor.fetchone()
      goalName = tools.toAscii_str( goalName )

      fullyTyped_ridList.append( [ rid, goalName ] )

  return fullyTyped_ridList


#######################
#  SET SUBGOAL TYPES  #
#######################
# iteratively use "fully typed" rules to type all subgoals per rule
def setSubgoalTypes( ridList, cursor ) :

  logging.debug( "  SET SUBGOAL TYPES : running process..." )

  # ===================================================== #
  # grab the list of all currently fully typed rules
  # if the list is empty, then the program is 
  # logicaly invalid.
  # At least one rule must be fully typed by the end of PASS2
  # because datalog program termination requires
  # at least one rule must be defined completely 
  # in terms of edbs.

  fullyTyped_ridList = getFullyTypedRIDList( ridList, cursor )
  logging.debug( "  SET SUBGOAL TYPES : fullyTyped_ridList = " + str( fullyTyped_ridList ) )

  # ===================================================== #
  # use the fully typed rules to type subgoals 
  # in other idbs

  for rid in ridList :

    logging.debug( "  SET SUBGOAL TYPES : rid = " + rid )

    # ===================================================== #
    # grab the rule dump

    ruleAttDump    = dumpers.singleRuleAttDump( rid, cursor )
    goalName       = ruleAttDump[ "goalName" ]
    goalAttData    = ruleAttDump[ "goalAttData" ]
    subgoalAttData = ruleAttDump[ "subgoalAttData" ]

    # ===================================================== #
    # iterate over subgoals

    for sub in subgoalAttData :

      logging.debug( "  SET SUBGOAL TYPES : sub = " + str( sub ) )

      subID      = sub[0]
      subName    = sub[1]
      subAttList = sub[2]

      # ------------------------------------------------ #
      # check if subgoal contains undefined types
      logging.debug( "  SET SUBGOAL TYPES : containsUndefinedTypes( subAttList ) = " + str( containsUndefinedTypes( subAttList ) ) )
      if containsUndefinedTypes( subAttList ) :

         # ------------------------------------------------ #
         # check if sub is fully typed
         for ftrule in fullyTyped_ridList :

           logging.debug( "  SET SUBGOAL TYPES : ftrule = " + str( ftrule ) )

           ftrule_rid      = ftrule[0]
           ftrule_goalName = ftrule[1]

           if subName == ftrule_goalName :

             # ------------------------------------------------ #
             # grab reference rule attribute info
             referenceRuleAttDump = dumpers.singleRuleAttDump( ftrule_rid, cursor )
             logging.debug( "  SET SUBGOAL TYPES : referenceRuleAttDump = " + str( referenceRuleAttDump ) )

             refGoalName       = referenceRuleAttDump[ "goalName" ]
             refGoalAttData    = referenceRuleAttDump[ "goalAttData" ]
             refSubgoalAttData = referenceRuleAttDump[ "subgoalAttData" ]

             for refatt in refGoalAttData :
               refAttID   = refatt[0]
               refAttName = refatt[1]
               refAttType = refatt[2]

               # ------------------------------------------------ #
               # perform update in target subgoal
               cursor.execute( "UPDATE SubgoalAtt SET attType='" + refAttType + "' WHERE rid=='" + rid + "' AND sid=='" + subID + "' AND attID=='" + str( refAttID ) + "'" )


  logging.debug( "  SET SUBGOAL TYPES : ...done." )


##############################
#  CONTAINS UNDEFINED TYPES  #
##############################
# given a list of att data, check if any att
# has an undefined type
def containsUndefinedTypes( attList ) :

  for att in attList :
    attID   = att[0]
    attName = att[1]
    attType = att[2]

    if attType == "UNDEFINEDTYPE" :
      return True

  return False


###################
#  SET GOAL ATTS  #
###################
# set goal attribute types based upon subgoal 
# attribute types.
def setGoalTypes( cursor ) :

  logging.debug( "  SET GOAL ATTS : running process..." )

  ruleAttDump = dumpers.ruleAttDump( cursor )

  for rid in ruleAttDump :

    logging.debug( "  SET GOAL ATTS : rid = " + rid )

    # ======================================== #
    # grab the data for this rule

    ruleData = ruleAttDump[ rid ]

    # ======================================== #
    # grab goal att data

    goalAttData = ruleData[ "goalAttData" ]

    # ======================================== #
    # grab att data

    subgoalAttData = ruleData[ "subgoalAttData" ]

    # ======================================== #
    # iterate over goal attributes
    # search for matching attribute in subgoals
    # if subgoal is edb, then pull the type
    # and save

    for gatt in goalAttData :
      gattID   = gatt[0]
      gattName = gatt[1]
      gattType = gatt[2]

      logging.debug( "  SET GOAL ATTS : gattName = " + gattName )
      logging.debug( "  SET GOAL ATTS : gattType = " + gattType )

      if gattType == "UNDEFINEDTYPE" :

        newGattType = None

        # SndTime and DelivTime attributes are always integers
        if gattName == "SndTime" or gattName == "DelivTime" :
          newGattType = "int"

        # aggregated goal attributes always have type 'int'
        elif isMath( gattName ) :
          newGattType = "int"

        # fixed string inputs always have type 'string'
        elif isFixedString( gattName ) :
          newGattType = "string"

        # fixed integer inputs always have type 'int'
        elif isFixedInt( gattName ) :
          newGattType = "int"

        else :
          for sub in subgoalAttData :
            subID      = sub[0]
            subName    = sub[1]
            subAttList = sub[2]

            for satt in subAttList :
              sattID   = satt[0]
              sattName = satt[1]
              sattType = satt[2]

              # check if the subgoal att matches the goal att
              # also make sure the subgoal att has a type
              if gattName == sattName and not sattType == "UNDEFINEDTYPE" :
                newGattType = sattType

        logging.debug( "  SET GOAL ATTS : newGattType = " + str( newGattType ) )

        # save the new attribute types
        if newGattType :

          logging.debug( "  SET GOAL ATTS : UPDATE GoalAtt SET attType=='" + newGattType + "' WHERE rid=='" + rid + "' AND attID=='" + str( gattID ) + "'" )

          cursor.execute( "UPDATE GoalAtt SET attType=='" + newGattType + "' WHERE rid=='" + rid + "' AND attID=='" + str( gattID ) + "'" )

  logging.debug( "  SET GOAL ATTS : ...done." )


#############
#  IS MATH  #
#############
# determine if the given input string contains an aggregate call
def isMath( gattName ) :

  # check for aggregate operators
  for op in aggOps :
    if gattName.startswith( op+"<" ) and gattName.endswith( ">" ) :
      return True

  # check for arithmetic operators
  for op in arithOps :
    if op in gattName :
      return True

  return False


#####################
#  IS FIXED STRING  #
#####################
# determine if the input string is a fixed string of input data
def isFixedString( gattName ) :
  if gattName.startswith( "'" ) and gattName.endswith( "'" ) :
    return True
  elif gattName.startswith( '"' ) and gattName.endswith( '"' ) :
    return True
  else :
    return False


##################
#  IS FIXED INT  #
##################
# determine if the input string is a fixed integer
def isFixedInt( gattName ) :

  if gattName.isdigit() :
    return True
  else :
    return False


####################
#  IS FULLY TYPED  #
####################
def isFullyTyped( rid, cursor ) :

  # ================================================= #
  # grab rule name for clarity of explanation

  cursor.execute( "SELECT goalName FROM Rule WHERE rid=='" + rid + "'" )
  goalName = cursor.fetchone()
  goalName = tools.toAscii_str( goalName )

  logging.debug( "  IS FULLY TYPED : running process on rule " + rid )

  # ===================================================== #
  # get the rule att data for the given rid

  currRuleAttData = dumpers.singleRuleAttDump( rid, cursor )

  # ===================================================== #
  # check of all goal attributes and all subgoal
  # attributes are fully typed

  # check goal atts
  goalAttData = currRuleAttData[ "goalAttData" ]
  for att in goalAttData :
    attName = att[0]
    attType = att[1]

    logging.debug( "  IS FULLY TYPED : att = " + str( att ) )

    if attType == "UNDEFINEDTYPE" :
      logging.debug( "  IS FULLY TYPED : goal atts returning False" )
      return False

  # check subgoal atts
  subgoalAttData = currRuleAttData[ "subgoalAttData" ]
  logging.debug( "  IS FULLY TYPED : subgoalAttData = " + str( subgoalAttData ) )
  for sub in subgoalAttData :
    subID   = sub[0]
    subName = sub[1]
    attList = sub[2]

    for att in attList :
      attID   = att[0]
      attName = att[1]
      attType = att[2]
      if attType == "UNDEFINEDTYPE" :
        logging.debug( "  IS FULLY TYPED : subgoal atts returning False" )
        return False

  logging.debug( "  IS FULLY TYPED : returning True" )
  return True


############
#  IS EDB  #
############
def isEDB( relationName, cursor ) :

  # grab all fact relation names
  cursor.execute( "SELECT name FROM Fact" )
  edbRelationNames = cursor.fetchall()
  edbRelationNames = tools.toAscii_list( edbRelationNames )

  if relationName in edbRelationNames :
    return True

  else :
    return False


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
def rewrite( EOT, factMeta, ruleMeta, cursor ) :

  logging.debug( "  REWRITE : running process..." )

  # ----------------------------------------------------------------------------- #
  # dedalus rewrite

  logging.debug( "  REWRITE : calling dedalus rewrites..." )

  allMeta  = dedalusRewriter.rewriteDedalus( factMeta, ruleMeta, cursor )
  factMeta = allMeta[0]
  ruleMeta = allMeta[1]

  # be sure to fill in all the type info for the new rule definitions
  setTypes( cursor )

  # ----------------------------------------------------------------------------- #
  # wilcard rewrites

#  logging.debug( "  REWRITE : calling wildcard rewrites..." )
#
#  try :
#    rewriteWildcards = tools.getConfig( "DEFAULT", "REWRITE_WILDCARDS", bool )
#    if rewriteWildcards :
#      rewriteNegativeSubgoalsWithWildcards.rewriteNegativeSubgoalsWithWildcards( cursor )
#
#  except ConfigParser.NoOptionError :
#    print "WARNING : no 'REWRITE_WILDCARDS' defined in 'DEFAULT' section of settings.ini ...running without wildcard rewrites."
#    pass

  # ----------------------------------------------------------------------------- #
  # negative rewrites

#  logging.debug( "  REWRITE : calling negative rewrites..." )
#
#  NEGPROV = tools.getConfig( "DEFAULT", "NEGPROV", bool )
#  if NEGPROV :
#    newDMRuleMeta = negativeWrites.negativeWrites( EOT, original_prog, cursor )
#    ruleMeta.extend( newDMRuleMeta )

  # ----------------------------------------------------------------------------- #
  # provenance rewrites

  logging.debug( "  REWRITE : calling provenance rewrites..." )

  # add the provenance rules to the existing rule set
  ruleMeta.extend( provenanceRewriter.rewriteProvenance( ruleMeta, cursor ) )

  # be sure to fill in all the type info for the new rule definitions
  setTypes( cursor )

  # ----------------------------------------------------------------------------- #

  logging.debug( "  REWRITE : ...done." )


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

  meta     = dedToIR( dedFile, cursor )
  factMeta = meta[0]
  ruleMeta = meta[1]

  logging.debug( "  RUN TRANSLATOR : len( ruleMeta ) = " + str( len( ruleMeta ) ) )

  # ------------------------------------------------------------- #
  # generate the first clock

  logging.debug( "  RUN TRANSLATOR : building starter clock..." )

  starterClock( cursor, argDict )

  logging.debug( "  RUN TRANSLATOR : ...done building starter clock." )

  # ------------------------------------------------------------- #
  # apply all rewrites to generate final IR version

  rewrite( argDict[ "EOT" ], factMeta, ruleMeta, cursor )

  # ------------------------------------------------------------- #
  # translate IR into datalog

  if evaluator == "c4" :

    logging.debug( "  RUN TRANSLATOR : launching c4 evaluation..." )

    allProgramLines = c4_translator.c4datalog( cursor )

    logging.debug( "  RUN TRANSLATOR : ...done with c4 evaluation." )

  elif evaluator == "pyDatalog" :
    allProgramLines = pydatalog_translator.getPyDatalogProg( cursor )

  # ------------------------------------------------------------- #

  #print allProgramLines

  logging.debug( "  RUN TRANSLATOR : returning allProgramLines = " + str( allProgramLines ) )
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

  complete_file_path = tools.compile_full_program_and_save( fileList )

  #logging.warning( "  TRANSLATE DEDALUS : translating files one at a time might be good if order matters." )
  logging.debug( "  TRANSLATE DEDALUS : complete_file_path = " + complete_file_path )
  allProgramData.extend( runTranslator( cursor, complete_file_path, argDict, evaluator ) )

  #logging.debug( dumpers.factDump( cursor ) )
  #logging.debug( dumpers.ruleDump( cursor ) )
  #logging.debug( dumpers.clockDump( cursor ) )

  # ----------------------------------------------------------------- #

  logging.debug( "  TRANSLATE DEDALUS : allProgramData = " + str( allProgramData ) )
  return allProgramData


#########
#  EOF  #
#########
