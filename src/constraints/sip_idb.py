#/usr/bin/env python

'''
sip.py
'''

import ConfigParser, copy, itertools, logging, os, sys

if not os.path.abspath( __file__ + "/../.." ) in sys.path :
  sys.path.append( os.path.abspath( __file__ + "/../.." ) )
if not os.path.abspath( __file__ + "/../../dedt/translators" ) in sys.path :
  sys.path.append( os.path.abspath( __file__ + "/../../dedt/translators" ) )
from translators import c4_translator, dumpers_c4
from dedt        import Fact, Rule
from evaluators  import c4_evaluator
from utils       import dumpers, tools, nw_tools


##################
#  ADD DOM SUBS  #
##################
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
def add_dom_subs( not_template_ruleMeta, ruleMeta, cursor ) :

  dom_subs = []

  for key in not_template_ruleMeta :

    orig_ruleMeta_list = get_orig_ruleMeta_list( key, ruleMeta )
    if len( orig_ruleMeta_list ) < 1 :
      print "skipping dom rules for " + key
      continue

    for a_not_rule in not_template_ruleMeta[ key ] :

      # only add subgoals to a rule once.
      if "unidom_" + a_not_rule.relationName in \
         [ sub[ "subgoalName" ] for sub in a_not_rule.subgoalListOfDicts ] :
        continue

      # build unidom_
      unidom = {}
      unidom[ "subgoalName" ]    = "unidom_" + a_not_rule.relationName
      unidom[ "subgoalAttList" ] = a_not_rule.goalAttList #this only works b/c uniformit rewrites
      unidom[ "subgoalTimeArg" ] = ""
      unidom[ "polarity" ]       = ""
  
      # add unidom_
      for ntr in not_template_ruleMeta[ key ] :
        ntr.ruleData[ "subgoalListOfDicts" ].append( unidom )
        logging.debug( "  ADD DOM SUBS : adding sub '" + str( unidom ) + "'" )
        ntr.saveSubgoals()

      # build exidom_
      # and exidom_ rules
      lists_of_exi_vars = []
      exidom_rules      = []
      for rule in orig_ruleMeta_list :
        exi_vars = []
        for sub in rule.subgoalListOfDicts :
          for var in sub[ "subgoalAttList" ] :
            if not var in rule.goalAttList and \
               not var in exi_vars         and \
               not var == "_"              and \
               not "'" in var              and \
               not '"' in var              and \
               not var.isdigit() :
              exi_vars.append( var )

        if len( exi_vars ) > 0 :
          lists_of_exi_vars.append( [ exi_vars, rule.rid ] )
          exidom_ruleData = {}
          exidom_ruleData[ "relationName" ]       = "exidom_" + \
                                                    a_not_rule.relationName + \
                                                    "_f" + str( rule.rid )
          exidom_ruleData[ "goalTimeArg" ]        = ""   
          exidom_ruleData[ "goalAttList" ]        = exi_vars
          exidom_ruleData[ "eqnDict" ]            = {}
          exidom_ruleData[ "subgoalListOfDicts" ] = []

          for sub in rule.subgoalListOfDicts :
            new_sub = copy.deepcopy( sub )
            for i in range( 0, len( sub[ "subgoalAttList"] ) ) :
              var = sub[ "subgoalAttList"][i]
              if not var in exi_vars :
                new_sub[ "subgoalAttList"][ i ] = "_"
              else :
                new_sub[ "subgoalAttList"][ i ] = var
            exidom_ruleData[ "subgoalListOfDicts" ].append( new_sub )

          # do save
          exi_rid         = tools.getIDFromCounters( "rid" )
          exi_rule        = copy.deepcopy( Rule.Rule( exi_rid, exidom_ruleData, cursor) )
          exi_rule.cursor = cursor # need to do this for some reason or else cursor disappears?
        
          # set the unidom rule types manually
          exi_goal_types = rule.goal_att_type_list
          assert( len( exi_goal_types ) > 0 )
        
          exi_rule.goal_att_type_list = exi_goal_types
          exi_rule.manually_set_types()
        
          # check if a rule already exists
          # to prevent duplicates.
          if not nw_tools.identical_rule_already_exists( exi_rule, ruleMeta ) :
            ruleMeta.append( exi_rule )
  
      exidom_subgoals = []
      for ev_list_info in lists_of_exi_vars :
        ev_list = ev_list_info[0]
        rid     = ev_list_info[1]
        exidom = {}
        exidom[ "subgoalName" ]    = "exidom_" + a_not_rule.relationName + "_f"  + str( rid )
        exidom[ "subgoalTimeArg" ] = ""   
        exidom[ "polarity" ]       = ""
        exidom[ "subgoalAttList" ] = ev_list
        exidom_subgoals.append( exidom )
  
      # add exidoms_, if applicable
      if len( exidom_subgoals ) > 0 :
        for ntr in not_template_ruleMeta[ key ] :
          flag = False
          for esub in exidom_subgoals :
            if is_applicable( esub, ntr ) :
              ntr.ruleData[ "subgoalListOfDicts" ].append( esub )
              logging.debug( "  ADD DOM SUBS : adding sub '" + str( sub ) + "'" )
              flag = True
          if flag :
            ntr.saveSubgoals()

    #if key == "log" :
    #  for i in orig_ruleMeta_list :
    #    print dumpers.reconstructRule( i.rid, i.cursor )
    #  for i in not_template_ruleMeta[ key ] :
    #    print dumpers.reconstructRule( i.rid, i.cursor )
    #  sys.exit( "blah" )

  return not_template_ruleMeta, exidom_rules


