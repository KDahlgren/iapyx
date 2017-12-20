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
if not os.path.abspath( __file__ + "/../../dml" ) in sys.path :
  sys.path.append( os.path.abspath( __file__ + "/../../dml" ) )

from utils       import dumpers, extractors, globalCounters, setTypes, tools, parseCommandLineInput
from translators import c4_translator, dumpers_c4

import dml, rewriteNegativeSubgoalsWithWildcards

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

  setTypes.setTypes( cursor )

  return [ factMeta, ruleMeta ]

'''
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

      # if subgoal is crash, then schema is trivial
      elif subgoalName == "crash" :
        attIDList   = [ 0, 1, 2 ]
        attTypeList = [ "string", "string", "int" ]
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
  # PASS 3 : populate data types for idb subgoals 
  #          (and a subset of idb goals in the process)

  setSubgoalTypes( ridList, cursor )

  # ---------------------------------------------------- #
  # PASS 2 : populate data types for idb goals in rules
  #          predicated on edbs

  setGoalTypes( cursor )

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
    # type as many subgoal atts as possible

    setSubgoalTypes( ridList, cursor )

    # ---------------------------------------------------- #
    # type as many goal atts as possible

    setGoalTypes( cursor )

    # ---------------------------------------------------- #
    # check liveness

    new_number_of_fully_typed_rules = len( getFullyTypedRIDList( ridList, cursor ) )
    logging.debug( "  SET TYPES : new_number_of_fully_typed_rules  = " + str( new_number_of_fully_typed_rules ) )
    logging.debug( "  SET TYPES : prev_number_of_fully_typed_rules = " + str( prev_number_of_fully_typed_rules ) )

    # define emergency termination condition
    if not new_number_of_fully_typed_rules > prev_number_of_fully_typed_rules :

      # terminate after two loop iterations with the same number of fully typed rules
      if terminationFlag :
        #print dumpers.ruleAttDump
        logging.debug( "ERROR : program is non-terminating. generating datalog dependency graph..." )
        logging.debug( generateDatalogDependencyGraph( cursor ) )
        logging.debug( printIRWithTypes( cursor ) )
        sys.exit( "  SET TYPES : ERROR : number of fully typed rules not increasing. program is non-terminating. aborting execution..." )

      else :
        terminationFlag = True

    # update emergency termination condition data
    prev_number_of_fully_typed_rules = new_number_of_fully_typed_rules

  logging.debug( generateDatalogDependencyGraph( cursor ) )
  logging.debug( "  SET TYPES : ...done." )
'''

