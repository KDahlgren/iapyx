#!/usr/bin/env python

'''
Test_dml.py
'''

#############
#  IMPORTS  #
#############
# standard python packages
import inspect, logging, os, string, sqlite3, sys, unittest

# ------------------------------------------------------ #
# import sibling packages HERE!!!
if not os.path.abspath( __file__ + "/../../src" ) in sys.path :
  sys.path.append( os.path.abspath( __file__ + "/../../src" ) )

from dedt       import dedt, dedalusParser, Fact, Rule, clockRelation, dedalusRewriter
from utils      import dumpers, globalCounters, tools
from evaluators import c4_evaluator

import dml

# ------------------------------------------------------ #


##############
#  TEST DML  #
##############
class Test_dml( unittest.TestCase ) :

  logging.basicConfig( format='%(levelname)s:%(message)s', level=logging.DEBUG )
  #logging.basicConfig( format='%(levelname)s:%(message)s', level=logging.INFO )
  #logging.basicConfig( format='%(levelname)s:%(message)s', level=logging.WARNING )

  PRINT_STOP    = False
  COMPARE_PROGS = True

  ################
  #  DML REPLOG  #
  ################
  # tests rewriting replog
  #@unittest.skip( "working on different example" )
  def test_dml_replog( self ) :

    # specify input and output paths
    inputfile               = os.getcwd() + "/testFiles/replog_driver.ded"
    expected_iapyx_dml_path = "./testFiles/replog_iapyx_dml.olg"
    expected_eval_path      = "./testFiles/replog_molly_eval.txt"

    self.comparison_workflow( inputfile, expected_iapyx_dml_path, expected_eval_path )


  ###############
  #  DML RDLOG  #
  ###############
  # tests rewriting rdlog
  #@unittest.skip( "working on different example" )
  def test_dml_rdlog( self ) :

    # specify input and output paths
    inputfile               = os.getcwd() + "/testFiles/rdlog_driver.ded"
    expected_iapyx_dml_path = "./testFiles/rdlog_iapyx_dml.olg"
    expected_eval_path      = "./testFiles/rdlog_molly_eval.txt"

    self.comparison_workflow( inputfile, expected_iapyx_dml_path, expected_eval_path )


  #################
  #  DML SIMPLOG  #
  #################
  # tests rewriting simplog
  #@unittest.skip( "working on different example" )
  def test_dml_simplog( self ) :

    # specify input and output paths
    inputfile               = os.getcwd() + "/testFiles/simplog_driver.ded"
    expected_iapyx_dml_path = "./testFiles/simplog_iapyx_dml.olg"
    expected_eval_path      = "./testFiles/simplog_molly_eval.txt"

    self.comparison_workflow( inputfile, expected_iapyx_dml_path, expected_eval_path )


  ############################
  #  DML TOY 3 AGG REWRITES  #
  ############################
  # tests rewriting the second toy program
  #@unittest.skip( "working on different example" )
  def test_dml_toy3_aggRewrites( self ) :

    # specify input and output paths
    inputfile               = os.getcwd() + "/testFiles/toy3_aggRewrites.ded"
    expected_iapyx_dml_path = "./testFiles/toy3_aggRewrites.olg"

    self.comparison_workflow( inputfile, expected_iapyx_dml_path, None )


  ###############
  #  DML TOY 2  #
  ###############
  # tests rewriting the second toy program
  @unittest.skip( "c4 illogically calculates a('a',2,2) and domcomp_a('a',2,2). behavior did not occur when using aggregates in next rules." )
  def test_dml_toy2( self ) :

    # specify input and output paths
    inputfile               = os.getcwd() + "/testFiles/toy2.ded"
    expected_iapyx_dml_path = "./testFiles/toy2.olg"

    self.comparison_workflow( inputfile, expected_iapyx_dml_path, None )


  #############
  #  DML TOY  #
  #############
  # tests rewriting the toy program
  #@unittest.skip( "working on different example" )
  def test_dml_toy( self ) :

    # specify input and output paths
    inputfile               = os.getcwd() + "/testFiles/toy.ded"
    expected_iapyx_dml_path = "./testFiles/toy.olg"

    self.comparison_workflow( inputfile, expected_iapyx_dml_path, None )


  #########################
  #  COMPARISON WORKFLOW  #
  #########################
  # defines iapyx dml comparison workflow
  def comparison_workflow( self, inputfile, expected_iapyx_dml_path, expected_eval_path ) :

    # --------------------------------------------------------------- #
    # testing set up.

    if os.path.isfile( "./IR.db" ) :
      logging.debug( "  COMPARISON WORKFLOW : removing rogue IR file." )
      os.remove( "./IR.db" )

    testDB = "./IR.db"
    IRDB    = sqlite3.connect( testDB )
    cursor  = IRDB.cursor()

    # --------------------------------------------------------------- #
    # reset counters for new test

    dedt.globalCounterReset()

    # --------------------------------------------------------------- #
    # runs through function to make sure it finishes with expected error

    # get argDict
    argDict = self.getArgDict( inputfile )

    # run translator
    programData = dedt.translateDedalus( argDict, cursor )

    # portray actual output program lines as a single string
    iapyx_results = self.getActualResults( programData[0] )

    if self.PRINT_STOP :
      print iapyx_results
      sys.exit( "print stop." )

    # ========================================================== #
    # IAPYX COMPARISON
    #
    # grab expected output results as a string

    if self.COMPARE_PROGS :
      expected_iapyx_results = None
      with open( expected_iapyx_dml_path, 'r' ) as expectedFile :
        expected_iapyx_results = expectedFile.read()

      self.assertEqual( iapyx_results, expected_iapyx_results )

    # ========================================================== #
    # EVALUATION COMPARISON

    self.evaluate( programData, expected_eval_path )

    # --------------------------------------------------------------- #
    #clean up testing

    IRDB.close()
    os.remove( testDB )


  ##############
  #  EVALUATE  #
  ##############
  # evaluate the datalog program using some datalog evaluator
  # return some data structure or storage location encompassing the evaluation results.
  def evaluate( self, programData, expected_eval_path ) :

    noOverlap = False

    results_array = c4_evaluator.runC4_wrapper( programData )

    # ----------------------------------------------------------------- #
    # convert results array into dictionary

    eval_results_dict = tools.getEvalResults_dict_c4( results_array )

    # ----------------------------------------------------------------- #
    # collect all pos/not_ rule pairs

    rule_pairs = self.getRulePairs( eval_results_dict )

    logging.debug( "  EVALUATE : rule_pairs = " + str( rule_pairs ) )

    # ----------------------------------------------------------------- #
    # make sure tables do not overlap

    self.assertFalse( self.hasOverlap( rule_pairs, eval_results_dict ) )

    # ----------------------------------------------------------------- #
    # make sure dml positive relation results are identical to molly
    # relation results

    if expected_eval_path :

      self.compare_evals( eval_results_dict, expected_eval_path )


  ###################
  #  COMPARE EVALS  #
  ###################
  # compare the actual evaluation results with the 
  # expected evaluation results.
  def compare_evals( self, eval_results_dict, expected_eval_path ) :

    # ----------------------------------------------------------------- #
    # get a dictionary of the expected results

    expected_results_array = []
    fo = open( expected_eval_path )
    for line in fo :
      line = line.rstrip()
      expected_results_array.append( line )
    fo.close()

    expected_eval_results_dict = tools.getEvalResults_dict_c4( expected_results_array )

    # ----------------------------------------------------------------- #
    # compare all positive tables (not prov)

    for rel_key in eval_results_dict :

      # ----------------------------------------------------------------- #
      # skip not_ rules, _prov rules, adom_ rules

      if rel_key.startswith( "not_" ) or \
         rel_key.startswith( "domcomp_" ) or \
         rel_key.startswith( "dom_" ) or \
         rel_key == "adom_string" or \
         rel_key == "adom_int" or \
         "_prov" in rel_key or \
         "_agg" in rel_key :

        pass

      # ----------------------------------------------------------------- #

      else :

        actual_eval   = eval_results_dict[ rel_key ]
        expected_eval = expected_eval_results_dict[ rel_key ]

        flag = True
        for expected_row in expected_eval :
          if not expected_row in actual_eval :
            logging.debug( "  COMPARE_EVALS : missing row : relation = " + rel_key + "\nexpected_row = " + str( expected_row ) + "\nactual_eval = " + str( actual_eval ) )
            flag = False
            break

        self.assertTrue( flag )


  #################
  #  HAS OVERLAP  #
  #################
  # make sure pos and not_pos tables do not overlap
  def hasOverlap( self, rule_pairs, eval_results_dict ) :

    for pair in rule_pairs :

      logging.debug( "  HAS OVERLAP : pair = " + str( pair ) )

      pos_results = eval_results_dict[ pair[0] ]
      not_results = eval_results_dict[ pair[1] ]

