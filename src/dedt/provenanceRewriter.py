#!/usr/bin/env python

'''
provenanceRewriter.py
   Define the functionality for adding provenance rules
   to the datalog program.
'''

import ConfigParser, copy, inspect, logging, os, sys

# ------------------------------------------------------ #
# import sibling packages HERE!!!
if not os.path.abspath( __file__ + "/../.." ) in sys.path :
  sys.path.append( os.path.abspath( __file__ + "/../.." ) )

from utils import dumpers, extractors, tools
import dedalusParser
import Rule
# ------------------------------------------------------ #

#############
#  GLOBALS  #
#############

aggOps  = [ "min", "max", "sum", "avg", "count" ]
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

def aggProv( aggRule, provid, cursor, argDict ) :

  logging.debug( "  AGG PROV : running aggProv..." )

  try :
    USING_MOLLY = tools.getConfig( argDict[ "settings" ], "DEFAULT", "USING_MOLLY", bool )
  except ConfigParser.NoOptionError :
    logging.warning( "WARNING : no 'USING_MOLLY' defined in 'DEFAULT' section of settings.ini ...assume running without molly." )
    USING_MOLLY = False

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

  bindingsmeta_ruleData = {}
  for key in aggRule.ruleData :
    val = aggRule.ruleData[ key ]
    bindingsmeta_ruleData[ key ] = val

  logging.debug( "  AGG PROV : bindingsmeta_ruleData = " + str( bindingsmeta_ruleData ) )

  # ------------------------------------------------------ #
  # the provenance rule name ends with "_prov" appended 
  # with a unique number

  # NOTE!!!! LDFI paper says "_bindings", but molly implementation actually uses "_vars" append. >~<

  #bindingsmeta_ruleData[ "relationName" ] = bindingsmeta_ruleData[ "relationName" ] + "_bindings" + str( provid )
  bindingsmeta_ruleData[ "relationName" ] = bindingsmeta_ruleData[ "relationName" ] + "_vars"

  # ------------------------------------------------------ #
  # the goal att list consists of all subgoal atts

  bindings_goalAttList = []

  # grab all goal atts
  old_bindings_goalAttList = bindingsmeta_ruleData[ "goalAttList" ]
  bindings_goalAttList     = getAllGoalAtts_noAggs( old_bindings_goalAttList )

  # extract and save the time argument as the last element in the attribute list
  bindings_goalAttList_last = bindings_goalAttList[-1]
  bindings_goalAttList      = bindings_goalAttList[:-1]

  # grab all subgoal atts
  subgoalListOfDicts = bindingsmeta_ruleData[ "subgoalListOfDicts" ]

  logging.debug( "  AGG PROV : subgoalListOfDicts = " + str( subgoalListOfDicts ) )

  for subgoal in subgoalListOfDicts :
    subgoalAttList = subgoal[ "subgoalAttList" ]
    for att in subgoalAttList :

      # don't duplicate atts in the prov head
      if not att in bindings_goalAttList :

        # do not add wildcards and fixed integer inputs
        if not att == "_" and not att.isdigit() :

          # do not add fixed string inputs
          if not isFixedString( att ) :
            bindings_goalAttList.append( att )

  # add the time argument last
  if not bindings_goalAttList_last in bindings_goalAttList :
    bindings_goalAttList.append( bindings_goalAttList_last )

  # save to rule data
  if USING_MOLLY :
    bindings_goalAttList                   = sortGoalAttList( bindings_goalAttList )
  bindingsmeta_ruleData[ "goalAttList" ] = bindings_goalAttList

  # ------------------------------------------------------ #
  # preserve adjustments by instantiating the new meta rule
  # as a Rule

  bindings_rule = Rule.Rule( bindings_rid, bindingsmeta_ruleData, cursor )
  bindings_rule.rule_type = aggRule.rule_type

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

  if USING_MOLLY :
    orig_aggRule_goalAttList = sortGoalAttList( orig_aggRule_goalAttList )

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
  aggprovmeta_rule.rule_type = aggRule.rule_type

  # ------------------------------------------------------ #
  #               REWRITE ORIGINAL AGG RULE                #
  # ------------------------------------------------------ #

  # ------------------------------------------------------ #

  # update rule meta with the new bindings subgoal
  aggRule.ruleData[ "subgoalListOfDicts" ] = aggprovmeta_rule.ruleData[ "subgoalListOfDicts" ]
  aggRule.subgoalListOfDicts               = aggRule.ruleData[ "subgoalListOfDicts" ]

  # save new subgoal data
  aggRule.saveSubgoals()

  # ------------------------------------------------------ #

  # update rule meta with the new empty eqn dict
  aggRule.ruleData[ "eqnDict" ] = aggprovmeta_rule.ruleData[ "eqnDict" ]
  aggRule.eqnDict               = aggRule.ruleData[ "eqnDict" ]

  # save new subgoal data
  aggRule.saveEquations()

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
def regProv( regRule, nameAppend, cursor, argDict ) :

  try :
    USING_MOLLY = tools.getConfig( argDict[ "settings" ], "DEFAULT", "USING_MOLLY", bool )
  except ConfigParser.NoOptionError :
    logging.warning( "WARNING : no 'USING_MOLLY' defined in 'DEFAULT' section of settings.ini ...assume running without molly." )
    USING_MOLLY = False

  logging.debug( "  REG PROV : running regProv..." )
  logging.debug( "  REG PROV : regRule              = " + str( regRule ) )
  logging.debug( "  REG PROV : regRule.relationName = " + regRule.relationName )

  # ------------------------------------------------------ #
  # generate a random ID for the new provenance rule

  rid = tools.getIDFromCounters( "rid" )

  # ------------------------------------------------------ #
  # initialize the prov rule to old version of
  # meta rule

  new_provmeta_ruleData = copy.deepcopy( regRule.ruleData )

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
#  provGoalAttList_last = provGoalAttList[-1]
#  provGoalAttList      = provGoalAttList[:-1]

  # ------------------------------------------------------------------ #
  # grab all subgoal atts

  subgoalListOfDicts = new_provmeta_ruleData[ "subgoalListOfDicts" ]
  for subgoal in subgoalListOfDicts :
    subgoalAttList = subgoal[ "subgoalAttList" ]
    for att in subgoalAttList :

      logging.debug( "  REG PROV : att in subgoalAttList = " + att )

      # don't duplicate atts in the prov head
      if not att in provGoalAttList :

        logging.debug( "  REG PROV : att not in " + str( provGoalAttList ) )

        # do not add wildcards and fixed integer inputs
        if not att == "_" and not att.isdigit() :

          logging.debug( "  REG PROV : att not '_' and not isdigit" )

          # do not add fixed string inputs
          # do not add unused variables (huh? why? messes up not_rule arities)
          #if not isFixedString( att ) and not isUnused( subgoalListOfDicts, new_provmeta_ruleData[ "eqnDict" ], att ) :
          if not isFixedString( att ) :
            provGoalAttList.append( att )

  # ------------------------------------------------------------------ #
  # add the time argument last

