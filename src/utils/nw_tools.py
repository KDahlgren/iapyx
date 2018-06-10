#/usr/bin/env python

'''
nw_tools.py
'''

import copy, inspect, logging, os, string, sys
import sympy
import itertools
import ConfigParser

import dm_time_att_replacement

# ------------------------------------------------------ #
# import sibling packages HERE!!!
if not os.path.abspath( __file__ + "/../.." ) in sys.path :
  sys.path.append( os.path.abspath( __file__ + "/../.." ) )

if not os.path.abspath( __file__ + "/../../dedt/translators" ) in sys.path :
  sys.path.append( os.path.abspath( __file__ + "/../../dedt/translators" ) )

from dedt       import Fact, Rule
from evaluators import c4_evaluator
from utils      import clockTools, tools, dumpers, setTypes

# ------------------------------------------------------ #

#############
#  GLOBALS  #
#############

arithOps   = [ "+", "-", "*", "/" ]
arithFuncs = [ "count", "avg", "min", "max", "sum" ]


#############################
#  DELETE UNUSED NOT RULES  #
#############################
def delete_unused_not_rules( ruleMeta, cursor ) :

  # delete unused rules
  COUNTER  = 0

  while unused_still_exist( ruleMeta ) :

    if COUNTER == 30 :
      sys.exit( "wtf man?" )

    # delete unused rules.
    not_used_indexes = []
    not_used_names   = []
    for i in range( 0, len( ruleMeta ) ) :
      rule = ruleMeta[ i ]
      if not is_used( rule, ruleMeta ) :
        not_used_indexes.append( i )
        not_used_names.append( rule.relationName )

    not_used_names = sorted( list( set( not_used_names ) ) )
    print not_used_names

    for i in reversed( not_used_indexes ) :
      rule = ruleMeta[ i ]
      logging.debug( "  DELETE UNUSED NOT RULES : deleting '" + dumpers.reconstructRule( rule.rid, rule.cursor ) + "'" )
      rule.delete_from_db()
      del ruleMeta[ i ]

    # delete rules with domain constraints derived from unused rules.
    collected_indexes = []
    for i in range( 0, len( ruleMeta ) ) : # discovery phase
      for rel in not_used_names :
        rule = ruleMeta[ i ]
        if "unidom_" + rel in [ sub[ "subgoalName" ] for sub in rule.subgoalListOfDicts ] :
          collected_indexes.append( i )

    collected_indexes = sorted( list( set( collected_indexes ) ) )

    for i in reversed( collected_indexes ) :
      rule = ruleMeta[ i ]
      logging.debug( "  DELETE UNUSED NOT RULES : deleting (2) '" + dumpers.reconstructRule( rule.rid, rule.cursor ) + "'" )
      ruleMeta[ i ].delete_from_db()
      del ruleMeta[ i ]

    COUNTER += 1

  #for r in ruleMeta :
  #  print str( r.rid ) + " : " + dumpers.reconstructRule( r.rid, r.cursor )
  #sys.exit( "blah" )

  return ruleMeta


########################
#  UNUSED STILL EXIST  #
########################
def unused_still_exist( ruleMeta ) :
  for rule in ruleMeta :
    if not rule.relationName == "post" and \
       not is_used( rule, ruleMeta ) :
      logging.debug( "  UNUSED STILL EXIST : '" + rule.relationName + "' is unused. returning True." )
      return True
  logging.debug( "  UNUSED STILL EXIST : returning False." )
  return False


#############
#  IS USED  #
#############
def is_used( target_rule, ruleMeta ) :
  logging.debug( "  IS USED : checking rule : " )
  logging.debug( "     " + str( target_rule.ruleData ) )
  logging.debug( "     " + dumpers.reconstructRule( target_rule.rid, target_rule.cursor ) )

  # keep post rules.
  if target_rule.relationName == "post" or \
     target_rule.relationName == "pre" :
    return True

  for rule in ruleMeta :
    if target_rule.relationName in \
       [ sub[ "subgoalName" ] for sub in rule.subgoalListOfDicts ] :
      logging.debug( "  IS USED : returning True." )
      return True
  logging.debug( "  IS USED : returning False." )

  return False


##############################
#  GET NEGATED SUBGOAL INFO  #
##############################
# get the list of names for negated IDB subgoals
def get_negated_subgoal_info( ruleMeta ) :

  cursor = ruleMeta[0].cursor # all cursors are the same

  # key on negated subgoal name, 
  # value on list of parent relation names negating that subgoal
  negatedNames_data = {}

  for rule in ruleMeta :

    logging.debug( "  GET NEGATED NAME LIST : rule.ruleData = " + str( rule.ruleData ) )

    parent_rule_name = rule.relationName
    parent_rule_rid  = rule.rid

    # ----------------------------------------- #
    # ignore domcomp rules
    if rule.relationName.startswith( "domcomp_" ) or \
       rule.relationName.startswith( "dom_" )     or \
       rule.relationName.startswith( "unidom_" )  or \
       rule.relationName.startswith( "exidom_" )  or \
       rule.relationName.startswith( "orig_" ) :
      pass

    else :

      # ----------------------------------------- #
      # grab subgoal dicts

      subgoalListOfDicts = copy.deepcopy( rule.ruleData[ "subgoalListOfDicts" ] )

      # ----------------------------------------- #
      # iterate over subgoal data

      for subgoalDict in subgoalListOfDicts :

        # save the rule object for the subgoal if the subgoal is negated and is idb
        if subgoalDict[ "polarity" ] == "notin" and isIDB( subgoalDict[ "subgoalName" ], cursor ) and \
           not subgoalDict[ "subgoalName" ].startswith( "orig_" ) :

          # ----------------------------------------- #
          # grab subgoal name

          logging.debug( "  GET NEGATED NAME LIST : adding '" + subgoalDict[ "subgoalName" ] + "' to negatedNames_data list" )

          if not subgoalDict[ "subgoalName" ] in negatedNames_data : # ignore duplicates created by prov rules
            negatedNames_data[ subgoalDict[ "subgoalName" ] ] = []
          negatedNames_data[ subgoalDict[ "subgoalName" ] ].append( [ parent_rule_name, parent_rule_rid ] )

  return negatedNames_data

####################################################################
#  GET RULE META SETS FOR RULES CORRESPONDING TO NEGATED SUBOGALS  #
####################################################################
# obtain the list of lists of rule objects corresponding to the idb definitions
# of idbs corresponding to negated subgoals in one or more rules
def getRuleMetaSetsForRulesCorrespondingToNegatedSubgoals( ruleMeta, cursor ) :

  logging.debug( "  GET RULE META FOR RULES CORRESPONDING TO NEGATED SUBGOALS : ruleMeta with len(ruleMeta) = " + str( len( ruleMeta ) ) )

  set_dict = {}

  # ----------------------------------------- #
  # get list of negated subgoal names

  negatedSubgoal_info = get_negated_subgoal_info( ruleMeta )

  # ----------------------------------------- #
  # initialize dictionary

  for name in negatedSubgoal_info :
    set_dict[ name ] = []

  # ----------------------------------------- #
  # iterate over rule meta

  for name in negatedSubgoal_info.keys() :
    for rule in ruleMeta :
      if rule.relationName == name :
        set_dict[ name ].append( rule )

  # ----------------------------------------- #
  # convert dictionary into a list of lists

  logging.debug( "  GET RULE META FOR RULES CORRESPONDING TO NEGATED SUBGOALS : set_dict = " + str( set_dict ) )

  targetRuleMetaSets = []
  for name in set_dict :
    targetRuleMetaSets.append( [ negatedSubgoal_info[ name ], set_dict[ name ] ] )

  for r in targetRuleMetaSets :
    logging.debug( "++++++++" )
    parent_list   = r[ 0 ]
    rule_obj_list = r[ 1 ]
    logging.debug( "  GET RULE META FOR RULES CORRESPONDING TO NEGATED SUBGOALS : parent_list   : " + str( parent_list ) )
    logging.debug( "  GET RULE META FOR RULES CORRESPONDING TO NEGATED SUBGOALS : rule_obj_list :" )
    for p in rule_obj_list :
      logging.debug( "    " + str( dumpers.reconstructRule( p.rid, p.cursor ) ) )

  # returns an array of arrays of arrays of parent rule strings and rule objects
  # [ [ [ "missing_log" ], [ log_obj_1, ...] ], ... ]
  return targetRuleMetaSets

