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
import dm_tools
import sip

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


########
#  DM  #
#########
# generate the new set of rules provided by the DM method for negative rewrites.
# factMeta := a list of Fact objects
# ruleMeta := a list of Rule objects
def dm( factMeta, ruleMeta, cursor, argDict ) :

  # ----------------------------------------- #

  logging.debug( "  DM : running process..." )

  settings_path = argDict[ "settings" ]

  # ----------------------------------------- #
  # get parameters

  # ========== OPTIMIZE NOT ========== #
  try :
    OPTIMIZE_NOT = tools.getConfig( settings_path, "DEFAULT", "OPTIMIZE_NOT", bool )
  except ConfigParser.NoOptionError :
    OPTIMIZE_NOT = False
    logging.warning( "WARNING : no 'OPTIMIZE_NOT' defined in 'DEFAULT' section of " + settings_path + \
                     " ...running with OPTIMIZE_NOT=False." )

  # ========== NW DOM DEF ========== #
  try :
    NW_DOM_DEF = tools.getConfig( settings_path, "DEFAULT", "NW_DOM_DEF", str )
    if NW_DOM_DEF == "dm_huge" or \
       NW_DOM_DEF == "sip_edb" or \
       NW_DOM_DEF == "sip_idb" :
      pass
    else :
      raise ValueError( "unrecognized NW_DOM_DEF option '" + NW_DOM_DEF + \
                        "'. aborting..." )
  except ConfigParser.NoOptionError :
    raise ValueError( "no 'NW_DOM_DEF' defined in 'DEFAULT' section of " + settings_path + \
                      ". aborting..." )

  # ----------------------------------------- #
  # replace unused variables with wildcards

  if NW_DOM_DEF == "sip_idb" :
    ruleMeta = dm_tools.replace_unused_vars( ruleMeta, cursor )

  # ----------------------------------------- #
  # rewrite rules with fixed data 
  # in the head

  ruleMeta, factMeta = fixed_data_head_rewrites( ruleMeta, factMeta, argDict )

  # ----------------------------------------- #
  # rewrite rules with aggregate functions
  # in the head

  ruleMeta = aggRewrites( ruleMeta, argDict )

  for rule in ruleMeta :
    logging.debug( "  DM : " + dumpers.reconstructRule( rule.rid, cursor ) )
  #sys.exit( "blah" )

  # ----------------------------------------- #
  # enforce a uniform goal attribute lists
    
  ruleMeta = setUniformAttList( ruleMeta, cursor )

  logging.debug( "  DM : len( ruleMeta ) after setUniformAttList = " + str( len( ruleMeta ) ) )

  for rule in ruleMeta :
    logging.debug( "  DM : " + dumpers.reconstructRule( rule.rid, cursor ) )
  #sys.exit( "blah" )

  # ----------------------------------------- #
  # enforce unique existential attributes
  # per rule
    
  ruleMeta = setUniqueExistentialVars( ruleMeta )

  logging.debug( "  DM : len( ruleMeta ) after setUniqueExistentialVars = " + \
                 str( len( ruleMeta ) ) )
  for rule in ruleMeta :
    logging.debug( "  DM : " + dumpers.reconstructRule( rule.rid, cursor ) )

  # ----------------------------------------- #
  # replace time att references

  ruleMeta = dm_time_att_replacement.dm_time_att_replacement( ruleMeta, cursor, argDict )

  logging.debug( "  DM : len( ruleMeta ) after dm_time_att_replacement= " + \
                 str( len( ruleMeta ) ) )
  for rule in ruleMeta :
    logging.debug( "  DM : " + dumpers.reconstructRule( rule.rid, cursor ) )

  # ----------------------------------------- #
  # append rids to all rel names and
  # generate cps of the original rules
  # (do not reference these in final programs)

  if NW_DOM_DEF == "sip_idb" : 
    #ruleMeta = dm_tools.change_rel_names( ruleMeta )

    # future optimization : do this lazily:
    ruleMeta.extend( dm_tools.generate_orig_cps( ruleMeta ) )

  # ----------------------------------------- #
  # generate a map of all rids to corresponding
  # rule meta object pointers.

  if NW_DOM_DEF == "sip_idb" : 
    rid_to_rule_meta_map = dm_tools.generate_rid_to_rule_meta_map( ruleMeta )

  # ----------------------------------------- #
  # build all de morgan's rules

  COUNTER = 0
  while stillContainsNegatedIDBs( ruleMeta, cursor ) :

    logging.debug( "  DM : COUNTER = " + str( COUNTER ) )

    # ----------------------------------------- #
    # create the adom definition and add
    # to rule meta list
    # only do this once.
     
    if COUNTER < 1 and NW_DOM_DEF == "dm_huge" :
      ruleMeta.extend( buildAdom( factMeta, cursor ) )
    
    # ----------------------------------------- #
    # check if any rules include negated idb
    # subgoals
  
    targetRuleMetaSets = getRuleMetaSetsForRulesCorrespondingToNegatedSubgoals( ruleMeta, cursor )
    
    # ----------------------------------------- #
    # break execution if no rules contain negated IDBs.
    # should not hit this b/c of loop condition.

    if len( targetRuleMetaSets ) < 1 :
      return []
    
    # ----------------------------------------- #
    # create the de morgan rewrite rules.
    # incorporates domcomp and existential 
    # domain subgoals.
    
    if NW_DOM_DEF == "dm_huge" : 
      ruleMeta = doDeMorgans_dm_huge( ruleMeta, \
                                      targetRuleMetaSets, \
                                      cursor, \
                                      argDict )
    elif NW_DOM_DEF == "sip_edb" : 
      ruleMeta = sip.doDeMorgans_sip_edb( factMeta, \
                                          ruleMeta, \
                                          targetRuleMetaSets, \
                                          cursor, \
                                          argDict )
    elif NW_DOM_DEF == "sip_idb" : 
      ruleMeta = sip.doDeMorgans_sip_idb( factMeta, \
                                          ruleMeta, \
                                          targetRuleMetaSets, \
                                          rid_to_rule_meta_map, \
                                          cursor, \
                                          argDict )
    else :
      raise ValueError( "unrecognized NW_DOM_DEF option '" + NW_DOM_DEF + \
                        "'. aborting..." )

    # ----------------------------------------- #
    # update rid to rule meta map

    rid_to_rule_meta_map = dm_tools.generate_rid_to_rule_meta_map( ruleMeta )

    # increment loop counter
    COUNTER += 1

    #for rule in ruleMeta :
    #  print str( rule.rid ) + " : " + dumpers.reconstructRule( rule.rid, rule.cursor )

  # ----------------------------------------- #
  # replace unused variables with wildcards

  if NW_DOM_DEF == "sip_idb" :
    ruleMeta = dm_tools.replace_unused_vars( ruleMeta, cursor )

  # ----------------------------------------- #  
  #  apply filters

  if OPTIMIZE_NOT :
    for rule in ruleMeta :
      if rule.ruleData[ "relationName" ].startswith( "not_" ) :
        # observe all negated subgoals, at this point, will be edb.
        remove_any_unnecessary_constraint_subgoals( rule )

#  for rule in ruleMeta :
#    print dumpers.reconstructRule( rule.rid, rule.cursor )
#  sys.exit( "blahahaha" )

  logging.debug( "  DM : ...done." )
  return factMeta, ruleMeta


