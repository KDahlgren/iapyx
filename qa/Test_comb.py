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

  logging.basicConfig( format='%(levelname)s:%(message)s', level=logging.DEBUG )
  #logging.basicConfig( format='%(levelname)s:%(message)s', level=logging.INFO )
  #logging.basicConfig( format='%(levelname)s:%(message)s', level=logging.WARNING )

  PRINT_STOP = False

  ###################
  # RUNNING EXAMPLE #
  ###################
  @unittest.skip( "example not working" )
  def test_comb_running_example( self ):
    test_id = "comb_running_example"
    # specify input and output paths
    inputfile               = os.getcwd() + "/testFiles/running_example.ded"
    expected_iapyx_comb_path = "./testFiles/running_example_comb.olg"

    self.comparison_workflow( inputfile, expected_iapyx_comb_path, test_id, \
                              nodes=["a", "jobscheduler"], eot=5, eff=4)  

  #######
  # 2PC #
  #######
  # @unittest.skip( "working on different example" )
  def test_comb_2pc( self ):

    test_id = "comb_2pc"

    # specify input and output paths
    inputfile               = os.getcwd() + "/testFiles/2pc_driver.ded"
    expected_iapyx_comb_path = "./testFiles/2pc_ctp_comb.olg"

    self.comparison_workflow( inputfile, expected_iapyx_comb_path, test_id )

  #################
  #  COMB ACK RB  #
  #################
  # tests rewriting ack_rb
  @unittest.skip( "results do not align." )
  def test_comb_ack_rb( self ) :

    test_id = "comb_ack_rb"

    # specify input and output paths
    inputfile                = os.getcwd() + "/testFiles/ack_rb_driver.ded"
    expected_iapyx_comb_path = "./testFiles/ack_rb_iapyx_comb.olg"

    self.comparison_workflow( inputfile, expected_iapyx_comb_path, test_id, eot=6 )

  ################
  #  COMB REPLOG  #
  ################
  # tests rewriting replog
  # @unittest.skip( "working on different example" )
  def test_comb_replog( self ) :

    test_id = "comb_replog"

    # specify input and output paths
    inputfile               = os.getcwd() + "/testFiles/replog_driver.ded"
    expected_iapyx_comb_path = "./testFiles/replog_iapyx_comb.olg"

    self.comparison_workflow( inputfile, expected_iapyx_comb_path, test_id )

  ################
  # COMB SIMPLOG  #
  ################
  # tests rewriting simplog
  # @unittest.skip( "working on different example" )
  def test_comb_simplog( self ) :

    test_id = "comb_simplog"

    # specify input and output paths
    inputfile               = os.getcwd() + "/testFiles/simplog_driver.ded"
    expected_iapyx_comb_path = "./testFiles/simplog_iapyx_comb.olg"

    self.comparison_workflow( inputfile, expected_iapyx_comb_path, test_id )


  ###############
  #  COMB RDLOG  #
  ###############
  # tests rewriting rdlog
  # @unittest.skip( "working on different example" )
  def test_comb_rdlog( self ) :

    test_id = "comb_rdlog"

    # specify input and output paths
    inputfile               = os.getcwd() + "/testFiles/rdlog_driver.ded"
    expected_iapyx_comb_path = "./testFiles/rdlog_iapyx_comb.olg"

    self.comparison_workflow( inputfile, expected_iapyx_comb_path, test_id )

  #############################
  #  COMB TOY 3 AGG REWRITES  #
  #############################
  # tests rewriting the second toy program
  @unittest.skip( "something strange is happenning with the prov, although doesn't actually call combo" )
  def test_comb_toy3_aggRewrites( self ) :

    test_id = "comb_toy3_aggRewrites"
    # specify input and output paths
    inputfile               = os.getcwd() + "/testFiles/toy3_aggRewrites.ded"
    expected_iapyx_comb_path = "./testFiles/toy3_aggRewrites_comb.olg"

    self.comparison_workflow( inputfile, expected_iapyx_comb_path, test_id )

  ###############
  #  COMB AGG 2 #
  ###############
  # tests rewriting the second toy program
  # @unittest.skip( "working on different example" )
  def test_comb_agg_2( self ):
    test_id = "comb_agg_2"
    # specify input and output paths
    inputfile               = os.getcwd() + "/testFiles/test_comb_agg_2.ded"
    expected_iapyx_comb_path = "./testFiles/test_comb_agg_2.olg"

    self.comparison_workflow( inputfile, expected_iapyx_comb_path, test_id )

  ###############
  #  COMB AGG 1 #
  ###############
  # tests rewriting the second toy program
  # @unittest.skip( "working on different example" )
  def test_comb_agg_1( self ) :

    test_id = "comb_agg_1"

    # specify input and output paths
    inputfile               = os.getcwd() + "/testFiles/test_comb_agg_1.ded"
    expected_iapyx_comb_path = "./testFiles/test_comb_agg_1.olg"

    self.comparison_workflow( inputfile, expected_iapyx_comb_path, test_id )

  ###############
  #  COMB TOY 2  #
  ###############
  # tests rewriting the second toy program
  # @unittest.skip( "working on different example" )
  def test_comb_toy2( self ) :

    test_id = "comb_comb_toy2"

    # specify input and output paths
    inputfile               = os.getcwd() + "/testFiles/toy2.ded"
    expected_iapyx_comb_path = "./testFiles/toy2_comb.olg"

    self.comparison_workflow( inputfile, expected_iapyx_comb_path, test_id )


  #############
  #  COMB TOY  #
  #############
  # tests rewriting the toy program
  # @unittest.skip( "working on different example" )
  def test_comb_toy( self ) :

    test_id = "comb_comb_toy"

    # specify input and output paths
    inputfile               = os.getcwd() + "/testFiles/toy.ded"
    expected_iapyx_comb_path = "./testFiles/toy_comb.olg"

    self.comparison_workflow( inputfile, expected_iapyx_comb_path, test_id )


  #########################
  #  COMPARISON WORKFLOW  #
  #########################
  # defines iapyx comb comparison workflow
  def comparison_workflow( self, \
                           inputfile, \
                           expected_iapyx_comb_path, \
                           test_id, \
                           nodes=["a", "b", "c"], \
                           eot=4, \
                           eff=4 ) :

    # --------------------------------------------------------------- #
    # get argDict

    argDict     = self.getArgDict( inputfile, negprov=True, nodes=nodes, eot=eot, eff=eff )
    origArgDict = self.getArgDict( inputfile, negprov=False, nodes=nodes, eot=eot, eff=eff )

    argDict[ "data_save_path" ]     += test_id
    origArgDict[ "data_save_path" ]  = argDict[ "data_save_path" ]
    self.make_data_dir( argDict[ "data_save_path" ], test_id )

    # --------------------------------------------------------------- #
    # testing set up.

    testDB = "./" + argDict[ "data_save_path" ] + "/IR_" + test_id
    testDB_combo = testDB + "_combo.db"
    testDB_orig  = testDB + "_orig.db"

    if os.path.isfile( testDB_combo ) :
      logging.debug( "  COMPARISON WORKFLOW : removing rogue IR file." )
      os.remove( testDB_combo )
    if os.path.isfile( testDB_orig ) :
      logging.debug( "  COMPARISON WORKFLOW : removing rogue IR file." )
      os.remove( testDB_orig )

    IRDB_combo   = sqlite3.connect( testDB_combo )
    cursor_combo = IRDB_combo.cursor()
    dedt.globalCounterReset()
    programData = dedt.translateDedalus( argDict, cursor_combo )

    # Clear db.
    IRDB_combo.close()
    os.remove( testDB_combo )

    if os.path.isfile( testDB_orig ) :
      logging.debug( "  COMPARISON WORKFLOW : removing rogue IR file." )
      os.remove( testDB_orig )

    IRDB_orig   = sqlite3.connect( testDB_orig )
    cursor_orig = IRDB_orig.cursor()
    dedt.globalCounterReset()

    # run the translator with negprov turned off to compare results
    origProgData = dedt.translateDedalus( origArgDict, cursor_orig )

    # portray actual output program lines as a single string
    iapyx_results = self.getActualResults( programData[0] )

    if self.PRINT_STOP :
      print iapyx_results
      sys.exit( "PRINT STOP" )

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

    self.evaluate( programData, origProgData, argDict )

    # --------------------------------------------------------------- #
    #clean up testing

    IRDB_orig.close()
    os.remove( testDB_orig )


  ##################
  #  GET ARG DICT  #
  ##################
  def getArgDict( self, inputfile, negprov=True, nodes=["a", "b", "c"], eot=4, eff=2 ) :

    # initialize
    argDict = {}

    settingsFile = "settings_files/settings_comb.ini"
    if not negprov:
      settingsFile = "settings_files/settings.ini"

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
    argDict[ 'EOT' ]                      = eot
    argDict[ 'find_all_counterexamples' ] = False
    argDict[ 'nodes' ]                    = nodes
    argDict[ 'evaluator' ]                = "c4"
    argDict[ 'EFF' ]                      = eff
    argDict[ 'data_save_path' ]           = "./data/"
    argDict[ 'neg_writes' ]               = "combo"

    if not negprov :
      argDict[ 'neg_writes' ] = ""

    return argDict

  ###################
  #  MAKE DATA DIR  #
  ###################
  def make_data_dir( self, data_save_path, test_id ) :
    logging.debug( "  TEST " + test_id.upper() + \
                   " : data save path not found : " + \
                   data_save_path )

    dir_list = data_save_path.split( "/" )
    complete_str = "./"
    for this_dir in dir_list :
      if this_dir == "./" :
        complete_str += this_dir
      else :
        complete_str += this_dir + "/"
        if not os.path.exists( complete_str ) :
          cmd = "mkdir " + complete_str
          logging.debug( "  TEST " + test_id.upper() + " : running cmd = " + cmd )
          os.system( cmd )

  ##############
  #  EVALUATE  #
  ##############
  # evaluate the datalog program using some datalog evaluator
  # return some data structure or storage location encompassing the evaluation results.
  def evaluate( self, programData, origProgData, argDict ) :

    results_array      = c4_evaluator.runC4_wrapper( programData[0], argDict )
    orig_results_array = c4_evaluator.runC4_wrapper( origProgData[0], argDict )

    # ----------------------------------------------------------------- #
    # convert results array into dictionary

    eval_results_dict      = tools.getEvalResults_dict_c4( results_array )
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

    self.check_results_alignment( orig_eval_results_dict, eval_results_dict )


  #############################
  #  CHECK RESULTS ALIGNMENT  #
  #############################
  def check_results_alignment( self, eval_molly, eval_combo ) :
    logging.debug( "" )
    logging.debug( "<><><><><><><><><><><><><><><><><><>" )
    logging.debug( "<>   CHECKING TUPLE ALIGNMENTS    <>" )

    # combo check
    logging.debug( "ooooooooooooooooooooooooooooooooooooooooooooooo" )
    logging.debug( "  checking results for combo v. molly:" )

    molly_tups_not_in_iapyx = []
    iapyx_tups_not_in_molly = []

    for rel in eval_molly :
      if "_prov" in rel :
        continue
      else :

        # check for extra molly tups
        extra_molly_tups = []
        for molly_tup in eval_molly[ rel ] :
          if not molly_tup in eval_combo[ rel ] :
            extra_molly_tups.append( molly_tup )
        molly_tups_not_in_iapyx.extend( extra_molly_tups )

        # check for extra combo tups
        extra_combo_tups = []
        for combo_tup in eval_combo[ rel ] :
          if not combo_tup in eval_molly[ rel ] :
            extra_combo_tups.append( combo_tup )
        iapyx_tups_not_in_molly.extend( extra_combo_tups )

        if len( extra_molly_tups ) > 0 or len( extra_combo_tups ) > 0 :
          logging.debug( ">>>> alignment inconsistencies for relation '" + rel + "' :" )

        if len( extra_molly_tups ) > 0 :
          logging.debug( "> tuples found in molly and not in combo for relation '" + rel.upper() + " :" )
          for tup in extra_molly_tups :
            logging.debug( ",".join( tup ) )
        if len( extra_combo_tups ) > 0 :
          logging.debug( "> tuples found in combo and not in molly for relation '" + rel.upper() + " :" )
          for tup in extra_combo_tups :
            logging.debug( ",".join( tup ) )
        if len( extra_molly_tups ) > 0 or len( extra_combo_tups ) > 0 :
          logging.debug( "<<<<" )

    logging.debug( "" )
    logging.debug( "<><><><><><><><><><><><><><><><><><>" )
    print molly_tups_not_in_iapyx
    self.assertTrue( len( molly_tups_not_in_iapyx ) < 1 )
    self.assertTrue( len( iapyx_tups_not_in_molly ) < 1 )


  ############################
  # COMPARE POSITIVE RESULTS #
  ############################
  # Checks that for each value in the original programs reults, the rewritten version
  # gets the same  reuslts
  def comparePositiveResults( self, orig_eval_results_dict, eval_results_dict ):

    for key, val in orig_eval_results_dict.iteritems():
      # ensuring matching tuple contents is 
      # not a good evaluation standard when the goal att orderings
      # in prov rules can't match whatever the hell order Molly's using.
      if not "_prov" in key :
        logging.debug( "  COMPARE POSITIVE RESULTS : key = " + key )
        for tup in val :
          logging.debug( "  COMPARE POSITIVE RESULTS : tup = " + str( tup ) )
        for tup in eval_results_dict[ key ] :
          self.assertTrue( tup in val )

    for key, val in eval_results_dict.iteritems():
      # ensuring matching tuple contents is 
      # not a good evaluation standard when the goal att orderings
      # in prov rules can't match whatever the hell order Molly's using.
      if not "_prov" in key :
        logging.debug( "  COMPARE POSITIVE RESULTS : key = " + key )
        for tup in val :
          logging.debug( "  COMPARE POSITIVE RESULTS : tup = " + str( tup ) )
        for tup in eval_results_dict[ key ] :
          self.assertTrue( tup in val )

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
          logging.debug( "  HAS OVERLAP : returning True." )
          return True

    logging.debug( "  HAS OVERLAP : returning False." )
    return False

  ########################
  #  GET ACTUAL RESULTS  #
  ########################
  def getActualResults( self, programLines ) :
    program_string  = "\n".join( programLines[0] )
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


##############################
#  MAIN THREAD OF EXECUTION  #
##############################
if __name__ == "__main__" :
  if os.path.exists( "./IR*.db*" ) :
    os.remove( "./IR*.db*" )
  unittest.main()
  if os.path.exists( "./IR*.db*" ) :
    os.remove( "./IR*.db*" )

#########
#  EOF  #
#########
