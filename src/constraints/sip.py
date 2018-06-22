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

import dm


######################
#  GET UNIDOM FACTS  #
######################
def get_unidom_facts( factMeta, \
                      parent_rule, \
                      target_ruleSet, \
                      ruleMeta, \
                      argDict, \
                      rid_to_rule_meta_map ) :

  logging.debug( "  GET UNIDOM FACTS : parent_rule = " + c4_translator.get_c4_line( parent_rule.ruleData, "rule" ) )
  logging.debug( "  GET UNIDOM FACTS : target_ruleSet :" )
  for r in target_ruleSet :
    logging.debug( "     " + c4_translator.get_c4_line( r.ruleData, "rule" ) )

  target_name = target_ruleSet[0].relationName

  # 0. get table list
  table_list = []
  for rule in ruleMeta :
    if not rule.relationName in table_list :
      table_list.append( rule.relationName )
  for fact in factMeta :
    if not fact.relationName in table_list :
      table_list.append( fact.relationName )

  # 1. get sip bindings for this parent rule 
  #    and generate the domcomp for the target set.

  sip_bindings   = get_sip_bindings( parent_rule, \
                                     target_ruleSet, \
                                     table_list, \
                                     factMeta, \
                                     ruleMeta, \
                                     argDict )

  target_domcomp = get_domcomp( target_ruleSet, \
                                table_list, \
                                factMeta, \
                                ruleMeta, \
                                argDict, \
                                rid_to_rule_meta_map )

  logging.debug( "  GET UNIDOM FACTS : target_domcomp :" )
  for t in target_domcomp :
    logging.debug( "     " + str( t ) )
  #sys.exit( "blah" )

  # 2. test each domcomp fact in a pilot program.
  #    keep only the domcomp facts which make sense.

  COUNTER = 0
  unidom_tups = []
  for domcomp_tup in target_domcomp :

    # sanity check : make sure identical atts have identical bindings
    flag = False
    for rule in target_ruleSet :
      matches = {}
      for i in range( 0, len( rule.ruleData[ "goalAttList" ] ) ) :
        gatt = rule.ruleData[ "goalAttList" ][i]
        val  = domcomp_tup[i]
        if not gatt in matches :
          matches[ gatt ] = val
        elif gatt in matches and \
             val == matches[ gatt ] :
          pass
        else :
          logging.debug( "  binding doesn't make sense for rule '" + \
                         dumpers.reconstructRule( rule.rid, rule.cursor ) + "'" )
          flag = True
          break

    if flag :
      continue # try the next domcomp tuple

    # 2a. build a pilot program using the domcomp tup.
    # observe target_domcomp also contains all the original program results.
    logging.debug( "  domcomp_tup = " + str( domcomp_tup ) )
    pilot_program, pilot_table_list = get_pilot_program( domcomp_tup, \
                                                         target_ruleSet, \
                                                         target_domcomp, \
                                                         factMeta, \
                                                         ruleMeta )

    # 2b. run the pilot program to see if the value makes sense
    #     => yields one of the sip bindings.
    parsedResults = run_program_c4( [ pilot_program, pilot_table_list ], argDict )

    for tup in sip_bindings :
      if tup in parsedResults[ target_ruleSet[0].relationName ] :
        if not domcomp_tup in unidom_tups :
          logging.debug( "  GET UNIDOM FACTS : COUNTER = " + str( COUNTER ) )
          logging.debug( "  GET UNIDOM FACTS : adding to unidom facts '" + str( domcomp_tup ) + "'" )
          unidom_tups.append( domcomp_tup )

    #if COUNTER == 8 and target_name == "link" :
    if COUNTER == 1081 :
      print "len( target_domcomp ) = " + str( len( target_domcomp ) )
      print "domcomp_tup = " + str( domcomp_tup )
      print "sip bindings :"
      for tup in sip_bindings :
        print tup
      print "++++++"
      print "parsed results for " + target_ruleSet[0].relationName + " :"
      for tup in parsedResults[ target_ruleSet[0].relationName ] :
        print tup
      print "unidom tups collection :"
      print len( unidom_tups )
      for t in unidom_tups :
        print t
      sys.exit( "one of life's grander delusions." )

    COUNTER += 1

  logging.debug( "  GET UNIDOM FACTS : unidom_tups :" )
  for t in unidom_tups :
    logging.debug( "     " + str( t ) )
  logging.debug( "  GET UNIDOM FACTS : COUNTER == " + str( COUNTER ) )
  #sys.exit( "lmao" )

  # generate facts
  unidom_facts = []
  for tup in unidom_tups :
    ufact = {}
    ufact[ "relationName" ] = "unidom_not_" + target_name
    ufact[ "factTimeArg" ]  = ""
    ufact[ "dataList" ]     = []
    for d in tup :
      if d.isdigit() :
        ufact[ "dataList" ].append( d )
      elif "'" in d or '"' in d :
        ufact[ "dataList" ].append( d )
      else :
        ufact[ "dataList" ].append( '"' + d + '"' )
    fid = tools.getIDFromCounters( "fid" )
    new_fact        = copy.deepcopy( Fact.Fact( fid, ufact, factMeta[0].cursor ) )
    new_fact.cursor = factMeta[0].cursor
    unidom_facts.append( new_fact )

  return unidom_facts


