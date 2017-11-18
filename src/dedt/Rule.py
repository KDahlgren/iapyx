#!/usr/bin/env python

'''
Rule.py
   Defines the Rule class.
   Establishes all relevant attributes and get/set methods.

============================================
IR TABLES STORING RULE DATA

  Fact         ( fid text, name text,     timeArg text                                                )
  FactData     ( fid text, dataID int,    data text,        dataType text                             )
  Rule         ( rid text, goalName text, goalTimeArg text, rewritten text                            )
  GoalAtt      ( rid text, attID int,     attName text,     attType text                              )
  Subgoals     ( rid text, sid text,      subgoalName text, subgoalPolarity text, subgoalTimeArg text )
  SubgoalAtt   ( rid text, sid text,      attID int,        attName text,         attType text        )
  Equation     ( rid text, eid text,      eqn text                                                    )
  EquationVars ( rid text, eid text,      varID int,        var text                                  )
  Clock        ( src text, dest text,     sndTime int,      delivTime int,        simInclude text     )

============================================

NOTES :

  All attribute types per rule are initialized to "UNDEFINED".
  Attribute types per rule cannot be derived until all program facts
  and rules, spanning ALL input Dedalus programs,
  appear in the IR database.

  The dedt submodule is responsible for defining and firing
  the logic for deriving the data types associated with all
  goals and subgoals per rule.

'''

import inspect, logging, os, sqlite3, sys

# ------------------------------------------------------ #
# import sibling packages HERE!!!
if not os.path.abspath( __file__ + "/../.." ) in sys.path :
  sys.path.append( os.path.abspath( __file__ + "/../.." ) )

from utils import dumpers, extractors, tools
# ------------------------------------------------------ #


DEBUG = tools.getConfig( "DEDT", "RULE_DEBUG", bool )