################################################
#  REMOVE ANY UNNECESSARY CONSTRAINT SUBGOALS  #
################################################
def remove_any_unnecessary_constraint_subgoals( rule ) :

  logging.debug( "----------------------------------------------------" )
  logging.debug( "  REMOVE ANY UNNECESSARY CONSTRAINT SUBGOALS : (before) rule = " + dumpers.reconstructRule( rule.rid, rule.cursor ) )

  # ----------------------------------------------------------- #
  # apply filter

  subgoalListOfDicts_tmp = []
  for sub in rule.ruleData[ "subgoalListOfDicts" ] :
    #if sub[ "subgoalName" ].startswith( "domcomp_") and not is_necessary( sub, rule ) :
    #  pass # excluding these makes the results incorrect
    if sub[ "subgoalName" ].startswith( "dom_")     and not is_necessary( sub, rule ) or \
       sub[ "subgoalName" ].startswith( "domcomp_") and not is_necessary( sub, rule ) or \
       sub[ "subgoalName" ].startswith( "unidom_")  and not is_necessary( sub, rule ) or \
       sub[ "subgoalName" ].startswith( "exidom_")  and not is_necessary( sub, rule ) or \
       sub[ "subgoalName" ].startswith( "orig_")  and not is_necessary( sub, rule ) :
      pass
    else :
      # keep it.
      subgoalListOfDicts_tmp.append( sub )

  # ----------------------------------------------------------- #
  # check if filter applied

  logging.debug( "  REMOVE ANY UNNECESSARY CONSTRAINT SUBGOALS : subgoalListOfDicts_tmp = " )
  for sub in subgoalListOfDicts_tmp :
    logging.debug( "  " + str( sub ) )

  if len( rule.ruleData[ "subgoalListOfDicts" ] ) > len( subgoalListOfDicts_tmp ) :
    # save new subgoal list
    rule.ruleData[ "subgoalListOfDicts" ] = subgoalListOfDicts_tmp
    rule.subgoalListOfDicts               = subgoalListOfDicts_tmp
    rule.saveSubgoals()
    logging.debug( "  REMOVE ANY UNNECESSARY CONSTRAINT SUBGOALS : (after) rule = " + dumpers.reconstructRule( rule.rid, rule.cursor ) )

  else :
    pass # do not mess with the input rule

  logging.debug( "  REMOVE ANY UNNECESSARY CONSTRAINT SUBGOALS : (after) rule = " + dumpers.reconstructRule( rule.rid, rule.cursor ) )


##################
#  IS NECESSARY  #
##################
def is_necessary( constraint_subgoal_dict, rule_obj ) :

  # ----------------------------------------------------------- #
  # collect list of all atts in all positive, 
  # non-constraint subgoals

  #pos_subgoal_att_list = get_pos_subgoal_att_list( rule_obj )
  subgoal_att_list = get_subgoal_att_list( rule_obj )

  logging.debug( "  IS NECESSARY : constraint_subgoal_dict[ 'subgoalAttList' ] = " )
  logging.debug( "     " + str( constraint_subgoal_dict[ "subgoalAttList" ] ) )
  #logging.debug( "  IS NECESSARY : pos_subgoal_att_list    = " + str( pos_subgoal_att_list ) )
  logging.debug( "  IS NECESSARY : pos_subgoal_att_list    = " + str( subgoal_att_list ) )

  for satt in constraint_subgoal_dict[ "subgoalAttList" ] :
    #if not satt in pos_subgoal_att_list :
    if not satt in subgoal_att_list :
      # then the existential var is not needed
      logging.debug( "  IS NECESSARY : returning False" )
      return False

  # otherwise, the existential var is essential for safety
  logging.debug( "  IS NECESSARY : returning True" )
  return True

#  # ----------------------------------------------------------- #
#  # check if constraint subgoal contains atts not already
#  # contained by a positive, non-constraint subgoal
#
#  for satt in constraint_subgoal_dict[ "subgoalAttList" ] :
#    if not satt in pos_subgoal_att_list :
#      logging.debug( "  IS NECESSARY : returning True" )
#      return True
#
#  logging.debug( "  IS NECESSARY : returning False" )
#  return False


##############################
#  GET SUBGOAL ATT LIST  #
##############################
def get_subgoal_att_list( rule_obj ) :
  subgoal_att_list = []
  for sub in rule_obj.ruleData[ "subgoalListOfDicts" ] :
    if not sub[ "subgoalName" ].startswith( "dom_" )     and \
       not sub[ "subgoalName" ].startswith( "domcomp_" ) and \
       not sub[ "subgoalName" ].startswith( "unidom_" )  and \
       not sub[ "subgoalName" ].startswith( "exidom_" )  and \
       not sub[ "subgoalName" ].startswith( "orig_" ) :
      for satt in sub[ "subgoalAttList" ] :
        if not satt in subgoal_att_list :
          subgoal_att_list.append( satt )
  return subgoal_att_list


##############################
#  GET POS SUBGOAL ATT LIST  #
##############################
def get_pos_subgoal_att_list( rule_obj ) :
  pos_subgoal_att_list = []
  for sub in rule_obj.ruleData[ "subgoalListOfDicts" ] :
    if not sub[ "subgoalName" ].startswith( "dom_" )     and \
       not sub[ "subgoalName" ].startswith( "domcomp_" ) and \
       not sub[ "subgoalName" ].startswith( "unidom_" )  and \
       not sub[ "subgoalName" ].startswith( "exidom_" )  and \
       not sub[ "subgoalName" ].startswith( "orig_" )    and \
       not sub[ "polarity" ]    == "notin" :
      for satt in sub[ "subgoalAttList" ] :
        if not satt in pos_subgoal_att_list :
          pos_subgoal_att_list.append( satt )
  return pos_subgoal_att_list


############
#  IS IDB  #
############
def is_idb( name, cursor ) :
  cursor.execute( "SELECT goalName FROM Rule" )
  idb_list = cursor.fetchall()
  idb_list = tools.toAscii_list( idb_list )
  if name in idb_list :
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


#################
#  EXTRACT RHS  #
#################
# get the rhs of the aggregated attribute
def extractRHS( att ) :

  for op in arithOps :
    if op in att :
      return op + att.split( op )[1]

  return ""



#######################
#  CONTAINS AGG RULE  #
#######################
# check if the rule contains an aggregate in the head
def containsAgg_rule( rule ) :

  for gatt in rule.goalAttList :
    if containsAgg( gatt ) :
      return True

  return False


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


#################
#  OVERLAPPING  #
#################
# check if the input lists contain any identical elements
def overlapping( existVars1, existVars2 ) :

  for var1 in existVars1 :
    if var1 in existVars2 :
      return True

  return False


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


#####################
#  IDENTICAL RULES  #
#####################
# check if the input rules are identical
def identicalRules( rule1, rule2 ) :

  if rule1.rid == rule2.rid :
    return True

  else :
    return False