#######################################
#  GENERATE DATALOG DEPENDENCY GRAPH  #
#######################################
# build a visualization of the datalog rule dependencies
# in the form of a graph.
def generateDatalogDependencyGraph( cursor ) :

  nodes = []
  edges = []

  # ----------------------------------------- #
  # get all rids

  cursor.execute( "SELECT rid FROM Rule" )
  ridList = cursor.fetchall()
  ridList = tools.toAscii_list( ridList )

  # ----------------------------------------- #
  # iterate over rules

  for rid in ridList :

    # ----------------------------------------- #
    # get relation name

    cursor.execute( "SELECT goalName FROM Rule WHERE rid=='" + rid + "'" )
    goalName = cursor.fetchone()
    goalName =  tools.toAscii_str( goalName )

    # ----------------------------------------- #
    # get goal atts

    cursor.execute( "SELECT attID,attName,attType FROM GoalAtt WHERE rid=='" + rid + "'" )
    gattData = cursor.fetchall()
    gattData = tools.toAscii_multiList( gattData )

    # ----------------------------------------- #
    # build goal string

    goalStr = ""
    goalStr += goalName + "("
    for gatt in gattData :
      gattName = gatt[1]
      gattType = gatt[2]
      goalStr += "[" + gattName + "," + gattType + "],"
    goalStr = goalStr[:-1]
    goalStr += ")"

    # add goal node and edge
    goalName_node      = pydot.Node( "GOAL=" + goalName, shape='oval' )
    goalStr_node       = pydot.Node( goalStr, shape='box' )
    goal_name_str_edge = pydot.Edge( goalName_node, goalStr_node )

    logging.debug( "  GENERATE DATALOG DEPENDENCY GRAPH : adding node " + goalName_node.get_name() )
    logging.debug( "  GENERATE DATALOG DEPENDENCY GRAPH : adding node " + goalStr_node.get_name() )
    logging.debug( "  GENERATE DATALOG DEPENDENCY GRAPH : adding edge " + goal_name_str_edge.get_source() + " -> " + goal_name_str_edge.get_destination() )

    nodes.append( goalName_node )
    nodes.append( goalStr_node )
    edges.append( goal_name_str_edge )

    # ----------------------------------------- #
    # get all subgoal ids

    cursor.execute( "SELECT sid FROM Subgoals WHERE rid=='" + rid + "'" )
    sidList = cursor.fetchall()
    sidList = tools.toAscii_list( sidList )

    # ----------------------------------------- #
    # iterate over subgoals

    for sid in sidList :

      # ----------------------------------------- #
      # get subgoal name

      cursor.execute( "SELECT subgoalName FROM Subgoals WHERE rid=='" + rid + "' AND sid=='" + sid + "'"  )
      subgoalName = cursor.fetchone()
      subgoalName = tools.toAscii_str( subgoalName )

      # ----------------------------------------- #
      # get subgoal atts

      cursor.execute( "SELECT attID,attName,attType FROM SubgoalAtt WHERE rid=='" + rid + "' AND sid=='" + sid + "'"  )
      sattData = cursor.fetchall()
      sattData = tools.toAscii_multiList( sattData )

      # ----------------------------------------- #
      # build subgoal str

      subgoalStr = ""
      subgoalStr += subgoalName + "("
      for satt in sattData :
        sattName = satt[1]
        sattType = satt[2]
        subgoalStr += "[" + sattName + "," + sattType + "],"
      subgoalStr  = subgoalStr[:-1]
      subgoalStr += ")"

      # add subgoal node and edges
      subgoalStr_node               = pydot.Node( subgoalStr, shape='diamond' )
      subgoalName_node              = pydot.Node( "SUBGOAL=" + subgoalName, shape='oval' )
      goal_str_subgoal_str_edge     = pydot.Edge( goalStr_node, subgoalStr_node )
      subgoal_str_subgoal_name_edge = pydot.Edge( subgoalStr_node, subgoalName_node )

      logging.debug( "  GENERATE DATALOG DEPENDENCY GRAPH : adding node " + subgoalStr_node.get_name() )
      logging.debug( "  GENERATE DATALOG DEPENDENCY GRAPH : adding node " + subgoalName_node.get_name() )
      logging.debug( "  GENERATE DATALOG DEPENDENCY GRAPH : adding edge " + goal_str_subgoal_str_edge.get_source() + " -> " + goal_str_subgoal_str_edge.get_destination() )
      logging.debug( "  GENERATE DATALOG DEPENDENCY GRAPH : adding edge " + subgoal_str_subgoal_name_edge.get_source() + " -> " + subgoal_str_subgoal_name_edge.get_destination() )

      nodes.append( subgoalStr_node )
      nodes.append( subgoalName_node )
      edges.append( goal_str_subgoal_str_edge )
      edges.append( subgoal_str_subgoal_name_edge )

      # ----------------------------------------- #
      # ----------------------------------------- #
      # add special nodes for fact connections

      if isFact( subgoalName, cursor ) :

        # ----------------------------------------- #
        # get an fid for a fact with the subgoal name

        cursor.execute( "SELECT fid FROM Fact WHERE name=='" + subgoalName + "'" )
        fidList = cursor.fetchall()
        fidList = tools.toAscii_list( fidList )
        anFID = fidList[0]

        # ----------------------------------------- #
        # get the att type schema for the fact

        cursor.execute( "SELECT dataID,data,dataType FROM FactData WHERE fid=='" + anFID + "'" )
        fattData = cursor.fetchall()
        fattData = tools.toAscii_multiList( fattData )

        fschema  = ""
        fschema += subgoalName + "("
        for fatt in fattData :
          fattType = fatt[2]
          fschema += fattType + ","
        fschema = fschema[:-1]
        fschema += ")"

        # save fact node and edge
        fschema_node = pydot.Node( "FACT=" + fschema, shape='cylinder' )
        subgoal_str_fschema_edge = pydot.Edge( subgoalStr_node, fschema_node )

        logging.debug( "  GENERATE DATALOG DEPENDENCY GRAPH : adding node " + fschema_node.get_name() )
        logging.debug( "  GENERATE DATALOG DEPENDENCY GRAPH : adding edge " + subgoal_str_fschema_edge.get_source() + " -> " + subgoal_str_fschema_edge.get_destination() )

        nodes.append( fschema_node )
        edges.append( subgoal_str_fschema_edge )

  # ----------------------------------------- #
  # generate goal to subgoal node edges

  for node1 in nodes :
    for node2 in nodes :
      if "SUBGOAL=" in node1.get_name() and "GOAL=" in node2.get_name() :
        subgoalName = node1.get_name().replace( "SUBGOAL=", "" )
        goalName    = node2.get_name().replace( "GOAL=", "" )
        if subgoalName == goalName :
          newEdge = pydot.Edge( node1, node2 )
          edges.append( newEdge )

  # ----------------------------------------- #
  # create graph
  graph = pydot.Dot( graph_type = 'digraph', strict = True ) # strict => ignore duplicate edges
  path  = os.getcwd() + "/datalogDependencyGraph.png"

  # add nodes :
  for n in nodes :
    graph.add_node( n )

  # add edges
  for e in edges :
    graph.add_edge( e )

  logging.info( "Saving prov tree render to " + str(path) )
  graph.write_png( path )


