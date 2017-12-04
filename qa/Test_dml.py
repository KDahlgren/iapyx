#!/usr/bin/env python

'''
Test_dml.py
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

from dedt  import dedt, dedalusParser, Fact, Rule, clockRelation, dedalusRewriter
from utils import dumpers, globalCounters, tools

import dml

# ------------------------------------------------------ #


##############
#  TEST DML  #
##############
class Test_dml( unittest.TestCase ) :

  logging.basicConfig( format='%(levelname)s:%(message)s', level=logging.DEBUG )
  #logging.basicConfig( format='%(levelname)s:%(message)s', level=logging.INFO )
  #logging.basicConfig( format='%(levelname)s:%(message)s', level=logging.WARNING )


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
    # build test fact set

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
                    "eqnDict":{} }
    ruleData_b0 = { "relationName":"b", \
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

    rid_a0 = tools.getIDFromCounters( "rid" )
    rid_b0 = tools.getIDFromCounters( "rid" )

    rule_a0 = Rule.Rule( rid_a0, ruleData_a0, cursor )
    rule_b0 = Rule.Rule( rid_b0, ruleData_b0, cursor )

    ruleMeta = [ rule_a0, rule_b0 ]

    # --------------------------------------------------------------- #
    # get the targeted rule meta list

    targetRuleMeta = dml.replaceSubgoalNegations( "f", "not_f", ruleMeta )

    actual_ruleData = []
    for rule in targetRuleMeta :
      actual_ruleData.append( rule.ruleData )

    # --------------------------------------------------------------- #
    # check assertion

    expected_ruleData_a0 = { "relationName": "a", \
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
    expected_ruleData_b0 = { "relationName":"b", \
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

    expected_ruleData = [ expected_ruleData_a0, expected_ruleData_b0 ]

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
    # build test fact set

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
    # build test fact set

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

    targetRuleMeta = dml.setUniformAttList( ruleMeta )

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
    # build test fact set

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
      domCompRule = dml.buildDomCompRule( orig_name, goalAttList, cursor )

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
    # build test fact set

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

    actual_domCompRules_ruleData = []
    for ruleSet in targetRuleMeta :

      # get not_ name
      orig_name = ruleSet[0].ruleData[ "relationName" ]
      not_name  = "not_" + orig_name

      # get goal att list
      goalAttList = ruleSet[0].ruleData[ "goalAttList" ]

      # get goal time arg
      goalTimeArg = ""

      # build dom comp rule
      domCompRule = dml.buildDomCompRule( orig_name, goalAttList, cursor )

      # collect ruleData for test
      actual_domCompRules_ruleData.append( domCompRule.ruleData )

    # --------------------------------------------------------------- #
    # check assertion

    expected_domComp_c = { 'relationName': 'domComp_c', \
                           'subgoalListOfDicts': [{ 'polarity': '', \
                                                    'subgoalName': 'adom', \
                                                    'subgoalAttList': ['X'], \
                                                    'subgoalTimeArg': ''}, \
                                                  { 'polarity': 'notin', \
                                                    'subgoalName': 'c', \
                                                    'subgoalAttList': ['X'], \
                                                    'subgoalTimeArg': ''}], \
                           'eqnDict': {}, \
                           'goalAttList': ['X'], \
                           'goalTimeArg': ''}

    expected_domComp_b = { 'relationName': 'domComp_b', \
                           'subgoalListOfDicts': [{ 'polarity': '', \
                                                    'subgoalName': 'adom', \
                                                    'subgoalAttList': ['X'], \
                                                    'subgoalTimeArg': ''}, \
                                                  { 'polarity': '', \
                                                    'subgoalName': 'adom', \
                                                    'subgoalAttList': ['Y'], \
                                                    'subgoalTimeArg': ''}, \
                                                  { 'polarity': 'notin', \
                                                    'subgoalName': 'b', \
                                                    'subgoalAttList': ['X','Y'], \
                                                    'subgoalTimeArg': ''}], \
                           'eqnDict': {}, \
                           'goalAttList': ['X','Y'], \
                           'goalTimeArg': ''}


    expected_domCompRules_ruleData = [ expected_domComp_c, expected_domComp_b ]

    self.assertEqual( actual_domCompRules_ruleData, expected_domCompRules_ruleData )

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
    # build test fact set

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
      domCompRule = dml.buildDomCompRule( orig_name, goalAttList, cursor )

      # build existential vars rules
      existentialVarsRules = dml.buildExistentialVarsRules( ruleSet, cursor )

      # get new dm rules
      negated_dnf_fmla = dml.generateBooleanFormula( ruleSet )
      pos_dnf_fmla     = str( dml.simplifyToDNF( negated_dnf_fmla ) )
      newDMRules       = dml.dnfToDatalog( not_name, goalAttList, goalTimeArg, pos_dnf_fmla, domCompRule, existentialVarsRules, ruleSet, cursor )

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
                                                'subgoalName': 'domComp_c', \
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
                                                'subgoalName': 'domComp_c', \
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
                                                'subgoalName': 'domComp_b', \
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
                                                'subgoalName': 'domComp_b', \
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
    # build test fact set

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
    # build test fact set

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
    # build test fact set

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
    # build test fact set

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

    factData1 = { "relationName":'a', "dataList":[ 1, 2, 3 ], "factTimeArg":"" }
    factData2 = { "relationName":'b', "dataList":[ "str1", "str2" ], "factTimeArg":"" }

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
      actualAdomRuleData.append( rule.ruleData )

    # --------------------------------------------------------------- #
    # check assertion

    ruleData1 = { "relationName":"adom", \
                  "goalAttList":[ "T" ], \
                  "goalTimeArg":"", 
                  "subgoalListOfDicts":[ { "subgoalName":"a", \
                                          "subgoalAttList":[ "T", "_", "_" ], \
                                          "polarity":"", \
                                          "subgoalTimeArg":"" } ], \
                  "eqnDict":{} }
    ruleData2 = { "relationName":"adom", \
                  "goalAttList":[ "T" ], \
                  "goalTimeArg":"", 
                  "subgoalListOfDicts":[ { "subgoalName":"a", \
                                          "subgoalAttList":[ "_", "T", "_" ], \
                                          "polarity":"", \
                                          "subgoalTimeArg":"" } ], \
                  "eqnDict":{} }
    ruleData3 = { "relationName":"adom", \
                  "goalAttList":[ "T" ], \
                  "goalTimeArg":"", 
                  "subgoalListOfDicts":[ { "subgoalName":"a", \
                                          "subgoalAttList":[ "_", "_", "T" ], \
                                          "polarity":"", \
                                          "subgoalTimeArg":"" } ], \
                  "eqnDict":{} }
    ruleData4 = { "relationName":"adom", \
                  "goalAttList":[ "T" ], \
                  "goalTimeArg":"", 
                  "subgoalListOfDicts":[ { "subgoalName":"b", \
                                          "subgoalAttList":[ "T", "_" ], \
                                          "polarity":"", \
                                          "subgoalTimeArg":"" } ], \
                  "eqnDict":{} }
    ruleData5 = { "relationName":"adom", \
                  "goalAttList":[ "T" ], \
                  "goalTimeArg":"", 
                  "subgoalListOfDicts":[ { "subgoalName":"b", \
                                           "subgoalAttList":[ "_", "T" ], \
                                           "polarity":"", \
                                           "subgoalTimeArg":"" } ], \
                  "eqnDict":{} }

    expectedAdomRuleData = [ ruleData1, ruleData2, ruleData3, ruleData4, ruleData5 ]

    self.assertEqual( actualAdomRuleData, expectedAdomRuleData )

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
