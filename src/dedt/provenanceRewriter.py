#!/usr/bin/env python

'''
provenanceRewriter.py
   Define the functionality for adding provenance rules
   to the datalog program.
'''

import inspect, logging, os, sys

# ------------------------------------------------------ #
# import sibling packages HERE!!!
if not os.path.abspath( __file__ + "/../.." ) in sys.path :
  sys.path.append( os.path.abspath( __file__ + "/../.." ) )

from utils import extractors, tools
import dedalusParser
import Rule
# ------------------------------------------------------ #

#############
#  GLOBALS  #
#############
PROVENANCEREWRITE_DEBUG = tools.getConfig( "DEDT", "PROVENANCEREWRITE_DEBUG", bool )
aggOps = [ "min", "max", "sum", "avg", "count" ]

timeAtt = "SndTime"

##############
#  AGG PROV  #
##############
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
#

def aggProv( aggRule, provid, cursor ) :

  logging.debug( "  AGG PROV : running aggProv..." )

  orig_aggRule_goalAttList = aggRule.ruleData[ "goalAttList" ]

  logging.debug( "  AGG PROV : orig_aggRule_goalAttList = " + str( orig_aggRule_goalAttList ) )

  # ------------------------------------------------------ #
  #                 BUILD THE BINDINGS RULE                #
  # ------------------------------------------------------ #

  # ------------------------------------------------------ #
  # generate a random ID for the new provenance rule

  bindings_rid = tools.getIDFromCounters( "rid" )

  # ------------------------------------------------------ #
  # initialize the prov rule to old version of
  # meta rule

  bindingsmeta_ruleData = aggRule.ruleData

  logging.debug( "  AGG PROV : bindingsmeta_ruleData = " + str( bindingsmeta_ruleData ) )

  # ------------------------------------------------------ #
  # the provenance rule name ends with "_prov" appended 
  # with a unique number

  bindingsmeta_ruleData[ "relationName" ] = bindingsmeta_ruleData[ "relationName" ] + "_bindings" + str( provid )

  # ------------------------------------------------------ #
  # the goal att list consists of all subgoal atts

  bindings_goalAttList = []

  # grab all goal atts
  old_bindings_goalAttList = bindingsmeta_ruleData[ "goalAttList" ]
  bindings_goalAttList     = getAllGoalAtts_noAggs( old_bindings_goalAttList )

  # extract and save the time argument as the last element in the attribute list
  bindings_goalAttList_last = bindings_goalAttList[-1]
  bindings_goalAttList = bindings_goalAttList[:-1]

  # grab all subgoal atts
  subgoalListOfDicts = bindingsmeta_ruleData[ "subgoalListOfDicts" ]

  logging.debug( "  AGG PROV : subgoalListOfDicts = " + str( subgoalListOfDicts ) )

  for subgoal in subgoalListOfDicts :
    subgoalAttList = subgoal[ "subgoalAttList" ]
    for att in subgoalAttList :

      # don't duplicate atts in the prov head
      if not att in bindings_goalAttList :

        # do not wildcards and fixed integer inputs
        if not att == "_" and not att.isdigit() :

          # fixed string inputs
          if not isFixedString( att ) :
            bindings_goalAttList.append( att )

  # add the time argument last
  if not bindings_goalAttList_last in bindings_goalAttList :
    bindings_goalAttList.append( bindings_goalAttList_last )

  # save to rule data
  bindingsmeta_ruleData[ "goal$iAttList" ] = bindings_goalAttList

  # ------------------------------------------------------ #
  # preserve adjustments by instantiating the new meta rule
  # as a Rule

  bindings_rule = Rule.Rule( bindings_rid, bindingsmeta_ruleData, cursor )


  # ------------------------------------------------------ #
  #              BUILD THE AGG PROVENANCE RULE             #
  # ------------------------------------------------------ #

  # ------------------------------------------------------ #
  # generate a random ID for the new provenance rule

  aggprovmeta_rid = tools.getIDFromCounters( "rid" )

  # ------------------------------------------------------ #
  # initialize rule data

  aggprovmeta_ruleData = {}

  # ------------------------------------------------------ #
  # the provenance rule name ends with "_bindings" appended 
  # with a unique number

  aggprovmeta_ruleData[ "relationName" ] = aggRule.ruleData[ "relationName" ] + "_prov" + str( provid )

  # ------------------------------------------------------ #
  # the goal att list consists of all subgoal atts

  aggprovmeta_ruleData[ "goalAttList" ] = orig_aggRule_goalAttList

  # ------------------------------------------------------ #
  # define goal time arg as empty

  aggprovmeta_ruleData[ "goalTimeArg" ] = ""

  # ------------------------------------------------------ #
  # define subgoal list of dicts
  # agg prov rules only have one subgoal in the head of
  # the previously defined bindings rule

  subgoalListOfDicts = []
  bindings_subgoal   = {}
  bindings_subgoal[ "subgoalName" ] = bindingsmeta_ruleData[ "relationName" ]

  # replace all existential vars in the subgoal att list with wildcards
  allGoalAtts    = getAllGoalAtts_noAggs( aggprovmeta_ruleData[ "goalAttList" ] )
  allSubgoalAtts = bindingsmeta_ruleData[ "goalAttList" ]

  subgoalAttList = []
  for att in allSubgoalAtts :
    if not att in allGoalAtts :
      subgoalAttList.append( "_" )
    else :
      subgoalAttList.append( att )

  bindings_subgoal[ "subgoalAttList" ] = subgoalAttList
  bindings_subgoal[ "polarity" ]       = ""
  bindings_subgoal[ "subgoalTimeArg" ] = ""

  subgoalListOfDicts.append( bindings_subgoal )
  aggprovmeta_ruleData[ "subgoalListOfDicts" ] = subgoalListOfDicts

  # ------------------------------------------------------ #
  # define eqnDict as empty

  aggprovmeta_ruleData[ "eqnDict" ] = {}

  # ------------------------------------------------------ #
  # preserve adjustments by instantiating the new meta rule
  # as a Rule

  aggprovmeta_rule = Rule.Rule( aggprovmeta_rid, aggprovmeta_ruleData, cursor )


  return [ bindings_rule, aggprovmeta_rule ]