############
#  IS IDB  #
############
# check if the given string corresponds to the name of a rule in an input program.
# if so, then the string corresponds to an IDB relation
def isIDB( subgoalName, cursor ) :

  cursor.execute( "SELECT rid FROM Rule WHERE goalName='" + subgoalName + "'" )
  rids = cursor.fetchall()
  rids = tools.toAscii_list( rids )

  if len( rids ) > 0 :
    return True
  else :
    return False

###############################
#  RULE CONTAINS NEGATED IDB  #
###############################
# check if the given rule contains a negated IDB
def ruleContainsNegatedIDB( rid, cursor ) :

  cursor.execute( "SELECT goalName FROM Rule WHERE rid=='" + str( rid ) + "'" )
  goalName = cursor.fetchone()
  goalName = tools.toAscii_str( goalName )

  if goalName.startswith( "domcomp_" ) or \
     goalName.startswith( "dom_" )     or \
     goalName.startswith( "unidom_" )  or \
     goalName.startswith( "exidom_" )  or \
     goalName.startswith( "orig_" ) :
    return False

  cursor.execute( "SELECT subgoalName FROM Subgoals WHERE rid='" + str( rid ) + "' AND subgoalPolarity=='notin'" )
  negatedSubgoals = cursor.fetchall()
  negatedSubgoals = tools.toAscii_list( negatedSubgoals )

  flag = False

  for subgoalName in negatedSubgoals :

    # skip these subgoals
    if subgoalName.startswith( "domcomp_" ) or \
       subgoalName.startswith( "dom_" )     or \
       subgoalName.startswith( "unidom_" )  or \
       subgoalName.startswith( "exidom_" )  or \
       subgoalName.startswith( "orig_" ) :
      pass

    elif isIDB( subgoalName, cursor ) :
      logging.debug( "  RULE CONTAINS NEGATED IDB : this one --> " + subgoalName  )
      flag = True

  return flag

#################################
#  STILL CONTAINS NEGATED IDBS  #
#################################
# check if new rules contain negated IDBs
def stillContainsNegatedIDBs( ruleMeta, cursor ) :

  for rule in ruleMeta :
    if not rule.relationName.startswith( "domcomp_" ) and \
       not rule.relationName.startswith( "dom_" )     and \
       not rule.relationName.startswith( "unidom_" )  and \
       not rule.relationName.startswith( "exidom_" )  and \
       not rule.relationName.startswith( "orig_" ) :
      if ruleContainsNegatedIDB( rule.rid, cursor ) :
        logging.debug( "  STILL CONTAINS NEGATED IDBs : rule contains negated idb : " + dumpers.reconstructRule( rule.rid, cursor ) )
        return True

  return False


####################
#  REMAINING IDBS  #
####################
# check if new rules contain negated IDBs
def remainingIDBs( ruleMeta, cursor ) :

  remainingRulesWIDBs = []

  for rule in ruleMeta :
    if not rule.relationName.startswith( "domcomp_" ) and \
       not rule.relationName.startswith( "dom_" )     and \
       not rule.relationName.startswith( "unidom_" )  and \
       not rule.relationName.startswith( "exidom_" )  and \
       not rule.relationName.startswith( "orig_" ) :
      if ruleContainsNegatedIDB( rule.rid, cursor ) :
        remainingRulesWIDBs.append( dumpers.reconstructRule( rule.rid, cursor ) )

  return remainingRulesWIDBs

#####################
#  IDENTICAL RULES  #
#####################
# check if the input rules are identical
def identicalRules( rule1, rule2 ) :

  if rule1.rid == rule2.rid :
    return True

  else :
    return False

##############################
#  EXTRACT EXISTENTIAL VARS  #
##############################
# return the list of all existential vars in this rule.
def extractExistentialVars( ruleData ) :

  allExistentialVars = []

  # ----------------------------------------- #
  # get goal att list

  goalAttList = ruleData[ "goalAttList" ]

  for subgoal in ruleData[ "subgoalListOfDicts" ] :

    # ----------------------------------------- #
    # get subgoal att list

    subgoalAttList = subgoal[ "subgoalAttList" ]

    # ----------------------------------------- #
    # collect all existential vars

    for satt in subgoalAttList :
      if not satt in goalAttList and \
         not satt in allExistentialVars and \
         not satt == "_" and \
         not is_fixed_string( satt ) and \
         not is_fixed_int( satt ) :
        allExistentialVars.append( satt )

  return allExistentialVars

##############################
#  EXTRACT EXISTENTIAL VARS  #
##############################
# return the list of all existential vars in this rule.
def extractExistentialVars( ruleData ) :

  allExistentialVars = []

  # ----------------------------------------- #
  # get goal att list

  goalAttList = ruleData[ "goalAttList" ]

  for subgoal in ruleData[ "subgoalListOfDicts" ] :

    # ----------------------------------------- #
    # get subgoal att list

    subgoalAttList = subgoal[ "subgoalAttList" ]

    # ----------------------------------------- #
    # collect all existential vars

    for satt in subgoalAttList :
      if not satt in goalAttList and \
         not satt in allExistentialVars and \
         not satt == "_" and \
         not is_fixed_string( satt ) and \
         not is_fixed_int( satt ) :
        allExistentialVars.append( satt )

  return allExistentialVars

######################
#  GET UNIFORM ATTS  #
######################
# return a list of strings with magnitude equal to input integer
def getUniformAtts( numAtts ) :

  uniformAtt_list = []

  for i in range( 0, numAtts) :

    uniformAtt_list.append( "Att" + str( i ) )

  return uniformAtt_list

###########################
#  DIFFERENT ATT SCHEMAS  #
###########################
# check if more than one universal attribute
# lists define the schemas for the rule set
# for this relation definition.
def differentAttSchemas( ruleSet ) :

  logging.debug( "  DIFFERENT ATT SCHEMAS : ruleSet = " + str( ruleSet ) )

  for rule1 in ruleSet :

    logging.debug( "  DIFFERENT ATT SCHEMAS : rule1 = " + str( rule1.ruleData ) )

    # ----------------------------------------- #
    # get goal att list

    gattList1 = rule1.goalAttList

    for rule2 in ruleSet :

      # ----------------------------------------- #
      # get goal att list

      gattList2 = rule2.goalAttList

      # sanity check attribute list lengths
      if not len( gattList1 ) == len( gattList2 ) :
        tools.bp( __name__, inspect.stack()[0][3], "FATAL ERROR : different schema arities for rules defining the same relation. \n" + str( rule1.ruleData ) + "\n" + str( rule2.ruleData ) )

      else :

        for i in range( 0, len( gattList1 ) ) :
          if not gattList1[ i ] == gattList2[ i ] :
            logging.debug( "  DIFFERENT ATT SCHEMAS : returning True." )
            return True

  logging.debug( "  DIFFERENT ATT SCHEMAS : returning False." )
  return False

