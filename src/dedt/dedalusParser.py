#!/usr/bin/env python

'''
dedalusParser.py
   Define the functionality for parsing Dedalus files.
'''

import inspect, logging, os, re, string, sys, traceback
from pyparsing import *

# ------------------------------------------------------ #
# import sibling packages HERE!!!
if not os.path.abspath( __file__ + "/../.." ) in sys.path :
  sys.path.append( os.path.abspath( __file__ + "/../.." ) )

from utils import tools
# ------------------------------------------------------ #

#############
#  GLOBALS  #
#############
DEDALUSPARSER_DEBUG = tools.getConfig( "DEDT", "DEDALUSPARSER_DEBUG", bool )

eqnOps = [ "==", "!=", ">=", "<=", ">", "<" ]
opList = eqnOps + [ "+", "-", "/", "*" ]
aggOps = [ "min", "max", "sum", "count", "avg" ]


##################
#  CLEAN RESULT  #
##################
# input pyparse object of the form ([...], {...})
# output only [...]
def cleanResult( result ) :
  newResult = []

  numParsedStrings = len(result)
  for i in range(0, numParsedStrings) :
    newResult.append( result[i] )

  return newResult


###########
#  PARSE  #
###########
# input a ded line
# output parsed line
# fact returns : [ 'fact', { relationName:'relationNameStr', dataList:[ data1, ... , dataN ] } ]
# rule returns : [ 'rule', 
#                   { relationName : 'relationNameStr', 
#                   goalAttList:[ data1, ... , dataN ], 
#                   goalTimeArg : <anInteger>, 
#                   subgoalListOfDicts : [ { subgoalName : 'subgoalNameStr', 
#                                            subgoalAttList : [ data1, ... , dataN ], 
#                                            polarity : 'notin' OR '', 
#                                            subgoalTimeArg : <anInteger> }, ... ],
#                   eqnDict : { 'eqn1':{ variableList : [ 'var1', ... , 'varI' ] }, 
#                               ... , 
#                               'eqnM':{ variableList : [ 'var1', ... , 'varJ' ] }  } } ]
def parse( dedLine ) :

  logging.debug( "  PARSE : dedLine = '" + dedLine + "'" )

  # ---------------------------------------------------- #
  # CASE : line is empty

  if dedLine == "" :
    return None

  # ---------------------------------------------------- #
  # CASE : line missing semicolon

  elif not ";" in dedLine : 
    sys.exit( "  PARSE : ERROR : missing semicolon in line '" + dedLine + "'" )

  # ---------------------------------------------------- #
  # CASE : line is an include

  elif dedLine.startswith( 'include"' ) or dedLine.startswith( "include'" ) :
    pass 

  # ---------------------------------------------------- #
  # CASE : line is a FACT

  elif not ":-" in dedLine :

    if not sanityCheckSyntax_fact_preChecks( dedLine ) :
      sys.exit( "  PARSE : ERROR : invalid syntax in fact '" + dedLine + "'" )

    factData = {}

    # ///////////////////////////////// #
    # get relation name
    relationName = dedLine.split( "(", 1 )[0]

    # ///////////////////////////////// #
    # get data list
    dataList = dedLine.split( "(", 1 )[1] # string
    dataList = dataList.split( ")", 1 )[0]   # string
    dataList = dataList.split( "," )

    # ///////////////////////////////// #
    # get time arg
    ampersandIndex = dedLine.index( "@" )
    factTimeArg = dedLine[ ampersandIndex + 1 : ]
    factTimeArg = factTimeArg.replace( ";", "" ) # remove semicolons

    # ///////////////////////////////// #
    # save fact information
    factData[ "relationName" ] = relationName
    factData[ "dataList" ]     = dataList
    factData[ "factTimeArg" ]  = factTimeArg

    if not sanityCheckSyntax_fact_postChecks( dedLine, factData ) :
      sys.exit( "  PARSE : ERROR : invalid syntax in fact '" + dedLine + "'" )

    logging.debug( "  PARSE : returning " + str( [ "fact", factData ] ) )

    return [ "fact", factData ]

  # ---------------------------------------------------- #
  # CASE : line is a RULE
  #
  # rule returns : [ 'rule', 
  #                  { relationName : 'relationNameStr', 
  #                    goalAttList:[ data1, ... , dataN ], 
  #                    goalTimeArg : <anInteger>, 
  #                    subgoalListOfDicts : [ { subgoalName : 'subgoalNameStr', 
  #                                             subgoalAttList : [ data1, ... , dataN ], 
  #                                             polarity : 'notin' OR '', 
  #                                             subgoalTimeArg : <anInteger> }, ... ],
  #                    eqnDict : { 'eqn1':{ variableList : [ 'var1', ... , 'varI' ] }, 
  #                                ... , 
  #                                'eqnM':{ variableList : [ 'var1', ... , 'varJ' ] }  } } ]

  elif ":-" in dedLine :

    if not sanityCheckSyntax_rule_preChecks( dedLine ) :
      sys.exit( "  PARSE : ERROR : invalid syntax in fact '" + dedLine + "'" )

    ruleData = {}

    # ///////////////////////////////// #
    # get relation name
    relationName = dedLine.split( "(", 1 )[0]

    ruleData[ "relationName" ] = relationName

    # ///////////////////////////////// #
    # get goal attribute list
    goalAttList = dedLine.split( "(", 1 )[1] # string
    goalAttList = goalAttList.split( ")", 1 )[0]   # string
    goalAttList = goalAttList.split( "," )

    ruleData[ "goalAttList" ] = goalAttList

    # ///////////////////////////////// #
    # get goal time argument
    goalTimeArg = dedLine.split( ":-", 1 )[0] # string
    try :
      goalTimeArg = goalTimeArg.split( "@", 1 )[1] # string
    except IndexError :
      goalTimeArg = ""

    ruleData[ "goalTimeArg" ] = goalTimeArg

    # ///////////////////////////////// #
    # parse the rule body for the eqn list
    eqnDict = getEqnDict( dedLine )

    ruleData[ "eqnDict" ] = eqnDict

    # ///////////////////////////////// #
    # parse the rule body for the eqn list
    subgoalListOfDicts = getSubgoalList( dedLine, eqnDict )

    ruleData[ "subgoalListOfDicts" ] = subgoalListOfDicts

    logging.debug( "  PARSE : relationName       = " + str( relationName ) )
    logging.debug( "  PARSE : goalAttList        = " + str( goalAttList ) )
    logging.debug( "  PARSE : goalTimeArg        = " + str( goalTimeArg ) )
    logging.debug( "  PARSE : subgoalListOfDicts = " + str( subgoalListOfDicts ) )
    logging.debug( "  PARSE : eqnDict            = " + str( eqnDict ) )

    if not sanityCheckSyntax_rule_postChecks( dedLine, ruleData ) :
      sys.exit( "  PARSE : ERROR : invalid syntax in fact '" + dedLine + "'" )

    logging.debug( "  PARSE : returning " + str( [ "rule", ruleData ] ) )
    return [ "rule", ruleData ]

  # ---------------------------------------------------- #
  # CASE : wtf???

  else :
    sys.exit( "  PARSE : ERROR : this line is not an empty, a fact, or a rule : '" + dedLine + "'. aborting..." )


