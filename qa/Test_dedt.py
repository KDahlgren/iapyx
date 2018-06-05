#!/usr/bin/env python

'''
Test_dedt.py
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

from dedt  import dedt, dedalusParser, clockRelation, dedalusRewriter
from utils import dumpers, globalCounters, tools

# ------------------------------------------------------ #


###############
#  TEST DEDT  #
###############
class Test_dedt( unittest.TestCase ) :

  logging.basicConfig( format='%(levelname)s:%(message)s', level=logging.DEBUG )
  #logging.basicConfig( format='%(levelname)s:%(message)s', level=logging.INFO )
  #logging.basicConfig( format='%(levelname)s:%(message)s', level=logging.WARNING )

  PRINT_STOP = False

  ##############################
  #  FIXED DATA 2 (FROM ORIK)  #
  ##############################
  # tests translation of a small program containing 
  # a subgoal with a fixed string data input.
  #@unittest.skip( "working on different example" )
  def test_fixed_data_2( self ) :

    test_id = "fixed_data_2"

    # --------------------------------------------------------------- #
    # testing set up.
    testDB = "./IR.db"
    IRDB   = sqlite3.connect( testDB )
    cursor = IRDB.cursor()

    # --------------------------------------------------------------- #
    #dependency
    #dedt.createDedalusIRTables(cursor)
    dedt.globalCounterReset()

    # --------------------------------------------------------------- #

    # specify input file path
    inputfile = "./testFiles/fixed_data_2.ded"

    # get argDict
    argDict = self.getArgDict( inputfile )

    # specify settings file
    argDict[ "settings" ] = "./settings_files/settings_sync_assumption.ini"

    # get custom save path
    argDict[ 'data_save_path' ] = self.custom_save_path( argDict, test_id )
    argDict[ "neg_writes" ]     = ""

    # run translator
    programData = dedt.translateDedalus( argDict, cursor )

    # portray actual output program lines as a single string
    actual_results = self.getActualResults( programData )

    if self.PRINT_STOP :
      print actual_results
      sys.exit( "print stop." )

    # grab expected output results as a string
    expected_results_path = "./testFiles/fixed_data_2.olg"
    expected_results      = None
    with open( expected_results_path, 'r' ) as expectedFile :
      expected_results = expectedFile.read()

    self.assertEqual( actual_results, expected_results )

    # --------------------------------------------------------------- #
    #clean up testing
    IRDB.close()
    os.remove( testDB )


  ########################
  #  TOY 4 AGG WITH EQN  #
  ########################
  # tests building agg rule provenance with an eqn
  #@unittest.skip( "working on different example" )
  def test_toy4_agg_with_eqn( self ) :

    test_id = "toy4_agg_with_eqn"

    # --------------------------------------------------------------- #
    # testing set up.
    testDB = "./IR.db"
    IRDB   = sqlite3.connect( testDB )
    cursor = IRDB.cursor()

    # --------------------------------------------------------------- #
    #dependency
    #dedt.createDedalusIRTables(cursor)
    dedt.globalCounterReset()

    # --------------------------------------------------------------- #

    # specify input file path
    inputfile = "./testFiles/toy4_agg_with_eqn.ded"

    # get argDict
    argDict = self.getArgDict( inputfile )

    # specify settings file
    argDict[ "settings" ] = "./settings_files/settings_sync_assumption.ini"

    # get custom save path
    argDict[ 'data_save_path' ] = self.custom_save_path( argDict, test_id )
    argDict[ "neg_writes" ]     = ""

    # run translator
    programData = dedt.translateDedalus( argDict, cursor )

    # portray actual output program lines as a single string
    actual_results = self.getActualResults( programData )

    if self.PRINT_STOP :
      print actual_results
      sys.exit( "print stop." )

    # grab expected output results as a string
    expected_results_path = "./testFiles/toy4_agg_with_eqn.olg"
    expected_results      = None
    with open( expected_results_path, 'r' ) as expectedFile :
      expected_results = expectedFile.read()

    self.assertEqual( actual_results, expected_results )

    # --------------------------------------------------------------- #
    #clean up testing
    IRDB.close()
    os.remove( testDB )


  ##############################
  #  TOY 2 USE NEXT CLOCK DM  #
  ##############################
  # tests next rule hanlding using the next clock and dm
  #@unittest.skip( "working on different example" )
  def test_toy2_use_next_clock_dm( self ) :

    test_id = "toy2_use_next_clock_dm"

    # --------------------------------------------------------------- #
    # testing set up.
    testDB = "./IR.db"
    IRDB    = sqlite3.connect( testDB )
    cursor  = IRDB.cursor()

    # --------------------------------------------------------------- #
    #dependency
    #dedt.createDedalusIRTables(cursor)
    dedt.globalCounterReset()

    # --------------------------------------------------------------- #

    # specify input file path
    inputfile = "./testFiles/toy2.ded"

    # get argDict
    argDict = self.getArgDict( inputfile )

    # specify settings file
    argDict[ "settings" ] = "./settings_files/settings_use_next_clock_dm.ini"

    # get custom save path
    argDict[ 'data_save_path' ] = self.custom_save_path( argDict, test_id )
    argDict[ "neg_writes" ]     = "dm"

    # run translator
    programData = dedt.translateDedalus( argDict, cursor )

    # portray actual output program lines as a single string
    actual_results = self.getActualResults( programData )

    if self.PRINT_STOP :
      print actual_results
      sys.exit( "print stop." )

    # grab expected output results as a string
    expected_results_path = "./testFiles/toy2_use_next_clock_dm.olg"
    expected_results      = None
    with open( expected_results_path, 'r' ) as expectedFile :
      expected_results = expectedFile.read()

    self.assertEqual( actual_results, expected_results )

    # --------------------------------------------------------------- #
    #clean up testing
    IRDB.close()
    os.remove( testDB )


  ##########################
  #  TOY 2 USE NEXT CLOCK  #
  ##########################
  # tests next rule hanlding using the next clock
  #@unittest.skip( "working on different example" )
  def test_toy2_use_next_clock( self ) :

    test_id = "toy2_use_next_clock"

    # --------------------------------------------------------------- #
    # testing set up.
    testDB = "./IR.db"
    IRDB    = sqlite3.connect( testDB )
    cursor  = IRDB.cursor()

    # --------------------------------------------------------------- #
    #dependency
    #dedt.createDedalusIRTables(cursor)
    dedt.globalCounterReset()

    # --------------------------------------------------------------- #

    # specify input file path
    inputfile = "./testFiles/toy2.ded"

    # get argDict
    argDict = self.getArgDict( inputfile )

    # specify settings file
    argDict[ "settings" ] = "./settings_files/settings_use_next_clock.ini"

    # get custom save path
    argDict[ 'data_save_path' ] = self.custom_save_path( argDict, test_id )
    argDict[ "neg_writes" ]     = ""

    # run translator
    programData = dedt.translateDedalus( argDict, cursor )

    # portray actual output program lines as a single string
    actual_results = self.getActualResults( programData )

    if self.PRINT_STOP :
      print actual_results
      sys.exit( "print stop." )

    # grab expected output results as a string
    expected_results_path = "./testFiles/toy2_use_next_clock.olg"
    expected_results      = None
    with open( expected_results_path, 'r' ) as expectedFile :
      expected_results = expectedFile.read()

    self.assertEqual( actual_results, expected_results )

    # --------------------------------------------------------------- #
    #clean up testing
    IRDB.close()
    os.remove( testDB )


  ###############################
  #  TOY 2 SYNC ASSUMPTION DM  #
  ###############################
  # tests next rule hanlding assuming a synchronous communication model and using dm
  #@unittest.skip( "working on different example" )
  def test_toy2_sync_assumption_dm( self ) :

    test_id = "toy2_sync_assumption_dm"

    # --------------------------------------------------------------- #
    # testing set up.
    testDB = "./IR.db"
    IRDB    = sqlite3.connect( testDB )
    cursor  = IRDB.cursor()

    # --------------------------------------------------------------- #
    #dependency
    #dedt.createDedalusIRTables(cursor)
    dedt.globalCounterReset()

    # --------------------------------------------------------------- #

    # specify input file path
    inputfile = "./testFiles/toy2.ded"

    # get argDict
    argDict = self.getArgDict( inputfile )

    # specify settings file
    argDict[ "settings" ] = "./settings_files/settings_sync_assumption_dm.ini"

    # get custom save path
    argDict[ 'data_save_path' ] = self.custom_save_path( argDict, test_id )
    argDict[ "neg_writes" ]     = "dm"

    # run translator
    programData = dedt.translateDedalus( argDict, cursor )

    # portray actual output program lines as a single string
    actual_results = self.getActualResults( programData )

    if self.PRINT_STOP :
      print actual_results
      sys.exit( "print stop." )

    # grab expected output results as a string
    expected_results_path = "./testFiles/toy2_sync_assumption_dm.olg"
    expected_results      = None
    with open( expected_results_path, 'r' ) as expectedFile :
      expected_results = expectedFile.read()

    self.assertEqual( actual_results, expected_results )

    # --------------------------------------------------------------- #
    #clean up testing
    IRDB.close()
    os.remove( testDB )


  ###########################
  #  TOY 2 SYNC ASSUMPTION  #
  ###########################
  # tests next rule hanlding assuming a synchronous communication model
  #@unittest.skip( "working on different example" )
  def test_toy2_sync_assumption( self ) :

    test_id = "toy2_sync_assumption"

    # --------------------------------------------------------------- #
    # testing set up.
    testDB = "./IR.db"
    IRDB    = sqlite3.connect( testDB )
    cursor  = IRDB.cursor()

    # --------------------------------------------------------------- #
    #dependency
    #dedt.createDedalusIRTables(cursor)
    dedt.globalCounterReset()

    # --------------------------------------------------------------- #

    # specify input file path
    inputfile = "./testFiles/toy2.ded"

    # get argDict
    argDict = self.getArgDict( inputfile )

    # specify settings file
    argDict[ "settings" ] = "./settings_files/settings_sync_assumption.ini"

    # get custom save path
    argDict[ 'data_save_path' ] = self.custom_save_path( argDict, test_id )
    argDict[ "neg_writes" ]     = ""

    # run translator
    programData = dedt.translateDedalus( argDict, cursor )

    # portray actual output program lines as a single string
    actual_results = self.getActualResults( programData )

    if self.PRINT_STOP :
      print actual_results
      sys.exit( "print stop." )

    # grab expected output results as a string
    expected_results_path = "./testFiles/toy2_sync_assumption.olg"
    expected_results      = None
    with open( expected_results_path, 'r' ) as expectedFile :
      expected_results = expectedFile.read()

    self.assertEqual( actual_results, expected_results )

    # --------------------------------------------------------------- #
    #clean up testing
    IRDB.close()
    os.remove( testDB )


  ########################
  #  TOY 2 USE AGGS DM  #
  ########################
  # tests next rule hanlding using agg rewrites and dm
  #@unittest.skip( "working on different example" )
  def test_toy2_use_aggs_dm( self ) :

    test_id = "toy2_use_aggs_dm"

    # --------------------------------------------------------------- #
    # testing set up.
    testDB = "./IR.db"
    IRDB    = sqlite3.connect( testDB )
    cursor  = IRDB.cursor()

    # --------------------------------------------------------------- #
    #dependency
    #dedt.createDedalusIRTables(cursor)
    dedt.globalCounterReset()

    # --------------------------------------------------------------- #

    # specify input file path
    inputfile = "./testFiles/toy2.ded"

    # get argDict
    argDict = self.getArgDict( inputfile )

    # specify settings file
    argDict[ "settings" ] = "./settings_files/settings_use_aggs_dm.ini"

    # get custom save path
    argDict[ 'data_save_path' ] = self.custom_save_path( argDict, test_id )
    argDict[ "neg_writes" ]     = "dm"

    # run translator
    programData = dedt.translateDedalus( argDict, cursor )

    # portray actual output program lines as a single string
    actual_results = self.getActualResults( programData )

    if self.PRINT_STOP :
      print actual_results
      sys.exit( "print stop." )

    # grab expected output results as a string
    expected_results_path = "./testFiles/toy2_use_aggs_dm.olg"
    expected_results      = None
    with open( expected_results_path, 'r' ) as expectedFile :
      expected_results = expectedFile.read()

    self.assertEqual( actual_results, expected_results )

    # --------------------------------------------------------------- #
    #clean up testing
    IRDB.close()
    os.remove( testDB )


  ####################
  #  TOY 2 USE AGGS  #
  ####################
  # tests next rule hanlding using agg rewrites
  #@unittest.skip( "working on different example" )
  def test_toy2_use_aggs( self ) :

    test_id = "toy2_use_aggs"

    # --------------------------------------------------------------- #
    # testing set up.
    testDB = "./IR.db"
    IRDB    = sqlite3.connect( testDB )
    cursor  = IRDB.cursor()

    # --------------------------------------------------------------- #
    #dependency
    #dedt.createDedalusIRTables(cursor)
    dedt.globalCounterReset()

    # --------------------------------------------------------------- #

    # specify input file path
    inputfile = "./testFiles/toy2.ded"

    # get argDict
    argDict = self.getArgDict( inputfile )

    # specify settings file
    argDict[ "settings" ] = "./settings_files/settings_use_aggs.ini"

    # get custom save path
    argDict[ 'data_save_path' ] = self.custom_save_path( argDict, test_id )
    argDict[ "neg_writes" ]     = ""

    # run translator
    programData = dedt.translateDedalus( argDict, cursor )

    # portray actual output program lines as a single string
    actual_results = self.getActualResults( programData )

    if self.PRINT_STOP :
      print actual_results
      sys.exit( "print stop." )

    # grab expected output results as a string
    expected_results_path = "./testFiles/toy2_use_aggs.olg"
    expected_results      = None
    with open( expected_results_path, 'r' ) as expectedFile :
      expected_results = expectedFile.read()

    self.assertEqual( actual_results, expected_results )

    # --------------------------------------------------------------- #
    #clean up testing
    IRDB.close()
    os.remove( testDB )


  ################
  #  EXAMPLE 16  #
  ################
  # example 16 details a correct program.
  # tests ded to c4 datalog translation with an aggregate function.
  # make sure this test produces the expected olg program.
  #@unittest.skip( "working on different example" )
  def test_example16( self ) :

    test_id = "example16"

    # --------------------------------------------------------------- #
    # testing set up.
    testDB = "./IR.db"
    IRDB    = sqlite3.connect( testDB )
    cursor  = IRDB.cursor()

    # --------------------------------------------------------------- #
    #dependency
    #dedt.createDedalusIRTables(cursor)
    dedt.globalCounterReset()

    # --------------------------------------------------------------- #

    # specify input file path
    inputfile = "./testFiles/example16.ded"

    # get argDict
    argDict = self.getArgDict( inputfile )

    # get custom save path
    argDict[ 'data_save_path' ] = self.custom_save_path( argDict, test_id )
    argDict[ "neg_writes" ]     = ""

    # run translator
    programData = dedt.translateDedalus( argDict, cursor )

    # portray actual output program lines as a single string
    actual_results = self.getActualResults( programData )

    if self.PRINT_STOP :
      print actual_results
      sys.exit( "print stop." )

    # grab expected output results as a string
    expected_results_path = "./testFiles/example16.olg"
    expected_results      = None
    with open( expected_results_path, 'r' ) as expectedFile :
      expected_results = expectedFile.read()

    self.assertEqual( actual_results, expected_results )

    # --------------------------------------------------------------- #
    #clean up testing
    IRDB.close()
    os.remove( testDB )


  ################
  #  EXAMPLE 15  #
  ################
  # test setting data types to rule attributes
  # tests type assignments for aggregated attributes and 
  # attributes with fixed data.
  #@unittest.skip( "working on different example" )
  def test_example15( self ) :

    test_id = "example15"

    # --------------------------------------------------------------- #
    # build empty IR db

    testDB = "./IR.db"
    IRDB   = sqlite3.connect( testDB )
    cursor = IRDB.cursor()
    dedt.createDedalusIRTables(cursor)
    dedt.globalCounterReset()

    # --------------------------------------------------------------- #
    # test rule saves

    inputfile = "./testFiles/example15.ded"
    argDict   = self.getArgDict( inputfile )

    # get custom save path
    argDict[ 'data_save_path' ] = self.custom_save_path( argDict, test_id )
    argDict[ "neg_writes" ]     = ""

    dedt.runTranslator( cursor, inputfile, argDict, "c4" )

    # dump rules
    actual_ruleData = dumpers.ruleAttDump( cursor )

    if self.PRINT_STOP :
      print actual_ruleData

    # expected rules
    expected_ruleData = {'1': {'goalName': 'new_term', 'goalAttData': [[0, 'N', 'string'], [1, 'T+1', 'int'], [2, 'NRESERVED', 'int']], 'subgoalAttData': [['7', 'term', [[0, 'N', 'string'], [1, 'T', 'int'], [2, 'NRESERVED', 'int']]], ['8', 'stall', [[0, 'N', 'string'], [1, 'T', 'int'], [2, 'NRESERVED', 'int']]]]}, '0': {'goalName': 'role_x', 'goalAttData': [[0, 'N', 'string'], [1, 'max<I>', 'int'], [2, 'NRESERVED', 'int']], 'subgoalAttData': [['13', 'role_x_vars', [[0, 'N', 'string'], [1, 'I', 'int'], [2, '_', 'string'], [3, 'NRESERVED', 'int']]]]}, '3': {'goalName': 'role_x_vars', 'goalAttData': [[0, 'N', 'string'], [1, 'I', 'int'], [2, 'R', 'string'], [3, 'NRESERVED', 'int']], 'subgoalAttData': [['10', 'role_change', [[0, 'N', 'string'], [1, 'R', 'string'], [2, 'NRESERVED', 'int']]], ['11', 'rank', [[0, 'N', 'string'], [1, 'R', 'string'], [2, 'I', 'int'], [3, 'NRESERVED', 'int']]]]}, '2': {'goalName': 'lclock_register', 'goalAttData': [[0, 'N', 'string'], [1, '"Localtime"', 'string'], [2, 'T', 'int'], [3, 'NRESERVED', 'int']], 'subgoalAttData': [['9', 'new_term', [[0, 'N', 'string'], [1, 'T', 'int'], [2, 'NRESERVED', 'int']]]]}, '5': {'goalName': 'new_term_prov1', 'goalAttData': [[0, 'N', 'string'], [1, 'T+1', 'int'], [2, 'T', 'int'], [3, 'NRESERVED', 'int']], 'subgoalAttData': [['14', 'term', [[0, 'N', 'string'], [1, 'T', 'int'], [2, 'NRESERVED', 'int']]], ['15', 'stall', [[0, 'N', 'string'], [1, 'T', 'int'], [2, 'NRESERVED', 'int']]]]}, '4': {'goalName': 'role_x_prov0', 'goalAttData': [[0, 'N', 'string'], [1, 'max<I>', 'int'], [2, 'NRESERVED', 'int']], 'subgoalAttData': [['12', 'role_x_vars', [[0, 'N', 'string'], [1, 'I', 'int'], [2, '_', 'string'], [3, 'NRESERVED', 'int']]]]}, '6': {'goalName': 'lclock_register_prov2', 'goalAttData': [[0, 'N', 'string'], [1, '"Localtime"', 'string'], [2, 'T', 'int'], [3, 'NRESERVED', 'int']], 'subgoalAttData': [['16', 'new_term', [[0, 'N', 'string'], [1, 'T', 'int'], [2, 'NRESERVED', 'int']]]]}}

    self.assertEqual( actual_ruleData, expected_ruleData )

    # --------------------------------------------------------------- #
    # clean up testing

    IRDB.close()
    os.remove( testDB )


  ################
  #  EXAMPLE 14  #
  ################
  # test setting data types to rule attributes
  # bad run => non-terminating
  #@unittest.skip( "working on different example" )
  def test_example14( self ) :

    # --------------------------------------------------------------- #
    # build empty IR db

    testDB = "./IR.db"
    IRDB   = sqlite3.connect( testDB )
    cursor = IRDB.cursor()
    dedt.createDedalusIRTables(cursor)
    dedt.globalCounterReset()

    # --------------------------------------------------------------- #
    # test rule saves

    # run program and catch error
    try :
      inputfile = "./testFiles/example14.ded"
      argDict   = self.getArgDict( inputfile )
      dedt.runTranslator( cursor, inputfile, argDict, "c4" )
    except :
      actual_results = self.getError( sys.exc_info() )

    # grab expected parse
    expected_error = "  SET TYPES : ERROR : number of fully typed rules not increasing. program is non-terminating. aborting execution..."

    self.assertEqual( actual_results, expected_error )

    # --------------------------------------------------------------- #
    # clean up testing

    IRDB.close()
    os.remove( testDB )


  ################
  #  EXAMPLE 13  #
  ################
  # test setting data types to rule attributes
  # good run
  #@unittest.skip( "working on different example" )
  def test_example13( self ) :

    test_id = "example13"

    # --------------------------------------------------------------- #
    # build empty IR db

    testDB = "./IR.db"
    IRDB   = sqlite3.connect( testDB )
    cursor = IRDB.cursor()
    dedt.createDedalusIRTables(cursor)
    dedt.globalCounterReset()

    # --------------------------------------------------------------- #
    # test rule saves

    inputfile = "./testFiles/example13.ded"
    argDict   = self.getArgDict( inputfile )

    # get custom save path
    argDict[ 'data_save_path' ] = self.custom_save_path( argDict, test_id )
    argDict[ "neg_writes" ]     = ""

    dedt.runTranslator( cursor, inputfile, argDict, "c4" )

    # dump rules
    actual_ruleData = dumpers.ruleAttDump( cursor )

    if self.PRINT_STOP :
      print actual_ruleData

    # expected rules
    expected_ruleData = {'1': {'goalName': 'd', 'goalAttData': [[0, 'X', 'string'], [1, 'Y', 'string'], [2, 'NRESERVED', 'int']], 'subgoalAttData': [['8', 'a', [[0, 'X', 'string'], [1, 'Z', 'int'], [2, 'NRESERVED', 'int']]], ['9', 'b', [[0, 'Z', 'int'], [1, 'Y', 'string'], [2, 'NRESERVED', 'int']]]]}, '0': {'goalName': 'c', 'goalAttData': [[0, 'X', 'string'], [1, 'Y', 'string'], [2, 'NRESERVED', 'int']], 'subgoalAttData': [['6', 'a', [[0, 'X', 'string'], [1, '_', 'int'], [2, 'NRESERVED', 'int']]], ['7', 'd', [[0, '_', 'string'], [1, 'Y', 'string'], [2, 'NRESERVED', 'int']]]]}, '3': {'goalName': 'c_prov0', 'goalAttData': [[0, 'X', 'string'], [1, 'Y', 'string'], [2, 'NRESERVED', 'int']], 'subgoalAttData': [['12', 'a', [[0, 'X', 'string'], [1, '_', 'int'], [2, 'NRESERVED', 'int']]], ['13', 'd', [[0, '_', 'string'], [1, 'Y', 'string'], [2, 'NRESERVED', 'int']]]]}, '2': {'goalName': 'e', 'goalAttData': [[0, 'X', 'string'], [1, 'Y', 'string'], [2, 'NRESERVED', 'int']], 'subgoalAttData': [['10', 'c', [[0, 'X', 'string'], [1, 'Z', 'string'], [2, 'NRESERVED', 'int']]], ['11', 'd', [[0, 'Z', 'string'], [1, 'Y', 'string'], [2, 'NRESERVED', 'int']]]]}, '5': {'goalName': 'e_prov2', 'goalAttData': [[0, 'X', 'string'], [1, 'Y', 'string'], [2, 'Z', 'string'], [3, 'NRESERVED', 'int']], 'subgoalAttData': [['16', 'c', [[0, 'X', 'string'], [1, 'Z', 'string'], [2, 'NRESERVED', 'int']]], ['17', 'd', [[0, 'Z', 'string'], [1, 'Y', 'string'], [2, 'NRESERVED', 'int']]]]}, '4': {'goalName': 'd_prov1', 'goalAttData': [[0, 'X', 'string'], [1, 'Y', 'string'], [2, 'Z', 'int'], [3, 'NRESERVED', 'int']], 'subgoalAttData': [['14', 'a', [[0, 'X', 'string'], [1, 'Z', 'int'], [2, 'NRESERVED', 'int']]], ['15', 'b', [[0, 'Z', 'int'], [1, 'Y', 'string'], [2, 'NRESERVED', 'int']]]]}}

    self.assertEqual( actual_ruleData, expected_ruleData )

    # --------------------------------------------------------------- #
    # clean up testing

    IRDB.close()
    os.remove( testDB )


  #################
  #  EXAMPLE 12B  #
  #################
  # test rule saves to IR db
  # bad subgoal definition in rule with arity error
  #@unittest.skip( "working on different example" )
  def test_example12b( self ) :

    # --------------------------------------------------------------- #
    # build empty IR db

    testDB = "./IR.db"
    IRDB   = sqlite3.connect( testDB )
    cursor = IRDB.cursor()
    dedt.createDedalusIRTables(cursor)
    dedt.globalCounterReset()

    # --------------------------------------------------------------- #
    # test rule saves

    # run program and catch error
    try :
      inputfile = "./testFiles/example12b.ded"

      # get argDict
      argDict = self.getArgDict( inputfile )

      dedt.runTranslator( cursor, inputfile, argDict, "c4" )
    except :
      actual_results = self.getError( sys.exc_info() )

    # grab expected parse
    expected_error = "  SET TYPES : arity error in rule 'pre(X,Pl,NRESERVED) <=  log(X,Pl,NRESERVED),notin bcast(X,1),notin crash(X,X,_,NRESERVED) ;' in subgoal 'bcast'. len(attIDList)==2, len(attTypeList)==3"

    self.assertEqual( actual_results, expected_error )

    # --------------------------------------------------------------- #
    # clean up testing

    IRDB.close()
    os.remove( testDB )


  #################
  #  EXAMPLE 12A  #
  #################
  # test rule saves to IR db
  # tests subgoal negation, subgoal time args, equations, goal time arg
  #@unittest.skip( "working on different example" )
  def test_example12a( self ) :

    # --------------------------------------------------------------- #
    # build empty IR db

    testDB = "./IR.db"
    IRDB   = sqlite3.connect( testDB )
    cursor = IRDB.cursor()
    dedt.createDedalusIRTables(cursor)
    dedt.globalCounterReset()

    # --------------------------------------------------------------- #
    # test rule saves

    inputfile = "./testFiles/example12a.ded"
    dedt.dedToIR( inputfile, cursor, "./settings.ini" )

    # dump rules
    actual_rules = dumpers.ruleDump( cursor )

    # expected rules
    expected_rules = ['missing_log(A,Pl):-log(X,Pl),node(X,A), notin log(A,Pl);', 'pre(X,Pl):-log(X,Pl), notin bcast(X,Pl)@1, notin crash(X,X,_);', 'post(X,Pl):-log(X,Pl), notin missing_log(_,Pl);', 'a(X)@async:-b(X,X2,Y1), notin c(X,Y3),X2==Y,X<Y1,X>Y3;']

    self.assertEqual( actual_rules, expected_rules )

    # --------------------------------------------------------------- #
    # test equation variable saves

    # dump equation variables
    actual_eqnVars = dumpers.eqnDump( cursor )

    # expected equation variables
    expected_eqnVars = {'X2==Y': ['X2', 'Y'], 'X<Y1': ['X', 'Y1'], 'X>Y3': ['X', 'Y3']}

    self.assertEqual( actual_eqnVars, expected_eqnVars )

    # --------------------------------------------------------------- #
    # clean up testing

    IRDB.close()
    os.remove( testDB )


  ################
  #  EXAMPLE 11  #
  ################
  # test fact saves to IR db
  #@unittest.skip( "working on different example" )
  def test_example11( self ) :

    # --------------------------------------------------------------- #
    # build empty IR db

    testDB = "./IR.db"
    IRDB   = sqlite3.connect( testDB )
    cursor = IRDB.cursor()
    dedt.createDedalusIRTables(cursor)
    dedt.globalCounterReset()

    # --------------------------------------------------------------- #

    inputfile = "./testFiles/examples_ft/delivery/bcast_edb.ded"
    dedt.dedToIR( inputfile, cursor, "./settings.ini" )

    # dump facts
    actual_facts = dumpers.factDump( cursor )

    # expected facts
    expected_facts = ['node("a","b")@1;', 'node("a","c")@1;', 'node("b","a")@1;', 'node("b","c")@1;', 'node("c","a")@1;', 'node("c","b")@1;', 'bcast("a","hello")@1;']

    self.assertEqual( actual_facts, expected_facts )

    # --------------------------------------------------------------- #
    # clean up testing

    IRDB.close()
    os.remove( testDB )


  ################
  #  EXAMPLE 10  #
  ################
  # test election parse to test acceptance of aggregates in head
  # and fixed strings in the body 
  #@unittest.skip( "working on different example" )
  def test_example10( self ) :

    # --------------------------------------------------------------- #

    # specify input file path
    inputfile = "./testFiles/example10.ded"
    argDict = self.getArgDict( inputfile )

    # run translator
    actual_parsedLines = dedalusParser.parseDedalus( inputfile, argDict[ "settings" ] )

    # expected parsed lines
    expected_parsedLines = [['rule', {'relationName': 'role_x', 'subgoalListOfDicts': [{'polarity': '', 'subgoalName': 'role_change', 'subgoalAttList': ['N', 'R'], 'subgoalTimeArg': ''}, {'polarity': '', 'subgoalName': 'rank', 'subgoalAttList': ['N', 'R', 'I'], 'subgoalTimeArg': ''}], 'eqnDict': {}, 'goalAttList': ['N', 'max<I>'], 'goalTimeArg': ''}], ['rule', {'relationName': 'new_term', 'subgoalListOfDicts': [{'polarity': '', 'subgoalName': 'term', 'subgoalAttList': ['N', 'T'], 'subgoalTimeArg': ''}, {'polarity': '', 'subgoalName': 'stall', 'subgoalAttList': ['N', 'T'], 'subgoalTimeArg': ''}], 'eqnDict': {}, 'goalAttList': ['N', 'T+1'], 'goalTimeArg': ''}], ['rule', {'relationName': 'lclock_register', 'subgoalListOfDicts': [{'polarity': '', 'subgoalName': 'new_term', 'subgoalAttList': ['N', 'T'], 'subgoalTimeArg': ''}], 'eqnDict': {}, 'goalAttList': ['N', '"Localtime"', 'T'], 'goalTimeArg': ''}]]

    self.assertEqual( actual_parsedLines, expected_parsedLines )


  ###############
  #  EXAMPLE 9  #
  ###############
  # test deliv_assert parse
  #@unittest.skip( "working on different example" )
  def test_example9( self ) :

    # --------------------------------------------------------------- #

    # specify input file path
    inputfile = "./testFiles/examples_ft/delivery/deliv_assert.ded"
    argDict   = self.getArgDict( inputfile )

    # run translator
    actual_parsedLines = dedalusParser.parseDedalus( inputfile, argDict[ "settings" ] )

    # expected parsed lines
    expected_parsedLines = [['rule', {'relationName': 'missing_log', 'subgoalListOfDicts': [{'polarity': '', 'subgoalName': 'log', 'subgoalAttList': ['X', 'Pl'], 'subgoalTimeArg': ''}, {'polarity': '', 'subgoalName': 'node', 'subgoalAttList': ['X', 'A'], 'subgoalTimeArg': ''}, {'polarity': 'notin', 'subgoalName': 'log', 'subgoalAttList': ['A', 'Pl'], 'subgoalTimeArg': ''}], 'eqnDict': {}, 'goalAttList': ['A', 'Pl'], 'goalTimeArg': ''}], ['rule', {'relationName': 'pre', 'subgoalListOfDicts': [{'polarity': '', 'subgoalName': 'log', 'subgoalAttList': ['X', 'Pl'], 'subgoalTimeArg': ''}, {'polarity': 'notin', 'subgoalName': 'bcast', 'subgoalAttList': ['X', 'Pl'], 'subgoalTimeArg': '1'}], 'eqnDict': {}, 'goalAttList': ['X', 'Pl'], 'goalTimeArg': ''}], ['rule', {'relationName': 'post', 'subgoalListOfDicts': [{'polarity': '', 'subgoalName': 'log', 'subgoalAttList': ['X', 'Pl'], 'subgoalTimeArg': ''}, {'polarity': 'notin', 'subgoalName': 'missing_log', 'subgoalAttList': ['_', 'Pl'], 'subgoalTimeArg': ''}], 'eqnDict': {}, 'goalAttList': ['X', 'Pl'], 'goalTimeArg': ''}]]

    self.assertEqual( actual_parsedLines, expected_parsedLines )


  ###############
  #  EXAMPLE 8  #
  ###############
  # test the dedalus parser
  #@unittest.skip( "working on different example" )
  def test_example8( self ) :

    # ====================================================== #
    # test 0 : good fact line
    # specify input file path

    inputfile = "./testFiles/example8_0.ded"
    argDict   = self.getArgDict( inputfile )

    actualParsedLines   = dedalusParser.parseDedalus( inputfile, argDict[ "settings" ] )
    expectedParsedLines = [['fact', {'dataList': ['"a"', '"b"'], 'relationName': 'node', 'factTimeArg': '1'}]]
    self.assertEqual( actualParsedLines, expectedParsedLines )

    # ====================================================== #
    # test 1 : bad fact line = missing '('
    # specify input file path

    dedLine = 'node"a","b")@1;'

    # run program
    try :
      actualParsedLines = dedalusParser.parse( dedLine, argDict[ "settings" ] )

    # something broke. save output as a single string
    except :
      actual_results = self.getError( sys.exc_info() )

    # grab expected error
    expected_results = "  SANITY CHECK SYNTAX FACT : ERROR : invalid syntax in line '" + dedLine + "'\n    line contains fewer than one '('\n"

    self.assertEqual( actual_results, expected_results )

    # ====================================================== #
    # test 2 : bad fact line = missing ')'
    # specify input file path

    dedLine = 'node("a","b"@1;'

    # run program
    try :
      actualParsedLines = dedalusParser.parse( dedLine, argDict[ "settings" ] )

    # something broke. save output as a single string
    except :
      actual_results = self.getError( sys.exc_info() )

    # grab expected error
    expected_results = "  SANITY CHECK SYNTAX FACT : ERROR : invalid syntax in line '" + dedLine + "'\n    line contains fewer than one ')'\n"

    self.assertEqual( actual_results, expected_results )

    # ====================================================== #
    # test 3 : bad fact line = more than 1 '('
    # specify input file path

    dedLine = 'node(("a","b")@1;'

    # run program
    try :
      actualParsedLines = dedalusParser.parse( dedLine, argDict[ "settings" ] )

    # something broke. save output as a single string
    except :
      actual_results = self.getError( sys.exc_info() )

    # grab expected error
    expected_results = "  SANITY CHECK SYNTAX FACT : ERROR : invalid syntax in line '" + dedLine + "'\n    line contains more than one '('\n"

    self.assertEqual( actual_results, expected_results )

    # ====================================================== #
    # test 4 : bad fact line = more than 1 ')'
    # specify input file path
    
    dedLine = 'node("a","b"))@1;'
    
    # run program
    try :
      actualParsedLines = dedalusParser.parse( dedLine, argDict[ "settings" ] )
  
    # something broke. save output as a single string
    except :
      actual_results = self.getError( sys.exc_info() )

    # grab expected error
    expected_results = "  SANITY CHECK SYNTAX FACT : ERROR : invalid syntax in line '" + dedLine + "'\n    line contains more than one ')'\n"

    self.assertEqual( actual_results, expected_results )

    # ====================================================== #
    # test 5 : bad fact line = missing pair of double quotes
    # specify input file path
   
    dedLine = 'node("a","b)@1;'
   
    # run program
    try :
      actualParsedLines = dedalusParser.parse( dedLine, argDict[ "settings" ] )

    # something broke. save output as a single string
    except :
      actual_results = self.getError( sys.exc_info() )

    # grab expected error
    expected_results = '  SANITY CHECK SYNTAX FACT : ERROR : invalid syntax in fact \'node("a","b)@1;\'\n    fact definition contains string data not surrounded by either exactly two single quotes or exactly two double quotes : "b\n'

    self.assertEqual( actual_results, expected_results )

    # ====================================================== #
    # test 6 : bad fact line = missing pair of single quotes
    # specify input file path

    dedLine = "node(a','b')@1;"

    # run program
    try :
      actualParsedLines = dedalusParser.parse( dedLine, argDict[ "settings" ] )

    # something broke. save output as a single string
    except :
      actual_results = self.getError( sys.exc_info() )

    # grab expected error
    expected_results = "  SANITY CHECK SYNTAX FACT : ERROR : invalid syntax in fact 'node(a','b')@1;'\n    fact definition contains string data not surrounded by either exactly two single quotes or exactly two double quotes : a'\n"

    self.assertEqual( actual_results, expected_results )

    # ====================================================== #
    # test 6 : bad fact line = missing quotes on string data
    # specify input file path
    
    dedLine = "node(a,'b')@1;"
    
    # run program
    try :
      actualParsedLines = dedalusParser.parse( dedLine, argDict[ "settings" ] )

    # something broke. save output as a single string
    except :
      actual_results = self.getError( sys.exc_info() )

    # grab expected error
    expected_results = "  SANITY CHECK SYNTAX FACT : ERROR : invalid syntax in fact 'node(a,'b')@1;'\n    fact definition contains string data not surrounded by either exactly two single quotes or exactly two double quotes : a\n"

    self.assertEqual( actual_results, expected_results )

    # ====================================================== #
    # test 7 : good fact line = tests integer with no quotes
    # specify input file path
   
    dedLine = "node(1,'b')@1;"
   
    # run program
    actualParsedLines = dedalusParser.parse( dedLine, argDict[ "settings" ] )

    # grab expected error
    expectedParsedLines = ['fact', {'dataList': ['1', "'b'"], 'relationName': 'node', 'factTimeArg': '1'}]
    
    self.assertEqual( actualParsedLines, expectedParsedLines )

    # ====================================================== #
    # test 8 : bad line = missing semicolon
    # specify input file path

    dedLine = "node(1,'b')@1"

    # run program
    try :
      actualParsedLines = dedalusParser.parse( dedLine, argDict[ "settings" ] )

    # something broke. save output as a single string
    except :
      actual_results = self.getError( sys.exc_info() )

    # grab expected error
    expected_results = "  PARSE : ERROR : missing semicolon in line 'node(1,'b')@1'"

    self.assertEqual( actual_results, expected_results )

    # ====================================================== #
    # test 9 : bad line = not parsable b/c missing semi colon
    # specify input file path

    dedLine = "node(1,'b')@1 node('a','b')@1;"

    # run program
    try :
      actualParsedLines = dedalusParser.parse( dedLine, argDict[ "settings" ] )

    # something broke. save output as a single string
    except :
      actual_results = self.getError( sys.exc_info() )

    # grab expected error
    expected_results = "  SANITY CHECK SYNTAX FACT : ERROR : invalid syntax in line 'node(1,'b')@1 node('a','b')@1;'\n    line contains more than one '('\n"

    self.assertEqual( actual_results, expected_results )

    # ====================================================== #
    # test 9a : bad line = not parsable b/c missing time arg
    # specify input file path

    dedLine = "node(1,'b')@;"

    # run program
    try :
      actualParsedLines = dedalusParser.parse( dedLine, argDict[ "settings" ] )

    # something broke. save output as a single string
    except :
      actual_results = self.getError( sys.exc_info() )

    # grab expected error
    expected_results = "  SANITY CHECK SYNTAX FACT : ERROR : invalid syntax in fact data list '" + str( dedLine ) + "'\n    fact definition has no time arg."

    self.assertEqual( actual_results, expected_results )

    # ====================================================== #
    # test 9b : bad line = not parsable b/c missing time arg
    # specify input file path

    dedLine = "node(1,'b');"

    # run program
    try :
      actualParsedLines = dedalusParser.parse( dedLine, argDict[ "settings" ] )

    # something broke. save output as a single string
    except :
      actual_results = self.getError( sys.exc_info() )

    # grab expected error
    expected_results = "  SANITY CHECK SYNTAX FACT : ERROR : invalid syntax in line 'node(1,'b');'\n    line does not contain a time argument.\n"

    self.assertEqual( actual_results, expected_results )

    # ====================================================== #
    # test 10 : good rule line with equations, goal time arg, subgoal time arg, negation
    # specify input file path
    
    dedLine = "a(X,Y)@async:-X>Y,b(X,Y)@2,X==Y, notin c(X,Y)@1,X>=Y;"
    
    # run program
    actualParse = dedalusParser.parse( dedLine, argDict[ "settings" ] )
  
    # grab expected parse
    expectedParse = ['rule', {'relationName': 'a', 'subgoalListOfDicts': [{'polarity': '', 'subgoalName': 'b', 'subgoalAttList': ['X', 'Y'], 'subgoalTimeArg': '2'}, {'polarity': 'notin', 'subgoalName': 'c', 'subgoalAttList': ['X', 'Y'], 'subgoalTimeArg': '1'}], 'eqnDict': {'X>Y': ['X', 'Y'], 'X>=Y': ['X', 'Y'], 'X==Y': ['X', 'Y']}, 'goalAttList': ['X', 'Y'], 'goalTimeArg': 'async'}]

    self.assertEqual( actualParse, expectedParse )

    # ====================================================== #
    # test 11 : bad rule line. fails paren precheck for ')'
    # specify input file path

    dedLine = "a(X,Y)@next:-X>Y,b(X,Y@2,X==Y, notin c(Y)@1,X>=Y;"

    # run program and catch error
    try :
      actualParse = dedalusParser.parse( dedLine, argDict[ "settings" ] )
    except :
      actual_results = self.getError( sys.exc_info() )

    # grab expected parse
    expected_error = "  SANITY CHECK SYNTAX RULE : ERROR : invalid syntax in line '" + dedLine + "'\n    rule contains inconsistent counts for '(' and ')'"

    self.assertEqual( actual_results, expected_error )

    # ====================================================== #
    # test 12 : bad rule line. fails paren precheck for '('
    # specify input file path

    dedLine = "a(X,Y)@next:-X>Y,b(X,Y)@2,X==Y, notin cY)@1,X>=Y;"

    # run program and catch error
    try :
      actualParse = dedalusParser.parse( dedLine, argDict[ "settings" ] )
    except :
      actual_results = self.getError( sys.exc_info() )

    # grab expected parse
    expected_error = "  SANITY CHECK SYNTAX RULE : ERROR : invalid syntax in line '" + dedLine + "'\n    rule contains inconsistent counts for '(' and ')'"

    self.assertEqual( actual_results, expected_error )

    # ====================================================== #
    # test 13 : bad rule line. fails single quote pre check
    # specify input file path

    dedLine = "a(X,Y)@next:-X>Y,b(X,Y)@2,X=='thing, notin c(Y)@1,X>=Y;"

    # run program and catch error
    try :
      actualParse = dedalusParser.parse( dedLine, argDict[ "settings" ] )
    except :
      actual_results = self.getError( sys.exc_info() )

    # grab expected parse
    expected_error = "  SANITY CHECK SYNTAX RULE : ERROR : invalid syntax in line '" + dedLine + "'\n    rule contains inconsistent use of single quotes."

    self.assertEqual( actual_results, expected_error )

    # ====================================================== #
    # test 14 : bad rule line. fails double quote pre check
    # specify input file path

    dedLine = 'a(X,Y)@next:-X>Y,b(X,Y)@2,X==thing", notin c(Y)@1,X>=Y;'

    # run program and catch error
    try :
      actualParse = dedalusParser.parse( dedLine, argDict[ "settings" ] )
    except :
      actual_results = self.getError( sys.exc_info() )

    # grab expected parse
    expected_error = "  SANITY CHECK SYNTAX RULE : ERROR : invalid syntax in line '" + dedLine + "'\n    rule contains inconsistent use of single quotes."

    self.assertEqual( actual_results, expected_error )

    # ====================================================== #
    # test 15 : bad rule line. fails goal attribute capitalization post check
    # specify input file path

    dedLine = 'a(x,Y)@async:-X>Y,b(X,Y)@2,X=="thing", notin c(X,Y)@1,X>=Y;'

    # run program and catch error
    try :
      actualParse = dedalusParser.parse( dedLine, argDict[ "settings" ] )
    except :
      actual_results = self.getError( sys.exc_info() )

    # grab expected parse
    expected_error = "  SANITY CHECK SYNTAX RULE : ERROR : invalid syntax in line '" + dedLine + "'\n    the goal contains contains an attribute not starting with a capitalized letter: 'x'. \n    attribute variables must start with an upper case letter." 

    self.assertEqual( actual_results, expected_error )

    # ====================================================== #
    # test 16 : bad rule line. fails subgoal attribute capitalization post check
    # specify input file path
    
    dedLine = 'a(Xasdf,Yasdf)@async:-Xasdf>Yasdf,b(Xasdf,blah)@2,Xadsf=="thing", notin c(Xasdf)@1,Xasdf>=Yasd;'
    
    # run program and catch error
    try :
      actualParse = dedalusParser.parse( dedLine, argDict[ "settings" ] )
    except :
      actual_results = self.getError( sys.exc_info() )

    # grab expected parse
    expected_error = "  SANITY CHECK SYNTAX RULE : ERROR : invalid syntax in line '" + dedLine + "'\n    subgoal 'b' contains an attribute not starting with a capitalized letter: 'blah'. \n    attribute variables must start with an upper case letter." 

    self.assertEqual( actual_results, expected_error )

    # ====================================================== #
    # test 17 : bad rule line. fails goal name lower case requirement post check
    # specify input file path
    
    dedLine = 'A(Xasdf,Yasdf)@async:-Xasdf>Yasdf,b(Xasdf,Blah)@2,Xadsf=="thing", notin c(Xasdf)@1,Xasdf>=Yasd;'
    
    # run program and catch error
    try :
      actualParse = dedalusParser.parse( dedLine, argDict[ "settings" ] )
    except :
      actual_results = self.getError( sys.exc_info() )

    # grab expected parse
    expected_error = "  SANITY CHECK SYNTAX RULE : ERROR : invalid syntax in line '" + dedLine + "'\n    The goal name 'A' contains an upper-case letter. \n    relation names must contain only lower-case characters."
    
    self.assertEqual( actual_results, expected_error )

    # ====================================================== #
    # test 18 : bad rule line. fails subgoal name lower case requirement post check
   
    dedLine = 'a(Xasdf,Yasdf)@async:-Xasdf>Yasdf,b(Xasdf,Blah)@2,Xadsf=="thing", notin Cat(Xasdf)@1,Xasdf>=Yasd;'
   
    # run program and catch error
    try :
      actualParse = dedalusParser.parse( dedLine, argDict[ "settings" ] )
    except :
      actual_results = self.getError( sys.exc_info() )

    # grab expected parse
    expected_error = "  SANITY CHECK SYNTAX RULE : ERROR : invalid syntax in line '" + dedLine + "'\n    The subgoal name 'Cat' contains an upper-case letter. \n    relation names must contain only lower-case characters."

    self.assertEqual( actual_results, expected_error )

    # ====================================================== #
    # test 19 : bad rule line. not all subgoals in next rule 
    #           have identical first attributes.
   
    dedLine = 'a(Xasdf,Yasdf)@next:-Xasdf>Yasdf,b(Xasdf,Blah)@2,Xadsf=="thing", notin Cat(Yasdf)@1,Xasdf>=Yasd;'
   
    # run program and catch error
    try :
      actualParse = dedalusParser.parse( dedLine, argDict[ "settings" ] )
    except :
      actual_results = self.getError( sys.exc_info() )

    # grab expected parse
    expected_error = '  SANITY CHECK SYNTAX RULE : ERROR : invalid syntax in line \n\'a(Xasdf,Yasdf)@next:-Xasdf>Yasdf,b(Xasdf,Blah)@2,Xadsf=="thing", notin Cat(Yasdf)@1,Xasdf>=Yasd;\'\n    all subgoals in next and async rules must have identical first attributes.\n'

    self.assertEqual( actual_results, expected_error )



  ###############
  #  EXAMPLE 7  #
  ###############
  # test use of file includes
  @unittest.skip( "deprecated." )
  def test_example7( self ) :

    # --------------------------------------------------------------- #
    # testing set up.
    testDB = "./IR.db"
    IRDB    = sqlite3.connect( testDB )
    cursor  = IRDB.cursor()

    # --------------------------------------------------------------- #
    # runs through function to make sure it finishes with expected error

    # specify input file path
    inputfile = os.getcwd() + "/testFiles/simplog_driver.ded"

    actualFileList = tools.get_all_include_file_paths( inputfile )

    expectedFileList_bulk = ['/Users/KsComp/projects/iapyx/qa/testFiles/examples_ft/delivery/bcast_edb.ded', '/Users/KsComp/projects/iapyx/qa/testFiles/examples_ft/delivery/deliv_assert.ded', '/Users/KsComp/projects/iapyx/qa/testFiles/examples_ft/delivery/simplog.ded', '/Users/KsComp/projects/iapyx/qa/testFiles/examples_ft/delivery/simplog_driver.ded']

    expectedFileList_individual = ['/Users/KsComp/projects/iapyx/qa/testFiles/./examples_ft/delivery/./bcast_edb.ded', '/Users/KsComp/projects/iapyx/qa/testFiles/./examples_ft/delivery/simplog.ded', '/Users/KsComp/projects/iapyx/qa/testFiles/./examples_ft/delivery/deliv_assert.ded', '/Users/KsComp/projects/iapyx/qa/testFiles/simplog_driver.ded']

    # need to branch on whether tests are run in bulk or individually???
    if actualFileList == expectedFileList_bulk :
      self.assertEqual( actualFileList, expectedFileList_bulk )
    else :
      self.assertEqual( actualFileList, expectedFileList_individual )

    # --------------------------------------------------------------- #
    # clean up testing
    IRDB.close()
    os.remove( testDB )


  #################
  #  EXAMPLE 6 D  #
  #################
  # example 6 details an incorrect program.
  # tests ded to c4 datalog translation using f(X) :- e(X)@1 ;
  #@unittest.skip( "working on different example" )
  def test_example6d( self ) :

    # --------------------------------------------------------------- #
    # testing set up.
    testDB = "./IR.db"
    IRDB    = sqlite3.connect( testDB )
    cursor  = IRDB.cursor()

    # --------------------------------------------------------------- #
    #dependency
    #dedt.createDedalusIRTables(cursor)
    dedt.globalCounterReset()

    # --------------------------------------------------------------- #
    #runs through function to make sure it finishes with expected error

    # specify input file path
    inputfile = "./testFiles/example6d.ded"

    # get argDict
    argDict = self.getArgDict( inputfile )

    # run program and catch error
    try :
      # run translator
      programData = dedt.translateDedalus( argDict, cursor )
    except :
      actual_results = self.getError( sys.exc_info() )

    # grab expected parse
    expected_error = "  SANITY CHECK SYNTAX RULE POST CHECKS : ERROR :  invalid syntax in line \n'f(X):-e(X)@1;'\n    line at least one positive subgoal must not be annotated with a numeric time argument."

    self.assertEqual( actual_results, expected_error )

    # --------------------------------------------------------------- #
    #clean up testing
    IRDB.close()
    os.remove( testDB )


  #################
  #  EXAMPLE 6 C  #
  #################
  # example 6 details a correct program.
  # tests ded to c4 datalog translation using f(X)@async :- e(X)@1 ;
  # make sure this test produces the expected olg program.
  #@unittest.skip( "working on different example" )
  def test_example6c( self ) :

    # --------------------------------------------------------------- #
    # testing set up.
    testDB = "./IR.db"
    IRDB    = sqlite3.connect( testDB )
    cursor  = IRDB.cursor()

    # --------------------------------------------------------------- #
    #dependency
    #dedt.createDedalusIRTables(cursor)
    dedt.globalCounterReset()

    # --------------------------------------------------------------- #
    #runs through function to make sure it finishes with expected error

    # specify input file path
    inputfile = "./testFiles/example6c.ded"

    # get argDict
    argDict = self.getArgDict( inputfile )
    argDict[ "neg_writes" ]     = ""

    # run translator
    programData = dedt.translateDedalus( argDict, cursor )

    # portray actual output program lines as a single string
    actual_results = self.getActualResults( programData )

    if self.PRINT_STOP :
      print actual_results
      sys.exit( "print stop." )

    # grab expected output results as a string
    expected_results_path = "./testFiles/example6c.olg"
    expected_results      = None
    with open( expected_results_path, 'r' ) as expectedFile :
      expected_results = expectedFile.read()

    self.assertEqual( actual_results, expected_results )

    # --------------------------------------------------------------- #
    #clean up testing
    IRDB.close()
    os.remove( testDB )


  #################
  #  EXAMPLE 6 B  #
  #################
  # example 6 details a correct program.
  # tests ded to c4 datalog translation using f(X)@next :- e(X)@1 ;
  # make sure this test produces the expected olg program.
  #@unittest.skip( "working on different example" )
  def test_example6b( self ) :

    # --------------------------------------------------------------- #
    # testing set up.
    testDB = "./IR.db"
    IRDB    = sqlite3.connect( testDB )
    cursor  = IRDB.cursor()

    # --------------------------------------------------------------- #
    #dependency
    #dedt.createDedalusIRTables(cursor)
    dedt.globalCounterReset()

    # --------------------------------------------------------------- #
    #runs through function to make sure it finishes with expected error

    # specify input file path
    inputfile = "./testFiles/example6b.ded"

    # get argDict
    argDict = self.getArgDict( inputfile )
    argDict[ "neg_writes" ]     = ""

    # run translator
    programData = dedt.translateDedalus( argDict, cursor )

    # portray actual output program lines as a single string
    actual_results = self.getActualResults( programData )

    if self.PRINT_STOP :
      print actual_results
      sys.exit( "print stop." )

    # grab expected output results as a string
    expected_results_path = "./testFiles/example6b.olg"
    expected_results      = None
    with open( expected_results_path, 'r' ) as expectedFile :
      expected_results = expectedFile.read()

    self.assertEqual( actual_results, expected_results )

    # --------------------------------------------------------------- #
    #clean up testing
    IRDB.close()
    os.remove( testDB )


  #################
  #  EXAMPLE 6 A  #
  #################
  # example 6 details a correct program.
  # tests ded to c4 datalog translation.
  # make sure this test produces the expected olg program.
  #@unittest.skip( "working on different example" )
  def test_example6a( self ) :

    # --------------------------------------------------------------- #
    # testing set up.
    testDB = "./IR.db"
    IRDB    = sqlite3.connect( testDB )
    cursor  = IRDB.cursor()

    # --------------------------------------------------------------- #
    #dependency
    #dedt.createDedalusIRTables(cursor)
    dedt.globalCounterReset()

    # --------------------------------------------------------------- #
    #runs through function to make sure it finishes with expected error

    # specify input file path
    inputfile = "./testFiles/example6a.ded"

    # get argDict
    argDict = self.getArgDict( inputfile )
    argDict[ "neg_writes" ]     = ""

    # run translator
    programData = dedt.translateDedalus( argDict, cursor )

    # portray actual output program lines as a single string
    actual_results = self.getActualResults( programData )

    if self.PRINT_STOP :
      print actual_results
      sys.exit( "print stop." )

    # grab expected output results as a string
    expected_results_path = "./testFiles/example6a.olg"
    expected_results      = None
    with open( expected_results_path, 'r' ) as expectedFile :
      expected_results = expectedFile.read()

    self.assertEqual( actual_results, expected_results )

    # --------------------------------------------------------------- #
    #clean up testing
    IRDB.close()
    os.remove( testDB )


  ###############
  #  EXAMPLE 5  #
  ###############
  # example 5 details an erroneous program.
  # make sure this test produces the expected error message.
  #@unittest.skip( "working on different example" )
  def test_example5( self ) :

    # --------------------------------------------------------------- #
    #testing set up. dedToIR has dependency
    #on createDedalusIRTables so that's
    #tested first above.
    testDB = "./IR.db"
    IRDB    = sqlite3.connect( testDB )
    cursor  = IRDB.cursor()

    # --------------------------------------------------------------- #
    #dependency
    dedt.createDedalusIRTables(cursor)
    dedt.globalCounterReset()

    # --------------------------------------------------------------- #
    #runs through function to make sure it finishes with expected error

    # specify input file path
    inputfile = "./testFiles/example5.ded"

    # get argDict
    argDict = self.getArgDict( inputfile )

    # run translator
    try :
      programData = dedt.translateDedalus( argDict, cursor )

      # portray actual output program lines as a single string
      actual_results = self.getActualResults( programData )

    # something broke. save output as a single string
    except :
      actual_results = self.getError( sys.exc_info() )

    # grab expected output results as a string
    expected_error = "  SANITY CHECK SYNTAX RULE : ERROR : invalid syntax in line 'a(X):-;'\n    rule contains no detected subgoals."

    self.assertEqual( actual_results, expected_error )

    # --------------------------------------------------------------- #
    #clean up testing
    IRDB.close()
    os.remove( testDB )


  ###############
  #  EXAMPLE 4  #
  ###############
  # example 4 details an erroneous program.
  # make sure this test produces the expected error message.
  #@unittest.skip( "working on different example" )
  def test_example4( self ) :

    # --------------------------------------------------------------- #
    #testing set up. dedToIR has dependency
    #on createDedalusIRTables so that's
    #tested first above.
    testDB = "./IR.db"
    IRDB    = sqlite3.connect( testDB )
    cursor  = IRDB.cursor()

    # --------------------------------------------------------------- #
    #dependency
    dedt.createDedalusIRTables(cursor)
    dedt.globalCounterReset()

    # --------------------------------------------------------------- #
    #runs through function to make sure it finishes with expected error

    # specify input file path
    inputfile = "./testFiles/example4.ded"

    # get argDict
    argDict = self.getArgDict( inputfile )

    # run translator
    try :
      programData = dedt.translateDedalus( argDict, cursor )

      # portray actual output program lines as a single string
      actual_results = self.getActualResults( programData )

    # something broke. save output as a single string
    except :
      actual_results = self.getError( sys.exc_info() )

    # grab expected error
    expected_error = "  SANITY CHECK SYNTAX FACT : ERROR : invalid syntax in line 'b(A)c(A);'\n    line does not contain a time argument.\n"

    self.assertEqual( actual_results, expected_error )

    # --------------------------------------------------------------- #
    #clean up testing
    IRDB.close()
    os.remove( testDB )


  ###############
  #  EXAMPLE 3  #
  ###############
  # example 3 details an erroneous program.
  # make sure this test produces the expected error message.
  #@unittest.skip( "working on different example" )
  def test_example3( self ) :
 
    # --------------------------------------------------------------- #
    #testing set up. dedToIR has dependency
    #on createDedalusIRTables so that's
    #tested first above.
    testDB = "./IR.db"
    IRDB    = sqlite3.connect( testDB )
    cursor  = IRDB.cursor()
 
    # --------------------------------------------------------------- #
    #dependency
    dedt.createDedalusIRTables(cursor)
    dedt.globalCounterReset()

    # --------------------------------------------------------------- #
    #runs through function to make sure it finishes with expected error

    # specify input file path
    inputfile = "./testFiles/example3.ded"

    # get argDict
    argDict = self.getArgDict( inputfile )

    # run translator
    try :
      programData = dedt.translateDedalus( argDict, cursor )
      # portray actual output program lines as a single string
      actual_results = self.getActualResults( programData )

    # something broke. save output as a single string
    except :
      actual_results = self.getError( sys.exc_info() )

    # grab expected error
    expected_error = "  SANITY CHECK SYNTAX RULE : ERROR : invalid syntax in line 'b(a):-!@$#@$;'\n    rule contains no detected subgoals."
   
    self.assertEqual( actual_results, expected_error )
    
    # --------------------------------------------------------------- #
    #clean up testing
    IRDB.close()
    os.remove( testDB )

  ###############
  #  EXAMPLE 2  #
  ###############
  # example 2 details an erroneous program.
  # make sure this test produces the expected error message.
  #@unittest.skip( "working on different example" )
  def test_example2( self ) :
 
    # --------------------------------------------------------------- #
    #testing set up. dedToIR has dependency
    #on createDedalusIRTables so that's
    #tested first above.
    testDB = "./IR.db"
    IRDB    = sqlite3.connect( testDB )
    cursor  = IRDB.cursor()
 
    # --------------------------------------------------------------- #
    #dependency
    dedt.createDedalusIRTables(cursor)
    dedt.globalCounterReset()

    # --------------------------------------------------------------- #
    #runs through function to make sure it finishes with expected error

    # specify input file path
    inputfile = "./testFiles/example2.ded"

    # get argDict
    argDict = self.getArgDict( inputfile )

    # run translator
    try :
      programData = dedt.translateDedalus( argDict, cursor )
      # portray actual output program lines as a single string
      actual_results = self.getActualResults( programData )

    # something broke. save output as a single string
    except :
      actual_results = self.getError( sys.exc_info() )

    # grab expected output results as a string
    expected_error = '  PARSE : ERROR : missing semicolon in line \'b("a","a")\''

    self.assertEqual( actual_results, expected_error )
    
    # --------------------------------------------------------------- #
    #clean up testing
    IRDB.close()
    os.remove( testDB )


  ###############
  #  EXAMPLE 1  #
  ###############
  # test input of one good fact
  #@unittest.skip( "working on different example" )
  def test_example1( self ) :
 
    test_id = "example1"
 
    # --------------------------------------------------------------- #
    #testing set up. dedToIR has dependency
    #on createDedalusIRTables so that's
    #tested first above.
    testDB = "./IR.db"
    IRDB    = sqlite3.connect( testDB )
    cursor  = IRDB.cursor()
  
    # --------------------------------------------------------------- #
    #dependency
    dedt.createDedalusIRTables(cursor)
    dedt.globalCounterReset()

    # --------------------------------------------------------------- #
    #runs through function to make sure it finishes without error

    # specify input file path
    inputfile = "./testFiles/example1.ded"

    # get argDict
    argDict = self.getArgDict( inputfile )

    # get custom save path
    argDict[ 'data_save_path' ] = self.custom_save_path( argDict, test_id )
    argDict[ "neg_writes" ]     = ""

    # run translator
    programData = dedt.translateDedalus( argDict, cursor )

    # portray actual output program lines as a single string
    actual_results = self.getActualResults( programData )

    # grab expected output results as a string
    expected_results_path = "./testFiles/example1.olg"
    expected_results      = None
    with open( expected_results_path, 'r' ) as expectedFile :
      expected_results = expectedFile.read()

    self.assertEqual( actual_results, expected_results )

    # --------------------------------------------------------------- #
    #clean up testing
    IRDB.close()
    os.remove( testDB )


  ###################
  #  EXAMPLE EMPTY  #
  ###################
  # input empty
  #@unittest.skip( "working on different example" )
  def test_example_empty( self ) :

    # --------------------------------------------------------------- #
    #testing set up. dedToIR has dependency
    #on createDedalusIRTables so that's
    #tested first above.
    testDB = "./IR.db"
    IRDB    = sqlite3.connect( testDB )
    cursor  = IRDB.cursor()

    # --------------------------------------------------------------- #
    #dependency
    dedt.createDedalusIRTables(cursor)
    dedt.globalCounterReset()

    # --------------------------------------------------------------- #
    #runs through function to make sure it finishes without error

    # specify input file path
    inputfile = "./testFiles/example_empty.ded"

    # get argDict
    argDict = self.getArgDict( inputfile )
    argDict[ "neg_writes" ]     = ""

    # run translator
    programData = dedt.translateDedalus( argDict, cursor )

    # portray actual output program lines as a single string
    actual_results = self.getActualResults( programData )

    # grab expected output results as a string
    expected_results_path = "./testFiles/example_empty.olg"
    expected_results      = None
    with open( expected_results_path, 'r' ) as expectedFile :
      expected_results = expectedFile.read()

    #print "expected_results:" + str( expected_results )
    self.assertEqual( actual_results, expected_results )

    # --------------------------------------------------------------- #
    #clean up testing
    IRDB.close()
    os.remove( testDB )


  #################################
  #  EXAMPLE EMPTY WITH COMMENTS  #
  #################################
  # input empty file with comments
  #@unittest.skip( "working on different example" )
  def test_example_empty_with_comments( self ) :

    # --------------------------------------------------------------- #
    #testing set up. dedToIR has dependency
    #on createDedalusIRTables so that's
    #tested first above.
    testDB = "./IR.db"
    IRDB    = sqlite3.connect( testDB )
    cursor  = IRDB.cursor()

    # --------------------------------------------------------------- #
    #dependency
    dedt.createDedalusIRTables(cursor)
    dedt.globalCounterReset()

    # --------------------------------------------------------------- #
    #runs through function to make sure it finishes without error

    # specify input file path
    inputfile = "./testFiles/example_empty_with_comments.ded"

    # get argDict
    argDict = self.getArgDict( inputfile )
    argDict[ "neg_writes" ] = ""

    # run translator
    programData = dedt.translateDedalus( argDict, cursor )

    # portray actual output program lines as a single string
    actual_results = self.getActualResults( programData )

    # grab expected output results as a string
    expected_results_path = "./testFiles/example_empty_with_comments.olg"
    expected_results      = None
    with open( expected_results_path, 'r' ) as expectedFile :
      expected_results = expectedFile.read()

    #print "expected_results:" + str( expected_results )
    self.assertEqual( actual_results, expected_results )

    # --------------------------------------------------------------- #
    #clean up testing
    IRDB.close()
    os.remove( testDB )


  ##########################
  #  GET CUSTOM SAVE PATH  #
  ##########################
  def custom_save_path( self, argDict, test_id ) :
    if not os.path.exists( argDict[ 'data_save_path' ] ) :
      os.system( "mkdir " + argDict[ 'data_save_path' ] )
    custom_save_path  = argDict[ 'data_save_path' ]
    custom_save_path += test_id
    if not os.path.exists( custom_save_path ) :
      os.system( "mkdir " + custom_save_path )
    return custom_save_path


  ###############
  #  GET ERROR  #
  ###############
  # extract error message from system info
  def getError( self, sysInfo ) :
    return str( sysInfo[1] )


  ########################
  #  GET ACTUAL RESULTS  #
  ########################
  def getActualResults( self, programData ) :
    program_string  = "\n".join( programData[0][0] )
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
    argDict[ 'settings' ]                 = "./settings_files/settings.ini"
    argDict[ 'negative_support' ]         = False
    argDict[ 'strategy' ]                 = None
    argDict[ 'file' ]                     = inputfile
    argDict[ 'EOT' ]                      = 4
    argDict[ 'find_all_counterexamples' ] = False
    argDict[ 'nodes' ]                    = [ "a", "b", "c" ]
    argDict[ 'evaluator' ]                = "c4"
    argDict[ 'EFF' ]                      = 2
    argDict[ 'data_save_path' ]           = "./data/"

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