##########################
#  GET RULE SETS UNIQUE  #
##########################
# return a dict mapping relation names to lists of rule objects
def getRuleSets_unique( ruleMeta ) :

  ruleSet_dict = {}

  for ruleObj in ruleMeta :

    # ----------------------------------------- #
    # get relation name

    relName = ruleObj.relationName

    # ----------------------------------------- #
    # organize rule object in dict

    if not relName in ruleSet_dict :
      ruleSet_dict[ relName ] = [ ruleObj ]

    else :
      ruleSet_dict[ relName ].append( ruleObj )

  return ruleSet_dict

###########################
#  GET RULE SETS UNIFORM  #
###########################
# return a dict mapping relation names to lists of rule objects
def getRuleSets_uniform( ruleMeta ) :

  ruleSet_dict = {}
  other_rules  = []

  for ruleObj in ruleMeta :

    # ----------------------------------------- #
    # get relation name

    relName = ruleObj.relationName

    # ----------------------------------------- #
    # organize rule object in dict

    # skip rules with goal aggs
    if containsAgg_rule( ruleObj ) :
      other_rules.append( ruleObj )

    else :
      if not relName in ruleSet_dict :
        ruleSet_dict[ relName ] = [ ruleObj ]

      else :
        ruleSet_dict[ relName ].append( ruleObj )


  return [ ruleSet_dict, other_rules ]

#################
#  MAKE UNIQUE  #
#################
# make the existential vars per rule in the given set unique
# make existential vars unique by just appending the rule id
def makeUnique( ruleSet ) :

  for rule in ruleSet :
    if rule.relationName == "log" :
      logging.debug( "  MAKE UNIQUE : log rule meta = " + str( rule.ruleData ) )
      rule.cursor.execute( "SELECT attID,attTYpe FROM GoalAtt WHERE rid=='" + str( rule.rid ) + "'" )
      typeList = rule.cursor.fetchall()
      typeList = tools.toAscii_multiList( typeList )
      for t in typeList :
        logging.debug(  "  MAKE UNIQUE : " + str( t ) )

  for rule in ruleSet :

    # ----------------------------------------- #
    # get rid

    rid = rule.rid

    # ----------------------------------------- #
    # get goal att list

    goalAttList = rule.ruleData[ "goalAttList" ]

    # ----------------------------------------- #
    # generate new subgoal info

    subgoalListOfDicts = []

    for subgoal in rule.ruleData[ "subgoalListOfDicts" ] :

      # ----------------------------------------- #
      # get all subgoal info

      subgoalName    = subgoal[ "subgoalName" ]
      subgoalAttList = subgoal[ "subgoalAttList" ]
      polarity       = subgoal[ "polarity" ]
      subgoalTimeArg = subgoal[ "subgoalTimeArg" ]

      new_subgoalAttList = []

      for satt in subgoalAttList :

        # ----------------------------------------- #
        # append the rid to all existential vars

        if satt in goalAttList or \
           satt == "_" or \
           is_fixed_string( satt ) or \
           is_fixed_int( satt ) :
          new_subgoalAttList.append( satt )

        else :
          new_subgoalAttList.append( satt + str( rid ) )

      # ----------------------------------------- #
      # save new subgoal

      new_sub_dict = {}
      new_sub_dict[ "subgoalName" ]    = subgoalName
      new_sub_dict[ "subgoalAttList" ] = new_subgoalAttList
      new_sub_dict[ "polarity" ]       = polarity
      new_sub_dict[ "subgoalTimeArg" ] = subgoalTimeArg

      subgoalListOfDicts.append( new_sub_dict )

    # ----------------------------------------- #
    # generate new eqn info

    eqnDict = {}

    for eqn in rule.ruleData[ "eqnDict" ] :

      # ----------------------------------------- #
      # get var list

      varList     = rule.ruleData[ "eqnDict" ][ eqn ]
      new_varList = []

      for var in varList :

        logging.debug( "  MAKE UNIQUE : var = " + var )

        # ----------------------------------------- #
        # append the rid to all existential vars

        if var in goalAttList :
          new_varList.append( var )

        else :
          new_var = var + str( rid )
          new_varList.append( new_var )

      # ----------------------------------------- #
      # get new eqn

      prev_vars = []
      new_eqn   = eqn
      for var in varList :

        if var in prev_vars :
          pass

        else :

          prev_vars.append( var )

          # skip universal vars
          if var in goalAttList :
            pass

          else :
            new_var = var + str( rid )
            new_eqn = new_eqn.replace( var, new_var )

      # ----------------------------------------- #
      # save new eqn data

      logging.debug( "  MAKE UNIQUE : new_eqn     = " + new_eqn )
      logging.debug( "  MAKE UNIQUE : new_varList = " + str( new_varList ) )

      eqnDict[ new_eqn ] = new_varList

    # ----------------------------------------- #
    # save new subgoal list

    logging.debug( " MAKE UNIQUE : subgoalListOfDicts = " + str( subgoalListOfDicts ) )

    rule.subgoalListOfDicts               = subgoalListOfDicts
    rule.ruleData[ "subgoalListOfDicts" ] = subgoalListOfDicts
    rule.saveSubgoals()

    # ----------------------------------------- #
    # save new eqn dict

    logging.debug( " MAKE UNIQUE : eqnDict = " + str( eqnDict ) )

    rule.eqnDict               = eqnDict
    rule.ruleData[ "eqnDict" ] = eqnDict
    rule.saveEquations()

  return ruleSet



#################
#  OVERLAPPING  #
#################
# check if the input lists contain any identical elements
def overlapping( existVars1, existVars2 ) :

  for var1 in existVars1 :
    if var1 in existVars2 :
      return True

  return False

#############################
#  UNIQUE EXISTENTIAL VARS  #
#############################
# check if each rule in the given rule set has a unique set of 
# existential variables.
def uniqueExistentialVars( ruleSet ) :

  for rule1 in ruleSet :

    # ----------------------------------------- #
    # extract set of existential vars

    existVars1 = extractExistentialVars( rule1.ruleData )

    for rule2 in ruleSet :

      # ----------------------------------------- #
      # skip identical rules

      if identicalRules( rule1, rule2 ) :
        pass

      else :

        # ----------------------------------------- #
        # extract set of existential vars

        existVars2 = extractExistentialVars( rule2.ruleData )

        # ----------------------------------------- #
        # check if existential var lists overlap

        if overlapping( existVars1, existVars2 ) :
          logging.debug( "  UNIQUE EXISTENTIAL VARS : returning False" )
          return False

  logging.debug( "  UNIQUE EXISTENTIAL VARS : returning True" )
  return True

#################################
#  SET UNIQUE EXISTENTIAL VARS  #
#################################
# rewriting existing rules to ensure each 
# rule per relation definition utilizes a unique 
# set of existential variables
def setUniqueExistentialVars( ruleMeta ) :

  # ----------------------------------------- #
  # extract rule sets

  ruleSet_dict = getRuleSets_unique( ruleMeta )

  # ----------------------------------------- #
  # make sure universal att schemas are identical

  tmp = []
  new_ruleMeta = []

  for relName in ruleSet_dict :

    # ----------------------------------------- #
    # make sure existential vars are unique 
    # per rule

    logging.debug( "  SET UNIQUE EXISTENTIAL VARS : evaluating relName = " + relName )

    ruleSet = ruleSet_dict[ relName ]

    if uniqueExistentialVars( ruleSet ) :
      new_ruleMeta.extend( ruleSet )

    else :
      new_ruleMeta.extend( makeUnique( ruleSet ) )
      tmp.extend( ruleSet )

  for rule in new_ruleMeta :
    logging.debug( "  SET UNIQUE EXISTENTIAL VARS : " + str( rule.ruleData ) )

  return new_ruleMeta

