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
from constraints import sip_idb

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

  logging.debug( "  DO DEMORGANS SIP IDB : running process..." )

  newDMRules = []

  COUNTER = 0
  for rule_info in targetRuleMetaSets :

    parent_list = rule_info[ 0 ]
    ruleSet     = rule_info[ 1 ]

    for rule in ruleSet :
      logging.debug( "//////////////////////////////////////////////////" )
      logging.debug( "  DO DEMORGANS SIP IDB : parent_list: " + str( parent_list ) )
      logging.debug( "  DO DEMORGANS SIP ODB : ruleSet:" )
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
    #logging.debug( "  DO DEMORGANS SIP IDB : done running eval." )

    # ----------------------------------------- #
  
    final_fmla = nw_tools.get_final_fmla( ruleSet )

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

      logging.debug( "  DO DEMORGANS SIP IDB : parent rule:" )
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

      dom_rules = sip_idb.get_dom_rules( orig_name, \
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
  
      ruleMeta = sip_idb.replaceSubgoalNegations( orig_name, \
                                                  not_name, \
                                                  parent_rid, \
                                                  ruleMeta )

    # ----------------------------------------- #
    # resolve double negations

    ruleMeta = sip_idb.resolveDoubleNegations( ruleMeta )

    # ----------------------------------------- #
    # order recursive rules last

    ruleMeta = nw_tools.sortDMRules( ruleMeta )

    COUNTER += 1

  return ruleMeta

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

      if subgoalDict[ "subgoalName" ] == orig_name :
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
      elif sip_idb.is_an_exidom( not_name, r, orig_name, ruleMeta ) :
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
        subgoalListOfDicts.append( exidom_sub )

    # ----------------------------------------- #
    # add existential domain subgoal,
    # if applicable

#    prevRules = []
#    for currRule in existentialVarsRules :
#
#      if currRule.relationName in prevRules :
#        pass
#
#      else :
#        prevRules.append( currRule.relationName )
#
#        existentialVarSubgoal_dict = {}
#        existentialVarSubgoal_dict[ "subgoalName" ]    = currRule.ruleData[ "relationName" ]
#        existentialVarSubgoal_dict[ "subgoalAttList" ] = currRule.ruleData[ "goalAttList" ]
#        existentialVarSubgoal_dict[ "polarity" ]       = ""
#        existentialVarSubgoal_dict[ "subgoalTimeArg" ] = ""
#    
#        subgoalListOfDicts.append( existentialVarSubgoal_dict )


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

  return newDMRules


#########
#  EOF  #
#########