#  if not provGoalAttList_last in provGoalAttList :
#    provGoalAttList.append( provGoalAttList_last )

  # ------------------------------------------------------------------ #

  logging.debug( "  REG PROV : new_provmeta_ruleData['relationName'] = " + new_provmeta_ruleData[ "relationName" ]  )
  logging.debug( "  REG PROV : provGoalAttList                       = " + str( provGoalAttList ) )

  # sort goal atts to ensure NRESERVED, NRESERVED+1, and MRESERVED are rightmost
  if USING_MOLLY :
    provGoalAttList = sortGoalAttList( provGoalAttList )

  logging.debug( "  REG PROV : provGoalAttList (after sorting)       = " + str( provGoalAttList ) )

  # save to rule data
  new_provmeta_ruleData[ "goalAttList" ] = provGoalAttList

  # ------------------------------------------------------ #
  # preserve adjustments by instantiating the new meta rule
  # as a Rule

  provRule               = Rule.Rule( rid, new_provmeta_ruleData, cursor )
  provRule.orig_rule_ptr = regRule
  provRule.rule_type     = regRule.rule_type

  logging.debug( "  REG PROV : regRule                  = " + str( regRule ) )
  logging.debug( "  REG PROV : regRule.orig_goalAttList = " + str( regRule.orig_goalAttList ) )
  logging.debug( "  REG PROV : provRule.orig_rule_ptr   = " + str( provRule.orig_rule_ptr ) )
  logging.debug( "  REG PROV : provRule.orig_rule_ptr.orig_goalAttList = " + str( provRule.orig_rule_ptr.orig_goalAttList ) )
  logging.debug( "  REG PROV : returning prov rule id " + str( rid ) + " provRule.ruleData = " + str( provRule.ruleData ) )
  logging.debug( "  REG PROV : provRule.relationName       = " + provRule.relationName )
  logging.debug( "  REG PROV : provRule.goalAttList        = " + str( provRule.goalAttList ) )
  logging.debug( "  REG PROV : provRule.goalTimeArg        = " + provRule.goalTimeArg )
  logging.debug( "  REG PROV : provRule.subgoalListOfDicts = " + str( provRule.subgoalListOfDicts ) )
  logging.debug( "  REG PROV : provRule.eqnDict            = " + str( provRule.eqnDict ) )
  logging.debug( "  REG PROV : provRule.orig_rule_ptr      = " + str( provRule.orig_rule_ptr ) )
  logging.debug( "  REG PROV : provRule.orig_rule_ptr.goalAttList = " + str( provRule.orig_rule_ptr.goalAttList ) )

  #if provRule.relationName == "not_missing_log_prov8" :
  #  sys.exit( "blah" )

  # ------------------------------------------------------ #
  # replace original time goal atts

