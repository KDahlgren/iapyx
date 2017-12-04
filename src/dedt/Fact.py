#!/usr/bin/env python

'''
Fact.py
   Defines the Fact class.
   Establishes all relevant attributes and get/set methods.
'''

import inspect, logging, os, sqlite3, sys

# ------------------------------------------------------ #
# import sibling packages HERE!!!
if not os.path.abspath( __file__ + "/../.." ) in sys.path :
  sys.path.append( os.path.abspath( __file__ + "/../.." ) )

from utils import tools
# ------------------------------------------------------ #

DEBUG = tools.getConfig( "DEDT", "FACT_DEBUG", bool )

class Fact :


  ################
  #  ATTRIBUTES  #
  ################
  fid               = ""
  cursor            = None
  factData          = None
  relationName      = ""
  factTimeArg       = None
  dataListWithTypes = []


  #################
  #  CONSTRUCTOR  #
  #################
  # factData = { relationName:'relationNameStr', dataList:[ data1, ... , dataN ], factTimeArg:<anInteger> }
  def __init__( self, fid, factData, cursor ) :

    self.fid      = fid
    self.cursor   = cursor
    self.factData = factData

    logging.debug( "  FACT : factData = " + str( factData ) )

    # =========================================== #
    # extract relation name
    self.relationName = self.factData[ "relationName" ]

    # =========================================== #
    # extract time argument
    self.factTimeArg = self.factData[ "factTimeArg" ]

    # =========================================== #
    # extract data list and derive types
    dataList_raw      = self.factData[ "dataList" ]
    self.dataListWithTypes = self.getDataAndTypes( dataList_raw )

    # =========================================== #
    # save data in the IR database

    logging.debug( "  FACT : self.relationName      = " + self.relationName )
    logging.debug( "  FACT : self.factTimeArg       = " + self.factTimeArg )
    logging.debug( "  FACT : self.dataListWithTypes = " + str( self.dataListWithTypes ) )

    self.saveFactInfo()
    self.saveFactDataList()



  ########################
  #  GET DATA AND TYPES  #
  ########################
  # given input data list, derive types
  # return a list matching data with type conclusions
  # currently only supports strings and ints.
  def getDataAndTypes( self, dataList_raw ) :

    dataListWithTypes = []

    for data in dataList_raw :
      if self.isString( data ) :
        dataType = "string"
      else :
        dataType = "int"

      dataListWithTypes.append( [ data, dataType ] )

    return dataListWithTypes


  ###############
  #  SAVE FACT  #
  ###############
  # save fact name and time argument
  def saveFactInfo( self ) :

    # delete all data for this id in the table, if applicable
    self.cursor.execute( "DELETE FROM Fact WHERE fid='%s'" % str( self.fid ) )

    logging.debug( "INSERT INTO Fact VALUES ('" + str( self.fid ) + "','" + self.relationName + "','" + self.factTimeArg + "')" )

    self.cursor.execute( "INSERT INTO Fact VALUES ('" + str( self.fid ) + "','" + self.relationName + "','" + self.factTimeArg + "')" )


  #########################
  #  SAVE FACT DATA LIST  #
  #########################
  # save the fact data in the IR database
  def saveFactDataList( self ) :

    # delete all data for this id in the table, if applicable
    self.cursor.execute( "DELETE FROM FactData WHERE fid='%s'" % str( self.fid ) )

    dataID = 0  # allows duplicate data in dataList

    for d in self.dataListWithTypes :
      thisData = d[0]
      thisType = d[1]
      logging.debug( "INSERT INTO FactData VALUES ('" + str( self.fid ) + "','" + str( dataID ) + "','" + str( thisData ) + "','" + str( thisType ) + "')" )
      self.cursor.execute( "INSERT INTO FactData VALUES ('" + str( self.fid ) + "','" + str( dataID ) + "','" + str( thisData ) + "','" + str( thisType ) + "')" )
      dataID += 1


  ###############
  #  IS STRING  #
  ###############
  # test if the input string contains any alphabetic characters.
  # if so, then the data is a string.
  def isString( self, testString ) :
 
    logging.debug( "  IS STRING : testString = " + str( testString ) )

    if type( testString ) is int :
      return False

    elif testString.isdigit() :
      return False

    else :
      alphabet = [ 'a', 'b', 'c', \
                   'd', 'e', 'f', \
                   'g', 'h', 'i', \
                   'j', 'k', 'l', \
                   'm', 'n', 'o', \
                   'p', 'q', 'r', \
                   's', 't', 'u', \
                   'v', 'w', 'x', \
                   'y', 'z' ]
  
      flag = False
      for character in testString :
        if character.lower() in alphabet :
          flag = True
  
      logging.debug( "  IS STRING : flag = " + str( flag ) )
      return flag


#########
#  EOF  #
#########