#############
#  IS FACT  #
#############
# check if the given relation name maps to a fact
def isFact( relationName, cursor ) :

  cursor.execute( "SELECT fid FROM Fact WHERE name=='" + relationName + "'" )
  fidList = cursor.fetchall()
  fidList = tools.toAscii_list( fidList )

  if len( fidList ) > 0 :
    return True
  else :
    return False


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


#########################
#  PRINT IR WITH TYPES  #
#########################
# output all rule goals with attnames and associated types.
def printIRWithTypes( cursor ) :

  logging.debug( "  PRINT IR WITH TYPES : running process..." )

  # ----------------------------------------- #
  # get all rids

  cursor.execute( "SELECT rid FROM Rule" )
  ridList = cursor.fetchall()
  ridList = tools.toAscii_list( ridList )

  logging.debug( "  PRINT IR WITH TYPE : number of fully typed rules = " + str( len( getFullyTypedRIDList( ridList, cursor ) ) ) )

  # ----------------------------------------- #
  # iterate over rids
  for rid in ridList :

    printLine = ""

    # ----------------------------------------- #
    # get relation name

    cursor.execute( "SELECT goalName FROM Rule WHERE rid=='" + rid + "'" )
    goalName = cursor.fetchone()
    goalName = tools.toAscii_str( goalName )

    # ----------------------------------------- #
    # get goal att names and types

    cursor.execute( "SELECT attID,attName,attType FROM GoalAtt WHERE rid=='" + rid + "'" )
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

    cursor.execute( "SELECT sid FROM Subgoals WHERE rid=='" + rid + "'" )
    sidList = cursor.fetchall()
    sidList = tools.toAscii_list( sidList )

    # ----------------------------------------- #
    # iterate over sids

    for sid in sidList :

      # ----------------------------------------- #
      # get subgoal name

      cursor.execute( "SELECT subgoalName FROM Subgoals WHERE rid=='" + rid + "' AND sid=='" + sid + "'" )
      subgoalName = cursor.fetchone()
      subgoalName = tools.toAscii_str( subgoalName )

      # ----------------------------------------- #
      # get subgoal att names and types

      cursor.execute( "SELECT attID,attName,attType FROM SubgoalAtt WHERE rid=='" + rid + "' AND sid=='" + sid + "'" )
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
    #print printLine[:-1]

  logging.debug( "  PRINT IR WITH TYPES : ...done." )


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

  logging.debug( "  GET FULLY TYPED RID LIST : running process..." )

  fullyTyped_list = []

  for rid in ridList :

    if isFullyTyped( rid, cursor ) :

      # grab the rule relation name
      cursor.execute( "SELECT goalName FROM Rule WHERE rid=='" + rid + "'" )
      goalName = cursor.fetchone()
      goalName = tools.toAscii_str( goalName )

      fullyTyped_list.append( [ rid, goalName ] )

  logging.debug( "  GET FULLY TYPED RID LIST : returning fullyTyped_list with len = " + str( len( fullyTyped_list ) ) )
  logging.debug( "  GET FULLY TYPED RID LIST : fullyTyped_list = " + str( fullyTyped_list ) )
  return fullyTyped_list


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

  fullyTyped_list = getFullyTypedRIDList( ridList, cursor )
  logging.debug( "  SET SUBGOAL TYPES : fullyTyped_list = " + str( fullyTyped_list ) )
  for ft in fullyTyped_list :
    logging.debug( "  SET SUBGOAL TYPES : ft = " + printRuleWithTypes( ft[0], cursor ) )

  # ===================================================== #
  # use the fully typed rules to type subgoals 
  # in other idbs

  for rid in ridList :

    logging.debug( "-------------------------------------------------------" )
    logging.debug( "  SET SUBGOAL TYPES : rid           = " + rid )
    logging.debug( "  SET SUBGOAL TYPES : original rule = " + printRuleWithTypes( rid, cursor ) )

    # ===================================================== #
    # grab the rule dump

    ruleAttDump    = dumpers.singleRuleAttDump( rid, cursor )
    goalName       = ruleAttDump[ "goalName" ]
    goalAttData    = ruleAttDump[ "goalAttData" ]
    subgoalAttData = ruleAttDump[ "subgoalAttData" ]

    logging.debug( "  SET SUBGOAL TYPES : goalName = " + goalName )

    # ===================================================== #
    # iterate over subgoals

    for sub in subgoalAttData :

      logging.debug( "    SSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSS" )
      logging.debug( "    SET SUBGOAL TYPES : sub = " + str( sub ) )

      subID      = sub[0]
      subName    = sub[1]
      subAttList = sub[2]

      # ------------------------------------------------ #
      # check if subgoal contains undefined types

      logging.debug( "    SET SUBGOAL TYPES : containsUndefinedTypes( subAttList ) = " + str( containsUndefinedTypes( subAttList ) ) )

      if containsUndefinedTypes( subAttList ) :

         # ------------------------------------------------ #
         # check if sub is fully typed

         for ftrule in fullyTyped_list :

           ftrule_rid      = ftrule[0]
           ftrule_goalName = ftrule[1]

           logging.debug( "      FFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF" )
           logging.debug( "      SET SUBGOAL TYPES : ftrule      = " + str( ftrule ) )
           logging.debug( "      SET SUBGOAL TYPES : ftrule rule = " + printRuleWithTypes( ftrule_rid, cursor ) )

           logging.debug( "      SET SUBGOAL TYPES : subName == ftrule_goalName is " + str( subName == ftrule_goalName ) )

           if subName == ftrule_goalName :

             # ------------------------------------------------ #
             # grab reference rule attribute info

             referenceRuleAttDump = dumpers.singleRuleAttDump( ftrule_rid, cursor )
             logging.debug( "    SET SUBGOAL TYPES : referenceRuleAttDump = " + str( referenceRuleAttDump ) )

             refGoalName       = referenceRuleAttDump[ "goalName" ]
             refGoalAttData    = referenceRuleAttDump[ "goalAttData" ]
             refSubgoalAttData = referenceRuleAttDump[ "subgoalAttData" ]

             for refatt in refGoalAttData :
               refAttID   = refatt[0]
               refAttName = refatt[1]
               refAttType = refatt[2]

               # ------------------------------------------------ #
               # perform update in target subgoal

               logging.debug( "    UPDATE SubgoalAtt SET attType='" + refAttType + "' WHERE rid=='" + rid + "' AND sid=='" + subID + "' AND attID=='" + str( refAttID ) + "'" )

               cursor.execute( "UPDATE SubgoalAtt SET attType='" + refAttType + "' WHERE rid=='" + rid + "' AND sid=='" + subID + "' AND attID=='" + str( refAttID ) + "'" )

               logging.debug( "    SET SUBGOAL TYPES : new rule  = " + printRuleWithTypes( rid, cursor ) )

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

  logging.debug( "  SET GOAL TYPES : running process..." )

  ruleAttDump = dumpers.ruleAttDump( cursor )

  for rid in ruleAttDump :

    logging.debug( "  SET GOAL TYPES : rid           = " + rid )
    logging.debug( "  SET GOAL TYPES : original rule = " + printRuleWithTypes( rid, cursor ) )

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

      logging.debug( "  SET GOAL TYPES : gattName = " + gattName )
      logging.debug( "  SET GOAL TYPES : gattType = " + gattType )

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

        logging.debug( "  SET GOAL TYPES : newGattType = " + str( newGattType ) )

        # save the new attribute types
        if newGattType :

          logging.debug( "  SET GOAL TYPES : UPDATE GoalAtt SET attType=='" + newGattType + "' WHERE rid=='" + rid + "' AND attID=='" + str( gattID ) + "'" )

          cursor.execute( "UPDATE GoalAtt SET attType=='" + newGattType + "' WHERE rid=='" + rid + "' AND attID=='" + str( gattID ) + "'" )

    logging.debug( "  SET GOAL TYPES : new rule  = " + printRuleWithTypes( rid, cursor ) )

  logging.debug( "  SET GOAL TYPES : ...done." )


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
# check if the input rule is fully typed, meaning
# all goal atts are typed and all subgoal atts are typed.
def isFullyTyped( rid, cursor ) :

  # ================================================= #
  # grab rule name for clarity of explanation

  cursor.execute( "SELECT goalName FROM Rule WHERE rid=='" + rid + "'" )
  goalName = cursor.fetchone()
  goalName = tools.toAscii_str( goalName )

  logging.debug( "  IS FULLY TYPED : running process on rule " + printRuleWithTypes( rid, cursor ) )

  # ===================================================== #
  # get the rule att data for the given rid

  currRuleAttData = dumpers.singleRuleAttDump( rid, cursor )

  # ===================================================== #
  # check of all goal attributes and all subgoal
  # attributes are fully typed

  # check goal atts
  goalAttData = currRuleAttData[ "goalAttData" ]
  for att in goalAttData :
    attID   = att[0]
    attName = att[1]
    attType = att[2]

    logging.debug( "  IS FULLY TYPED : att = " + str( att ) )

    if attType == "UNDEFINEDTYPE" :
      logging.debug( "  IS FULLY TYPED : goal atts returning False" )
      return False

  # check subgoal atts
  if not RELAX_SUBGOAL_TYPE_REQ :
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
def rewrite_to_datalog( argDict, factMeta, ruleMeta, cursor ) :

  logging.debug( "  REWRITE : running process..." )

  settings_path = argDict[ "settings" ]
  EOT           = argDict[ "EOT" ]

  # ----------------------------------------------------------------------------- #
  # dedalus rewrite

  logging.debug( "  REWRITE : calling dedalus rewrites..." )

  allMeta  = dedalusRewriter.rewriteDedalus( argDict, factMeta, ruleMeta, cursor )
  factMeta = allMeta[0]
  ruleMeta = allMeta[1]

  # be sure to fill in all the type info for the new rule definitions
  setTypes.setTypes( cursor )

  # ----------------------------------------------------------------------------- #
  # wilcard rewrites