#######################
#  GET PILOT PROGRAM  #
#######################
# pilot programs are built using individual tuples of the domcomp.
# the programs test whether the domcomp tuple makes sense in the 
# context of the definition of the positive relation.
def get_pilot_program( domcomp_bindings_tup, \
                       target_ruleSet, \
                       target_domcomp, \
                       factMeta, \
                       ruleMeta ) :

  logging.debug( "  GET PILOT PROGRAM : domcomp_bindings_tup = " + \
                 str( domcomp_bindings_tup ) )

  # collect the unidom facts associated with this test
  test_unidom = []

  # 0. build initial program.
  #    work with a new ruleData element called "sip_bindings",
  #    which is a list of binary lists matching attributes to
  #    sip binding values.

  # [ { 'ruleData'     : { <ruleData> }, 
  #     'sip_bindings' : [ <data tuple> ], 
  #     'sub_colors'   : [ <True | False> ] }, ... ]
  all_pilot_rules = []

  # [ { 'factData' : { <factData> }, ... ]
  all_pilot_facts = []
  for fact in factMeta :
    new_fact = {}
    new_fact[ "factData" ] = fact.factData
    all_pilot_facts.append( new_fact )

  logging.debug( "  GET PILOT PROGRAM : orig facts :" )
  for tup in all_pilot_facts :
    logging.debug( "     " + str( tup ) )

  for rule in target_ruleSet :
    a_pilot_rule = {}

    if not rule.relationName.startswith( "exidom_" ) and \
       not rule.relationName.startswith( "orig_" ) :

      a_pilot_rule[ "ruleData" ]     = copy.deepcopy( rule.ruleData )
      a_pilot_rule[ "sip_bindings" ] = domcomp_bindings_tup
      a_pilot_rule[ "sub_colors" ]   = [ False for i in \
                                         a_pilot_rule[ "ruleData" ][ "subgoalListOfDicts" ] ]
      assert( len( a_pilot_rule[ "ruleData" ][ "subgoalListOfDicts" ] ) == \
              len( a_pilot_rule[ "sub_colors" ] ) )

      all_pilot_rules.append( a_pilot_rule )

      # spawn any new edbs to support the bindings.
      new_bound_facts = get_new_bound_facts( a_pilot_rule, factMeta, ruleMeta )
      logging.debug( "  GET PILOT PROGRAM : initial new pilot facts :" )
      for tup in new_bound_facts :
        logging.debug( "     " + str( tup ) )
      all_pilot_facts.extend( new_bound_facts )
      test_unidom.extend( new_bound_facts )

  # 1. push down domcomp bindings until no more bound idbs exist.
  COUNTER = 0
  while bound_idbs_still_exist( target_ruleSet[0].relationName, \
                                all_pilot_rules, \
                                ruleMeta ) :

    # 1a. get info on a bound idb
    target_bound_idb, pilot_rule, sub_index = get_bound_idb( target_ruleSet[0].relationName, \
                                                             all_pilot_rules, \
                                                             ruleMeta )

    # 1b. get the rule corresponding to the bound idb
    new_pilot_rules = get_defn( target_bound_idb[ "subgoalName" ], \
                                pilot_rule, \
                                sub_index, \
                                ruleMeta )
    pilot_rule[ "sub_colors" ][ sub_index ] = True
    for npr in new_pilot_rules :
      #all_pilot_rules.append( npr )
      if not pilot_rule_already_exists( npr, all_pilot_rules ) :
        all_pilot_rules.append( npr )
        logging.debug( "  GET NEW BOUND FACTS : adding '" + \
                       c4_translator.get_c4_line( npr[ "ruleData" ], "rule" ) + "'" )
      else :
        logging.debug( "  GET NEW BOUND FACTS : not adding '" + \
                       c4_translator.get_c4_line( npr[ "ruleData" ], "rule" ) + "'" )

    # 1c. push down tuple bindings to target rule edbs and save the new facts
    for npr in new_pilot_rules :
      # spawn any new edbs to support the bindings.
      new_bound_facts = get_new_bound_facts( npr, factMeta, ruleMeta )
      logging.debug( "  GET NEW BOUND FACTS : while loop additions :" )
      for tup in new_bound_facts :
        logging.debug( "     " + str( tup ) )
      all_pilot_facts.extend( new_bound_facts )
      test_unidom.extend( new_bound_facts )

    if COUNTER == 100 :
      for l in all_pilot_rules :
        print c4_translator.get_c4_line( l[ "ruleData" ], "rule" )
        print l[ "sip_bindings" ]
        print l[ "sub_colors" ]
      print bound_idbs_still_exist( target_ruleSet[0].relationName, \
                                    all_pilot_rules, \
                                    ruleMeta )
      sys.exit( "shit" )

    COUNTER += 1

  # 2. convert program into a list of strings
  rule_fact_lines = []
  for r in all_pilot_rules :
    line = c4_translator.get_c4_line( r[ "ruleData" ], "rule" )
    if not line in rule_fact_lines :
      rule_fact_lines.append( line )

  #for l in program_lines :
  #  print l
  #sys.exit( "shit" )

  # 3. add the program facts
  for f in all_pilot_facts :
    rule_fact_lines.append( c4_translator.get_c4_line( f[ "factData" ], "fact" ) )

  # 4. derive and all all the defines
  table_list = []
  defines    = []
  for pr in all_pilot_rules :
    this_rule = None
    for rule in ruleMeta :
      if rule.relationName == pr[ "ruleData" ][ "relationName" ] :
        this_rule = rule
        break
    type_list   = [ t[1] for t in this_rule.goal_att_type_list ]
    rule_define = "define(" + \
                    rule.relationName + "," + \
                    "{" + ",".join( type_list ) + "});"
    if not rule_define in defines :
      defines.append( rule_define )
      table_list.append( rule.relationName )
  for fact in factMeta :
    type_list = [ t[1] for t in fact.dataListWithTypes ]
    fact_define = "define(" + \
                  fact.factData[ "relationName" ] + "," + \
                  "{" + ",".join( type_list ) + "});"
    if not fact_define in defines :
      defines.append( fact_define )
      table_list.append( fact.factData[ "relationName" ] )

  # deal with clocks.
  if need_clocks( ruleMeta ) :
    ruleMeta[0].cursor.execute( "SELECT src,dest,sndTime,delivTime FROM Clock" )
    clock_facts = ruleMeta[0].cursor.fetchall()
    clock_facts = tools.toAscii_multiList( clock_facts )
    for cf in clock_facts :
      rule_fact_lines.append( 'clock("'  + cf[0] + \
                                   '","' + cf[1] + \
                                   '",'  + str( cf[2] ) + \
                                   ','   + str( cf[3] ) + ');' )
    defines.append( "define(clock,{string,string,int,int});" )

  program_lines = defines + rule_fact_lines

  #for l in program_lines :
  #  print l
  #print table_list
  #sys.exit( "fuck" )

  return program_lines, table_list

