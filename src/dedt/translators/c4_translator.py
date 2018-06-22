#!/usr/bin/env python

'''
c4_translator.py
   Tools for producig c4 datalog programs from the IR in the dedt compiler.
'''

import copy
import inspect, logging, os, re, string, sqlite3, sys
import dumpers_c4
import ConfigParser

# ------------------------------------------------------ #
# import sibling packages HERE!!!
if not os.path.abspath( __file__ + "/../../.." ) in sys.path :
  sys.path.append( os.path.abspath( __file__ + "/../../.." ) )

from utils import tools
from dedt  import Rule
# ------------------------------------------------------ #


#################
#  GET C4 LINE  #
#################
def get_c4_line( data, conversion_type ) :

  if conversion_type == "rule" :
    rel_name = data[ "relationName" ]
    goal_att_list = data[ "goalAttList" ]
    subgoal_strs = []
    for sub in data[ "subgoalListOfDicts" ] :
      sub_name     = sub[ "subgoalName" ]
      sub_polarity = sub[ "polarity" ]
      sub_att_list = sub[ "subgoalAttList" ]
      subgoal_strs.append( sub_polarity + " " + sub_name + "(" + ",".join( sub_att_list ) + ")" )
  
    # order negative subgoals last
    pos = []
    neg = []
    for sub in subgoal_strs :
      if sub.startswith( "notin " ) :
        neg.append( sub )
      else :
        pos.append( sub )
    subgoal_strs = copy.deepcopy( pos + neg )

    head = rel_name + "(" + ",".join( goal_att_list ) + ")"
    body = ""
    for i in range( 0, len( subgoal_strs ) ) :
      sub = subgoal_strs[ i ]
      body += sub
      if i < len( subgoal_strs )-1 :
        body += ","
  
    # add eqns
    for i in range( 0, len( data[ "eqnDict" ] ) ) :
      if i == 0 :
        body += ","
      eqn = data[ "eqnDict" ].keys()[i]
      body += eqn
      if i < len( data[ "eqnDict" ] )-1 :
        body += ","

    return head + ":-" + body + ";"

  elif conversion_type == "fact" :
    rel_name  = data[ "relationName" ]
    data_list = data[ "dataList" ]
    return rel_name + "(" + ",".join( data_list ) + ");"

  else :
    raise ValueError( "unrecognized conversion type '" + conversion_type + "'. aborting..." )


#####################
#  EXISTING DEFINE  #
#####################
# input subgoal name and list of currently accumulated define statements
# determine if a define already exists for the relation indicated by the subgoal
# output boolean

def existingDefine( name, definesNames ) :

  if name in definesNames :
    return True
  else :
    return False


################
#  C4 DATALOG  #
################
# input cursor for IR db
# output the full path for the intermediate file containing the c4 datalog program.