#  if tools.getConfig( argDict[ "settings" ], "DEFAULT", "DM", bool ) :
#    provRule = replaceTimeAtts( provRule )
#
#  logging.debug( "  REG PROV : returning prov rule id " + str( rid ) + " provRule.ruleData = " + str( provRule.ruleData ) )
#  logging.debug( "  REG PROV : provRule.relationName       = " + provRule.relationName )
#  logging.debug( "  REG PROV : provRule.goalAttList        = " + str( provRule.goalAttList ) )
#  logging.debug( "  REG PROV : provRule.goalTimeArg        = " + provRule.goalTimeArg )
#  logging.debug( "  REG PROV : provRule.subgoalListOfDicts = " + str( provRule.subgoalListOfDicts ) )
#  logging.debug( "  REG PROV : provRule.eqnDict            = " + str( provRule.eqnDict ) )

  return provRule


###############
#  IS UNUSED  #
###############
# check if the input subgoal attribute is unused.
def isUnused( subgoalListOfDicts, eqn_dict, satt ) :

  # get list of all subgoal attributes
  all_satts = []
  for sub in subgoalListOfDicts :
    all_satts.extend( sub[ "subgoalAttList" ] )

  for eq in eqn_dict :
    for var in eqn_dict[ eq ] :
      if not isFixedString( var ) :
        all_satts.extend( eqn_dict[ eq ] )

  # time refs are always copied to the goal att list
  if satt == "NRSERVED" or \
     satt == "MRESERVED" :
    return False

  if all_satts.count( satt ) > 1 :
    logging.debug( " IS UNUSED : returning False" )
    return False
  else :
    logging.debug( " IS UNUSED : returning True" )
    return True