#########################
#  GET NEW BOUND FACTS  #
#########################
def get_new_bound_facts( a_pilot_rule, factMeta, ruleMeta ) :

  logging.debug( "  GET NEW BOUND FACTS : a_pilot_rule :" )
  logging.debug( "  GET NEW BOUND FACTS :    " + \
                    c4_translator.get_c4_line( a_pilot_rule[ "ruleData" ], "rule" ) )
  logging.debug( "  GET NEW BOUND FACTS :    sip_bindings :" + \
                    str( a_pilot_rule[ "sip_bindings" ] ) )
  logging.debug( "  GET NEW BOUND FACTS :    sub_colors :" + \
                    str( a_pilot_rule[ "sub_colors" ] ) )

  pilot_ruleData = a_pilot_rule[ "ruleData" ]
  sip_bindings   = a_pilot_rule[ "sip_bindings" ]

  # match goal atts with tup values
  # no exi vars or wild cards by defn of goal att.
  assert( len( pilot_ruleData[ "goalAttList" ] ) == len( sip_bindings ) )
  matches = {}
  for i in range( 0, len( pilot_ruleData[ "goalAttList" ] ) ) :
    gatt = pilot_ruleData[ "goalAttList" ][ i ]
    val  = sip_bindings[ i ]
    if not val == "_" :
      matches[ gatt ] = val

  logging.debug( "  GET NEW BOUND FACTS : matches = " + str( matches ) )

  #if a_pilot_rule[ "ruleData" ][ "relationName" ] == "link" :
  #  print matches
  #  sys.exit( "bla" )

  # generate new facts
  new_facts = []
  for i in range( 0, len( pilot_ruleData[ "subgoalListOfDicts" ] ) ) :
    sub = pilot_ruleData[ "subgoalListOfDicts" ][i]
    if not nw_tools.is_idb_only( sub[ "subgoalName" ], factMeta, ruleMeta ) and \
       has_binding_refs( sub[ "subgoalAttList" ], matches ) :

      # get all new fact tups
      tmp = []
      for j in range( 0, len( sub[ "subgoalAttList" ] ) ) :
        satt = sub[ "subgoalAttList" ][j]
        if satt in matches :
          data = matches[ satt ]
          if data.isdigit() :
            tmp.append( [ data ] )
          elif "'" in data or '"' in data :
            tmp.append( data )
          else :
            tmp.append( [ '"' + data + '"' ] )
        else :
          tmp.append( all_fact_data_on_index( sub[ "subgoalName" ], j, factMeta ) )

      # generate all new facts
      all_dataLists = list( itertools.product( *tmp ) )
      new_facts_factData = []
      for dataList in all_dataLists :
        new_bound_factData = {}
        new_bound_factData[ "relationName" ] = sub[ "subgoalName" ]
        new_bound_factData[ "factTimeArg" ]  = ""
        new_bound_factData[ "dataList" ]     = list( copy.deepcopy( dataList ) )
        if not new_bound_factData in new_facts_factData :
          new_fact = {}
          new_fact[ "factData" ] = new_bound_factData
          new_facts_factData.append( new_bound_factData )
          new_facts.append( new_fact )
      #for factData in new_facts_factData :
      #  fid = tools.getIDFromCounters( "fid" )
      #  new_fact        = copy.deepcopy( Fact.Fact( fid, factData, factMeta[0].cursor ) )
      #  new_fact.cursor = factMeta[0].cursor
      #  new_facts.append( new_fact )

      # be sure to color this subgoal.
      a_pilot_rule[ "sub_colors" ][ i ] = True

  logging.debug( "  GET NEW BOUND FACTS : returning :" )
  for f in new_facts :
    logging.debug( "     " + str( f ) )
    logging.debug( "     " + c4_translator.get_c4_line( f[ "factData" ], "fact" ) )
  #sys.exit( "asdf" )

  return new_facts

############################
#  ALL FACT DATA ON INDEX  #
############################
def all_fact_data_on_index( rel_name, index, factMeta ) :
  fact_data = []
  for fact in factMeta :
    if fact.relationName == rel_name :
      data = fact.factData[ "dataList" ][index]
      if data.isdigit() :
        fact_data.append( data )
      elif "'" in data or '"' in data :
        fact_data.append( data )
      else :
        fact_data.append( '"' + data + '"' )
  return fact_data

