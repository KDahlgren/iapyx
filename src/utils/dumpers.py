#!/usr/bin/env python

'''
dumpers.py
   Methods for dumping specific contents from the database.
'''

import inspect, logging, os, sys
import tools

# ------------------------------------------------------ #
# import sibling packages HERE!!!
# ------------------------------------------------------ #

#############
#  GLOBALS  #
#############
#DUMPERS_DEBUG = tools.getConfig( "UTILS", "DUMPERS_DEBUG", bool )
DUMPERS_DEBUG = False

##################
#  PROGRAM DUMP  #
##################
# dump entire (preformatted) program to stdout
def programDump( cursor ) :
  factDump(  cursor )
  clockDump( cursor )
  ruleDump(  cursor )


###################
#  RULE ATT DUMP  #
###################
# dump a dictionary of goal attribute and subgoal 
# attribute data for all rules mapping attributes to data types
def ruleAttDump( cursor ) :

  ruleAttData = {}

  # ================================================= #
  # grab all rule ids

  cursor.execute( "SELECT rid FROM Rule" )
  ridList = cursor.fetchall()
  ridList = tools.toAscii_list( ridList )

  for rid in ridList :

    # ================================================= #
    # collect rule att data

    currRuleAttData = singleRuleAttDump( rid, cursor )

    # ================================================= #
    # save attribute data per rule

    ruleAttData[ rid ] = currRuleAttData

  return ruleAttData


##########################
#  SINGLE RULE ATT DUMP  #
##########################
# dump the goal and subgoal attribute info
# for the given rule
def singleRuleAttDump( rid, cursor ) :

  currRuleAttData = {}

  # ================================================= #
  # grab rule name for clarity of explanation

  cursor.execute( "SELECT goalName FROM Rule WHERE rid=='" + rid + "'" )
  goalName = cursor.fetchone()
  goalName = tools.toAscii_str( goalName )

  currRuleAttData[ "goalName" ] = goalName

  # ================================================= #
  # grab all goal atts and att types

  cursor.execute( "SELECT attID,attName,attType FROM GoalAtt WHERE rid=='" + rid + "'" )
  goalAttData = cursor.fetchall()
  goalAttData = tools.toAscii_multiList( goalAttData )

  goalAttTypeMappingArrays = []
  for i in range( 0, len( goalAttData ) ) :
    attID   = goalAttData[i][0]
    attName = goalAttData[i][1]
    attType = goalAttData[i][2]
    goalAttTypeMappingArrays.append( [ attID, attName, attType ] )

  currRuleAttData[ "goalAttData" ] = goalAttTypeMappingArrays

  # ================================================= #
  # grab all subgoal atts and att types
  # [ [ subgoal1, [ [ data1, type1 ], ..., [ dataM, typeM ] ] ], 
  #    ..., 
  #   [ subgoalK, [ [ data1, type1 ], ..., [ dataN, typeN ] ] ] ]

  # grab all subgoal ids
  cursor.execute( "SELECT sid FROM Subgoals WHERE rid=='" + rid + "'" )
  sidList = cursor.fetchall()
  sidList = tools.toAscii_list( sidList )

  subgoalAttDataMaps = []
  for sid in sidList :

    # grab the subgoal name for clarity of explanation
    cursor.execute( "SELECT subgoalName FROM Subgoals WHERE rid=='" + rid + "' AND sid=='" + sid + "'" )
    subgoalName = cursor.fetchone()
    subgoalName = tools.toAscii_str( subgoalName )

    # grab subgoal att list and types
    cursor.execute( "SELECT attID,attName,attType FROM SubgoalAtt WHERE rid=='" + rid + "' AND sid=='" + sid + "'" )
    subgoalAttData = cursor.fetchall()
    subgoalAttData = tools.toAscii_multiList( subgoalAttData )

    # grab attribute maps per subgoal and store in arrays
    subgoalAttTypeMappingArrays = []
    for i in range( 0, len( subgoalAttData ) ) :
      attID   = subgoalAttData[i][0]
      attName = subgoalAttData[i][1]
      attType = subgoalAttData[i][2]
      subgoalAttTypeMappingArrays.append( [ attID, attName, attType ] )

    # save to subgoalAttData
    subgoalAttDataMaps.append( [ sid, subgoalName, subgoalAttTypeMappingArrays ] )

  currRuleAttData[ "subgoalAttData" ] = subgoalAttDataMaps

  # ================================================= #

  return currRuleAttData


