#/usr/bin/env python

'''
combo.py
   Define the functionality for collecting the provenance of negative subgoals
   using the DeMorgan's Law method for negative rewrites..
'''

import copy, inspect, logging, os, string, sys
import sympy
import itertools
import ConfigParser

# ------------------------------------------------------ #
# import sibling packages HERE!!!
if not os.path.abspath( __file__ + "/../.." ) in sys.path :
  sys.path.append( os.path.abspath( __file__ + "/../.." ) )

if not os.path.abspath( __file__ + "/../../dedt/translators" ) in sys.path :
  sys.path.append( os.path.abspath( __file__ + "/../../dedt/translators" ) )

from dedt        import Fact, Rule
from evaluators  import c4_evaluator
from utils       import clockTools, tools, dumpers, setTypes, nw_tools
from dm          import dm_time_att_replacement
from constraints import sip_idb

# ------------------------------------------------------ #

#############
#  GLOBALS  #
#############

arithOps   = [ "+", "-", "*", "/" ]
arithFuncs = [ "count", "avg", "min", "max", "sum" ]


###########
#  COMBO  #
###########
# generate the new set of rules provided by the COMBO method for negative rewrites.
# factMeta := a list of Fact objects
# ruleMeta := a list of Rule objects
def combo( factMeta, ruleMeta, cursor, argDict ) :

  # ----------------------------------------- #

  logging.debug( "  COMBO : running process..." )

  settings_path = argDict[ "settings" ]

  # ----------------------------------------- #
  # get parameters

  # ========== NW DOM DEF ========== #
  try :
    NW_DOM_DEF = tools.getConfig( settings_path, "DEFAULT", "NW_DOM_DEF", str )
    if NW_DOM_DEF == "sip_idb" :
      pass
    else :
      raise ValueError( "unrecognized NW_DOM_DEF option '" + NW_DOM_DEF + \
                        "' for combo NW rewrites. aborting..." )
  except ConfigParser.NoOptionError :
    raise ValueError( "no 'NW_DOM_DEF' defined in 'DEFAULT' section of " + settings_path + \
                      ". aborting..." )

  # ----------------------------------------- #
  # replace unused variables with wildcards

  if NW_DOM_DEF == "sip_idb" :
    ruleMeta = nw_tools.replace_unused_vars( ruleMeta, cursor )

  # ----------------------------------------- #
  # rewrite rules with fixed data 
  # in the head

  ruleMeta, factMeta = nw_tools.fixed_data_head_rewrites( ruleMeta, factMeta, argDict )

  # ----------------------------------------- #
  # rewrite rules with aggregate functions
  # in the head

  ruleMeta = nw_tools.aggRewrites( ruleMeta, argDict )

  # ----------------------------------------- #
  # enforce a uniform goal attribute lists

  ruleMeta = nw_tools.setUniformAttList( ruleMeta, cursor )

  logging.debug( "  COMBO : len( ruleMeta ) after setUniformAttList = " + str( len( ruleMeta ) ) )

  # ----------------------------------------- #
  # enforce unique existential attributes
  # per rule
   
  ruleMeta = nw_tools.setUniqueExistentialVars( ruleMeta )

  # ----------------------------------------- #
  # replace time att references

  ruleMeta = dm_time_att_replacement.dm_time_att_replacement( ruleMeta, cursor, argDict )

  # ----------------------------------------- #
  # append rids to all rel names and
  # generate cps of the original rules
  # (do not reference these in final programs)

  if NW_DOM_DEF == "sip_idb" :

    # future optimization : do this lazily:
    ruleMeta.extend( nw_tools.generate_orig_cps( ruleMeta ) )

  # ----------------------------------------- #
  # append rids to all rel names and
  # generate cps of the original rules
  # (do not reference these in final programs)

  if NW_DOM_DEF == "sip_idb" :

    # future optimization : do this lazily:
    ruleMeta = get_not_template_ruleMeta( ruleMeta )
    #for r in ruleMeta :
    #  print str( r.rid ) + " : " + dumpers.reconstructRule( r.rid, r.cursor )
    #sys.exit( "blee" )

  # ----------------------------------------- #
  # generate a map of all rids to corresponding
  # rule meta object pointers.

  if NW_DOM_DEF == "sip_idb" :
    rid_to_rule_meta_map = nw_tools.generate_rid_to_rule_meta_map( ruleMeta )

  # ----------------------------------------- #
  # build all de morgan's rules

  COUNTER = 0
  while nw_tools.stillContainsNegatedIDBs( ruleMeta, cursor ) :

    logging.debug( "  COMBO : COUNTER = " + str( COUNTER ) )
    if COUNTER == 3 :
      for r in ruleMeta :
        print dumpers.reconstructRule( r.rid, r.cursor )
      sys.exit( "wtf?" )

    # ----------------------------------------- #
    # check if any rules include negated idb
    # subgoals

    targetRuleMetaSets = nw_tools.getRuleMetaSetsForRulesCorrespondingToNegatedSubgoals( ruleMeta, cursor )

    # ----------------------------------------- #
    # break execution if no rules contain negated IDBs.
    # should not hit this b/c of loop condition.

    if len( targetRuleMetaSets ) < 1 :
      return []

    # ----------------------------------------- #
    # create the de morgan rewrite rules.
    # incorporates domcomp and existential 
    # domain subgoals.

    if NW_DOM_DEF == "sip_idb" :
      ruleMeta = do_combo_sip_idb( ruleMeta, \
                                   targetRuleMetaSets, \
                                   rid_to_rule_meta_map, \
                                   cursor, \
                                   argDict )
    else :
      raise ValueError( "unrecognized NW_DOM_DEF option '" + NW_DOM_DEF + \
                        "'. aborting..." )

    # ----------------------------------------- #
    # update rid to rule meta map

    rid_to_rule_meta_map = nw_tools.generate_rid_to_rule_meta_map( ruleMeta )

    # increment loop counter
    COUNTER += 1

  # ----------------------------------------- #
  # replace unused variables with wildcards

  if NW_DOM_DEF == "sip_idb" :
    ruleMeta = nw_tools.replace_unused_vars( ruleMeta, cursor )

  # ----------------------------------------- #
  # filter out unused not_ rules

  if NW_DOM_DEF == "sip_idb" :
    ruleMeta = nw_tools.delete_unused_not_rules( ruleMeta, cursor )

  for r in ruleMeta :
    print str( r.rid ) + " : " + dumpers.reconstructRule( r.rid, r.cursor )
  #sys.exit( "blahasdf" )

  logging.debug( "  COMBO : ...done." )
  return factMeta, ruleMeta