#  logging.debug( "  REWRITE : calling wildcard rewrites..." )
#
#  try :
#    rewriteWildcards = tools.getConfig( settings_path, "DEFAULT", "REWRITE_WILDCARDS", bool )
#    if rewriteWildcards :
#      rewriteNegativeSubgoalsWithWildcards.rewriteNegativeSubgoalsWithWildcards( cursor )
#
#  except ConfigParser.NoOptionError :
#    print "WARNING : no 'REWRITE_WILDCARDS' defined in 'DEFAULT' section of settings.ini ...running without wildcard rewrites."
#    pass

  # ----------------------------------------------------------------------------- #
  # dml rewrites

  try :
    RUN_DML = tools.getConfig( settings_path, "DEFAULT", "DML", bool )
    if RUN_DML :

      ruleMeta = dml.dml( factMeta, ruleMeta, cursor ) # returns new ruleMeta

      # be sure to fill in all the type info for the new rule definitions
      setTypes.setTypes( cursor )

  except ConfigParser.NoOptionError :
    logging.info( "WARNING : no 'DML' defined in 'DEFAULT' section of settings file ...running without dml rewrites" )
    pass

  # ----------------------------------------------------------------------------- #
  # provenance rewrites

  logging.debug( "  REWRITE : before prov dump :" )
  for rule in ruleMeta :
    logging.debug( "  REWRITE : r = " + printRuleWithTypes( rule.rid, cursor ) )

  logging.debug( "  REWRITE : calling provenance rewrites..." )

  # add the provenance rules to the existing rule set
  ruleMeta.extend( provenanceRewriter.rewriteProvenance( ruleMeta, cursor ) )

  for rule in ruleMeta :
    logging.debug( "  REWRITE : r = " + dumpers.reconstructRule( rule.rid, rule.cursor ) )

  # be sure to fill in all the type info for the new rule definitions
  setTypes.setTypes( cursor )

  # ----------------------------------------------------------------------------- #

  logging.debug( "  REWRITE : ...done." )

  return [ factMeta, ruleMeta ]


