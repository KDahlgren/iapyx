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
from utils import dumpers, tools

# ------------------------------------------------------ #


###############
#  TEST DEDT  #
###############
class Test_dedt( unittest.TestCase ) :

  logging.basicConfig( format='%(levelname)s:%(message)s', level=logging.DEBUG )
  #logging.basicConfig( format='%(levelname)s:%(message)s', level=logging.INFO )


  ################
  #  EXAMPLE 12  
  ################
  # test rule saves to IR db
  # tests subgoal negation, subgoal time args, equations, goal time arg
  def test_example12( self ) :

    # --------------------------------------------------------------- #
    # build empty IR db

    testDB = "./IR.db"
    IRDB   = sqlite3.connect( testDB )
    cursor = IRDB.cursor()
    dedt.createDedalusIRTables(cursor)

    # --------------------------------------------------------------- #
    # test rule saves

    inputfile = "./testFiles/example12.ded"
    dedt.dedToIR( inputfile, cursor )

    # dump rules
    actual_rules = dumpers.ruleDump( cursor )

    # expected rules
    expected_rules = ['missing_log(A,Pl):-log(X,Pl),node(X,A), notin log(A,Pl);', 'pre(X,Pl):-log(X,Pl), notin bcast(X,Pl)@1, notin crash(X,X,_);', 'post(X,Pl):-log(X,Pl), notin missing_log(_,Pl);', 'a(X)@async:-b(X,X2,Y1), notin c(X2,Y3),X2==Y,X<Y1,X>Y3;']

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
  def test_example11( self ) :

    # --------------------------------------------------------------- #
    # build empty IR db

    testDB = "./IR.db"
    IRDB   = sqlite3.connect( testDB )
    cursor = IRDB.cursor()
    dedt.createDedalusIRTables(cursor)

    # --------------------------------------------------------------- #

    inputfile = "./testFiles/bcast_edb.ded"
    dedt.dedToIR( inputfile, cursor )

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
  def test_example10( self ) :

    # --------------------------------------------------------------- #

    # specify input file path
    inputfile = "./testFiles/election.ded"

    # run translator
    actual_parsedLines = dedalusParser.parseDedalus( inputfile )

    # expected parsed lines
    expected_parsedLines = [['rule', {'relationName': 'role', 'subgoalListOfDicts': \
                            [{'polarity': '', 'subgoalName': 'role', 'subgoalAttList': ['N', 'R'], \
                            'subgoalTimeArg': ''}, {'polarity': 'notin', 'subgoalName': 'role_change', \
                            'subgoalAttList': ['N', '_'], 'subgoalTimeArg': ''}], 'eqnDict': {}, 'goalAttList': \
                            ['N', 'R'], 'goalTimeArg': 'next'}], \
                            ['rule', {'relationName': 'role_x',  \
                             'subgoalListOfDicts': [{'polarity': '', 'subgoalName': 'role_change', \
                             'subgoalAttList': ['N', 'R'], 'subgoalTimeArg': ''}, \
                            {'polarity': '', 'subgoalName': 'rank', 'subgoalAttList': ['N', 'R', 'I'], \
                             'subgoalTimeArg': ''}], 'eqnDict': {}, 'goalAttList': ['N', 'max<I>'], 'goalTimeArg': ''}], \
                            ['rule', {'relationName': 'role', 'subgoalListOfDicts': [{'polarity': '', \
                             'subgoalName': 'role_x', 'subgoalAttList': ['N', 'I'], 'subgoalTimeArg': ''}, 
                            {'polarity': '', 'subgoalName': 'rank', 'subgoalAttList': ['N', 'R', 'I'], 'subgoalTimeArg': ''}], \
                             'eqnDict': {}, 'goalAttList': ['N', 'R'], 'goalTimeArg': 'next'}], \
                            ['rule', {'relationName': 'term', 'subgoalListOfDicts': [{'polarity': '', 'subgoalName': 'term', \
                             'subgoalAttList': ['N', 'T'], 'subgoalTimeArg': ''}, {'polarity': 'notin', 'subgoalName': 'stall', \
                             'subgoalAttList': ['N', 'T'], 'subgoalTimeArg': ''}], 'eqnDict': {}, 'goalAttList': ['N', 'T'], \
                             'goalTimeArg': 'next'}], ['rule', {'relationName': 'term', 'subgoalListOfDicts': [{'polarity': '', \
                             'subgoalName': 'new_term', 'subgoalAttList': ['N', 'T'], 'subgoalTimeArg': ''}], \
                             'eqnDict': {}, 'goalAttList': ['N', 'T'], 'goalTimeArg': 'next'}], \
                             ['rule', {'relationName': 'new_term', 'subgoalListOfDicts': [{'polarity': '', \
                             'subgoalName': 'term', 'subgoalAttList': ['N', 'T'], 'subgoalTimeArg': ''}, \
                             {'polarity': '', 'subgoalName': 'stall', 'subgoalAttList': ['N', 'T'], 'subgoalTimeArg': ''}], \
                             'eqnDict': {}, 'goalAttList': ['N', 'T+1'], 'goalTimeArg': ''}], \
                             ['rule', {'relationName': 'lclock_register', 'subgoalListOfDicts': [{'polarity': '', \
                             'subgoalName': 'new_term', 'subgoalAttList': ['N', 'T'], 'subgoalTimeArg': ''}], 'eqnDict': {}, \
                             'goalAttList': ['N', '"Localtime"', 'T'], 'goalTimeArg': ''}], \
                             ['rule', {'relationName': 'current_term', 'subgoalListOfDicts': \
                             [{'polarity': '', 'subgoalName': 'term', 'subgoalAttList': ['N', 'T'], 'subgoalTimeArg': ''}], \
                             'eqnDict': {}, 'goalAttList': ['N', 'T'], 'goalTimeArg': ''}], \
                             ['rule', {'relationName': 'leader', 'subgoalListOfDicts': [{'polarity': '', 'subgoalName': \
                             'current_term', 'subgoalAttList': ['N', 'T'], 'subgoalTimeArg': ''}, \
                             {'polarity': '', 'subgoalName': 'append_log', 'subgoalAttList': ['N', 'T', 'L', '_', '_', '_', '_', '_'], \
                             'subgoalTimeArg': ''}], 'eqnDict': {}, 'goalAttList': ['N', 'T', 'L'], 'goalTimeArg': ''}], \
                             ['rule', {'relationName': 'last_append', 'subgoalListOfDicts': \
                             [{'polarity': '', 'subgoalName': 'append_log', 'subgoalAttList': \
                             ['Node', 'Term', '_', '_', '_', '_', '_', 'Rcv'], 'subgoalTimeArg': ''}], \
                             'eqnDict': {}, 'goalAttList': ['Node', 'Term', 'max<Rcv>'], 'goalTimeArg': ''}], \
                             ['rule', {'relationName': 'stall', 'subgoalListOfDicts': [{'polarity': '', \
                             'subgoalName': 'lclock', 'subgoalAttList': ['Node', '"Localtime"', 'Term', 'Time'], 'subgoalTimeArg': ''}, \
                             {'polarity': '', 'subgoalName': 'last_append', 'subgoalAttList': ['Node', 'Term', 'Last'], 'subgoalTimeArg': ''}, \
                             {'polarity': '', 'subgoalName': 'current_term', 'subgoalAttList': ['Node', 'Term'], 'subgoalTimeArg': ''}, \
                             {'polarity': 'notin', 'subgoalName': 'role', 'subgoalAttList': ['Node', '"L"'], \
                             'subgoalTimeArg': ''}], 'eqnDict': {'Time-Last>1': ['Time', 'Last', '1']}, \
                             'goalAttList': ['Node', 'Term'], 'goalTimeArg': 'next'}], \
                             ['rule', {'relationName': 'stall', 'subgoalListOfDicts': \
                             [{'polarity': '', 'subgoalName': 'role', 'subgoalAttList': ['Node', '_'], 'subgoalTimeArg': ''}, \
                             {'polarity': 'notin', 'subgoalName': 'append_log', 'subgoalAttList': ['Node', '_', '_', '_', '_', '_', '_', '_'], \
                             'subgoalTimeArg': ''}], 'eqnDict': {}, 'goalAttList': ['Node', '0'], 'goalTimeArg': 'next'}], \
                             ['rule', {'relationName': 'role_change', 'subgoalListOfDicts': [{'polarity': '', \
                             'subgoalName': 'stall', 'subgoalAttList': ['N', '_'], 'subgoalTimeArg': ''}], \
                             'eqnDict': {}, 'goalAttList': ['N', '"C"'], 'goalTimeArg': ''}], \
                             ['rule', {'relationName': 'role_change', 'subgoalListOfDicts': \
                             [{'polarity': '', 'subgoalName': 'append_entries', 'subgoalAttList': ['N', 'T', 'L', '_', '_', '_', '_'], \
                             'subgoalTimeArg': ''}], 'eqnDict': {'L!=N': ['L', 'N']}, \
                             'goalAttList': ['N', '"F"'], 'goalTimeArg': ''}], \
                             ['rule', {'relationName': 'request_vote', 'subgoalListOfDicts': [{'polarity': '', \
                             'subgoalName': 'stall', 'subgoalAttList': ['Candidate', 'Lastlogterm'], 'subgoalTimeArg': ''}, \
                             {'polarity': '', 'subgoalName': 'member', 'subgoalAttList': ['Candidate', 'Node', '_'], 'subgoalTimeArg': ''}, \
                             {'polarity': '', 'subgoalName': 'log_indx', 'subgoalAttList': ['Candidate', 'Lastlogindx'], \
                             'subgoalTimeArg': ''}], 'eqnDict': {}, 'goalAttList': ['Node', 'Lastlogterm+1', 'Candidate', \
                             'Lastlogindx', 'Lastlogterm'], 'goalTimeArg': 'async'}], \
                             ['rule', {'relationName': 'accept_vote', 'subgoalListOfDicts': [{'polarity': '', 'subgoalName': 'winner', \
                             'subgoalAttList': ['Node', 'Term', 'Id'], 'subgoalTimeArg': ''}, \
                             {'polarity': '', 'subgoalName': 'member', 'subgoalAttList': ['Node', 'Candidate', 'Id'], 'subgoalTimeArg': ''}, \
                             {'polarity': '', 'subgoalName': 'log_term', 'subgoalAttList': ['Node', 'Lterm'], 'subgoalTimeArg': ''}], \
                             'eqnDict': {'Lterm<Term': ['Lterm', 'Term']}, 'goalAttList': ['Node', 'Candidate', 'Term'], 'goalTimeArg': ''}], \
                             ['rule', {'relationName': 'winner', 'subgoalListOfDicts': [{'polarity': '', 'subgoalName': 'request_vote', \
                             'subgoalAttList': ['Node', 'Term', 'Candidate', '_', '_'], 'subgoalTimeArg': ''}, \
                             {'polarity': '', 'subgoalName': 'member', 'subgoalAttList': ['Node', 'Candidate', 'Id'], 'subgoalTimeArg': ''}], \
                             'eqnDict': {}, 'goalAttList': ['Node', 'Term', 'min<Id>'], 'goalTimeArg': ''}], \
                             ['rule', {'relationName': 'vote', 'subgoalListOfDicts': [{'polarity': '', \
                             'subgoalName': 'request_vote', 'subgoalAttList': ['Node', 'Term', 'Candidate', '_', '_'], \
                             'subgoalTimeArg': ''}, {'polarity': '', 'subgoalName': 'log_term', 'subgoalAttList': ['Node', 'Lterm'], \
                             'subgoalTimeArg': ''}], 'eqnDict': {'Lterm>Term': ['Lterm', 'Term']}, \
                             'goalAttList': ['Candidate', 'Node', 'Term', '"F"'], 'goalTimeArg': 'async'}], \
                             ['rule', {'relationName': 'vote', 'subgoalListOfDicts': [{'polarity': '', 'subgoalName': 'accept_vote', \
                             'subgoalAttList': ['Node', 'Candidate', 'Term'], 'subgoalTimeArg': ''}], \
                             'eqnDict': {}, 'goalAttList': ['Candidate', 'Node', 'Term', '"T"'], 'goalTimeArg': 'async'}], \
                             ['rule', {'relationName': 'vote_log', 'subgoalListOfDicts': [{'polarity': '', 'subgoalName': 'vote', \
                             'subgoalAttList': ['C', 'N', 'T', 'V'], 'subgoalTimeArg': ''}], 'eqnDict': {}, \
                             'goalAttList': ['C', 'N', 'T', 'V'], 'goalTimeArg': ''}], ['rule', {'relationName': 'vote_log', \
                             'subgoalListOfDicts': [{'polarity': '', 'subgoalName': 'vote_log', 'subgoalAttList': ['C', 'N', 'T', 'V'], \
                             'subgoalTimeArg': ''}], 'eqnDict': {}, 'goalAttList': ['C', 'N', 'T', 'V'], 'goalTimeArg': 'next'}], \
                             ['rule', {'relationName': 'member_cnt', 'subgoalListOfDicts': [{'polarity': '', 'subgoalName': 'member', \
                             'subgoalAttList': ['N', '_', 'M'], 'subgoalTimeArg': ''}], 'eqnDict': {}, 'goalAttList': ['N', 'count<M>'], \
                             'goalTimeArg': ''}], ['rule', {'relationName': 'yes_vote_cnt', 'subgoalListOfDicts': [{'polarity': '', \
                             'subgoalName': 'vote_log', 'subgoalAttList': ['Node', 'Member', 'Term', '"T"'], 'subgoalTimeArg': ''}, \
                             {'polarity': '', 'subgoalName': 'member', 'subgoalAttList': ['Node', 'Member', 'Id'], 'subgoalTimeArg': ''}], \
                             'eqnDict': {}, 'goalAttList': ['Node', 'Term', 'count<Id>'], 'goalTimeArg': ''}], ['rule', {'relationName': \
                             'role_change', 'subgoalListOfDicts': [{'polarity': '', 'subgoalName': 'yes_vote_cnt', 'subgoalAttList': \
                             ['N', '_', 'Cnt1'], 'subgoalTimeArg': ''}, {'polarity': '', 'subgoalName': 'member_cnt', 'subgoalAttList': \
                             ['N', 'Cnt2'], 'subgoalTimeArg': ''}], 'eqnDict': {'Cnt1>Cnt2/2': ['Cnt1', 'Cnt2', '2']}, 'goalAttList': ['N', '"L"'], \
                             'goalTimeArg': ''}], ['rule', {'relationName': 'commit_indx', \
                             'subgoalListOfDicts': [{'polarity': '', 'subgoalName': 'log_term', 'subgoalAttList': ['Node', 'Idx'], \
                             'subgoalTimeArg': ''}], 'eqnDict': {}, 'goalAttList': ['Node', 'Idx'], 'goalTimeArg': ''}], \
                             ['rule', {'relationName': 'member', 'subgoalListOfDicts': [{'polarity': '', 'subgoalName': 'member', \
                             'subgoalAttList': ['N', 'M', 'I'], 'subgoalTimeArg': ''}], 'eqnDict': {}, \
                             'goalAttList': ['N', 'M', 'I'], 'goalTimeArg': 'next'}]]

    self.assertEqual( actual_parsedLines, expected_parsedLines )


  ###############
  #  EXAMPLE 9  #
  ###############
  # test deliv_assert parse
  def test_example9( self ) :

    # --------------------------------------------------------------- #

    # specify input file path
    inputfile = "./testFiles/deliv_assert.ded"

    # run translator
    actual_parsedLines = dedalusParser.parseDedalus( inputfile )

    # expected parsed lines
    expected_parsedLines = [['rule', {'relationName': 'missing_log', 'subgoalListOfDicts': [{'polarity': '', 'subgoalName': 'log', 'subgoalAttList': ['X', 'Pl'], 'subgoalTimeArg': ''}, {'polarity': '', 'subgoalName': 'node', 'subgoalAttList': ['X', 'A'], 'subgoalTimeArg': ''}, {'polarity': 'notin', 'subgoalName': 'log', 'subgoalAttList': ['A', 'Pl'], 'subgoalTimeArg': ''}], 'eqnDict': {}, 'goalAttList': ['A', 'Pl'], 'goalTimeArg': ''}], ['rule', {'relationName': 'pre', 'subgoalListOfDicts': [{'polarity': '', 'subgoalName': 'log', 'subgoalAttList': ['X', 'Pl'], 'subgoalTimeArg': ''}, {'polarity': 'notin', 'subgoalName': 'bcast', 'subgoalAttList': ['X', 'Pl'], 'subgoalTimeArg': '1'}, {'polarity': 'notin', 'subgoalName': 'crash', 'subgoalAttList': ['X', 'X', '_'], 'subgoalTimeArg': ''}], 'eqnDict': {}, 'goalAttList': ['X', 'Pl'], 'goalTimeArg': ''}], ['rule', {'relationName': 'post', 'subgoalListOfDicts': [{'polarity': '', 'subgoalName': 'log', 'subgoalAttList': ['X', 'Pl'], 'subgoalTimeArg': ''}, {'polarity': 'notin', 'subgoalName': 'missing_log', 'subgoalAttList': ['_', 'Pl'], 'subgoalTimeArg': ''}], 'eqnDict': {}, 'goalAttList': ['X', 'Pl'], 'goalTimeArg': ''}]]

    self.assertEqual( actual_parsedLines, expected_parsedLines )


  ###############
  #  EXAMPLE 8  #
  ###############
  # test the dedalus parser
  def test_example8( self ) :

    # ====================================================== #
    # test 0 : good fact line
    # specify input file path

    inputfile = "./testFiles/example8_0.ded"

    actualParsedLines   = dedalusParser.parseDedalus( inputfile )
    expectedParsedLines = [['fact', {'dataList': ['"a"', '"b"'], 'relationName': 'node', 'factTimeArg': '1'}]]
    self.assertEqual( actualParsedLines, expectedParsedLines )

    # ====================================================== #
    # test 1 : bad fact line = missing '('
    # specify input file path

    dedLine = 'node"a","b")@1;'

    # run program
    try :
      actualParsedLines = dedalusParser.parse( dedLine )

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
      actualParsedLines = dedalusParser.parse( dedLine )

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
      actualParsedLines = dedalusParser.parse( dedLine )

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
      actualParsedLines = dedalusParser.parse( dedLine )
  
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
      actualParsedLines = dedalusParser.parse( dedLine )

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
      actualParsedLines = dedalusParser.parse( dedLine )

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
      actualParsedLines = dedalusParser.parse( dedLine )

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
    actualParsedLines = dedalusParser.parse( dedLine )

    # grab expected error
    expectedParsedLines = ['fact', {'dataList': ['1', "'b'"], 'relationName': 'node', 'factTimeArg': '1'}]
    
    self.assertEqual( actualParsedLines, expectedParsedLines )

    # ====================================================== #
    # test 8 : bad line = missing semicolon
    # specify input file path

    dedLine = "node(1,'b')@1"

    # run program
    try :
      actualParsedLines = dedalusParser.parse( dedLine )

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
      actualParsedLines = dedalusParser.parse( dedLine )

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
      actualParsedLines = dedalusParser.parse( dedLine )

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
      actualParsedLines = dedalusParser.parse( dedLine )

    # something broke. save output as a single string
    except :
      actual_results = self.getError( sys.exc_info() )

    # grab expected error
    expected_results = "  SANITY CHECK SYNTAX FACT : ERROR : invalid syntax in line 'node(1,'b');'\n    line does not contain a time argument.\n"

    self.assertEqual( actual_results, expected_results )

    # ====================================================== #
    # test 10 : good rule line with equations, goal time arg, subgoal time arg, negation
    # specify input file path
    
    dedLine = "a(X,Y)@next:-X>Y,b(X,Y)@2,X==Y, notin c(Y)@1,X>=Y;"
    
    # run program
    actualParse = dedalusParser.parse( dedLine )
  
    # grab expected parse
    expectedParse = ['rule', {'relationName': 'a', 'subgoalListOfDicts': [{'polarity': '', 'subgoalName': 'b', 'subgoalAttList': ['X', 'Y'], 'subgoalTimeArg': '2'}, {'polarity': 'notin', 'subgoalName': 'c', 'subgoalAttList': ['Y'], 'subgoalTimeArg': '1'}], 'eqnDict': {'X>Y': ['X', 'Y'], 'X>=Y': ['X', 'Y'], 'X==Y': ['X', 'Y']}, 'goalAttList': ['X', 'Y'], 'goalTimeArg': 'next'}]

    self.assertEqual( actualParse, expectedParse )

    # ====================================================== #
    # test 11 : bad rule line. fails paren precheck for ')'
    # specify input file path

    dedLine = "a(X,Y)@next:-X>Y,b(X,Y@2,X==Y, notin c(Y)@1,X>=Y;"

    # run program and catch error
    try :
      actualParse = dedalusParser.parse( dedLine )
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
      actualParse = dedalusParser.parse( dedLine )
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
      actualParse = dedalusParser.parse( dedLine )
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
      actualParse = dedalusParser.parse( dedLine )
    except :
      actual_results = self.getError( sys.exc_info() )

    # grab expected parse
    expected_error = "  SANITY CHECK SYNTAX RULE : ERROR : invalid syntax in line '" + dedLine + "'\n    rule contains inconsistent use of single quotes."

    self.assertEqual( actual_results, expected_error )

    # ====================================================== #
    # test 15 : bad rule line. fails goal attribute capitalization post check
    # specify input file path

    dedLine = 'a(x,Y)@next:-X>Y,b(X,Y)@2,X=="thing", notin c(Y)@1,X>=Y;'

    # run program and catch error
    try :
      actualParse = dedalusParser.parse( dedLine )
    except :
      actual_results = self.getError( sys.exc_info() )

    # grab expected parse
    expected_error = "  SANITY CHECK SYNTAX RULE : ERROR : invalid syntax in line '" + dedLine + "'\n    the goal contains contains an attribute not starting with a capitalized letter: 'x'. \n    attribute variables must start with an upper case letter." 

    self.assertEqual( actual_results, expected_error )

    # ====================================================== #
    # test 16 : bad rule line. fails subgoal attribute capitalization post check
    # specify input file path
    
    dedLine = 'a(Xasdf,Yasdf)@next:-Xasdf>Yasdf,b(Xasdf,blah)@2,Xadsf=="thing", notin c(Yasdf)@1,Xasdf>=Yasd;'
    
    # run program and catch error
    try :
      actualParse = dedalusParser.parse( dedLine )
    except :
      actual_results = self.getError( sys.exc_info() )

    # grab expected parse
    expected_error = "  SANITY CHECK SYNTAX RULE : ERROR : invalid syntax in line '" + dedLine + "'\n    subgoal 'b' contains an attribute not starting with a capitalized letter: 'blah'. \n    attribute variables must start with an upper case letter." 

    self.assertEqual( actual_results, expected_error )

    # ====================================================== #
    # test 17 : bad rule line. fails goal name lower case requirement post check
    # specify input file path
    
    dedLine = 'A(Xasdf,Yasdf)@next:-Xasdf>Yasdf,b(Xasdf,Blah)@2,Xadsf=="thing", notin c(Yasdf)@1,Xasdf>=Yasd;'
    
    # run program and catch error
    try :
      actualParse = dedalusParser.parse( dedLine )
    except :
      actual_results = self.getError( sys.exc_info() )

    # grab expected parse
    expected_error = "  SANITY CHECK SYNTAX RULE : ERROR : invalid syntax in line '" + dedLine + "'\n    The goal name 'A' contains an upper-case letter. \n    relation names must contain only lower-case characters."
    
    self.assertEqual( actual_results, expected_error )

    # ====================================================== #
    # test 18 : bad rule line. fails subgoal name lower case requirement post check
    # specify input file path
   
    dedLine = 'a(Xasdf,Yasdf)@next:-Xasdf>Yasdf,b(Xasdf,Blah)@2,Xadsf=="thing", notin Cat(Yasdf)@1,Xasdf>=Yasd;'
   
    # run program and catch error
    try :
      actualParse = dedalusParser.parse( dedLine )
    except :
      actual_results = self.getError( sys.exc_info() )

    # grab expected parse
    expected_error = "  SANITY CHECK SYNTAX RULE : ERROR : invalid syntax in line '" + dedLine + "'\n    The subgoal name 'Cat' contains an upper-case letter. \n    relation names must contain only lower-case characters."

    self.assertEqual( actual_results, expected_error )



  @unittest.skip( "working on different example" )
  ###############
  #  EXAMPLE 7  #
  ###############
  # test use of file includes
  def test_example7( self ) :

    # --------------------------------------------------------------- #
    # testing set up. dedToIR has dependency
    # on createDedalusIRTables so that's
    # tested first above.
    testDB = "./IR.db"
    IRDB    = sqlite3.connect( testDB )
    cursor  = IRDB.cursor()

    # --------------------------------------------------------------- #
    # runs through function to make sure it finishes with expected error

    # specify input file path
    inputfile = "./testFiles/simplog_driver.ded"

    actualFileList = tools.get_all_include_file_paths( inputfile )
    expectedFileList = ['/Users/KsComp/projects/iapyx/qa/testFiles/bcast_edb.ded', '/Users/KsComp/projects/iapyx/qa/testFiles/deliv_assert.ded', '/Users/KsComp/projects/iapyx/qa/testFiles/simplog.ded', '/Users/KsComp/projects/iapyx/qa/testFiles/simplog_driver.ded']

    self.assertEqual( actualFileList, expectedFileList )

    # --------------------------------------------------------------- #
    # clean up testing
    IRDB.close()
    os.remove( testDB )


  ###############
  #  EXAMPLE 6  #
  ###############
  # example 6 details a correct program.
  # make sure this test produces the expected olg program.
  @unittest.skip( "working on different example" )
  def test_example6( self ) :

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

    # --------------------------------------------------------------- #
    #runs through function to make sure it finishes with expected error

    # specify input file path
    inputfile = "./testFiles/example6.ded"

    # get argDict
    argDict = self.getArgDict( inputfile )

    # run translator
    try :
      programData = dedt.translateDedalus( argDict, cursor )
      # portray actual output program lines as a single string
      actual_results = self.getActualResults( programData[0][0] )

    # something broke. save output as a single string
    except :
      actual_results = self.getError( sys.exc_info() )

    # grab expected output results as a string
    expected_results_path = "./testFiles/example6.olg"
    expected_results      = None
    with open( expected_results_path, 'r' ) as expectedFile :
      expected_results = expectedFile.read()

    self.assertEqual( actual_results, expected_results )

    # --------------------------------------------------------------- #
    #clean up testing
    IRDB.close()
    os.remove( testDB )


  @unittest.skip( "working on different example" )
  ###############
  #  EXAMPLE 5  #
  ###############
  # example 5 details an erroneous program.
  # make sure this test produces the expected error message.
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
      actual_results = self.getActualResults( programData[0][0] )

    # something broke. save output as a single string
    except :
      actual_results = self.getError( sys.exc_info() )

    # grab expected output results as a string
    expected_results_path = "./testFiles/example5_error.txt"
    expected_results      = None
    with open( expected_results_path, 'r' ) as expectedFile :
      expected_results = expectedFile.read()

    self.assertEqual( actual_results, expected_results )

    # --------------------------------------------------------------- #
    #clean up testing
    IRDB.close()
    os.remove( testDB )


  @unittest.skip( "working on different example" )
  ###############
  #  EXAMPLE 4  #
  ###############
  # example 4 details an erroneous program.
  # make sure this test produces the expected error message.
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
      actual_results = self.getActualResults( programData[0][0] )

    # something broke. save output as a single string
    except :
      actual_results = self.getError( sys.exc_info() )

    # grab expected output results as a string
    expected_results_path = "./testFiles/example4_error.txt"
    expected_results      = None
    with open( expected_results_path, 'r' ) as expectedFile :
      expected_results = expectedFile.read()

    self.assertEqual( actual_results, expected_results )

    # --------------------------------------------------------------- #
    #clean up testing
    IRDB.close()
    os.remove( testDB )


  @unittest.skip( "working on different example" )
  ###############
  #  EXAMPLE 3  #
  ###############
  # example 3 details an erroneous program.
  # make sure this test produces the expected error message.
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
      actual_results = self.getActualResults( programData[0][0] )

    # something broke. save output as a single string
    except :
      actual_results = self.getError( sys.exc_info() )

    # grab expected output results as a string
    expected_results_path = "./testFiles/example3_error.txt"
    expected_results      = None
    with open( expected_results_path, 'r' ) as expectedFile :
      expected_results = expectedFile.read()
   
    self.assertEqual( actual_results, expected_results )
    
    # --------------------------------------------------------------- #
    #clean up testing
    IRDB.close()
    os.remove( testDB )

  @unittest.skip( "working on different example" )
  ###############
  #  EXAMPLE 2  #
  ###############
  # example 2 details an erroneous program.
  # make sure this test produces the expected error message.
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
      actual_results = self.getActualResults( programData[0][0] )

    # something broke. save output as a single string
    except :
      actual_results = self.getError( sys.exc_info() )

    # grab expected output results as a string
    expected_results_path = "./testFiles/example2_error.txt"
    expected_results      = None
    with open( expected_results_path, 'r' ) as expectedFile :
      expected_results = expectedFile.read()

    self.assertEqual( actual_results, expected_results )
    
    # --------------------------------------------------------------- #
    #clean up testing
    IRDB.close()
    os.remove( testDB )


  @unittest.skip( "working on different example" )
  ###############
  #  EXAMPLE 1  #
  ###############
  def test_example1( self ) :
  
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

    # --------------------------------------------------------------- #
    #runs through function to make sure it finishes without error

    # specify input file path
    inputfile = "./testFiles/example1.ded"

    # get argDict
    argDict = self.getArgDict( inputfile )

    # run translator
    programData = dedt.translateDedalus( argDict, cursor )

    # portray actual output program lines as a single string
    actual_results = self.getActualResults( programData[0][0] )

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


  @unittest.skip( "working on different example" )
  ###################
  #  EXAMPLE EMPTY  #
  ###################
  # input empty
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

    # --------------------------------------------------------------- #
    #runs through function to make sure it finishes without error

    # specify input file path
    inputfile = "./testFiles/example_empty.ded"

    # get argDict
    argDict = self.getArgDict( inputfile )

    # run translator
    programData = dedt.translateDedalus( argDict, cursor )

    # portray actual output program lines as a single string
    actual_results = self.getActualResults( programData[0][0] )

    # grab expected output results as a string
    expected_results_path = "./testFiles/example_empty.olg"
    expected_results      = None
    with open( expected_results_path, 'r' ) as expectedFile :
      expected_results = expectedFile.read()

    print "expected_results:" + str( expected_results )
    self.assertEqual( actual_results, expected_results )

    # --------------------------------------------------------------- #
    #clean up testing
    IRDB.close()
    os.remove( testDB )


  @unittest.skip( "working on different example" )
  #################################
  #  EXAMPLE EMPTY WITH COMMENTS  #
  #################################
  # input empty file with comments
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

    # --------------------------------------------------------------- #
    #runs through function to make sure it finishes without error

    # specify input file path
    inputfile = "./testFiles/example_empty_with_comments.ded"

    # get argDict
    argDict = self.getArgDict( inputfile )

    # run translator
    programData = dedt.translateDedalus( argDict, cursor )

    # portray actual output program lines as a single string
    actual_results = self.getActualResults( programData[0][0] )

    # grab expected output results as a string
    expected_results_path = "./testFiles/example_empty_with_comments.olg"
    expected_results      = None
    with open( expected_results_path, 'r' ) as expectedFile :
      expected_results = expectedFile.read()

    print "expected_results:" + str( expected_results )
    self.assertEqual( actual_results, expected_results )

    # --------------------------------------------------------------- #
    #clean up testing
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