#############
#  HAS AGG  #
#############
# check if the input attribute contains one 
# of the supported aggregate operations.
def hasAgg( attStr ) :

  flag = False
  for agg in aggOps :
    if agg+"<" in attStr :
      flag = True

  return flag


##################
#  IS FIXED STR  #
##################
# check if the input attribute is a string,
# as indicated by single or double quotes
def isFixedStr( att ) :

  if att.startswith( "'" ) and att.startswith( "'" ) :
    return True
  elif att.startswith( '"' ) and att.startswith( '"' ) :
    return True
  else :
    return False


##################
#  IS FIXED INT  #
##################
# check if input attribute is an integer
def isFixedInt( att ) :

  if att.isdigit() :
    return True
  else :
    return False


##########################################
#  SANITY CHECK SYNTAX RULE POST CHECKS  #
##########################################
# make sure contents of rule make sense.
def sanityCheckSyntax_rule_postChecks( ruleLine, ruleData ) :

  # ------------------------------------------ #
  # make sure all subgoals in next rules have
  # identical first attributes

  if ruleData[ "goalTimeArg" ] == "next" :
    subgoalListOfDicts = ruleData[ "subgoalListOfDicts" ]
    firstAtts          = []
    for sub in subgoalListOfDicts :
      subgoalAttList = sub[ "subgoalAttList" ]
      firstAtts.append( subgoalAttList[0] )

    firstAtts = set( firstAtts )
    if not len( firstAtts ) < 2 :
      sys.exit( "  SANITY CHECK SYNTAX RULE : ERROR : invalid syntax in line '" + ruleLine + "'\n    all subgoals in next rules must have identical first attributes.\n" )

  # ------------------------------------------ #
  # make sure all goal and subgoal attribute 
  # variables start with a captial letter

  goalAttList = ruleData[ "goalAttList" ]
  for att in goalAttList :
    if not att[0].isalpha() or not att[0].isupper() :
      if not hasAgg( att ) : # att is not an aggregate call
        if not isFixedStr( att ) :  # att is not a fixed data input
          if not isFixedInt( att ) :  # att is not a fixed data input
            sys.exit( "  SANITY CHECK SYNTAX RULE : ERROR : invalid syntax in line '" + ruleLine + "'\n    the goal contains contains an attribute not starting with a capitalized letter: '" + att + "'. \n    attribute variables must start with an upper case letter." )

  subgoalListOfDicts = ruleData[ "subgoalListOfDicts" ]
  for sub in subgoalListOfDicts :

    subgoalAttList = sub[ "subgoalAttList" ]
    for att in subgoalAttList :

      if not att[0].isalpha() or not att[0].isupper() :
        if not hasAgg( att ) : # att is not an aggregate call
          if not isFixedStr( att ) :  # att is not a fixed data input
            if not isFixedInt( att ) :  # att is not a fixed data input
              # subgoals can have wildcards
              if not att[0] == "_" :
                sys.exit( "  SANITY CHECK SYNTAX RULE : ERROR : invalid syntax in line '" + ruleLine + "'\n    subgoal '" + sub[ "subgoalName" ] + "' contains an attribute not starting with a capitalized letter: '" + att + "'. \n    attribute variables must start with an upper case letter." )

  # ------------------------------------------ #
  # make sure all relation names are 
  # lower case

  goalName = ruleData[ "relationName" ]
  for c in goalName :
    if c.isalpha() and not c.islower() :
      sys.exit( "  SANITY CHECK SYNTAX RULE : ERROR : invalid syntax in line '" + ruleLine + "'\n    The goal name '" + goalName + "' contains an upper-case letter. \n    relation names must contain only lower-case characters." )

  subgoalListOfDicts = ruleData[ "subgoalListOfDicts" ]
  for sub in subgoalListOfDicts :
    subName = sub[ "subgoalName" ]
    for c in subName :
      if c.isalpha() and not c.islower() :
        sys.exit( "  SANITY CHECK SYNTAX RULE : ERROR : invalid syntax in line '" + ruleLine + "'\n    The subgoal name '" + subName + "' contains an upper-case letter. \n    relation names must contain only lower-case characters." )

  return True


