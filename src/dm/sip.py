#/usr/bin/env python

'''
sip.py
'''

import ConfigParser, copy, itertools, logging, os, sys
import dm_tools

if not os.path.abspath( __file__ + "/../.." ) in sys.path :
  sys.path.append( os.path.abspath( __file__ + "/../.." ) )
if not os.path.abspath( __file__ + "/../../dedt/translators" ) in sys.path :
  sys.path.append( os.path.abspath( __file__ + "/../../dedt/translators" ) )
from translators import c4_translator, dumpers_c4
from dedt        import Fact, Rule
from evaluators  import c4_evaluator
from utils       import dumpers, tools

##########################
#  DO DEMORGANS SIP IDB  #
##########################
# create a new set of rules representing the application of 
# DeMorgan's Law on the first-order logic representation
# of the targetted rules.
# use domains defined via evaluation results gathered in idbs.
# observe every program appearing at the end of a DM-SIP rewrite
# is runnable.
def doDeMorgans_sip_idb( factMeta, \
                         ruleMeta, \
                         targetRuleMetaSets, \
                         rid_to_rule_meta_map, \
                         cursor, \
                         argDict ) :

  logging.debug( "  DO DEMORGANS SIP EDB : running process..." )

  newDMRules = []

  COUNTER = 0
  for rule_info in targetRuleMetaSets :

    parent_list = rule_info[ 0 ]
    ruleSet     = rule_info[ 1 ]

    for rule in ruleSet :
      logging.debug( "//////////////////////////////////////////////////" )
      logging.debug( "  DO DEMORGANS SIP EDB : parent_list: " + str( parent_list ) )
      logging.debug( "  DO DEMORGANS SIP EDB : ruleSet:" )
      logging.debug( "    " + dumpers.reconstructRule( rule.rid, rule.cursor ) )
      logging.debug( "//////////////////////////////////////////////////" )

    # ----------------------------------------- #
    # get an original rule id to reference types

    orig_rid = ruleSet[0].rid

    # ----------------------------------------- #
    # get new rule name

    orig_name = ruleSet[0].relationName

    # ----------------------------------------- #
    # get new rule goal attribute list
    # works only if goal att lists are uniform 
    # across all rules per set

    goalAttList = ruleSet[0].ruleData[ "goalAttList" ]

    # ----------------------------------------- #
    # get new rule goal time arg

    goalTimeArg = ""

    # ----------------------------------------- #
    # get current results

    #parsedResults = get_current_results( argDict, cursor )
    #logging.debug( "  DO DEMORGANS SIP EDB : done running eval." )

    # ----------------------------------------- #
  
    final_fmla = get_final_fmla( ruleSet )

    # ----------------------------------------- #
    # get the lists of all strings and ints

    #all_strings = get_all_strings( factMeta )
    #all_ints    = get_all_ints( factMeta, cursor )

    # ----------------------------------------- #
    # need a new set of dm rules for every instance of a particular
    # negated subgoal

    for curr_parent in parent_list :

      parent_name = curr_parent[0]
      parent_rid  = curr_parent[1]

      logging.debug( "  DO DEMORGANS SIP EDB : parent rule:" )
      logging.debug( "     " + dumpers.reconstructRule( parent_rid, cursor ) )

      not_name = "not_" + orig_name + "_f" + str( parent_rid )

      # ----------------------------------------- #
      # build the domain subgoal info

      # returns a subgoal dict
      #uni_dom_sub = build_uni( not_name, goalAttList )

      # returns a subgoal dict
      #exi_dom_sub = build_exi( orig_name, not_name, goalAttList, ruleMeta )

      # ----------------------------------------- #
      # get the domain rules

      dom_rules = get_dom_rules( orig_name, \
                                 not_name, \
                                 orig_rid, \
                                 parent_rid, \
                                 rid_to_rule_meta_map, \
                                 ruleMeta, \
                                 cursor, \
                                 argDict )
      ruleMeta.extend( dom_rules )

      # ----------------------------------------- #
      # each clause in the final dnf fmla 
      # informs the subgoal list of a new 
      # datalog rule
  
      newDMRules = dnfToDatalog( orig_name, \
                                 not_name, \
                                 goalAttList, \
                                 goalTimeArg, \
                                 final_fmla, \
                                 ruleSet, \
                                 ruleMeta, \
                                 parent_name, \
                                 parent_rid, \
                                 rid_to_rule_meta_map, \
                                 cursor, \
                                 argDict )
  
      # ----------------------------------------- #
      # add new dm rules to the rule meta
  
      ruleMeta.extend( newDMRules )

      # ----------------------------------------- #
      # replace instances of the negated subgoal
      # with instances of the positive not_
      # subgoal
  
      ruleMeta = replaceSubgoalNegations( orig_name, \
                                          not_name, \
                                          parent_rid, \
                                          ruleMeta )

    # ----------------------------------------- #
    # resolve double negations

    ruleMeta = resolveDoubleNegations( ruleMeta )

    # ----------------------------------------- #
    # order recursive rules last

    ruleMeta = dm_tools.sortDMRules( ruleMeta )

    COUNTER += 1

  return ruleMeta