##########################
#  DO DEMORGANS DM HUGE  #
##########################
# create a new set of rules representing the application of 
# DeMorgan's Law on the first-order logic representation
# of the targetted rules
def doDeMorgans_dm_huge( ruleMeta, targetRuleMetaSets, cursor, argDict ) :

  logging.debug( "  DO DEMORGANS DM HUGE : running process..." )

  newDMRules = []

  for rule_info in targetRuleMetaSets :

    parent_list = rule_info[ 0 ]
    ruleSet     = rule_info[ 1 ]

    for rule in ruleSet :
      logging.debug( "//////////////////////////////////////////////////" )
      logging.debug( "  DO DEMORGANS DM HUGE : rule.ruleData     = " + str( rule.ruleData ) )
      logging.debug( "  DO DEMORGANS DM HUGE : rule.relationName = " + str( rule.relationName ) )
      logging.debug( "  DO DEMORGANS DM HUGE : rule.rid          = " + str( rule.rid ) )
      logging.debug( "//////////////////////////////////////////////////" )

    # ----------------------------------------- #
    # get an original rule id to reference types

    orig_rid = ruleSet[0].rid

    logging.debug( "  DO DEMORGANS DM HUGE : orig_rid = " + str( orig_rid ) )

    # ----------------------------------------- #
    # get new rule name

    orig_name = ruleSet[0].relationName
    not_name  = "not_" + orig_name

    # ----------------------------------------- #
    # get new rule goal attribute list
    # works only if goal att lists are uniform 
    # across all rules per set

    goalAttList = ruleSet[0].ruleData[ "goalAttList" ]

    # ----------------------------------------- #
    # get new rule goal time arg

    goalTimeArg = ""

    # ----------------------------------------- #
    # build domcomp rule and save to 
    # rule meta list

    domcompRule = buildDomCompRule( orig_name, \
                                    goalAttList, \
                                    orig_rid, \
                                    cursor, \
                                    argDict )
    ruleMeta.append( domcompRule )

    # ----------------------------------------- #
    # build existential attribute domain rules

    existentialVarsRules = buildExistentialVarsRules( ruleSet, cursor )
    ruleMeta.extend( existentialVarsRules )

    # ----------------------------------------- #
    # build the boolean dnf fmla

    final_fmla = dm_tools.get_final_fmla( ruleSet )

    # ----------------------------------------- #
    # each clause in the final dnf fmla 
    # informs the subgoal list of a new 
    # datalog rule

    newDMRules = dnfToDatalog( not_name, \
                               goalAttList, \
                               goalTimeArg, \
                               final_fmla, \
                               domcompRule, \
                               existentialVarsRules, \
                               ruleSet, \
                               cursor, \
                               argDict )

    # ----------------------------------------- #
    # add new dm rules to the rule meta

    ruleMeta.extend( newDMRules )

    # ----------------------------------------- #
    # replace instances of the negated subgoal
    # with instances of the positive not_
    # subgoal

    ruleMeta = dm_tools.replaceSubgoalNegations( ruleMeta, argDict )

    # ----------------------------------------- #
    # resolve double negations

    ruleMeta = dm_tools.resolveDoubleNegations( ruleMeta )

    # ----------------------------------------- #
    # order recursive rules last

    ruleMeta = dm_tools.sortDMRules( ruleMeta )

  return ruleMeta


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


##################################
#  BUILD EXISTENTIAL VARS RULES  #
##################################
# build the set of existential rules for this rule set
# observe exisistential vars must be unique per original rule
# for this to work.
def buildExistentialVarsRules( ruleSet, cursor ) :

  logging.debug( "--------------------------------------------------------------------------------" )
  logging.debug( "  BUILD EXISTENTIAL VARS RULES : ruleSet = \n" )
  for rule in ruleSet :
    logging.debug( str( rule.ruleData ) + "\n" )

  # ----------------------------------------- #
  # get the original rule name

  orig_name = ruleSet[0].ruleData[ "relationName" ]

  # ----------------------------------------- #
  # iterate over rule set

  existentialDomRules = []

  for rule in ruleSet :

    # ----------------------------------------- #
    # check if rule contains existential vars

    if containsExistentialVars( rule ) :

      logging.debug( "  BUILD EXISTENTIAL VARS RULES : rule contains existential vars : " + str( rule.ruleData ) )

      # ----------------------------------------- #
      # get the list of existential vars

      existentialAttList = getExistentialVarList( rule )

      logging.debug( "  BUILD EXISTENTIAL VARS RULES : existentialAttList = " + str( existentialAttList ) )

      # ----------------------------------------- #
      # iterate over rule subgoals to build a base 
      # list of dictionaries.
      # preserve existential vars, but replace
      # universal vars with wildcards

      base_subgoalListOfDicts = []

      for subgoal in rule.subgoalListOfDicts :
        thisSubgoalDict = {}
        thisSubgoalDict[ "subgoalName" ]    = subgoal[ "subgoalName" ]
        thisSubgoalDict[ "polarity" ]       = ""
        thisSubgoalDict[ "subgoalTimeArg" ] = ""

        subgoalAttList = []
        for satt in subgoal[ "subgoalAttList" ] :
          if satt in existentialAttList :
            subgoalAttList.append( satt )
          else :
            subgoalAttList.append( "_" )

        if not onlyWildcards( subgoalAttList ) :
          thisSubgoalDict[ "subgoalAttList" ] = subgoalAttList
          base_subgoalListOfDicts.append( thisSubgoalDict )
        #thisSubgoalDict[ "subgoalAttList" ] = subgoalAttList
        #base_subgoalListOfDicts.append( thisSubgoalDict )

      # ----------------------------------------- #
      # build a table of 0s and 1s marking the binary
      # polarities of the subgoals

      patternMap = getPatternMap( len( base_subgoalListOfDicts ) )

      # ----------------------------------------- #
      # build a set of new rules manifesting the
      # combinatorial set of polarity options
      # across subgoals.
      # only save safe rules.

      ruleData = {}
      ruleData[ "goalAttList" ]        = existentialAttList
      ruleData[ "goalTimeArg" ]        = ""
      ruleData[ "eqnDict" ]            = {}

      ruleData[ "relationName" ] = "dom_" + orig_name + "_"
      for att in existentialAttList :
        ruleData[ "relationName" ] += att.lower()

      #if ruleData[ "relationName" ] == "dom_primary_failure_timethresh" :
      #  for sub in base_subgoalListOfDicts :
      #    print sub
      #  sys.exit( "blah" )

      for row in patternMap :

        subgoalListOfDicts = []

        for i in range( 0, len( row ) ) :

          bit = row[ i ]

          newSubgoal = base_subgoalListOfDicts[ i ]
          if bit == "0" :
            newSubgoal[ "polarity" ] = ""
          else :
            newSubgoal[ "polarity" ] = "notin"

          subgoalListOfDicts.append( newSubgoal )

        # ----------------------------------------- #
        # save rule, if safe

        ruleData[ "subgoalListOfDicts" ] = copy.deepcopy( subgoalListOfDicts )

        if isSafe( ruleData ) :
          rid = tools.getIDFromCounters( "rid" )
          #existentialDomRules.append( copy.deepcopy( Rule.Rule( rid, ruleData, None ) ) )
          newRule        = copy.deepcopy( Rule.Rule( rid, ruleData, cursor) )
          newRule.cursor = cursor # need to do this for some reason or else cursor disappears?
          existentialDomRules.append( newRule )

  for rule in existentialDomRules :
    logging.debug( "  BUILD EXISTENTIAL VARS RULES : >>> returning existential rule with ruleData = " + str( rule.ruleData ) )

  return existentialDomRules


####################
#  ONLY WILDCARDS  #
####################
def onlyWildcards( subgoalAttList ) :
  if subgoalAttList.count( "_" ) < len( subgoalAttList ) :
    return False
  else :
    return True


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


##############################
#  GET EXISTENTIAL VAR LIST  #
##############################
# retrive the list of existential vars in the given rule
def getExistentialVarList( rule ) :

  # ----------------------------------------- #
  # get goal att list

  universalAttList = rule.goalAttList

  # ----------------------------------------- #
  # get list of all subgoal atts

  existentialAttList = []
  for subgoal in rule.subgoalListOfDicts :
    subgoalAttList = subgoal[ "subgoalAttList" ]
    for satt in subgoalAttList :
      if not satt in universalAttList and \
         not satt in existentialAttList and \
         not satt == "_" and \
         not is_fixed_string( satt ) and \
         not is_fixed_int( satt ) :
        existentialAttList.append( satt )

  return existentialAttList


###############################
#  CONTAINS EXISTENTIAL VARS  #
###############################
# check if the input rule contains existential vars
def containsExistentialVars( rule ) :

  # ----------------------------------------- #
  # get goal att list

  universalAttList = rule.goalAttList

  # ----------------------------------------- #
  # get list of all subgoal atts

  existentialAttList = []
  for subgoal in rule.subgoalListOfDicts :
    subgoalAttList = subgoal[ "subgoalAttList" ]
    for satt in subgoalAttList :
      if not satt == "_" :
        if not satt in universalAttList and \
           not satt in existentialAttList and \
           not is_fixed_string( satt ) and \
           not is_fixed_int( satt ) :
          existentialAttList.append( satt )

  if len( existentialAttList ) > 0 :
    return True
  else :
    return False


