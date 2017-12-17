#!/usr/bin/env python

'''
dedalusRewriter.py
   Define the functionality for rewriting Dedalus into datalog.
'''

import inspect, logging, os, sys

# ------------------------------------------------------ #
# import sibling packages HERE!!!
if not os.path.abspath( __file__ + "/../.." ) in sys.path :
  sys.path.append( os.path.abspath( __file__ + "/../.." ) )

from utils import clockTools, tools, dumpers
import Fact, Rule
# ------------------------------------------------------ #


#############
#  GLOBALS  #
#############

timeAtt_snd    = "NRESERVED"
timeAtt_deliv  = "MRESERVED"


#######################
#  REWRITE DEDUCTIVE  #
#######################
# ruleData = { relationName : 'relationNameStr', 
#              goalAttList:[ data1, ... , dataN ], 
#              goalTimeArg : ""/next/async,
#              subgoalListOfDicts : [ { subgoalName : 'subgoalNameStr', 
#                                       subgoalAttList : [ data1, ... , dataN ], 
#                                       polarity : 'notin' OR '', 
#                                       subgoalTimeArg : <anInteger> }, ... ],
#              eqnDict : { 'eqn1':{ variableList : [ 'var1', ... , 'varI' ] }, 
#                          ... , 
#                          'eqnM':{ variableList : [ 'var1', ... , 'varJ' ] }  } }
def rewriteDeductive( metarule, cursor ) :

  logging.debug( "  REWRITE DEDUCTIVE : running process..." )
  logging.debug( "  REWRITE DEDUCTIVE : metarule.ruleData = " + str( metarule.ruleData ) )

  # ------------------------------------------------------ #
  # dedalus rewrites overwrite the original rules
  # so, grab the original rid

  rid = metarule.rid

  # ------------------------------------------------------ #
  # initialize new version of meta rule to old version of
  # meta rule

  new_metarule_ruleData = metarule.ruleData

  # ------------------------------------------------------ #
  # add SndTime to goal attribute list

  new_metarule_ruleData[ "goalAttList"].append( timeAtt_snd )

  # ------------------------------------------------------ #
  # add SndTime (or given numeric time argument) 
  # to all subgoal attribute lists

  for subgoal in new_metarule_ruleData[ "subgoalListOfDicts" ] :

    # ------------------------------------------------------ #
    # CASE : subgoal time argument in an integer
    if subgoal[ "subgoalTimeArg" ].isdigit() :
      subgoal[ "subgoalAttList" ].append( subgoal[ "subgoalTimeArg" ] )
      subgoal[ "subgoalTimeArg" ] = "" # erase time arg after assignment

    # ------------------------------------------------------ #
    # CASE : subgoal has no time argument
    else :
      subgoal[ "subgoalAttList" ].append( timeAtt_snd )

  # ------------------------------------------------------ #
  # add clock subgoal
  #
  # NOTE!!!! 
  #  Deductive rules do NOT need clock subgoals. I'm adding this b/c
  #  molly adds clock subgoals to deductive rules.
  #  Semantically, the clock subgoals only contribute self-comms,
  #  which are ignored later in the LDFI workflow.

  # grab the first attribute in a subgoal
  # observe the parser ensures the first attributes 
  # in all inductive rule subgoals

  firstAtt = new_metarule_ruleData[ "subgoalListOfDicts" ][0][ "subgoalAttList" ][0]

  # build the new clock subgoal dict
  # format :
  #   { subgoalName : 'subgoalNameStr', 
  #     subgoalAttList : [ data1, ... , dataN ], 
  #     polarity : 'notin' OR '', 
  #     subgoalTimeArg : <anInteger> }

  clock_subgoalName    = "clock"
  clock_subgoalAttList = [ firstAtt, firstAtt, timeAtt_snd, "_" ]
  clock_polarity       = "" # clocks are positive until proven negative.
  clock_subgoalTimeArg = ""

  clock_subgoalDict                      = {}
  clock_subgoalDict[ "subgoalName" ]     = clock_subgoalName
  clock_subgoalDict[ "subgoalAttList" ]  = clock_subgoalAttList
  clock_subgoalDict[ "polarity" ] = clock_polarity
  clock_subgoalDict[ "subgoalTimeArg" ]  = clock_subgoalTimeArg

  # ------------------------------------------------------ #
  # add the clock subgoal to the subgoal list for this rule

  new_metarule_ruleData[ "subgoalListOfDicts" ].append( clock_subgoalDict )

  # ------------------------------------------------------ #
  # preserve adjustments by instantiating the new meta rule
  # as a Rule

  new_metarule = Rule.Rule( rid, new_metarule_ruleData, cursor )

  logging.debug( "  REWRITE DEDUCTIVE : returning new meta rule with rule data = " + str( new_metarule.ruleData ) )
  return new_metarule