#######################
#  REPLACE TIME ATTS  #
#######################
# input a dm-rewritten rule 
# replace uniform atts referencing time 
# atts with the fixed att strings referencing time.
# observe every rewritten dedalus rule will contain
# a maximum of one time reference.
# also, replace all unused variables with wildcards.
def replaceTimeAtts( rule ) :

  logging.debug( "  REPLACE TIME ATTS : running process..." )

  logging.debug( "  REPLACE TIME ATTS : ======================================" )
  logging.debug( "  REPLACE TIME ATTS : running process..." )
  logging.debug( "  REPLACE TIME ATTS : rule.relationName  = " + str( rule.relationName ) )
  logging.debug( "  REPLACE TIME ATTS : rule.ruleData      = " + str( rule.ruleData ) )
  logging.debug( "  REPLACE TIME ATTS : rule.orig_rule_ptr = " + str( rule.orig_rule_ptr ) )
  logging.debug( "  REPLACE TIME ATTS : rule.orig_rule_ptr.orig_goal_time_type = " + str( rule.orig_rule_ptr.orig_goal_time_type ) )
  logging.debug( "  REPLACE TIME ATTS : rule.orig_rule_ptr.orig_rule_attMapper  = " + str( rule.orig_rule_ptr.orig_rule_attMapper ) )
  logging.debug( "  REPLACE TIME ATTS : rule.orig_rule_ptr.orig_rule_attMapper_aggRewrites  = " + str( rule.orig_rule_ptr.orig_rule_attMapper_aggRewrites ) )
  logging.debug( "  REPLACE TIME ATTS : rule.orig_rule_ptr.orig_goal_time_type  = " + str( rule.orig_rule_ptr.orig_goal_time_type ) )
  logging.debug( "  REPLACE TIME ATTS : rule.goalAttList = " + str( rule.goalAttList ) )
  logging.debug( "  REPLACE TIME ATTS : rule.orig_rule_ptr._orig_goalAttList = " + str( rule.orig_rule_ptr.orig_goalAttList ) )

  goalAttList = copy.deepcopy( rule.goalAttList )

  # ----------------------------------------- #
  # replace all unused vars with wildcards

  logging.debug( "  REPLACE TIME ATTS : executing wildcard replacement..." )

  subgoalAttList_complete = []
  subgoalListOfDicts      = copy.deepcopy( rule.subgoalListOfDicts )
  for subgoal in subgoalListOfDicts :
    subgoalAttList_complete.extend( subgoal[ "subgoalAttList" ] )

  countMapper = {}
  for satt in subgoalAttList_complete :
    if not satt in countMapper :
      countMapper[ satt ] = 1
    else :
      countMapper[ satt ] += 1

  new_subgoalListOfDicts = []
  for subgoal in subgoalListOfDicts :
    new_subgoalDict = {}
    new_subgoalDict[ "subgoalName" ]    = subgoal[ "subgoalName" ]
    new_subgoalDict[ "polarity" ]       = subgoal[ "polarity" ]
    new_subgoalDict[ "subgoalTimeArg" ] = subgoal[ "subgoalTimeArg" ]
    new_subgoalDict[ "subgoalAttList" ] = []

    orig_subgoalAttList = subgoal[ "subgoalAttList" ]
    for satt in orig_subgoalAttList :

      # keep all fixed data in subgoals
      if isFixedString( satt ) or satt.isdigit() :
        new_subgoalDict[ "subgoalAttList" ].append( satt )
        continue

      if countMapper[ satt ] > 1 or satt in goalAttList :
        new_subgoalDict[ "subgoalAttList" ].append( satt )
      else :
        new_subgoalDict[ "subgoalAttList" ].append( "_" )

    new_subgoalListOfDicts.append( copy.deepcopy( new_subgoalDict ) )

  rule.subgoalListOfDicts               = copy.deepcopy( new_subgoalListOfDicts )
  rule.ruleData[ "subgoalListOfDicts" ] = copy.deepcopy( new_subgoalListOfDicts )
  rule.saveSubgoals()

  logging.debug( "  REPLACE TIME ATTS : ...wildcard replacement done." )

  # ----------------------------------------- #
  # replace all instances of the rightmost 
  # att of the original rule with MRESERVED
  # (this probably breaks in async model)
  # not_ rules only!