#########################
#  BUILD DOM COMP RULE  #
#########################
# build the dom comp rule
def buildDomCompRule( orig_name, goalAttList, orig_rid, cursor, argDict ) :

  logging.debug( "===================================================" )
  logging.debug( "  BUILD DOM COMP RULE : running process..." )
  logging.debug( "  BUILD DOM COMP RULE : orig_name   = " + orig_name )
  logging.debug( "  BUILD DOM COMP RULE : goalAttList = " + str( goalAttList ) )
  logging.debug( "  BUILD DOM COMP RULE : orig_rid    = " + str( orig_rid ) )

  ruleData = {}

  # ----------------------------------------- #
  # get ordered list of types for this 
  # relation schema
  #
  # NOTE!!! predicates upon the call to setTypes
  # performed prior to any rewrite procedure 
  # in the rewrite() method of dedt.py

  # grab att id as well, to keep duplicates
  cursor.execute( "SELECT attID,attType FROM GoalAtt WHERE rid=='" + str( orig_rid ) + "'" )
  goalTypeList_tmp = cursor.fetchall()
  goalTypeList_tmp = tools.toAscii_multiList( goalTypeList_tmp )
  goalTypeList     = [ x[1] for x in goalTypeList_tmp ]

  # ----------------------------------------- #
  # extract all goal atts from agg'd 
  # expressions

  tmp = []
  for gatt in goalAttList :
    if containsAgg( gatt ) :
      tmp.append( extractAtt( gatt ) )
    else :
      tmp.append( gatt )
  goalAttList = copy.copy( tmp )

  logging.debug( "  BULD DOM COMP RULE : new goalAttList = " + str( goalAttList ) )

  # ----------------------------------------- #
  # sanity check break

  if not len( goalAttList ) == len( goalTypeList ) :
    tools.bp( __name__, inspect.stack()[0][3], "FATAL ERROR : buildDomCompRule : " + \
              "the length of the goal att list '" + str( goalAttList ) + \
              "' does not match the length of the goal type list '" + \
              str( goalTypeList ) + \
              "' for rule:\n" + dumpers.reconstructRule( orig_rid, cursor ) )

  else :

    subgoalListOfDicts = []

    try :
      DM_CONCISE = tools.getConfig( argDict[ "settings" ], "DEFAULT", "DM_CONCISE", bool )

    except ConfigParser.NoOptionError :
      logging.debug( "  WARNING : DM_CONCISE not defined in settings file '" + \
                     argDict[ "settings" ] + "'. running with DM_CONCISE = False." )
      DM_CONCISE = False

    # ----------------------------------------- #
    # build adom subgoals

    #if not DM_CONCISE :
    if True :
      for i in range( 0, len( goalAttList ) ) :
  
        att = goalAttList[ i ]
  
        subgoalDict = {}
        subgoalDict[ "subgoalName" ]    = "adom_" + goalTypeList[ i ]
        subgoalDict[ "subgoalAttList" ] = [ att ]
        subgoalDict[ "polarity" ]       = ""
        subgoalDict[ "subgoalTimeArg" ] = ""
        subgoalListOfDicts.append( subgoalDict )

    # ----------------------------------------- #
    # build negated original subgoal

    negatedOrig_subgoal = {}
    negatedOrig_subgoal[ "subgoalName" ]    = orig_name
    negatedOrig_subgoal[ "subgoalAttList" ] = goalAttList
    negatedOrig_subgoal[ "polarity" ]       = "notin"
    negatedOrig_subgoal[ "subgoalTimeArg" ] = ""
    subgoalListOfDicts.append( negatedOrig_subgoal )

    # ----------------------------------------- #
    # add modified subgoals of the original
    # relation for concision

    if DM_CONCISE :
      for i in range( 0, len( goalAttList ) ) :
  
        att = goalAttList[ i ]
 
        if not att == "NRESERVED" and not att == "MRESERVED" :
          subgoalDict = {}
          subgoalDict[ "subgoalName" ]    = orig_name
          subgoalDict[ "polarity" ]       = ""
          subgoalDict[ "subgoalTimeArg" ] = ""
    
          subgoalDict[ "subgoalAttList" ] = []
          for j in range( 0, len( goalAttList ) ) :
            if j == i :
              subgoalDict[ "subgoalAttList" ].append( att )
            else :
              subgoalDict[ "subgoalAttList" ].append( "_" )
    
          subgoalListOfDicts.append( subgoalDict )

    # ----------------------------------------- #
    # save rule data and create the 
    # dom comp rule

    ruleData[ "relationName" ]       = "domcomp_" + orig_name
    ruleData[ "goalAttList" ]        = goalAttList
    ruleData[ "goalTimeArg" ]        = ""
    ruleData[ "subgoalListOfDicts" ] = subgoalListOfDicts
    ruleData[ "eqnDict" ]            = {}

    rid = tools.getIDFromCounters( "rid" )

    #domcompRule = Rule.Rule( rid, ruleData, cursor )
    domcompRule        = copy.deepcopy( Rule.Rule( rid, ruleData, cursor ) )
    domcompRule.cursor = cursor # need to do this for some reason or else cursor disappears?

    return domcompRule


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


#################
#  EXTRACT ATT  #
#################
# extract the attribute from a given agg expression,
# if applicable.
def extractAtt( gatt ) :

  # ----------------------------------------- #
  # check if gatt contains an agg op

  flag    = False
  firstOp = None
  for op in arithOps :
    if op in gatt :
      flag    = True
      firstOp = op
      break

  if not flag :
    return gatt

  # ----------------------------------------- #
  # extract agg op
  # assume the real goal att
  # is on the lhs of the expression

  else :

    return gatt.split( firstOp )[0]