#######################
#  REWRITE INDUCTIVE  #
#######################
# ruleData = { relationName : 'relationNameStr', 
#              goalAttList:[ data1, ... , dataN ], 
#              goalTimeArg : ""/next/async,
#              subgoalListOfDicts : [ { subgoalName : 'subgoalNameStr', 
#                                       subgoalAttList : [ data1, ... , dataN ], 
#                                       polarity : 'notin' OR '', 
#                                       subgoalTimeArg : <anInteger> }, ... ],
#              eqnDict : { 'eqn1':{ variableList : [ 'var1', ... , 'varI' ] }, 
#                          ... , 
#                          'eqnM':{ variableList : [ 'var1', ... , 'varJ' ] }  } }
def rewriteInductive( metarule, cursor ) :

  logging.debug( "  REWRITE INDUCTIVE : running process..." )
  logging.debug( "  REWRITE INDUCTIVE : metarule.ruleData = " + str( metarule.ruleData ) )

  # ------------------------------------------------------ #
  # dedalus rewrites overwrite the original rules
  # so, grab the original rid

  rid = metarule.rid

  # ------------------------------------------------------ #
  # initialize new version of meta rule to old version of
  # meta rule

  new_metarule_ruleData = metarule.ruleData

  # ------------------------------------------------------ #
  # add SndTime+1/DelivTime to goal attribute list

  #new_metarule_ruleData[ "goalAttList"].append( timeAtt_snd+"+1" )
  new_metarule_ruleData[ "goalAttList"].append( timeAtt_deliv ) # only works in synchronous communication model.

  # ------------------------------------------------------ #
  # remove goal time arg

  new_metarule_ruleData[ "goalTimeArg"] = ""

  # ------------------------------------------------------ #
  # add SndTime (or given numeric time argument) 
  # to all subgoal attribute lists

  for subgoal in new_metarule_ruleData[ "subgoalListOfDicts" ] :

    # ------------------------------------------------------ #
    # CASE : subgoal time argument in an integer
    if subgoal[ "subgoalTimeArg" ].isdigit() :
      subgoal[ "subgoalAttList" ].append( subgoal[ "subgoalTimeArg" ] )
      subgoal[ "subgoalTimeArg" ] = "" # erase time arg after assignment

    # ------------------------------------------------------ #
    # CASE : subgoal has no time argument
    else :
      subgoal[ "subgoalAttList" ].append( timeAtt_snd )

  # ------------------------------------------------------ #
  # add clock subgoal

  # grab the first attribute in a subgoal
  # observe the parser ensures the first attributes 
  # in all inductive rule subgoals

  firstAtt = new_metarule_ruleData[ "subgoalListOfDicts" ][0][ "subgoalAttList" ][0]

  # build the new clock subgoal dict
  # format :
  #   { subgoalName : 'subgoalNameStr', 
  #     subgoalAttList : [ data1, ... , dataN ], 
  #     polarity : 'notin' OR '', 
  #     subgoalTimeArg : <anInteger> }

  clock_subgoalName    = "clock"
  #clock_subgoalAttList = [ firstAtt, "_", timeAtt_snd, "_" ]
  clock_subgoalAttList = [ firstAtt, "_", timeAtt_snd, "MRESERVED" ] # only works for synchronous model.
  clock_polarity       = "" # clocks are positive until proven negative.
  clock_subgoalTimeArg = ""

  clock_subgoalDict                      = {}
  clock_subgoalDict[ "subgoalName" ]     = clock_subgoalName
  clock_subgoalDict[ "subgoalAttList" ]  = clock_subgoalAttList
  clock_subgoalDict[ "polarity" ] = clock_polarity
  clock_subgoalDict[ "subgoalTimeArg" ]  = clock_subgoalTimeArg

  # ------------------------------------------------------ #
  # add the clock subgoal to the subgoal list for this rule

  new_metarule_ruleData[ "subgoalListOfDicts" ].append( clock_subgoalDict )

  # ------------------------------------------------------ #
  # preserve adjustments by instantiating the new meta rule
  # as a Rule

  new_metarule = Rule.Rule( rid, new_metarule_ruleData, cursor )

  logging.debug( "  REWRITE INDUCTIVE : returning new meta rule with rule data = " + str( new_metarule.ruleData ) )
  return new_metarule