#  if rule.relationName.startswith( "not_" ) :
#
#    logging.debug( "  REPLACE TIME ATTS : time att replacement in not_ rule..." )
#
#    orig_rightmost = rule.orig_rule_ptr.goalAttList[ -1 ]
#    orig_rightmost = orig_rightmost.split( "+" )[ 0 ] # next time args always use '+'
#  
#    new_goalAttList = []
#    for gatt in rule.goalAttList :
##      if gatt == orig_rightmost :
##        new_goalAttList.append( "MRESERVED" )
##      elif gatt == orig_rightmost + "+1" :
#      if gatt == orig_rightmost + "+1" :
#        new_goalAttList.append( "MRESERVED" )
#      else :
#        new_goalAttList.append( gatt )
#  
#    new_goalAttList = sortGoalAttList( new_goalAttList )
#  
#    rule.ruleData[ "goalAttList" ] = new_goalAttList
#    rule.goalAttList               = new_goalAttList
#    rule.saveToGoalAtt()
#  
#    subgoalListOfDicts     = copy.deepcopy( rule.subgoalListOfDicts )
#    new_subgoalListOfDicts = []
#    for subgoal in subgoalListOfDicts :
#      new_subgoalDict = {}
#      new_subgoalDict[ "subgoalName" ]    = subgoal[ "subgoalName" ]
#      new_subgoalDict[ "polarity" ]       = subgoal[ "polarity" ]
#      new_subgoalDict[ "subgoalTimeArg" ] = subgoal[ "subgoalTimeArg" ]
#      new_subgoalDict[ "subgoalAttList" ] = []
#  
#      orig_subgoalAttList = subgoal[ "subgoalAttList" ]
#      for satt in orig_subgoalAttList :
#        if satt == orig_rightmost :
#          new_subgoalDict[ "subgoalAttList" ].append( "MRESERVED" )
#        else :
#          new_subgoalDict[ "subgoalAttList" ].append( satt )
#  
#      new_subgoalListOfDicts.append( copy.deepcopy( new_subgoalDict ) )
#
#    rule.subgoalListOfDicts               = copy.deepcopy( new_subgoalListOfDicts )
#    rule.ruleData[ "subgoalListOfDicts" ] = copy.deepcopy( new_subgoalListOfDicts )
#    rule.saveSubgoals()
#
#  logging.debug( "  REPLACE TIME ATTS : ...time att replacement in not_ rule done." )
#
#  if rule.relationName == "not_a_timer_agg1_prov43" :
#    logging.debug( rule.ruleData )
#    sys.exit( "blah_replaceTimeAtt" )

  # ----------------------------------------- #
  # replace all uniform attributes 
  # representing time references with the
  # original time references

  # ========================================= #
  # handle time ref replacement in 
  # next and async rules :

  if rule.orig_rule_ptr.orig_goal_time_type == "next" or \
     rule.orig_rule_ptr.orig_goal_time_type == "async" :

    logging.debug( "  REPLACE TIME ATTS : hit inductive or async rule ..." )

    orig_rightmost       = rule.orig_rule_ptr.orig_goalAttList[ -1 ]
    new_second_rightmost = rule.goalAttList[ -2 ]

    logging.debug( "  REPLACE TIME ATTS : orig_rightmost       = " + orig_rightmost )
    logging.debug( "  REPLACE TIME ATTS : new_second_rightmost = " + new_second_rightmost )

    if not new_second_rightmost == "NRESERVED" and \
       not new_second_rightmost == "NRESERVED+1" :

      logging.debug( " rule.relationName                   = " + rule.relationName )
      logging.debug( " rule.orig_rule_ptr.orig_goalAttList = " + str( rule.orig_rule_ptr.orig_goalAttList ) )
      logging.debug( " rule.goalAttList                    = " + str( rule.goalAttList ) )
      logging.debug( " orig_rightmost                      = " + str( orig_rightmost ) )
      logging.debug( " new_second_rightmost                = " + str( new_second_rightmost ) )
  
      # replace the time reference in the goal
      new_goalAttList = []
      for gatt in rule.goalAttList :
        new_second_rightmost_att = new_second_rightmost.split( "+" )[0]
        if gatt == new_second_rightmost :
          new_goalAttList.append( orig_rightmost )
        elif gatt.startswith( new_second_rightmost_att ) :
          orig_rightmost_att = orig_rightmost.split( "+" )[0]
          new_goalAttList.append( orig_rightmost_att )
        else :
          new_goalAttList.append( gatt )
 
      logging.debug( " **new_goalAttList = " + str( new_goalAttList ) ) 

      gattMapper = {}
      for i in range( 0, len( rule.goalAttList ) ) :
        gattMapper[ rule.goalAttList[ i ] ] = new_goalAttList[ i ]

      if USING_MOLLY :
        new_goalAttList = sortGoalAttList( new_goalAttList )
  
      rule.ruleData[ "goalAttList" ] = new_goalAttList
      rule.goalAttList               = new_goalAttList
      rule.saveToGoalAtt()
  
      # replace the time reference in the subgoals
      new_subgoalListOfDicts = []
      for subgoal in subgoalListOfDicts :
        new_subgoalDict = {}
        new_subgoalDict[ "subgoalName" ]    = subgoal[ "subgoalName" ]
        new_subgoalDict[ "polarity" ]       = subgoal[ "polarity" ]
        new_subgoalDict[ "subgoalTimeArg" ] = subgoal[ "subgoalTimeArg" ]
        new_subgoalDict[ "subgoalAttList" ] = []
    
        # replace all instances of new_rightmost with orig_rightmost
        orig_subgoalAttList = subgoal[ "subgoalAttList" ]
        for satt in orig_subgoalAttList :
          if satt in gattMapper :
            new_subgoalDict[ "subgoalAttList" ].append( gattMapper[ satt ] )
          else :
            new_subgoalDict[ "subgoalAttList" ].append( satt )

        new_subgoalListOfDicts.append( copy.deepcopy( new_subgoalDict ) )
    
      rule.subgoalListOfDicts               = copy.deepcopy( new_subgoalListOfDicts )
      rule.ruleData[ "subgoalListOfDicts" ] = copy.deepcopy( new_subgoalListOfDicts )
      rule.saveSubgoals()

  # ========================================= #
  # handle time ref replacement in 
  # deductive rules :

  elif rule.orig_rule_ptr.orig_goal_time_type == "" :

    logging.debug( "  REPLACE TIME ATTS : hit deductive rule ..." )

    if rule.relationName.startswith( "not_" ) :
      orig_rightmost = "MRESERVED"
    else :
      orig_rightmost = rule.orig_rule_ptr.orig_goalAttList[ -1 ]

    new_rightmost = rule.orig_rule_ptr.goalAttList[ -1 ]
    new_rightmost = new_rightmost.split( "+" )[0]

    logging.debug( " rule.relationName                   = " + rule.relationName )
    logging.debug( " rule.orig_rule_ptr.orig_goalAttList = " + str( rule.orig_rule_ptr.orig_goalAttList ) )
    logging.debug( " rule.goalAttList                    = " + str( rule.goalAttList ) )
    logging.debug( " orig_rightmost                      = " + str( orig_rightmost ) )
    logging.debug( " new_rightmost                       = " + str( new_rightmost ) )

    # replace the time reference in the goal
    new_goalAttList = []
    for gatt in rule.goalAttList :
      logging.debug( "> gatt = " + gatt )
      if gatt == new_rightmost :
        new_goalAttList.append( orig_rightmost )
      elif gatt == new_rightmost + "+1" :
        new_goalAttList.append( orig_rightmost + "+1" )
      else :
        new_goalAttList.append( gatt )

    if USING_MOLLY :
      new_goalAttList = sortGoalAttList( new_goalAttList )

    rule.ruleData[ "goalAttList" ] = new_goalAttList
    rule.goalAttList               = new_goalAttList
    rule.saveToGoalAtt()

    logging.debug( " rule.relationName                   = " + rule.relationName )
    logging.debug( " rule.orig_rule_ptr.orig_goalAttList = " + str( rule.orig_rule_ptr.orig_goalAttList ) )
    logging.debug( " rule.goalAttList                    = " + str( rule.goalAttList ) )
    logging.debug( " orig_rightmost                      = " + str( orig_rightmost ) )
    logging.debug( " new_rightmost                       = " + str( new_rightmost ) )

    # replace the time reference in the subgoals
    new_subgoalListOfDicts = []
    for subgoal in subgoalListOfDicts :
      new_subgoalDict = {}
      new_subgoalDict[ "subgoalName" ]    = subgoal[ "subgoalName" ]
      new_subgoalDict[ "polarity" ]       = subgoal[ "polarity" ]
      new_subgoalDict[ "subgoalTimeArg" ] = subgoal[ "subgoalTimeArg" ]
      new_subgoalDict[ "subgoalAttList" ] = []
  
      # replace all instances of new_rightmost with orig_rightmost
      orig_subgoalAttList = subgoal[ "subgoalAttList" ]
      for satt in orig_subgoalAttList :
        if satt == new_rightmost :
          if orig_rightmost == "NRESERVED+1" :
            new_subgoalDict[ "subgoalAttList" ].append( "NRESERVED" )
          elif orig_rightmost == "NRESERVED" :
            new_subgoalDict[ "subgoalAttList" ].append( "NRESERVED" )
          elif orig_rightmost == "MRESERVED" :
            new_subgoalDict[ "subgoalAttList" ].append( "MRESERVED" )
        else :
          new_subgoalDict[ "subgoalAttList" ].append( satt )

      new_subgoalListOfDicts.append( copy.deepcopy( new_subgoalDict ) )

    rule.subgoalListOfDicts               = copy.deepcopy( new_subgoalListOfDicts )
    rule.ruleData[ "subgoalListOfDicts" ] = copy.deepcopy( new_subgoalListOfDicts )
    rule.saveSubgoals()

    logging.debug( "  REPLACE TIME ATT : new rule data = " + str( rule.ruleData ) )

  else :

    logging.debug( "  REPLACE TIME ATTS : executing else..." )

    if len( rule.orig_rule_ptr.orig_rule_attMapper_aggRewrites ) > 0 :

      inv_attMapper_aggRewrites = {v: k for k, v in rule.orig_rule_ptr.orig_rule_attMapper_aggRewrites.iteritems()}

      # replace the time reference in the goal
      new_goalAttList = []
      for gatt in rule.goalAttList :
        if gatt in inv_attMapper_aggRewrites and \
         ( inv_attMapper_aggRewrites[ gatt ] == "NRESERVED" or \
           inv_attMapper_aggRewrites[ gatt ] == "NRESERVED+1" or \
           inv_attMapper_aggRewrites[ gatt ] == "MRESERVED"  ) :
          new_goalAttList.append( "NRESERVED" )
        elif gatt+"+1" in inv_attMapper_aggRewrites and \
         ( inv_attMapper_aggRewrites[ gatt+"+1" ] == "NRESERVED" or \
           inv_attMapper_aggRewrites[ gatt+"+1" ] == "NRESERVED+1" or \
           inv_attMapper_aggRewrites[ gatt+"+1" ] == "MRESERVED"  ) :
          new_goalAttList.append( "NRESERVED+1" )
        else :
          new_goalAttList.append( gatt )
 
      if USING_MOLLY : 
        new_goalAttList = sortGoalAttList( new_goalAttList )
  
      rule.ruleData[ "goalAttList" ] = new_goalAttList
      rule.goalAttList               = new_goalAttList
      rule.saveToGoalAtt()
  
      # replace the time reference in the subgoals
      new_subgoalListOfDicts = []
      for subgoal in subgoalListOfDicts :
        new_subgoalDict = {}
        new_subgoalDict[ "subgoalName" ]    = subgoal[ "subgoalName" ]
        new_subgoalDict[ "polarity" ]       = subgoal[ "polarity" ]
        new_subgoalDict[ "subgoalTimeArg" ] = subgoal[ "subgoalTimeArg" ]
        new_subgoalDict[ "subgoalAttList" ] = []
   
        # replace all instances of new_rightmost with orig_rightmost
        orig_subgoalAttList = subgoal[ "subgoalAttList" ]
        for satt in orig_subgoalAttList :
          if satt in inv_attMapper_aggRewrites and \
           ( inv_attMapper_aggRewrites[ satt ] == "NRESERVED" or \
             inv_attMapper_aggRewrites[ satt ] == "NRESERVED+1" or \
             inv_attMapper_aggRewrites[ satt ] == "MRESERVED"  ) :
            new_subgoalDict[ "subgoalAttList" ].append( "NRESERVED" )
          elif satt+"+1" in inv_attMapper_aggRewrites and \
           ( inv_attMapper_aggRewrites[ satt+"+1" ] == "NRESERVED" or \
             inv_attMapper_aggRewrites[ satt+"+1" ] == "NRESERVED+1" or \
             inv_attMapper_aggRewrites[ satt+"+1" ] == "MRESERVED"  ) :
            new_goalAttList.append( "NRESERVED+1" )
          else :
            new_subgoalDict[ "subgoalAttList" ].append( satt )
  
        new_subgoalListOfDicts.append( copy.deepcopy( new_subgoalDict ) )
  
      rule.subgoalListOfDicts               = copy.deepcopy( new_subgoalListOfDicts )
      rule.ruleData[ "subgoalListOfDicts" ] = copy.deepcopy( new_subgoalListOfDicts )
      rule.saveSubgoals()

  logging.debug( "  REPLACE TIME ATTS : ...done." )
  return rule