###################
#  GET DOM RULES  #
###################
# Rule object structure :
#  { relationName : 'relationNameStr', 
#    goalAttList:[ data1, ... , dataN ], 
#    goalTimeArg : ""/next/async,
#    subgoalListOfDicts : [ { subgoalName : 'subgoalNameStr', 
#                             subgoalAttList : [ data1, ... , dataN ], 
#                             polarity : 'notin' OR '', 
#                             subgoalTimeArg : <anInteger> }, ... ],
#    eqnDict : { 'eqn1':{ variableList : [ 'var1', ... , 'varI' ] }, 
#                 ... , 
#                 'eqnM':{ variableList : [ 'var1', ... , 'varJ' ] }  } }
def get_dom_rules( orig_name, \
                   not_name, \
                   orig_rid, \
                   parent_rid, \
                   rid_to_rule_meta_map, \
                   ruleMeta, \
                   cursor, \
                   argDict ) :

  newRules = []

  # ----------------------------------------- #
  # get parameters

  settings_path = argDict[ "settings" ]

  # ========== POST EOT FILTER ========== #
  try :
    POST_EOT_FILTER = tools.getConfig( settings_path, "DEFAULT", "POST_EOT_FILTER", bool )
  except ConfigParser.NoOptionError :
    POST_EOT_FILTER = False
    logging.warning( "WARNING : no 'POST_EOT_FILTER' defined in 'DEFAULT' section of " + \
                     "settings.ini ...running with POST_EOT_FILTER=False." )

  # ----------------------------------------- #
  # ----------------------------------------- #

  logging.debug( "=====================================================" )
  logging.debug( "  GET DOM RULES : orig_name   = " + orig_name )
  logging.debug( "  GET DOM RULES : not_name    = " + not_name )
  logging.debug( "  GET DOM RULES : orig_rid    = " + str( orig_rid ) )
  logging.debug( "  GET DOM RULES : parent_rid  = " + str( parent_rid ) )
  logging.debug( "  GET DOM RULES : parent rule : " )
  logging.debug( "     " + dumpers.reconstructRule( parent_rid, cursor ) )

  # ------------------------------------------ #
  # gather subgoal atts

  negated_subgoal_atts = get_negated_subgoal_atts( orig_name, parent_rid, ruleMeta )
  logging.debug( "  GET DOM RULES : negated_subgoal_atts = " + str( negated_subgoal_atts ) )

  # ------------------------------------------ #
  # map parent goal indexes to atts for
  # eval data extraction

  parent_goal_att_to_index_map, parent_goal_att_list = get_goal_att_to_index_map( parent_rid, ruleMeta )
  logging.debug( "  GET DOM RULES : parent_goal_att_to_index_map = " + str( parent_goal_att_to_index_map ) )

  # ------------------------------------------ #
  # generate sip domain idbs
  # [ { subgoalName : 'subgoalNameStr', 
  #     subgoalAttList : [ data1, ... , dataN ], 
  #     polarity : 'notin' OR '', 
  #     subgoalTimeArg : <anInteger> }, ... ]

  # ------------------------------------------ #
  # build the universal domain rule

  uni_ruleData = {}

  # get relation name
  uni_ruleData[ "relationName" ] = "unidom_" + not_name

  # check if a rule already exists
  # to prevent duplicates.
  if idb_already_exists( uni_ruleData[ "relationName" ], cursor ) :
    return newRules

  #get goal atts
  uni_ruleData[ "goalAttList" ] = [ "A" + str(i) \
                                for i in \
                                range( 0, len( negated_subgoal_atts[0] ) ) ] # just need one for arity

  # map domain atts to negated subgoal atts
  # eg. [ [ X, Y ], [ Y, Q ] ]
  #  => dom_thing( A0, A1 ) <- ...
  #  => { A0: [ X, Y ], A1: [ Y, Q ] }
  # initialize maps to empty lists.
  uni_dom_atts_to_par_atts_map = { "A" + str( i ) : [] \
                                   for i in range( 0, \
                                   len( uni_ruleData[ "goalAttList" ] ) ) }
  for neg_sub_atts in negated_subgoal_atts :
    for i in range( 0, len( neg_sub_atts ) ) :
      sub_att = neg_sub_atts[ i ]
      uni_dom_atts_to_par_atts_map[ "A" + str(i) ].append( sub_att )
  logging.debug( "  GET DOM RULES : uni_dom_atts_to_par_atts_map = " + str( uni_dom_atts_to_par_atts_map ) )

  logging.debug( "  GET DOM RULES : ----------------------------------------" )
  logging.debug( "  GET DOM RULES : relationName         = " + uni_ruleData[ "relationName" ] )
  logging.debug( "  GET DOM RULES : goalAttList          = " + str( uni_ruleData[ "goalAttList" ] ) )
  logging.debug( "  GET DOM RULES : negated_subgoal_atts = " + str( negated_subgoal_atts ) )

  # get goal time arg
  uni_ruleData[ "goalTimeArg" ] = ""

  # get eqn dict
  uni_ruleData[ "eqnDict" ] = {}

  # =================================== #
  # get subgoal list of dicts

  # unidom rules encompass the subset of all tuples in the complenent of the
  # rule targetted for the DM rewrite which help generate data in the parent rule.
  # accordingly, copy over the contents of the parent rule and project the 
  # attributes for the targeted subgoal(s).
  # constrain any remaining free goal variables with the actual contents of the
  # positive definition of the targetted rule.


  # 1. copy and edit over the list of parent subgoals

  parent_rule_meta       = rid_to_rule_meta_map[ parent_rid ]
  uni_subgoalListOfDicts = copy.deepcopy( parent_rule_meta.subgoalListOfDicts )

  # replace subgoal references to the orig_ versions of the rule.
  for i in range( 0, len( uni_subgoalListOfDicts ) ) :
    if dm_tools.is_idb( uni_subgoalListOfDicts[ i ][ "subgoalName" ], ruleMeta ) and \
       not uni_subgoalListOfDicts[ i ][ "subgoalName" ].startswith( "not_" )     and \
       not uni_subgoalListOfDicts[ i ][ "subgoalName" ].startswith( "orig_" )     and \
       not uni_subgoalListOfDicts[ i ][ "subgoalName" ].startswith( "unidom_" )  and \
       not uni_subgoalListOfDicts[ i ][ "subgoalName" ].startswith( "exidom_" ) :
      uni_subgoalListOfDicts[ i ][ "subgoalName" ] = "orig_" + \
                                                     uni_subgoalListOfDicts[ i ][ "subgoalName" ]

  # replace atts in the parent subgoals with the goal atts 
  # for the unidom rule.
  for gatt in uni_dom_atts_to_par_atts_map :
    these_par_atts = uni_dom_atts_to_par_atts_map[ gatt ]

    # iterate over parent subgoals
    for i in range( 0, len( uni_subgoalListOfDicts ) ) :
      sub = uni_subgoalListOfDicts[ i ]

      # iterate over the parent subgoal atts
      for j in range( 0, len( sub[ "subgoalAttList" ] ) ) :
        sub_att = sub[ "subgoalAttList" ][ j ]

        # make the replacement if the parent sub att appears
        # in the atts corresponding to the unidom goal att
        # under consideration.
        if sub_att in these_par_atts :
          uni_subgoalListOfDicts[ i ][ "subgoalAttList" ][ j ] = gatt

  logging.debug( "  GET DOM RULES : subgoalListOfDicts = " + str( uni_subgoalListOfDicts ) )

  # 2. integrate a reference to the original version of the targetted rule to fill
  #    in any missing attributes.

  all_body_atts = []
  for sub in uni_subgoalListOfDicts :
    if sub[ "polarity" ] == "" :
      for satt in sub[ "subgoalAttList" ] :
        if not satt in all_body_atts :
          all_body_atts.append( satt )

  missing_gatts = []
  for gatt in uni_dom_atts_to_par_atts_map :
    if not gatt in all_body_atts :
      missing_gatts.append( gatt )