######################
#  HAS BINDING REFS  #
######################
def has_binding_refs( subgoalAttList, matches ) :
  for satt in subgoalAttList :
    if satt in matches :
      return True
  return False

##############
#  GET DEFN  #
##############
def get_defn( target_name, \
              pilot_rule, \
              sub_index, \
              ruleMeta ) :

  # 0. get subgoal sip bindings
  gatt_to_sip  = {}
  for i in range( 0, len( pilot_rule[ "ruleData" ][ "goalAttList" ] ) ) :
    gatt                = pilot_rule[ "ruleData" ][ "goalAttList" ][i]
    gatt_to_sip[ gatt ] = pilot_rule[ "sip_bindings" ][i]

  sub_sip_bindings = []
  for i in range( 0, len( pilot_rule["ruleData"][ "subgoalListOfDicts" ][ sub_index ][ "subgoalAttList" ] ) ) :
    satt = pilot_rule["ruleData"][ "subgoalListOfDicts" ][ sub_index ][ "subgoalAttList" ][i]

    try :
      sub_sip_bindings.append( gatt_to_sip[ satt ] )
    except KeyError :
      sub_sip_bindings.append( "_" )

  # 1. get new pilot rules
  new_pilot_rules = []
  for rule in ruleMeta :
    if rule.relationName == target_name :
      new_pilot_rule = {}
      new_pilot_rule[ "ruleData" ]     = rule.ruleData
      new_pilot_rule[ "sip_bindings" ] = sub_sip_bindings
      new_pilot_rule[ "sub_colors" ]   = [ False for i in new_pilot_rule[ "ruleData" ][ "subgoalListOfDicts" ] ]
      new_pilot_rules.append( new_pilot_rule )

  return new_pilot_rules

###################
#  GET BOUND IDB  #
###################
def get_bound_idb( target_name, all_pilot_rules, ruleMeta ) :
  for a_pilot_rule in all_pilot_rules :
    # check if any sub using the binding vars is idb.
    for i in range( 0, len( a_pilot_rule[ "ruleData" ][ "subgoalListOfDicts" ] ) ) :
      sub = a_pilot_rule[ "ruleData" ][ "subgoalListOfDicts" ][ i ]
      if not sub[ "subgoalName" ] == target_name :
        if nw_tools.isIDB( sub[ "subgoalName" ], ruleMeta[0].cursor ) and \
           not a_pilot_rule[ "sub_colors" ][ i ] :
          logging.debug( "  GET BOUND IDB : found one ---> " + str(sub) )
          return sub, a_pilot_rule, i
      else :
        a_pilot_rule[ "sub_colors" ][ i ] = True # hit a recursive subgoal. flip the color.

############################
#  BOUND IDBS STILL EXIST  #
############################
# idb subs are no longer bound if they've been sip_colored in a 
# previous iteration.
def bound_idbs_still_exist( target_name, all_pilot_rules, ruleMeta ) :
  for a_pilot_rule in all_pilot_rules :
    # check if any sub using the binding vars is idb.
    for i in range( 0, len( a_pilot_rule[ "sub_colors" ] ) ) :
      sub = a_pilot_rule[ "ruleData" ][ "subgoalListOfDicts" ][ i ]
      if sub[ "subgoalName" ] == "clock" :
        a_pilot_rule[ "sub_colors" ][ i ] = True
      elif not sub[ "subgoalName" ] == target_name                  and \
         nw_tools.isIDB( sub[ "subgoalName" ], ruleMeta[0].cursor ) and \
         not a_pilot_rule[ "sub_colors" ][ i ] :
        logging.debug( "  BOUND IDBS STILL EXIST : found one ---> " + str(sub) )
        logging.debug( "  BOUND IDBS STILL EXIST : returning True." )
        return True
  logging.debug( "  BOUND IDBS STILL EXIST : returning False." )
  return False

####################
#  IS SIP COLORED  #
####################
def is_sip_colored( rel_name, ruleMeta ) :
  for rule in ruleMeta :
    if rule.relationName == rel_name and \
       rule.sip_color    == True :
      return True
  return False