###############
#  RULE DUMP  #
###############
# input database cursor
# output nothing, print all rules to stdout
def ruleDump( cursor ) :

  logging.debug( "  RULE DUMP : running process..." )

  rules = []

  # --------------------------------------------------------------- #
  #                           GOALS                                 #

  # get all rule ids
  cursor.execute( "SELECT rid FROM Rule" )
  ruleIDs = cursor.fetchall()
  ruleIDs = tools.toAscii_list( ruleIDs )

  # iterate over rule ids
  newRule = []
  for i in ruleIDs :
    cursor.execute( "SELECT goalName FROM Rule WHERE rid == '" + i + "'" ) # get goal name
    goalName    = cursor.fetchone()
    goalName    = tools.toAscii_str( goalName )

    # get list of attribs in goal
    goalList    = cursor.execute( "SELECT attName FROM GoalAtt WHERE rid == '" + i + "'" )# list of goal atts
    goalList    = cursor.fetchall()
    goalList    = tools.toAscii_list( goalList )

    # get goal time arg
    goalTimeArg = ""
    cursor.execute( "SELECT goalTimeArg FROM Rule WHERE rid == '" + i + "'" )
    goalTimeArg = cursor.fetchone()
    goalTimeArg = tools.toAscii_str( goalTimeArg )

    # convert goal info to pretty string
    newRule.append( goalName + "(" )
    for j in range(0,len(goalList)) :
      if j < (len(goalList) - 1) :
        newRule.append( goalList[j] + "," )
      else :
        newRule.append( goalList[j] + ")" )
    if not goalTimeArg == "" :
      newRule.append( "@" + goalTimeArg + ":-" )
    else :
      newRule.append( ":-" )

    # --------------------------------------------------------------- #
    #                         SUBGOALS                                #

    # get list of sids for the subgoals of this rule
    cursor.execute( "SELECT sid FROM Subgoals WHERE rid == '" + str(i) + "'" ) # get list of sids for this rule
    subIDs = cursor.fetchall()
    subIDs = tools.toAscii_list( subIDs )

    # iterate over subgoal ids
    for k in range(0,len(subIDs)) :
      s = subIDs[k]

      # get subgoal name
      cursor.execute( "SELECT subgoalName FROM Subgoals WHERE rid == '" + str(i) + "' AND sid == '" + str(s) + "'" )
      subgoalName = cursor.fetchone()

      if not subgoalName == None :
        subgoalName = tools.toAscii_str( subgoalName )

        # --------------------------------------- #
        # get subgoal attribute list
        subAtts = cursor.execute( "SELECT attName FROM SubgoalAtt WHERE rid == '" + i + "' AND sid == '" + s + "'" )
        subAtts = cursor.fetchall()
        subAtts = tools.toAscii_list( subAtts )

        # --------------------------------------- #
        # get subgoal time arg
        cursor.execute( "SELECT subgoalTimeArg FROM Subgoals WHERE rid == '" + i + "' AND sid == '" + s + "'" )
        subTimeArg = cursor.fetchone()
        subTimeArg = tools.toAscii_str( subTimeArg )

        # --------------------------------------- #
        # get subgoal additional args
        cursor.execute( "SELECT subgoalPolarity FROM Subgoals WHERE rid == '" + i + "' AND sid == '" + s + "'" )
        subAddArg = cursor.fetchone()
        subAddArg = tools.toAscii_str( subAddArg )
        if subAddArg == "notin" :
          subAddArg += " "
          newRule.append( " " + subAddArg )

        # all subgoals have a name and open paren
        newRule.append( subgoalName + "(" )

        # add in all attributes
        for j in range(0,len(subAtts)) :
          if j < (len(subAtts) - 1) :
            newRule.append( subAtts[j] + "," )
          else :
            newRule.append( subAtts[j] + ")" )

        # conclude with time arg, if applicable
        if not subTimeArg == "" :
          newRule.append( "@" + subTimeArg )

        # cap with a comma, if applicable
        if k < len( subIDs ) - 1 :
          newRule.append( "," )

    # --------------------------------------------------------------- #
    #                         EQUATIONS                               #

    cursor.execute( "SELECT eid,eqn FROM Equation WHERE rid=='" + i + "'" ) # get list of eids for this rule
    eqnList = cursor.fetchall()
    eqnList = tools.toAscii_multiList( eqnList )

    for e in eqnList :
      eid = e[0]
      eqn = e[1]
      newRule.append( "," + str(eqn) )

    # --------------------------------------------------------------- #

    newRule.append( ";" ) # end all rules with a semicolon
    rules.append( newRule )
    newRule = []

  logging.debug( "  RULE DUMP : rules = " + str( rules ) )

  returnRules = []
  for r in rules :
    returnRules.append( ''.join(r) )

  return returnRules