#  print "uni_dom_atts_to_par_atts_map = " + str( uni_dom_atts_to_par_atts_map )
#  print "all_body_atts = " + str( all_body_atts )
#  print "missing_gatts = " + str( missing_gatts )
#
#  if uni_ruleData[ "relationName" ] == "unidom_not_node_f23" :
#    sys.exit( "blah" )

  if len( missing_gatts ) > 0 :
    orig_sub = {}
    orig_sub[ "subgoalName" ]    = orig_name
    orig_sub[ "subgoalTimeArg" ] = ""
    orig_sub[ "polarity" ]       = ""
    orig_sub[ "subgoalAttList" ] = []
    for i in range( 0, len( uni_dom_atts_to_par_atts_map ) ) :
      if "A" + str( i ) in missing_gatts :
        orig_sub[ "subgoalAttList" ].append( "A" + str( i ) )
      else :
        orig_sub[ "subgoalAttList" ].append( "_" )
    uni_subgoalListOfDicts.append( orig_sub )

  uni_ruleData[ "subgoalListOfDicts" ] = uni_subgoalListOfDicts

  # =================================== #
  # save rule

  # replace time arg with constant if the negated subgoal stems from post
  if POST_EOT_FILTER and parent_name == "post" :
    uni_ruleData[ "goalAttList" ][ -1 ] = argDict[ "EOT" ]

  uni_rid            = tools.getIDFromCounters( "rid" )
  uni_rule        = copy.deepcopy( Rule.Rule( uni_rid, uni_ruleData, cursor) )
  uni_rule.cursor = cursor # need to do this for some reason or else cursor disappears?

  # set the unidom rule types manually
  uni_goal_types = []
  for rule in ruleMeta :
    if rule.rid == orig_rid :
      uni_goal_types = rule.goal_att_type_list
  assert( len( uni_goal_types ) > 0 )

  uni_rule.goal_att_type_list = uni_goal_types
  uni_rule.manually_set_types()

  # check if a rule already exists
  # to prevent duplicates.
  if not dm_tools.identical_rule_already_exists( uni_rule, ruleMeta ) :
    newRules.append( uni_rule )
    logging.debug( "  GET DOM RULES : added uni dom rule :\n     " + \
                   dumpers.reconstructRule( uni_rule.rid, uni_rule.cursor ) )
  else :
    logging.debug( "  GET DOM RULES : NOT adding uni dom rule :\n     " + \
                   dumpers.reconstructRule( uni_rule.rid, uni_rule.cursor ) ) 

