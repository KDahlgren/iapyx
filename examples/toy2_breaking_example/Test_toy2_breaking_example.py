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
if not os.path.abspath( __file__ + "/../../../src" ) in sys.path :
  sys.path.append( os.path.abspath( __file__ + "/../../../src" ) )

from dedt       import dedt, dedalusParser, Fact, Rule, clockRelation, dedalusRewriter
from utils      import dumpers, globalCounters, tools
from evaluators import c4_evaluator

import dml
import log_settings

# ------------------------------------------------------ #


#################################
#  TEST TOY 2 BREAKING EXAMPLE  #
#################################
class Test_toy2_breaking_example( unittest.TestCase ) :

  # get debug level
  if log_settings.debug_level == "debug" :
    logging.basicConfig( format='%(levelname)s:%(message)s', level=logging.DEBUG )

  elif log_settings.debug_level == "info" :
    logging.basicConfig( format='%(levelname)s:%(message)s', level=logging.INFO )

  elif log_settings.debug_level == "warning" :
    logging.basicConfig( format='%(levelname)s:%(message)s', level=logging.WARNING )

  else :
    tools.bp( __name__, inspect.stack()[0][3], "FATAL ERROR : unrecognized debug_level '" + debug_level + "'. use 'debug', 'info', or 'warning' only." )

  # set globals
  PRINT_STOP    = False
  COMPARE_PROGS = True

  ##############################
  #  DML TOY 2 USE NEXT CLOCK  #
  ##############################
  # tests rewriting the second toy program using next_clock
  #@unittest.skip( "c4 illogically calculates a('a',2,2) and domcomp_a('a',2,2). behavior did not occur when using aggregates in next rules." )
  def test_dml_toy2_use_next_clock( self ) :

    # specify input and output paths
    inputfile               = "./toy2.ded"
    expected_iapyx_dml_path = "./toy2_breaking_example_use_next_clock.olg"

    # get argDict
    argDict = self.getArgDict( inputfile )
    argDict[ "settings" ] = "./settings_use_next_clock.ini"

    self.comparison_workflow( argDict, inputfile, expected_iapyx_dml_path, None )


  ###############################
  #  DML TOY 2 SYNC ASSUMPTION  #
  ###############################
  # tests rewriting the second toy program using the synchronous assumption
  #@unittest.skip( "c4 illogically calculates a('a',2,2) and domcomp_a('a',2,2). behavior did not occur when using aggregates in next rules." )
  def test_dml_toy2_sync_assumption( self ) :

    # specify input and output paths
    inputfile               = "./toy2.ded"
    expected_iapyx_dml_path = "./toy2_breaking_example_sync_assumption.olg"

    # get argDict
    argDict = self.getArgDict( inputfile )
    argDict[ "settings" ] = "./settings_sync_assumption.ini"

    self.comparison_workflow( argDict, inputfile, expected_iapyx_dml_path, None )


  ########################
  #  DML TOY 2 USE AGGS  #
  ########################
  # tests rewriting the second toy program using agg rewrites
  #@unittest.skip( "c4 illogically calculates a('a',2,2) and domcomp_a('a',2,2). behavior did not occur when using aggregates in next rules." )
  def test_dml_toy2_use_aggs( self ) :

    # specify input and output paths
    inputfile               = "./toy2.ded"
    expected_iapyx_dml_path = "./toy2_breaking_example_use_aggs.olg"

    # get argDict
    argDict = self.getArgDict( inputfile )
    argDict[ "settings" ] = "./settings_use_aggs.ini"

    self.comparison_workflow( argDict, inputfile, expected_iapyx_dml_path, None )


  #########################
  #  COMPARISON WORKFLOW  #
  #########################
  # defines iapyx dml comparison workflow
  def comparison_workflow( self, argDict, inputfile, expected_iapyx_dml_path, expected_eval_path ) :

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


#########
#  EOF  #
#########