####################
#  DNF TO DATALOG  #
####################
# use the positive fmla to generate a new set of
# formulas for the not_ rules
def dnfToDatalog( not_name, \
                  goalAttList, \
                  goalTimeArg, \
                  final_fmla, \
                  domcompRule, \
                  existentialVarsRules, \
                  ruleSet, \
                  cursor, \
                  argDict ) :

  settings_path    = argDict[ "settings" ]

  logging.debug( "  DNF TO DATALOG : not_name    = " + not_name )
  logging.debug( "  DNF TO DATALOG : goalAttList = " + str( goalAttList ) )
  logging.debug( "  DNF TO DATALOG : goalTimeArg = " + goalTimeArg )
  logging.debug( "  DNF TO DATALOG : final_fmla  = " + final_fmla )
  logging.debug( "  DNF TO DATALOG : ruleSet     = " + str( ruleSet ) )

  # ----------------------------------------- #
  # generate combined equation list
  # collect eqns from all rules and append to
  # all dm rules.

  eqnDict_combined = {}
  for rule in ruleSet :
    for eqn in rule.eqnDict :
      eqnDict_combined[ eqn ] = rule.eqnDict[ eqn ]

  # ----------------------------------------- #
  # break positive dnf fmla into a set of 
  # conjuncted clauses

  clauseList = final_fmla.replace( "(", "" )      # valid b/c dnf
  clauseList = clauseList.replace( ")", "" )      # valid b/c dnf
  clauseList = clauseList.split( "|" )

  logging.debug( "  DNF TO DATALOG : clauseList = " + str( clauseList ) )

  # ----------------------------------------- #
  # iterate over clause list to create
  # the list of new dm rules
  # create one new dm rule per clause

  newDMRules = []

  for clause in clauseList :

    subgoalListOfDicts = []

    # ----------------------------------------- #
    # get list of subgoal literals

    subgoalLiterals = clause.split( "&" )
    logging.debug( "  DNF TO DATALOG : subgoalLiterals = " + str( subgoalLiterals ) )

    # ----------------------------------------- #
    # iterate over the subgoal literals
    # observe the first integer represents the 
    # index of the parent target rule in the 
    # rule meta list of _targetted_ rule objects
    # the second integer represents the index
    # of the associated subgoal in the current
    # targetted rule

    for literal in subgoalLiterals :

      logging.debug( "  DNF TO DATALOG : literal = " + literal )

      # ----------------------------------------- #
      # get subgoal polarity

      if "~" in literal :
        polarity = "notin"
        literal = literal.replace( "~", "" )

      else :
        polarity = ""

      # ----------------------------------------- #
      # grab the rule and subgoal indexes

      literal      = literal.split( "_" )
      ruleIndex    = int( literal[ 0 ] )
      subgoalIndex = int( literal[ 1 ] )

      # ----------------------------------------- #
      # grab subgoal dict from appropriate rule

      rule        = ruleSet[ ruleIndex ]

      # make copy of subgoal dictionary b/c 
      # python referencing is shit sometimes

      subgoalDict = {}
      sub         = rule.subgoalListOfDicts[ subgoalIndex ]

      for key in sub :
        subgoalDict[ key ] = sub[ key ]

      logging.debug( "  DNF TO DATALOG : orig subgoalDict : " + str( subgoalDict ) )

      # ----------------------------------------- #
      # set polarity

      subgoalDict[ "polarity" ] = polarity

      # ----------------------------------------- #
      # save to subgoal list of dicts

      logging.debug( "  DNF TO DATALOG : adding subgoalDict to rule '" + \
                     not_name + "' : " + str( subgoalDict ) )

      subgoalListOfDicts.append( subgoalDict )

    # ----------------------------------------- #
    # add dom comp subgoal, if applicable

    domcompSubgoal_dict = {}
    domcompSubgoal_dict[ "subgoalName" ]    = domcompRule.ruleData[ "relationName" ]
    domcompSubgoal_dict[ "subgoalAttList" ] = domcompRule.ruleData[ "goalAttList" ]
    domcompSubgoal_dict[ "polarity" ]       = ""
    domcompSubgoal_dict[ "subgoalTimeArg" ] = ""
  
    logging.debug( "  DNF TO DATALOG : domcompSubgoal_dict subgoalName    = " + \
                   domcompSubgoal_dict[ "subgoalName" ] )
    logging.debug( "  DNF TO DATALOG : domcompSubgoal_dict subgoalAttList = " + \
                   str( domcompSubgoal_dict[ "subgoalAttList" ] ) )
    logging.debug( "  DNF TO DATALOG : domcompSubgoal_dict polarity       = " + \
                   domcompSubgoal_dict[ "polarity" ] )
    logging.debug( "  DNF TO DATALOG : domcompSubgoal_dict subgoalTimeArg = " + \
                   domcompSubgoal_dict[ "subgoalTimeArg" ] )
  
    subgoalListOfDicts.append( domcompSubgoal_dict )

    # ----------------------------------------- #
    # add existential domain subgoal,
    # if applicable

    prevRules = []
    for currRule in existentialVarsRules :

      if currRule.relationName in prevRules :
        pass

      else :
        prevRules.append( currRule.relationName )

        existentialVarSubgoal_dict = {}
        existentialVarSubgoal_dict[ "subgoalName" ]    = currRule.ruleData[ "relationName" ]
        existentialVarSubgoal_dict[ "subgoalAttList" ] = currRule.ruleData[ "goalAttList" ]
        existentialVarSubgoal_dict[ "polarity" ]       = ""
        existentialVarSubgoal_dict[ "subgoalTimeArg" ] = ""
   
        subgoalListOfDicts.append( existentialVarSubgoal_dict )

    # ----------------------------------------- #
    # build ruleData for new rule and save

    ruleData = {}
    ruleData[ "relationName" ]       = not_name
    ruleData[ "goalAttList" ]        = goalAttList
    ruleData[ "goalTimeArg" ]        = goalTimeArg
    ruleData[ "subgoalListOfDicts" ] = subgoalListOfDicts
    ruleData[ "eqnDict" ]            = eqnDict_combined

    # ----------------------------------------- #
    # save rule

    rid            = tools.getIDFromCounters( "rid" )
    newRule        = copy.deepcopy( Rule.Rule( rid, ruleData, cursor) )
    newRule.cursor = cursor # need to do this for some reason or else cursor disappears?
    newDMRules.append( newRule )

  for newRule in newDMRules :
    logging.debug( "  DNF TO DATALOG : returing newDMRule.ruleData = " + str( newRule.ruleData ) )

  return newDMRules


#####################
#  SIMPLIFY TO DNF  #
#####################
# simplify the input sympy fmla to dnf
def simplifyToDNF( negated_dnf_fmla ) :
  return sympy.to_dnf( str( negated_dnf_fmla ) )


##############################
#  GENERATE BOOLEAN FORMULA  #
##############################
# use the subgoals in the rule set to build a negated
# dnf formula
# return the formula
# literals := "[~]ruleIndex,subgoalindex"
# ^build literals as strings concatenating 
# the index of the rule in the rule set with the 
# index of the subgoals in that rule over a comma.
# negated subgoals require a "~" prepend.
def generateBooleanFormula( ruleSet ) :

  fmla = ""

  # ----------------------------------------- #
  # iterate over each rule
  # to build a clause for the initial dnf fmla

  for i in range( 0, len( ruleSet ) ) :

    thisClause = ""
    thisRule   = ruleSet[ i ]

    # ----------------------------------------- #
    # get subgoal information

    thisSubgoalListOfDicts = thisRule.subgoalListOfDicts

    # ----------------------------------------- #
    # iterate over subgoals to get polarity

    for j in range( 0, len( thisSubgoalListOfDicts ) ) :

      thisSubgoalDict = thisSubgoalListOfDicts[ j ]
      polarity        = thisSubgoalDict[ "polarity" ]

      thisLiteral = "INDX" + str( i ) + "_INDX" + str( j )

      # ----------------------------------------- #
      # build clause to insert into return fmla

      if polarity == "notin" :
        thisLiteral = "~" + thisLiteral

      logging.debug( "  GENERATE BOOLEAN FORMULA : thisLiteral = " + thisLiteral )

      # ----------------------------------------- #
      # save in this clause

      # add an AND when necessary
      if j > 0 :
        thisClause += " & "

      thisClause += thisLiteral

      logging.debug( "  GENERATE BOOLEAN FORMULA : thisClause = " + thisClause )

    # ----------------------------------------- #
    # save the clause to the fmla

    # add an OR when necessary
    if i > 0 :
      fmla += " | "

    fmla += "(" + thisClause + ")"

  # ----------------------------------------- #
  # return the negated version of the fmla

  returnFmla = "~" + "(" + fmla + ")"

  logging.debug( "  GENERATE BOOLEAN FORMULA : returning returnFmla = " + returnFmla )

  return returnFmla


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


