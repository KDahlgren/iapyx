#!/usr/bin/env python

'''
Test_comb.py
'''

#############
#  IMPORTS  #
#############
# standard python packages
import inspect, logging, os, sqlite3, sys, unittest
from StringIO import StringIO

# ------------------------------------------------------ #
# import sibling packages HERE!!!
if not os.path.abspath( __file__ + "/../../src" ) in sys.path :
  sys.path.append( os.path.abspath( __file__ + "/../../src" ) )

from dedt       import dedt, dedalusParser, Fact, Rule, clockRelation, dedalusRewriter
from utils      import dumpers, globalCounters, tools
from evaluators import c4_evaluator

# ------------------------------------------------------ #


##############
#  TEST COMB  #
##############
class Test_comb( unittest.TestCase ) :

  #logging.basicConfig( format='%(levelname)s:%(message)s', level=logging.DEBUG )
  logging.basicConfig( format='%(levelname)s:%(message)s', level=logging.DEBUG )
  #logging.basicConfig( format='%(levelname)s:%(message)s', level=logging.WARNING )

  PRINT_STOP = False


  #######
  # 2PC #
  #######
  @unittest.skip( "example not working" )
  def test_comb_running_example( self ):
    # specify input and output paths
    inputfile               = os.getcwd() + "/testFiles/running_example.ded"
    expected_iapyx_comb_path = "./testFiles/running_example_comb.olg"

    self.comparison_workflow( inputfile, expected_iapyx_comb_path )  

  #######
  # 2PC #
  #######
  # @unittest.skip( "working on different example" )
  def test_comb_2pc( self ):
    # specify input and output paths
    inputfile               = os.getcwd() + "/testFiles/2pc_driver.ded"
    expected_iapyx_comb_path = "./testFiles/2pc_ctp_comb.olg"

    self.comparison_workflow( inputfile, expected_iapyx_comb_path )

  ################
  #  COMB REPLOG  #
  ################
  # tests rewriting replog
  # @unittest.skip( "working on different example" )
  def test_comb_replog( self ) :

    # specify input and output paths
    inputfile               = os.getcwd() + "/testFiles/replog_driver.ded"
    expected_iapyx_comb_path = "./testFiles/replog_iapyx_comb.olg"

    self.comparison_workflow( inputfile, expected_iapyx_comb_path )

  ################
  # COMB SIMPLOG  #
  ################
  # tests rewriting simplog
  # @unittest.skip( "working on different example" )
  def test_comb_simplog( self ) :

    # specify input and output paths
    inputfile               = os.getcwd() + "/testFiles/simplog_driver.ded"
    expected_iapyx_comb_path = "./testFiles/simplog_iapyx_comb.olg"

    self.comparison_workflow( inputfile, expected_iapyx_comb_path )


  ###############
  #  COMB RDLOG  #
  ###############
  # tests rewriting rdlog
  # @unittest.skip( "working on different example" )
  def test_comb_rdlog( self ) :

    # specify input and output paths
    inputfile               = os.getcwd() + "/testFiles/rdlog_driver.ded"
    expected_iapyx_comb_path = "./testFiles/rdlog_iapyx_comb.olg"

    self.comparison_workflow( inputfile, expected_iapyx_comb_path )

  # ############################
  # #  COMB TOY 3 AGG REWRITES  #
  # ############################
  # tests rewriting the second toy program
  @unittest.skip( "something strange is happenning with the prov, although doesn't actually call combo" )
  def test_comb_toy3_aggRewrites( self ) :

    # specify input and output paths
    inputfile               = os.getcwd() + "/testFiles/toy3_aggRewrites.ded"
    expected_iapyx_comb_path = "./testFiles/toy3_aggRewrites_comb.olg"

    self.comparison_workflow( inputfile, expected_iapyx_comb_path )

  ###############
  #  COMB AGG 2 #
  ###############
  # tests rewriting the second toy program
  # @unittest.skip( "working on different example" )
  def test_comb_agg_2( self ):
    # specify input and output paths
    inputfile               = os.getcwd() + "/testFiles/test_comb_agg_2.ded"
    expected_iapyx_comb_path = "./testFiles/test_comb_agg_2.olg"

    self.comparison_workflow( inputfile, expected_iapyx_comb_path )

  ###############
  #  COMB AGG 1 #
  ###############
  # tests rewriting the second toy program
  # @unittest.skip( "working on different example" )
  def test_comb_agg_1( self ) :

    # specify input and output paths
    inputfile               = os.getcwd() + "/testFiles/test_comb_agg_1.ded"
    expected_iapyx_comb_path = "./testFiles/test_comb_agg_1.olg"

    self.comparison_workflow( inputfile, expected_iapyx_comb_path )

  ###############
  #  COMB TOY 2  #
  ###############
  # tests rewriting the second toy program
  # @unittest.skip( "working on different example" )
  def test_comb_toy2( self ) :

    # specify input and output paths
    inputfile               = os.getcwd() + "/testFiles/toy2.ded"
    expected_iapyx_comb_path = "./testFiles/toy2_comb.olg"

    self.comparison_workflow( inputfile, expected_iapyx_comb_path )


  #############
  #  COMB TOY  #
  #############
  # tests rewriting the toy program
  # @unittest.skip( "working on different example" )
  def test_comb_toy( self ) :

    # specify input and output paths
    inputfile               = os.getcwd() + "/testFiles/toy.ded"
    expected_iapyx_comb_path = "./testFiles/toy_comb.olg"

    self.comparison_workflow( inputfile, expected_iapyx_comb_path )


  #########################
  #  COMPARISON WORKFLOW  #
  #########################
  # defines iapyx comb comparison workflow
  def comparison_workflow( self, inputfile, expected_iapyx_comb_path ) :

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
    argDict = self.getArgDict( inputfile, negprov=True )
    origArgDict = self.getArgDict( inputfile, negprov=False )

    # run translator
    programData = dedt.translateDedalus( argDict, cursor )

    # Clear db.
    IRDB.close()
    os.remove( testDB )

    if os.path.isfile( "./IR.db" ) :
      logging.debug( "  COMPARISON WORKFLOW : removing rogue IR file." )
      os.remove( "./IR.db" )

    testDB = "./IR.db"
    IRDB    = sqlite3.connect( testDB )
    cursor  = IRDB.cursor()

    # run the translator with negprov turned off to compare results
    origProgData = dedt.translateDedalus( origArgDict, cursor )


    # portray actual output program lines as a single string
    iapyx_results = self.getActualResults( programData[0] )

    if self.PRINT_STOP :
      print iapyx_results
      sys.exit( "print stop." )

    # ========================================================== #
    # IAPYX COMPARISON
    #
    # grab expected output results as a string

    expected_iapyx_results = None
    with open( expected_iapyx_comb_path, 'r' ) as expectedFile :
      expected_iapyx_results = expectedFile.read()

    self.assertEqual( iapyx_results, expected_iapyx_results )

    # ========================================================== #
    # EVALUATION COMPARISON

    self.evaluate( programData, origProgData )

    # --------------------------------------------------------------- #
    #clean up testing

    IRDB.close()
    os.remove( testDB )


  ##################
  #  GET ARG DICT  #
  ##################
  def getArgDict( self, inputfile, negprov=True ) :

    # initialize
    argDict = {}

    settingsFile = "settings_comb.ini"
    if not negprov:
      settingsFile = "settings.ini"

    # populate with unit test defaults
    argDict[ 'prov_diagrams' ]            = False
    argDict[ 'use_symmetry' ]             = False
    argDict[ 'crashes' ]                  = 0
    argDict[ 'solver' ]                   = None
    argDict[ 'disable_dot_rendering' ]    = False
    argDict[ 'settings' ]                 = settingsFile
    argDict[ 'negative_support' ]         = False
    argDict[ 'strategy' ]                 = None
    argDict[ 'file' ]                     = inputfile
    argDict[ 'EOT' ]                      = 4
    argDict[ 'find_all_counterexamples' ] = False
    argDict[ 'nodes' ]                    = [ "a", "b", "c" ]
    argDict[ 'evaluator' ]                = "c4"
    argDict[ 'EFF' ]                      = 2

    return argDict



  ##############
  #  EVALUATE  #
  ##############
  # evaluate the datalog program using some datalog evaluator
  # return some data structure or storage location encompassing the evaluation results.
  def evaluate( self, programData, origProgData ) :

    noOverlap = False

    results_array = c4_evaluator.runC4_wrapper( programData )
    orig_results_array = c4_evaluator.runC4_wrapper( origProgData )
    # ----------------------------------------------------------------- #
    # convert results array into dictionary

    eval_results_dict = tools.getEvalResults_dict_c4( results_array )
    orig_eval_results_dict = tools.getEvalResults_dict_c4( orig_results_array )

    # ----------------------------------------------------------------- #
    # collect all pos/not_ rule pairs

    rule_pairs = self.getRulePairs( eval_results_dict )

    logging.debug( "  EVALUATE : rule_pairs = " + str( rule_pairs ) )

    # ----------------------------------------------------------------- #
    # make sure tables do not overlap

    self.assertFalse( self.hasOverlap( rule_pairs, eval_results_dict ) )

    # ----------------------------------------------------------------- #
    # make sure comb positive relation results are identical to molly
    # relation results

    self.comparePositiveResults( orig_eval_results_dict, eval_results_dict )



  ############################
  # COMPARE POSITIVE RESULTS #
  ############################
  # Checks that for each value in the original programs reuslts, the rewritten version
  # gets the same  reuslts
  def comparePositiveResults( self, orig_eval_results_dict, eval_results_dict ):
    for key, val in orig_eval_results_dict.iteritems():
      for item in val:
        self.assertTrue(item in eval_results_dict[key])
      for item in eval_results_dict[key]:
        self.assertTrue(item in val)

    #################
  #  HAS OVERLAP  #
  #################
  # make sure pos and not_pos tables do not overlap
  def hasOverlap( self, rule_pairs, eval_results_dict ) :

    for pair in rule_pairs :
      logging.debug( "  HAS OVERLAP : pair = " + str( pair ) )

      pos_results = eval_results_dict[ pair[0] ]
      not_results = eval_results_dict[ pair[1] ]

      for pos_row in pos_results :
        if pos_row in not_results :
          return True

    return False

  ########################
  #  GET ACTUAL RESULTS  #
  ########################
  def getActualResults( self, programLines ) :
    program_string  = "\n".join( programLines )
    program_string += "\n" # add extra newline to align with read() parsing
    return program_string

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