########################
#  SORT GOAL ATT LIST  #
########################
# input a list of goal attributes for a provenance rule
# re-order atts to place the NRESERVED, NRESERVED+1, and MRESERVED atts as the
# rightmost fields.
# output the sorted list.
def sortGoalAttList( provGoalAttList ) :

  logging.debug( "  SORT GOAL ATT LIST : running process...")
  logging.debug( "  SORT GOAL ATT LIST : provGoalAttList = " + str( provGoalAttList ) )

  tmp = []

  flag_nreserved     = False
  flag_nreserved_agg = False
  flag_mreserved     = False
  flag_mreserved_agg = False
  for gatt in provGoalAttList :
    if gatt == "NRESERVED+1" :
      flag_nreserved_agg = True
    elif gatt == "NRESERVED" :
      flag_nreserved = True
    elif gatt == "MRESERVED" :
      flag_mreserved = True
    elif gatt == "MRESERVED+1" :
      flag_mreserved_agg = True
    else :
      tmp.append( gatt )

  logging.debug( "flag_nreserved     = " + str( flag_nreserved ) )
  logging.debug( "flag_nreserved_agg = " + str( flag_nreserved_agg ) )
  logging.debug( "flag_mreserved     = " + str( flag_mreserved ) )
  logging.debug( "flag_mreserved_agg = " + str( flag_mreserved_agg ) )

  if flag_nreserved :
    tmp.append( "NRESERVED" )
  if flag_nreserved_agg :
    tmp.append( "NRESERVED+1" )
  if flag_mreserved :
    tmp.append( "MRESERVED" )
  if flag_mreserved_agg :
    tmp.append( "MRESERVED+1" )

  logging.debug( "  SORT GOAL ATT LIST : returning " + str( tmp ) ) 

  return tmp