class Rule :


  ################
  #  ATTRIBUTES  #
  ################
  rid                = ""
  cursor             = None
  relationName       = ""
  goalAttList        = []
  goalTimeArg        = None
  subgoalListOfDicts = []
  eqnDict            = {}
  ruleData           = {}


  #################
  #  CONSTRUCTOR  #
  #################
  # ruleData = { relationName : 'relationNameStr', 
  #              goalAttList:[ data1, ... , dataN ], 
  #              goalTimeArg : ""/next/async,
  #              subgoalListOfDicts : [ { subgoalName : 'subgoalNameStr', 
  #                                       subgoalAttList : [ data1, ... , dataN ], 
  #                                       polarity : 'notin' OR '', 
  #                                       subgoalTimeArg : <anInteger> }, ... ],
  #              eqnDict : { 'eqn1':{ variableList : [ 'var1', ... , 'varI' ] }, 
  #                          ... , 
  #                          'eqnM':{ variableList : [ 'var1', ... , 'varJ' ] }  } }
  def __init__( self, rid, ruleData, cursor ) :
    self.rid      = rid
    self.cursor   = cursor
    self.ruleData = ruleData

    logging.debug( "  RULE : ruleData = " + str( ruleData ) )

    # =========================================== #
    # extract relation name
    self.relationName = ruleData[ "relationName" ]

    # =========================================== #
    # extract goal attribute list
    self.goalAttList = ruleData[ "goalAttList" ]

    # =========================================== #
    # extract goal time argument
    self.goalTimeArg = ruleData[ "goalTimeArg" ]

    # =========================================== #
    # extract subgoal information
    self.subgoalListOfDicts = ruleData[ "subgoalListOfDicts" ]

    # =========================================== #
    # extract equation dictionary
    self.eqnDict = ruleData[ "eqnDict" ]

    # =========================================== #
    # save data in the IR database

    logging.debug( "  RULE : self.relationName       = " + self.relationName )
    logging.debug( "  RULE : self.goalAttList        = " + str( self.goalAttList ) )
    logging.debug( "  RULE : self.goalTimeArg        = " + self.goalTimeArg )
    logging.debug( "  RULE : self.subgoalListOfDicts = " + str( self.subgoalListOfDicts ) )
    logging.debug( "  RULE : self.eqnDict            = " + str( self.eqnDict ) )

    self.saveToRule()
    self.saveToGoalAtt()
    self.saveSubgoals()
    self.saveEquations()


  ##################
  #  SAVE TO RULE  #
  ##################
  # save goal name and time arg
  # Rule( rid text, goalName text, goalTimeArg text, rewritten text )
  def saveToRule( self ) :

    rewrittenFlag = False # all rules are initially NOT rewritten

    # delete all data for this id in the table, if applicable
    self.cursor.execute( "DELETE FROM Rule WHERE rid='%s'" % str( self.rid ) )

    self.cursor.execute("INSERT INTO Rule (rid, goalName, goalTimeArg, rewritten) VALUES ('" + str( self.rid ) + "','" + self.relationName + "','" + self.goalTimeArg + "','" + str( rewrittenFlag ) + "')")


  ######################
  #  SAVE TO GOAL ATT  #
  ######################
  # save goal attribute data
  # GoalAtt( rid text, attID int, attName text, attType text )
  def saveToGoalAtt( self ) :

    # delete all data for this id in the table, if applicable
    self.cursor.execute( "DELETE FROM GoalAtt WHERE rid='%s'" % str( self.rid ) )

    attID = 0  # allows duplicate attributes in attList

    for attName in self.goalAttList :

      self.cursor.execute("INSERT INTO GoalAtt VALUES ('" + str( self.rid ) + "','" + str( attID ) + "','" + str( attName ) + "','UNDEFINEDTYPE')")

      attID += 1


  ###################
  #  SAVE SUBGOALS  #
  ###################
  # save all subgoal data
  # subgoalListOfDicts : [ { subgoalName : 'subgoalNameStr', 
  #                          subgoalAttList : [ data1, ... , dataN ], 
  #                          polarity : 'notin' OR '', 
  #                          subgoalTimeArg : <anInteger> }, ... ]
  def saveSubgoals( self ) :

    # delete all data for this id in the table, if applicable
    logging.debug( "  SAVE SUBGOALS : self.ruleData = = " + str( self.ruleData ) ) 

    logging.debug( "DELETE FROM Subgoals WHERE rid='%s'" % str( self.rid ) ) 

    self.cursor.execute( "DELETE FROM Subgoals WHERE rid='%s'" % str( self.rid ) )

    logging.debug( "self.subgoalListOfDicts = " + str( self.subgoalListOfDicts ) )

    for sub in self.subgoalListOfDicts :

      # ----------------------------- #
      # grab relevant data

      subgoalName    = sub[ "subgoalName" ]
      subgoalAttList = sub[ "subgoalAttList" ]
      polarity       = sub[ "polarity" ]
      subgoalTimeArg = sub[ "subgoalTimeArg" ]

      # ----------------------------- #
      # generate random subgoal id 

      #sid = tools.getID()
      sid = tools.getIDFromCounters( "sid" )

      # ----------------------------- #
      # save subgoal data 

      self.saveToSubgoals( sid, subgoalName, polarity, subgoalTimeArg )
      self.saveToSubgoalAtt( sid, subgoalAttList )


  ######################
  #  SAVE TO SUBGOALS  #
  ######################
  # save subgoal names and time arguments
  # Subgoals( rid text, sid text, subgoalName text, subgoalTimeArg text )
  def saveToSubgoals( self, sid, subgoalName, subgoalPolarity, subgoalTimeArg ) :

    self.cursor.execute( "INSERT INTO Subgoals VALUES ('" + str( self.rid )        + "','" \
                                                          + str( sid )             + "','" \
                                                          + subgoalName            + "','" \
                                                          + subgoalPolarity        + "','" \
                                                          + str( subgoalTimeArg )  +"')" )


  #########################
  #  SAVE TO SUBGOAL ATT  #
  #########################
  # save subgoal attributes and data types
  # SubgoalAtt( rid text, sid text, attID int, attName text, attType text )
  def saveToSubgoalAtt( self, sid, subgoalAttList ) :

    attID = 0
    for attName in subgoalAttList :

      self.cursor.execute( "INSERT INTO SubgoalAtt VALUES ('" + str( self.rid )     + "','" \
                                                              + str( sid )          + "','" \
                                                              + str( attID )        + "','" \
                                                              + attName \
                                                              + "','UNDEFINEDTYPE')" )
      attID += 1


  ####################
  #  SAVE EQUATIONS  #
  ####################
  # save all equation data
  # eqnDict : { 'eqn1':{ variableList : [ 'var1', ... , 'varI' ] }, 
  #             ... , 
  #             'eqnM':{ variableList : [ 'var1', ... , 'varJ' ] } }
  def saveEquations( self ) :

    # delete all data for this id in the table, if applicable
    self.cursor.execute( "DELETE FROM Equation WHERE rid='%s'" % str( self.rid ) )

    for eqnStr in self.eqnDict :

      # ----------------------------- #
      # grab relevant data

      variableList = self.eqnDict[ eqnStr ]

      # ----------------------------- #
      # generate random eqn id 

      #eid = tools.getID()
      eid = tools.getIDFromCounters( "eid" )

      # ----------------------------- #
      # save equation data 

      self.saveToEquation( eid, eqnStr )
      self.saveToEquationVars( eid, variableList )

    return None


  ######################
  #  SAVE TO EQUATION  #
  ######################
  # save all equations
  # Equation( rid text, eid text, eqn text )
  def saveToEquation( self, eid, eqnStr ) :

    self.cursor.execute( "INSERT INTO Equation VALUES ('" + str( self.rid ) + "','" \
                                                          + str( eid )      + "','" \
                                                          + eqnStr + "')" )


  ###########################
  #  SAVE TO EQUATION VARS  #
  ###########################
  # save all equation variables separately for convenience
  # EquationVars( rid text, eid text, varID int, var text )
  def saveToEquationVars( self, eid, variableList ) :

    varID = 0
    for var in variableList :

      self.cursor.execute( "INSERT INTO EquationVars VALUES ('" + str( self.rid )     + "','" \
                                                                + str( eid )          + "','" \
                                                                + str( varID )        + "','" \
                                                                + var + "')" )
      varID += 1


#########
#  EOF  #
#########