#########################################
#  SANITY CHECK SYNTAX RULE PRE CHECKS  #
#########################################
# make an initial pass on the rule syntax
def sanityCheckSyntax_rule_preChecks( ruleLine ) :

  # make sure parentheses make sense
  if not ruleLine.count( "(" ) == ruleLine.count( ")" ) :
    sys.exit( "  SANITY CHECK SYNTAX RULE : ERROR : invalid syntax in line '" + ruleLine + "'\n    rule contains inconsistent counts for '(' and ')'" )

  # make sure number of single is even
  if not ruleLine.count( "'" ) % 2 == 0 :
    sys.exit( "  SANITY CHECK SYNTAX RULE : ERROR : invalid syntax in line '" + ruleLine + "'\n    rule contains inconsistent use of single quotes." )

  # make sure number of double quotes is even
  if not ruleLine.count( '"' ) % 2 == 0 :
    sys.exit( "  SANITY CHECK SYNTAX RULE : ERROR : invalid syntax in line '" + ruleLine + "'\n    rule contains inconsistent use of single quotes." )

  return True


##################
#  GET EQN DICT  #
##################
# get the complete dictionary of equations in the given rule line
def getEqnDict( dedLine ) :

  eqnDict = {}

  body = getBody( dedLine )
  body = body.split( "," )

  # get the complete list of eqns from the rule body
  eqnList = []
  for thing in body :
    if isEqn( thing ) :
      eqnList.append( thing )

  # get the complete list of variables per eqn
  for eqn in eqnList :
    varList = getEqnVarList( eqn )
    eqnDict[ eqn ] = varList

  return eqnDict


######################
#  GET EQN VAR LIST  #
######################
def getEqnVarList( eqnString ) :

  for op in opList :
    eqnString = eqnString.replace( op, "___COMMA___" )

  varList = eqnString.split( "___COMMA___" )

  return varList