##########################
#  REWRITE ASYNCHRONOUS  #
##########################
# ruleData = { relationName : 'relationNameStr', 
#              goalAttList:[ data1, ... , dataN ], 
#              goalTimeArg : ""/next/async,
#              subgoalListOfDicts : [ { subgoalName : 'subgoalNameStr', 
#                                       subgoalAttList : [ data1, ... , dataN ], 
#                                       polarity : 'notin' OR '', 
#                                       subgoalTimeArg : <anInteger> }, ... ],
#              eqnDict : { 'eqn1':{ variableList : [ 'var1', ... , 'varI' ] }, 
#                          ... , 
#                          'eqnM':{ variableList : [ 'var1', ... , 'varJ' ] }  } }
def rewriteAsynchronous( metarule, cursor ) :

  logging.debug( "  REWRITE ASYNCHRONOUS  : running process..." )
  logging.debug( "  REWRITE ASYNCHRONOUS : metarule.ruleData = " + str( metarule.ruleData ) )

  # ------------------------------------------------------ #
  # dedalus rewrites overwrite the original rules
  # so, grab the original rid

  rid = metarule.rid

  # ------------------------------------------------------ #
  # initialize new version of meta rule to old version of
  # meta rule

  new_metarule_ruleData = metarule.ruleData

  # ------------------------------------------------------ #
  # add DelivTime to goal attribute list

  new_metarule_ruleData[ "goalAttList"].append( timeAtt_deliv )

  # ------------------------------------------------------ #
  # remove goal time arg

  new_metarule_ruleData[ "goalTimeArg"] = ""

  # ------------------------------------------------------ #
  # add SndTime (or given numeric time argument) 
  # to all subgoal attribute lists

  for subgoal in new_metarule_ruleData[ "subgoalListOfDicts" ] :

    # ------------------------------------------------------ #
    # CASE : subgoal time argument in an integer
    if subgoal[ "subgoalTimeArg" ].isdigit() :
      subgoal[ "subgoalAttList" ].append( subgoal[ "subgoalTimeArg" ] )
      subgoal[ "subgoalTimeArg" ] = "" # erase time arg after assignment

    # ------------------------------------------------------ #
    # CASE : subgoal has no time argument
    else :
      subgoal[ "subgoalAttList" ].append( timeAtt_snd )

  # ------------------------------------------------------ #
  # add clock subgoal

  # assum the first att in all subgoals of
  # next rules is the source.
  # grab the first attribute in a subgoal
  # observe the parser ensures the first attributes 
  # in all inductive rule subgoals

  firstAtt  = new_metarule_ruleData[ "subgoalListOfDicts" ][0][ "subgoalAttList" ][0]

  # assume the first att in the goal list of 
  # async rules is the destingation.
  # grab the first attribute in the goal att list
  # observe the parser ensures the first attributes 
  # in all async rule subgoals

  secondAtt = new_metarule_ruleData[ "goalAttList" ][0]

  # build the new clock subgoal dict
  # format :
  #   { subgoalName : 'subgoalNameStr', 
  #     subgoalAttList : [ data1, ... , dataN ], 
  #     polarity : 'notin' OR '', 
  #     subgoalTimeArg : <anInteger> }

  clock_subgoalName    = "clock"
  clock_subgoalAttList = [ firstAtt, secondAtt, timeAtt_snd, timeAtt_deliv ]
  clock_polarity       = "" # clocks are positive until proven negative.
  clock_subgoalTimeArg = ""

  clock_subgoalDict                      = {}
  clock_subgoalDict[ "subgoalName" ]     = clock_subgoalName
  clock_subgoalDict[ "subgoalAttList" ]  = clock_subgoalAttList
  clock_subgoalDict[ "polarity" ] = clock_polarity
  clock_subgoalDict[ "subgoalTimeArg" ]  = clock_subgoalTimeArg

  # ------------------------------------------------------ #
  # add the clock subgoal to the subgoal list for this rule

  new_metarule_ruleData[ "subgoalListOfDicts" ].append( clock_subgoalDict )

  # ------------------------------------------------------ #
  # preserve adjustments by instantiating the new meta rule
  # as a Rule

  logging.debug( "  REWRITE RULES : overwriting old rule with new ruleData = " + str( new_metarule_ruleData ) )
  new_metarule = Rule.Rule( rid, new_metarule_ruleData, cursor )

  logging.debug( "  REWRITE ASYNCHRONOUS : returning new meta rule with rule data = " + str( new_metarule.ruleData ) )
  return new_metarule