#  if uni_rule.relationName == "unidom_not_node_f40" :
#    print orig_name
#    print not_name
#    print dumpers.reconstructRule( parent_rid, uni_rule.cursor )
#    print dumpers.reconstructRule( uni_rule.rid, uni_rule.cursor )
#    sys.exit( "blah" )

  # ------------------------------------------ #
  # build the existential domain rules

  # exidom_ encompasses the set of data from the original version
  # of the target rule which contributes to generating data in 
  # the original version of the target relation.
  # accordingly, one exidom_ rule exists per rule in the definition.

  # get the list of rules defining the target relation
  target_rules = []
  for rule in ruleMeta :
    if rule.relationName == "orig_" + orig_name :
      target_rules.append( rule )

  for target_rule in target_rules :

    # grab all existential vars from the original definition for the
    # target relation.
    all_exi_vars = []
    for sub in target_rule.subgoalListOfDicts :
      for satt in sub[ "subgoalAttList" ] :
        if not satt in target_rule.goalAttList and \
           not satt in all_exi_vars            and \
           not satt == "_" :
          all_exi_vars.append( satt )
  
    # only write an exidom_ rule if existential vars exist.
    if len( all_exi_vars ) > 0 :

      # =================================== #
      # get subgoals
      # need one exidom rule per subgoal
      # in the target rule.

      all_subgoals = copy.deepcopy( target_rule.subgoalListOfDicts )

      for asub in all_subgoals :

        print "asub = " + str( asub )

        exi_ruleData = {}
    
        # get relation name
        # need the extra _f to maintain arities.
        exi_ruleData[ "relationName" ] = "exidom_" + not_name + "_f" + str( target_rule.rid )
  
        #get goal atts
        exi_ruleData[ "goalAttList" ] = copy.deepcopy( all_exi_vars )

        # get goal time arg
        exi_ruleData[ "goalTimeArg" ] = ""

        # get eqn dict
        exi_ruleData[ "eqnDict" ] = {}

        if not asub[ "subgoalName" ].startswith( "orig_" )   and \
           not asub[ "subgoalName" ] == "clock"              and \
           not asub[ "subgoalName" ] == "next_clock"         and \
           not asub[ "subgoalName" ] == "crash"              and \
           not asub[ "subgoalName" ].startswith( "not_" )    and \
           not asub[ "subgoalName" ].startswith( "unidom_" ) and \
           not asub[ "subgoalName" ].startswith( "exidom_" ) and \
           dm_tools.is_idb( asub[ "subgoalName" ], ruleMeta ) :
          asub[ "subgoalName" ] = "orig_" + asub[ "subgoalName" ]
    
        exi_ruleData[ "subgoalListOfDicts" ] = [ asub ]

        # =================================== #
        # save rule
    
        exi_rid         = tools.getIDFromCounters( "rid" )
        exi_rule        = copy.deepcopy( Rule.Rule( exi_rid, exi_ruleData, cursor) )
        exi_rule.cursor = cursor # need to do this for some reason or else cursor disappears?
    
        # set the rule types manually
        exi_goal_types = []
        for gatt in exi_rule.goalAttList :
          for sub in exi_ruleData[ "subgoalListOfDicts" ] :
            if gatt in sub[ "subgoalAttList" ] :
              gatt_index = sub[ "subgoalAttList" ].index( gatt )
              for rule in ruleMeta :
                if rule.relationName == sub[ "subgoalName" ] :
                  exi_goal_types.append( rule.goal_att_type_list[ gatt_index ] )
  
        exi_rule.goal_att_type_list = exi_goal_types
        exi_rule.manually_set_types()
      
        # check if a rule already exists
        # to prevent duplicates.
        if not dm_tools.identical_rule_already_exists( exi_rule, cursor ) :
          newRules.append( exi_rule )
          logging.debug( "  GET DOM RULES : added exi dom rule :\n     " + \
                         dumpers.reconstructRule( exi_rule.rid, exi_rule.cursor ) ) 
        else :
          logging.debug( "  GET DOM RULES : NOT adding exi dom rule :\n     " + \
                         dumpers.reconstructRule( exi_rule.rid, exi_rule.cursor ) ) 
  
  logging.debug( "  GET DOM RULES : domain rules:" )
  for rule in newRules :
    logging.debug( "     " + dumpers.reconstructRule( rule.rid, rule.cursor ) )

  #if uni_ruleData[ "relationName" ] == "unidom_not_path_f2" :
  #  for rule in newRules :
  #    print dumpers.reconstructRule( rule.rid, rule.cursor )
  #  sys.exit( "blah" )

  return newRules