######################
#  GET SUBGOAL LIST  #
######################
# get the complete list of subgoals in the given rule line
#  subgoalListOfDicts : [ { subgoalName : 'subgoalNameStr', 
#                           subgoalAttList : [ data1, ... , dataN ], 
#                           polarity : 'notin' OR '', 
#                           subgoalTimeArg : <anInteger> }, ... ]
def getSubgoalList( dedLine, eqnList ) :

  subgoalListOfDicts = []

  # ========================================= #
  # replace eqn instances in line
  for eqn in eqnList :
    dedLine = dedLine.replace( eqn, "" )

  dedLine = dedLine.replace( ",,", "," )

  # ========================================= #
  # grab subgoals

  # grab indexes of commas separating subgoals
  indexList = getCommaIndexes( getBody( dedLine ) )

  #print indexList

  # replace all subgoal-separating commas with a special character sequence
  body     = getBody( dedLine )
  tmp_body = ""
  for i in range( 0, len( body ) ) :
    if not i in indexList :
      tmp_body += body[i]
    else :
      tmp_body += "___SPLIT___HERE___"
  body = tmp_body
  #print body

  # generate list of separated subgoals by splitting on the special
  # character sequence
  subgoals = body.split( "___SPLIT___HERE___" )

  # ========================================= #
  # parse all subgoals in the list
  for sub in subgoals :

    #print sub

    currSubData = {}

    if not sub == "" :

      # get subgoalTimeArg
      try :
        ampersandIndex = sub.index( "@" )
        subgoalTimeArg = sub[ ampersandIndex + 1 : ]
        sub = sub.replace( "@" + subgoalTimeArg, "" ) # remove the time arg from the subgoal
      except ValueError :
        subgoalTimeArg = ""

      # get subgoal name and polarity
      data        = sub.replace( ")", "" )
      data        = data.split( "(" )
      subgoalName = data[0]
      subgoalName = subgoalName.replace( ",", "" ) # remove any rogue commas
      if " notin " in subgoalName :
        polarity    = "notin"
        subgoalName = subgoalName.replace( " notin ", "" )
      else :
        polarity = ""

      # get subgoal att list
      subgoalAttList = data[1]
      subgoalAttList = subgoalAttList.split( "," )

      # collect subgoal data
      currSubData[ "subgoalName" ]    = subgoalName
      currSubData[ "subgoalAttList" ] = subgoalAttList
      currSubData[ "polarity" ]       = polarity
      currSubData[ "subgoalTimeArg" ] = subgoalTimeArg

      # save data for this subgoal
      subgoalListOfDicts.append( currSubData )

  #print subgoalListOfDict
  #sys.exit( "foo" )
  return subgoalListOfDicts


#######################
#  GET COMMA INDEXES  #
#######################
# given a rule body, get the indexes of commas separating subgoals.
def getCommaIndexes( body ) :

  underscoreStr = getCommaIndexes_helper( body )

  indexList = []
  for i in range( 0, len( underscoreStr ) ) :
    if underscoreStr[i] == "," :
      indexList.append( i )

  return indexList


##############################
#  GET COMMA INDEXES HELPER  #
##############################
# replace all paren contents with underscores
def getCommaIndexes_helper( body ) :

  # get the first occuring paren group
  nextParenGroup = "(" + re.search(r'\((.*?)\)',body).group(1) + ")"

  # replace the group with the same number of underscores in the body
  replacementStr = ""
  for i in range( 0, len(nextParenGroup)-2 ) :
    replacementStr += "_"
  replacementStr = "_" + replacementStr + "_" # use underscores to replace parentheses

  body = body.replace( nextParenGroup, replacementStr )

  # BASE CASE : no more parentheses
  if not "(" in body :
    return body

  # RECURSIVE CASE : yes more parentheses
  else :
    return getCommaIndexes_helper( body )


############
#  IS EQN  #
############
# check if input contents from the rule body is an equation
def isEqn( sub ) :

  flag = False
  for op in eqnOps :
    if op in sub :
      flag = True

  return flag


##############
#  GET BODY  #
##############
# return the body str from the input rule
def getBody( query ) :

  body = query.replace( "notin", "___NOTIN___" )
  body = body.replace( ";", "" )
  body = body.translate( None, string.whitespace )
  body = body.split( ":-" )
  body = body[1]
  body = body.replace( "___NOTIN___", " notin " )

  return body