#############################
#  GET ORIG RULE META LIST  #
#############################
def get_orig_ruleMeta_list( rel_name, ruleMeta ) :
  orig_ruleMeta_list = []
  for rule in ruleMeta :
    if rule.relationName == rel_name :
      orig_ruleMeta_list.append( rule )
  return orig_ruleMeta_list


###################
#  IS APPLICABLE  #
###################
# check if the exidom_ (esub) is needed to constrain the existential
# domains for the given rule.
def is_applicable( esub, rule ) :
  for sub in rule.subgoalListOfDicts :
    for var in sub[ "subgoalAttList" ] :
      if var in esub[ "subgoalAttList" ] :
        return True
  return False

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
    if nw_tools.is_idb( uni_subgoalListOfDicts[ i ][ "subgoalName" ], ruleMeta ) and \
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
  if not nw_tools.identical_rule_already_exists( uni_rule, ruleMeta ) :
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
  # build the existential domain rule

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

    exi_ruleData = {}
  
    # get relation name
    # need the extra _f to maintain arities.
    exi_ruleData[ "relationName" ] = "exidom_" + not_name + "_f" + str( target_rule.rid )
  
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

      #get goal atts
      exi_ruleData[ "goalAttList" ] = copy.deepcopy( all_exi_vars )
  
      # get goal time arg
      exi_ruleData[ "goalTimeArg" ] = ""
    
      # get eqn dict
      exi_ruleData[ "eqnDict" ] = {}
    
      # =================================== #
      # get subgoals
  
      exi_subgoalListOfDicts = copy.deepcopy( target_rule.subgoalListOfDicts )
      for i in range( 0, len( exi_subgoalListOfDicts ) ) :
        sub = exi_subgoalListOfDicts[ i ]
        if not sub[ "subgoalName" ].startswith( "orig_" )   and \
           not sub[ "subgoalName" ] == "clock"              and \
           not sub[ "subgoalName" ] == "next_clock"         and \
           not sub[ "subgoalName" ] == "crash"              and \
           not sub[ "subgoalName" ].startswith( "not_" )    and \
           not sub[ "subgoalName" ].startswith( "unidom_" ) and \
           not sub[ "subgoalName" ].startswith( "exidom_" ) and \
           nw_tools.is_idb( sub[ "subgoalName" ], ruleMeta ) :
          exi_subgoalListOfDicts[ i ][ "subgoalName" ] = "orig_" + sub[ "subgoalName" ]
  
      exi_ruleData[ "subgoalListOfDicts" ] = exi_subgoalListOfDicts
  
      # =================================== #
      # save rule
  
      exi_rid         = tools.getIDFromCounters( "rid" )
      exi_rule        = copy.deepcopy( Rule.Rule( exi_rid, exi_ruleData, cursor) )
      exi_rule.cursor = cursor # need to do this for some reason or else cursor disappears?
  
      # set the unidom rule types manually
      exi_goal_types = []
      for gatt in exi_rule.goalAttList :
        for sub in exi_subgoalListOfDicts :
          if gatt in sub[ "subgoalAttList" ] :
            gatt_index = sub[ "subgoalAttList" ].index( gatt )
            for rule in ruleMeta :
              if rule.relationName == sub[ "subgoalName" ] :
                exi_goal_types.append( rule.goal_att_type_list[ gatt_index ] )
      assert( len( uni_goal_types ) > 0 )
    
      exi_rule.goal_att_type_list = exi_goal_types
      exi_rule.manually_set_types()
    
      # check if a rule already exists
      # to prevent duplicates.
      if not nw_tools.identical_rule_already_exists( exi_rule, cursor ) :
        newRules.append( exi_rule )
        logging.debug( "  GET DOM RULES : added exi dom rule :\n     " + \
                       dumpers.reconstructRule( exi_rule.rid, exi_rule.cursor ) ) 
      else :
        logging.debug( "  GET DOM RULES : NOT adding exi dom rule :\n     " + \
                       dumpers.reconstructRule( exi_rule.rid, exi_rule.cursor ) ) 

  logging.debug( "  GET DOM RULES : domain rules:" )
  for rule in newRules :
    logging.debug( "     " + dumpers.reconstructRule( rule.rid, rule.cursor ) )

  #if uni_ruleData[ "relationName" ] == "unidom_not_node_f23" :
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

    # 2. make replacements in this set of not rules
    else :
      if rule.relationName == not_name :

#        print "replace subgoals"
#        print rule.relationName
#        print rule.lineage_not_names
#        print dumpers.reconstructRule( rule.rid, rule.cursor )

        for i in range( 0, len( rule.subgoalListOfDicts ) ) :
          sub = rule.subgoalListOfDicts[ i ]
          if sub[ "polarity" ] == "notin" :
            print "checking subgoal : " + str( sub )
            for lineage_not_name in rule.lineage_not_names :
              if lineage_not_name.startswith( "not_" + sub[ "subgoalName" ] ) :
                print "here"
                rule.subgoalListOfDicts[ i ][ "subgoalName" ] = lineage_not_name
                rule.subgoalListOfDicts[ i ][ "polarity" ]    = ""

      rule.saveSubgoals()

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