#################
#  GET DOMCOMP  #
#################
def get_domcomp( target_ruleSet, \
                 table_list, \
                 factMeta, \
                 ruleMeta, \
                 argDict, \
                 rid_to_rule_meta_map ) :

  logging.debug( "  GET DOMCOMP : target_ruleSet :" )
  for t in target_ruleSet :
    logging.debug( "    " + c4_translator.get_c4_line( t.ruleData, "rule" ) )
  #sys.exit( "shit" )

  cursor      = ruleMeta[0].cursor # it's all the same db cursor
  target_name = target_ruleSet[0].relationName

  program_lines = []
  domcomp_table_list = copy.deepcopy( table_list )

  # get defines
  defines = []
  for rule in ruleMeta :
    type_list   = [ t[1] for t in rule.goal_att_type_list ]
    rule_define = "define(" + \
                    rule.relationName + "," + \
                    "{" + ",".join( type_list ) + "});"
    if not rule_define in defines :
      defines.append( rule_define )
  for fact in factMeta :
    type_list = [ t[1] for t in fact.dataListWithTypes ]
    fact_define = "define(" + \
                  fact.factData[ "relationName" ] + "," + \
                  "{" + ",".join( type_list ) + "});"
    if not fact_define in defines :
      defines.append( fact_define )

  # check for user-defined not_ constraints
  if user_constriaints_exist( target_name, factMeta ) :
    pass

  else :

    # otherwise, build adom rules
    adom_rule_meta = dm.buildAdom( factMeta, cursor )
    for arm in adom_rule_meta :
      program_lines.append( c4_translator.get_c4_line( arm.ruleData, "rule" ) )
      if arm.relationName == "adom_string" :
        arm_type = "string"
        domcomp_table_list.append( "adom_string" )
      else :
        arm_type = "int"
        domcomp_table_list.append( "adom_int" )
      arm_define = "define(" + \
                   arm.ruleData[ "relationName" ] + "," + \
                   "{" + arm_type + "});"
      if not arm_define in defines :
        defines.append( arm_define )

  # get domcomp rule
  if user_constriaints_exist( target_name, factMeta ) :
    domcomp_ruleData, domcomp_type_list = get_domcomp_rule( target_ruleSet, \
                                                            True, \
                                                            ruleMeta, \
                                                            rid_to_rule_meta_map )
  else :
    domcomp_ruleData, domcomp_type_list = get_domcomp_rule( target_ruleSet, \
                                                            False, \
                                                            ruleMeta, \
                                                            rid_to_rule_meta_map )
    domcomp_define = "define(" + \
                     domcomp_ruleData[ "relationName" ] + "," + \
                     "{" + ",".join( domcomp_type_list ) + "});"
    defines.append( domcomp_define )

  program_lines.append( c4_translator.get_c4_line( domcomp_ruleData, "rule" ) )
  domcomp_table_list.append( "domcomp_not_" + target_name )

  # add all other rules
  rule_fact_lines = []
  for rule in ruleMeta :
    rule_fact_lines.append( c4_translator.get_c4_line( rule.ruleData, "rule" ) )
  for fact in factMeta :
    rule_fact_lines.append( c4_translator.get_c4_line( fact.factData, "fact" ) )

  # deal with clocks.
  if need_clocks( ruleMeta ) :
    ruleMeta[0].cursor.execute( "SELECT src,dest,sndTime,delivTime FROM Clock" )
    clock_facts = ruleMeta[0].cursor.fetchall()
    clock_facts = tools.toAscii_multiList( clock_facts )
    for cf in clock_facts :
      rule_fact_lines.append( 'clock("'  + cf[0] + \
                                   '","' + cf[1] + \
                                   '",'  + str( cf[2] ) + \
                                   ','   + str( cf[3] ) + ');' )
    defines.append( "define(clock,{string,string,int,int});" )

  # run program
  program_lines = defines + program_lines + rule_fact_lines
  parsedResults = run_program_c4( [ program_lines, domcomp_table_list ], argDict )

  return parsedResults[ "domcomp_not_" + target_name ]

############################
#  USER CONSTRAINTS EXIST  #
############################
def user_constriaints_exist( target_name, factMeta ) :
  for fact in factMeta :
    if fact.relationName.startswith( "adom_not_" + target_name ) :
      return True
  return False

######################
#  GET DOMCOMP RULE  #
######################
# user_constraints_exist = boolean
# return rule data
# ONLY SUPPORTS ONE DOMCOMP RULE ONLY!!!
def get_domcomp_rule( target_ruleSet, user_constraints_exist, ruleMeta, rid_to_rule_meta_map ) :

  target_name = target_ruleSet[0].relationName

  # check for a user-defined constraint rule
  if user_constraint_rule_exists( target_name, ruleMeta ) :
    for rule in ruleMeta :
      if rule.relationName == "domcomp_not_" + target_name :
        type_list = [ t[1] for t in  rule.goal_att_type_list ]
        return copy.deepcopy( rule.ruleData ), copy.deepcopy( type_list )

  # otherwise, generate the initial complement automatically.
  else :
    domcomp_ruleData = {}
    domcomp_ruleData[ "relationName" ]       = "domcomp_not_" + target_name
    domcomp_ruleData[ "goalTimeArg" ]        = ""
    domcomp_ruleData[ "goalAttList" ]        = target_ruleSet[0].goalAttList
    domcomp_ruleData[ "eqnDict" ]            = {}
    domcomp_ruleData[ "subgoalListOfDicts" ] = []
  
    goal_att_type_list = [ t[1] for t in target_ruleSet[0].goal_att_type_list ]
  
    # add adom subgoals
    domcomp_type_list = []
    for i in range( 0, len( domcomp_ruleData[ "goalAttList" ] ) ) :
      curr_att  = domcomp_ruleData[ "goalAttList" ][i]
      curr_type = goal_att_type_list[i]
  
      sub = {}
      sub[ "polarity" ]       = ""
      sub[ "subgoalTimeArg" ] = ""
      if curr_type == "string" :
        if user_constraints_exist :
          sub[ "subgoalName" ]    = "adom_not_" + target_name + "_string"
        else :
          sub[ "subgoalName" ]    = "adom_string"
        sub[ "subgoalAttList" ] = [ curr_att ]
        domcomp_type_list.append( "string" )
      else :
        if user_constraints_exist :
          sub[ "subgoalName" ]    = "adom_not_" + target_name + "_int"
        else :
          sub[ "subgoalName" ]    = "adom_int"
        sub[ "subgoalAttList" ] = [ curr_att ]
        domcomp_type_list.append( "int" )
  
      domcomp_ruleData[ "subgoalListOfDicts" ].append( sub )
  
    # add negative positive rule subgoal reference
    neg_sub = {}
    neg_sub[ "subgoalName" ]    = target_name
    neg_sub[ "polarity" ]       = "notin"
    neg_sub[ "subgoalAttList" ] = domcomp_ruleData[ "goalAttList" ]
    neg_sub[ "subgoalTimeArg" ] = ""
  
    domcomp_ruleData[ "subgoalListOfDicts" ].append( neg_sub )
  
    return domcomp_ruleData, domcomp_type_list