##################
#  MAKE UNIFORM  #
##################
# input a list of rule objects.
# replace all goal attributes lists with a 
# generated uniform set of universal variables
def makeUniform( ruleSet, cursor ) :

  logging.debug( "  MAKE UNIFORM : running process..." )

  # ----------------------------------------- #
  # generate uniform set of universal 
  # attributes

  numAtts     = len( ruleSet[0].goalAttList )
  uniformAtts = getUniformAtts( numAtts )

  # ----------------------------------------- #
  # replace goal att list and universal
  # atts in subgoals

  for rule in ruleSet :

    logging.debug( "  MAKE UNIFORM : rule.relationName = " + rule.relationName )

    # ----------------------------------------- #
    # record hitting uniform rewrites

    rule.hitUniformRewrites = True

    # ----------------------------------------- #
    # save cursor or else it breaks

    rule.cursor = cursor

    # ----------------------------------------- #
    # get copy of original att list

    orig_goalAttList = rule.goalAttList

    # ----------------------------------------- #
    # generate a mapping between old and
    # new att strings

    if not len( uniformAtts ) == len( orig_goalAttList ) :
      tools.bp( __name__, inspect.stack()[0][3], "FATAL ERROR : inconsistent arity between new uniform att list and original att list in rule definition:\n" + str( uniformAtts ) + "\n" + str( orig_goalAttList ) + "\n" + str( rule.ruleData ) )

    attMapper = {}
    for i in range( 0, len( orig_goalAttList ) ) :
      this_orig_att = orig_goalAttList[ i ]

      ## skip time atts
      ## observe this makes zero sense.
      #if not this_orig_att.startswith( "NRESERVED" ) and not this_orig_att.startswith( "MRESERVED" ) :
      #  attMapper[ this_orig_att ] = uniformAtts[ i ]

      # preserve time atts
      # observe this shits up the process of 
      # shuffling inter-rule subgoals across not_ rules.
      #if this_orig_att.startswith( "NRESERVED" ) or this_orig_att.startswith( "MRESERVED" ) :
      #  attMapper[ this_orig_att ] = this_orig_att
      #else :
      #  attMapper[ this_orig_att ] = uniformAtts[ i ]

      # this is the regular line:
      attMapper[ this_orig_att ] = uniformAtts[ i ]

    logging.debug( "  MAKE UNIFORM : attMapper = " + str( attMapper ) )

    rule.orig_rule_attMapper = attMapper

    # ----------------------------------------- #
    # build new goal attributes list

    logging.debug( "  MAKE UNIFORM : build new goal att list." )

    new_goalAttList = []
    for gatt in orig_goalAttList :
      #if not gatt.startswith( "NRESERVED" ) and not gatt.startswith( "MRESERVED" ) :
      #  new_goalAttList.append( attMapper[ gatt ] )
      #else :
      #  new_goalAttList.append( gatt )
      new_goalAttList.append( attMapper[ gatt ] )

    # ----------------------------------------- #
    # replace goal att list

    logging.debug( "  MAKE UNIFORM : replace goal att list." )

    rule.goalAttList               = copy.deepcopy( new_goalAttList )
    rule.ruleData[ "goalAttList" ] = copy.deepcopy( new_goalAttList )
    rule.saveToGoalAtt()

    logging.debug( "  MAKE UNIFORM : replace goal att list." )

    # ----------------------------------------- #
    # replace universal atts in subgoals

    subgoalListOfDicts = []

    for subgoal in rule.ruleData[ "subgoalListOfDicts" ] :

      # ----------------------------------------- #
      # get subgoal info

      subgoalName    = subgoal[ "subgoalName" ]
      subgoalAttList = subgoal[ "subgoalAttList" ]
      polarity       = subgoal[ "polarity" ]
      subgoalTimeArg = subgoal[ "subgoalTimeArg" ]

      # ----------------------------------------- #
      # create new subgoal att list with 
      # replacements

      new_subgoalAttList = []

      for satt in subgoalAttList :

        if satt in attMapper :
          logging.debug( "  MAKE UNIFORM : satt = " + satt + ", attMapper[ " + satt + " ] = " + attMapper[ satt ] )
        else :
          logging.debug( "  MAKE UNIFORM : satt = " + satt )

        if satt in attMapper :
          new_subgoalAttList.append( attMapper[ satt ] )
        else :
          new_subgoalAttList.append( satt )

      logging.debug( "  MAKE UNIFORM : new_subgoalAttList = " + str( new_subgoalAttList ) )

      # ----------------------------------------- #
      # save new subgoal info

      new_sub_dict = {}
      new_sub_dict[ "subgoalName" ]    = subgoalName
      new_sub_dict[ "subgoalAttList" ] = new_subgoalAttList
      new_sub_dict[ "polarity" ]       = polarity
      new_sub_dict[ "subgoalTimeArg" ] = subgoalTimeArg

      subgoalListOfDicts.append( new_sub_dict )

    # ----------------------------------------- #
    # replace univseral atts in eqns

    eqnDict = {}

    for eqn in rule.ruleData[ "eqnDict" ] :

      # ----------------------------------------- #
      # get var list

      varList     = rule.ruleData[ "eqnDict" ][ eqn ]
      new_varList = []

      for var in varList :

        logging.debug( "  MAKE UNIFORM : var = " + var )

        if var in attMapper :
          logging.debug( "  MAKE UNIFORM : var = " + var + ", attMapper[ " + var + " ] = " + attMapper[ var ] )
        else :
          logging.debug( "  MAKE UNIFORM : var = " + var )

        if var in attMapper :
          new_varList.append( attMapper[ var ] )
        else :
          new_varList.append( var )

      # ----------------------------------------- #
      # get new eqn

      prev_vars = []
      new_eqn   = eqn
      for var in varList :

        if var in prev_vars :
          pass

        else :

          prev_vars.append( var )

          # skip existential vars
          if var in attMapper :
            new_var = attMapper[ var ]
            new_eqn = new_eqn.replace( var, new_var )

          else :
            pass

      # ----------------------------------------- #
      # save new eqn data

      logging.debug( "  MAKE UNIFORM : new_eqn     = " + new_eqn )
      logging.debug( "  MAKE UNIFORM : new_varList = " + str( new_varList ) )

      eqnDict[ new_eqn ] = new_varList

    # ----------------------------------------- #
    # save new subgoal list

    logging.debug( "  MAKE UNIFORM : subgoalListOfDicts = " + str( subgoalListOfDicts ) )

    rule.subgoalListOfDicts               = copy.deepcopy( subgoalListOfDicts )
    rule.ruleData[ "subgoalListOfDicts" ] = copy.deepcopy( subgoalListOfDicts )
    rule.saveSubgoals()

    # ----------------------------------------- #
    # save new eqn dict

    logging.debug( " MAKE UNIFORM : eqnDict = " + str( eqnDict ) )

    rule.eqnDict               = copy.deepcopy( eqnDict )
    rule.ruleData[ "eqnDict" ] = copy.deepcopy( eqnDict )
    rule.saveEquations()

  logging.debug( "  MAKE UNIFORM : ...done." )
  return ruleSet