########################
#  REWRITE PROVENANCE  #
########################
def rewriteProvenance( ruleMeta, cursor, argDict ) :

  logging.debug( " REWRITE PROVENANCE : running process..." ) 
  logging.debug( " REWRITE PROVENANCE : len( ruleMeta ) = " + str( len( ruleMeta ) ) ) 

  # -------------------------------------------------- #
  # iterate over rules

  prov_ruleMeta    = []
  provid           = 0
  previousGoalName = ""
  for rule in ruleMeta :

    logging.debug( "  REWRITE PROVENANCE : ruleData = " + str( rule.ruleData ) )

    goalName = rule.ruleData[ "relationName" ]

    # -------------------------------------------------- #
    # do not bother making prov rules for dom_, domcomp_,
    # adom_string, or adom_int

    if goalName.startswith( "domcomp_" ) or \
       goalName.startswith( "dom_" )     or \
       goalName.startswith( "adom_" )    or \
       goalName.startswith( "unidom_" )  or \
       goalName.startswith( "exidom_" )  or \
       goalName.startswith( "orig_" ) :
       continue

    # -------------------------------------------------- #
    # make all provenance name append numbers start from
    # 0 for each new rule name

    #goalName = rule.ruleData[ "relationName" ]

    # don't need to be this smart when comparing output w/ molly
    #if goalName == previousGoalName :
    #  pass
    #else :
    #  provid = 0

    # -------------------------------------------------- #
    # CASE : rule contains aggregate calls in the head

    if containsAggInHead( rule ) :
      provRules = aggProv( rule, provid, cursor, argDict )
      prov_ruleMeta.extend( provRules )

    # -------------------------------------------------- #
    # CASE : rule contains no aggregate calls 
    #        in the head

    else :
      provRule = regProv( rule, "_prov" + str( provid ), cursor, argDict )
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
