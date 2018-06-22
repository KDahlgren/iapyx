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

import copy, inspect, logging, os, sqlite3, sys

# ------------------------------------------------------ #
# import sibling packages HERE!!!
if not os.path.abspath( __file__ + "/../.." ) in sys.path :
  sys.path.append( os.path.abspath( __file__ + "/../.." ) )

from utils import dumpers, extractors, tools
# ------------------------------------------------------ #


class Rule :

  #################
  #  CONSTRUCTOR  #
  #################
  #
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
  #
  def __init__( self, rid, ruleData, cursor ) :

    ########################
    #  ATTRIBUTE DEFAULTS  #
    ########################
    self.rid = ""

    # the ptr to the original rule for provenance rules only.
    self.orig_rule_ptr = None

    # map of original goal att strings to uniform att strings (dm rewrites).
    self.orig_rule_attMapper = {}

    # map of original goal att strings to uniform att strings in aggregate rewrites (dm rewrites).
    self.orig_rule_attMapper_aggRewrites = {}

    self.cursor                = None
    self.relationName          = ""
    self.goalAttList           = []
    self.orig_goalAttList      = []
    self.goalTimeArg           = None
    self.orig_goal_time_type   = ""
    self.subgoalListOfDicts    = []
    self.eqnDict               = {}
    self.ruleData              = {}
    self.rule_type             = "UNDEFINED_RULE_TYPE"
    self.hitUniformityRewrites = False

    self.goal_att_type_list = []
    self.lineage_not_names  = []

    self.sip_color = False

    # =========================================== #

    self.rid      = rid
    self.cursor   = cursor
    self.ruleData = ruleData

    logging.debug( "  RULE : ruleData = " + str( ruleData ) )

    # =========================================== #
    # extract relation name

    self.relationName = ruleData[ "relationName" ]

    # =========================================== #
    # extract goal attribute list

    self.goalAttList      = ruleData[ "goalAttList" ]
    self.orig_goalAttList = copy.deepcopy( ruleData[ "goalAttList" ] )

    # =========================================== #
    # extract goal time argument

    self.goalTimeArg = ruleData[ "goalTimeArg" ]

    if self.goalAttList[ -1 ] == "NRESERVED" :
      self.orig_goal_time_type = ""
    elif self.goalAttList[ -1 ] == "MRESERVED" :
      self.orig_goal_time_type = "async"
    elif self.goalAttList[ -1 ] == "NRESERVED+1" :
      self.orig_goal_time_type = "next"
    else :
      self.orig_goal_time_type == "UNKNOWN_TIME_REF"

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


  ####################
  #  DELETE FROM DB  #
  ####################
  def delete_from_db( self ) :
    self.cursor.execute( "DELETE FROM Rule         WHERE rid='%s'" % str( self.rid ) )
    self.cursor.execute( "DELETE FROM GoalAtt      WHERE rid='%s'" % str( self.rid ) )
    self.cursor.execute( "DELETE FROM Subgoals     WHERE rid='%s'" % str( self.rid ) )
    self.cursor.execute( "DELETE FROM SubgoalAtt   WHERE rid='%s'" % str( self.rid ) )
    self.cursor.execute( "DELETE FROM Equation     WHERE rid='%s'" % str( self.rid ) )
    self.cursor.execute( "DELETE FROM EquationVars WHERE rid='%s'" % str( self.rid ) )


  ##############
  #  SET NAME  #
  ##############
  def set_name( self, new_rel_name ) :
    self.cursor.execute( "UPDATE Rule SET goalName='" + new_rel_name + \
                         "' WHERE rid=='" + str( self.rid ) + "'" )

  ##################
  #  SAVE TO RULE  #
  ##################
  # save goal name and time arg
  # Rule( rid text, goalName text, goalTimeArg text, rewritten text )
  def saveToRule( self ) :

    rewrittenFlag = False # all rules are initially NOT rewritten

    # delete all data for this id in the table, if applicable
    self.cursor.execute( "DELETE FROM Rule WHERE rid='%s'" % str( self.rid ) )

    self.cursor.execute( "INSERT INTO Rule (rid, goalName, goalTimeArg, rewritten) VALUES ('" + \
                         str( self.rid )   + "','" + \
                         self.relationName + "','" + \
                         self.goalTimeArg  + "','" + \
                         str( rewrittenFlag ) + "')")

  ################################
  #  UPDATE GOAL ATT TYPES LIST  #
  ################################
  def update_goal_att_types_list( self ) :

    logging.debug( "  UPDATE GOAL ATT TYPES LIST : running process for rule :\n" + \
                   dumpers.reconstructRule( self.rid, self.cursor ) )

    self.cursor.execute( "SELECT attID,attType FROM GoalAtt WHERE rid=='" + str( self.rid ) + "'" )
    typeList = self.cursor.fetchall()
    typeList = tools.toAscii_multiList( typeList )
    for t in typeList :
      logging.debug(  "  UPDATE GOAL ATT TYPES LIST : " + str( t ) )

    # get type list
    self.cursor.execute( "SELECT attID,attType FROM GoalAtt WHERE rid=='" + str( self.rid ) + "'" )
    typeList = self.cursor.fetchall()
    typeList = tools.toAscii_multiList( typeList )
    self.goal_att_type_list = typeList

    logging.debug( "  UPDATE GOAL ATT TYPES LIST : len( self.goalAttList ) = " + str( self.goalAttList ) )
    logging.debug( "  UPDATE GOAL ATT TYPES LIST : typeList                = " + str( typeList ) )

    assert( len( self.goalAttList ) == len( typeList ) )

  ########################
  #  MANUALLY SET TYPES  #
  ########################
  def manually_set_types( self ) :

    logging.debug( "  MANUALLY SET TYPES : running process for rule :\n" + \
                   dumpers.reconstructRule( self.rid, self.cursor ) )

    for i in range( 0, len( self.goal_att_type_list ) ) :
      att_type = self.goal_att_type_list[ i ][ 1 ]
      self.cursor.execute( "UPDATE GoalAtt SET attType='" + att_type + \
                           "' WHERE rid=='" + str( self.rid ) + \
                           "' AND attID=='" + str( i ) + "'" )


  ######################
  #  SAVE TO GOAL ATT  #
  ######################
  # save goal attribute data
  # GoalAtt( rid text, attID int, attName text, attType text )
  def saveToGoalAtt( self ) :

    logging.debug( "========================================================" )
    logging.debug( "  SAVE TO GOAL ATT : self.relationName = " + self.relationName )
    logging.debug( "  SAVE TO GOAL ATT : rule : " + \
                   str( dumpers.reconstructRule( self.rid, self.cursor ) ) )
    self.cursor.execute( "SELECT attID,attType FROM GoalAtt WHERE rid=='" + str( self.rid ) + "'" )
    typeList = self.cursor.fetchall()
    typeList = tools.toAscii_multiList( typeList )
    for t in typeList :
      logging.debug(  "  SAVE TO GOAL ATT : " + str( t ) )

    # get type list
    if len( typeList ) > 0 :
      self.cursor.execute( "SELECT attID,attType FROM GoalAtt WHERE rid=='" + str( self.rid ) + "'" )
      typeList = self.cursor.fetchall()
      typeList = tools.toAscii_multiList( typeList )
      self.goal_att_type_list = typeList
    else :
      typeList = self.goal_att_type_list

    logging.debug( "  SAVE TO GOAL ATT : len( self.goalAttList ) = " + str( self.goalAttList ) )
    logging.debug( "  SAVE TO GOAL ATT : typeList                = " + str( typeList ) )
    #assert( len( self.goalAttList ) == len( typeList ) )

    # delete all data for this id in the table
    self.cursor.execute( "DELETE FROM GoalAtt WHERE rid=='" + str( self.rid ) + "'" )

    attID = 0  # allows duplicate attributes in attList

    for i in range( 0, len( self.goalAttList ) ) :
      attName = self.goalAttList[ i ]
      try :
        attType = typeList[ i ][ 1 ]
      except IndexError :
        attType = "UNDEFINEDTYPE"

      logging.debug( "  SAVE TO GOAL ATT : attType = " + str( attType ) )

      self.cursor.execute( "INSERT INTO GoalAtt VALUES ('" + \
                           str( self.rid ) + "','" + \
                           str( attID )    + "','" + \
                           str( attName )  + "','" + \
                           attType + "')" )
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
    logging.debug( "  SAVE SUBGOALS : self.cursor             = " + str( self.cursor ) ) 
    logging.debug( "  SAVE SUBGOALS : self.ruleData           = " + str( self.ruleData ) ) 
    logging.debug( "  SAVE SUBGOALS : self.rid                = " + str( self.rid ) ) 
    logging.debug( "  SAVE SUBGOALS : self.relationName       = " + self.relationName )
    logging.debug( "  SAVE SUBGOALS : self.goalAttList        = " + str( self.goalAttList ) )
    logging.debug( "  SAVE SUBGOALS : self.goalTimeArg        = " + self.goalTimeArg )
    logging.debug( "  SAVE SUBGOALS : self.subgoalListOfDicts = " + str( self.subgoalListOfDicts ) )

    # Subgoals deletes
    self.cursor.execute( "SELECT * FROM Subgoals WHERE rid=='" + str( self.rid ) + "'" )
    res = self.cursor.fetchall()
    res = tools.toAscii_multiList( res )
    for r in res :
      logging.debug( "r = " + str( r ) )

    logging.debug( "DELETE FROM Subgoals WHERE rid='%s'" % str( self.rid ) ) 
    self.cursor.execute( "DELETE FROM Subgoals WHERE rid='%s'" % str( self.rid ) )

    # SubgoalAtt deletes
    self.cursor.execute( "SELECT * FROM SubgoalAtt WHERE rid=='" + str( self.rid ) + "'" )
    res = self.cursor.fetchall()
    res = tools.toAscii_multiList( res )
    for r in res :
      logging.debug( "r = " + str( r ) )

    logging.debug( "DELETE FROM SubgoalAtt WHERE rid='%s'" % str( self.rid ) )
    self.cursor.execute( "DELETE FROM SubgoalAtt WHERE rid='%s'" % str( self.rid ) )

    logging.debug( "self.subgoalListOfDicts = " + str( self.subgoalListOfDicts ) )

    for sub in self.subgoalListOfDicts :

      logging.debug( "  SAVE SUBGOALS : sub = " + str( sub ) )

      # ----------------------------- #
      # grab relevant data

      subgoalName    = sub[ "subgoalName" ]
      subgoalAttList = sub[ "subgoalAttList" ]
      polarity       = sub[ "polarity" ]
      subgoalTimeArg = sub[ "subgoalTimeArg" ]

      logging.debug( "  SAVE SUBGOALS : subgoalName    = " + subgoalName )
      logging.debug( "  SAVE SUBGOALS : subgoalAttList = " + str( subgoalAttList ) )
      logging.debug( "  SAVE SUBGOALS : polarity       = " + polarity )
      logging.debug( "  SAVE SUBGOALS : subgoalTimeArg = " + subgoalTimeArg )

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

      logging.debug( "  SAVE TO SUBGOAL ATT : self.rid = " + str( self.rid ) )
      logging.debug( "  SAVE TO SUBGOAL ATT : self.sid = " + str( sid ) )
      logging.debug( "  SAVE TO SUBGOAL ATT : attID    = " + str( attID ) )
      logging.debug( "  SAVE TO SUBGOAL ATT : attName  = " + str( attName ) )

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

    logging.debug( "  SAVE EQUATIONS : running process..." )

    # delete all data for this id in the relevant tables, if applicable
    logging.debug( "DELETE FROM Equation WHERE rid='%s'" % str( self.rid ) )
    logging.debug( "DELETE FROM EquationVars WHERE rid='%s'" % str( self.rid ) )

    self.cursor.execute( "DELETE FROM Equation WHERE rid='%s'" % str( self.rid ) )
    self.cursor.execute( "DELETE FROM EquationVars WHERE rid='%s'" % str( self.rid ) )

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


  ######################
  #  SAVE TO EQUATION  #
  ######################
  # save all equations
  # Equation( rid text, eid text, eqn text )
  def saveToEquation( self, eid, eqnStr ) :

    logging.debug( "INSERT INTO Equation VALUES ('" + str( self.rid ) + "','" \
                                                    + str( eid )      + "','" \
                                                    + eqnStr + "')" )

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

      logging.debug( "INSERT INTO EquationVars VALUES ('" + str( self.rid )     + "','" \
                                                          + str( eid )          + "','" \
                                                          + str( varID )        + "','" \
                                                          + var + "')" )

      self.cursor.execute( "INSERT INTO EquationVars VALUES ('" + str( self.rid )     + "','" \
                                                                + str( eid )          + "','" \
                                                                + str( varID )        + "','" \
                                                                + var + "')" )
      varID += 1


#########
#  EOF  #
#########
