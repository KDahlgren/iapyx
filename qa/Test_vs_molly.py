#!/usr/bin/env python

'''
Test_vs_molly.py
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

from dedt  import dedt, dedalusParser, clockRelation, dedalusRewriter
from utils import dumpers, globalCounters, tools

# ------------------------------------------------------ #


############################################################################
#                                                                          #
#  NOTE!!!!                                                                #
#                                                                          #
#    iapyx v. molly comparisons ignore clock and crash fact differences.   #
#                                                                          #
############################################################################


###################
#  TEST VS MOLLY  #
###################
class Test_vs_molly( unittest.TestCase ) :

  #logging.basicConfig( format='%(levelname)s:%(message)s', level=logging.DEBUG )
  logging.basicConfig( format='%(levelname)s:%(message)s', level=logging.INFO )


  #####################
  #  EXAMPLE SIMPLOG  #
  #####################
  # tests ded to c4 datalog for simplog
  #@unittest.skip( "working on different example" )
  def test_simplog( self ) :

    # --------------------------------------------------------------- #
    # testing set up.
    testDB = "./IR.db"
    IRDB    = sqlite3.connect( testDB )
    cursor  = IRDB.cursor()

    # --------------------------------------------------------------- #
    # reset counters for new test

    dedt.globalCounterReset()

    # --------------------------------------------------------------- #
    #runs through function to make sure it finishes with expected error

    # specify input file path
    inputfile = os.getcwd() + "/testFiles/simplog.ded"

    # get argDict
    argDict = self.getArgDict( inputfile )

    # run translator
    programData = dedt.translateDedalus( argDict, cursor )

    # portray actual output program lines as a single string
    iapyx_results = self.getActualResults( programData[0] )

    # ========================================================== #
    # IAPYX COMPARISON
    #
    # grab expected output results as a string
    #
    expected_iapyx_path    = "./testFiles/simplog_iapyx.olg"
    expected_iapyx_results = None
    with open( expected_iapyx_path, 'r' ) as expectedFile :
      expected_iapyx_results = expectedFile.read()

    self.assertEqual( iapyx_results, expected_iapyx_results )

    # ========================================================== #
    # MOLLY COMPARISON
    #
    # grab expected output results as a string
    #
    molly_path    = "./testFiles/simplog_molly.olg"
    molly_results = None
    with open( molly_path, 'r' ) as mollyFile :
      molly_results = mollyFile.read()

    expected_results = self.compareIapyxAndMolly( iapyx_results, molly_results )

    self.assertEqual( True, expected_results )

    # --------------------------------------------------------------- #
    #clean up testing
    IRDB.close()
    os.remove( testDB )


  #############################
  #  COMPARE IAPYX AND MOLLY  #
  #############################
  # compare programs minus all whitespace.
  # ignore clock and crash facts.
  def compareIapyxAndMolly( self, iapyx_results, molly_results ) :

    # ----------------------------------------------------- #
    # grab relevant substring from iapyx results
    iapyx_substring  = iapyx_results.split( "\nclock", 1 )
    iapyx_substring  = iapyx_substring[0]
    iapyx_substring  = iapyx_substring.replace( "\n", "" )                  # remove all newlines
    iapyx_substring  = iapyx_substring.translate( None, string.whitespace ) # remove all whitespace
    iapyx_line_array = iapyx_substring.split( ";" )

    # ----------------------------------------------------- #
    # grab relevant substring from molly results
    molly_substring  = molly_results.split( "\nclock", 1 )
    molly_substring  = molly_substring[0]
    molly_substring  = molly_substring.replace( "\n", "" )                  # remove all newlines
    molly_substring  = molly_substring.translate( None, string.whitespace ) # remove all whitespace
    molly_line_array = molly_substring.split( ";" )

    # ----------------------------------------------------- #
    # make sure lists contain all and only the same elements

    if not len( iapyx_line_array ) == len( molly_line_array ) :
      logging.debug( "  COMPARE IAPYX AND MOLLY : inconsistent number of program statements." )
      return False

    match_elements_flag = False
    for iapyx_line in iapyx_line_array :

      # ignore the crash table
      if "define(crash,{" in iapyx_line :
        pass

      # actually, just skip all defines since molly's using some weird rule to 
      # order goal atts in prov rules.
      elif iapyx_line.startswith( "define(" ) and iapyx_line.endswith( "})" ) :
        pass

      else : # next question : does a matching line exist in the molly table?

        # if line is a rule, need a smarter comparison method
        if self.isRule( iapyx_line ) :

          if iapyx_line in molly_line_array :
            match_elements_flag = True

          elif not self.matchExists( iapyx_line, molly_line_array ) :
            logging.debug( "  COMPARE IAPYX AND MOLLY (1) : iapyx_line '" + iapyx_line + "' not found in molly program." )
            match_elements_flag = False

        # otherwise, line is a fact, so checking existence is sufficient.
        else :
          if not iapyx_line in molly_line_array :
            logging.debug( "  COMPARE IAPYX AND MOLLY (2) : iapyx_line '" + iapyx_line+ "' not found in molly program." )
            match_elements_flag = False

    logging.debug( "  COMPARE IAPYX AND MOLLY : returning match_elements_flag = " + str( match_elements_flag ) )
    return match_elements_flag


  ##################
  #  MATCH EXISTS  #
  ##################
  # check if the iapyx_rule appears in the molly_line_array
  def matchExists( self, iapyx_rule, molly_line_array ) :

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
        if iapyx_goalName == molly_goalName and iapyx_body == molly_body :

          logging.debug( "  MATCH EXISTS : identical goalNames and bodies." )

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

    logging.debug( "  MATCH EXISTS : returning False" )
    return False


  ###################
  #  GET GOAL NAME  #
  ###################
  # extract the goal name from the input rule.
  def getGoalName( self, rule ) :

    goalName = rule.split( "(", 1 )
    goalName = goalName[0]

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
    argDict[ 'settings' ]                 = "./settings.ini"
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
