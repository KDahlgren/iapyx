#/usr/bin/env python

'''
dm.py
   Define the functionality for collecting the provenance of negative subgoals
   using the DeMorgan's Law method for negative rewrites..
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
      if IDENTICAL_SUBS == len( target_rule ) :
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

#    if newRule.relationName == "orig_log" :
#      print dumpers.reconstructRule( rule.rid, rule.cursor )
#      print rule.goal_att_type_list
#      sys.exit( "blah" )

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
  for rule in ruleMeta :
    logging.debug( "  REPLACE UNUSED VARS : rule (before) :\n     >" + \
                   dumpers.reconstructRule( rule.rid, rule.cursor ) )
    subgoalChanged = False
    for i in range( 0, len ( rule.ruleData[ "subgoalListOfDicts" ] ) ):
      sub = rule.ruleData[ "subgoalListOfDicts" ][ i ]
      for j in range( 0, len( sub[ "subgoalAttList" ] ) ) :
        if is_unused( sub[ "subgoalAttList" ][ j ], rule ) :
          rule.ruleData[ "subgoalListOfDicts" ][ i ][ "subgoalAttList" ][ j ] = "_"
          subgoalChanged = True
    if subgoalChanged :
      rule.subgoalListOfDicts = rule.ruleData[ "subgoalListOfDicts" ]
      rule.saveSubgoals()
    logging.debug( "  REPLACE UNUSED VARS : rule (after) :\n     >" + \
                   dumpers.reconstructRule( rule.rid, rule.cursor ) )

  return ruleMeta


###############
#  IS UNUSED  #
###############
def is_unused( var, rule ) :

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