###############
#  FACT DUMP  #
###############
# input database cursor
# output nothing, print all facts to stdout
def factDump( cursor ) :

  logging.debug( "  FACT DUMP : running process..." )

  facts = []

  # get all fact ids
  cursor.execute( "SELECT fid FROM Fact" )
  factIDs = cursor.fetchall()
  factIDs = tools.toAscii_list( factIDs )

  # iterate over fact ids
  newFact = []
  for i in factIDs :
    cursor.execute( "SELECT name FROM Fact WHERE fid == '" + str(i) + "'" ) # get fact name
    factName = cursor.fetchone()
    factName = tools.toAscii_str( factName )

    # get list of attribs in fact
    factList = cursor.execute( "SELECT data FROM FactData WHERE fid == '" + str(i) + "'" ) # list of fact atts
    factList = cursor.fetchall()
    factList = tools.toAscii_list( factList )

    logging.debug( "  FACT DUMP : factList = " + str( factList ) )

    # get fact time arg
    factTimeArg = ""
    cursor.execute( "SELECT timeArg FROM Fact WHERE fid == '" + i + "'" )
    factTimeArg = cursor.fetchone()
    factTimeArg = tools.toAscii_str( factTimeArg )

    # convert fact info to formatted string
    newFact.append( factName + "(" )
    for j in range(0,len(factList)) :

      if j < (len(factList) - 1) :
        newFact.append( factList[j] + "," )
      else :
        newFact.append( factList[j] + ")" )

    if not factTimeArg == "" :
      newFact.append( "@" + factTimeArg )

    newFact.append( ";" ) # end all facts with a semicolon
    facts.append( newFact )
    newFact = []


  returnFacts = []
  for f in facts :
    returnFacts.append( ''.join(f) )

  logging.debug( "  FACT DUMP : returning returnFacts = " + str( returnFacts ) )
  return returnFacts


##############
#  EQN DUMP  #
##############
# input database cursor
# output eqn data
def eqnDump( cursor ) :

  logging.debug( "  EQN DUMP : running process..." )

  eqns = {}

  # get all eqn ids
  cursor.execute( "SELECT eid FROM Equation" )
  eqnIDs = cursor.fetchall()
  eqnIDs = tools.toAscii_list( eqnIDs )

  # iterate over eqn ids
  for i in eqnIDs :

    # get eqn string
    cursor.execute( "SELECT eqn FROM Equation WHERE eid == '" + str(i) + "'" )
    eqnStr = cursor.fetchone()
    eqnStr = tools.toAscii_str( eqnStr )

    # get list of variables in the equation
    cursor.execute( "SELECT var FROM EquationVars WHERE eid == '" + str(i) + "'" ) # list of fact atts
    varList = cursor.fetchall()
    varList = tools.toAscii_list( varList )

    eqns[ eqnStr ] = varList 

  logging.debug( "  EQN DUMP : eqns = " + str( eqns ) )

  return eqns


################
#  CLOCK DUMP  #
################
# input db cursor
# output nothing, print all clock entries to stdout
def clockDump( cursor ) :

  print "********************\nProgram Clock :"
  clock = cursor.execute('''SELECT * FROM Clock''')

  for c in clock :
    print c