###################
#  GET DOM FACTS  #
###################
# Fact object structure :
# { relationName : 'relationNameStr', 
#   dataList     : [ data1, ... , dataN ], 
#   factTimeArg:<anInteger> }
def get_dom_facts( orig_name, \
                   not_name, \
                   orig_rid, \
                   parent_name, \
                   parent_rid, \
                   parsedResults, \
                   ruleMeta, \
                   all_strings, \
                   all_ints, \
                   cursor, \
                   argDict ) :

  logging.debug( "  GET DOM FACTS : not_name = " + not_name )

  newFacts = []

  # ------------------------------------------ #
  # gather subgoal atts

  negated_subgoal_atts = get_negated_subgoal_atts( orig_name, parent_rid, ruleMeta )

  logging.debug( "  GET DOM FACTS : negated_subgoal_atts = " + str( negated_subgoal_atts ) )

  # ------------------------------------------ #
  # map parent goal indexes to atts for
  # eval data extraction

  parent_goal_att_to_index_map = get_goal_att_to_index_map( parent_rid, ruleMeta )

  logging.debug( "  GET DOM FACTS : parent_goal_att_to_index_map = " + str( parent_goal_att_to_index_map ) )

  # ------------------------------------------ #
  # generate sip edbs based upon parent eval
  # results.

  logging.debug( "  GET DOM FACTS : parsedResults['" + parent_name + \
                 "'] = " + str( parsedResults[ parent_name ] ) )

  try :
    assert( len( parsedResults[ parent_name ] ) > 0 )
  except AssertionError :
    raise AssertionError( "parsedResults['" + parent_name + \
                 "'] = " + str( parsedResults[ parent_name ] ) )

  for tup in parsedResults[ parent_name ] :
    data_list = []

    for att_list in negated_subgoal_atts :
      a_data_list   = []
      contains_list = False

      for index in range( 0, len( att_list ) ) :
        att = att_list[ index ]

        if att in parent_goal_att_to_index_map :
          this_data = tup[ parent_goal_att_to_index_map[ att ] ] 

          # need to make this a list for iterttools
          if this_data.isdigit() :
            a_data_list.append( [ tup[ parent_goal_att_to_index_map[ att ] ] ] )
          else :
            a_data_list.append( [ '"' + tup[ parent_goal_att_to_index_map[ att ] ] + '"' ] )

        else :
          att_type = get_goal_att_type( index, orig_rid, ruleMeta )
          if att_type == "string" :
            a_data_list.append( all_strings )
            contains_list = True

          elif att_type == "int" :
            a_data_list.append( all_ints )
            contains_list = True

          else :
            raise ValueError( "  GET DOM FACTS : unrecognized att_type '" + att_type + "'" )

      data_lists = get_all_data_lists( a_data_list )

    # ------------------------------------------ #
    # create a new edb fact for every data tuple

    for data_tup in data_lists :

      # ------------------------------------------ #
      # generate random ID for fact

      fid = tools.getIDFromCounters( "fid" )

      # ------------------------------------------ #
      # also add in the type info, since 
      # it's easily accessible.
      # observe this only works b/c currently 
      # supporting only ints and strings.

      dataListWithTypes = []
      for data in data_tup :
        if data.isdigit() :
          dataListWithTypes.append( [ data, "int" ] )
        else :
          dataListWithTypes.append( [ data, "string" ] )

      # ------------------------------------------ #
      # define factData

      factData = {}
      factData[ "relationName" ] = "dom_" + not_name
      factData[ "dataList" ]     = data_tup
      factData[ "factTimeArg" ]  = ""

      # ------------------------------------------ #
      # save fact data in persistent DB using IR

      newFact                   = Fact.Fact( fid, factData, cursor )
      newFact.dataListWithTypes = dataListWithTypes

      logging.debug( "  GET DOM FACTS : adding fact:\n     " + \
                     dumpers.reconstructFact( newFact.fid, newFact.cursor ) )

      newFacts.append( newFact )

  #if not_name == "not_node_from_not_log_from_missing_log" :
  #if not_name == "not_log_from_missing_log" :
  #  sys.exit( "blah" )

  return newFacts


########################
#  GET ALL DATA LISTS  #
########################
# based on https://stackoverflow.com/a/798893
def get_all_data_lists( a_data_list ) :
  return list( itertools.product( *a_data_list ) )


#####################
#  GET ALL STRINGS  #
#####################
def get_all_strings( factMeta ) :

  all_strings = []

  for f in factMeta :
    for data_info in f.dataListWithTypes :
      if data_info[ 1 ] == "string" :
        a_string = data_info[ 0 ] 
        #a_string = a_string.replace( "'", "" )
        #a_string = a_string.replace( '"', "" )
        all_strings.append( a_string )

  return list( set( all_strings ) )


##################
#  GET ALL INTS  #
##################
def get_all_ints( factMeta, cursor ) :

  all_ints = []

  # grab all ints from the program
  for f in factMeta :
    for data_info in f.dataListWithTypes :
      if data_info[ 1 ] == "int" :
        all_ints.append( int( data_info[ 0 ] ) )

  # grab all ints from the clock
  cursor.execute( "SELECT sndTime FROM Clock" )
  clock_ints = cursor.fetchall()
  clock_ints = [ x[0] for x in clock_ints ]
  all_ints.extend( clock_ints )

  cursor.execute( "SELECT delivTime FROM Clock" )
  clock_ints = cursor.fetchall()
  clock_ints = [ x[0] for x in clock_ints ]
  all_ints.extend( clock_ints )

  return list( set( all_ints ) )


#######################
#  GET GOAL ATT TYPE  #
#######################
def get_goal_att_type( index, orig_rid, ruleMeta ) :
  for r in ruleMeta :
    if r.rid == orig_rid :
      return r.goal_att_type_list[ index ][ 1 ]
  raise Exception( "  GET GOAL ATT TYPE : no orig_rid '" + \
                   str( orig_rid ) + "' in ruleMeta." )


###############################
#  GET GOAL ATT TO INDEX MAP  #
###############################
# looses duplicate attributes.
# should be fine, though, since only the types are interesting.
def get_goal_att_to_index_map( parent_rid, ruleMeta ) :
  att_to_index_map = {}
  att_list         = []
  for r in ruleMeta :
    if r.rid == parent_rid :
      goalAttList = r.ruleData[ "goalAttList" ]
      for i in range( 0, len( goalAttList ) ) :
        att = goalAttList[ i ]
        att_to_index_map[ att ] = i
        att_list.append( att )
  return att_to_index_map, att_list