#################################
#  USER CONSTRAINT RULE EXISTS  #
#################################
def user_constraint_rule_exists( target_name, ruleMeta ) :
  for rule in ruleMeta :
    if rule.relationName == "domcomp_not_" + target_name :
      return True
  return False

######################
#  GET SIP BINDINGS  #
######################
def get_sip_bindings( parent_rule, target_ruleSet, table_list, factMeta, ruleMeta, argDict ) :

  logging.debug( "  GET SIP BINDINGS : parent_rule :" )
  logging.debug( "     " + c4_translator.get_c4_line( parent_rule.ruleData, "rule" ) )
  logging.debug( "  GET SIP BINDINGS : target_ruleSet :" )
  for t in target_ruleSet :
    logging.debug( "     " + c4_translator.get_c4_line( t.ruleData, "rule" ) )
  logging.debug( "  GET SIP BINDINGS : ruleMeta :" )
  for r in ruleMeta :
    logging.debug( "     " + c4_translator.get_c4_line( r.ruleData, "rule" ) )

  target_name = target_ruleSet[0].relationName

  # generate sip rule
  orig_rel_name                        = target_ruleSet[0].relationName
  sip_ruleData                         = {}
  sip_ruleData[ "relationName" ]       = "sip_not_" + orig_rel_name
  sip_ruleData[ "goalTimeArg" ]        = ""
  sip_ruleData[ "subgoalListOfDicts" ] = copy.deepcopy( parent_rule.subgoalListOfDicts )
  sip_ruleData[ "eqnDict" ]            = copy.deepcopy( parent_rule.eqnDict )

  lists_of_att_bindings = []
  for sub in parent_rule.subgoalListOfDicts :
    #print "sub = " + str( sub )
    if sub[ "subgoalName" ] == orig_rel_name and \
       sub[ "polarity" ] == "notin" :
      lists_of_att_bindings.append( sub[ "subgoalAttList" ] )

  # cannot support the appearance of the same negated subgoal
  # more than once in the same rule.
  try :
    assert( len( lists_of_att_bindings ) == 1 )
  except AssertionError :
    if len( lists_of_att_bindings ) > 1 :
      raise AssertionError( "iapyx does not support rules negating the same subgoal twice. " + \
                            "see rule :\n     " + \
                            dumpers.reconstructRule( parent_rule.rid, parent_rule.cursor ) )
    else :
      raise AssertionError( "no rule bindings for relation '" + \
                            orig_rel_name + \
                            "' in rule :\n     " + \
                            dumpers.reconstructRule( parent_rule.rid, parent_rule.cursor ) )

  # replace wildcards with some actual value.
  # since the value doesn't matter, just pick one.
  if "_" in lists_of_att_bindings[0] :
    program       = get_program( table_list, factMeta, ruleMeta )
    parsedResults = run_program_c4( program, argDict )

    logging.debug( "before:" )
    logging.debug( lists_of_att_bindings[0] )

    for i in range( 0, len( lists_of_att_bindings[0] ) ) :
      satt = lists_of_att_bindings[0][ i ]
      if satt == "_" :
        pick_something = parsedResults[ orig_rel_name ][0][ i ]
        if pick_something.isdigit() :
          lists_of_att_bindings[0][ i ] = pick_something
        elif "'" in pick_something or '"' in pick_something :
          lists_of_att_bindings[0][ i ] = pick_something
        else :
          lists_of_att_bindings[0][ i ] = '"' + pick_something + '"'

    logging.debug( "after:" )
    logging.debug( lists_of_att_bindings[0] )
    #sys.exit( "fuckingshit" )

  sip_ruleData[ "goalAttList" ] = lists_of_att_bindings[0]

  #sip_type_list = [ t[1] for t in parent_rule.goal_att_type_list ]
  sip_type_list = [ t[1] for t in target_ruleSet[0].goal_att_type_list ]

  if target_name == "link" and \
     lists_of_att_bindings[0] == [ "S", "Z3", "Y", "_", "NRESERVED" ] :
    print c4_translator.get_c4_line( parent_rule.ruleData, "rule" )
    for l in target_ruleSet :
      print c4_translator.get_c4_line( l.ruleData, "rule" )
    print sip_ruleData
    print sip_type_list
    print c4_translator.get_c4_line( sip_ruleData, "rule" )
    sys.exit( "asdf" )

  # build and run program
  program       = get_program( table_list, factMeta, ruleMeta, sip_ruleData, sip_type_list )
  parsedResults = run_program_c4( program, argDict )

  return parsedResults[ sip_ruleData[ "relationName" ] ]