######################
#  GET NOT TEMPLATE  #
######################
# return a dict mapping positive relation names to 
# lists of not_ rules derived from the target NW rewrite
# process. The not_ rules act as templates and do not
# include domain subgoals.
def get_not_template_ruleMeta( ruleMeta ) :

  cursor = ruleMeta[0].cursor # all this stuff happens on the same db.

  not_template_ruleMeta = {}

  for rule in ruleMeta :

    orig_polarity_pattern = ""
    for sub in rule.subgoalListOfDicts :
      if sub[ "polarity" ] == "" :
        orig_polarity_pattern += "1" 
      else :
        orig_polarity_pattern += "0" 

    if rule.relationName.startswith( "orig_" ) :
      continue

    # instantiate relation name, if applicable.
    if not rule.relationName  in not_template_ruleMeta :
      not_template_ruleMeta[ rule.relationName ] = []

    # build the appropriate not_rules
    # combo builds not_ rules per rule,
    # so no grouping needed.

    pattern_map = nw_tools.getPatternMap( len( rule.subgoalListOfDicts ) )

    for pattern in pattern_map :

      # not_ rules never look like the original rule.
      if pattern == orig_polarity_pattern :
        continue

      # also, never add a rule with only negative subgoals
      # if the original rule is recursive.
      # it would only fire for data outside of the domain.
      # therefore, the correct firing rules should be the 
      # ground rules defined elsewhere in the program.
      elif is_recursive( rule ) and \
           not "1" in pattern :
        continue

      not_ruleData = {}
      not_ruleData[ "relationName" ]       = "not_" + rule.relationName
      not_ruleData[ "goalAttList" ]        = rule.goalAttList
      not_ruleData[ "goalTimeArg" ]        = rule.goalTimeArg
      not_ruleData[ "subgoalListOfDicts" ] = []
      not_ruleData[ "eqnDict" ]            = rule.eqnDict

      # flip polarities
      for i in range( 0, len( pattern ) ) :
        sub = copy.deepcopy( rule.subgoalListOfDicts[ i ]  )
        if pattern[ i ] == "1" :
          sub[ "polarity" ] = ""
        else :
          sub[ "polarity" ] = "notin"
        not_ruleData[ "subgoalListOfDicts" ].append( copy.deepcopy( sub ) )

      # replace recursion references
      for sub in not_ruleData[ "subgoalListOfDicts" ] :
        if sub[ "polarity" ] == "notin" and \
           sub[ "subgoalName" ] == rule.relationName :
          sub[ "polarity" ]    = ""
          sub[ "subgoalName" ] = not_ruleData[ "relationName" ]

      rid                         = tools.getIDFromCounters( "rid" )
      not_rule                    = copy.deepcopy( Rule.Rule( rid, not_ruleData, cursor ) )
      not_rule.cursor             = cursor
      not_rule.goal_att_type_list = rule.goal_att_type_list
      not_rule.manually_set_types()
      not_template_ruleMeta[ rule.relationName ].append( not_rule )

  # add unidom and exidom subgoals
  not_template_ruleMeta, exidom_rules = sip_idb.add_dom_subs( not_template_ruleMeta, ruleMeta, cursor )
  #for key in not_template_ruleMeta :
  #  for r in not_template_ruleMeta[ key ] :
  #    print str( r.rid ) + " : " + dumpers.reconstructRule( r.rid, r.cursor )
  #sys.exit( "blah" )

  # update ruleMeta
  for key in not_template_ruleMeta :
    for rule in not_template_ruleMeta[ key ] :
      ruleMeta.append( rule )

  #for r in ruleMeta :
  #  print str( r.rid ) + " : " + dumpers.reconstructRule( r.rid, r.cursor )
  #sys.exit( "blah" )

  return ruleMeta