##############################
#  GET NEGATED SUBGOAL ATTS  #
##############################
# gather the lists of subgoal attributes per occurence of the 
# negated IDB for this rule.
def get_negated_subgoal_atts( orig_name, parent_rid, ruleMeta ) :

  negated_subgoal_atts = []

  for r in ruleMeta :
    if r.rid == parent_rid :
      for sub in r.ruleData[ 'subgoalListOfDicts' ] :
        if sub[ "subgoalName" ] == orig_name and sub[ "polarity" ] == "notin" :
          negated_subgoal_atts.append( sub[ "subgoalAttList" ] )

  return negated_subgoal_atts


#########################
#  GET CURRENT RESULTS  #
#########################
# collect the results from the current version of the program
# need to do this before building out the new not_ rules for this set.
def get_current_results( argDict, cursor ) :
  original_prog = c4_translator.c4datalog( argDict, cursor )
  results_array = c4_evaluator.runC4_wrapper( original_prog, argDict )
  parsedResults = tools.getEvalResults_dict_c4( results_array )
  return parsedResults


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


################
##  BUILD UNI  #
################
#def build_uni( not_name, \
#               goalAttList ) :
#
#  dom_sub = {}
#  dom_sub[ "subgoalName" ]    = "unidom_" + not_name
#  dom_sub[ "subgoalAttList" ] = goalAttList
#  dom_sub[ "polarity" ]       = ""
#  dom_sub[ "subgoalTimeArg" ] = ""
#
#  return dom_sub
#
################
##  BUILD EXI  #
################
#def build_exi( orig_name, \
#               not_name, \
#               goalAttList, \
#               ruleMeta ) :
#
#  # gather all existential atts across all rules
#  # defining orig_name.
#  # it would be more efficient to do this only once 
#  # and outside of the parent loop.
#  all_exi_atts = []
#  for rule in ruleMeta :
#    if rule.relationName == orig_name :
#      for sub in rule.subgoalListOfDicts :
#        for satt in sub[ "subgoalAttList" ] :
#          if not satt in goalAttList and \
#             not satt in all_exi_atts :
#            all_exi_atts.append( satt )
#
#  dom_sub = {}
#  dom_sub[ "subgoalName" ]    = "exidom_" + not_name
#  dom_sub[ "subgoalAttList" ] = all_exi_atts
#  dom_sub[ "polarity" ]       = ""
#  dom_sub[ "subgoalTimeArg" ] = ""
#
#  return dom_sub

####################
#  DNF TO DATALOG  #
####################
# use the positive fmla to generate a new set of
# formulas for the not_ rules
def dnfToDatalog( orig_name, \
                  not_name, \
                  goalAttList, \
                  goalTimeArg, \
                  final_fmla, \
                  ruleSet, \
                  ruleMeta, \
                  parent_name, \
                  parent_rid, \
                  rid_to_rule_meta_map, \
                  cursor, \
                  argDict ) :

  settings_path    = argDict[ "settings" ]

  logging.debug( "  DNF TO DATALOG : running process..." )
  logging.debug( "  DNF TO DATALOG : not_name    = " + not_name )
  logging.debug( "  DNF TO DATALOG : goalAttList = " + str( goalAttList ) )
  logging.debug( "  DNF TO DATALOG : goalTimeArg = " + goalTimeArg )
  logging.debug( "  DNF TO DATALOG : final_fmla  = " + final_fmla )

  # get goal types
  goal_types = ruleSet[ 0 ].goal_att_type_list # just pick any rule in the set.

  logging.debug( "  DNF TO DATALOG : ruleSet :" )
  for r in ruleSet :
    logging.debug( "    " + str( dumpers.reconstructRule( r.rid, r.cursor ) ) )

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
      subgoalDict = {}
      sub         = rule.subgoalListOfDicts[ subgoalIndex ]
      for key in sub :
        subgoalDict[ key ] = sub[ key ]

      # ----------------------------------------- #
      # if not_ rule contains a negated recusrion
      # instance, replace with the positive head.

      #if subgoalDict[ "subgoalName" ] == orig_name :
      if False :
        subgoalDict[ "subgoalName" ] = not_name
        subgoalDict[ "polarity" ]    = ""

      else :

        # ----------------------------------------- #
        # set polarity
  
        subgoalDict[ "polarity" ] = polarity

      # ----------------------------------------- #
      # save to subgoal list of dicts

      logging.debug( "  DNF TO DATALOG : adding subgoalDict to rule '" + \
                     not_name + "' : " + str( subgoalDict ) )

      subgoalListOfDicts.append( subgoalDict )

    # ----------------------------------------- #
    # add domain subgoals, if applicable

    unidom_rules = []
    exidom_rules = []
    for r in ruleMeta :
      if r.relationName.endswith( not_name ) and \
         r.relationName.startswith( "unidom_" ) :
        unidom_rules.append( r )
      elif is_an_exidom( not_name, r, orig_name, ruleMeta ) :
        exidom_rules.append( r )

    try :
      assert( len( unidom_rules ) == 1 )
    except AssertionError :
      raise AssertionError( "no unidom_ rule. all DM rules have a unidom_. aborting..." )

    unidom_sub = {}
    unidom_sub[ "subgoalName" ]    = unidom_rules[0].relationName
    unidom_sub[ "subgoalTimeArg" ] = ""
    unidom_sub[ "polarity" ]       = ""
    unidom_sub[ "subgoalAttList" ] = goalAttList
    subgoalListOfDicts.append( unidom_sub )

    if len( exidom_rules ) > 0 :
      for esub in exidom_rules :
        exidom_sub = {}
        exidom_sub[ "subgoalName" ]    = esub.relationName
        exidom_sub[ "subgoalTimeArg" ] = ""
        exidom_sub[ "polarity" ]       = ""
        exidom_sub[ "subgoalAttList" ] = esub.goalAttList
        if not exidom_sub in subgoalListOfDicts :
          subgoalListOfDicts.append( exidom_sub )

    # ----------------------------------------- #
    # build ruleData for new rule and save

    ruleData = {}
    ruleData[ "relationName" ]       = not_name
    ruleData[ "goalAttList" ]        = goalAttList
    ruleData[ "goalTimeArg" ]        = goalTimeArg
    ruleData[ "subgoalListOfDicts" ] = subgoalListOfDicts
    ruleData[ "eqnDict" ]            = eqnDict_combined

    # ----------------------------------------- #
    # add negation of original version 
    # for good measure.
    # need for some reason? whatevs.

    orig_neg = {}
    orig_neg[ "subgoalName" ]    = "orig_" + orig_name
    orig_neg[ "subgoalTimeArg" ] = ""
    orig_neg[ "polarity" ]       = "notin"
    orig_neg[ "subgoalAttList" ] = ruleData[ "goalAttList" ]
    ruleData[ "subgoalListOfDicts" ].append( orig_neg )

    # ----------------------------------------- #
    # save rule

    rid            = tools.getIDFromCounters( "rid" )
    newRule        = copy.deepcopy( Rule.Rule( rid, ruleData, cursor) )
    newRule.cursor = cursor # need to do this for some reason or else cursor disappears?
    newRule.goal_att_type_list = goal_types

    # maintain a list of not_ rules previously derived in the
    # lineage of this rule.
    parent_rule = rid_to_rule_meta_map[ parent_rid ]
    newRule.lineage_not_names = parent_rule.lineage_not_names
    if parent_name.startswith( "not_" ) :
      newRule.lineage_not_names.append( parent_name )

    newRule.manually_set_types()
    newDMRules.append( newRule )

