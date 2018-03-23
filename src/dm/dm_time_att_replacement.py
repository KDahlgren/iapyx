#/usr/bin/env python

'''
dm_time_att_replacement.py
'''

import copy, inspect, logging, os, string, sys
import ConfigParser

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

arithOps = [ "+", "-", "*", "/" ]


#############################
#  DM TIME ATT REPLACEMENT  #
#############################
# rewrite the goal attributes of rules defined by 
# some mixture of deductive, inductive, and async rules.
# ruleMeta := a list of Rule objects
def dm_time_att_replacement( ruleMeta, cursor, argDict ) :

  logging.debug( "  DM TIME ATT REPLACEMENT : running process..." )

  replacement_time_att = "MRESERVED"

  target_rule_sets = getRuleMetaSets( ruleMeta, cursor )

  for ruleSet in target_rule_sets :
    logging.debug( ".........." )
    for rule in ruleSet :
      logging.debug( rule.relationName + ", " + str( rule.goalAttList ) + ", " + str( rule.hitUniformityRewrites ) )
  #sys.exit( "blah" )

  # replace the time att
  for ruleSet in target_rule_sets :
    for rule in ruleSet :

      if rule.hitUniformityRewrites == True :
 
        target_att = rule.goalAttList[-1]
 
        # save new goal attribute list
        rule.ruleData[ "goalAttList" ] = rule.goalAttList[:-1] + [ replacement_time_att ]
        rule.goalAttList               = rule.goalAttList[:-1] + [ replacement_time_att ]
        rule.saveToGoalAtt()
  
        new_subgoalListOfDicts = []
        for sub in rule.ruleData[ "subgoalListOfDicts" ] :
  
          subgoalAttList     = sub[ "subgoalAttList" ]
          new_subgoalAttList = []
  
          for satt in subgoalAttList :
            if satt == target_att :
              new_subgoalAttList.append( replacement_time_att )
            else :
              new_subgoalAttList.append( satt )
 
          new_sub_dict = {}
          new_sub_dict[ "subgoalName" ]    = sub[ "subgoalName" ]
          new_sub_dict[ "subgoalAttList" ] = new_subgoalAttList
          new_sub_dict[ "polarity" ]       = sub[ "polarity" ]
          new_sub_dict[ "subgoalTimeArg" ] = sub[ "subgoalTimeArg" ]
          new_subgoalListOfDicts.append( new_sub_dict )
  
        # save new subgoals
        rule.ruleData[ "subgoalListOfDicts" ] = new_subgoalListOfDicts
        rule.subgoalListOfDicts               = new_subgoalListOfDicts
        rule.saveSubgoals()

  for rule in ruleMeta :
    logging.debug( dumpers.reconstructRule( rule.rid, cursor ) )
  #sys.exit( "blah" )

  logging.debug( "  DM TIME ATT REPLACEMENT : ...done." )

  return ruleMeta


########################
#  GET RULE META SETS  #
########################
# obtain the list of lists of rule objects corresponding to the idb definitions
# of idbs corresponding to negated subgoals in one or more rules
def getRuleMetaSets( ruleMeta, cursor ) :

  logging.debug( "  GET RULE META SETS : ruleMeta with len(ruleMeta) = " + str( len( ruleMeta ) ) )

  set_dict = {}

  # ----------------------------------------- #
  # get all relation names

  all_names = []
  for rule in ruleMeta :
    if not rule.relationName in all_names :
      all_names.append( rule.relationName )

  # ----------------------------------------- #
  # iterate over rule meta

  for name in all_names :
    for rule in ruleMeta :
      if rule.relationName == name :
        if name in set_dict :
          set_dict[ name ].append( rule )
        else :
          set_dict[ name ] = [ rule ]

  # ----------------------------------------- #
  # convert dictionary into a list of lists

  targetRuleMetaSets = []
  for name in set_dict :
    targetRuleMetaSets.append( set_dict[ name ] )

  return targetRuleMetaSets


#########
#  EOF  #
#########