#################
#  GET PROGRAM  #
#################
def get_program( table_list, factMeta, ruleMeta, sip_ruleData=None, sip_type_list=None ) :

  program_lines = []

  # get defines
  defines = []
  for rule in ruleMeta :
    type_list   = [ t[1] for t in rule.goal_att_type_list ]
    rule_define = "define(" + \
                    rule.relationName + "," + \
                    "{" + ",".join( type_list ) + "});"
    if not rule_define in defines :
      defines.append( rule_define )
  for fact in factMeta :
    type_list = [ t[1] for t in fact.dataListWithTypes ]
    fact_define = "define(" + \
                  fact.factData[ "relationName" ] + "," + \
                  "{" + ",".join( type_list ) + "});"
    if not fact_define in defines :
      defines.append( fact_define )

  # get sip program line
  if sip_ruleData and sip_type_list :
    sip_line = c4_translator.get_c4_line( sip_ruleData, "rule" )
    sip_define = "define(" + \
                      sip_ruleData[ "relationName" ] + "," + \
                      "{" + ",".join( sip_type_list ) + "});"

  # get program lines
  rule_fact_lines = []
  for rule in ruleMeta :
    rule_fact_lines.append( c4_translator.get_c4_line( rule.ruleData, "rule" ) )

  for fact in factMeta :
    rule_fact_lines.append( c4_translator.get_c4_line( fact.factData, "fact" ) )

  # build program
  if sip_ruleData and sip_type_list :
    defines.append( sip_define )
    rule_fact_lines = [ sip_line ] + rule_fact_lines

  if need_clocks( ruleMeta ) :
    ruleMeta[0].cursor.execute( "SELECT src,dest,sndTime,delivTime FROM Clock" )
    clock_facts = ruleMeta[0].cursor.fetchall()
    clock_facts = tools.toAscii_multiList( clock_facts )
    for cf in clock_facts :
      rule_fact_lines.append( 'clock("'  + cf[0] + \
                                   '","' + cf[1] + \
                                   '",'  + str( cf[2] ) + \
                                   ','   + str( cf[3] ) + ');' )
    defines.append( "define(clock,{string,string,int,int});" )

  program_lines.extend( defines )
  program_lines.extend( rule_fact_lines )

  # get table list
  # sever pointer to original table_list
  if sip_ruleData and sip_type_list :
    sip_table_list = table_list + [ sip_ruleData[ "relationName" ] ]
    return [ program_lines, sip_table_list ]
  else :
    return [ program_lines, table_list ]

####################
#  RUN PROGRAM C4  #
####################
# return evaluation results dictionary.
def run_program_c4( program_data, argDict ) :

  # run c4 evaluation
  results_array = c4_evaluator.runC4_wrapper( program_data, argDict )
  parsedResults = tools.getEvalResults_dict_c4( results_array )

  return parsedResults