##########################
#  SET UNIFORM ATT LIST  #
##########################
# rewrites rules to ensure a uniform schema 
# of universal variables per relation definition
def setUniformAttList( ruleMeta, cursor ) :

  logging.debug( "  SET UNIFORM ATT LIST : running process..." )

  for rule in ruleMeta :
    logging.debug( "  SET UNIFORM ATT LIST : " + str( rule.ruleData ) )

  # ----------------------------------------- #
  # extract rule sets

  ruleSet_data = getRuleSets_uniform( ruleMeta )
  ruleSet_dict = ruleSet_data[0]
  other_rules  = ruleSet_data[1]

  # ----------------------------------------- #
  # make sure universal att schemas are identical

  new_ruleMeta = []

  for relName in ruleSet_dict :

    logging.debug( "  SET UNIFORM ATT LIST : evaluating relName = " + relName )

    ruleSet = ruleSet_dict[ relName ]

    if differentAttSchemas( ruleSet ) :
      for rule in ruleSet :
        rule.hitUniformityRewrites = True

      new_ruleMeta.extend( makeUniform( ruleSet, cursor ) )

    else :
      new_ruleMeta.extend( ruleSet )

  for rule in new_ruleMeta :
    logging.debug( "  SET UNIFORM ATT LIST : " + str( rule.ruleData ) )

  # add the skipped rules
  new_ruleMeta.extend( other_rules )

  logging.debug( "  SET UNIFORM ATT LIST : ...done." )
  return new_ruleMeta

##################
#  CONTAINS AGG  #
##################
# check if the given attribute 
# contains an agg operator
def containsAgg( att ) :
  for op in arithOps :
    if op in att :
      return True
  for op in arithFuncs :
    if att.startswith( op + "<" ) and att.endswith( ">" ) :
      return True

  return False

#######################
#  CONTAINS AGG RULE  #
#######################
# check if the rule contains an aggregate in the head
def containsAgg_rule( rule ) :

  for gatt in rule.goalAttList :
    if containsAgg( gatt ) :
      return True

  return False

##################
#  AGG REWRITES  #
##################
# perform aggregate rewrites
def aggRewrites( ruleMeta, argDict ) :

  logging.debug( "  AGG REWRITES : running process..." )

  settings_path = argDict[ "settings" ]

  new_ruleMeta = []
  new_relationNames = []

  for rule in ruleMeta :

    logging.debug( "  AGG REWRITES : ======================================" )
    logging.debug( "  AGG REWRITES : rule.ruleData           = " + str( rule.ruleData ) )
    logging.debug( "  AGG REWRITES : **rule.orig_goalAttList = " + str( rule.orig_goalAttList ) )
    logging.debug( "  AGG REWRITES : rule                    = " + str( rule ) )

    if containsAgg_rule( rule ) :

      orig_name = copy.copy( rule.relationName )

      # ----------------------------------------- #
      # normalize universal attributes

      # get goal att list
      goalAttList = copy.deepcopy( rule.goalAttList )

      # ----------------------------------------- #
      # rename rule with _agg + index number 
      # convention

      new_relationName                = rule.relationName + "_agg" + str( rule.rid )
      rule.ruleData[ "relationName" ] = new_relationName
      rule.relationName               = new_relationName
      rule.saveToRule()

      new_ruleMeta.append( rule )
      logging.debug( "  AGG REWRITES : **rule.orig_goalAttList = " + str( rule.orig_goalAttList ) )

      # ----------------------------------------- #
      # add new agg relation rule
      # for original rule definition

      orig_goalAttList = copy.deepcopy( rule.orig_goalAttList )
      new_goalAttList = [ "Att" + str( i ) for i in range( 0, len( goalAttList ) ) ]

      gattMapper = {}
      for i in range( 0, len( goalAttList ) ) :
        gattMapper[ goalAttList[ i ] ] = new_goalAttList[ i ]

      newRuleData = {}
      newRuleData[ "relationName" ]       = orig_name
      newRuleData[ "goalAttList" ]        = new_goalAttList
      newRuleData[ "goalTimeArg" ]        = rule.goalTimeArg
      newRuleData[ "subgoalListOfDicts" ] = [ { "subgoalName": new_relationName, "subgoalAttList": new_goalAttList, "polarity": "", "subgoalTimeArg": "" } ]
      #newRuleData[ "eqnDict" ]            = rule.eqnDict
      newRuleData[ "eqnDict" ]            = {}

      rid = tools.getIDFromCounters( "rid" )

      newRule                                 = copy.deepcopy( Rule.Rule( rid, newRuleData, rule.cursor ) )
      newRule.cursor = rule.cursor # need to do this for some reason or else cursor disappears?
      newRule.orig_rule_attMapper_aggRewrites = gattMapper
      newRule.orig_goalAttList                = orig_goalAttList # maintain original goal att list
      newRule.rule_type                       = rule.rule_type
      newRule.hitUniformityRewrites           = True
      new_ruleMeta.append( newRule )

      setTypes.setTypes( rule.cursor, argDict )

    else :
      new_ruleMeta.append( rule )

  logging.debug( "  AGG REWRITES : len( new_ruleMeta ) = " + str( len( new_ruleMeta ) ) )
  return new_ruleMeta

#####################
#  IS FIXED STRING  #
#####################
def is_fixed_string( att ) :
  if att.startswith( "'" ) and att.endswith( "'" ) :
    return True
  elif att.startswith( '"' ) and att.endswith( '"' ) :
    return True
  else :
    return False

##################
#  IS FIXED INT  #
##################
def is_fixed_int( att ) :
  if att.isdigit() :
    return True
  else :
    return False

##############################
#  HEAD CONTAINS FIXED DATA  #
##############################
def head_contains_fixed_data( rule ) :

  for gatt in rule.goalAttList :
    if is_fixed_string( gatt ) :
      return True
    elif is_fixed_int( gatt ) :
      return True

  return False