#################
#  REWRITE DML  #
#################
# apply the dml rewriting procedure
def rewrite_dml( argDict, factMeta, ruleMeta, cursor ) :

  logging.debug( "  REWRITE DML : running process..." )

  settings_path = argDict[ "settings" ]
  evaluator     = argDict[ "evaluator" ]

  try :
    RUN_DML = tools.getConfig( settings_path, "DEFAULT", "DML", bool )
    if RUN_DML :

      ruleMeta = dml.dml( factMeta, ruleMeta, cursor ) # returns new ruleMeta

      # ------------------------------------------- #
      #                 DERIVE TYPES                #
      # ------------------------------------------- #
      # all rules now exist in the IR database.
      # fire the logic for deriving data types for all
      # goals and subgoals per rule.
    
      setTypes.setTypes( cursor )

      # ------------------------------------------------------------- #
      # translate IR into datalog

      if evaluator == "c4" :

        logging.debug( "  REWRITE DML : launching c4 evaluation..." )

        allProgramLines = c4_translator.c4datalog( argDict, cursor )

        logging.debug( "  REWRITE DML : ...done with c4 evaluation." )

      elif evaluator == "pyDatalog" :
        allProgramLines = pydatalog_translator.getPyDatalogProg( cursor )

      # ------------------------------------------------------------- #

      logging.debug( "  REWRITE DML : returning allProgramLines = " + str( allProgramLines ) )
      return [ allProgramLines, factMeta, ruleMeta ]

  except ConfigParser.NoOptionError :
    logging.info( "WARNING : no 'DML' defined in 'DEFAULT' section of settings file ...running without dml rewrites" )
    pass


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

  complete_file_path = tools.compile_full_program_and_save( fileList )

  #logging.warning( "  TRANSLATE DEDALUS : translating files one at a time might be good if order matters." )
  logging.debug( "  TRANSLATE DEDALUS : complete_file_path = " + complete_file_path )
  allData = runTranslator( cursor, complete_file_path, argDict, evaluator )

  datalogLines = allData[ 0 ]
  factMeta     = allData[ 1 ]
  ruleMeta     = allData[ 2 ]

  # ----------------------------------------------------------------- #

  logging.debug( "  TRANSLATE DEDALUS : datalogLines = " + str( datalogLines ) )
  return datalogLines


#########
#  EOF  #
#########