#      # check is too strong
#      logging.debug( "  HAS OVERLAP : pos_results :" )
#      for r in pos_results :
#        logging.debug( r )
#
#      logging.debug( "  HAS OVERLAP : not_results :" )
#      for r in not_results :
#        logging.debug( r )
#
#      if len( pos_results ) > 0 :
#        nonEmpty_pos = True
#      else :
#        nonEmpty_pos = False
#      self.assertTrue( nonEmpty_pos )
#
#      if len( not_results ) > 0 :
#        nonEmpty_not = True
#      else :
#        nonEmpty_not = False
#      self.assertTrue( nonEmpty_not )

      for pos_row in pos_results :
        if pos_row in not_results :
          logging.debug( "HAS OVERLAP : pos_row '" + str( pos_row ) + "' is in not_results:" )
          for not_row in not_results :
            logging.debug( "HAS OVERLAP : not_row " + str( not_row ) )
          return True

    return False


  ####################
  #  GET RULE PAIRS  #
  ####################
  # grab all pos/not_
  def getRulePairs( self, eval_results_dict ) :

    pair_list = []

    # pull out positive names
    for relName1 in eval_results_dict :

      if not relName1.startswith( "not_" ) and not "_prov" in relName1 :

        for relName2 in eval_results_dict :
  
          if not relName1 == relName2 :
            if relName2.startswith( "not_" ) and relName2[4:] == relName1 :
              pair_list.append( [ relName1, relName2 ] )

    return pair_list


  ##################
  #  MATCH EXISTS  #
  ##################
  # check if the iapyx_rule appears in the molly_line_array
  def matchExists( self, iapyx_rule, molly_line_array ) :

    logging.debug( "-------------------------------------------------------------" )
    logging.debug( "  MATCH EXISTS : iapyx_rule        = " + iapyx_rule )

    iapyx_goalName    = self.getGoalName( iapyx_rule )
    iapyx_goalAttList = self.getGoalAttList( iapyx_rule )
    iapyx_body        = self.getBody( iapyx_rule )

    logging.debug( "  MATCH EXISTS : iapyx_goalName    = " + iapyx_goalName )
    logging.debug( "  MATCH EXISTS : iapyx_goalAttList = " + str( iapyx_goalAttList ) )
    logging.debug( "  MATCH EXISTS : iapyx_body        = " + iapyx_body )

    for line in molly_line_array :

      if self.isRule( line ) :

        molly_goalName    = self.getGoalName( line )
        molly_goalAttList = self.getGoalAttList( line )
        molly_body        = self.getBody( line )
 
        logging.debug( "  MATCH EXISTS : molly_goalName    = " + molly_goalName )
        logging.debug( "  MATCH EXISTS : molly_goalAttList = " + str( molly_goalAttList ) )
        logging.debug( "  MATCH EXISTS : molly_body        = " + molly_body )

        # goal names and bodies match 
        if self.sameName( iapyx_goalName, molly_goalName ) :

          logging.debug( "  MATCH EXISTS : identical goalNames." )

          if self.sameBodies( iapyx_body, molly_body ) :

            logging.debug( "  MATCH EXISTS : identical goalNames." )

            # make sure all iapyx atts appear in the molly att list
            iapyx_match = False
            for iapyx_att in iapyx_goalAttList :
              if iapyx_att in molly_goalAttList :
                iapyx_match = True

            # make sure all molly atts appear in the iapyx att list
            molly_match = False
            for molly_att in molly_goalAttList :
              if molly_att in iapyx_goalAttList :
                molly_match = True

            if iapyx_match or molly_match :
              logging.debug( "  MATCH EXISTS : returning True" )
              return True

          else :
            logging.debug( "  MATCH EXISTS : different bodies : iapyx_body = " + iapyx_body + ", molly_body = " + molly_body  )

        else :
          logging.debug( "  MATCH EXISTS : different goalNames (sans _prov# appends) : iapyx_goalName = " + iapyx_goalName + ", molly_goalName = " + molly_goalName  )


    logging.debug( "  MATCH EXISTS : returning False" )
    return False


  #################
  #  SAME BODIES  #
  #################
  # separate subgoals and eqns in to separate lists.
  # make sure all elements appear in both lists.
  def sameBodies( self, body1, body2 ) :

    # compare eqn lists
    eqnList1 = self.getEqnList( body1 )
    eqnList2 = self.getEqnList( body2 )

    if len( eqnList1 ) == len( eqnList2 ) :
      eqnListLen = True
    else :
      eqnListLen = False

    sameEqns = False
    if eqnList1 == eqnList2 :
      sameEqns = True
    else :
      for e1 in eqnList1 :
        if e1 in eqnList2 :
          sameEqns = True

    # compare subgoal lists
    subgoalList1 = self.getSubgoalList( body1, eqnList1 )
    subgoalList2 = self.getSubgoalList( body2, eqnList2 )

    if len( subgoalList1 ) == len( subgoalList2 ) :
      subListLen = True
    else :
      subListLen = False

    sameSubgoals = False
    for e1 in subgoalList1 :
      if e1 in subgoalList2 :
        sameSubgoals = True

    logging.debug( "  SAME BODIES : eqnList1     = " + str( eqnList1 ) )
    logging.debug( "  SAME BODIES : eqnList2     = " + str( eqnList2 ) )
    logging.debug( "  SAME BODIES : subgoalList1 = " + str( subgoalList1 ) )
    logging.debug( "  SAME BODIES : subgoalList2 = " + str( subgoalList2 ) )
    logging.debug( "  SAME BODIES : subListLen   = " + str( subListLen ) )
    logging.debug( "  SAME BODIES : sameSubgoals = " + str( sameSubgoals ) )
    logging.debug( "  SAME BODIES : eqnListLen   = " + str( eqnListLen ) )
    logging.debug( "  SAME BODIES : sameEqns     = " + str( sameEqns ) )

    if subListLen and sameSubgoals and eqnListLen and sameEqns :
      return True
    else :
      return False


  ######################
  #  GET SUBGOAL LIST  #
  ######################
  # extract the list of subgoals from the given rule body
  def getSubgoalList( self, body, eqnList ) :

    # ========================================= #
    # replace eqn instances in line
    for eqn in eqnList :
      body = body.replace( eqn, "" )
  
    body = body.replace( ",,", "," )
  
    # ========================================= #
    # grab subgoals
  
    # grab indexes of commas separating subgoals
    indexList = self.getCommaIndexes( body )
  
    #print indexList
  
    # replace all subgoal-separating commas with a special character sequence
    tmp_body = ""
    for i in range( 0, len( body ) ) :
      if not i in indexList :
        tmp_body += body[i]
      else :
        tmp_body += "___SPLIT___HERE___"
    body = tmp_body
  
    # generate list of separated subgoals by splitting on the special
    # character sequence
    subgoalList = body.split( "___SPLIT___HERE___" )

    # remove empties
    tmp_subgoalList = []
    for sub in subgoalList :
      if not sub == "" :
        tmp_subgoalList.append( sub )
    subgoalList = tmp_subgoalList

    return subgoalList


  ##################
  #  GET EQN LIST  #
  ##################
  # extract the list of equations in the given rule body
  def getEqnList( self, body ) :

    body = body.split( "," )
  
    # get the complete list of eqns from the rule body
    eqnList = []
    for thing in body :
      if self.isEqn( thing ) :
        eqnList.append( thing )

    return eqnList


  #######################
  #  GET COMMA INDEXES  #
  #######################
  # given a rule body, get the indexes of commas separating subgoals.
  def getCommaIndexes( self, body ) :
  
    underscoreStr = self.getCommaIndexes_helper( body )
  
    indexList = []
    for i in range( 0, len( underscoreStr ) ) :
      if underscoreStr[i] == "," :
        indexList.append( i )
  
    return indexList
  
  
  ##############################
  #  GET COMMA INDEXES HELPER  #
  ##############################
  # replace all paren contents with underscores
  def getCommaIndexes_helper( self, body ) :
  
    # get the first occuring paren group
    nextParenGroup = "(" + re.search(r'\((.*?)\)',body).group(1) + ")"
  
    # replace the group with the same number of underscores in the body
    replacementStr = ""
    for i in range( 0, len(nextParenGroup)-2 ) :
      replacementStr += "_"
    replacementStr = "_" + replacementStr + "_" # use underscores to replace parentheses
  
    body = body.replace( nextParenGroup, replacementStr )
  
    # BASE CASE : no more parentheses
    if not "(" in body :
      return body
  
    # RECURSIVE CASE : yes more parentheses
    else :
      return self.getCommaIndexes_helper( body )


  ############
  #  IS EQN  #
  ############
  # check if input contents from the rule body is an equation
  def isEqn( self, sub ) :
  
    flag = False
    for op in eqnOps :
      if op in sub :
        flag = True
  
    return flag
  
  
  ###############
  #  SAME NAME  #
  ###############
  # extract the core name, without the '_prov' append, and compare
  # if rule name is an _vars#_prov, cut off at the end of the _vars append
  def sameName( self, name1, name2 ) :

    # extract the core name for the first input name
    if self.isAggsProvRewrite( name1 ) :
      endingStr = re.search( '(.*)_prov(.*)', name1 )
      coreName1 = name1.replace( endingStr.group(1), "" )
    elif self.isProvRewrite( name1 ) :
      coreName1 = name1.split( "_prov" )
      coreName1 = coreName1[:-1]
      coreName1 = "".join( coreName1 )
    else :
      coreName1 = name1

    # extract the core name for the second input name
    if self.isAggsProvRewrite( name2 ) :
      endingStr = re.search( '(.*)_prov(.*)', name2 )
      coreName2 = name1.replace( endingStr.group(1), "" )
    elif self.isProvRewrite( name2 ) :
      coreName2 = name2.split( "_prov" )
      coreName2 = coreName2[:-1]
      coreName2 = "".join( coreName2 )
    else :
      coreName2 = name2

    logging.debug( "  SAME NAME : coreName1 = " + coreName1 )
    logging.debug( "  SAME NAME : coreName2 = " + coreName2 )

    if coreName1 == coreName2 :
      logging.debug( "  SAME NAME : returning True" )
      return True
    else :
      logging.debug( "  SAME NAME : returning False" )
      return False


  ##########################
  #  IS AGGS PROV REWRITE  #
  ##########################
  # check if the input relation name is indicative of an aggregate provenance rewrite
  def isAggsProvRewrite( self, relationName ) :

    middleStr = re.search( '_vars(.*)_prov', relationName )

    if middleStr :
      if middleStr.group(1).isdigit() :
        if relationName.endswith( middleStr.group(1) ) :
          return True
        else :
          return False
      else :
        return False
    else :
      return False


  #####################
  #  IS PROV REWRITE  #
  #####################
  # check if the input relation name is indicative of an aggregate provenance rewrite
  def isProvRewrite( self, relationName ) :

    endingStr = re.search( '_prov(.*)', relationName )

    if endingStr :
      if endingStr.group(1).isdigit() :
        if relationName.endswith( endingStr.group(1) ) :
          return True
        else :
          return False
      else :
        return False
    else :
      return False


  ###################
  #  GET GOAL NAME  #
  ###################
  # extract the goal name from the input rule.
  def getGoalName( self, rule ) :

    logging.debug( "  GET GOAL NAME : rule     = " + rule )

    goalName = rule.split( "(", 1 )
    goalName = goalName[0]

    logging.debug( "  GET GOAL NAME : goalName = " + goalName )
    return goalName


  #######################
  #  GET GOAL ATT LIST  #
  #######################
  # extract the goal attribute list.
  def getGoalAttList( self, rule ) :

    attList = rule.split( ")", 1 )
    attList = attList[0]
    attList = attList.split( "(", 1 )
    attList = attList[1]
    attList = attList.split( "," )

    return attList


  ##############
  #  GET BODY  #
  ##############
  # extract the rule body.
  def getBody( self, rule ) :

    body = rule.split( ":-" )
    body = body[1]

    return body


  #############
  #  IS RULE  #
  #############
  # check if input program line denotes a rule
  def isRule( self, line ) :
    if ":-" in line :
      return True
    else :
      return False


  ###############
  #  GET ERROR  #
  ###############
  # extract error message from system info
  def getError( self, sysInfo ) :
    return str( sysInfo[1] )


  ########################
  #  GET ACTUAL RESULTS  #
  ########################
  def getActualResults( self, programLines ) :
    program_string  = "\n".join( programLines )
    program_string += "\n" # add extra newline to align with read() parsing
    return program_string


  ##################
  #  GET ARG DICT  #
  ##################
  def getArgDict( self, inputfile ) :

    # initialize
    argDict = {}

    # populate with unit test defaults
    argDict[ 'prov_diagrams' ]            = False
    argDict[ 'use_symmetry' ]             = False
    argDict[ 'crashes' ]                  = 0
    argDict[ 'solver' ]                   = None
    argDict[ 'disable_dot_rendering' ]    = False
    argDict[ 'settings' ]                 = "./settings_dml.ini"
    argDict[ 'negative_support' ]         = False
    argDict[ 'strategy' ]                 = None
    argDict[ 'file' ]                     = inputfile
    argDict[ 'EOT' ]                      = 4
    argDict[ 'find_all_counterexamples' ] = False
    argDict[ 'nodes' ]                    = [ "a", "b", "c" ]
    argDict[ 'evaluator' ]                = "c4"
    argDict[ 'EFF' ]                      = 2

    return argDict


  ###############################
  #  REPLACE SUBGOAL NEGATIONS  #
  ###############################
  # tests rewriting existing rules to replace 
  # instances of negated subgoal instances 
  # with derived not_rules
  #@unittest.skip( "working on different example" )
  def test_replaceSubgoalNegations( self ) :

    # --------------------------------------------------------------- #
    # set up test

    testDB  = "./IR.db"
    IRDB    = sqlite3.connect( testDB )
    cursor  = IRDB.cursor()
    dedt.createDedalusIRTables( cursor )

    # --------------------------------------------------------------- #
    # build test rule set

    ruleData_a0    = { "relationName": "a", \
                       "goalAttList":[ "X" ], \
                       "goalTimeArg":"", \
                       "subgoalListOfDicts": [ { "subgoalName":"b", \
                                                 "subgoalAttList":[ "X", "Z" ], \
                                                 "polarity":"", \
                                                 "subgoalTimeArg":"" } , \
                                               { "subgoalName":"c", \
                                                 "subgoalAttList":[ "Z", "_" ], \
                                                 "polarity":"notin", \
                                                 "subgoalTimeArg":"" } ], \
                       "eqnDict":{} }
    ruleData_b0    = { "relationName":"b", \
                       "goalAttList":[ "Att0", "Att1" ], \
                       "goalTimeArg":"", \
                       "subgoalListOfDicts": [ { "subgoalName":"d", \
                                                 "subgoalAttList":[ "Att0", "Att1", "P" ], \
                                                 "polarity":"", \
                                                 "subgoalTimeArg":"" }  , \
                                               { "subgoalName":"f", \
                                                 "subgoalAttList":[ "P" ], \
                                                 "polarity":"notin", \
                                                 "subgoalTimeArg":"" } ], \
                       "eqnDict":{} }
    ruleData_not_f = { "relationName": "not_f", \
                       "goalAttList":[ "X" ], \
                       "goalTimeArg":"", \
                       "subgoalListOfDicts": [ { "subgoalName":"b", \
                                                 "subgoalAttList":[ "X", "Z" ], \
                                                 "polarity":"", \
                                                 "subgoalTimeArg":"" } , \
                                               { "subgoalName":"c", \
                                                 "subgoalAttList":[ "Z", "_" ], \
                                                 "polarity":"notin", \
                                                 "subgoalTimeArg":"" } ], \
                       "eqnDict":{} }

    rid_a0    = tools.getIDFromCounters( "rid" )
    rid_b0    = tools.getIDFromCounters( "rid" )
    rid_noT_f = tools.getIDFromCounters( "rid" )

    rule_a0    = Rule.Rule( rid_a0, ruleData_a0, cursor )
    rule_b0    = Rule.Rule( rid_b0, ruleData_b0, cursor )
    rule_not_f = Rule.Rule( rid_b0, ruleData_not_f, cursor )

    ruleMeta = [ rule_a0, rule_b0, rule_not_f ]

    # --------------------------------------------------------------- #
    # get the targeted rule meta list

    targetRuleMeta = dml.replaceSubgoalNegations( ruleMeta )

    actual_ruleData = []
    for rule in targetRuleMeta :
      actual_ruleData.append( rule.ruleData )

    # --------------------------------------------------------------- #
    # check assertion

    expected_ruleData_a0    = { "relationName": "a", \
                                "goalAttList":[ "X" ], \
                                "goalTimeArg":"", \
                                "subgoalListOfDicts": [ { "subgoalName":"b", \
                                                          "subgoalAttList":[ "X", "Z" ], \
                                                          "polarity":"", \
                                                          "subgoalTimeArg":"" } , \
                                                        { "subgoalName":"c", \
                                                          "subgoalAttList":[ "Z", "_" ], \
                                                          "polarity":"notin", \
                                                          "subgoalTimeArg":"" } ], \
                                "eqnDict":{} }
    expected_ruleData_b0    = { "relationName":"b", \
                                "goalAttList":[ "Att0", "Att1" ], \
                                "goalTimeArg":"", \
                                "subgoalListOfDicts": [ { "subgoalName":"d", \
                                                          "subgoalAttList":[ "Att0", "Att1", "P" ], \
                                                          "polarity":"", \
                                                          "subgoalTimeArg":"" }  , \
                                                        { "subgoalName":"not_f", \
                                                          "subgoalAttList":[ "P" ], \
                                                          "polarity":"", \
                                                          "subgoalTimeArg":"" } ], \
                                "eqnDict":{} }
    expected_ruleData_not_f = { "relationName": "not_f", \
                                "goalAttList":[ "X" ], \
                                "goalTimeArg":"", \
                                "subgoalListOfDicts": [ { "subgoalName":"b", \
                                                          "subgoalAttList":[ "X", "Z" ], \
                                                          "polarity":"", \
                                                          "subgoalTimeArg":"" } , \
                                                        { "subgoalName":"c", \
                                                          "subgoalAttList":[ "Z", "_" ], \
                                                          "polarity":"notin", \
                                                          "subgoalTimeArg":"" } ], \
                                "eqnDict":{} }

    expected_ruleData = [ expected_ruleData_a0, expected_ruleData_b0, expected_ruleData_not_f ]

    self.assertEqual( actual_ruleData, expected_ruleData )

    # --------------------------------------------------------------- #
    # clean up testing
 
    IRDB.close()
    os.remove( testDB )


  #################################
  #  SET UNIQUE EXISTENTIAL VARS  #
  #################################
  # tests rewriting existing rules to ensure each 
  # rule per relation definition utilizes a unique 
  # set of existential variables
  #@unittest.skip( "working on different example" )
  def test_setUniqueExistentialVars( self ) :

    # --------------------------------------------------------------- #
    # set up test

    testDB  = "./IR.db"
    IRDB    = sqlite3.connect( testDB )
    cursor  = IRDB.cursor()
    dedt.createDedalusIRTables( cursor )

    # --------------------------------------------------------------- #
    # build test rule set

    ruleData_a0 = { "relationName": "a", \
                    "goalAttList":[ "X" ], \
                    "goalTimeArg":"", \
                    "subgoalListOfDicts": [ { "subgoalName":"b", \
                                              "subgoalAttList":[ "X", "Z" ], \
                                              "polarity":"", \
                                              "subgoalTimeArg":"" } , \
                                            { "subgoalName":"c", \
                                              "subgoalAttList":[ "Z", "_" ], \
                                              "polarity":"notin", \
                                              "subgoalTimeArg":"" } ], \
                    "eqnDict":{ "X==Z" : [ "X", "Z" ] } }
    ruleData_a1 = { "relationName": "a", \
                    "goalAttList":[ "X" ], \
                    "goalTimeArg":"", \
                    "subgoalListOfDicts": [ { "subgoalName":"e", \
                                              "subgoalAttList":[ "X", "Z" ], \
                                              "polarity":"", \
                                              "subgoalTimeArg":"" } , \
                                            { "subgoalName":"f", \
                                              "subgoalAttList":[ "X", "Z" ], \
                                              "polarity":"notin", \
                                              "subgoalTimeArg":"" } ], \
                    "eqnDict":{ "X<Z" : [ "X", "Z" ] } }
    ruleData_b0 = { "relationName":"b", \
                    "goalAttList":[ "Att0", "Att1" ], \
                    "goalTimeArg":"", \
                    "subgoalListOfDicts": [ { "subgoalName":"d", \
                                              "subgoalAttList":[ "Att0", "P" ], \
                                              "polarity":"", \
                                              "subgoalTimeArg":"" }  , \
                                            { "subgoalName":"e", \
                                              "subgoalAttList":[ "P", "Att1" ], \
                                              "polarity":"", \
                                              "subgoalTimeArg":"" } ], \
                    "eqnDict":{ "Att0==P" : [ "Att0", "P" ], "Att1>P" : [ "Att1", "P" ] } }
    ruleData_b1 = { "relationName":"b", \
                    "goalAttList":[ "Att0", "Att1" ], \
                    "goalTimeArg":"", \
                    "subgoalListOfDicts": [ { "subgoalName":"d", \
                                              "subgoalAttList":[ "Att0", "Att1", "P" ], \
                                              "polarity":"", \
                                              "subgoalTimeArg":"" }  , \
                                            { "subgoalName":"f", \
                                              "subgoalAttList":[ "P" ], \
                                              "polarity":"notin", \
                                              "subgoalTimeArg":"" } ], \
                    "eqnDict":{ "Att0<=P" : [ "Att0", "P" ], "Att1>=P" : [ "Att1", "P" ] } }

    rid_a0 = tools.getIDFromCounters( "rid" )
    rid_a1 = tools.getIDFromCounters( "rid" )
    rid_b0 = tools.getIDFromCounters( "rid" )
    rid_b1 = tools.getIDFromCounters( "rid" )

    rule_a0 = Rule.Rule( rid_a0, ruleData_a0, cursor )
    rule_a1 = Rule.Rule( rid_a1, ruleData_a1, cursor )
    rule_b0 = Rule.Rule( rid_b0, ruleData_b0, cursor )
    rule_b1 = Rule.Rule( rid_b1, ruleData_b1, cursor )

    ruleMeta = [ rule_a0, rule_a1, rule_b0, rule_b1 ]

    # --------------------------------------------------------------- #
    # get the targeted rule meta list

    targetRuleMeta = dml.setUniqueExistentialVars( ruleMeta )

    actual_ruleData = []
    for rule in targetRuleMeta :
      actual_ruleData.append( rule.ruleData )

    # --------------------------------------------------------------- #
    # check assertion

    eqnKey_a0   = "X==Z" + str( ruleMeta[0].rid )
    eqnVal_a0_Z = "Z" + str( ruleMeta[0].rid )
    eqnKey_a1   = "X<Z" + str( ruleMeta[1].rid )
    eqnVal_a1_Z = "Z" + str( ruleMeta[1].rid )
    eqnKey_b0_0   = "Att0==P" + str( ruleMeta[2].rid )
    eqnVal_b0_0_P = "P" + str( ruleMeta[2].rid )
    eqnKey_b0_1   = "Att1>P" + str( ruleMeta[2].rid )
    eqnVal_b0_1_P = "P" + str( ruleMeta[2].rid )
    eqnKey_b1_0   = "Att0<=P" + str( ruleMeta[3].rid )
    eqnVal_b1_0_P = "P" + str( ruleMeta[3].rid )
    eqnKey_b1_1   = "Att1>=P" + str( ruleMeta[3].rid )
    eqnVal_b1_1_P = "P" + str( ruleMeta[3].rid )

    expected_ruleData_a0 = { "relationName": "a", \
                             "goalAttList":[ "X" ], \
                             "goalTimeArg":"", \
                             "subgoalListOfDicts": [ { "subgoalName":"b", \
                                                       "subgoalAttList":[ "X", "Z" + str( ruleMeta[0].rid ) ], \
                                                       "polarity":"", \
                                                       "subgoalTimeArg":"" } , \
                                                     { "subgoalName":"c", \
                                                       "subgoalAttList":[ "Z" + str( ruleMeta[0].rid ), "_" ], \
                                                       "polarity":"notin", \
                                                       "subgoalTimeArg":"" } ], \
                             "eqnDict":{ eqnKey_a0 : [ "X", eqnVal_a0_Z ] } }
    expected_ruleData_a1 = { "relationName": "a", \
                             "goalAttList":[ "X" ], \
                             "goalTimeArg":"", \
                             "subgoalListOfDicts": [ { "subgoalName":"e", \
                                                       "subgoalAttList":[ "X", "Z" + str( ruleMeta[1].rid ) ], \
                                                       "polarity":"", \
                                                       "subgoalTimeArg":"" } , \
                                                     { "subgoalName":"f", \
                                                       "subgoalAttList":[ "X", "Z" + str( ruleMeta[1].rid ) ], \
                                                       "polarity":"notin", \
                                                       "subgoalTimeArg":"" } ], \
                             "eqnDict":{ eqnKey_a1 : [ "X", eqnVal_a1_Z ] } }
    expected_ruleData_b0 = { "relationName":"b", \
                             "goalAttList":[ "Att0", "Att1" ], \
                             "goalTimeArg":"", \
                             "subgoalListOfDicts": [ { "subgoalName":"d", \
                                                       "subgoalAttList":[ "Att0", "P" + str( ruleMeta[2].rid ) ], \
                                                       "polarity":"", \
                                                       "subgoalTimeArg":"" }  , \
                                                     { "subgoalName":"e", \
                                                       "subgoalAttList":[ "P" + str( ruleMeta[2].rid ), "Att1" ], \
                                                       "polarity":"", \
                                                       "subgoalTimeArg":"" } ], \
                             "eqnDict":{ eqnKey_b0_0 : [ "Att0", eqnVal_b0_0_P ], eqnKey_b0_1 : [ "Att1", eqnVal_b0_1_P ] } }
    expected_ruleData_b1 = { "relationName":"b", \
                             "goalAttList":[ "Att0", "Att1" ], \
                             "goalTimeArg":"", \
                             "subgoalListOfDicts": [ { "subgoalName":"d", \
                                                       "subgoalAttList":[ "Att0", "Att1", "P" + str( ruleMeta[3].rid ) ], \
                                                       "polarity":"", \
                                                       "subgoalTimeArg":"" }  , \
                                                     { "subgoalName":"f", \
                                                       "subgoalAttList":[ "P" + str( ruleMeta[3].rid ) ], \
                                                       "polarity":"notin", \
                                                       "subgoalTimeArg":"" } ], \
                             "eqnDict":{ eqnKey_b1_0 : [ "Att0", eqnVal_b1_0_P ], eqnKey_b1_1 : [ "Att1", eqnVal_b1_1_P ] } }

    expected_ruleData = [ expected_ruleData_a0, expected_ruleData_a1, expected_ruleData_b0, expected_ruleData_b1 ]

    self.assertEqual( actual_ruleData, expected_ruleData )

    # --------------------------------------------------------------- #
    # clean up testing

    IRDB.close()
    os.remove( testDB )


  ##########################
  #  SET UNIFORM ATT LIST  #
  ##########################
  # tests rewriting rules to ensure a uniform schema 
  # of universal variables per relation definition
  #@unittest.skip( "working on different example" )
  def test_setUniformAttList( self ) :

    # --------------------------------------------------------------- #
    # set up test

    testDB  = "./IR.db"
    IRDB    = sqlite3.connect( testDB )
    cursor  = IRDB.cursor()
    dedt.createDedalusIRTables( cursor )

    # --------------------------------------------------------------- #
    # build test rule set

    ruleData_a0 = { "relationName": "a", \
                    "goalAttList":[ "X" ], \
                    "goalTimeArg":"", \
                    "subgoalListOfDicts": [ { "subgoalName":"b", \
                                              "subgoalAttList":[ "X", "_" ], \
                                              "polarity":"", \
                                              "subgoalTimeArg":"" } , \
                                            { "subgoalName":"c", \
                                              "subgoalAttList":[ "X", "_" ], \
                                              "polarity":"notin", \
                                              "subgoalTimeArg":"" } ], \
                    "eqnDict":{} }
    ruleData_a1 = { "relationName": "a", \
                    "goalAttList":[ "X" ], \
                    "goalTimeArg":"", \
                    "subgoalListOfDicts": [ { "subgoalName":"d", \
                                              "subgoalAttList":[ "X", "X" ], \
                                              "polarity":"", \
                                              "subgoalTimeArg":"" } ], \
                    "eqnDict":{} }
    ruleData_b0 = { "relationName":"b", \
                    "goalAttList":[ "X1", "Y1" ], \
                    "goalTimeArg":"", \
                    "subgoalListOfDicts": [ { "subgoalName":"d", \
                                              "subgoalAttList":[ "X1", "Z" ], \
                                              "polarity":"", \
                                              "subgoalTimeArg":"" }  , \
                                            { "subgoalName":"e", \
                                              "subgoalAttList":[ "Z", "Y1" ], \
                                              "polarity":"", \
                                              "subgoalTimeArg":"" } ], \
                    "eqnDict":{ "X1==Y1" : [ "X1", "Y1" ] } }
    ruleData_b1 = { "relationName":"b", \
                    "goalAttList":[ "X2", "Y2" ], \
                    "goalTimeArg":"", \
                    "subgoalListOfDicts": [ { "subgoalName":"d", \
                                              "subgoalAttList":[ "X2", "Y2" ], \
                                              "polarity":"", \
                                              "subgoalTimeArg":"" }  , \
                                            { "subgoalName":"f", \
                                              "subgoalAttList":[ "Y2" ], \
                                              "polarity":"notin", \
                                              "subgoalTimeArg":"" } ], \
                    "eqnDict":{ "X2>Y2" : [ "X2", "Y2" ] } }

    rid_a0 = tools.getIDFromCounters( "rid" )
    rid_a1 = tools.getIDFromCounters( "rid" )
    rid_b0 = tools.getIDFromCounters( "rid" )
    rid_b1 = tools.getIDFromCounters( "rid" )

    rule_a0 = Rule.Rule( rid_a0, ruleData_a0, cursor )
    rule_a1 = Rule.Rule( rid_a1, ruleData_a1, cursor )
    rule_b0 = Rule.Rule( rid_b0, ruleData_b0, cursor )
    rule_b1 = Rule.Rule( rid_b1, ruleData_b1, cursor )

    ruleMeta = [ rule_a0, rule_a1, rule_b0, rule_b1 ]

    # --------------------------------------------------------------- #
    # get the targeted rule meta list

    targetRuleMeta = dml.setUniformAttList( ruleMeta, cursor )

    actual_ruleData = []
    for rule in targetRuleMeta :
      actual_ruleData.append( rule.ruleData )

    # --------------------------------------------------------------- #
    # check assertion

    expected_ruleData_a0 = { "relationName": "a", \
                             "goalAttList":[ "X" ], \
                             "goalTimeArg":"", \
                             "subgoalListOfDicts": [ { "subgoalName":"b", \
                                                       "subgoalAttList":[ "X", "_" ], \
                                                       "polarity":"", \
                                                       "subgoalTimeArg":"" } , \
                                                     { "subgoalName":"c", \
                                                       "subgoalAttList":[ "X", "_" ], \
                                                       "polarity":"notin", \
                                                       "subgoalTimeArg":"" } ], \
                             "eqnDict":{} }
    expected_ruleData_a1 = { "relationName": "a", \
                             "goalAttList":[ "X" ], \
                             "goalTimeArg":"", \
                             "subgoalListOfDicts": [ { "subgoalName":"d", \
                                                       "subgoalAttList":[ "X", "X" ], \
                                                       "polarity":"", \
                                                       "subgoalTimeArg":"" } ], \
                             "eqnDict":{} }
    expected_ruleData_b0 = { "relationName":"b", \
                             "goalAttList":[ "Att0", "Att1" ], \
                             "goalTimeArg":"", \
                             "subgoalListOfDicts": [ { "subgoalName":"d", \
                                                       "subgoalAttList":[ "Att0", "Z" ], \
                                                       "polarity":"", \
                                                       "subgoalTimeArg":"" }  , \
                                                     { "subgoalName":"e", \
                                                       "subgoalAttList":[ "Z", "Att1" ], \
                                                       "polarity":"", \
                                                       "subgoalTimeArg":"" } ], \
                             "eqnDict":{ "Att0==Att1" : [ "Att0", "Att1" ] } }
    expected_ruleData_b1 = { "relationName":"b", \
                             "goalAttList":[ "Att0", "Att1" ], \
                             "goalTimeArg":"", \
                             "subgoalListOfDicts": [ { "subgoalName":"d", \
                                                       "subgoalAttList":[ "Att0", "Att1" ], \
                                                       "polarity":"", \
                                                       "subgoalTimeArg":"" }  , \
                                                     { "subgoalName":"f", \
                                                       "subgoalAttList":[ "Att1" ], \
                                                       "polarity":"notin", \
                                                       "subgoalTimeArg":"" } ], \
                             "eqnDict":{ "Att0>Att1" : [ "Att0", "Att1" ] } }

    expected_ruleData = [ expected_ruleData_a0, expected_ruleData_a1, expected_ruleData_b0, expected_ruleData_b1 ]

    self.assertEqual( actual_ruleData, expected_ruleData )

    # --------------------------------------------------------------- #
    # clean up testing

    IRDB.close()
    os.remove( testDB )


  ##################################
  #  BUILD EXISTENTIAL VARS RULES  #
  ##################################
  # tests building existential domain rules
  #@unittest.skip( "working on different example" )
  def test_buildExistentialVarsRules( self ) :

    # --------------------------------------------------------------- #
    # set up test

    testDB  = "./IR.db"
    IRDB    = sqlite3.connect( testDB )
    cursor  = IRDB.cursor()
    dedt.createDedalusIRTables( cursor )

    # --------------------------------------------------------------- #
    # build test rule set

    ruleData_a = { "relationName": "a", \
                   "goalAttList":[ "X" ], \
                   "goalTimeArg":"", \
                   "subgoalListOfDicts": [ { "subgoalName":"b", \
                                             "subgoalAttList":[ "X", "_" ], \
                                             "polarity":"", \
                                             "subgoalTimeArg":"" } , \
                                           { "subgoalName":"c", \
                                             "subgoalAttList":[ "X", "_" ], \
                                             "polarity":"notin", \
                                             "subgoalTimeArg":"" } ], \
                   "eqnDict":{} }
    ruleData_b1 = { "relationName":"b", \
                    "goalAttList":[ "X", "Y" ], \
                    "goalTimeArg":"", \
                    "subgoalListOfDicts": [ { "subgoalName":"d", \
                                              "subgoalAttList":[ "X", "Z" ], \
                                              "polarity":"", \
                                              "subgoalTimeArg":"" }  , \
                                            { "subgoalName":"e", \
                                              "subgoalAttList":[ "Z", "Y" ], \
                                              "polarity":"", \
                                              "subgoalTimeArg":"" } ], \
                    "eqnDict":{} }
    ruleData_c1 = { "relationName": "c", \
                    "goalAttList":[ "X" ], \
                    "goalTimeArg":"", \
                    "subgoalListOfDicts": [ { "subgoalName":"d", \
                                              "subgoalAttList":[ "X", "Z" ], \
                                              "polarity":"", \
                                              "subgoalTimeArg":"" } , \
                                            { "subgoalName":"b", \
                                              "subgoalAttList":[ "Z", "_" ], \
                                              "polarity":"notin", \
                                              "subgoalTimeArg":"" } ], \
                    "eqnDict":{} }
    ruleData_c2 = { "relationName": "c", \
                    "goalAttList":[ "X" ], \
                    "goalTimeArg":"", \
                    "subgoalListOfDicts": [ { "subgoalName":"f", \
                                              "subgoalAttList":[ "X", "_" ], \
                                              "polarity":"", \
                                              "subgoalTimeArg":"" } ], \
                    "eqnDict":{} }

    rid_a  = tools.getIDFromCounters( "rid" )
    rid_b1 = tools.getIDFromCounters( "rid" )
    rid_c1 = tools.getIDFromCounters( "rid" )
    rid_c2 = tools.getIDFromCounters( "rid" )

    rule_a  = Rule.Rule( rid_a, ruleData_a, cursor )
    rule_b1 = Rule.Rule( rid_b1, ruleData_b1, cursor )
    rule_c1 = Rule.Rule( rid_c1, ruleData_c1, cursor )
    rule_c2 = Rule.Rule( rid_c2, ruleData_c2, cursor )

    ruleMeta = [ rule_a, rule_b1, rule_c1, rule_c2 ]

    # --------------------------------------------------------------- #
    # get the targeted rule meta list

    targetRuleMeta = dml.getRuleMetaSetsForRulesCorrespondingToNegatedSubgoals( ruleMeta, cursor )

    actual_existentialVarsRules_ruleData = []
    for ruleSet in targetRuleMeta :

      # get not_ name
      orig_name = ruleSet[0].ruleData[ "relationName" ]
      not_name  = "not_" + orig_name

      # get goal att list
      goalAttList = ruleSet[0].ruleData[ "goalAttList" ]

      # get goal time arg
      goalTimeArg = ""

      # build dom comp rule
      domcompRule = dml.buildDomCompRule( orig_name, goalAttList, ruleSet[0].rid, cursor )

      # build existential vars rules
      existentialVarsRules = dml.buildExistentialVarsRules( ruleSet, cursor )

      # collect ruleData for test
      for rule in existentialVarsRules :
        actual_existentialVarsRules_ruleData.append( rule.ruleData )

    # --------------------------------------------------------------- #
    # check assertion

    expected_dom_c_z_1 = { 'relationName': 'dom_c_z', \
                           'eqnDict': {}, \
                           'goalTimeArg': '', \
                           'subgoalListOfDicts': [{ 'polarity': '', \
                                                    'subgoalName': 'd', \
                                                    'subgoalAttList': ['_', 'Z'], \
                                                    'subgoalTimeArg': ''}, \
                                                  { 'polarity': '', \
                                                    'subgoalName': 'b', \
                                                    'subgoalAttList': ['Z', '_'], \
                                                    'subgoalTimeArg': ''}], \
                           'goalAttList': ['Z']}
    expected_dom_c_z_2 = { 'relationName': 'dom_c_z', \
                           'eqnDict': {}, \
                           'goalTimeArg': '', \
                           'subgoalListOfDicts': [{ 'polarity': '', \
                                                    'subgoalName': 'd', \
                                                    'subgoalAttList': ['_', 'Z'], \
                                                    'subgoalTimeArg': ''}, \
                                                  { 'polarity': 'notin', \
                                                    'subgoalName': 'b', \
                                                    'subgoalAttList': ['Z', '_'], \
                                                    'subgoalTimeArg': ''}], \
                           'goalAttList': ['Z']}
    expected_dom_c_z_3 = { 'relationName': 'dom_c_z', \
                           'eqnDict': {}, \
                           'goalTimeArg': '', \
                           'subgoalListOfDicts': [{ 'polarity': 'notin', \
                                                    'subgoalName': 'd', \
                                                    'subgoalAttList': ['_', 'Z'], \
                                                    'subgoalTimeArg': ''}, \
                                                  { 'polarity': '', \
                                                    'subgoalName': 'b', \
                                                    'subgoalAttList': ['Z', '_'], \
                                                    'subgoalTimeArg': ''}], \
                           'goalAttList': ['Z']}
    expected_dom_b_z_1 = { 'relationName': 'dom_b_z', \
                           'eqnDict': {}, \
                           'goalTimeArg': '', \
                           'subgoalListOfDicts': [{ 'polarity': '', \
                                                    'subgoalName': 'd', \
                                                    'subgoalAttList': ['_', 'Z'], \
                                                    'subgoalTimeArg': ''}, \
                                                  { 'polarity': '', \
                                                    'subgoalName': 'e', \
                                                    'subgoalAttList': ['Z', '_'], \
                                                    'subgoalTimeArg': ''}], \
                           'goalAttList': ['Z']}
    expected_dom_b_z_2 = { 'relationName': 'dom_b_z', \
                           'eqnDict': {}, \
                           'goalTimeArg': '', \
                           'subgoalListOfDicts': [{ 'polarity': '', \
                                                    'subgoalName': 'd', \
                                                    'subgoalAttList': ['_', 'Z'], \
                                                    'subgoalTimeArg': ''}, \
                                                  { 'polarity': 'notin', \
                                                    'subgoalName': 'e', \
                                                    'subgoalAttList': ['Z', '_'], \
                                                    'subgoalTimeArg': ''}], \
                           'goalAttList': ['Z']}
    expected_dom_b_z_3 = { 'relationName': 'dom_b_z', \
                           'eqnDict': {}, \
                           'goalTimeArg': '', \
                           'subgoalListOfDicts': [{ 'polarity': 'notin', \
                                                    'subgoalName': 'd', \
                                                    'subgoalAttList': ['_', 'Z'], \
                                                    'subgoalTimeArg': ''}, \
                                                  { 'polarity': '', \
                                                    'subgoalName': 'e', \
                                                    'subgoalAttList': ['Z', '_'], \
                                                    'subgoalTimeArg': ''}], \
                           'goalAttList': ['Z']}

    expected_existentialVarsRules_ruleData = [ expected_dom_c_z_1, expected_dom_c_z_2, expected_dom_c_z_3, expected_dom_b_z_1, expected_dom_b_z_2, expected_dom_b_z_3 ]

    self.assertEqual( actual_existentialVarsRules_ruleData, expected_existentialVarsRules_ruleData )

    # --------------------------------------------------------------- #
    # clean up testing

    IRDB.close()
    os.remove( testDB )


  ####################
  #  BUILD DOM COMP  #
  ####################
  # tests building domain complement rules
  #@unittest.skip( "working on different example" )
  def test_buildDomComp( self ) :

    # --------------------------------------------------------------- #
    # set up test

    testDB  = "./IR.db"
    IRDB    = sqlite3.connect( testDB )
    cursor  = IRDB.cursor()
    dedt.createDedalusIRTables( cursor )

    # --------------------------------------------------------------- #
    # build test rule set

    ruleData_a = { "relationName": "a", \
                   "goalAttList":[ "X" ], \
                   "goalTimeArg":"", \
                   "subgoalListOfDicts": [ { "subgoalName":"b", \
                                             "subgoalAttList":[ "X", "_" ], \
                                             "polarity":"", \
                                             "subgoalTimeArg":"" } , \
                                           { "subgoalName":"c", \
                                             "subgoalAttList":[ "X", "_" ], \
                                             "polarity":"notin", \
                                             "subgoalTimeArg":"" } ], \
                   "eqnDict":{} }
    ruleData_b1 = { "relationName":"b", \
                    "goalAttList":[ "X", "Y" ], \
                    "goalTimeArg":"", \
                    "subgoalListOfDicts": [ { "subgoalName":"d", \
                                              "subgoalAttList":[ "X", "Z" ], \
                                              "polarity":"", \
                                              "subgoalTimeArg":"" }  , \
                                            { "subgoalName":"e", \
                                              "subgoalAttList":[ "Z", "Y" ], \
                                              "polarity":"", \
                                              "subgoalTimeArg":"" } ], \
                    "eqnDict":{} }
    ruleData_c1 = { "relationName": "c", \
                    "goalAttList":[ "X" ], \
                    "goalTimeArg":"", \
                    "subgoalListOfDicts": [ { "subgoalName":"d", \
                                              "subgoalAttList":[ "X", "Z" ], \
                                              "polarity":"", \
                                              "subgoalTimeArg":"" } , \
                                            { "subgoalName":"b", \
                                              "subgoalAttList":[ "Z", "_" ], \
                                              "polarity":"notin", \
                                              "subgoalTimeArg":"" } ], \
                    "eqnDict":{} }
    ruleData_c2 = { "relationName": "c", \
                    "goalAttList":[ "X" ], \
                    "goalTimeArg":"", \
                    "subgoalListOfDicts": [ { "subgoalName":"f", \
                                              "subgoalAttList":[ "X", "_" ], \
                                              "polarity":"", \
                                              "subgoalTimeArg":"" } ], \
                    "eqnDict":{} }

    rid_a  = tools.getIDFromCounters( "rid" )
    rid_b1 = tools.getIDFromCounters( "rid" )
    rid_c1 = tools.getIDFromCounters( "rid" )
    rid_c2 = tools.getIDFromCounters( "rid" )

    rule_a  = Rule.Rule( rid_a, ruleData_a, cursor )
    rule_b1 = Rule.Rule( rid_b1, ruleData_b1, cursor )
    rule_c1 = Rule.Rule( rid_c1, ruleData_c1, cursor )
    rule_c2 = Rule.Rule( rid_c2, ruleData_c2, cursor )

    ruleMeta = [ rule_a, rule_b1, rule_c1, rule_c2 ]

    # --------------------------------------------------------------- #
    # get the targeted rule meta list

    targetRuleMeta = dml.getRuleMetaSetsForRulesCorrespondingToNegatedSubgoals( ruleMeta, cursor )

    actual_domcompRules_ruleData = []
    for ruleSet in targetRuleMeta :

      # get not_ name
      orig_name = ruleSet[0].ruleData[ "relationName" ]
      not_name  = "not_" + orig_name

      # get goal att list
      goalAttList = ruleSet[0].ruleData[ "goalAttList" ]

      # get goal time arg
      goalTimeArg = ""

      # build dom comp rule
      domcompRule = dml.buildDomCompRule( orig_name, goalAttList, ruleSet[0].rid, cursor )

      # collect ruleData for test
      actual_domcompRules_ruleData.append( domcompRule.ruleData )

    # --------------------------------------------------------------- #
    # check assertion

    # using adom_UNDEFINEDTYPE b/c hacky

    expected_domcomp_c = { 'relationName': 'domcomp_c', \
                           'subgoalListOfDicts': [{ 'polarity': '', \
                                                    'subgoalName': 'adom_UNDEFINEDTYPE', \
                                                    'subgoalAttList': ['X'], \
                                                    'subgoalTimeArg': ''}, \
                                                  { 'polarity': 'notin', \
                                                    'subgoalName': 'c', \
                                                    'subgoalAttList': ['X'], \
                                                    'subgoalTimeArg': ''}], \
                           'eqnDict': {}, \
                           'goalAttList': ['X'], \
                           'goalTimeArg': ''}

    expected_domcomp_b = { 'relationName': 'domcomp_b', \
                           'subgoalListOfDicts': [{ 'polarity': '', \
                                                    'subgoalName': 'adom_UNDEFINEDTYPE', \
                                                    'subgoalAttList': ['X'], \
                                                    'subgoalTimeArg': ''}, \
                                                  { 'polarity': '', \
                                                    'subgoalName': 'adom_UNDEFINEDTYPE', \
                                                    'subgoalAttList': ['Y'], \
                                                    'subgoalTimeArg': ''}, \
                                                  { 'polarity': 'notin', \
                                                    'subgoalName': 'b', \
                                                    'subgoalAttList': ['X','Y'], \
                                                    'subgoalTimeArg': ''}], \
                           'eqnDict': {}, \
                           'goalAttList': ['X','Y'], \
                           'goalTimeArg': ''}


    expected_domcompRules_ruleData = [ expected_domcomp_c, expected_domcomp_b ]

    self.assertEqual( actual_domcompRules_ruleData, expected_domcompRules_ruleData )

    # --------------------------------------------------------------- #
    # clean up testing

    IRDB.close()
    os.remove( testDB )


  ##############################
  #  DNF TO DATALOG WITH EQNS  #
  ##############################
  # tests the conversion of negated dnf fmlas into positive dnf fmlas
  #@unittest.skip( "working on different example" )
  def test_dnfToDatalog_withEqns( self ) :

    # --------------------------------------------------------------- #
    # set up test

    testDB  = "./IR.db"
    IRDB    = sqlite3.connect( testDB )
    cursor  = IRDB.cursor()
    dedt.createDedalusIRTables( cursor )

    # --------------------------------------------------------------- #
    # build test rule set

    ruleData_a = { "relationName": "a", \
                   "goalAttList":[ "X" ], \
                   "goalTimeArg":"", \
                   "subgoalListOfDicts": [ { "subgoalName":"b", \
                                             "subgoalAttList":[ "X", "_" ], \
                                             "polarity":"", \
                                             "subgoalTimeArg":"" } , \
                                           { "subgoalName":"c", \
                                             "subgoalAttList":[ "X", "_" ], \
                                             "polarity":"notin", \
                                             "subgoalTimeArg":"" } ], \
                   "eqnDict":{} }
    ruleData_b1 = { "relationName":"b", \
                    "goalAttList":[ "X", "Y" ], \
                    "goalTimeArg":"", \
                    "subgoalListOfDicts": [ { "subgoalName":"d", \
                                              "subgoalAttList":[ "X", "Z" ], \
                                              "polarity":"", \
                                              "subgoalTimeArg":"" }  , \
                                            { "subgoalName":"e", \
                                              "subgoalAttList":[ "Z", "Y" ], \
                                              "polarity":"", \
                                              "subgoalTimeArg":"" } ], \
                    "eqnDict":{ "X>Y": [ "X", "Y" ], "Z==Y": [ "Z", "Y" ] } }
    ruleData_c1 = { "relationName": "c", \
                    "goalAttList":[ "X" ], \
                    "goalTimeArg":"", \
                    "subgoalListOfDicts": [ { "subgoalName":"d", \
                                              "subgoalAttList":[ "X", "Z" ], \
                                              "polarity":"", \
                                              "subgoalTimeArg":"" } , \
                                            { "subgoalName":"b", \
                                              "subgoalAttList":[ "Z", "_" ], \
                                              "polarity":"notin", \
                                              "subgoalTimeArg":"" } ], \
                    "eqnDict":{ "X==Z": [ "X", "Z" ] } }
    ruleData_c2 = { "relationName": "c", \
                    "goalAttList":[ "X" ], \
                    "goalTimeArg":"", \
                    "subgoalListOfDicts": [ { "subgoalName":"f", \
                                              "subgoalAttList":[ "X", "_" ], \
                                              "polarity":"", \
                                              "subgoalTimeArg":"" } ], \
                    "eqnDict":{} }

    rid_a  = tools.getIDFromCounters( "rid" )
    rid_b1 = tools.getIDFromCounters( "rid" )
    rid_c1 = tools.getIDFromCounters( "rid" )
    rid_c2 = tools.getIDFromCounters( "rid" )

    rule_a  = Rule.Rule( rid_a, ruleData_a, cursor )
    rule_b1 = Rule.Rule( rid_b1, ruleData_b1, cursor )
    rule_c1 = Rule.Rule( rid_c1, ruleData_c1, cursor )
    rule_c2 = Rule.Rule( rid_c2, ruleData_c2, cursor )

    ruleMeta = [ rule_a, rule_b1, rule_c1, rule_c2 ]

    # --------------------------------------------------------------- #
    # get the targeted rule meta list

    targetRuleMeta = dml.getRuleMetaSetsForRulesCorrespondingToNegatedSubgoals( ruleMeta, cursor )

    actual_newDMRules_ruleData = []
    for ruleSet in targetRuleMeta :

      # get not_ name
      orig_name = ruleSet[0].ruleData[ "relationName" ]
      not_name  = "not_" + orig_name

      # get goal att list
      goalAttList = ruleSet[0].ruleData[ "goalAttList" ]

      # get goal time arg
      goalTimeArg = ""

      # build dom comp rule
      domcompRule = dml.buildDomCompRule( orig_name, goalAttList, ruleSet[0].rid, cursor )

      # build existential vars rules
      existentialVarsRules = dml.buildExistentialVarsRules( ruleSet, cursor )

      # get new dm rules
      negated_dnf_fmla = dml.generateBooleanFormula( ruleSet )
      pos_dnf_fmla     = str( dml.simplifyToDNF( negated_dnf_fmla ) )
      newDMRules       = dml.dnfToDatalog( not_name, goalAttList, goalTimeArg, pos_dnf_fmla, domcompRule, existentialVarsRules, ruleSet, cursor )

      # collect ruleData for test
      for rule in newDMRules :
        actual_newDMRules_ruleData.append( rule.ruleData )

    # --------------------------------------------------------------- #
    # check assertion

    # not_c = ~b AND f
    expected_rule1 = { 'relationName': 'not_c', \
                       'subgoalListOfDicts': [{ 'polarity': '', \
                                                'subgoalName': 'b', \
                                                'subgoalAttList': ['Z', '_'], \
                                                'subgoalTimeArg': ''}, \
                                              { 'polarity': 'notin', \
                                                'subgoalName': 'f', \
                                                'subgoalAttList': ['X', '_'], \
                                                'subgoalTimeArg': ''}, \
                                              { 'polarity': '', \
                                                'subgoalName': 'domcomp_c', \
                                                'subgoalAttList': ['X'], \
                                                'subgoalTimeArg': ''}, \
                                              { 'polarity': '', \
                                                'subgoalName': 'dom_c_z', \
                                                'subgoalAttList': ['Z'], \
                                                'subgoalTimeArg': ''}], \
                       'eqnDict':{ 'X==Z': [ 'X', 'Z' ] }, \
                       'goalAttList': ['X'], \
                       'goalTimeArg': ''}

    # not_c = ~d AND f
    expected_rule2 = { 'relationName': 'not_c', \
                       'subgoalListOfDicts': [{ 'polarity': 'notin', \
                                                'subgoalName': 'd', \
                                                'subgoalAttList': ['X', 'Z'], \
                                                'subgoalTimeArg': ''}, \
                                              { 'polarity': 'notin', \
                                                'subgoalName': 'f', \
                                                'subgoalAttList': ['X', '_'], \
                                                'subgoalTimeArg': ''}, \
                                              { 'polarity': '', \
                                                'subgoalName': 'domcomp_c', \
                                                'subgoalAttList': ['X'], \
                                                'subgoalTimeArg': ''}, \
                                              { 'polarity': '', \
                                                'subgoalName': 'dom_c_z', \
                                                'subgoalAttList': ['Z'], \
                                                'subgoalTimeArg': ''}], \
                       'eqnDict':{ 'X==Z': [ 'X', 'Z' ] }, \
                       'goalAttList': ['X'], \
                       'goalTimeArg': ''}

    # not_b = ~d
    expected_rule3 = { 'relationName': 'not_b', \
                       'subgoalListOfDicts': [{ 'polarity': 'notin', \
                                                'subgoalName': 'd', \
                                                'subgoalAttList': ['X', 'Z'], \
                                                'subgoalTimeArg': ''}, \
                                              { 'polarity': '', \
                                                'subgoalName': 'domcomp_b', \
                                                'subgoalAttList': ['X','Y'], \
                                                'subgoalTimeArg': ''}, \
                                              { 'polarity': '', \
                                                'subgoalName': 'dom_b_z', \
                                                'subgoalAttList': ['Z'], \
                                                'subgoalTimeArg': ''}], \
                       'eqnDict':{ 'X>Y': [ 'X', 'Y' ], 'Z==Y': [ 'Z', 'Y' ] }, \
                       'goalAttList': ['X', 'Y'], \
                       'goalTimeArg': ''}

    # not_b = ~e
    expected_rule4 = { 'relationName': 'not_b', \
                       'subgoalListOfDicts': [{ 'polarity': 'notin', \
                                                'subgoalName': 'e', \
                                                'subgoalAttList': ['Z', 'Y'], \
                                                'subgoalTimeArg': ''}, \
                                              { 'polarity': '', \
                                                'subgoalName': 'domcomp_b', \
                                                'subgoalAttList': ['X','Y'], \
                                                'subgoalTimeArg': ''}, \
                                              { 'polarity': '', \
                                                'subgoalName': 'dom_b_z', \
                                                'subgoalAttList': ['Z'], \
                                                'subgoalTimeArg': ''}], \
                       'eqnDict':{ 'X>Y': [ 'X', 'Y' ], 'Z==Y': [ 'Z', 'Y' ] }, \
                       'goalAttList': ['X', 'Y'], \
                       'goalTimeArg': ''}

    expected_newDMRules_ruleData = [ expected_rule1, expected_rule2, expected_rule3, expected_rule4  ]

    self.assertEqual( actual_newDMRules_ruleData, expected_newDMRules_ruleData )

    # --------------------------------------------------------------- #
    # clean up testing

    IRDB.close()
    os.remove( testDB )


  ####################
  #  DNF TO DATALOG  #
  ####################
  # tests the conversion of negated dnf fmlas into positive dnf fmlas
  #@unittest.skip( "working on different example" )
  def test_dnfToDatalog( self ) :

    # --------------------------------------------------------------- #
    # set up test

    testDB  = "./IR.db"
    IRDB    = sqlite3.connect( testDB )
    cursor  = IRDB.cursor()
    dedt.createDedalusIRTables( cursor )

    # --------------------------------------------------------------- #
    # build test rule set

    ruleData_a = { "relationName": "a", \
                   "goalAttList":[ "X" ], \
                   "goalTimeArg":"", \
                   "subgoalListOfDicts": [ { "subgoalName":"b", \
                                             "subgoalAttList":[ "X", "_" ], \
                                             "polarity":"", \
                                             "subgoalTimeArg":"" } , \
                                           { "subgoalName":"c", \
                                             "subgoalAttList":[ "X", "_" ], \
                                             "polarity":"notin", \
                                             "subgoalTimeArg":"" } ], \
                   "eqnDict":{} }
    ruleData_b1 = { "relationName":"b", \
                    "goalAttList":[ "X", "Y" ], \
                    "goalTimeArg":"", \
                    "subgoalListOfDicts": [ { "subgoalName":"d", \
                                              "subgoalAttList":[ "X", "Z" ], \
                                              "polarity":"", \
                                              "subgoalTimeArg":"" }  , \
                                            { "subgoalName":"e", \
                                              "subgoalAttList":[ "Z", "Y" ], \
                                              "polarity":"", \
                                              "subgoalTimeArg":"" } ], \
                    "eqnDict":{} }
    ruleData_c1 = { "relationName": "c", \
                    "goalAttList":[ "X" ], \
                    "goalTimeArg":"", \
                    "subgoalListOfDicts": [ { "subgoalName":"d", \
                                              "subgoalAttList":[ "X", "Z" ], \
                                              "polarity":"", \
                                              "subgoalTimeArg":"" } , \
                                            { "subgoalName":"b", \
                                              "subgoalAttList":[ "Z", "_" ], \
                                              "polarity":"notin", \
                                              "subgoalTimeArg":"" } ], \
                    "eqnDict":{} }
    ruleData_c2 = { "relationName": "c", \
                    "goalAttList":[ "X" ], \
                    "goalTimeArg":"", \
                    "subgoalListOfDicts": [ { "subgoalName":"f", \
                                              "subgoalAttList":[ "X", "_" ], \
                                              "polarity":"", \
                                              "subgoalTimeArg":"" } ], \
                    "eqnDict":{} }

    rid_a  = tools.getIDFromCounters( "rid" )
    rid_b1 = tools.getIDFromCounters( "rid" )
    rid_c1 = tools.getIDFromCounters( "rid" )
    rid_c2 = tools.getIDFromCounters( "rid" )

    rule_a  = Rule.Rule( rid_a, ruleData_a, cursor )
    rule_b1 = Rule.Rule( rid_b1, ruleData_b1, cursor )
    rule_c1 = Rule.Rule( rid_c1, ruleData_c1, cursor )
    rule_c2 = Rule.Rule( rid_c2, ruleData_c2, cursor )

    ruleMeta = [ rule_a, rule_b1, rule_c1, rule_c2 ]

    # --------------------------------------------------------------- #
    # get the targeted rule meta list

    targetRuleMeta = dml.getRuleMetaSetsForRulesCorrespondingToNegatedSubgoals( ruleMeta, cursor )

    actual_newDMRules_ruleData = []
    for ruleSet in targetRuleMeta :

      # get not_ name
      orig_name = ruleSet[0].ruleData[ "relationName" ]
      not_name  = "not_" + orig_name

      # get goal att list
      goalAttList = ruleSet[0].ruleData[ "goalAttList" ]

      # get goal time arg
      goalTimeArg = ""

      # build dom comp rule
      domcompRule = dml.buildDomCompRule( orig_name, goalAttList, ruleSet[0].rid, cursor )

      # build existential vars rules
      existentialVarsRules = dml.buildExistentialVarsRules( ruleSet, cursor )

      # get new dm rules
      negated_dnf_fmla = dml.generateBooleanFormula( ruleSet )
      pos_dnf_fmla     = str( dml.simplifyToDNF( negated_dnf_fmla ) )
      newDMRules       = dml.dnfToDatalog( not_name, goalAttList, goalTimeArg, pos_dnf_fmla, domcompRule, existentialVarsRules, ruleSet, cursor )

      # collect ruleData for test
      for rule in newDMRules :
        actual_newDMRules_ruleData.append( rule.ruleData )

    # --------------------------------------------------------------- #
    # check assertion

    # not_c = ~b AND f
    expected_rule1 = { 'relationName': 'not_c', \
                       'subgoalListOfDicts': [{ 'polarity': '', \
                                                'subgoalName': 'b', \
                                                'subgoalAttList': ['Z', '_'], \
                                                'subgoalTimeArg': ''}, \
                                              { 'polarity': 'notin', \
                                                'subgoalName': 'f', \
                                                'subgoalAttList': ['X', '_'], \
                                                'subgoalTimeArg': ''}, \
                                              { 'polarity': '', \
                                                'subgoalName': 'domcomp_c', \
                                                'subgoalAttList': ['X'], \
                                                'subgoalTimeArg': ''}, \
                                              { 'polarity': '', \
                                                'subgoalName': 'dom_c_z', \
                                                'subgoalAttList': ['Z'], \
                                                'subgoalTimeArg': ''}], \
                       'eqnDict': {}, \
                       'goalAttList': ['X'], \
                       'goalTimeArg': ''}

    # not_c = ~d AND f
    expected_rule2 = { 'relationName': 'not_c', \
                       'subgoalListOfDicts': [{ 'polarity': 'notin', \
                                                'subgoalName': 'd', \
                                                'subgoalAttList': ['X', 'Z'], \
                                                'subgoalTimeArg': ''}, \
                                              { 'polarity': 'notin', \
                                                'subgoalName': 'f', \
                                                'subgoalAttList': ['X', '_'], \
                                                'subgoalTimeArg': ''}, \
                                              { 'polarity': '', \
                                                'subgoalName': 'domcomp_c', \
                                                'subgoalAttList': ['X'], \
                                                'subgoalTimeArg': ''}, \
                                              { 'polarity': '', \
                                                'subgoalName': 'dom_c_z', \
                                                'subgoalAttList': ['Z'], \
                                                'subgoalTimeArg': ''}], \
                       'eqnDict': {}, \
                       'goalAttList': ['X'], \
                       'goalTimeArg': ''}

    # not_b = ~d
    expected_rule3 = { 'relationName': 'not_b', \
                       'subgoalListOfDicts': [{ 'polarity': 'notin', \
                                                'subgoalName': 'd', \
                                                'subgoalAttList': ['X', 'Z'], \
                                                'subgoalTimeArg': ''}, \
                                              { 'polarity': '', \
                                                'subgoalName': 'domcomp_b', \
                                                'subgoalAttList': ['X','Y'], \
                                                'subgoalTimeArg': ''}, \
                                              { 'polarity': '', \
                                                'subgoalName': 'dom_b_z', \
                                                'subgoalAttList': ['Z'], \
                                                'subgoalTimeArg': ''}], \
                       'eqnDict': {}, \
                       'goalAttList': ['X', 'Y'], \
                       'goalTimeArg': ''}

    # not_b = ~e
    expected_rule4 = { 'relationName': 'not_b', \
                       'subgoalListOfDicts': [{ 'polarity': 'notin', \
                                                'subgoalName': 'e', \
                                                'subgoalAttList': ['Z', 'Y'], \
                                                'subgoalTimeArg': ''}, \
                                              { 'polarity': '', \
                                                'subgoalName': 'domcomp_b', \
                                                'subgoalAttList': ['X','Y'], \
                                                'subgoalTimeArg': ''}, \
                                              { 'polarity': '', \
                                                'subgoalName': 'dom_b_z', \
                                                'subgoalAttList': ['Z'], \
                                                'subgoalTimeArg': ''}], \
                       'eqnDict': {}, \
                       'goalAttList': ['X', 'Y'], \
                       'goalTimeArg': ''}

    expected_newDMRules_ruleData = [ expected_rule1, expected_rule2, expected_rule3, expected_rule4  ]

    self.assertEqual( actual_newDMRules_ruleData, expected_newDMRules_ruleData )

    # --------------------------------------------------------------- #
    # clean up testing

    IRDB.close()
    os.remove( testDB )


  #####################
  #  SIMPLIFY TO DNF  #
  #####################
  # tests the conversion of negated dnf fmlas into positive dnf fmlas
  #@unittest.skip( "working on different example" )
  def test_simplify_to_dnf( self ) :

    # --------------------------------------------------------------- #
    # set up test

    testDB = "./IR.db"
    IRDB    = sqlite3.connect( testDB )
    cursor  = IRDB.cursor()
    dedt.createDedalusIRTables( cursor )

    # --------------------------------------------------------------- #
    # build test rule set

    ruleData_a = { "relationName": "a", \
                   "goalAttList":[ "X" ], \
                   "goalTimeArg":"", \
                   "subgoalListOfDicts": [ { "subgoalName":"b", \
                                             "subgoalAttList":[ "X", "_" ], \
                                             "polarity":"", \
                                             "subgoalTimeArg":"" } , \
                                           { "subgoalName":"c", \
                                             "subgoalAttList":[ "X", "_" ], \
                                             "polarity":"notin", \
                                             "subgoalTimeArg":"" } ], \
                   "eqnDict":{} }
    ruleData_b1 = { "relationName":"b", \
                    "goalAttList":[ "X", "Y" ], \
                    "goalTimeArg":"", \
                    "subgoalListOfDicts": [ { "subgoalName":"d", \
                                              "subgoalAttList":[ "X", "Z" ], \
                                              "polarity":"", \
                                              "subgoalTimeArg":"" }  , \
                                            { "subgoalName":"e", \
                                              "subgoalAttList":[ "Z", "Y" ], \
                                              "polarity":"", \
                                              "subgoalTimeArg":"" } ], \
                    "eqnDict":{} }
    ruleData_c1 = { "relationName": "c", \
                    "goalAttList":[ "X" ], \
                    "goalTimeArg":"", \
                    "subgoalListOfDicts": [ { "subgoalName":"d", \
                                              "subgoalAttList":[ "X", "Z" ], \
                                              "polarity":"", \
                                              "subgoalTimeArg":"" } , \
                                            { "subgoalName":"b", \
                                              "subgoalAttList":[ "Z", "_" ], \
                                              "polarity":"notin", \
                                              "subgoalTimeArg":"" } ], \
                    "eqnDict":{} }
    ruleData_c2 = { "relationName": "c", \
                    "goalAttList":[ "X" ], \
                    "goalTimeArg":"", \
                    "subgoalListOfDicts": [ { "subgoalName":"f", \
                                              "subgoalAttList":[ "X", "_" ], \
                                              "polarity":"", \
                                              "subgoalTimeArg":"" } ], \
                    "eqnDict":{} }

    rid_a  = tools.getIDFromCounters( "rid" )
    rid_b1 = tools.getIDFromCounters( "rid" )
    rid_c1 = tools.getIDFromCounters( "rid" )
    rid_c2 = tools.getIDFromCounters( "rid" )

    rule_a  = Rule.Rule( rid_a, ruleData_a, cursor )
    rule_b1 = Rule.Rule( rid_b1, ruleData_b1, cursor )
    rule_c1 = Rule.Rule( rid_c1, ruleData_c1, cursor )
    rule_c2 = Rule.Rule( rid_c2, ruleData_c2, cursor )

    ruleMeta = [ rule_a, rule_b1, rule_c1, rule_c2 ]

    # --------------------------------------------------------------- #
    # get the targeted rule meta list

    targetRuleMeta = dml.getRuleMetaSetsForRulesCorrespondingToNegatedSubgoals( ruleMeta, cursor )

    actual_pos_dnf_fmlas = []
    for ruleSet in targetRuleMeta :
      negated_dnf_fmla = dml.generateBooleanFormula( ruleSet )
      actual_pos_dnf_fmlas.append( str( dml.simplifyToDNF( negated_dnf_fmla ) ) )

    # --------------------------------------------------------------- #
    # check assertion

    expected_pos_dnf_fmlas = ["(INDX0_INDX1 & ~INDX1_INDX0) | (~INDX0_INDX0 & ~INDX1_INDX0)", "~INDX0_INDX0 | ~INDX0_INDX1"]

    self.assertEqual( actual_pos_dnf_fmlas, expected_pos_dnf_fmlas )

    # --------------------------------------------------------------- #
    # clean up testing

    IRDB.close()
    os.remove( testDB )


  ###########################
  #  GENERATE BOOLEAN FMLA  #
  ###########################
  # tests the generation of boolean fmlas in dnf from
  # the collective subgoals of a relation definition in datalog
  #@unittest.skip( "working on different example" )
  def test_generateBooleanFormula( self ) :

    # --------------------------------------------------------------- #
    # set up test

    testDB = "./IR.db"
    IRDB    = sqlite3.connect( testDB )
    cursor  = IRDB.cursor()
    dedt.createDedalusIRTables( cursor )

    # --------------------------------------------------------------- #
    # build test rule set

    ruleData_a = { "relationName": "a", \
                   "goalAttList":[ "X" ], \
                   "goalTimeArg":"", \
                   "subgoalListOfDicts": [ { "subgoalName":"b", \
                                             "subgoalAttList":[ "X", "_" ], \
                                             "polarity":"", \
                                             "subgoalTimeArg":"" } , \
                                           { "subgoalName":"c", \
                                             "subgoalAttList":[ "X", "_" ], \
                                             "polarity":"notin", \
                                             "subgoalTimeArg":"" } ], \
                   "eqnDict":{} }
    ruleData_b1 = { "relationName":"b", \
                    "goalAttList":[ "X", "Y" ], \
                    "goalTimeArg":"", \
                    "subgoalListOfDicts": [ { "subgoalName":"d", \
                                              "subgoalAttList":[ "X", "Z" ], \
                                              "polarity":"", \
                                              "subgoalTimeArg":"" }  , \
                                            { "subgoalName":"e", \
                                              "subgoalAttList":[ "Z", "Y" ], \
                                              "polarity":"", \
                                              "subgoalTimeArg":"" } ], \
                    "eqnDict":{} }
    ruleData_c1 = { "relationName": "c", \
                    "goalAttList":[ "X" ], \
                    "goalTimeArg":"", \
                    "subgoalListOfDicts": [ { "subgoalName":"d", \
                                              "subgoalAttList":[ "X", "Z" ], \
                                              "polarity":"", \
                                              "subgoalTimeArg":"" } , \
                                            { "subgoalName":"b", \
                                              "subgoalAttList":[ "Z", "_" ], \
                                              "polarity":"notin", \
                                              "subgoalTimeArg":"" } ], \
                    "eqnDict":{} }
    ruleData_c2 = { "relationName": "c", \
                    "goalAttList":[ "X" ], \
                    "goalTimeArg":"", \
                    "subgoalListOfDicts": [ { "subgoalName":"f", \
                                              "subgoalAttList":[ "X", "_" ], \
                                              "polarity":"", \
                                              "subgoalTimeArg":"" } ], \
                    "eqnDict":{} }

    rid_a  = tools.getIDFromCounters( "rid" )
    rid_b1 = tools.getIDFromCounters( "rid" )
    rid_c1 = tools.getIDFromCounters( "rid" )
    rid_c2 = tools.getIDFromCounters( "rid" )

    rule_a  = Rule.Rule( rid_a, ruleData_a, cursor )
    rule_b1 = Rule.Rule( rid_b1, ruleData_b1, cursor )
    rule_c1 = Rule.Rule( rid_c1, ruleData_c1, cursor )
    rule_c2 = Rule.Rule( rid_c2, ruleData_c2, cursor )

    ruleMeta = [ rule_a, rule_b1, rule_c1, rule_c2 ]

    # --------------------------------------------------------------- #
    # get the targeted rule meta list

    targetRuleMeta = dml.getRuleMetaSetsForRulesCorrespondingToNegatedSubgoals( ruleMeta, cursor )

    actualFmlas = []
    for ruleSet in targetRuleMeta :
      actualFmlas.append( dml.generateBooleanFormula( ruleSet ) )

    # --------------------------------------------------------------- #
    # check assertion

    expectedFmlas = ['~((INDX0_INDX0 & ~INDX0_INDX1) | (INDX1_INDX0))', '~((INDX0_INDX0 & INDX0_INDX1))']

    self.assertEqual( actualFmlas, expectedFmlas )

    # --------------------------------------------------------------- #
    # clean up testing

    IRDB.close()
    os.remove( testDB )


  ###########################################################################
  #  GENERATE RULE META SETS FOR RULES CORRESPONDING TO NEGATED SUBGOALS 2  #
  ###########################################################################
  # tests the collection of rule meta sets for rules corresponding
  # to negated subgoals in the program
  # tests collection of rules across two sets
  #@unittest.skip( "working on different example" )
  def test_getRuleMetaSetsForRulesCorrespondingToNegatedSubgoals_2( self ) :

    # --------------------------------------------------------------- #
    # set up test

    testDB = "./IR.db"
    IRDB    = sqlite3.connect( testDB )
    cursor  = IRDB.cursor()
    dedt.createDedalusIRTables( cursor )

    # --------------------------------------------------------------- #
    # build test rule set

    ruleData_a = { "relationName": "a", \
                   "goalAttList":[ "X" ], \
                   "goalTimeArg":"", \
                   "subgoalListOfDicts": [ { "subgoalName":"b", \
                                             "subgoalAttList":[ "X", "_" ], \
                                             "polarity":"", \
                                             "subgoalTimeArg":"" } , \
                                           { "subgoalName":"c", \
                                             "subgoalAttList":[ "X", "_" ], \
                                             "polarity":"notin", \
                                             "subgoalTimeArg":"" } ], \
                   "eqnDict":{} }
    ruleData_b1 = { "relationName":"b", \
                    "goalAttList":[ "X", "Y" ], \
                    "goalTimeArg":"", \
                    "subgoalListOfDicts": [ { "subgoalName":"d", \
                                              "subgoalAttList":[ "X", "Z" ], \
                                              "polarity":"", \
                                              "subgoalTimeArg":"" }  , \
                                            { "subgoalName":"e", \
                                              "subgoalAttList":[ "Z", "Y" ], \
                                              "polarity":"", \
                                              "subgoalTimeArg":"" } ], \
                    "eqnDict":{} }
    ruleData_c1 = { "relationName": "c", \
                    "goalAttList":[ "X" ], \
                    "goalTimeArg":"", \
                    "subgoalListOfDicts": [ { "subgoalName":"d", \
                                              "subgoalAttList":[ "X", "Z" ], \
                                              "polarity":"", \
                                              "subgoalTimeArg":"" } , \
                                            { "subgoalName":"b", \
                                              "subgoalAttList":[ "Z", "_" ], \
                                              "polarity":"notin", \
                                              "subgoalTimeArg":"" } ], \
                    "eqnDict":{} }
    ruleData_c2 = { "relationName": "c", \
                    "goalAttList":[ "X" ], \
                    "goalTimeArg":"", \
                    "subgoalListOfDicts": [ { "subgoalName":"f", \
                                              "subgoalAttList":[ "X", "_" ], \
                                              "polarity":"", \
                                              "subgoalTimeArg":"" } ], \
                    "eqnDict":{} }

    rid_a  = tools.getIDFromCounters( "rid" )
    rid_b1 = tools.getIDFromCounters( "rid" )
    rid_c1 = tools.getIDFromCounters( "rid" )
    rid_c2 = tools.getIDFromCounters( "rid" )

    rule_a  = Rule.Rule( rid_a, ruleData_a, cursor )
    rule_b1 = Rule.Rule( rid_b1, ruleData_b1, cursor )
    rule_c1 = Rule.Rule( rid_c1, ruleData_c1, cursor )
    rule_c2 = Rule.Rule( rid_c2, ruleData_c2, cursor )

    ruleMeta = [ rule_a, rule_b1, rule_c1, rule_c2 ]

    # --------------------------------------------------------------- #
    # get the targeted rule meta list

    targetRuleMeta = dml.getRuleMetaSetsForRulesCorrespondingToNegatedSubgoals( ruleMeta, cursor )

    actualTargetRuleData = []
    for ruleSet in targetRuleMeta :
      ruleDataSet = []
      for rule in ruleSet :
        ruleDataSet.append( rule.ruleData )
      actualTargetRuleData.append( ruleDataSet )

    # --------------------------------------------------------------- #
    # check assertion

    expectedRuleData = [ [ ruleData_c1, ruleData_c2 ], [ ruleData_b1 ] ]

    self.assertEqual( actualTargetRuleData, expectedRuleData )

    # --------------------------------------------------------------- #
    # clean up testing

    IRDB.close()
    os.remove( testDB )


  ######################################################################
  #  GET RULE META SETS FOR RULES CORRESPONDING TO NEGATED SUBGOALS 1  #
  ######################################################################
  # tests the collection of rule meta for rules corresponding
  # to negated subgoals in the program
  # one rule set
  #@unittest.skip( "working on different example" )
  def test_getRuleMetaSetsForRulesCorrespondingToNegatedSubgoals_1( self ) :

    # --------------------------------------------------------------- #
    # set up test

    testDB = "./IR.db"
    IRDB    = sqlite3.connect( testDB )
    cursor  = IRDB.cursor()
    dedt.createDedalusIRTables( cursor )

    # --------------------------------------------------------------- #
    # build test rule set

    ruleData1 = { "relationName":"a", \
                  "goalAttList":[ "X" ], \
                  "goalTimeArg":"", \
                  "subgoalListOfDicts": [ { "subgoalName":"c", \
                                            "subgoalAttList":[ "X", "_" ], \
                                            "polarity":"", \
                                            "subgoalTimeArg":"" } ], \
                  "eqnDict":{} }
    ruleData2 = { "relationName": "b", \
                  "goalAttList":[ "X" ], \
                  "goalTimeArg":"", \
                  "subgoalListOfDicts": [ { "subgoalName":"c", \
                                            "subgoalAttList":[ "X", "_" ], \
                                            "polarity":"", \
                                            "subgoalTimeArg":"" } , \
                                          { "subgoalName":"a", \
                                            "subgoalAttList":[ "X", "_" ], \
                                            "polarity":"notin", \
                                            "subgoalTimeArg":"" } ], \
                  "eqnDict":{} }

    rid1 = tools.getIDFromCounters( "rid" )
    rid2 = tools.getIDFromCounters( "rid" )

    rule1 = Rule.Rule( rid1, ruleData1, cursor )
    rule2 = Rule.Rule( rid2, ruleData2, cursor )

    ruleMeta = [ rule1, rule2 ]

    # --------------------------------------------------------------- #
    # get the targeted rule meta list

    targetRuleMeta = dml.getRuleMetaSetsForRulesCorrespondingToNegatedSubgoals( ruleMeta, cursor )

    actualTargetRuleData = targetRuleMeta[0][0].ruleData # should yield only one rule in one rule set

    # --------------------------------------------------------------- #
    # check assertion

    expectedRuleData = ruleData1

    self.assertEqual( actualTargetRuleData, expectedRuleData )

    # --------------------------------------------------------------- #
    # clean up testing

    IRDB.close()
    os.remove( testDB )


  ################
  #  BUILD ADOM  #
  ################
  # tests build adom on a simple set of fact instances
  #@unittest.skip( "working on different example" )
  def test_buildAdom( self ) :

    # --------------------------------------------------------------- #
    # set up test

    testDB = "./IR.db"
    IRDB    = sqlite3.connect( testDB )
    cursor  = IRDB.cursor()
    dedt.createDedalusIRTables( cursor )

    # --------------------------------------------------------------- #
    # build test fact set

    #factData1 = { "relationName":'a', "dataList":[ 1, "2", 3 ], "factTimeArg":"" } # fails. need to be smarter about recognizing numeric strings.
    factData1 = { "relationName":'a', "dataList":[ 1, "str2", 3 ], "factTimeArg":"" }
    factData2 = { "relationName":'b', "dataList":[ "str1", "str2", 1, 2 ], "factTimeArg":"" }

    fid1 = tools.getIDFromCounters( "fid" )
    fid2 = tools.getIDFromCounters( "fid" )

    fact1 = Fact.Fact( fid1, factData1, cursor )
    fact2 = Fact.Fact( fid2, factData2, cursor )

    factMeta = [ fact1, fact2 ]

    # --------------------------------------------------------------- #
    # create adom rules

    adomRules = dml.buildAdom( factMeta, cursor )

    actualAdomRuleData = []
    for rule in adomRules :
      logging.debug( "  TEST BUILD ADOM : actual rule with data = " + str( rule.ruleData ) )
      actualAdomRuleData.append( rule.ruleData )

    # --------------------------------------------------------------- #
    # check assertion

    expected_a0 = { "relationName":"adom_int", \
                    "goalAttList":[ "T" ], \
                    "goalTimeArg":"", 
                    "subgoalListOfDicts":[ { "subgoalName":"a", \
                                             "subgoalAttList":[ "T", "_", "_" ], \
                                             "polarity":"", \
                                             "subgoalTimeArg":"" } ], \
                    "eqnDict":{} }
    #expected_a1 = { "relationName":"adom_str", \
    #                "goalAttList":[ "T" ], \
    #                "goalTimeArg":"", 
    #                "subgoalListOfDicts":[ { "subgoalName":"a", \
    #                                         "subgoalAttList":[ "_", "T", "_" ], \
    #                                         "polarity":"", \
    #                                         "subgoalTimeArg":"" } ], \
    #                "eqnDict":{} }
    expected_a1 = { "relationName":"adom_string", \
                    "goalAttList":[ "T" ], \
                    "goalTimeArg":"", 
                    "subgoalListOfDicts":[ { "subgoalName":"a", \
                                             "subgoalAttList":[ "_", "T", "_" ], \
                                             "polarity":"", \
                                             "subgoalTimeArg":"" } ], \
                    "eqnDict":{} }
    expected_a2 = { "relationName":"adom_int", \
                    "goalAttList":[ "T" ], \
                    "goalTimeArg":"", 
                    "subgoalListOfDicts":[ { "subgoalName":"a", \
                                             "subgoalAttList":[ "_", "_", "T" ], \
                                             "polarity":"", \
                                             "subgoalTimeArg":"" } ], \
                    "eqnDict":{} }
    expected_b0 = { "relationName":"adom_string", \
                    "goalAttList":[ "T" ], \
                    "goalTimeArg":"", 
                    "subgoalListOfDicts":[ { "subgoalName":"b", \
                                             "subgoalAttList":[ "T", "_", "_", "_" ], \
                                             "polarity":"", \
                                             "subgoalTimeArg":"" } ], \
                    "eqnDict":{} }
    expected_b1 = { "relationName":"adom_string", \
                    "goalAttList":[ "T" ], \
                    "goalTimeArg":"", 
                    "subgoalListOfDicts":[ { "subgoalName":"b", \
                                             "subgoalAttList":[ "_", "T", "_", "_" ], \
                                             "polarity":"", \
                                             "subgoalTimeArg":"" } ], \
                    "eqnDict":{} }
    expected_b2 = { "relationName":"adom_int", \
                    "goalAttList":[ "T" ], \
                    "goalTimeArg":"", 
                    "subgoalListOfDicts":[ { "subgoalName":"b", \
                                             "subgoalAttList":[ "_", "_", "T", "_" ], \
                                             "polarity":"", \
                                             "subgoalTimeArg":"" } ], \
                    "eqnDict":{} }
    expected_b3 = { "relationName":"adom_int", \
                    "goalAttList":[ "T" ], \
                    "goalTimeArg":"", 
                    "subgoalListOfDicts":[ { "subgoalName":"b", \
                                             "subgoalAttList":[ "_", "_", "_", "T" ], \
                                             "polarity":"", \
                                             "subgoalTimeArg":"" } ], \
                    "eqnDict":{} }

    expectedAdomRuleData = [ expected_a0, expected_a1, expected_a2, expected_b0, expected_b1, expected_b2, expected_b3 ]

    for i in range( 0, len( actualAdomRuleData ) ) :
      actual   = actualAdomRuleData[ i ]
      expected = expectedAdomRuleData[ i ]

      logging.debug( "  TEST BUILD ADOM : comparing :\n" + str( actual ) + "\nvs\n" + str( expected ) )

      self.assertEqual( actual, expected )

    # --------------------------------------------------------------- #
    # clean up testing

    IRDB.close()
    os.remove( testDB )


  ###############
  #  GET ERROR  #
  ###############
  # extract error message from system info
  def getError( self, sysInfo ) :
    return str( sysInfo[1] )


  ########################
  #  GET ACTUAL RESULTS  #
  ########################
  def getActualResults( self, programLines ) :
    program_string  = "\n".join( programLines )
    program_string += "\n" # add extra newline to align with read() parsing
    return program_string


  ##################
  #  GET ARG DICT  #
  ##################
  def getArgDict( self, inputfile ) :

    # initialize
    argDict = {}

    # populate with unit test defaults
    argDict[ 'prov_diagrams' ]            = False
    argDict[ 'use_symmetry' ]             = False
    argDict[ 'crashes' ]                  = 0
    argDict[ 'solver' ]                   = None
    argDict[ 'disable_dot_rendering' ]    = False
    argDict[ 'settings' ]                 = "./settings_dml.ini"
    argDict[ 'negative_support' ]         = False
    argDict[ 'strategy' ]                 = None
    argDict[ 'file' ]                     = inputfile
    argDict[ 'EOT' ]                      = 4
    argDict[ 'find_all_counterexamples' ] = False
    argDict[ 'nodes' ]                    = [ "a", "b", "c" ]
    argDict[ 'evaluator' ]                = "c4"
    argDict[ 'EFF' ]                      = 2

    return argDict


#########
#  EOF  #
#########