##############################
#  FIXED DATA HEAD REWRITES  #
##############################
# if head contains fixed data, replace with a new goal
# att connected to a new edb subgoal defined 
# using that piece of fixed data.
#
#    t( X, 4 ) :- m( X ) ;
#
# => t( X, Y ) :- m( X ), fdhr_4( Y ) ;
#    fdhr_4( 4 ) ;
#
def fixed_data_head_rewrites( ruleMeta, factMeta, argDict ) :

  settings_path = argDict[ "settings" ]

  for rule in ruleMeta :

    if head_contains_fixed_data( rule ) :

      orig_name   = copy.copy( rule.relationName )
      logging.debug( "  FIXED DATA HEAD REWRITES : rule.cursor = " + str( rule.cursor ) )

      # ----------------------------------------- #
      # normalize universal attributes

      # get goal att list
      goalAttList = copy.deepcopy( rule.goalAttList )

      # build new goal att list
      new_goalAttList = []
      index           = 0
      fixed_data_list = []
      for gatt in goalAttList :

        # replace fixed data with attribute variables
        if is_fixed_string( gatt ) or is_fixed_int( gatt ) :
          new_gatt = "FDHRAtt" + str( index )
          fixed_data_list.append( [ new_gatt, gatt ] )

        # otherwise, keep the old string
        else :
          new_gatt = gatt

        new_goalAttList.append( new_gatt )
        index += 1

      logging.debug( "  FIXED DATA HEAD REWRITES : new_goalAttList = " + str( new_goalAttList ) )


      # save new goal attribute list
      rule.ruleData[ "goalAttList" ] = new_goalAttList
      rule.goalAttList               = new_goalAttList
      rule.saveToGoalAtt()

      logging.debug( "  FIXED DATA HEAD REWRITES : rule.ruleData[ 'goalAttList' ] = " + str( rule.ruleData[ "goalAttList" ] ) )
      logging.debug( "  FIXED DATA HEAD REWRITES : rule.goalAttList               = " + str( rule.goalAttList ) )

      # add subgoals for fixed data
      subgoalListOfDicts = rule.subgoalListOfDicts

      # copy over all existing subgoals
      new_subgoalListOfDicts = []
      for sub in subgoalListOfDicts :
        new_subgoalListOfDicts.append( copy.copy( sub ) )

      for fdata in fixed_data_list :

        new_att  = fdata[ 0 ]
        raw_data = fdata[ 1 ]

        if is_fixed_string( raw_data ) :
          raw_data = raw_data.replace( "'", "" )
          raw_data = raw_data.replace( '"', "" )
          raw_data = raw_data.lower()

        new_sub_dict = {}
        new_sub_dict[ "subgoalName" ]    = "fdhr_" + str( raw_data )
        new_sub_dict[ "subgoalAttList" ] = [ new_att ]
        new_sub_dict[ "polarity" ]       = ""
        new_sub_dict[ "subgoalTimeArg" ] = ""
        new_subgoalListOfDicts.append( new_sub_dict )

      logging.debug( "  FIXED DATA HEAD REWRITES : new_subgoalListOfDicts = " + str( new_subgoalListOfDicts ) )

      # save new subgoals
      rule.ruleData[ "subgoalListOfDicts" ] = new_subgoalListOfDicts
      rule.subgoalListOfDicts               = new_subgoalListOfDicts
      rule.saveSubgoals()

      # ----------------------------------------- #
      # add new corresponding facts
      # factData = { relationName:'relationNameStr', dataList:[ data1, ... , dataN ], factTimeArg:<anInteger> }

      for fdata in fixed_data_list :

        logging.debug( "  FIXED DATA HEAD REWRITES : fdata = " + str( fdata ) )

        new_att       = fdata[ 0 ]
        raw_data_orig = fdata[ 1 ]

        if is_fixed_string( raw_data_orig ) :
          raw_data = raw_data_orig.replace( "'", "" )
          raw_data = raw_data.replace( '"', "" )
          raw_data = raw_data.lower()
        else :
          raw_data = raw_data_orig

        newFactData = {}
        newFactData[ "relationName" ] = "fdhr_" + str( raw_data )
        newFactData[ "dataList" ]     = [ raw_data_orig ]
        newFactData[ "factTimeArg" ]  = "" # n/a b/c datalog

        logging.debug( "  FIXED DATA HEAD REWRITES : newFactData = " + str( newFactData ) )

        fid = tools.getIDFromCounters( "fid" )

        newFact        = copy.deepcopy( Fact.Fact( fid, newFactData, rule.cursor ) ) # cursor should be identical for everything.
        newFact.cursor = rule.cursor # need to do this for some reason or else cursor disappears?
        factMeta.append( newFact )

        setTypes.setTypes( rule.cursor, argDict )

  logging.debug( "  FIXED DATA HEAD REWRITES : len( ruleMeta )     = " + str( len( ruleMeta ) ) )
  logging.debug( "  FIXED DATA HEAD REWRITES : len( factMeta )     = " + str( len( factMeta ) ) )
  return ruleMeta, factMeta


#############
#  IS SAFE  #
#############
# check if the rule given by the input rule data dictionary is safe
def isSafe( ruleData ) :

  #logging.debug( "  IS SAFE : ruleData = " + str( ruleData ) )

  # ----------------------------------------- #
  # get the set of goat attributes

  goalAttList = ruleData[ "goalAttList" ]

  # ----------------------------------------- #
  # get the set of all atts 
  # in positive subgoals

  subAttSet = []
  subgoalListOfDicts = ruleData[ "subgoalListOfDicts" ]
  for subgoal in subgoalListOfDicts :
    if subgoal[ "polarity" ] == "" :
      for satt in subgoal[ "subgoalAttList" ] :
        if not satt in subAttSet :
          subAttSet.append( satt )

  # ----------------------------------------- #
  # rule is safe if the set of all atts 
  # in all positive subgoals is exactly 
  # the set of goal attributes in the rule

  #logging.debug( "  IS SAFE : goalAttList = " + str( goalAttList ) )
  #logging.debug( "  IS SAFE : subAttSet   = " + str( subAttSet ) )

  flag = True
  for gatt in goalAttList :
    if not gatt in subAttSet :
      flag = False

  #logging.debug( "  IS SAFE : returning flag = " + str( flag ) )
  return flag


#####################
#  GET PATTERN MAP  #
#####################
# build a table of all possible combinations of 0s and 1s in rows of the input length
def getPatternMap( numSubgoals ) :

  logging.debug( "  GET PATTERN MAPsatt : numSubgoals = " + str( numSubgoals ) )

  patternMap = [ ''.join( i ) for i in itertools.product( [ "0", "1" ], repeat = numSubgoals ) ]

  for row in patternMap :
    logging.debug( "  GET PATTERNMAP : row = " + row )

  return patternMap


####################
#  GET FINAL FMLA  #
####################
def get_final_fmla( ruleSet ) :

  logging.debug( "  GET FINAL FMLA : running process..." )
  logging.debug( "  GET FINAL FMLA : ruleSet :" )
  for r in ruleSet :
    logging.debug( "    " + str( dumpers.reconstructRule( r.rid, r.cursor ) ) )

  # collect the initial set of literals
  literal_id_lists = []
  for rule_index in range( 0, len( ruleSet ) ) :
    rule = ruleSet[ rule_index ]
    this_literal_id_list = []
    for sub_index in range( 0, len( rule.subgoalListOfDicts ) ) :
      this_literal = str( rule_index ) + "_" + str( sub_index )
      if rule.subgoalListOfDicts[ sub_index ][ "polarity" ] == "notin" :
        this_literal = "~" + this_literal
      this_literal_id_list.append( this_literal )
    literal_id_lists.append( this_literal_id_list )

  logging.debug( "  GET FINAL FMLA : literal_id_lists = " + str( literal_id_lists ) )

  # based on https://stackoverflow.com/a/798893
  all_clause_combos = list( itertools.product( *literal_id_lists ) )

  # flip literal polarities
  flipped_literal_id_lists = []
  for clause in all_clause_combos :
    flipped_lits_clause = []
    for lit in clause :
      if "~" in lit :
        lit = lit.replace( "~", "" )
      else :
        lit = "~" + lit
      flipped_lits_clause.append( lit )
    flipped_literal_id_lists.append( flipped_lits_clause )

  logging.debug( "  GET FINAL FMLA : flipped_literal_id_lists = " + \
                 str( flipped_literal_id_lists ) )

  # build final fmla
  final_fmla = ""
  for i in range( 0, len( flipped_literal_id_lists ) ) :
    clause = flipped_literal_id_lists[ i ]
    this_clause = ""
    for j in range( 0, len( clause ) ) :
      lit          = clause[ j ]
      this_clause += lit
      if j < len( clause ) - 1 :
        this_clause += "&"
    this_clause = "(" + this_clause + ")"
    if i < len( flipped_literal_id_lists ) - 1 :
      this_clause += "|"
    final_fmla += this_clause

  return final_fmla