##############################
#  SANITY CHECK SYNTAX FACT  #
##############################
# check fact lines for invalud syntax.
# abort if invalid syntax found.
# return True otherwise.
def sanityCheckSyntax_fact_preChecks( factLine ) :

  logging.debug( "  SANITY CHECK SYNTAX FACT : running process..." )
  logging.debug( "  SANITY CHECK SYNTAX FACT : factLine = " + str( factLine ) )

  # ------------------------------------------ #
  # facts must have time args.

  if not "@" in factLine :
    sys.exit( "  SANITY CHECK SYNTAX FACT : ERROR : invalid syntax in line '" + factLine + "'\n    line does not contain a time argument.\n" )

  # ------------------------------------------ #
  # check parentheses

  if not factLine.count( "(" ) < 2 :
    sys.exit( "  SANITY CHECK SYNTAX FACT : ERROR : invalid syntax in line '" + factLine + "'\n    line contains more than one '('\n" )
  elif not factLine.count( "(" ) > 0 :
    sys.exit( "  SANITY CHECK SYNTAX FACT : ERROR : invalid syntax in line '" + factLine + "'\n    line contains fewer than one '('\n" )
  if not factLine.count( ")" ) < 2 :
    sys.exit( "  SANITY CHECK SYNTAX FACT : ERROR : invalid syntax in line '" + factLine + "'\n    line contains more than one ')'\n" )
  elif not factLine.count( ")" ) > 0 :
    sys.exit( "  SANITY CHECK SYNTAX FACT : ERROR : invalid syntax in line '" + factLine + "'\n    line contains fewer than one ')'\n" )

  return True


##########################################
#  SANITY CHECK SYNTAX FACT POST CHECKS  #
##########################################
# check fact lines for invalud syntax.
# abort if invalid syntax found.
# return True otherwise.
def sanityCheckSyntax_fact_postChecks( factLine, factData ) :

  logging.debug( "  SANITY CHECK SYNTAX FACT : running process..." )
  logging.debug( "  SANITY CHECK SYNTAX FACT : factData = " + str( factData ) )

  # ------------------------------------------ #
  # check quotes on input string data

  dataList = factData[ "dataList" ]
  for data in dataList :
    logging.debug( "  SANITY CHECK SYNTAX FACT : data = " + str( data ) + ", type( data  ) = " + str( type( data) ) + "\n" )
    if isString( data ) :
      # check quotes
      if not data.count( "'" ) == 2 and not data.count( '"' ) == 2 :
        sys.exit( "  SANITY CHECK SYNTAX FACT : ERROR : invalid syntax in fact '" + str( factLine ) + "'\n    fact definition contains string data not surrounded by either exactly two single quotes or exactly two double quotes : " + data + "\n" )
    else :
      pass

  # ------------------------------------------ #
  # check time arg

  factTimeArg = factData[ "factTimeArg" ]
  if not factTimeArg.isdigit() :
    sys.exit( "  SANITY CHECK SYNTAX FACT : ERROR : invalid syntax in fact data list '" + str( factLine ) + "'\n    fact definition has no time arg." )

  return True


###############
#  IS STRING  #
###############
# test if the input string contains any alphabetic characters.
# if so, then the data is a string.
def isString( testString ) :

  logging.debug( "  IS STRING : testString = " + str( testString ) )

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


###################
#  PARSE DEDALUS  #
###################
# input name of raw dedalus file
# output array of arrays containing the contents of parsed ded lines
def parseDedalus( dedFile ) :

  logging.debug( "  PARSE DEDALUS : dedFile = " + dedFile )

  parsedLines = []

  # ------------------------------------------------------------- #
  # remove all multiline whitespace and place all rules 
  # on individual lines

  lineList = sanitizeFile( dedFile )   

  # ------------------------------------------------------------- #
  # iterate over each line and parse

  for line in lineList :
    result = parse( line ) # parse returns None on empty lines
    if result :
      parsedLines.append( result )

  logging.debug( "  PARSE DEDALUS : parsedLines = " + str( parsedLines ) )

  return parsedLines

  # ------------------------------------------------------------- #


###################
#  SANITIZE FILE  #
###################
# input all lines from input file
# combine all lines into a single huge string.
# to preserve syntax :
#   replace semicolons with string ';___NEWLINE___'
#   replace all notins with '___notin___'
# split on '___NEWLINE__'
def sanitizeFile( dedFile ) :

  bigLine = ""

  # "always check if files exist" -- Ye Olde SE proverb
  if os.path.isfile( dedFile ) :

    f = open( dedFile, "r" )

    # combine all lines into one big line
    for line in f :

      line = line.replace( "//", "___THISISACOMMENT___" )
      line = line.split( "___THISISACOMMENT___", 1 )[0]

      line = line.replace( "notin", "___notin___" )    # preserve notins
      line = line.replace( ";", ";___NEWLINE___" )     # preserve semicolons
      line = line.translate( None, string.whitespace ) # remove all whitespace
      bigLine += line

    f.close()

    bigLine  = bigLine.replace( "___notin___", " notin " ) # restore notins
    lineList = bigLine.split( "___NEWLINE___" )            # split big line into a list of lines

    return lineList

  else :
    sys.exit( "ERROR: File at " + dedFile + " does not exist.\nAborting..." )


#########
#  EOF  #
#########
