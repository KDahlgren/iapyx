#/usr/bin/env python

'''
rewrite_wildcards.py
'''

import copy, inspect, logging, os, string, sys

# ------------------------------------------------------ #
# import sibling packages HERE!!!
if not os.path.abspath( __file__ + "/../.." ) in sys.path :
  sys.path.append( os.path.abspath( __file__ + "/../.." ) )

if not os.path.abspath( __file__ + "/../../dedt/translators" ) in sys.path :
  sys.path.append( os.path.abspath( __file__ + "/../../dedt/translators" ) )

from dedt        import Rule
from evaluators  import c4_evaluator
from translators import c4_translator
from utils       import clockTools, tools, dumpers

# ------------------------------------------------------ #

#############
#  GLOBALS  #
#############

arithOps = [ "+", "-", "*", "/" ]


#######################
#  REWRITE WILDCARDS  #
#######################
# rewrite all rules predicated on negated subgoals containing wilcards
def rewrite_wildcards( ruleMeta, cursor ) :

  logging.debug( "  REWRITE WILDCARDS : running process..." )

  # ------------------------------------------- #

  for rule in ruleMeta :

    logging.debug( "  REWRITE WILDCARDS : rule.relationName = " + rule.relationName )    

    if "_nowilds" in rule.relationName and not rule.relationName.startswith( "not_" ) :
      logging.debug( "  REWRITE WILDCARDS : skipping wildcard rewrites." )

    else :

      # ------------------------------------------- #
      # examine all subgoals per rule

      itID = 0 
      nowilds_rules = []
      subgoalListOfDicts = []
      for subgoal in rule.ruleData[ "subgoalListOfDicts" ] :

        logging.debug( "  REWRITE WILDCARDS : subgoal = " + str( subgoal ) )
 
        # ------------------------------------------- #
        # examine all negated subgoals
  
        if subgoal[ "polarity" ] == "notin" :
          logging.debug( "  REWRITE WILDCARDS : hit a notin" )
  
          # ------------------------------------------- #
          # generate new subgoal name
    
          new_subgoalName = subgoal[ "subgoalName" ] + "_nowilds" + str( rule.rid ) + "_" + str( itID )
          itID += 1

          logging.debug( "  REWRITE WILDCARDS : new_subgoalName = " + new_subgoalName )
    
          # ------------------------------------------- #
          # generate new subgoal att list
    
          new_subgoalAttList = []
          for att in subgoal[ "subgoalAttList" ] :
            if not att == "_" :
              new_subgoalAttList.append( att )
    
          # ------------------------------------------- #
          # save new subgoal
    
          new_subgoal = {}
          new_subgoal[ "subgoalName" ]    = new_subgoalName
          new_subgoal[ "subgoalAttList" ] = new_subgoalAttList
          new_subgoal[ "polarity" ]       = subgoal[ "polarity" ]
          new_subgoal[ "subgoalTimeArg" ] = subgoal[ "subgoalTimeArg" ]

          subgoalListOfDicts.append( new_subgoal )
    
          # ------------------------------------------- #
          # build new nowilds rule
    
          nowilds_ruleData = {}
          nowilds_ruleData[ "relationName" ] = new_subgoalName
          nowilds_ruleData[ "goalAttList" ]  = new_subgoalAttList
          nowilds_ruleData[ "goalTimeArg" ]  = ""
          nowilds_ruleData[ "eqnDict" ]      = {}
    
          nowilds_subgoal                          = copy.deepcopy( subgoal )
          nowilds_subgoal[ "polarity" ]            = ""
          nowilds_ruleData[ "subgoalListOfDicts" ] = [ nowilds_subgoal ]
    
          rid = tools.getIDFromCounters( "rid" )
          ruleMeta.append( Rule.Rule( rid, nowilds_ruleData, cursor ) )
          logging.debug( "  REWRITE WILDCARDS : added rule with ruleData = " + str( nowilds_ruleData ) )

        else :
          logging.debug( "  REWRITE WILDCARDS : hit positive subgoal." )
          subgoalListOfDicts.append( subgoal )
    
        # ------------------------------------------- #
        # save original rule with any new subgoal data
    
        rule.ruleData[ "subgoalListOfDicts" ] = subgoalListOfDicts
        rule.subgoalListOfDicts               = subgoalListOfDicts
        rule.saveSubgoals()

  logging.debug( "  REWRITE WILDCARDS : ...done." )
  return ruleMeta


#########
#  EOF  #
#########
