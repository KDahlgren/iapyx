#!/usr/bin/env python

'''
Test_iedb_rewrites.py
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

import iedb_rewrites

# ------------------------------------------------------ #


############################
#  TEST WILDCARD REWRITES  #
############################
class Test_wildcard_rewrites( unittest.TestCase ) :

  #logging.basicConfig( format='%(levelname)s:%(message)s', level=logging.DEBUG )
  logging.basicConfig( format='%(levelname)s:%(message)s', level=logging.INFO )
  #logging.basicConfig( format='%(levelname)s:%(message)s', level=logging.WARNING )

  PRINT_STOP    = False
  COMPARE_PROGS = True

  #####################
  #  NEG SUB WILDS 1  #
  #####################
  # tests rewriting the example 1 program
  #@unittest.skip( "working on different example" )
  def test_neg_sub_wilds_1( self ) :

    test_id = "neg_sub_wilds_1"
    logging.info( "  TEST WILDCARD REWRITES : " + test_id + "..." )

    # specify input and output paths
    inputfile                             = os.getcwd() + "/testFiles/" + test_id + ".ded"
    expected_iapyx_wildcard_rewrites_path = os.getcwd() + "/testFiles/" + test_id + ".olg"

    # get argDict
    argDict = self.getArgDict( inputfile )
    argDict[ "nodes" ]    = [ "a", "b", "x", "y", "thing" ]
    argDict[ "settings" ] = os.getcwd() + "/settings_files/settings_wild.ini"

    # get custom save path
    if not os.path.exists( argDict[ "data_save_path" ] ) :
      os.system( "mkdir " + argDict[ 'data_save_path' ] )
    argDict[ 'data_save_path' ] += test_id
    if not os.path.exists( argDict[ 'data_save_path' ] ) :
      os.system( "mkdir " + argDict[ 'data_save_path' ] )

    self.comparison_workflow( argDict, expected_iapyx_wildcard_rewrites_path, None, "wildcard_rewrites_" + test_id )
    logging.info( "  TEST WILDCARD REWRITES : ...done." )


  ##########
  #  EX 1  #
  ##########
  # tests rewriting the example 1 program
  #@unittest.skip( "working on different example" )
  def test_ex_1( self ) :

    test_id = "ex_1"
    logging.info( "  TEST_WILDCARD_REWRITES : " + test_id + "..." )

    # specify input and output paths
    inputfile                             = os.getcwd() + "/testFiles/" + test_id + ".ded"
    expected_iapyx_wildcard_rewrites_path = os.getcwd() + "/testFiles/" + test_id + ".olg"

    # get argDict
    argDict = self.getArgDict( inputfile )
    argDict[ "nodes" ]    = [ "a", "b" ]
    argDict[ "settings" ] = os.getcwd() + "/settings_files/settings_wild.ini"

    # get custom save path
    if not os.path.exists( argDict[ "data_save_path" ] ) :
      os.system( "mkdir " + argDict[ 'data_save_path' ] )
    argDict[ 'data_save_path' ] += test_id
    if not os.path.exists( argDict[ 'data_save_path' ] ) :
      os.system( "mkdir " + argDict[ 'data_save_path' ] )

    self.comparison_workflow( argDict, expected_iapyx_wildcard_rewrites_path, None, "wildcard_rewrites_" + test_id )
    logging.info( "  TEST_WILDCARD_REWRITES : ...done." )


  #########################
  #  COMPARISON WORKFLOW  #
  #########################
  # defines iapyx iedb_rewrites comparison workflow
  def comparison_workflow( self, argDict, expected_iapyx_iedb_rewrites_path, expected_eval_path, db_name_append ) :

    # --------------------------------------------------------------- #
    # testing set up.

    if os.path.isfile( "./IR*.db*" ) :
      logging.debug( "  COMPARISON WORKFLOW : removing rogue IR*.db* files." )
      os.remove( "./IR*.db*" )

    testDB = "./IR_" + db_name_append + ".db"
    IRDB    = sqlite3.connect( testDB )
    cursor  = IRDB.cursor()

    # --------------------------------------------------------------- #
    # reset counters for new test

    dedt.globalCounterReset()

    # --------------------------------------------------------------- #
    # runs through function to make sure it finishes with expected error

    # run translator
    programData, factMeta, ruleMeta = dedt.translateDedalus( argDict, cursor )

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
      with open( expected_iapyx_iedb_rewrites_path, 'r' ) as expectedFile :
        expected_iapyx_results = expectedFile.read()

      self.assertEqual( iapyx_results, expected_iapyx_results )

    # ========================================================== #
    # EVALUATION COMPARISON

    self.evaluate( programData, expected_eval_path, argDict )

    # --------------------------------------------------------------- #
    #clean up testing

    IRDB.close()
    os.remove( testDB )


  ##############
  #  EVALUATE  #
  ##############
  # evaluate the datalog program using some datalog evaluator
  # return some data structure or storage location encompassing the evaluation results.
  def evaluate( self, programData, expected_eval_path, argDict ) :

    noOverlap = False

    results_array = c4_evaluator.runC4_wrapper( programData, argDict )

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
    # make sure iedb_rewrites positive relation results are identical to molly
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
         rel_key.endswith( "_edb" ) or \
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
    argDict[ 'settings' ]                 = "./settings_files/settings_iedb_rewrites.ini"
    argDict[ 'negative_support' ]         = False
    argDict[ 'strategy' ]                 = None
    argDict[ 'file' ]                     = inputfile
    argDict[ 'EOT' ]                      = 4
    argDict[ 'find_all_counterexamples' ] = False
    argDict[ 'nodes' ]                    = [ "a", "b", "c" ]
    argDict[ 'evaluator' ]                = "c4"
    argDict[ 'EFF' ]                      = 2
    argDict[ 'data_save_path' ]           = "./data/"
    argDict[ 'neg_writes' ]               = ""

    return argDict


if __name__ == "__main__" :
  if os.path.exists( "./IR*.db*" ) :
    os.remove( "./IR*.db*" )
  unittest.main()
  if os.path.exists( "./IR*.db*" ) :
    os.remove( "./IR*.db*" )


#########
#  EOF  #
#########