######################
#  DO COMBO SIP IDB  #
######################
# this fails for parent rules multiple negated subgoals sharing the same
# name but parameterized with different sets of subgoal attributes.
# the sip from parent to negated subgoal rule set would be
# valid for only one of the two negated instances.
def do_combo_sip_idb( ruleMeta, \
                      targetRuleMetaSets, \
                      rid_to_rule_meta_map, \
                      cursor, \
                      argDict ) :

  logging.debug( "  DO COMBO SIP IDB : running process..." )

  COUNTER = 0
  for rule_info in targetRuleMetaSets :

    logging.debug( "  DO COMBO SIP IDB : >COUNTER  = " + str( COUNTER ) )

    parent_list = rule_info[ 0 ]
    ruleSet     = rule_info[ 1 ]

    logging.debug( "//////////////////////////////////////////////////" )
    logging.debug( "  DO COMBO SIP IDB : parent_list: " + str( parent_list ) )
    logging.debug( "  DO COMBO SIP IDB : ruleSet:" )
    for rule in ruleSet :
      logging.debug( "    " + dumpers.reconstructRule( rule.rid, rule.cursor ) )
    logging.debug( "//////////////////////////////////////////////////" )

    # Augment the unidom rules for this relation using the parent information.
    for curr_parent in parent_list :

      parent_name = curr_parent[0]
      parent_rid  = curr_parent[1]
      parent_rule = rid_to_rule_meta_map[ parent_rid ]

      # don't build unidom references for recursive rules.
      if parent_name == "not_" + ruleSet[0].relationName :
        pass
      elif parent_name == "not_post" :
        pass
      else :

        # 2. build the unidom definition using parent data
        unidom_ruleData = {}
        unidom_ruleData[ "relationName" ]       = "unidom_not_" + ruleSet[0].relationName
        unidom_ruleData[ "goalAttList" ]        = [ "Att" + str( i ) for i in range( 0, len( ruleSet[0].goalAttList ) ) ]
        unidom_ruleData[ "goalTimeArg" ]        = ""
        unidom_ruleData[ "eqnDict" ]            = {}

        # map new goal atts to existing body atts in the parent rule
        # this breaks if the same patt appears more than once in the
        # same subgoal!!!
        patt_to_gatt  = {}
        for i in range( 0, len( parent_rule.subgoalListOfDicts ) ) :
          sub = parent_rule.subgoalListOfDicts[ i ]
          print sub
          if sub[ "subgoalName" ] == ruleSet[0].relationName :
            for j in range( 0, len( sub[ "subgoalAttList" ] ) ) :
              print sub[ "subgoalAttList" ][ j ]
              if not sub[ "subgoalAttList" ][ j ] == "_" :
                patt_to_gatt[ sub[ "subgoalAttList" ][ j ] ] = "Att" + str( j )

        # replace fixed data in head
        gatt_to_patt = { v : k for k, v in patt_to_gatt.iteritems() }
        for i in range( 0, len( unidom_ruleData[ "goalAttList" ] ) ) :
          gatt = unidom_ruleData[ "goalAttList" ][ i ]
          try :
            patt = gatt_to_patt[ gatt ]
            if patt.isdigit() or \
               "'" in patt    or \
               '"' in patt :
              unidom_ruleData[ "goalAttList" ][ i ] = patt
          except KeyError :
            pass

        unidom_ruleData[ "subgoalListOfDicts" ] = copy.deepcopy( parent_rule.subgoalListOfDicts )
        for i in range( 0, len( unidom_ruleData[ "subgoalListOfDicts" ] ) ) :
          sub = unidom_ruleData[ "subgoalListOfDicts" ][ i ]

          # make sure subgoals reference orig_ rules
          if nw_tools.isIDB( sub[ "subgoalName" ], cursor )   and \
             not sub[ "subgoalName" ].startswith( "unidom_" ) and \
             not sub[ "subgoalName" ].startswith( "exidom_" ) and \
             not sub[ "subgoalName" ].startswith( "not_" )    and \
             not sub[ "subgoalName" ].startswith( "orig_" ) :
            unidom_ruleData[ "subgoalListOfDicts" ][ i ][ "subgoalName" ] = "orig_" + sub[ "subgoalName" ]
          elif sub[ "subgoalName" ].startswith( "not_" ) :
            unidom_ruleData[ "subgoalListOfDicts" ][ i ][ "subgoalName" ] = sub[ "subgoalName" ][ 4: ]
            unidom_ruleData[ "subgoalListOfDicts" ][ i ][ "polarity" ]    = "notin"

          # replace parent att references with goal atts.
          for j in range( 0, len( sub[ "subgoalAttList" ] ) ) :
            satt = sub[ "subgoalAttList" ][ j ]
            if satt in patt_to_gatt :
              if satt.isdigit() or \
                 "'" in satt    or \
                 '"' in satt :
                pass
              else :
                unidom_ruleData[ "subgoalListOfDicts" ][ i ][ "subgoalAttList" ][ j ] = patt_to_gatt[ satt ]

        # fill out any missing gatts by referencing the original target relation
        missing_gatts = [ gatt for gatt in unidom_ruleData[ "goalAttList" ] if not gatt in patt_to_gatt.values() ]
        if len( missing_gatts ) > 0 :
          orig_target_rel_sub = {}
          orig_target_rel_sub[ "subgoalName" ]    = "orig_" + ruleSet[0].relationName
          orig_target_rel_sub[ "polarity" ]       = ""
          orig_target_rel_sub[ "subgoalTimeArg" ] = ""
          orig_target_rel_sub[ "subgoalAttList" ] = []
          for i in range( 0, len( unidom_ruleData[ "goalAttList" ] ) ) :
            if "Att" + str( i ) in missing_gatts :
              orig_target_rel_sub[ "subgoalAttList" ].append( "Att" + str( i ) )
            else :
              orig_target_rel_sub[ "subgoalAttList" ].append( "_" )
          unidom_ruleData[ "subgoalListOfDicts" ].append( orig_target_rel_sub )
          logging.debug( "  DO COMBO SIP IDB : adding subgoal '" + str( orig_target_rel_sub ) + "'" )

        # do save
        uni_rid         = tools.getIDFromCounters( "rid" )
        uni_rule        = copy.deepcopy( Rule.Rule( uni_rid, unidom_ruleData, cursor ) )
        uni_rule.cursor = cursor # need to do this for some reason or else cursor disappears?

        #if unidom_ruleData[ "relationName" ] == "unidom_not_log" and COUNTER == 17 :
        #  print "fuck"
        #  print COUNTER
        #  print patt_to_gatt
        #  print dumpers.reconstructRule( parent_rid, cursor )
        #  print missing_gatts
        #  print dumpers.reconstructRule( uni_rule.rid, uni_rule.cursor )
        #  sys.exit( "blah" )

        # set the unidom rule types manually
        uni_goal_types = ruleSet[0].goal_att_type_list
        assert( len( uni_goal_types ) > 0 )

        uni_rule.goal_att_type_list = uni_goal_types
        uni_rule.manually_set_types()

        # check if a rule already exists
        # to prevent duplicates.
        if not nw_tools.identical_rule_already_exists( uni_rule, ruleMeta ) :
          ruleMeta.append( uni_rule )

      # make not_ subgoal replacements in parent rules.
      flag = False
      for i in range( 0, len( parent_rule.subgoalListOfDicts ) ) :
        sub = parent_rule.subgoalListOfDicts[ i ]
        if sub[ "subgoalName" ] == ruleSet[0].relationName and \
           sub[ "polarity" ] == "notin" :
          parent_rule.subgoalListOfDicts[ i ][ "subgoalName" ] = "not_" + ruleSet[0].relationName
          parent_rule.subgoalListOfDicts[ i ][ "polarity" ]    = ""
          flag = True
      if flag :
        parent_rule.saveSubgoals()

      COUNTER += 1

  # ----------------------------------------- #
  # order recursive rules last

  ruleMeta = nw_tools.sortDMRules( ruleMeta )

  return ruleMeta


##################
#  IS RECURSIVE  #
##################
# check if the input rule is recursive.
def is_recursive( rule ) :
  for sub in rule.subgoalListOfDicts :
    if sub[ "subgoalName" ] == rule.relationName :
      return True
  return False


#########
#  EOF  #
#########