###################################
#  IDENTICAL RULE ALREADY EXISTS  #
###################################
def identical_rule_already_exists( target_rule, ruleMeta ) :
  for rule in ruleMeta :
    if rule.relationName == target_rule.relationName :
      logging.debug( "  IDENTICAL RULE ALREADY EXISTS : comparing :" )
      logging.debug( "     " + dumpers.reconstructRule( target_rule.rid, target_rule.cursor ) )
      logging.debug( "     " + dumpers.reconstructRule( rule.rid, rule.cursor ) )
      IDENTICAL_SUBS = 0
      for sub_rule in rule.subgoalListOfDicts :
        if sub_rule in target_rule.subgoalListOfDicts :
          IDENTICAL_SUBS += 1
      if IDENTICAL_SUBS == len( target_rule.subgoalListOfDicts ) :
        logging.debug( "  IDENTICAL RULE ALREADY EXISTS : returning False." )
        return True
  logging.debug( "  IDENTICAL RULE ALREADY EXISTS : returning False." )
  return False


############
#  IS IDB  #
############
# check if the given relation name is an idb.
def is_idb( rel_name, ruleMeta ) :
  for rule in ruleMeta :
    if rule.relationName == rel_name :
      return True
  return False

###################################
#  GENERATE RID TO RULE META MAP  #
###################################
def generate_rid_to_rule_meta_map( ruleMeta ) :
  rid_to_rule_meta_map = {}
  for rule in ruleMeta :
    rid_to_rule_meta_map[ rule.rid ] = rule
  return rid_to_rule_meta_map  


#######################
#  GENERATE ORIG CPS  #
#######################
def generate_orig_cps( ruleMeta ) :

  new_rules = []
  for rule in ruleMeta :
    new_ruleData                   = copy.deepcopy( rule.ruleData )
    new_ruleData[ "relationName" ] = "orig_" + rule.relationName

    for i in range( 0, len( new_ruleData[ "subgoalListOfDicts" ] ) ) :
      sub = new_ruleData[ "subgoalListOfDicts" ][ i ]
      if not sub[ "subgoalName" ].startswith( "orig_" ) and \
         not sub[ "subgoalName" ].endswith( "_edb" )    and \
         is_idb( sub[ "subgoalName" ], ruleMeta ) :
        new_ruleData[ "subgoalListOfDicts" ][ i ][ "subgoalName" ] = "orig_" + sub[ "subgoalName" ]

    rid            = tools.getIDFromCounters( "rid" )
    newRule        = copy.deepcopy( Rule.Rule( rid, new_ruleData, rule.cursor) )
    newRule.cursor = rule.cursor

    # copy over types manually
    newRule.goal_att_type_list = rule.goal_att_type_list
    newRule.manually_set_types()

    # save rule
    new_rules.append( newRule )

    #if newRule.relationName == "orig_node" :
    #  print dumpers.reconstructRule( rule.rid, rule.cursor )
    #  print rule.goal_att_type_list
    #  sys.exit( "blah" )

  return new_rules

######################
#  CHANGE REL NAMES  #
######################
# append the rule id to all rule names
def change_rel_names( ruleMeta ) :

  new_rules = []

  for rule in ruleMeta :

    if rule.relationName.startswith( "orig_" ) :

      new_rel_name = rule.relationName + "_r" + str( rule.rid )
  
      # generate a new rule using the original head, 
      # but pointing to the new rel name.
      ruleData = {}
      ruleData[ "relationName" ]      = rule.relationName
      ruleData[ "goalAttList" ]       = rule.goalAttList
      ruleData[ "goalTimeArg" ]       = ""
      ruleData[ "eqnDict" ]           = {}
      ruleData[ "subgoalListOfDicts"] = [ { "subgoalName"    : new_rel_name, \
                                            "subgoalAttList" : ruleData[ "goalAttList" ], \
                                            "polarity"       : "", \
                                            "subgoalTimeArg" : "" }]
  
      rid            = tools.getIDFromCounters( "rid" )
      newRule        = copy.deepcopy( Rule.Rule( rid, ruleData, rule.cursor) )
      newRule.cursor = rule.cursor
      new_rules.append( newRule )
  
      # change the relation name in the original rule.
      rule.set_name( new_rel_name )

  ruleMeta.extend( new_rules )
  return ruleMeta

###################
#  SORT DM RULES  #
###################
# order DM rules with recursive rules last
def sortDMRules( ruleMeta ) :

  regularRules   = []
  recursiveRules = []

  for r in ruleMeta :
    if is_dm_and_recursive( r ) :
      recursiveRules.append( r )
    else :
      regularRules.append( r )

  for r in regularRules :
    logging.debug( dumpers.reconstructRule( r.rid, r.cursor ) )
  logging.debug( "-----" )
  for r in recursiveRules :
    logging.debug( dumpers.reconstructRule( r.rid, r.cursor ) )

  sorted_ruleMeta = []
  sorted_ruleMeta.extend( regularRules )
  sorted_ruleMeta.extend( recursiveRules )

  for r in sorted_ruleMeta :
    logging.debug( dumpers.reconstructRule( r.rid, r.cursor ) )
  #sys.exit( "blah" )

  return sorted_ruleMeta

#########################
#  IS DM AND RECURSIVE  #
#########################
def is_dm_and_recursive( rule ) :
  goalName = rule.relationName
  for sub in rule.subgoalListOfDicts :
    subName = sub[ "subgoalName" ]
    if subName == goalName and subName.startswith( "not_" ) :
      return True
  return False

##############################
#  RESOLVE DOUBLE NEGATIONS  #
##############################
# a negated not_ rule is th original rule.
def resolveDoubleNegations( ruleMeta ) :

  for rule in ruleMeta :

    # ----------------------------------------- #
    # get subgoal info

    subgoalListOfDicts = copy.deepcopy( rule.subgoalListOfDicts )

    new_subgoalListOfDicts = []

    for subgoal in subgoalListOfDicts :

      logging.debug( "  RESOLVE DOUBLE NEGATIONS : subgoalName    = " + \
                     subgoal[ "subgoalName" ] )
      logging.debug( "  RESOLVE DOUBLE NEGATIONS : polarity       = " + \
                     subgoal[ "polarity" ] )
      logging.debug( "  RESOLVE DOUBLE NEGATIONS : subgoalAttList = " + \
                     str( subgoal[ "subgoalAttList" ] ) )
      logging.debug( "  RESOLVE DOUBLE NEGATIONS : subgoalTimeArg = " + \
                     subgoal[ "subgoalTimeArg" ] )

      # ----------------------------------------- #
      # resolve double negatives

      if subgoal[ "subgoalName" ].startswith( "not_" ) and subgoal[ "polarity" ] == "notin" :

        logging.debug( "  RESOLVE DOUBLE NEGATIONS: original subgoal = " + str( subgoal ) )

        new_sub_dict = {}
        new_sub_dict[ "subgoalName" ]    = subgoal[ "subgoalName" ][4:]
        new_sub_dict[ "subgoalAttList" ] = subgoal[ "subgoalAttList" ]
        new_sub_dict[ "polarity" ]       = ""
        new_sub_dict[ "subgoalTimeArg" ] = subgoal[ "subgoalTimeArg" ]

        logging.debug( "  RESOLVE DOUBLE NEGATIONS : new_sub_dict = " + \
                       str( new_sub_dict ) )
        logging.debug( "  RESOLVE DOUBLE NEGATIONS : adding to new_subgoalListOfDicts : " + \
                       str( new_sub_dict ) + "->1")

        new_subgoalListOfDicts.append( copy.deepcopy( new_sub_dict ) )

      else :

        logging.debug( "  RESOLVE DOUBLE NEGATIONS : adding to new_subgoalListOfDicts : " + \
                       str( subgoal ) + " -> 3" )

        new_subgoalListOfDicts.append( copy.deepcopy( subgoal )  )

    # ----------------------------------------- #
    # save new subgoal list

    logging.debug( "  RESOLVE DOUBLE NEGATIONS : new_subgoalListOfDicts = " + \
                   str( new_subgoalListOfDicts ) )

    rule.subgoalListOfDicts               = copy.deepcopy( new_subgoalListOfDicts )
    rule.ruleData[ "subgoalListOfDicts" ] = copy.deepcopy( new_subgoalListOfDicts )
    rule.saveSubgoals()

  return ruleMeta        