#    if len( newRule.lineage_not_names ) > 0 :
#      print newRule.lineage_not_names
#      print dumpers.reconstructRule( parent_rid, cursor )
#      print dumpers.reconstructRule( newRule.rid, newRule.cursor )
#      sys.exit( "blah" )

  logging.debug( "  DNF TO DATALOG : newDMRules :" )
  for newRule in newDMRules :
    logging.debug( "    " + str( dumpers.reconstructRule( newRule.rid, newRule.cursor )) )
  #sys.exit( "blahaha" )

  return newDMRules


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

        logging.debug( "  RESOLVE DOUBLE NEGATIONS : hit a double neg for rule:" )
        logging.debug( "     " + dumpers.reconstructRule( rule.rid, rule.cursor ) )
        logging.debug( "  RESOLVE DOUBLE NEGATIONS : original subgoal = " + str( subgoal ) )

        # based on https://stackoverflow.com/a/14496084
        double_neg_sub_name = subgoal[ "subgoalName" ]
        double_neg_sub_name = double_neg_sub_name[ 4 : ] # remove the first not
        last_f              = double_neg_sub_name.rfind( "_f" )
        orig_sub_name       = double_neg_sub_name[ : last_f ]

        logging.debug( "  RESOLVE DOUBLE NEGATIONS : double_neg_sub_name = " + str( double_neg_sub_name ) )
        logging.debug( "  RESOLVE DOUBLE NEGATIONS : orig_sub_name       = " + str( orig_sub_name ) )

        new_sub_dict = {}
        new_sub_dict[ "subgoalName" ]    = orig_sub_name
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

    logging.debug( "  RESOLVE DOUBLE NEGATIONS : new rule :" )
    logging.debug( "     " + dumpers.reconstructRule( rule.rid, rule.cursor ) )

  return ruleMeta


###############################
#  REPLACE SUBGOAL NEGATIONS  #
###############################
# rewrite existing rules to replace 
# instances of negated subgoal instances 
# with derived not_rules
def replaceSubgoalNegations( orig_name, \
                             not_name, \
                             parent_rid, \
                             ruleMeta ) :


  logging.debug( "  REPLACE SUBGOAL NEGATIONS : running process..." )
  logging.debug( "  REPLACE SUBGOAL NEGATIONS : orig_name = " + orig_name )
  logging.debug( "  REPLACE SUBGOAL NEGATIONS : not_name  = " + not_name )
  logging.debug( "  REPLACE SUBGOAL NEGATIONS : parent rule :" )
  logging.debug( "          " + dumpers.reconstructRule( parent_rid, ruleMeta[0].cursor ) )

  for rule in ruleMeta :

    # 1. make replacement in the parent.
    if rule.rid == parent_rid :

      # ----------------------------------------- #
      # get subgoal info

      for i in range( 0, len( rule.subgoalListOfDicts ) ) :
        sub = rule.subgoalListOfDicts[ i ]

        # ----------------------------------------- #
        # replace negatives

        if sub[ "subgoalName" ] == orig_name and \
           sub[ "polarity" ] == "notin" :

          rule.subgoalListOfDicts[ i ][ "subgoalName" ] = not_name
          rule.subgoalListOfDicts[ i ][ "polarity" ]    = ""

      # ----------------------------------------- #
      # save new subgoal list

      rule.saveSubgoals()

    ## 2. make replacements in this set of not rules
    #else :
    #  if rule.relationName == not_name :

