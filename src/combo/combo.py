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
from translators import c4_translator
from evaluators  import c4_evaluator
from utils       import clockTools, tools, dumpers, setTypes, nw_tools
from dm          import dm_time_att_replacement
from constraints import sip

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
    if NW_DOM_DEF == "sip" :
      pass
    else :
      raise ValueError( "unrecognized NW_DOM_DEF option '" + NW_DOM_DEF + \
                        "' for combo NW rewrites. aborting..." )
  except ConfigParser.NoOptionError :
    raise ValueError( "no 'NW_DOM_DEF' defined in 'DEFAULT' section of " + settings_path + \
                      ". aborting..." )

  # ----------------------------------------- #
  # replace unused variables with wildcards

  if NW_DOM_DEF == "sip" :
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

  if NW_DOM_DEF == "sip" :

    # future optimization : do this lazily:
    ruleMeta.extend( nw_tools.generate_orig_cps( ruleMeta ) )

  # ----------------------------------------- #
  # append rids to all rel names and
  # generate cps of the original rules
  # (do not reference these in final programs)

  if NW_DOM_DEF == "sip" :

    # future optimization : do this lazily:
    not_templates, ruleMeta = get_not_templates_combo( factMeta, ruleMeta )

    #for r in ruleMeta :
    #  print str( r.rid ) + " : " + dumpers.reconstructRule( r.rid, r.cursor )
    #sys.exit( "blee" )

  # ----------------------------------------- #
  # generate a map of all rids to corresponding
  # rule meta object pointers.

  if NW_DOM_DEF == "sip" :
    rid_to_rule_meta_map = nw_tools.generate_rid_to_rule_meta_map( ruleMeta )

  # ----------------------------------------- #
  # build all de morgan's rules

  COUNTER = 0
  while nw_tools.stillContainsNegatedIDBs( ruleMeta, cursor ) :

    logging.debug( "  COMBO : COUNTER = " + str( COUNTER ) )
    if COUNTER == 3 :
      print "////////////"
      for r in ruleMeta :
        print dumpers.reconstructRule( r.rid, r.cursor )
      sys.exit( "wtf?" )

    # ----------------------------------------- #
    # check if any rules include negated idb
    # subgoals

    targetRuleMetaSets = nw_tools.getRuleMetaSetsForRulesCorrespondingToNegatedSubgoals( ruleMeta, \
                                                                                         cursor )

    #if COUNTER == 2 :
    #  print targetRuleMetaSets[0][0]
    #  for r in targetRuleMetaSets[0][1] :
    #    print c4_translator.get_c4_line( r.ruleData, "rule" )
    #  print "////////////"
    #  for r in ruleMeta :
    #    print dumpers.reconstructRule( r.rid, r.cursor )
    #  sys.exit( "asdf" )

    # ----------------------------------------- #
    # break execution if no rules contain negated IDBs.
    # should not hit this b/c of loop condition.

    if len( targetRuleMetaSets ) < 1 :
      return []

    # ----------------------------------------- #
    # create the de morgan rewrite rules.
    # incorporates domcomp and existential 
    # domain subgoals.

    if NW_DOM_DEF == "sip" :
      ruleMeta = do_combo_sip( factMeta, \
                               ruleMeta, \
                               targetRuleMetaSets, \
                               not_templates, \
                               rid_to_rule_meta_map, \
                               cursor, \
                               argDict )
    else :
      raise ValueError( "unrecognized NW_DOM_DEF option '" + NW_DOM_DEF + \
                        "'. aborting..." )

    #for r in ruleMeta :
    #  print str( r.rid ) + " : " + dumpers.reconstructRule( r.rid, r.cursor )
    #sys.exit( "blast" )

    # ----------------------------------------- #
    # update rid to rule meta map

    rid_to_rule_meta_map = nw_tools.generate_rid_to_rule_meta_map( ruleMeta )

    #if COUNTER == 2 :
    #  for r in ruleMeta :
    #    print str( r.rid ) + " : " + dumpers.reconstructRule( r.rid, r.cursor )
    #  sys.exit( "blahasdf" )

    # increment loop counter
    COUNTER += 1

  # ----------------------------------------- #
  # replace unused variables with wildcards

  if NW_DOM_DEF == "sip" :
    ruleMeta = nw_tools.replace_unused_vars( ruleMeta, cursor )

  # ----------------------------------------- #
  # filter out unused not_ rules

  if NW_DOM_DEF == "sip" :
    ruleMeta = nw_tools.delete_unused_not_rules( ruleMeta, cursor )

  for r in ruleMeta :
    print str( r.rid ) + " : " + dumpers.reconstructRule( r.rid, r.cursor )
  sys.exit( "blahasdf" )

  logging.debug( "  COMBO : ...done." )
  return factMeta, ruleMeta