def c4datalog( argDict, cursor ) :

  logging.debug( "  C4 DATALOG : running process..." )

  goalName         = None
  provGoalNameOrig = None

  tableListStr   = "" # collect all table names delmited by a single comma only.
  tableListArray = []

  # ----------------------------------------------------------- #
  # create goal defines

  # get all rids
  cursor.execute( "SELECT rid FROM Rule" )
  ridList = cursor.fetchall()
  ridList = tools.toAscii_list( ridList )

  definesNames = []
  definesList  = []
  # ////////////////////////////////////////////////////////// #
  # populate defines list for rules
  for rid in ridList :
    newDefine   = ""

    # get goal name
    cursor.execute( "SELECT goalName FROM Rule WHERE rid = '" + rid + "'" )
    goalName = cursor.fetchone()
    goalName = tools.toAscii_str( goalName )

    # if it's a prov rule, get the original goal name
    provGoalNameOrig = None
    if "_prov" in goalName :
      provGoalNameOrig = goalName.split( "_prov" )
      provGoalNameOrig = provGoalNameOrig[0]

    # populate table information collection structures
    tableListStr += goalName + ","
    tableListArray.append( goalName )

    # ////////////////////////////////////////////////////////// #
    # populate defines list for rule goals
    logging.debug( "In c4datalog: definesList = " + str(definesList) )

    if not existingDefine( goalName, definesNames ) : # prevent duplicates

      # get goal attribute list
      cursor.execute( "SELECT attID,attType From GoalAtt WHERE rid = '" + rid + "'" )
      goalAttList = cursor.fetchall()
      goalAttList = tools.toAscii_multiList( goalAttList )

      logging.debug( "* goalName = " + goalName + ", goalAttList " + str( goalAttList ) )

      # populate type list for rule
      typeList = []
      for k in range(0,len(goalAttList)) :
        att     = goalAttList[ k ]
        attID   = att[0]
        attType = att[1]

        typeList.append( attType )

      # populate new c4 define statement
      newDefine = ""
      newDefine += "define("
      newDefine += goalName
      newDefine += ",{"

      for i in range(0,len(typeList)) :
        newDefine += typeList[i]
        if i < len(typeList) - 1 :
          newDefine += ","
        else :
          newDefine += "});" + "\n"

      # save new c4 define statement
      if not newDefine in definesList :
        definesNames.append( goalName )
        definesList.append( newDefine )
    # ////////////////////////////////////////////////////////// #

  # ----------------------------------------------------------- #
  # create fact defines

  # get all fact ids
  cursor.execute( "SELECT fid FROM Fact" )
  fidList = cursor.fetchall()
  fidList = tools.toAscii_list( fidList )

  for fid in fidList :

    # get goal name
    cursor.execute( "SELECT name FROM Fact WHERE fid = '" + fid + "'" )
    factName = cursor.fetchone()
    factName = tools.toAscii_str( factName )

    logging.debug( "**> factName = " + factName )

    logging.debug( "In c4datalog: definesList = " + str(definesList) )

    if not existingDefine( factName, definesNames ) : # prevent duplicates

      # populate table string
      tableListStr += factName + ","
      tableListArray.append( factName )

      # get goal attribute list
      cursor.execute( "SELECT dataID,dataType From FactData WHERE fid = '" + fid + "'" )
      factAttList = cursor.fetchall()
      factAttList = tools.toAscii_multiList( factAttList )

      logging.debug( "* factName = " + factName + ", factAttList " + str( factAttList ) )

      # populate type list for fact
      typeList = []
      for k in range(0,len(factAttList)) :
        att     = factAttList[ k ]
        attID   = att[0]
        attType = att[1]

        typeList.append( attType )

      # check for time argument
      #cursor.execute( "SELECT timeArg FROM Fact WHERE fid='" + fid + "'" )
      #timeArg = cursor.fetchone()
      #timeArg = tools.toAscii_str( timeArg )

      #if timeArg :
      #  typeList.append( "int" )

      # populate new c4 define statement
      newDefine = ""
      newDefine += "define("
      newDefine += factName
      newDefine += ",{"

      for i in range(0,len(typeList)) :
        newDefine += typeList[i]
        if i < len(typeList) - 1 :
          newDefine += ","
        else :
          newDefine += "});" + "\n"

      # save new c4 define statement
      if not newDefine in definesList :
        definesNames.append( factName )
        definesList.append( newDefine )
  # ////////////////////////////////////////////////////////// #

  # ----------------------------------------------------------- #
  # add clock define

  definesList.append( "define(clock,{string,string,int,int});\n" )
  tableListStr += "clock,"
  tableListArray.append( "clock" )

  # ----------------------------------------------------------- #
  # add not_clock define

  #definesList.append( "define(not_clock,{string,string,int,int});\n" )
  #tableListStr += "not_clock,"
  #tableListArray.append( "not_clock" )

  # ----------------------------------------------------------- #
  # add crash define

  definesList.append( "define(crash,{string,string,int,int});\n" )
  tableListStr += "crash,"
  tableListArray.append( "crash" )

  # ----------------------------------------------------------- #
  # add facts

  cursor.execute( "SELECT fid FROM Fact" )
  fidList = cursor.fetchall()
  fidList = tools.toAscii_list( fidList )

  factList = []
  for fid in fidList :
    newFact = dumpers_c4.dumpSingleFact_c4( fid, cursor )
    factList.append( newFact )

  # ----------------------------------------------------------- #
  # add clock facts

  clockFactList = dumpers_c4.dump_clock( cursor )

  logging.debug( "c4_translator: clockFactList = " + str( clockFactList ) )

  # ----------------------------------------------------------- #
  # add crash facts

  crashFactList = dumpers_c4.dump_crash( cursor )
  #crashFactList = []

  #print crashFactList
  #tools.bp( __name__, inspect.stack()[0][3], "blah" )

  #logging.debug( "c4_translator: crashFactList = " + str( crashFactList ) )

  # ----------------------------------------------------------- #
  # add rules

  cursor.execute( "SELECT rid FROM Rule" )
  ridList = cursor.fetchall()
  ridList = tools.toAscii_list( ridList )

  ruleList = []
  for rid in ridList :

    # verify data type compatibility for rules with equations
    #verificationResults = tools.checkDataTypes( rid, cursor ) # returns array

    #yesCompatible = verificationResults[0]
    #offensiveEqn  = verificationResults[1]
    #lhsType       = verificationResults[2]
    #rhsType       = verificationResults[3]

    #if yesCompatible :
    if True :
      newRule = dumpers_c4.dumpSingleRule_c4( rid, cursor )
      ruleList.append( newRule )

    else : # data types are incompatible
      # throw error and abort
      tools.bp( __name__, inspect.stack()[0][3], "FATAL ERROR: DATA TYPE INCOMPATABILITY\nAttempting to evaluate an equation in which variables possess incomparable types.\nERROR in line: " + dumpers_c4.dumpSingleRule_c4( rid, cursor )+ "\nERROR in eqn: " + offensiveEqn + "\nlhs is of type " + lhsType + " and rhs is of type " + rhsType )

  # ------------------------------------------------------ #
  # grab the next rule handling method

  try :
    NEXT_RULE_HANDLING = tools.getConfig( argDict[ "settings" ], \
                                          "DEFAULT", \
                                          "NEXT_RULE_HANDLING", \
                                          str )

  except ConfigParser.NoOptionError :
    logging.info( "WARNING : no 'NEXT_RULE_HANLDING' defined in 'DEFAULT' section of settings file." )
    tools.bp( __name__, inspect.stack()[0][3], \
             "FATAL ERROR : NEXT_RULE_HANDLING parameter not specified in DEFAULT section of settings file. use 'USE_AGGS', 'SYNC_ASSUMPTION', or 'USE_NEXT_CLOCK' only." )

  # sanity check next rule handling value
  if NEXT_RULE_HANDLING == "USE_AGGS" or \
     NEXT_RULE_HANDLING == "SYNC_ASSUMPTION" or \
     NEXT_RULE_HANDLING == "USE_NEXT_CLOCK" :
    pass
  else :
    tools.bp( __name__, inspect.stack()[0][3], \
              "FATAL ERROR : unrecognized NEXT_RULE_HANDLING value '" + NEXT_RULE_HANDLING + "'. use 'USE_AGGS', 'SYNC_ASSUMPTION', or 'USE_NEXT_CLOCK' only." )

  # ----------------------------------------------------------- #
  # add next_clock, if necessary

  if NEXT_RULE_HANDLING == "USE_NEXT_CLOCK" :

    # ------------------------------------------------------ #
    # add define

    definesList.append( "define(next_clock,{string,string,int,int});\n" )
    tableListStr += "next_clock,"
    tableListArray.append( "next_clock" )

    # ------------------------------------------------------ #
    # add next_clock facts for all synchronous facts appearing clock

    next_clock_factList = []
    for cfact in clockFactList :
      if isSynchronous( cfact ) :
        next_clock_fact = "next_" + cfact
        next_clock_factList.append( next_clock_fact )

  # ----------------------------------------------------------- #
  # save table list

  logging.debug( "*******************************************" )
  logging.debug( "table list str :\n" + str( tableListStr ) )
  logging.debug( "table list array :\n" + str( tableListArray ) )

  # ----------------------------------------------------------- #
  # collect program statements

  logging.debug( "*******************************************" )
  logging.debug( "definesList :\n" + str( definesList ) )
  logging.debug( "*******************************************" )
  logging.debug( "factList :\n" + str( factList ) )
  logging.debug( "*******************************************" )
  logging.debug( "ruleList :\n" + str( ruleList ) )

  # NOTE: listOfStatementLists controls the ordering of statements
  #       in the final c4 program.
  if NEXT_RULE_HANDLING == "USE_NEXT_CLOCK" :
    listOfStatementLists = [ definesList, \
                             ruleList, \
                             factList, \
                             crashFactList, \
                             next_clock_factList, \
                             clockFactList ]
  else :
    #listOfStatementLists = [ definesList, \
    #                         factList, \
    #                         ruleList, \
    #                         clockFactList ]
    listOfStatementLists = [ definesList, \
                             ruleList, \
                             factList, \
                             crashFactList, \
                             clockFactList ]

  program = tools.combineLines( listOfStatementLists )

  # break down into list of individual statements
  allProgramLines = []
  for group in listOfStatementLists :
    for statement in group :
      allProgramLines.append( statement.rstrip() )

  # remove duplicates
  tableListArray = set( tableListArray )
  tableListArray = list( tableListArray )

  logging.debug( "  C4 DATALOG : ...done." )
  return [ allProgramLines, tableListArray ]


####################
#  IS SYNCHRONOUS  #
####################
# check if the input clock fact is synchronous
def isSynchronous( cfact ) :

  cfact = cfact.replace( "clock(", "" )
  cfact = cfact.replace( ");","" )

  cfact = cfact.split( "," )
  send  = cfact[2]
  deliv = cfact[3]

  if int( deliv ) == int( send ) + 1 :
    return True
  else :
    return False


#########
#  EOF  #
#########