################
#  BUILD ADOM  #
################
# generate the set of rules describing the entire active domain for the program,
# which is precisely the 
def buildAdom( factMeta, cursor ) :

  logging.debug( "  BUILD ADOM : factMeta = " + str( factMeta ) )

  newRules = []

  # ----------------------------------------- #
  # define the base relation name

  base_relationName = "adom"

  # ----------------------------------------- #
  # define goalAttList 

  goalAttList = [ "T" ]

  # ----------------------------------------- #
  # define goalTimeArg

  goalTimeArg = ""

  # ----------------------------------------- #
  # define subgoalListOfDicts
  #
  # iterate over each fact for edb name 
  # and arity

  prev_evald_facts = []

  for fact in factMeta :

    # ----------------------------------------- #
    # get relation name

    subgoalName = fact.relationName

    # avoid duplicates
    if subgoalName in prev_evald_facts :
      pass

    else :

      prev_evald_facts.append( subgoalName )

      # ----------------------------------------- #
      # get length of data list

      numAdomRulesForThisFact = len( fact.dataListWithTypes )

      logging.debug( "  BUILD ADOM : subgoalName            = " + str( subgoalName ) )
      logging.debug( "  BUILD ADOM : fact.dataListWithTypes = " + str( fact.dataListWithTypes ) )

      # ----------------------------------------- #
      # need one adom rule per datum in the fact

      for i in range( 0, numAdomRulesForThisFact ) :

        subgoalListOfDicts = []
        oneSubgoalDict = {}

        # ----------------------------------------- #
        # define subgoal attribute list

        subgoalAttList = []
        for j in range( 0, numAdomRulesForThisFact ) :

          # set variable and wildcards
          if i == j :
            subgoalAttList.append( "T" )

            # append type to base relation name
            dataType     = fact.dataListWithTypes[ i ][ 1 ]
            relationName = base_relationName + "_" + dataType
            logging.debug( "  BUILD ADOM : relationName = " + relationName )

          else :
            subgoalAttList.append( "_" )


        # ----------------------------------------- #
        # define subgoal polarity

        polarity = ""

        # ----------------------------------------- #
        # define subgoal time argument

        subgoalTimeArg = ""

        # ----------------------------------------- #
        # save data to subgoal dict

        if subgoalName.endswith( "_edb" ) :
          oneSubgoalDict[ "subgoalName" ]    = subgoalName.replace( "_edb", "" )
        else :
          oneSubgoalDict[ "subgoalName" ]    = subgoalName

        oneSubgoalDict[ "subgoalAttList" ] = subgoalAttList
        oneSubgoalDict[ "polarity" ]       = polarity
        oneSubgoalDict[ "subgoalTimeArg" ] = subgoalTimeArg

        subgoalListOfDicts.append( oneSubgoalDict )

        # ----------------------------------------- #
        # save adom rule

        newRuleData = {}
        newRuleData[ "relationName" ]       = relationName
        newRuleData[ "goalAttList" ]        = goalAttList
        newRuleData[ "goalTimeArg" ]        = goalTimeArg
        newRuleData[ "subgoalListOfDicts" ] = subgoalListOfDicts
        newRuleData[ "eqnDict" ]            = {}

        logging.debug( "  BUILD ADOM : newRule with relationName       = " + str( newRuleData[ "relationName" ] ) )
        logging.debug( "  BUILD ADOM : newRule with goalAttList        = " + str( newRuleData[ "goalAttList" ] ) )
        logging.debug( "  BUILD ADOM : newRule with goalTimeArg        = " + str( newRuleData[ "goalTimeArg" ] ) )
        logging.debug( "  BUILD ADOM : newRule with subgoalListOfDicts = " + str( newRuleData[ "subgoalListOfDicts" ] ) )
        logging.debug( "  BUILD ADOM : newRule with eqnDict            = " + str( newRuleData[ "eqnDict" ] ) )

        # ----------------------------------------- #
        # generate a new rule id

        rid = tools.getIDFromCounters( "rid" )

        # ----------------------------------------- #
        # create new rule object and save meta

        #newRule = Rule.Rule( rid, newRuleData, cursor )
        #newRules.append( newRule )
        newRule        = copy.deepcopy( Rule.Rule( rid, newRuleData, cursor) )
        newRule.cursor = cursor # need to do this for some reason or else cursor disappears?

        if newRule.relationName == "adom_string" :
          newRule.goal_att_type_list.append( [ 0, "string" ] )
          newRule.saveToGoalAtt()
        elif newRule.relationName == "adom_int" :
          newRule.goal_att_type_list.append( [ 0, "int" ]  )
          newRule.saveToGoalAtt()

        newRules.append( newRule )

        logging.debug( "  BUILD ADOM : saved new rule with rid=" + str( newRule.rid ) + " and ruleData:\n" + str( newRule.ruleData ) )


#  # ----------------------------------------- #
#  # define adom rules over clock facts
#
#  newRuleData_clock_att0 = {}
#  newRuleData_clock_att0[ "relationName" ]       = "adom_string"
#  newRuleData_clock_att0[ "goalAttList" ]        = [ "T" ]
#  newRuleData_clock_att0[ "goalTimeArg" ]        = ""
#  newRuleData_clock_att0[ "subgoalListOfDicts" ] = [ { "subgoalName" : "clock", \
#                                                       "subgoalAttList" : [ "T", "_", "_", "_" ], \
#                                                       "polarity" : "", \
#                                                       "subgoalTimeArg" : "" } ]
#  newRuleData_clock_att0[ "eqnDict" ]            = {}
#  rid = tools.getIDFromCounters( "rid" )
#  newRule_clock_att0        = copy.deepcopy( Rule.Rule( rid, newRuleData_clock_att0, cursor) )
#  newRule_clock_att0.cursor = cursor # need to do this for some reason or else cursor disappears?
#  newRules.append( newRule_clock_att0 )
#
#  newRuleData_clock_att1 = {}
#  newRuleData_clock_att1[ "relationName" ]       = "adom_string"
#  newRuleData_clock_att1[ "goalAttList" ]        = [ "T" ]
#  newRuleData_clock_att1[ "goalTimeArg" ]        = ""
#  newRuleData_clock_att1[ "subgoalListOfDicts" ] = [ { "subgoalName" : "clock", \
#                                                       "subgoalAttList" : [ "_", "T", "_", "_" ], \
#                                                       "polarity" : "", \
#                                                       "subgoalTimeArg" : "" } ]
#  newRuleData_clock_att1[ "eqnDict" ]            = {}
#  rid = tools.getIDFromCounters( "rid" )
#  newRule_clock_att1        = copy.deepcopy( Rule.Rule( rid, newRuleData_clock_att1, cursor) )
#  newRule_clock_att1.cursor = cursor # need to do this for some reason or else cursor disappears?
#  newRules.append( newRule_clock_att1 )
#
#  newRuleData_clock_att2 = {}
#  newRuleData_clock_att2[ "relationName" ]       = "adom_int"
#  newRuleData_clock_att2[ "goalAttList" ]        = [ "T" ]
#  newRuleData_clock_att2[ "goalTimeArg" ]        = ""
#  newRuleData_clock_att2[ "subgoalListOfDicts" ] = [ { "subgoalName" : "clock", \
#                                                       "subgoalAttList" : [ "_", "_", "T", "_" ], \
#                                                       "polarity" : "", \
#                                                       "subgoalTimeArg" : "" } ]
#  newRuleData_clock_att2[ "eqnDict" ]            = {}
#  rid = tools.getIDFromCounters( "rid" )
#  newRule_clock_att2        = copy.deepcopy( Rule.Rule( rid, newRuleData_clock_att2, cursor) )
#  newRule_clock_att2.cursor = cursor # need to do this for some reason or else cursor disappears?
#  newRules.append( newRule_clock_att2 )
#
#  newRuleData_clock_att3 = {}
#  newRuleData_clock_att3[ "relationName" ]       = "adom_int"
#  newRuleData_clock_att3[ "goalAttList" ]        = [ "T" ] 
#  newRuleData_clock_att3[ "goalTimeArg" ]        = ""
#  newRuleData_clock_att3[ "subgoalListOfDicts" ] = [ { "subgoalName" : "clock", \
#                                                       "subgoalAttList" : [ "_", "_", "_", "T" ], \
#                                                       "polarity" : "", \
#                                                       "subgoalTimeArg" : "" } ]
#  newRuleData_clock_att3[ "eqnDict" ]            = {}
#  rid = tools.getIDFromCounters( "rid" )
#  newRule_clock_att3        = copy.deepcopy( Rule.Rule( rid, newRuleData_clock_att3, cursor) )
#  newRule_clock_att3.cursor = cursor # need to do this for some reason or else cursor disappears?
#  newRules.append( newRule_clock_att3 )

  logging.debug( "  BUILD ADOM : returning newRules = " + str( newRules ) )
  return newRules