#   #     print "replace subgoals"
#   #     print rule.relationName
#   #     print rule.lineage_not_names
#   #     print dumpers.reconstructRule( rule.rid, rule.cursor )

    #    for i in range( 0, len( rule.subgoalListOfDicts ) ) :
    #      sub = rule.subgoalListOfDicts[ i ]
    #      if sub[ "polarity" ] == "notin" :
    #        print "checking subgoal : " + str( sub )
    #        for lineage_not_name in rule.lineage_not_names :
    #          if lineage_not_name.startswith( "not_" + sub[ "subgoalName" ] ) :
    #            print "here"
    #            rule.subgoalListOfDicts[ i ][ "subgoalName" ] = lineage_not_name
    #            rule.subgoalListOfDicts[ i ][ "polarity" ]    = ""

    #  rule.saveSubgoals()

#      if rule.relationName == "not_log_f24" :
#        print dumpers.reconstructRule( rule.rid, rule.cursor )
#        sys.exit( "blee" )


  return ruleMeta


########################
#  IDB ALREADY EXISTS  #
########################
def idb_already_exists( rel_name, cursor ) :

  logging.debug( "  IDB ALREADY EXISTS : rel_name = " + rel_name )

  cursor.execute( "SELECT rid FROM Rule WHERE goalName=='" + rel_name + "'" )
  res = cursor.fetchall()
  if len( res ) > 0 :
    return True
  else :
    return False


####################################
#  EQUIVALENT RULE ALREADY EXISTS  #
####################################
def equivalent_rule_already_exists( orig_parent_rule, ruleMeta ) :
  logging.debug( "  EQUIVALENT RULE ALREADY EXISTS : checking:\n     " + \
                 dumpers.reconstructRule( orig_parent_rule.rid, orig_parent_rule.cursor ) )
  for rule in ruleMeta :
    logging.debug( "  EQUIVALENT RULE ALREADY EXISTS : against:\n     " + \
                   dumpers.reconstructRule( rule.rid, rule.cursor ) )
    if rule.relationName == orig_parent_rule.relationName and \
      equivalent_subgoals( orig_parent_rule.relationName, \
                           rule.subgoalListOfDicts, \
                           orig_parent_rule.subgoalListOfDicts ) :
      logging.debug( "  EQUIVALENT RULE ALREADY EXISTS : returning True." )
      return True
    logging.debug( "  EQUIVALENT RULE ALREADY EXISTS : not a match." )

  logging.debug( "  EQUIVALENT RULE ALREADY EXISTS : returning False." )
  return False


#########################
#  EQUIVALENT SUBGOALS  #
#########################
def equivalent_subgoals( orig_parent_rel_name, subList1, subList2 ) :

  if not len( subList1 ) == len( subList2 ) :
    logging.debug( "  EQUIVALENT SUBGOALS : returning False b/c diff number of subgoals." )
    return False

  equiv_tracker = [ False for i in range( 0, len( subList1 ) ) ]
  for i in range( 0, len( subList1 ) ) :
    sub1 = subList1[ i ]
    sub2 = subList2[ i ]

    logging.debug( "  EQUIVALENT SUBGOALS : comparing '" + sub1[ "subgoalName" ] + \
                   "' and '" + sub2[ "subgoalName" ] + "'" )

    if sub1[ "subgoalName" ] == sub2[ "subgoalName" ] and \
       sub1[ "polarity" ]    == sub2[ "polarity" ] :

      equiv_tracker[ i ] = True # found an equivalent in subList2
      logging.debug( "  EQUIVALENT SUBGOALS : yes match." )

    else :

      #last_from        = orig_parent_rel_name.rfind( "_from_" )
      #orig_parent_from = orig_parent_rel_name[ last_from : ]

      #   "not_" + sub1[ "subgoalName" ] + orig_parent_from == sub2[ "subgoalName" ] :
      if sub1[ "polarity" ] == "notin" and \
        sub2[ "subgoalName" ].startswith( "not_" + sub1[ "subgoalName" ] ) :
        equiv_tracker[ i ] = True # found an equivalent in subList2
        logging.debug( "  EQUIVALENT SUBGOALS : yes match." )

      #     "not_" + sub2[ "subgoalName" ] + orig_parent_from == sub1[ "subgoalName" ] :
      elif sub2[ "polarity" ] == "notin" and \
           sub1[ "subgoalName" ].startswith( "not_" + sub2[ "subgoalName" ] ) :
        equiv_tracker[ i ] = True # found an equivalent in subList2
        logging.debug( "  EQUIVALENT SUBGOALS : yes match." )

      else :
        logging.debug( "  EQUIVALENT SUBGOALS : not match." )

  print equiv_tracker
  if equiv_tracker.count( True ) < len( subList1 ) :
    logging.debug( "  EQUIVALENT SUBGOALS : returning False." )
    return False
  else :
    logging.debug( "  EQUIVALENT SUBGOALS : returning True." )
    return True


##################
#  IS AN EXIDOM  #
##################
def is_an_exidom( not_name, r, orig_name, ruleMeta ) :
  if r.relationName.startswith( "exidom_" ) and \
     not_name + "_f" in r.relationName :
     return True
  return False


#########
#  EOF  #
#########