#####################
#  ADD EXIDOM SUBS  #
#####################
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
def add_exidom_subs( not_template_ruleData, factMeta, ruleMeta, cursor ) :

  exidom_ruleData_list          = []
  exi_var_to_rel_index_map_list = []
  for key in not_template_ruleData :

    orig_ruleMeta_list = get_orig_ruleMeta_list( key, ruleMeta )
    if len( orig_ruleMeta_list ) < 1 :
      logging.debug( "skipping dom rules for " + key )
      continue

    # build exidom_ rules
    lists_of_exi_vars = []
    for orule in orig_ruleMeta_list :
      exi_vars = []
      for sub in orule.subgoalListOfDicts :
        for var in sub[ "subgoalAttList" ] :
          if not var in orule.goalAttList and \
             not var in exi_vars         and \
             not var == "_"              and \
             not "'" in var              and \
             not '"' in var              and \
             not var.isdigit() :
            exi_vars.append( var )

      if len( exi_vars ) > 0 :

        lists_of_exi_vars.append( [ exi_vars, orule.rid ] )

        # catch all possible values for existential atts
        patternMap = nw_tools.getPatternMap( len( orule.subgoalListOfDicts ) )
        for row in patternMap :

          #print "len( exidom_ruleData_list ) = " + str( len( exidom_ruleData_list ) )
          #print "row = " + str( row )

          # one exidom rule per pattern
          exidom_ruleData = {}
          exidom_ruleData[ "relationName" ]       = "exidom_" + \
                                                    "not_" + key + \
                                                    "_f" + str( orule.rid )
          exidom_ruleData[ "goalTimeArg" ]        = ""   
          exidom_ruleData[ "goalAttList" ]        = exi_vars

          # fails if exi_var parameterized with equations.
          exidom_ruleData[ "eqnDict" ] = {}

          exidom_ruleData[ "subgoalListOfDicts" ] = []

          # maintain a map of exi_vars to appearances in subgoals
          exi_var_to_rel_index_map = {}
          for var in exi_vars :
            exi_var_to_rel_index_map[ var ] = []

          for i in range( 0, len( row ) ) :
            bit = row[ i ]
            newSubgoal = orule.subgoalListOfDicts[ i ]

            # edit the polarity
            if bit == "0" :
              newSubgoal[ "polarity" ] = ""
            else :
              newSubgoal[ "polarity" ] = "notin"

            # remove references to global vars
            for i in range( 0, len( newSubgoal[ "subgoalAttList"] ) ) :
              var = newSubgoal[ "subgoalAttList"][i]
              if not var in exi_vars :
                newSubgoal[ "subgoalAttList"][ i ] = "_"
              else :
                newSubgoal[ "subgoalAttList"][ i ] = var
                exi_var_to_rel_index_map[ var ].append( [ newSubgoal[ "subgoalName" ], i ] )
            #logging.debug( "adding newSubgoal = " + str( newSubgoal ) )
            exidom_ruleData[ "subgoalListOfDicts" ].append( newSubgoal )

          exi_var_to_rel_index_map_list.append( copy.deepcopy( exi_var_to_rel_index_map ) )
          logging.debug( "  ADD EXIDOM SUBS : adding rule data for " + \
                         c4_translator.get_c4_line( exidom_ruleData, "rule" ) )
          exidom_ruleData_list.append( copy.deepcopy( exidom_ruleData ) )

          #print "checking contents exidom_ruleData_list:"
          #for e in exidom_ruleData_list :
          #  print c4_translator.get_c4_line( e, "rule" )

    logging.debug( "  ADD EXIDOM SUBS : exidom_ruleData_list:" )
    for r in exidom_ruleData_list :
      logging.debug( "     " +  c4_translator.get_c4_line( r, "rule" ) )
    #sys.exit( "shit" )

    # define subgoals
    exidom_subgoals = []
    for ev_list_info in lists_of_exi_vars :
      ev_list = ev_list_info[0]
      rid     = ev_list_info[1]
      exidom = {}
      exidom[ "subgoalName" ]    = "exidom_" + "not_" + key + "_f"  + str( rid )
      exidom[ "subgoalTimeArg" ] = ""   
      exidom[ "polarity" ]       = ""
      exidom[ "subgoalAttList" ] = ev_list
      exidom_subgoals.append( exidom )
  
    # add exidom_ subgoals, if applicable
    if len( exidom_subgoals ) > 0 :
      for ntr_ruleData in not_template_ruleData[ key ] :
        for esub in exidom_subgoals :
          if is_applicable( esub, ntr_ruleData ) :
            ntr_ruleData[ "subgoalListOfDicts" ].append( esub )
            logging.debug( "  ADD DOM SUBS : added sub '" + str( sub ) + "'" )

  # define exidom rules, if applicable
  exidom_rules = []
  for i in range( 0, len( exidom_ruleData_list ) ) :

    exidom_ruleData               = exidom_ruleData_list[i]
    this_exi_var_to_rel_index_map = exi_var_to_rel_index_map_list[i]

    #print c4_translator.get_c4_line( exidom_ruleData, "rule" )

    if nw_tools.isSafe( exidom_ruleData ) and \
       not nw_tools.identical_rule_already_exists( exidom_ruleData, ruleMeta ) :

      # do save
      exi_rid         = tools.getIDFromCounters( "rid" )
      exi_rule        = copy.deepcopy( Rule.Rule( exi_rid, exidom_ruleData, cursor) )
      exi_rule.cursor = cursor # need to do this for some reason or else cursor disappears?

      # set the exidom rule types manually
      exi_goal_types = []
      for i in range( 0, len( exidom_ruleData[ "goalAttList" ] ) ) :
        gatt = exidom_ruleData[ "goalAttList" ][ i ]

        # assume the types make sense
        representative_rel_index = this_exi_var_to_rel_index_map[ gatt ][0]

        # check rules for type data
        this_type = None
        for rule in ruleMeta :
          if rule.relationName == representative_rel_index[ 0 ] :
            index = representative_rel_index[ 1 ]
            this_type = [ i, rule.goal_att_type_list[index][1] ]
            break

        if not this_type :
          for fact in factMeta :
            if fact.relationName == representative_rel_index[0] :
              index     = representative_rel_index[ 1 ]
              this_type = [ i, fact.dataListWithTypes[index][1] ]

        assert( this_type != None )
        exi_goal_types.append( this_type )

      assert( len( exi_goal_types ) > 0 )
        
      exi_rule.goal_att_type_list = exi_goal_types
      exi_rule.manually_set_types()
      exidom_rules.append( exi_rule )

  ruleMeta.extend( exidom_rules )

  #for r in exidom_rules :
  #  print "rid = " + str( r.rid ) + " : " + c4_translator.get_c4_line( r.ruleData, "rule" )
  #sys.exit( "asdf" )

  return not_template_ruleData, ruleMeta

#############################
#  GET ORIG RULE META LIST  #
#############################
def get_orig_ruleMeta_list( rel_name, ruleMeta ) :
  orig_ruleMeta_list = []
  for rule in ruleMeta :
    if rule.relationName == rel_name :
      orig_ruleMeta_list.append( rule )
  return copy.deepcopy( orig_ruleMeta_list ) # sever pointers to ruleMeta objects

###################
#  IS APPLICABLE  #
###################
# check if the exidom_ (esub) is needed to constrain the existential
# domains for the given rule.
def is_applicable( esub, ruleData ) :
  for sub in ruleData[ "subgoalListOfDicts" ] :
    for var in sub[ "subgoalAttList" ] :
      if var in esub[ "subgoalAttList" ] :
        return True
  return False

#################
#  NEED CLOCKS  #
#################
def need_clocks( ruleMeta ) :
  for rule in ruleMeta :
    for sub in rule.subgoalListOfDicts :
      if sub[ "subgoalName" ] == "clock" :
        return True
  return False

###############################
#  PILOT RULE ALREADY EXISTS  #
###############################
def pilot_rule_already_exists( pilot_rule, all_pilot_rules ) :
  pilot_ruleData = pilot_rule[ "ruleData" ]
  for apr in all_pilot_rules :
    apr_ruleData = apr[ "ruleData" ]
    if pilot_ruleData == apr_ruleData :
      logging.debug( "  PILOT RULE ALREADY EXISTS : returning True." )
      return True
  logging.debug( "  PILOT RULE ALREADY EXISTS : returning False." )
  return False

#########
#  EOF  #
#########