##############################
#  RESOLVE DOUBLE NEGATIVES  #
##############################
def resolveDoubleNegatives( rid, fromName, cursor ) :

  # get all subgoal ids and names
  cursor.execute( "SELECT sid,subgoalName FROM Subgoals WHERE rid=='" + rid + "'" )
  subInfo = cursor.fetchall()
  subInfo = tools.toAscii_multiList( subInfo )

  print "subInfo = " + str( subInfo )

  # check for double negatives
  for sub in subInfo :

    sid  = sub[0]
    name = sub[1]

    if "not_" in name[0:4] and "_from_" in name :

      # check if negated
      cursor.execute( "SELECT subgoalPolarity FROM Subgoals WHERE rid=='" + rid + "' AND sid=='" + sid + "'" )
      sign = cursor.fetchone()
      sign = tools.toAscii_str( sign )

      if sign == "notin" :

        # build base name
        baseName = "_from_" + fromName

        # build positive name
        nameLen     = len( name )
        baseNameLen = len( baseName )
        posName     = name[ 4 : nameLen - baseNameLen ]

        # replace subgoal name with postivie equivalent.
        cursor.execute( "UPDATE Subgoals SET subgoalName=='" + posName + "' WHERE rid=='" + rid + "' AND sid=='" + sid + "'" )

        # remove negation
        cursor.execute( "UPDATE Subgoals SET subgoalPolarity=='' WHERE rid=='" + rid + "' AND sid=='" + sid + "'" )

        print "UPDATED DOUBLE NEGATIVE!"
        print dumpers.reconstructRule( rid, cursor )
        #tools.bp( __name__, inspect.stack()[0][3], "ici" )



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
#  SHIFT ARITH OPS  #
#####################
# given list of rids for the IDB rule set to be negated.
# for rules with arithmetic operations in the head,
# rewrite the rules into a series of separate, but sematically
# equivalent rules.
def shiftArithOps( nameRIDs, cursor ) :

  newRIDs = []

  # for each rule, check if goal contains an arithmetic operation
  for rid in nameRIDs :
    cursor.execute( "SELECT attID,attName FROM GoalAtt WHERE rid=='" + rid + "'" )
    attData = cursor.fetchall()
    attData = tools.toAscii_multiList( attData )

    for att in attData :
      attID   = att[0]
      attName = att[1]

      if containsOp( attName ) :

        # compose raw attribute with function call 
        # (only supporting arithmetic ops at the moment)
        decomposedAttName = getOp( attName )  # [ lhs, op, rhs ]
        lhs = decomposedAttName[0]
        op  = decomposedAttName[1]
        rhs = decomposedAttName[2]

        # build substitute goal attribute variable
        newAttName = lhs + "0"

        # replace the goal attribute variable
        replaceGoalAtt( newAttName, attID, rid, cursor )

        # rewrite subgoals containing the universal variable included in the equation
        # with unique subgoals referencing new IDB definitions.
        newArithRuleRIDs = arithOpSubgoalRewrites( rid, newAttName, lhs, attName, cursor )
        newRIDs.extend( newArithRuleRIDs )

  return newRIDs

###############################
#  ARITH OP SUBGOAL REWRITES  #
###############################
# given the id for one of the rules targeted for NegativeWrites,
# the string replacing the arithmetic expression in the goal,
# and the universal attribute appearing in an arithmetic expression
# in the head.
# replace the subgoals containing the universal attribute with new subgoals
# such that the new subgoals have unique names and the new replacement attribute 
# replace the universal attribute in the subgoal.
#
def arithOpSubgoalRewrites( rid, newAttName, oldExprAtt, oldExpr, cursor ) :

  newRIDs = []

  # get subgoal info
  cursor.execute( "SELECT Subgoals.sid,Subgoals.subgoalName,attID FROM Subgoals,SubgoalAtt WHERE Subgoals.rid=='" + rid + "' AND Subgoals.rid==SubgoalAtt.rid AND attName=='" + oldExprAtt + "'" )
  sidData = cursor.fetchall()
  sidData = tools.toAscii_multiList( sidData )

  # ............................................. #
  # remove duplicates
  tmp = []
  for sid in sidData :
    if not sid in tmp :
      tmp.append( sid )
  sidData = tmp
  # ............................................. #

  for data in sidData :
    sid         = data[0]
    subgoalName = data[1]
    attID       = data[2]

    # --------------------------------------------- #
    # replace subgoal name with unique new name 
    # connecting to another set of IDB rule(s)

    # get rule name for this rid
    cursor.execute( "SELECT goalName FROM Rule WHERE rid=='" + rid + "'" )
    ruleName = cursor.fetchone()
    ruleName = tools.toAscii_str( ruleName )

    # generate new unique subgoal name
    newSubgoalName = ruleName + "_" + subgoalName + "_" + tools.getID_4() + "_arithoprewrite"

    cursor.execute( "UPDATE Subgoals SET subgoalName=='" + newSubgoalName + "' WHERE rid=='" + rid + "' AND sid=='" + sid + "'" )

    # --------------------------------------------- #
    # replace universal attribute in subgoals
    cursor.execute( "UPDATE SubgoalAtt SET attName=='" + newAttName + "' WHERE rid=='" + rid + "' AND attID=='" + str( attID ) + "' AND sid=='" + sid + "'" )

    # --------------------------------------------- #
    # build new subgoal IDB rules
    newRID = arithOpSubgoalIDBWrites( rid, sid, newSubgoalName, subgoalName, oldExprAtt, oldExpr, attID, cursor )
    newRIDs.append( newRID )

  return newRIDs


#################################
#  ARITH OP SUBGOAL IDB WRITES  #
#################################
# write the new IDB rules supporting the distribution of equations
# across rule subgoals.
def arithOpSubgoalIDBWrites( oldRID, targetSID, newSubgoalName, oldSubgoalName, oldExprAtt, oldExpr, attID, cursor) :

  # --------------------------------------------- #
  # generate new rule ID                          #
  # --------------------------------------------- #
  newRID = tools.getID()

  # --------------------------------------------- #
  # insert new rule data                          #
  # --------------------------------------------- #
  rid         = newRID
  goalName    = newSubgoalName
  goalTimeArg = ""
  rewritten   = "True"
  cursor.execute( "INSERT INTO Rule (rid, goalName, goalTimeArg, rewritten) VALUES ('" + rid + "','" + goalName + "','" + goalTimeArg + "','" + rewritten + "')" )

  # --------------------------------------------- #
  # insert new rule data                          #
  # --------------------------------------------- #
  # get attribute data from original subgoal
  cursor.execute( "SELECT attID,attName,attType FROM SubgoalAtt WHERE rid=='" + oldRID + "' AND sid=='" + targetSID + "'" )
  data = cursor.fetchall()
  data = tools.toAscii_multiList( data )

  # ............................................. #
  # define the att list for the only subgoal 
  # in the new rule body and replace new goal
  # att str with old goal att str

  subgoalAttData             = data
  subgoalAttData[ attID ][1] = oldExprAtt

  # ............................................. #
  # resolve wildcard attributes to actual 
  # variables.

  subgoalAttData = resolveWildcardAtts( subgoalAttData )

  # ............................................. #
  # define goal att list and 
  # replace old arithmetic expression

  # need this shit to prevent mutating subgoalAttData
  goalAttData = []
  for thing in data :
    thisThing = [ i for i in thing ]
    goalAttData.append( thisThing )
  goalAttData[attID][1] = oldExpr

  # ............................................. #
  # perform inserts

  # goal attributes
  for att in goalAttData :
    attID   = att[0]
    attName = att[1]
    attType = att[2]
    cursor.execute( "INSERT INTO GoalAtt (rid, attID, attName, attType) VALUES ('" + rid + "','" + str( attID ) + "','" + attName + "','" + attType + "')" )

  # subgoal
  sid            = tools.getID()
  subgoalName    = oldSubgoalName
  subgoalTimeArg = ""
  cursor.execute( "INSERT INTO Subgoals (rid, sid, subgoalName, subgoalTimeArg) VALUES ('" + rid + "','" + sid + "','" + subgoalName + "','" + subgoalTimeArg + "')" )

  # subgoal attributes
  for att in subgoalAttData :
    attID   = att[0]
    attName = att[1]
    attType = att[2]
    cursor.execute( "INSERT INTO SubgoalAtt (rid, sid, attID, attName, attType) VALUES ('" + rid + "','" + sid + "','" + str( attID ) + "','" + attName + "','" + attType + "')" )

  # ............................................. #
  # resolve types
  newRule = Rule.Rule( newRID, cursor )
  newRule.setAttTypes()

  #if "log_log_" in newSubgoalName[0:8] and "_log_" in newSubgoalName[12:17] :
  #  tools.bp( __name__, inspect.stack()[0][3], "here" )

  return newRID # means building the rule object twice. kind of redundant...