###############################
#  REPLACE SUBGOAL NEGATIONS  #
###############################
# rewrite existing rules to replace 
# instances of negated subgoal instances 
# with derived not_rules
def replaceSubgoalNegations( ruleMeta, argDict ) :

  settings_path = argDict[ "settings" ]

  for rule in ruleMeta :

    # ----------------------------------------- #
    # skip domcomp rules

    if rule.relationName.startswith( "domcomp_" ) or \
       rule.relationName.startswith( "dom_" )     or \
       rule.relationName.startswith( "unidom_" )  or \
       rule.relationName.startswith( "exidom_" )  or \
       rule.relationName.startswith( "orig_" ) :
      pass

    else :

      # ----------------------------------------- #
      # get subgoal info

      subgoalListOfDicts = copy.deepcopy( rule.subgoalListOfDicts )

      new_subgoalListOfDicts = []

      for subgoal in subgoalListOfDicts :

        logging.debug( "  REPLACE SUBUGOAL NEGATIONS : subgoalName    = " + \
                       subgoal[ "subgoalName" ] )
        logging.debug( "  REPLACE SUBUGOAL NEGATIONS : polarity       = " + \
                       subgoal[ "polarity" ] )
        logging.debug( "  REPLACE SUBUGOAL NEGATIONS : subgoalAttList = " + \
                       str( subgoal[ "subgoalAttList" ] ) )
        logging.debug( "  REPLACE SUBUGOAL NEGATIONS : subgoalTimeArg = " + \
                       subgoal[ "subgoalTimeArg" ] )

        # ----------------------------------------- #
        # replace negatives

        if subgoal[ "subgoalName" ] == "missing_log" and subgoal[ "polarity" ] == "notin" :
          logging.debug( "  REPLACE SUBGOAL NEGATIONS : hasDM missing_log = " + \
                         str( hasDM( "missing_log", ruleMeta ) ) )

        if hasDM( subgoal[ "subgoalName" ], ruleMeta ) and subgoal[ "polarity" ] == "notin" :

          logging.debug( "  REPLACE SUBGOAL NEGATIONS : original subgoal = " + str( subgoal ) )

          new_sub_dict = {}
          new_sub_dict[ "subgoalName" ]    = "not_" + subgoal[ "subgoalName" ]
          new_sub_dict[ "subgoalAttList" ] = subgoal[ "subgoalAttList" ]
          new_sub_dict[ "polarity" ]       = ""
          new_sub_dict[ "subgoalTimeArg" ] = subgoal[ "subgoalTimeArg" ]

          logging.debug( "  REPLACE SUBGOAL NEGATIONS : new_sub_dict = " + str( new_sub_dict ) )
          logging.debug( "  REPLACE SUBGOAL NEGATIONS : adding to new_subgoalListOfDicts : " + \
                         str( new_sub_dict ) + "->1")

          new_subgoalListOfDicts.append( new_sub_dict )

        else :

          logging.debug( "  REPLACE SUBGOAL NEGATIONS : adding to new_subgoalListOfDicts : " + \
                         str( subgoal ) + " -> 2" )

          new_subgoalListOfDicts.append( copy.deepcopy( subgoal )  )

      # ----------------------------------------- #
      # save new subgoal list

      logging.debug( "  REPLACE SUBGOAL NEGATIONS : new_subgoalListOfDicts_tmp = " + \
                     str( new_subgoalListOfDicts ) )
      rule.subgoalListOfDicts               = copy.deepcopy( new_subgoalListOfDicts )
      rule.ruleData[ "subgoalListOfDicts" ] = copy.deepcopy( new_subgoalListOfDicts )

      rule.saveSubgoals()

  return ruleMeta

#############
#  HAS DM  #
#############
# check if the subgoal has a corresponding not_ rule
def hasDM( subgoalName, ruleMeta ) :
  for rule in ruleMeta :
    #if rule.relationName.startswith( "not_" + subgoalName ) :
    if rule.relationName == "not_" + subgoalName :
      return True
  return False


##############
#  HAS DM 2  #
##############
# check if the subgoal has a corresponding not_ rule
def hasDM_2( subgoalName, parent_name, ruleMeta ) :
  for rule in ruleMeta :
    if rule.relationName.startswith( "not_" + subgoalName ) and \
      rule.relationName.endswith( "_from_" + parent_name ) :
      return True
  return False


#########################
#  REPLACE UNUSED VARS  #
#########################
#  given the entire rule set, replace unused variables
# with wildcards.
def replace_unused_vars( ruleMeta, cursor ) :

  COUNTER = 0
  for rule in ruleMeta :

    logging.debug( "  REPLACE UNUSED VARS : rule (before) :\n     >" + \
                   dumpers.reconstructRule( rule.rid, rule.cursor ) )

    subgoalChanged = False
    sub_keepers    = []
    for i in range( 0, len ( rule.ruleData[ "subgoalListOfDicts" ] ) ):

      # replace unused vars with wildcards
      sub = rule.ruleData[ "subgoalListOfDicts" ][ i ]
      for j in range( 0, len( sub[ "subgoalAttList" ] ) ) :
        if is_unused_var( sub[ "subgoalAttList" ][ j ], rule ) :
          sub[ "subgoalAttList" ][ j ] = "_"
          subgoalChanged = True

      # remove subgoals with all wildcards
      if sub[ "subgoalAttList" ] == [ "_" for i in range( 0, len( sub[ "subgoalAttList" ] ) ) ] :
        subgoalChanged = True
        pass
      else :
        sub_keepers.append( sub )

    print sub_keepers

    if subgoalChanged :
      rule.ruleData[ "subgoalListOfDicts" ] = sub_keepers
      rule.subgoalListOfDicts               = rule.ruleData[ "subgoalListOfDicts" ]
      rule.saveSubgoals()

    logging.debug( "  REPLACE UNUSED VARS : rule (after) :\n     >" + \
                   dumpers.reconstructRule( rule.rid, rule.cursor ) )

    COUNTER += 1

    #if rule.relationName == "unidom_not_node" :
    #  print COUNTER
    #  sys.exit( "blah" )

  return ruleMeta


###############
#  IS UNUSED  #
###############
def is_unused_var( var, rule ) :

  logging.debug( "  IS UNUSED : var = " + var )

  head_vars = rule.goalAttList
  body_vars = []
  for sub in rule.ruleData[ "subgoalListOfDicts" ] :
    body_vars.extend( sub[ "subgoalAttList" ] )

  # a variable is unused if it appears only once in the body
  # and not in the head.
  if body_vars.count( var ) < 2 and \
     not var in head_vars       and \
     not var == "_"             and \
     not var.isdigit()          and \
     not "'" in var             and \
     not '"' in var :
    logging.debug( "  IS UNUSED : returning True." )
    return True
  else :
    logging.debug( "  IS UNUSED : returning False." )
    return False


#########
#  EOF  #
#########