###################
#  REWRITE FACTS  #
###################
# update fact schemas with time arguments.
# { relationName:'relationNameStr', dataList:[ data1, ... , dataN ] }
def rewriteFacts( factMeta, cursor ) :

  logging.debug( "  REWRITE FACTS : running process..." )
  logging.debug( "  REWRITE FACTS : factMeta = " + str( factMeta ) )

  for fact in factMeta :

    logging.debug( "  REWRITE FACTS : fact.factData = " + str( fact.factData ) )

    # ------------------------------------------ #
    # grab time arg and reset to ""

    factTimeArg                    = fact.factData[ "factTimeArg" ]
    fact.factData[ "factTimeArg" ] = ""
    fact.factTimeArg               = ""

    # ------------------------------------------ #
    # add time arg to the end of the fact data
    # list

    fact.factData[ "dataList" ].append( factTimeArg )

    # ------------------------------------------ #
    # update data list with types

    fact.dataListWithTypes.append( [ factTimeArg, "int" ] )

    # ------------------------------------------ #
    # perform saves

    fact.saveFactInfo()
    fact.saveFactDataList()

  logging.debug( "  REWRITE FACTS : returning updated fact meta = " + str( factMeta ) )
  return factMeta


#####################
#  DEDALUS REWRITE  #
#####################
# 'rewrite' the rule manifestations in the IR db
# into a format more amenable to datalog translations
def rewriteDedalus( factMeta, ruleMeta, cursor ) :

  logging.debug( "  REWRITE DEDALUS : running rewriteDedalus..." )

  # ------------------------------------ #
  # rewrite rules

  new_ruleMeta = []
  for rule in ruleMeta :

    # ------------------------------------ #
    # rewrite deductive rules
    # (aka rules with no time arg)

    if isDeductive( rule ) :
      new_ruleMeta.append( rewriteDeductive( rule, cursor ) )
  
    # ------------------------------------ #
    # rewrite inductive rules
    # (aka 'next' rules)

    elif isInductive( rule ) :
      new_ruleMeta.append( rewriteInductive( rule, cursor ) )
  
    # ------------------------------------ #
    # rewrite asynchronous rules
    # (aka 'async' rules)

    elif isAsync( rule ) :
      new_ruleMeta.append( rewriteAsynchronous( rule, cursor ) )

    # ------------------------------------ #
    # wtf???

    else :
      sys.exit( "  REWRITE DEDALUS : rule with meta '" + str( rule.ruleData ) + "' is not deductive, inductive, or asynchronous. congratulations. aborting..." )

  # ------------------------------------ #
  # rewrite facts

  new_factMeta = rewriteFacts( factMeta, cursor )

  logging.debug( "  REWRITE DEDALUS : returning meta = " + str( [ new_factMeta, new_ruleMeta ] ) ) 
  return [ new_factMeta, new_ruleMeta ]


##################
#  IS DEDUCTIVE  #
##################
# check if the given rule is deductive
def isDeductive( rule ) :
  if rule.ruleData[ "goalTimeArg" ] == "" :
    return True
  else :
    return False


##################
#  IS INDUCTIVE  #
##################
# check if the given rule is inductive
def isInductive( rule ) :
  if rule.ruleData[ "goalTimeArg" ] == "next" :
    return True
  else :
    return False


##############
#  IS ASYNC  #
##############
# check if the given rule is async
def isAsync( rule ) :
  if rule.ruleData[ "goalTimeArg" ] == "async" :
    return True
  else :
    return False


#########
#  EOF  #
#########