###########################
#  RESOLVE WILDCARD ATTS  #
###########################
# resolve wildcard attributes to actual variables b/c
# these attributes are copied directly into the goal 
# attribute list of this new rule.
def resolveWildcardAtts( subgoalAttData ) :
  counter = 0
  for data in subgoalAttData :

    if data[1] == "_" :
      data[1] = "B" + str( counter )
      counter += 1

  return subgoalAttData


##########################
#  SHIFT FUNCTION CALLS  #
##########################
# given list of rids for IDB rule set to be negated.
# for rules with function calls in the head, shift 
# the function call to an eqn in the body.
def shiftFunctionCalls( nameRIDs, cursor ) :

  # for each rule, check if goal contains a function call
  for rid in nameRIDs :
    cursor.execute( "SELECT attID,attName FROM GoalAtt WHERE rid=='" + rid + "'" )
    attData = cursor.fetchall()
    attData = tools.toAscii_multiList( attData )

    for att in attData :
      attID   = att[0]
      attName = att[1]

      if containsOp( attName ) :

        # compose raw attribute with function call 
        # (only supporting arithmetic ops at the moment)
        decomposedAttName = getOp( attName )  # [ lhs, op, rhs ]
        lhs = decomposedAttName[0]
        op  = decomposedAttName[1]
        rhs = decomposedAttName[2]

        # build substitute goal attribute variable
        newAttName = lhs + "0"

        # generate appropriate equation using a new variable 
        # for the corresponding goal attribute.
        eqn = generateEqn( newAttName, lhs, op, rhs, rid, cursor )

        # replace the goal attribute variable
        replaceGoalAtt( newAttName, attID, rid, cursor )

        # add equation to rule
        addEqn( eqn, rid, cursor )


##################
#  GENERATE EQN  #
##################
# generate appropriate equation using a new variable 
# for the corresponding goal attribute.
def generateEqn( newAttName, lhs, op, rhs, rid, cursor ) :

  eqn = newAttName + "==" + lhs + op + rhs

  return eqn


######################
#  REPLACE GOAL ATT  #
######################
# replace the goal attribute variable
def replaceGoalAtt( newAttName, attID, rid, cursor ) :

  cursor.execute( "UPDATE GoalAtt SET attName=='" + newAttName + "' WHERE rid=='" + rid + "' AND attID=='" + str( attID ) + "'" )


#############
#  ADD EQN  #
#############
# add equation to rule
def addEqn( eqn, rid, cursor ) :

  # generate new random identifier
  eid = tools.getID()

  # add equation for this rule
  cursor.execute( "INSERT INTO Equation VALUES ('" + rid + "','" + eid + "','" + eqn + "')" )


######################
#  GENERATE NEW VAR  #
######################
def generateNewVar( oldVar ) :
  return oldVar + "__KEEP__" #+ tools.getID_4()


#################
#  CONTAINS OP  #
#################
def containsOp( attName ) :

  flag = False
  for op in arithOps :
    if op in attName :
      flag = True

  return flag


############
#  GET OP  #
############
def getOp( attName ) :

  for op in arithOps :

    if op in attName :
      s = attName.split( op )
      return [ s[0], op, s[1] ]

    else :
      tools.bp( __name__, inspect.stack()[0][3], "FATAL ERROR : attName '" + attName + "' does not contain an arithOp.\nPlease check if universe exploded. Aborting..."  )


#################
#  PRINT RULES  #
#################
def printRules( rids, cursor ) :
  for rid in rids :
    print dumpers.reconstructRule( rid, cursor )


##################
#  GET ALL RIDS  #
##################
# return the list of rids for all rules in the program currently stored in cursor.
def getAllRuleRIDs( cursor ) :
  cursor.execute( "SELECT rid FROM Rule" )
  rids = cursor.fetchall()
  rids = tools.toAscii_list( rids )
  return rids


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


#########################
#  REWRITE PARENT RULE  #
#########################
# replace negated subgoals in parent rules with positive counterparts.
# returns name of negated subgoal replaced by positive subgoal and 
# the parent RID.
def rewriteParentRule( rid, cursor ) :

  negatedIDBNames = []

  # .................................................... #
  # get rule name
  cursor.execute( "SELECT goalName FROM Rule WHERE rid='" + rid + "'" )
  goalName = cursor.fetchone()
  goalName = tools.toAscii_str( goalName )

  # .................................................... #
  # get list of negated IDB subgoals
  cursor.execute( "SELECT sid,subgoalName FROM Subgoals WHERE rid='" + rid + "' AND argName=='notin'" )
  negatedSubgoals = cursor.fetchall()
  negatedSubgoals = tools.toAscii_multiList( negatedSubgoals )

  #print "negatedSubgoals = " + str( negatedSubgoals )

  # .................................................... #
  # substitute with appropriate positive counterpart
  for subgoal in negatedSubgoals :
    sid  = subgoal[0]
    name = subgoal[1]

    if "_arithoprewrite" in name :
      pass

    elif isIDB( name, cursor ) :

      positiveName = "not_" + name + "_from_" + goalName
  
      #print "positiveName = " + positiveName
  
      # .................................................... #
      # substitute in positive subgoal name
      cursor.execute( "UPDATE Subgoals SET subgoalName=='" + positiveName + "' WHERE rid=='" + rid + "' AND sid=='" + sid + "'" )
  
      # .................................................... #
      # erase negation on this subgoal
      cursor.execute( "UPDATE Subgoals SET subgoalPolarity=='' WHERE rid=='" + rid + "' AND sid=='" + sid + "'" )
  
      # .................................................... #
      # save for return data
      negatedIDBNames.append( [ name, rid, sid ] )


  # .................................................... #
  # remove duplicates
  #negatedIDBNames = removeDups( rid, negatedIDBNames )

  return negatedIDBNames


#################
#  REMOVE DUPS  #
#################
def removeDups( parentRID, negatedIDBNames ) :

  tmp = []
  for data in negatedIDBNames :
    name = data[0]
    if not name in tmp :
      tmp.append( name )

  return [ [ x, parentRID ] for x in tmp ]


########################
#  GET RIDS FROM NAME  #
########################
# return the list of all rids associated with a particular goal name.
def getRIDsFromName( name, cursor ) :

  cursor.execute( "SELECT rid FROM Rule WHERE goalName='" + name + "'" )
  ridList = cursor.fetchall()
  ridList = tools.toAscii_list( ridList )

  return ridList


#########
#  EOF  #
#########