###############################
#  GET ALL GOAL ATTS NO AGGS  #
###############################
# return the list of attributes in the att list
# after extracting attributes from any aggregate
# functions
def getAllGoalAtts_noAggs( attList ) :

  atts_wo_aggs_list = []

  for att in attList :
    if hasAgg( att ) :
      att_wo_agg = att.split( "<")
      att_wo_agg = att_wo_agg[1]
      att_wo_agg = att_wo_agg.replace( ">", "" )
      atts_wo_aggs_list.append( att_wo_agg )
    else :
      atts_wo_aggs_list.append( att )

  return atts_wo_aggs_list


#######################
#  REGULAR RULE PROV  #
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
def regProv( regRule, nameAppend, cursor ) :

  logging.debug( "  REG PROV : running regProv..." )

  # ------------------------------------------------------ #
  # generate a random ID for the new provenance rule

  rid = tools.getIDFromCounters( "rid" )

  # ------------------------------------------------------ #
  # initialize the prov rule to old version of
  # meta rule

  new_provmeta_ruleData = regRule.ruleData

  # ------------------------------------------------------ #
  # the provenance rule name ends with "_prov" appended 
  # with a unique number

  new_provmeta_ruleData[ "relationName" ] = new_provmeta_ruleData[ "relationName" ] + nameAppend

  # ------------------------------------------------------ #
  # the goal att list consists of all subgoal atts

  provGoalAttList = []

  # grab all goal atts
  goalAttList = new_provmeta_ruleData[ "goalAttList" ]

  # save to provenance rule goal attribute list
  provGoalAttList.extend( goalAttList )

  # extract and save the time argument as the last element in the attribute list
  provGoalAttList_last = provGoalAttList[-1]
  provGoalAttList      = provGoalAttList[:-1]

  # grab all subgoal atts
  subgoalListOfDicts = new_provmeta_ruleData[ "subgoalListOfDicts" ]
  for subgoal in subgoalListOfDicts :
    subgoalAttList = subgoal[ "subgoalAttList" ]
    for att in subgoalAttList :

      # don't duplicate atts in the prov head
      if not att in provGoalAttList :

        # do not wildcards and fixed integer inputs
        if not att == "_" and not att.isdigit() :

          # fixed string inputs
          if not isFixedString( att ) :
            provGoalAttList.append( att )

  # add the time argument last
  if not provGoalAttList_last in provGoalAttList :
    provGoalAttList.append( provGoalAttList_last )

  # save to rule data
  new_provmeta_ruleData[ "goalAttList" ] = provGoalAttList

  # ------------------------------------------------------ #
  # preserve adjustments by instantiating the new meta rule
  # as a Rule

  provRule = Rule.Rule( rid, new_provmeta_ruleData, cursor )

  logging.debug( "  REG PROV : returning provRule.ruleData = " + str( provRule.ruleData ) )

  return provRule


########################
#  REWRITE PROVENANCE  #
########################
def rewriteProvenance( ruleMeta, cursor ) :

  logging.debug( " REWRITE PROVENANCE : running process..." ) 
  logging.debug( " REWRITE PROVENANCE : len( ruleMeta ) = " + str( len( ruleMeta ) ) ) 

  # -------------------------------------------------- #
  # iterate over rules

  prov_ruleMeta    = []
  provid           = 0
  previousGoalName = ""
  for rule in ruleMeta :

    logging.debug( "  REWRITE PROVENANCE : ruleData = " + str( rule.ruleData ) )

    # -------------------------------------------------- #
    # make all provenance name append numbers start from
    # 0 for each new rule name

    goalName = rule.ruleData[ "relationName" ]

    # don't need to be this smart when comparing output w/ molly
    #if goalName == previousGoalName :
    #  pass
    #else :
    #  provid = 0

    # -------------------------------------------------- #
    # CASE : rule contains aggregate calls in the head

    if containsAggInHead( rule ) :
      provRules = aggProv( rule, provid, cursor )
      prov_ruleMeta.extend( provRules )

    # -------------------------------------------------- #
    # CASE : rule contains no aggregate calls 
    #        in the head

    else :
      provRule = regProv( rule, "_prov" + str( provid ), cursor )
      prov_ruleMeta.append( provRule )

    # -------------------------------------------------- #
    # update iteration info
    previousGoalName = goalName
    provid += 1

  logging.debug( " REWRITE PROVENANCE : returning prov_ruleMeta = " + str( prov_ruleMeta ) )
  return prov_ruleMeta


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


##########################
#  CONTAINS AGG IN HEAD  #
##########################
# check if the rule head contains an aggregate function call
def containsAggInHead( metarule ) :

  for att in metarule.goalAttList :
    for op in aggOps :
      if att.startswith( op+"<" ) and att.endswith( ">" ) :
        return True

  return False


#############
#  HAS AGG  #
#############
# determine if the given input string contains an aggregate call
def hasAgg( gattName ) :

  # check for aggregate operators
  for op in aggOps :
    if gattName.startswith( op+"<" ) and gattName.endswith( ">" ) :
      return True

  return False


#########
#  EOF  #
#########