######################
#  RECONSTRUCT RULE  #
######################
def reconstructRule( rid, cursor ) :

  if DUMPERS_DEBUG :
    print "... running reconstructRule ..."

  rule = ""

  # -------------------------------------------------------------- #
  #                           GOAL                                 #
  # -------------------------------------------------------------- #
  #
  # get goal name
  cursor.execute( "SELECT goalName FROM Rule WHERE rid == '" + str( rid ) + "'" ) # get goal name
  goalName    = cursor.fetchone()
  goalName    = tools.toAscii_str( goalName )

  # get list of attribs in goal
  goalList    = cursor.execute( "SELECT attName FROM GoalAtt WHERE rid == '" + str( rid ) + "'" )# list of goal atts
  goalList    = cursor.fetchall()
  goalList    = tools.toAscii_list( goalList )

  # get goal time arg
  goalTimeArg = ""
  cursor.execute( "SELECT goalTimeArg FROM Rule WHERE rid == '" + str( rid ) + "'" )
  goalTimeArg = cursor.fetchone()
  goalTimeArg = tools.toAscii_str( goalTimeArg )

  # convert goal info to string
  rule += goalName + "("
  for j in range(0,len(goalList)) :
    if j < (len(goalList) - 1) :
      rule += goalList[j] + ","
    else :
      rule += goalList[j] + ")"
  if not goalTimeArg == "" :
    rule += "@" + goalTimeArg + ":-"
  else :
    rule += " <= "

  # --------------------------------------------------------------- #
  #                         SUBGOALS                                #
  # --------------------------------------------------------------- #
  #

  # get list of sids for the subgoals of this rule
  cursor.execute( "SELECT sid FROM Subgoals WHERE rid == '" + str( rid ) + "'" ) # get list of sids for this rule
  subIDs = cursor.fetchall()
  subIDs = tools.toAscii_list( subIDs )

  # iterate over subgoal ids
  for k in range(0,len(subIDs)) :
    newSubgoal = ""

    s = subIDs[k]

    # get subgoal name
    cursor.execute( "SELECT subgoalName FROM Subgoals WHERE rid == '" + str(rid) + "' AND sid == '" + str(s) + "'" )
    subgoalName = cursor.fetchone()

    if not subgoalName == None :
      subgoalName = tools.toAscii_str( subgoalName )

      # get subgoal attribute list
      subAtts = cursor.execute( "SELECT attName FROM SubgoalAtt WHERE rid == '" + str( rid ) + "' AND sid == '" + s + "'" )
      subAtts = cursor.fetchall()
      subAtts = tools.toAscii_list( subAtts )

      # get subgoal time arg
      cursor.execute( "SELECT subgoalTimeArg FROM Subgoals WHERE rid == '" + str( rid ) + "' AND sid == '" + s + "'" ) # get list of sids for this rule
      subTimeArg = cursor.fetchone() # assume only one additional arg
      subTimeArg = tools.toAscii_str( subTimeArg )

      # get subgoal additional args
      subAddArg = None
      cursor.execute( "SELECT subgoalPolarity FROM Subgoals WHERE rid == '" + str( rid ) + "' AND sid == '" + s + "'" ) # get list of sids for this rule
      subAddArg = cursor.fetchone() # assume only one additional arg
      if not subAddArg == "" :
        subAddArg = tools.toAscii_str( subAddArg )
        subAddArg += " "
        newSubgoal += subAddArg

      # all subgoals have a name and open paren
      newSubgoal += subgoalName + "("

      # add in all attributes
      for j in range(0,len(subAtts)) :
        if j < (len(subAtts) - 1) :
          newSubgoal += subAtts[j] + ","
        else :
          newSubgoal += subAtts[j] + ")"

      # cap with a comma, if applicable
      if k < len( subIDs ) - 1 :
        newSubgoal += ","

    rule += newSubgoal

  # --------------------------------------------------------------- #
  #                         EQUATIONS                               #
  # --------------------------------------------------------------- #

  cursor.execute( "SELECT eid,eqn FROM Equation WHERE rid=='" + str( rid ) + "'" ) # get list of eids for this rule
  eqnList = cursor.fetchall()
  eqnList = tools.toAscii_multiList( eqnList )

  for e in eqnList :
    eid = e[0]
    eqn = e[1]
    rule += "," + str(eqn)

  # --------------------------------------------------------------- #

  rule += " ;" # end all rules with a semicolon

  return rule


#####################
#  RULE TABLE DUMP  #
#####################
# dump the entire rule table to stdout
def ruleTableDump( cursor ) :

  cursor.execute( "SELECT * FROM Rule" )
  allRecords = cursor.fetchall()
  allRecords = tools.toAscii_multiList( allRecords )

  for rec in allRecords :
    print rec


#########################
#  GOAL ATT TABLE DUMP  #
#########################
# dump the entire GoalAtt table to stdout
def goalAttTableDump( cursor ) :

  cursor.execute( "SELECT * FROM GoalAtt" )
  allRecords = cursor.fetchall()
  allRecords = tools.toAscii_multiList( allRecords )

  for rec in allRecords :
    print rec


##################
#  GET ALL RIDS  #
##################
# extract all rule ids from the IR database
def getAllRIDs( cursor ) :

  cursor.execute( "SELECT rid FROM Rule" )
  ridList = cursor.fetchall()
  ridList = tools.toAscii_list( ridList )

  return ridList


#########
#  EOF  #
######### 