#############################
#  GET NOT TEMPLATES COMBO  #
#############################
# return a dict mapping positive relation names to 
# lists of not_ rules derived from the target NW rewrite
# process. The not_ rules act as templates and do not
# include domain subgoals.
def get_not_templates_combo( factMeta, ruleMeta ) :

  cursor = ruleMeta[0].cursor # all this stuff happens on the same db.

  not_template_ruleData = {}

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
    if not rule.relationName  in not_template_ruleData :
      not_template_ruleData[ rule.relationName ] = []

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

      not_template_ruleData[ rule.relationName ].append( not_ruleData )

      #rid                         = tools.getIDFromCounters( "rid" )
      #not_rule                    = copy.deepcopy( Rule.Rule( rid, not_ruleData, cursor ) )
      #not_rule.cursor             = cursor
      #not_rule.goal_att_type_list = rule.goal_att_type_list
      #not_rule.manually_set_types()
      #not_template_ruleMeta[ rule.relationName ].append( not_rule )

  # add exidom subgoals
  not_template_ruleData, ruleMeta = sip.add_exidom_subs( not_template_ruleData, \
                                                         factMeta, \
                                                         ruleMeta, \
                                                         cursor )
  #print "-------------------------------"
  #for r in ruleMeta :
  #  print c4_translator.get_c4_line( r.ruleData, "rule" )
  #print "-------------------------------"
  #ruleMeta[0].cursor.execute( "SELECT rid FROM Rule" )
  #rid_list = ruleMeta[0].cursor.fetchall()
  #rid_list = tools.toAscii_list( rid_list )
  #for r in rid_list :
  #  print "rid = " + str( r ) + " : " + dumpers.reconstructRule( r, ruleMeta[0].cursor )
  #sys.exit( "asdf" )

  return not_template_ruleData, ruleMeta

##################
#  DO COMBO SIP  #
##################
def do_combo_sip( factMeta, \
                  ruleMeta, \
                  targetRuleMetaSets, \
                  not_templates, \
                  rid_to_rule_meta_map, \
                  cursor, \
                  argDict ) :

  logging.debug( "  DO COMBO SIP : running process..." )

  #for r in targetRuleMetaSets :
  #  print r
  #for r in ruleMeta :
  #  print c4_translator.get_c4_line( r.ruleData, "rule" )
  #sys.exit( "asdf" )

  COUNTER = 0
  for rule_info in targetRuleMetaSets :

    logging.debug( "  DO COMBO SIP : >COUNTER  = " + str( COUNTER ) )

    parent_list = rule_info[ 0 ]
    ruleSet     = rule_info[ 1 ]

    # 0. pull the template not_ rules.
    target_name = ruleSet[0].relationName
    #target_not_template = copy.deepcopy( not_templates[ target_name ] )
    if not previously_pulled( target_name, ruleMeta ) :
      target_not_template = copy.deepcopy( not_templates[ target_name ] )
    else :
      target_not_template = []

    logging.debug( "//////////////////////////////////////////////////" )
    logging.debug( "  DO COMBO SIP : parent_list : " + str( parent_list ) )
    logging.debug( "  DO COMBO SIP : ruleSet:" )
    for rule in ruleSet :
      logging.debug( "    " + dumpers.reconstructRule( rule.rid, rule.cursor ) )
    logging.debug( "  DO COMBO SIP : target_name : " + target_name )
    logging.debug( "  DO COMBO SIP : target_not_template : " )
    for t in target_not_template :
      logging.debug( "     " + c4_translator.get_c4_line( t, "rule" ) )
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

        # 2. build and save unidom facts derived using bindings from parent rules.
        unidom_facts = sip.get_unidom_facts( factMeta, \
                                             parent_rule, \
                                             ruleSet, \
                                             ruleMeta, \
                                             argDict, \
                                             rid_to_rule_meta_map )
        factMeta.extend( unidom_facts )

        #if parent_list == [['post',2]] :
        #  print COUNTER
        #  sys.exit( "here" )

        # 3. add the parent-specific unidom subgoal to the template not_ rule.
        #if COUNTER == 0 : # why this???
        if True :

          for ruleData in target_not_template :
            uni_sub = {}
            uni_sub[ "subgoalName" ]    = unidom_facts[0].relationName
            uni_sub[ "subgoalAttList" ] = ruleData[ "goalAttList" ]
            uni_sub[ "polarity" ]       = ""
            uni_sub[ "subgoalTimeArg" ] = ""
            ruleData[ "subgoalListOfDicts" ].append( uni_sub )
  
            # add rule to ruleMeta
            rid            = tools.getIDFromCounters( "rid" )
            newRule        = copy.deepcopy( Rule.Rule( rid, ruleData, cursor) )
            newRule.cursor = cursor
 
            newRule.goal_att_type_list = copy.deepcopy( ruleSet[0].goal_att_type_list )
            newRule.manually_set_types()
  
            logging.debug( "  DO COMBO SIP : adding rule '" + \
                           c4_translator.get_c4_line( newRule.ruleData, "rule" ) + "'" )
            ruleMeta.append( newRule )

      # 4. make not_ subgoal replacements in parent rules.
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

      #if parent_list == [['post', 2]] :
      #  for rule in ruleMeta :
      #    print c4_translator.get_c4_line( rule.ruleData, "rule" )
      #  for fact in factMeta :
      #    print c4_translator.get_c4_line( fact.factData, "fact" )
      #  sys.exit( "lmao" )

      COUNTER += 1

  # ----------------------------------------- #
  # order recursive rules last

  ruleMeta = nw_tools.sortDMRules( ruleMeta )

#  if ruleSet[0].relationName == "link" :
#    for r in ruleMeta :
#      print dumpers.reconstructRule( r.rid, r.cursor )
#      #print c4_translator.get_c4_line( r.ruleData, "rule" )
#    sys.exit( "blah" )

  logging.debug( "  DO COMBO SIP : ...done." )
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


#######################
#  PREVIOUSLY PULLED  #
#######################
def previously_pulled( target_name, ruleMeta ) :
  logging.debug( "  PREVIOUSLY PULLED : checking not_ '" + target_name + "'" )
  for rule in ruleMeta :
    if rule.relationName == "not_" + target_name :
      logging.debug( "  PREVIOUSLY PULLED : returning True." )
      return True
  logging.debug( "  PREVIOUSLY PULLED : returning False." )
  return False


#########
#  EOF  #
#########
