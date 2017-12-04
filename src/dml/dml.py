#/usr/bin/env python

'''
dml.py
   Define the functionality for collecting the provenance of negative subgoals
   using the DeMorgan's Law method for negative rewrites..
'''

import copy, inspect, logging, os, string, sys
import sympy
import itertools

# ------------------------------------------------------ #
# import sibling packages HERE!!!
if not os.path.abspath( __file__ + "/../.." ) in sys.path :
  sys.path.append( os.path.abspath( __file__ + "/../.." ) )

if not os.path.abspath( __file__ + "/../../dedt/translators" ) in sys.path :
  sys.path.append( os.path.abspath( __file__ + "/../../dedt/translators" ) )

from dedt        import Rule
from evaluators  import c4_evaluator
from translators import c4_translator
from utils       import clockTools, tools, dumpers

import deMorgans
import domainRewrites
import rewriteNegativeSubgoalsWithWildcards

# ------------------------------------------------------ #

#############
#  GLOBALS  #
#############

arithOps = [ "+", "-", "*", "/" ]


#########
#  DML  #
#########
# generate the new set of rules provided by the DML method for negative rewrites.
# factMeta := a list of Fact objects
# ruleMeta := a list of Rule objects
def dml( factMeta, ruleMeta, cursor ) :

  logging.debug( "  DML : running process..." )

  newRuleMeta = []

  # ----------------------------------------- #
  # enforce a uniform goal attribute lists

  ruleMeta = setUniformAttList( ruleMeta )

  # ----------------------------------------- #
  # enforce unique existential attributes
  # per rule

  ruleMeta = setUniqueExistentialVars( ruleMeta )

  # ----------------------------------------- #
  # check if any rules include negated idb
  # subgoals

  targetRuleMetaSets = getRuleMetaSetsForRulesCorrespondingToNegatedSubgoals( ruleMeta, cursor )

  # break execution if no rules contain negated IDBs
  if len( targetRuleMetaSets ) < 1 :
    return []

  # ----------------------------------------- #
  # create the adom definition and add
  # to rule meta list

  ruleMeta.extend( buildAdom( factMeta, cursor ) )

  # ----------------------------------------- #
  # create the de morgan rewrite rules
  # incorporates domComp and existential 
  # domain subgoals

  ruleMeta = doDeMorgans( targetRuleMetaSets, cursor )

  logging.debug( "  DML : returning newRuleMeta with len( newRuleMeta ) = " + str( newRuleMeta ) )

  return ruleMeta


##########################
#  SET UNIFORM ATT LIST  #
##########################
# rewrites rules to ensure a uniform schema 
# of universal variables per relation definition
def setUniformAttList( ruleMeta ) :

  for rule in ruleMeta :
    logging.debug( "  SET UNIFORM ATT LIST : " + str( rule.ruleData ) )

  # ----------------------------------------- #
  # extract rule sets

  ruleSet_dict = getRuleSets( ruleMeta )

  # ----------------------------------------- #
  # make sure universal att schemas are identical

  new_ruleMeta = []

  for relName in ruleSet_dict :

    logging.debug( "  SET UNIFORM ATT LIST : evaluating relName = " + relName )

    ruleSet = ruleSet_dict[ relName ]

    if differentAttSchemas( ruleSet ) :
      new_ruleMeta.extend( makeUniform( ruleSet ) )
    else :
      new_ruleMeta.extend( ruleSet )

  for rule in new_ruleMeta :
    logging.debug( rule.ruleData )

  return new_ruleMeta


##################
#  MAKE UNIFORM  #
##################
# input a list of rule objects.
# replace all goal attributes lists with a 
# generate a uniform set of universal variables
def makeUniform( ruleSet  ) :

  # ----------------------------------------- #
  # generate uniform set of universal 
  # attributes

  numAtts     = len( ruleSet[0].goalAttList )
  uniformAtts = getUniformAtts( numAtts )

  # ----------------------------------------- #
  # replace goal att list and universal
  # atts in subgoals

  for rule in ruleSet :

    # ----------------------------------------- #
    # get copy of original att list
    # and generate a mapping between old and
    # new att strings

    orig_goalAttList = rule.goalAttList

    if not len( uniformAtts ) == len( orig_goalAttList ) :
      tools.bp( __name__, inspect.stack()[0][3], "FATAL ERROR : inconsistent arity between new uniform att list and original att list in rule definition:\n" + str( uniformAtts ) + "\n" + str( orig_goalAttList ) + "\n" + str( rule.ruleData ) )

    attMapper = {}
    for i in range( 0, len( orig_goalAttList ) ) :
      attMapper[ orig_goalAttList[ i ] ] = uniformAtts[ i ]

    logging.debug( "  MAKE UNIFORM : attMapper = " + str( attMapper ) )

    # ----------------------------------------- #
    # replace goal att list

    rule.goalAttList               = uniformAtts
    rule.ruleData[ "goalAttList" ] = uniformAtts
    rule.saveToGoalAtt()

    # ----------------------------------------- #
    # replace universal atts in subgoals

    subgoalListOfDicts = []

    for subgoal in rule.ruleData[ "subgoalListOfDicts" ] :

      # ----------------------------------------- #
      # get subgoal info

      subgoalName    = subgoal[ "subgoalName" ]
      subgoalAttList = subgoal[ "subgoalAttList" ]
      polarity       = subgoal[ "polarity" ]
      subgoalTimeArg = subgoal[ "subgoalTimeArg" ]

      # ----------------------------------------- #
      # create new subgoal att list with 
      # replacements

      new_subgoalAttList = []

      for satt in subgoalAttList :

        if satt in attMapper :
          logging.debug( "  MAKE UNIFORM : satt = " + satt + ", attMapper[ " + satt + " ] = " + attMapper[ satt ] )
        else :
          logging.debug( "  MAKE UNIFORM : satt = " + satt )

        if satt in attMapper :
          new_subgoalAttList.append( attMapper[ satt ] )
        else :
          new_subgoalAttList.append( satt )

      logging.debug( "  MAKE UNIFORM : new_subgoalAttList = " + str( new_subgoalAttList ) )

      # ----------------------------------------- #
      # save new subgoal info

      new_sub_dict = {}
      new_sub_dict[ "subgoalName" ]    = subgoalName
      new_sub_dict[ "subgoalAttList" ] = new_subgoalAttList
      new_sub_dict[ "polarity" ]       = polarity
      new_sub_dict[ "subgoalTimeArg" ] = subgoalTimeArg

      subgoalListOfDicts.append( new_sub_dict )

    # ----------------------------------------- #
    # replace univseral atts in eqns

    eqnDict = {}

    for eqn in rule.ruleData[ "eqnDict" ] :

      # ----------------------------------------- #
      # get var list

      varList     = rule.ruleData[ "eqnDict" ][ eqn ]
      new_varList = []

      for var in varList :

        logging.debug( "  MAKE UNIFORM : var = " + var )

        if var in attMapper :
          logging.debug( "  MAKE UNIFORM : var = " + var + ", attMapper[ " + var + " ] = " + attMapper[ var ] )
        else :
          logging.debug( "  MAKE UNIFORM : var = " + var )

        if var in attMapper :
          new_varList.append( attMapper[ var ] )
        else :
          new_varList.append( var )

      # ----------------------------------------- #
      # get new eqn

      prev_vars = []
      new_eqn   = eqn
      for var in varList :

        if var in prev_vars :
          pass

        else :

          prev_vars.append( var )

          # skip existential vars
          if var in attMapper :
            new_var = attMapper[ var ]
            new_eqn = new_eqn.replace( var, new_var )

          else :
            pass

      # ----------------------------------------- #
      # save new eqn data

      logging.debug( "  MAKE UNIFORM : new_eqn     = " + new_eqn )
      logging.debug( "  MAKE UNIFORM : new_varList = " + str( new_varList ) )

      eqnDict[ new_eqn ] = new_varList


    # ----------------------------------------- #
    # save new subgoal list

    logging.debug( "  MAKE UNIFORM : subgoalListOfDicts = " + str( subgoalListOfDicts ) )

    rule.subgoalListOfDicts = subgoalListOfDicts
    rule.ruleData[ "subgoalListOfDicts" ] = subgoalListOfDicts
    rule.saveSubgoals()

    # ----------------------------------------- #
    # save new eqn dict

    logging.debug( " MAKE UNIFORM : eqnDict = " + str( eqnDict ) )

    rule.eqnDict               = eqnDict
    rule.ruleData[ "eqnDict" ] = eqnDict
    rule.saveEquations()

  return ruleSet


######################
#  GET UNIFORM ATTS  #
######################
# return a list of strings with magnitude equal to input integer
def getUniformAtts( numAtts ) :

  uniformAtt_list = []

  for i in range( 0, numAtts) :

    uniformAtt_list.append( "Att" + str( i ) )

  return uniformAtt_list


###########################
#  DIFFERENT ATT SCHEMAS  #
###########################
# check if more than one universal attribute
# lists define the schemas for the rule set
# for this relation definition.
def differentAttSchemas( ruleSet ) :

  logging.debug( "  DIFFERENT ATT SCHEMAS : ruleSet = " + str( ruleSet ) )

  for rule1 in ruleSet :

    # ----------------------------------------- #
    # get goal att list

    gattList1 = rule1.goalAttList

    for rule2 in ruleSet :

      # ----------------------------------------- #
      # get goal att list

      gattList2 = rule2.goalAttList

      # sanity check attribute list lengths
      if not len( gattList1 ) == len( gattList2 ) :
        tools.bp( __name__, inspect.stack()[0][3], "FATAL ERROR : different schema arities for rules defining the same relation. \n" + str( rule1.ruleData ) + "\n" + str( rule2.ruleData ) )

      else :

        for i in range( 0, len( gattList1 ) ) :
          if not gattList1[ i ] == gattList2[ i ] :
            logging.debug( "  DIFFERENT ATT SCHEMAS : returning True." )
            return True

  logging.debug( "  DIFFERENT ATT SCHEMAS : returning False." )
  return False


###################
#  GET RULE SETS  #
###################
# return a dict mapping relation names to lists of rule objects
def getRuleSets( ruleMeta ) :

  ruleSet_dict = {}

  for ruleObj in ruleMeta :

    # ----------------------------------------- #
    # get relation name

    relName = ruleObj.relationName

    # ----------------------------------------- #
    # organize rule object in dict

    if not relName in ruleSet_dict :
      ruleSet_dict[ relName ] = [ ruleObj ]

    else :
      ruleSet_dict[ relName ].append( ruleObj )


  return ruleSet_dict


#################################
#  SET UNIQUE EXISTENTIAL VARS  #
#################################
# rewriting existing rules to ensure each 
# rule per relation definition utilizes a unique 
# set of existential variables
def setUniqueExistentialVars( ruleMeta ) :

  # ----------------------------------------- #
  # extract rule sets

  ruleSet_dict = getRuleSets( ruleMeta )

  # ----------------------------------------- #
  # make sure universal att schemas are identical

  new_ruleMeta = []

  for relName in ruleSet_dict :

    # ----------------------------------------- #
    # make sure existential vars are unique 
    # per rule

    logging.debug( "  SET UNIQUE EXISTENTIAL VARS : evaluating relName = " + relName )

    ruleSet = ruleSet_dict[ relName ]

    if uniqueExistentialVars( ruleSet ) :
      new_ruleMeta.extend( ruleSet )
    else :
      new_ruleMeta.extend( makeUnique( ruleSet ) )

  for rule in new_ruleMeta :
    logging.debug( "  SET UNIQUE EXISTENTIAL VARS : " + str( rule.ruleData ) )

  return new_ruleMeta


#############################
#  UNIQUE EXISTENTIAL VARS  #
#############################
# check if each rule in the given rule set has a unique set of 
# existential variables.
def uniqueExistentialVars( ruleSet ) :

  for rule1 in ruleSet :

    # ----------------------------------------- #
    # extract set of existential vars

    existVars1 = extractExistentialVars( rule1.ruleData )

    for rule2 in ruleSet :

      # ----------------------------------------- #
      # skip identical rules

      if identicalRules( rule1, rule2 ) :
        pass

      else :

        # ----------------------------------------- #
        # extract set of existential vars

        existVars2 = extractExistentialVars( rule2.ruleData )

        # ----------------------------------------- #
        # check if existential var lists overlap

        if overlapping( existVars1, existVars2 ) :
          logging.debug( "  UNIQUE EXISTENTIAL VARS : returning False" )
          return False

  logging.debug( "  UNIQUE EXISTENTIAL VARS : returning True" )
  return True


#################
#  OVERLAPPING  #
#################
# check if the input lists contain any identical elements
def overlapping( existVars1, existVars2 ) :

  for var1 in existVars1 :
    if var1 in existVars2 :
      return True

  return False


#################
#  MAKE UNIQUE  #
#################
# make the existential vars per rule in the given set unique
# make existential vars unique by just appending the rule id
def makeUnique( ruleSet ) :

  for rule in ruleSet :

    # ----------------------------------------- #
    # get rid

    rid = rule.rid

    # ----------------------------------------- #
    # get goal att list

    goalAttList = rule.ruleData[ "goalAttList" ]

    # ----------------------------------------- #
    # generate new subgoal info

    subgoalListOfDicts = []

    for subgoal in rule.ruleData[ "subgoalListOfDicts" ] :

      # ----------------------------------------- #
      # get all subgoal info

      subgoalName    = subgoal[ "subgoalName" ]
      subgoalAttList = subgoal[ "subgoalAttList" ]
      polarity       = subgoal[ "polarity" ]
      subgoalTimeArg = subgoal[ "subgoalTimeArg" ]

      new_subgoalAttList = []

      for satt in subgoalAttList :

        # ----------------------------------------- #
        # append the rid to all existential vars

        if satt in goalAttList or satt == "_" :
          new_subgoalAttList.append( satt )

        else :
          new_subgoalAttList.append( satt + str( rid ) )

      # ----------------------------------------- #
      # save new subgoal

      new_sub_dict = {}
      new_sub_dict[ "subgoalName" ]    = subgoalName
      new_sub_dict[ "subgoalAttList" ] = new_subgoalAttList
      new_sub_dict[ "polarity" ]       = polarity
      new_sub_dict[ "subgoalTimeArg" ] = subgoalTimeArg

      subgoalListOfDicts.append( new_sub_dict )
  
    # ----------------------------------------- #
    # generate new eqn info

    eqnDict = {}

    for eqn in rule.ruleData[ "eqnDict" ] :

      # ----------------------------------------- #
      # get var list

      varList     = rule.ruleData[ "eqnDict" ][ eqn ]
      new_varList = []

      for var in varList :

        logging.debug( "  MAKE UNIQUE : var = " + var )

        # ----------------------------------------- #
        # append the rid to all existential vars

        if var in goalAttList :
          new_varList.append( var )

        else :
          new_var = var + str( rid )
          new_varList.append( new_var )

      # ----------------------------------------- #
      # get new eqn

      prev_vars = []
      new_eqn   = eqn
      for var in varList :

        if var in prev_vars :
          pass

        else :

          prev_vars.append( var )

          # skip universal vars
          if var in goalAttList :
            pass

          else :
            new_var = var + str( rid )
            new_eqn = new_eqn.replace( var, new_var )

      # ----------------------------------------- #
      # save new eqn data

      logging.debug( "  MAKE UNIQUE : new_eqn     = " + new_eqn )
      logging.debug( "  MAKE UNIQUE : new_varList = " + str( new_varList ) )

      eqnDict[ new_eqn ] = new_varList

    # ----------------------------------------- #
    # save new subgoal list
  
    logging.debug( " MAKE UNIQUE : subgoalListOfDicts = " + str( subgoalListOfDicts ) )
  
    rule.subgoalListOfDicts               = subgoalListOfDicts
    rule.ruleData[ "subgoalListOfDicts" ] = subgoalListOfDicts
    rule.saveSubgoals()

    # ----------------------------------------- #
    # save new eqn dict
  
    logging.debug( " MAKE UNIQUE : eqnDict = " + str( eqnDict ) )
  
    rule.eqnDict               = eqnDict
    rule.ruleData[ "eqnDict" ] = eqnDict
    rule.saveEquations()

  return ruleSet


##############################
#  EXTRACT EXISTENTIAL VARS  #
##############################
# return the list of all existential vars in this rule.
def extractExistentialVars( ruleData ) :

  allExistentialVars = []

  # ----------------------------------------- #
  # get goal att list

  goalAttList = ruleData[ "goalAttList" ]

  for subgoal in ruleData[ "subgoalListOfDicts" ] :

    # ----------------------------------------- #
    # get subgoal att list

    subgoalAttList = subgoal[ "subgoalAttList" ]

    # ----------------------------------------- #
    # collect all existential vars

    for satt in subgoalAttList :
      if not satt in goalAttList and not satt in allExistentialVars and not satt == "_" :
        allExistentialVars.append( satt )

  return allExistentialVars


#####################
#  IDENTICAL RULES  #
#####################
# check if the input rules are identical
def identicalRules( rule1, rule2 ) :

  if rule1.rid == rule2.rid :
    return True

  else :
    return False


##################
#  DO DEMORGANS  #
##################
# create a new set of rules representing the application of 
# DeMorgan's Law on the first-order logic representation
# of the targetted rules
def doDeMorgans( targetRuleMetaSets, cursor ) :

  newDMRules = []

  for ruleSet in targetRuleMetaSets :

    # ----------------------------------------- #
    # get new rule name

    orig_name = ruleSet[0].ruleData[ "relationName" ]
    not_name  = "not_" + orig_name

    # ----------------------------------------- #
    # get new rule goal attribute list
    # works only if goal att lists are uniform 
    # across all rules per set

    goalAttList = ruleSet[0].ruleData[ "goalAttList" ]

    # ----------------------------------------- #
    # get new rule goal time arg

    goalTimeArg = ""

    # ----------------------------------------- #
    # build domComp subgoal and save to 
    # rule meta list

    domCompRule = buildDomCompRule( orig_name, goalAttList, cursor )
    ruleMeta.append( domCompRule )

    # ----------------------------------------- #
    # build existential subgoal

    existentialVarsRules = buildExistentialVarsRules( ruleSet, cursor )
    ruleMeta.append( existentialVarsRules )

    # ----------------------------------------- #
    # generate sympy boolean formula over
    # subgoals across rules per set
    # such that literals are strings identifying
    # index of the rule containing the subgoal
    # and the index of the subgoal in the subgoal
    # lists of particular rules

    negated_dnf_fmla = generateBooleanFmla( ruleSet )

    # ----------------------------------------- #
    # simplify into another dnf fmla

    pos_dnf_fmla = simplifyToDNF( negated_dnf_fmla )

    # ----------------------------------------- #
    # each clause in the final dnf fmla 
    # informs the subgoal list of a new 
    # datalog rule

    newDMRules = dnfToDatalog( not_name, goalAttList, goalTimeArg, pos_dnf_fmla, domCompRule, existentialVarsRules, ruleSet, cursor )

    # ----------------------------------------- #
    # add new dm rules to the rule meta

    ruleMeta.extend( newDMRules )

    # ----------------------------------------- #
    # replace instances of the negated subgoal
    # with instances of the positive not_
    # subgoal

    ruleMeta = replaceSubgoalNegations( orig_name, not_name, ruleMeta )

  return ruleMeta


###############################
#  REPLACE SUBGOAL NEGATIONS  #
###############################
# rewrite existing rules to replace 
# instances of negated subgoal instances 
# with derived not_rules
def replaceSubgoalNegations( orig_name, not_name, ruleMeta ) :

  for rule in ruleMeta :

    # ----------------------------------------- #
    # get subgoal info

    subgoalListOfDicts = rule.subgoalListOfDicts

    new_subgoalListOfDicts = []

    for subgoal in subgoalListOfDicts :

      # ----------------------------------------- #
      # check if the subgoal is the original subgoal

      if subgoal[ "subgoalName" ] == orig_name :

        new_sub_dict = {}
        new_sub_dict[ "subgoalName" ]    = not_name
        new_sub_dict[ "subgoalAttList" ] = subgoal[ "subgoalAttList" ]
        new_sub_dict[ "polarity" ]       = ""
        new_sub_dict[ "subgoalTimeArg" ] = subgoal[ "subgoalTimeArg" ]

        new_subgoalListOfDicts.append( new_sub_dict )

      else :
        new_subgoalListOfDicts.append( subgoal )

    # ----------------------------------------- #
    # save new subgoal list

    logging.debug( " MAKE UNIQUE : new_subgoalListOfDicts = " + str( new_subgoalListOfDicts ) )

    rule.subgoalListOfDicts               = new_subgoalListOfDicts
    rule.ruleData[ "subgoalListOfDicts" ] = new_subgoalListOfDicts
    rule.saveSubgoals()

  return ruleMeta


##################################
#  BUILD EXISTENTIAL VARS RULES  #
##################################
# build the set of existential rules for this rule set
# observe exisistential vars must be unique per original rule
# for this to work.
def buildExistentialVarsRules( ruleSet, cursor ) :

  logging.debug( "--------------------------------------------------------------------------------" )
  logging.debug( "  BUILD EXISTENTIAL VARS RULES : ruleSet = " + str( [ rule.ruleData for rule in ruleSet ] ) )

  # ----------------------------------------- #
  # get the original rule name

  orig_name = ruleSet[0].ruleData[ "relationName" ]

  # ----------------------------------------- #
  # iterate over rule set

  existentialDomRules = []

  for rule in ruleSet :

    # ----------------------------------------- #
    # check if rule contains existential vars

    if containsExistentialVars( rule ) :

      logging.debug( "  BUILD EXISTENTIAL VARS RULES : rule contains existential vars : " + str( rule.ruleData ) )

      # ----------------------------------------- #
      # get the list of existential vars

      existentialAttList = getExistentialVarList( rule )

      # ----------------------------------------- #
      # iterate over rule subgoals to build a base 
      # list of dictionaries
      # preserve existential vars, but replace
      # universal vars with wildcards

      base_subgoalListOfDicts = []

      for subgoal in rule.subgoalListOfDicts :
        thisSubgoalDict = {}
        thisSubgoalDict[ "subgoalName" ]    = subgoal[ "subgoalName" ]
        thisSubgoalDict[ "polarity" ]       = ""
        thisSubgoalDict[ "subgoalTimeArg" ] = ""

        subgoalAttList = []
        for satt in subgoal[ "subgoalAttList" ] :
          if satt in existentialAttList :
            subgoalAttList.append( satt )
          else :
            subgoalAttList.append( "_" )

        thisSubgoalDict[ "subgoalAttList" ] = subgoalAttList
        base_subgoalListOfDicts.append( thisSubgoalDict )

      # ----------------------------------------- #
      # build a table of 0s and 1s marking the binary
      # polarities of the subgoals

      patternMap = getPatternMap( len( base_subgoalListOfDicts ) )

      # ----------------------------------------- #
      # build a set of new rules manifesting the
      # combinatorial set of polarity options
      # across subgoals.
      # only save safe rules.

      ruleData = {}
      ruleData[ "goalAttList" ]        = existentialAttList
      ruleData[ "goalTimeArg" ]        = ""
      ruleData[ "eqnDict" ]            = {}

      ruleData[ "relationName" ] = "dom_" + orig_name + "_"
      for att in existentialAttList :
        ruleData[ "relationName" ] += att.lower()

      for row in patternMap :

        subgoalListOfDicts = []

        for i in range( 0, len( row ) ) :

          bit = row[ i ]

          newSubgoal = base_subgoalListOfDicts[ i ]
          if bit == "0" :
            newSubgoal[ "polarity" ] = ""
          else :
            newSubgoal[ "polarity" ] = "notin"

          subgoalListOfDicts.append( newSubgoal )

        # ----------------------------------------- #
        # save rule, if safe

        ruleData[ "subgoalListOfDicts" ] = copy.deepcopy( subgoalListOfDicts )

        if isSafe( ruleData ) :
          rid = tools.getIDFromCounters( "rid" )
          existentialDomRules.append( copy.deepcopy( Rule.Rule( rid, ruleData, cursor ) ) )

  for rule in existentialDomRules :
    logging.debug( "  BUILD EXISTENTIAL VARS RULES : >>> returning existential rule with ruleData = " + str( rule.ruleData ) )

  return existentialDomRules


#############
#  IS SAFE  #
#############
# check if the rule given by the input rule data dictionary is safe
def isSafe( ruleData ) :

  #logging.debug( "  IS SAFE : ruleData = " + str( ruleData ) )

  # ----------------------------------------- #
  # get the set of goat attributes

  goalAttList = ruleData[ "goalAttList" ]

  # ----------------------------------------- #
  # get the set of all atts 
  # in positive subgoals

  subAttSet = []
  subgoalListOfDicts = ruleData[ "subgoalListOfDicts" ]
  for subgoal in subgoalListOfDicts :
    if subgoal[ "polarity" ] == "" :
      for satt in subgoal[ "subgoalAttList" ] :
        if not satt in subAttSet :
          subAttSet.append( satt )

  # ----------------------------------------- #
  # rule is safe if the set of all atts 
  # in all positive subgoals is exactly 
  # the set of goal attributes in the rule

  #logging.debug( "  IS SAFE : goalAttList = " + str( goalAttList ) )
  #logging.debug( "  IS SAFE : subAttSet   = " + str( subAttSet ) )

  flag = True
  for gatt in goalAttList :
    if not gatt in subAttSet :
      flag = False

  #logging.debug( "  IS SAFE : returning flag = " + str( flag ) )
  return flag


#####################
#  GET PATTERN MAP  #
#####################
# build a table of all possible combinations of 0s and 1s in rows of the input length
def getPatternMap( numSubgoals ) :

  logging.debug( "  GET PATTERN MAP : numSubgoals = " + str( numSubgoals ) )

  patternMap = [ ''.join( i ) for i in itertools.product( [ "0", "1" ], repeat = numSubgoals ) ]

  for row in patternMap :
    logging.debug( "  GET PATTERNMAP : row = " + row )

  return patternMap


##############################
#  GET EXISTENTIAL VAR LIST  #
##############################
# retrive the list of existential vars in the given rule
def getExistentialVarList( rule ) :

  # ----------------------------------------- #
  # get goal att list

  universalAttList = rule.goalAttList

  # ----------------------------------------- #
  # get list of all subgoal atts

  existentialAttList = []
  for subgoal in rule.subgoalListOfDicts :
    subgoalAttList = subgoal[ "subgoalAttList" ]
    for satt in subgoalAttList :
      if not satt in universalAttList and not satt in existentialAttList and not satt == "_" :
        existentialAttList.append( satt )

  return existentialAttList


###############################
#  CONTAINS EXISTENTIAL VARS  #
###############################
# check if the input rule contains existential vars
def containsExistentialVars( rule ) :

  # ----------------------------------------- #
  # get goal att list

  universalAttList = rule.goalAttList

  # ----------------------------------------- #
  # get list of all subgoal atts

  existentialAttList = []
  for subgoal in rule.subgoalListOfDicts :
    subgoalAttList = subgoal[ "subgoalAttList" ]
    for satt in subgoalAttList :
      if not satt == "_" :
        if not satt in universalAttList and not satt in existentialAttList :
          existentialAttList.append( satt )

  if len( existentialAttList ) > 0 :
    return True
  else :
    return False


#########################
#  BUILD DOM COMP RULE  #
#########################
# build the dom comp rule
def buildDomCompRule( orig_name, goalAttList, cursor ) :

  ruleData = {}

  # ----------------------------------------- #
  # build adom subgoals

  subgoalListOfDicts = []
  for att in goalAttList :
    subgoalDict = {}
    subgoalDict[ "subgoalName" ]    = "adom"
    subgoalDict[ "subgoalAttList" ] = [ att ]
    subgoalDict[ "polarity" ]       = ""
    subgoalDict[ "subgoalTimeArg" ] = ""
    subgoalListOfDicts.append( subgoalDict )

  # ----------------------------------------- #
  # build negated original subgoal

  negatedOrig_subgoal = {}
  negatedOrig_subgoal[ "subgoalName" ]    = orig_name
  negatedOrig_subgoal[ "subgoalAttList" ] = goalAttList
  negatedOrig_subgoal[ "polarity" ]       = "notin"
  negatedOrig_subgoal[ "subgoalTimeArg" ] = ""
  subgoalListOfDicts.append( negatedOrig_subgoal )

  # ----------------------------------------- #
  # save rule data and create the 
  # dom comp rule

  ruleData[ "relationName" ]       = "domComp_" + orig_name
  ruleData[ "goalAttList" ]        = goalAttList
  ruleData[ "goalTimeArg" ]        = ""
  ruleData[ "subgoalListOfDicts" ] = subgoalListOfDicts
  ruleData[ "eqnDict" ]            = {}

  rid = tools.getIDFromCounters( "rid" )

  domCompRule = Rule.Rule( rid, ruleData, cursor )

  return domCompRule


####################
#  DNF TO DATALOG  #
####################
# use the positive fmla to generate a new set of
# formulas for the not_ rules
def dnfToDatalog( not_name, goalAttList, goalTimeArg, pos_dnf_fmla, domCompRule, existentialVarsRules, ruleSet, cursor ) :

  logging.debug( "  DNF TO DATALOG : not_name     = " + not_name )
  logging.debug( "  DNF TO DATALOG : goalAttList  = " + str( goalAttList ) )
  logging.debug( "  DNF TO DATALOG : goalTimeArg  = " + goalTimeArg )
  logging.debug( "  DNF TO DATALOG : pos_dnf_fmla = " + pos_dnf_fmla )
  logging.debug( "  DNF TO DATALOG : ruleSet      = " + str( ruleSet ) )

  # ----------------------------------------- #
  # break positive dnf fmla into a set of 
  # conjuncted clauses

  clauseList = pos_dnf_fmla.replace( "INDX", "" )
  clauseList = clauseList.replace( "(", "" )      # valid b/c dnf
  clauseList = clauseList.replace( ")", "" )      # valid b/c dnf
  clauseList = clauseList.split( " | " )

  logging.debug( "  DNF TO DATALOG : clauseList = " + str( clauseList ) )

  # ----------------------------------------- #
  # iterate over clause list to create
  # the list of new dm rules

  newDMRules = []

  for clause in clauseList :

    subgoalListOfDicts = []

    # ----------------------------------------- #
    # get list of subgoal literals

    subgoalLiterals = clause.split( "&" )
    logging.debug( "  DNF TO DATALOG : subgoalLiterals = " + str( subgoalLiterals ) )

    # ----------------------------------------- #
    # iterate over the subgoal literals
    # observe the first integer represents the 
    # index of the parent target rule in the 
    # rule meta list of _targetted_ rule objects
    # the second integer represents the index
    # of the associated subgoal in the current
    # targetted rule

    for literal in subgoalLiterals :

      logging.debug( "  DNF TO DATALOG : literal = " + literal )

      # ----------------------------------------- #
      # get subgoal polarity

      if "~" in literal :
        polarity = "notin"
        literal = literal.replace( "~", "" )

      else :
        polarity = ""

      # ----------------------------------------- #
      # grab the rule and subgoal indexes

      literal      = literal.split( "_" )
      ruleIndex    = int( literal[ 0 ] )
      subgoalIndex = int( literal[ 1 ] )

      # ----------------------------------------- #
      # grab subgoal dict from appropriate rule

      rule        = ruleSet[ ruleIndex ]

      # make copy of subgoal dictionary b/c 
      # python referencing is shit sometimes

      subgoalDict = {}
      sub         = rule.subgoalListOfDicts[ subgoalIndex ]

      for key in sub :
        subgoalDict[ key ] = sub[ key ]

      logging.debug( "  DNF TO DATALOG : orig subgoalDict : " + str( subgoalDict ) )

      # ----------------------------------------- #
      # set polarity

      subgoalDict[ "polarity" ] = polarity

      # ----------------------------------------- #
      # save to subgoal list of dicts

      logging.debug( "  DNF TO DATALOG : adding subgoalDict to rule '" + not_name + "' : " + str( subgoalDict ) )

      subgoalListOfDicts.append( subgoalDict )

    # ----------------------------------------- #
    # add dom comp subgoal

    domCompSubgoal_dict = {}
    domCompSubgoal_dict[ "subgoalName" ]    = domCompRule.ruleData[ "relationName" ]
    domCompSubgoal_dict[ "subgoalAttList" ] = domCompRule.ruleData[ "goalAttList" ]
    domCompSubgoal_dict[ "polarity" ]       = ""
    domCompSubgoal_dict[ "subgoalTimeArg" ] = ""

    subgoalListOfDicts.append( domCompSubgoal_dict )

    # ----------------------------------------- #
    # add get existential domain subgoal,
    # if applicable

    if len( existentialVarsRules ) > 0 :

      # just pick the first rule, 'cause we only need the goal data
      firstExistentialVarDomRule = existentialVarsRules[0]
  
      existentialVarSubgoal_dict = {}
      existentialVarSubgoal_dict[ "subgoalName" ]    = firstExistentialVarDomRule.ruleData[ "relationName" ]
      existentialVarSubgoal_dict[ "subgoalAttList" ] = firstExistentialVarDomRule.ruleData[ "goalAttList" ]
      existentialVarSubgoal_dict[ "polarity" ]       = ""
      existentialVarSubgoal_dict[ "subgoalTimeArg" ] = ""
  
      subgoalListOfDicts.append( existentialVarSubgoal_dict )

    # ----------------------------------------- #
    # build ruleData for new rule and save

    ruleData = {}
    ruleData[ "relationName" ]       = not_name
    ruleData[ "goalAttList" ]        = goalAttList
    ruleData[ "goalTimeArg" ]        = goalTimeArg
    ruleData[ "subgoalListOfDicts" ] = subgoalListOfDicts
    ruleData[ "eqnDict" ]            = {}

    rid = tools.getIDFromCounters( "rid" )

    newDMRules.append( Rule.Rule( rid, ruleData, cursor ) )

  for newRule in newDMRules :
    logging.debug( "  DNF TO DATALOG : returing newDMRule.ruleData = " + str( newRule.ruleData ) )

  return newDMRules


#####################
#  SIMPLIFY TO DNF  #
#####################
# simplify the input sympy fmla to dnf
def simplifyToDNF( negated_dnf_fmla ) :
  return sympy.to_dnf( str( negated_dnf_fmla ) )


##############################
#  GENERATE BOOLEAN FORMULA  #
##############################
# use the subgoals in the rule set to build a negated
# dnf formula
# return the formula
# literals := "[~]ruleIndex,subgoalindex"
# ^build literals as strings concatenating 
# the index of the rule in the rule set with the 
# index of the subgoals in that rule over a comma.
# negated subgoals require a "~" prepend.
def generateBooleanFormula( ruleSet ) :

  fmla = ""

  # ----------------------------------------- #
  # iterate over each rule
  # to build a clause for the initial dnf fmla

  for i in range( 0, len( ruleSet ) ) :

    thisClause = ""
    thisRule   = ruleSet[ i ]

    # ----------------------------------------- #
    # get subgoal information

    thisSubgoalListOfDicts = thisRule.subgoalListOfDicts

    # ----------------------------------------- #
    # iterate over subgoals to get polarity

    for j in range( 0, len( thisSubgoalListOfDicts ) ) :

      thisSubgoalDict = thisSubgoalListOfDicts[ j ]
      polarity        = thisSubgoalDict[ "polarity" ]

      thisLiteral = "INDX" + str( i ) + "_INDX" + str( j )

      # ----------------------------------------- #
      # build clause to insert into return fmla

      if polarity == "notin" :
        thisLiteral = "~" + thisLiteral

      logging.debug( "  GENERATE BOOLEAN FORMULA : thisLiteral = " + thisLiteral )

      # ----------------------------------------- #
      # save in this clause

      # add an AND when necessary
      if j > 0 :
        thisClause += " & "

      thisClause += thisLiteral

      logging.debug( "  GENERATE BOOLEAN FORMULA : thisClause = " + thisClause )

    # ----------------------------------------- #
    # save the clause to the fmla

    # add an OR when necessary
    if i > 0 :
      fmla += " | "

    fmla += "(" + thisClause + ")"

  # ----------------------------------------- #
  # return the negated version of the fmla

  returnFmla = "~" + "(" + fmla + ")"

  logging.debug( "  GENERATE BOOLEAN FORMULA : returning returnFmla = " + returnFmla )

  return returnFmla


####################################################################
#  GET RULE META SETS FOR RULES CORRESPONDING TO NEGATED SUBOGALS  #
####################################################################
# obtain the list of lists of rule objects corresponding to the idb definitions
# of idbs corresponding to negated subgoals in one or more rules
def getRuleMetaSetsForRulesCorrespondingToNegatedSubgoals( ruleMeta, cursor ) :

  logging.debug( "  GET RULE META FOR RULES CORRESPONDING TO NEGATED SUBGOALS : ruleMeta with len(ruleMeta) = " + str( len( ruleMeta ) ) )

  targetRuleMetaSets = []

  # ----------------------------------------- #
  # iterate over rule meta

  for rule in ruleMeta :

    targetSet = []

    # ----------------------------------------- #
    # grab subgoal dicts

    subgoalListOfDicts = rule.ruleData[ "subgoalListOfDicts" ]

    # ----------------------------------------- #
    # iterate over subgoal data

    for subgoalDict in subgoalListOfDicts :

      logging.debug( "  GET RULE META FOR RULES CORRESPONDING TO NEGATED SUBGOALS : subgoalDict = " + str( subgoalDict ) )

      # save the rule object for the subgoal if the subgoal is negated and is idb
      if subgoalDict[ "polarity" ] == "notin" and isIDB( subgoalDict[ "subgoalName" ], cursor ) :

        # ----------------------------------------- #
        # get subgoal name

        relationName = subgoalDict[ "subgoalName" ]

        logging.debug( "  GET RULE META FOR RULES CORRESPONDING TO NEGATED SUBGOALS : relationName = " + relationName )

        # ----------------------------------------- #
        # get rule objects with the same 
        # relation name

        for r in ruleMeta :
          if r.relationName == relationName :

            targetSet.append( r )
        targetRuleMetaSets.append( targetSet )

  logging.debug( "  GET RULE META FOR RULES CORRESPONDING TO NEGATED SUBGOALS : returning targetRuleMetaSets with len(targetRuleMetaSets) = " + str( len( targetRuleMetaSets ) ) )

  return targetRuleMetaSets


################
#  BUILD ADOM  #
################
# generate the set of rules describing the entire active domain for the program,
# which is precisely the 
def buildAdom( factMeta, cursor ) :

  logging.debug( "  BUILD ADOM : factMeta = " + str( factMeta ) )

  newRules = []

  # ----------------------------------------- #
  # define relation name

  relationName = "adom"

  # ----------------------------------------- #
  # define goalAttList 

  goalAttList = [ "T" ]

  # ----------------------------------------- #
  # define goalTimeArg

  goalTimeArg = ""

  # ----------------------------------------- #
  # define subgoalListOfDicts
  #
  # iterate over each fact for edb name 
  # and arity

  for fact in factMeta :

    # ----------------------------------------- #
    # get relation name

    subgoalName = fact.relationName

    # ----------------------------------------- #
    # get length of data list

    numAdomRulesForThisFact = len( fact.dataListWithTypes )

    # ----------------------------------------- #
    # need one adom rule per datum in the fact

    for i in range( 0, numAdomRulesForThisFact ) :

      subgoalListOfDicts = []
      oneSubgoalDict = {}

      # ----------------------------------------- #
      # define subgoal attribute list

      subgoalAttList = []
      for j in range( 0, numAdomRulesForThisFact ) :

        if i == j :
          subgoalAttList.append( "T" )
        else :
          subgoalAttList.append( "_" )

      # ----------------------------------------- #
      # define subgoal polarity

      polarity = ""

      # ----------------------------------------- #
      # define subgoal time argument

      subgoalTimeArg = ""

      # ----------------------------------------- #
      # save data to subgoal dict

      oneSubgoalDict[ "subgoalName" ]    = subgoalName
      oneSubgoalDict[ "subgoalAttList" ] = subgoalAttList
      oneSubgoalDict[ "polarity" ]       = polarity
      oneSubgoalDict[ "subgoalTimeArg" ] = subgoalTimeArg

      subgoalListOfDicts.append( oneSubgoalDict )

      # ----------------------------------------- #
      # save adom rule

      newRuleData = {}
      newRuleData[ "relationName" ]       = relationName
      newRuleData[ "goalAttList" ]        = goalAttList
      newRuleData[ "goalTimeArg" ]        = goalTimeArg
      newRuleData[ "subgoalListOfDicts" ] = subgoalListOfDicts
      newRuleData[ "eqnDict" ]            = {}

      # ----------------------------------------- #
      # generate a new rule id

      rid = tools.getIDFromCounters( "rid" )

      # ----------------------------------------- #
      # create new rule object and save meta

      newRule = Rule.Rule( rid, newRuleData, cursor )
      newRules.append( newRule )

  logging.debug( "  BUILD ADOM : returning newRules = " + str( newRules ) )

  return newRules


########################
#  SET NEGATIVE RULES  #
########################
# the DB instance accessible via 'cursor' is the input program P
# translated into the intermediate representation amenable to
# syntactical anaylsis and/or translation into a particular flavor
# of Datalog.
#
# use the input program to build another program P' incorporating
# negative writes.
# 
# if P' contains negated IDB subgoals, repeat negativeWrites on P'.
#
def setNegativeRules( EOT, original_prog, oldRuleMeta, COUNTER, cursor ) :

  domainRewrites.addDomainEDBs( original_prog, cursor )

  print "COUNTER = " + str( COUNTER )

  if NEGATIVEWRITES_DEBUG :
    print " ... running set negative rules ..."

  # --------------------------------------------------- #
  # run input program and collect results               #
  # --------------------------------------------------- #
  #print "made it here1."

  # get results from running the input program P
  pResults = evaluate( COUNTER, cursor )

  # --------------------------------------------------- #
  # rewrite lines containing negated IDBs               #
  # --------------------------------------------------- #
  # maintian list of IDB goal names to rewrite.
  # IDBs pulled from rules across the entire program.
  negatedList  = []
  newDMRIDList = []

  pRIDs = getAllRuleRIDs( cursor )

  for rid in pRIDs :

    if ruleContainsNegatedIDB( rid, cursor ) :
      negatedIDBNames = rewriteParentRule( rid, cursor )
      negatedList.extend( negatedIDBNames )

    else :
      pass

  # --------------------------------------------------- #
  # add new rules for negated IDBs                      #
  # --------------------------------------------------- #
  #####################################################################
  # NOTE :                                                            #
  # negatedList is an array of [ IDB goalName, parent rule id ] pairs #
  #####################################################################
  DMList   = []
  newRules = oldRuleMeta

  # >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>> #
  # remove duplicates
  # alleviates some rule duplication in 
  # rewritten programs.
  #print 
  #print "REMOVING DUPLICATES IN NEGATED LIST :"
  #print "before : negatedList : " + str( negatedList )
  relNameList = []
  tmp         = []
  for nameData in negatedList :
    posName     = nameData[0]  # name of negated IDB subgoal
    parentRID   = nameData[1]  # rid of parent rule
    sidInParent = nameData[2]  # rid of parent rule
    if not posName in relNameList :
      tmp.append( nameData )
      relNameList.append( posName )
  negatedList = tmp
  #print "after : negatedList : " + str( negatedList )
  # >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>> #

  for nameData in negatedList :

    posName     = nameData[0]  # name of negated IDB subgoal
    parentRID   = nameData[1]  # rid of parent rule
    sidInParent = nameData[2]  # rid of parent rule

    print "nameData    : " + str( nameData )
    print "posName     : " + posName
    print "parent rule : " + dumpers.reconstructRule( parentRID, cursor )

    # ............................................................... #
    # collect all rids for this IDB name
    posNameRIDs = getRIDsFromName( posName, cursor )

    # ............................................................... #
    # rewrite original rules to shift function calls in goal atts 
    # and rewrite as a series of new rules.
    # branch condition : 
    # shift arith ops if IDB defined by multiple rules
    # otherwise, just shift the equation from the goal to the body.
    newArithRuleRIDList = shiftArithOps( posNameRIDs, cursor )

    # build rule meta for provenance rewriter
    for rid in newArithRuleRIDList :
      print ">>> arith rule : " + dumpers.reconstructRule( rid, cursor )
      newRule = Rule.Rule( rid, cursor )
      newRules.append( newRule )

    # ............................................................... #
    # rewrite original rules with uniform universal attribute variables
    # if relation possesses more than one IDB rule definition.
    if len( posNameRIDs ) > 1 :
      setUniformUniversalAttributes( posNameRIDs, cursor )

    # ............................................................... #
    # apply the demorgan's rewriting scheme to the rule set.
    newDMRIDList = applyDeMorgans( parentRID, posNameRIDs, cursor )
    DMList.append( [ newDMRIDList, posName ] )

    print "//<< parent : " + dumpers.reconstructRule( parentRID, cursor )
    for r in newDMRIDList :
      print "//>> new DM rule : " + dumpers.reconstructRule( r, cursor )

    # build rule meta for provenance rewriter
    for rid in newDMRIDList :
      newRule = Rule.Rule( rid, cursor )
      newRules.append( newRule )

    # ............................................................... #
    # add domain rule and subgoals to new DM rules.
    newRuleMeta = domainRewrites.domainRewrites( parentRID, sidInParent, posName, posNameRIDs, newDMRIDList, COUNTER, cursor )
    newRules.append( newRuleMeta )

    # --------------------------------------------------- #
    # replace existential vars with wildcards.            #
    # --------------------------------------------------- #
    #setWildcards( EOT, newDMRIDList, cursor )

  # --------------------------------------------------- #
  # final checks
  # --------------------------------------------------- #
  # ................................................... #
  # resolve negated subgoals in the new demorgans       # 
  # rules.                                              #
  # ................................................... #
  filterDMNegations( DMList, cursor )

  #if COUNTER == 1 :
  #  tools.dumpAndTerm( cursor )

  # ................................................... #
  # rewrite rules with negated EDBs containing          #
  # wildcards                                           #
  # needed to make results readable by masking          #
  # default values.                                     #
  # Also, c4 doesn't properly handle negated subgoals   #
  # with wildcards.                                     #
  # ................................................... #
  #additionalNewRules = rewriteNegativeSubgoalsWithWildcards.rewriteNegativeSubgoalsWithWildcards( cursor )
  #newRules.extend( additionalNewRules )

  #if COUNTER == 1 :
  #  tools.dumpAndTerm( cursor )

  # ................................................... #
  # branch on continued presence of negated IDBs
  # ................................................... #
  # recurse if rewritten program still contains rogue negated IDBs
  if not newDMRIDList == [] and stillContainsNegatedIDBs( newDMRIDList, cursor ) :
    COUNTER += 1
    new_original_program = c4_translator.c4datalog( cursor ) # assumes c4 evaluator
    setNegativeRules( EOT, new_original_program, newRules, COUNTER, cursor )

  # otherwise, the program only has negated EDB subgoals.
  # get the hell out of here.
  return newRules


#########################
#  FILTER DM NEGATIONS  #
#########################
# examine all new rules generated as a result of the 
# de Morgan's rewrites.
# replace subgoals satisfying the characteristics of 
# circumstances triggering previous rewrites.
# replace double negatives with calls to the original 
# positive subgoals.
def filterDMNegations( DMList, cursor ) :

  print "DUMPING RULES HERE:"
  print "DMList = " + str( DMList )

  for ruleInfo in DMList :

    newRIDList = ruleInfo[0]
    origName   = ruleInfo[1]

    for rid in newRIDList :

      print ";;;;;;;;;;;;;;;;;;;;;;;;;;;;;"
      print "FILTERING RULE "
      print "old rule:"
      print dumpers.reconstructRule( rid, cursor )

      # ............................................... #
      # replace previously rewritten negated subgoals   #
      # ............................................... #
      replaceRewrittenSubgoals( rid, origName, cursor )

      # ............................................... #
      # resolve double negatives                        #
      # ............................................... #
      resolveDoubleNegatives( rid, origName, cursor )

      print "new rule:"
      print dumpers.reconstructRule( rid, cursor )

    #tools.dumpAndTerm( cursor )


##############################
#  RESOLVE DOUBLE NEGATIVES  #
##############################
def resolveDoubleNegatives( rid, fromName, cursor ) :

  # get all subgoal ids and names
  cursor.execute( "SELECT sid,subgoalName FROM Subgoals WHERE rid=='" + rid + "'" )
  subInfo = cursor.fetchall()
  subInfo = tools.toAscii_multiList( subInfo )

  print "subInfo = " + str( subInfo )

  # check for double negatives
  for sub in subInfo :

    sid  = sub[0]
    name = sub[1]

    if "not_" in name[0:4] and "_from_" in name :

      # check if negated
      cursor.execute( "SELECT subgoalPolarity FROM Subgoals WHERE rid=='" + rid + "' AND sid=='" + sid + "'" )
      sign = cursor.fetchone()
      sign = tools.toAscii_str( sign )

      if sign == "notin" :

        # build base name
        baseName = "_from_" + fromName

        # build positive name
        nameLen     = len( name )
        baseNameLen = len( baseName )
        posName     = name[ 4 : nameLen - baseNameLen ]

        # replace subgoal name with postivie equivalent.
        cursor.execute( "UPDATE Subgoals SET subgoalName=='" + posName + "' WHERE rid=='" + rid + "' AND sid=='" + sid + "'" )

        # remove negation
        cursor.execute( "UPDATE Subgoals SET subgoalPolarity=='' WHERE rid=='" + rid + "' AND sid=='" + sid + "'" )

        print "UPDATED DOUBLE NEGATIVE!"
        print dumpers.reconstructRule( rid, cursor )
        #tools.bp( __name__, inspect.stack()[0][3], "ici" )

################################
#  REPLACE REWRITTEN SUBGOALS  #
################################
# check if the rule at rid contains a subgoal 
# such that the not_ version of the subgoal 
# already exists as a result of a previous 
# DM rewrite.
# returns boolean
def replaceRewrittenSubgoals( rid, origName, cursor ) :

  print "... running negatesRewrittenSubgoal ..."
  print "origName : " + origName
  print "this rule : " + dumpers.reconstructRule( rid, cursor )

  # .............................................. #
  # generate negated name base                     #
  # (i.e. the "_from_" portion)                    #
  baseName = "_from_" + origName

  # .............................................. #
  # get sids for all negated subgoals in this rule
  cursor.execute( "SELECT sid From Subgoals WHERE rid=='" + rid + "' AND subgoalPolarity=='notin'" )
  sids = cursor.fetchall()
  sids = tools.toAscii_list( sids )

  # get subgoal names for negated subgoals
  negatedSubs = []
  for sid in sids :
    cursor.execute( "SELECT subgoalName FROM Subgoals WHERE rid=='" + rid + "' AND sid=='" + sid + "'" )
    thisName = cursor.fetchone()
    thisName = tools.toAscii_str( thisName )
    negatedSubs.append( [ thisName, sid ] )

  # .............................................. #
  # get list of previously DM-rewritten rule names
  dmNames = prevDMRewrites_NamesOnly( cursor )

  print "dmNames : " + str( dmNames )

  # .............................................. #
  flag = False
  for sub in negatedSubs :

    name = sub[0]
    sid  = sub[1]

    # build hypothetical full name
    fullName = "not_" + name + baseName

    # check for existence
    if fullName in dmNames :

      # replace subgoal name
      cursor.execute( "UPDATE Subgoals SET subgoalName=='" + fullName + "' WHERE rid=='" + rid + "' AND sid=='" + sid + "'" )

      # replace negation argument
      cursor.execute( "UPDATE Subgoals SET polarity=='' WHERE rid=='" + rid + "' AND sid=='" + sid + "'" )

      print "REPLACED REWRITTEN SUBGOAL!"


#################################
#  PREV DM REWRITES NAMES ONLY  #
#################################
def prevDMRewrites_NamesOnly( cursor ) :

  cursor.execute( "SELECT goalName FROM Rule WHERE ( goalName LIKE 'not_%' ) AND ( goalName LIKE '%_from_%' )" )
  goalNames = cursor.fetchall()
  goalNames = tools.toAscii_list( goalNames )

  # remove duplicates
  goalNames = set( goalNames )
  goalNames = list( goalNames )

  return goalNames


#################################
#  STILL CONTAINS NEGATED IDBS  #
#################################
# check if new rules contain negated IDBs
def stillContainsNegatedIDBs( newDMRIDList, cursor ) :

  flag = False

  for rid in newDMRIDList :
    if ruleContainsNegatedIDB( rid, cursor ) :
      flag = True
    else :
      continue

  return flag


###################
#  SET WILDCARDS  #
###################
def setWildcards( EOT, newDMRIDList, cursor ) :

  for rid in newDMRIDList :

    # ---------------------------------------- #
    # get goal att list
    cursor.execute( "SELECT attID,attName,attType FROM GoalAtt WHERE rid=='" + rid + "'" )
    goalAttList = cursor.fetchall()
    goalAttList = tools.toAscii_multiList( goalAttList )

    atts = [ x[1] for x in goalAttList ]

    # ---------------------------------------- #
    # get list of subgoal ids
    cursor.execute( "SELECT sid FROM Subgoals WHERE rid=='" + rid + "'" )
    sids = cursor.fetchall()
    sids = tools.toAscii_list( sids )

    for sid in sids :

      # ---------------------------------------- #
      # branch on clock subgoals. 
      if isClock( rid, sid, cursor ) :
        handleClockSubgoals( EOT, rid, sid, cursor )

      else :
        handleNonClockSubgoals( atts, rid, sid, cursor )

      #handleNonClockSubgoals( atts, rid, sid, cursor )


###############################
#  HANDLE NON CLOCK SUBGOALS  #
###############################
def handleNonClockSubgoals( atts, rid, sid, cursor ) :
  # ---------------------------------------- #
  # get subgoal att list
  cursor.execute( "SELECT attID,attName,attType FROM SubgoalAtt WHERE rid=='" + rid + "' AND sid=='" + sid + "'" )
  subgoalAttList = cursor.fetchall()
  subgoalAttList = tools.toAscii_multiList( subgoalAttList )

  # ---------------------------------------- #
  # replace all subgoal atts not appearing in goal att list
  # with wildcards
  for att in subgoalAttList :

    attID   = att[0]
    attName = att[1]
    attType = att[2]

    if attName in atts :
      continue

    else :
      if not attName == "_" :
        replaceWithWildcard( rid, sid, attID, cursor )


##########################
#  REPLACE WITH WILCARD  #
##########################
def replaceWithWildcard( rid, sid, attID, cursor ) :
  attName = "_"
  cursor.execute( "UPDATE SubgoalAtt SET attName='" + attName + "' WHERE rid=='" + rid + "' AND sid=='" + sid + "' AND attID=='" + str( attID ) + "'" )


###########################
#  HANDLE CLOCK SUBGOALS  #
###########################
# check clock for existential attributes, regardless of whether clock is negative or positive.
# if existential attributes exist for either SndTime or DelivTime, 
# add an additional subgoal to the rule.
def handleClockSubgoals( EOT, rid, sid, cursor ) :

  # ------------------------------------ #
  # get all goal atts
  cursor.execute( "SELECT attID,attName FROM GoalAtt WHERE rid=='" + rid + "'" )
  gattData = cursor.fetchall()
  gattData = tools.toAscii_multiList( gattData )

  # ------------------------------------ #
  # get all subgoal atts
  cursor.execute( "SELECT attID,attName FROM SubgoalAtt WHERE rid=='" + rid + "' AND sid=='" + sid + "'" )
  sattData = cursor.fetchall()
  sattData = tools.toAscii_multiList( sattData )

  # ------------------------------------ #
  # check if sugoal att is existnetial
  gattList = [ att[1] for att in gattData ]
  sattList = [ att[1] for att in sattData ]

  # ------------------------------------ #
  for i in range( 0, len(sattList) ) :

    att = sattList[i]

    # check if clock subgoal att appears in goal att list
    # thus, att is universal
    if att in gattList :
      continue

    # otherwise, clock subgoal att does not appear in goal
    # att list. thus, att is existential.
    else :
      if att == "SndTime" or att == "DelivTime" :
        addAdditionalTimeDom( EOT, att, rid, cursor )

      else :
        replaceWithWildcard( rid, sid, i, cursor )


#############################
#  ADD ADDITIONAL TIME DOM  #
#############################
def addAdditionalTimeDom( EOT, att, rid, cursor ) :

  sid            = tools.getID()
  subgoalTimeArg = ""
  attID          = 0 # dom subgoals are fixed at arity 1
  attType        = "int"
  argName        = ""

  if att == "SndTime" :
    subgoalName = "dom_sndtime"
    attName     = "SndTime"

  else : # att == "DelivTime"
    subgoalName = "dom_delivtime"
    attName     = "DelivTime"

  # ------------------------------------- #
  # add info to Subgoals relation
  cursor.execute( "INSERT INTO Subgoals VALUES ('" + rid + "','" + sid + "','" + subgoalName + "','" + argName + "','" + subgoalTimeArg + "')" )

  # ------------------------------------- #
  # add info to SubgoalAtt relation
  cursor.execute( "INSERT INTO SubgoalAtt VALUES ('" + rid + "','" + sid + "','" + str( attID ) + "','" + attName + "','" + attType + "')" )

  # ------------------------------------- #
  # add relevant new facts.
  # dom ranges over all ints between 1 and EOT.
  name    = subgoalName
  timeArg = 1   # all dom facts are true starting at time 1
  attType = "int"
  attID   = 0

  for i in range( 1, EOT+1 ) :
    fid = tools.getID()

    # ------------------------------------- #
    # add info to Fact relation
    cursor.execute( "INSERT INTO Fact VALUES ('" + fid + "','" + name + "','" + str( timeArg ) + "')" )

    # ------------------------------------- #
    # add info to FactData
    attName = i
    cursor.execute( "INSERT INTO FactData VALUES ('" + fid + "','" + str( attID ) + "','" + str( attName ) + "','" + attType + "')" )


##############
#  IS CLOCK  #
##############
# check if subgoal at sid in rule rid is a clock subgoal
def isClock( rid, sid, cursor ) :

  cursor.execute( "SELECT subgoalName FROM Subgoals WHERE rid=='" + rid + "' AND sid=='" + sid + "'" )
  subName = cursor.fetchone()
  subName = tools.toAscii_str( subName )

  if subName == "clock" :
    return True

  return False


#########################
#  ADD DOMAIN SUBGOALS  #
#########################
# add domain constraints to universal attributes per rewritten rule.
def addDomainSubgoals( parentRID, posName, nameRIDS, newDMRIDList, pResults, cursor ) :

  if NEGATIVEWRITES_DEBUG :
    print "   ... running ADD DOMAIN SUBGOALS ..."

  # -------------------------------------------------- #
  # make sure results exist.                           #
  # -------------------------------------------------- #
  attDomsMap        = getAttDoms( parentRID, posName, nameRIDS, newDMRIDList, pResults, cursor )
  childParentAttMap = getChildParentAttMap( parentRID, posName, cursor )

  if not attDomsMap == {} :

    # -------------------------------------------------- #
    # build domain EDBs and add to facts tables.         #
    # -------------------------------------------------- #
    # get base att domain name
    domNameBase = getAttDomNameBase( posName )

    # save EDB facts
    newDomNames = saveDomFacts( childParentAttMap, domNameBase, attDomsMap, posName, pResults, cursor )

    # -------------------------------------------------- #
    # add attribute domain subgoals to all new DM rules. #
    # -------------------------------------------------- #
    addSubgoalsToRules( newDomNames, newDMRIDList, cursor )


##############################
#  GET CHILD PARENT ATT MAP  #
##############################
# map goal attribute indexes of parent rule to the attribute indexes of targeted negated subgoals.
def getChildParentAttMap( parentRID, posName, cursor ) :

  # ------------------------------------------- #
  # get parent name

  cursor.execute( "SELECT goalName FROM Rule WHERE rid=='" + parentRID + "'" )
  parentName = cursor.fetchone()
  parentName = tools.toAscii_str( parentName )

  # ------------------------------------------- #
  # get all parent goal atts

  cursor.execute( "SELECT attID,attName FROM GoalAtt WHERE rid=='" + parentRID + "'" )
  gatts = cursor.fetchall()
  gatts = tools.toAscii_multiList( gatts )

  # ------------------------------------------- #
  # get all subgoal atts for not_posName

  negName = "not_" + posName + "_from_" + parentName
  cursor.execute( "SELECT sid FROM Subgoals WHERE rid=='" + parentRID + "' AND subgoalName=='" + negName + "'" )
  sids = cursor.fetchall()
  sids = tools.toAscii_list( sids )

  # ------------------------------------------- #
  # map indexes of subgoal atts to goal att indexes

  childParentAttMap = {}
  for sid in sids :
    cursor.execute( "SELECT attID,attName FROM SubgoalAtt WHERE rid=='" + parentRID + "' AND sid=='" + sid + "'"  )
    satts = cursor.fetchall()
    satts = tools.toAscii_multiList( satts )

    thisMap = {}
    for gatt in gatts :
      gattID   = gatt[0]
      gattName = gatt[1]

      for satt in satts :
        sattID   = satt[0]
        sattName = satt[1]

        if sattName == "_" :
          thisMap[ sattID ] = "_"

        if gattName == sattName :
          thisMap[ sattID ] = gattID

    childParentAttMap[ sid ] = thisMap

  childParentAttMap = combineMaps( childParentAttMap )

  return childParentAttMap


##################
#  COMBINE MAPS  #
##################
# if parent rule negates the target subgoal multiple times,
# then combine the goal index valus into a list per subgoal att index 
# across negated instances.
def combineMaps( childParentAttMap ) :

  allMaps = []
  for sidkey in childParentAttMap :
    thismap = childParentAttMap[ sidkey ]
    allMaps.append( thismap )

  combinedMaps = {}

  # iniliaze att id keys with empty lists
  aMap = allMaps[0]
  for key in aMap :
    combinedMaps[ key ] = []

  # iterate over all maps and accumulate indexes
  for aMap in allMaps :
    for key in aMap :
      val = aMap[ key ]
      if not val in combinedMaps[ key ] :
        combinedMaps[ key ].append(val)

  return combinedMaps


##################
#  GET ATT DOMS  #
##################
def getAttDoms( parentRID, posName, nameRIDS, newDMRIDList, pResults, cursor ) :

  print "================================================"
  print "... running GET ATT DOMS from negativeWrites ..."
  print "================================================"

  print "parent rule    : " + dumpers.reconstructRule( parentRID, cursor )
  print "posName        : " + posName
  print "nameRIDS rules :"
  for rid in nameRIDS :
    print dumpers.reconstructRule( rid, cursor )

  attDomsMap = {}

  #----------------------------------------------------------#
  #if "missing_log" in posName[0:11] :
  #  print "parent Rule:"
  #  print dumpers.reconstructRule( parentRID, cursor )

  #  print "nameRIDS"
  #  for rid in nameRIDS :
  #    print dumpers.reconstructRule( rid, cursor )

  #  print "newDMRIDList"
  #  for rid in newDMRIDList :
  #    print dumpers.reconstructRule( rid, cursor )
  #----------------------------------------------------------#

  # ---------------------------------------------------- #
  # get the parent rule name                             #
  # ---------------------------------------------------- #
  parentName = getParentName( parentRID, cursor )

  print "parentName = " + parentName
  print "pResults[ " + parentName + " ] :"
  print pResults[ parentName ]

  # ---------------------------------------------------- #
  # get the domain for each attribute of positive rule,  #
  # as determined in pResults.                           #
  # ---------------------------------------------------- #
  attDomsMap = getParentAttDomains( pResults[ parentName ] )

  # ---------------------------------------------------- #
  # empty domain map means parent rule didn't fire.      #
  # fill doms with default values.                       #
  # ---------------------------------------------------- #
  if attDomsMap == {} :
    print "filling defaults..."
    attDomsMap = fillDefaults( newDMRIDList, cursor )

  #----------------------------------------------------------#
  #if "missing_log" in posName[0:11] :
  #  print "attDomsMap = " + str( attDomsMap )
  #  tools.bp( __name__, inspect.stack()[0][3], "shit" )
  #----------------------------------------------------------#

  print "attDomsMap = " + str( attDomsMap )

  return attDomsMap


###################
#  FILL DEFAULTS  #
###################
def fillDefaults( newDMRIDList, cursor ) :

  # get goal arity
  chooseAnRID = newDMRIDList[0]
  cursor.execute( "SELECT attID,attType FROM GoalAtt WHERE rid=='" + chooseAnRID + "'" )
  data = cursor.fetchall()
  data = tools.toAscii_multiList( data )

  lastAttID = data[-1][0]
  arity     = lastAttID + 1

  domMap = {}
  for i in range( 0, arity ) :

    attType = data[ i ][ 1 ]

    if attType == "string" :
      col = [ "_DEFAULT_STRING_" ]
    else :
      col = [ 99999999999 ]

    domMap[ i ] = col

  return domMap


#####################
#  GET PARENT NAME  #
#####################
def getParentName( parentRID, cursor ) :

  cursor.execute( "SELECT goalName FROM Rule WHERE rid=='" + parentRID + "'" )
  parentName = cursor.fetchone()
  parentName = tools.toAscii_str( parentName )

  return parentName


###########################
#  ADD SUBGOALS TO RULES  #
###########################
# add domain subgoals to new demorgan's rules.
def addSubgoalsToRules( newDomNames, newDMRIDList, cursor ) :

  for rid in newDMRIDList :

    print "this rule : " + dumpers.reconstructRule( rid, cursor )

    # ----------------------------------- #
    # get goal att list
    cursor.execute( "SELECT attID,attName,attType FROM GoalAtt WHERE rid=='" + rid + "'" )
    goalAttList = cursor.fetchall()
    goalAttList = tools.toAscii_multiList( goalAttList )

    print "goalAttList = " + str( goalAttList )
    print "newDomNames = " + str( newDomNames )

    # ----------------------------------- #
    # map att names to att indexes
    attNameIndex = {}
    for att in goalAttList :
      attID   = att[0]
      attName = att[1]
      attType = att[2]

      attIndex = attName.replace( "A", "" )

      attNameIndex[ attName ] = attIndex

    subNum = 0 
    for subName in newDomNames :

      # ----------------------------------- #
      # generate sid                        #
      # ----------------------------------- #
      sid = tools.getID()

      # ----------------------------------- #
      # fixed subgoal time arg to nothing   #
      # ----------------------------------- #
      subgoalTimeArg = ""

      # ----------------------------------- #
      # insert subgoal metadata             #
      # ----------------------------------- #
      cursor.execute( "INSERT INTO Subgoals VALUES ('" + rid + "','"  + sid + "','" + subName + "','" + subgoalTimeArg +"')" )

      # ----------------------------------- #
      # insert subgoal att data             #
      # ----------------------------------- #

      print "subNum = " + str(subNum)
      print "subName = " + str( subName )

      att     = goalAttList[ subNum ]
      attID   = 0       # domain subgoals have arity 1
      attName = att[1]
      attType = att[2]

      cursor.execute( "INSERT INTO SubgoalAtt VALUES ('" + rid + "','" + sid + "','" + str( attID ) + "','" + attName + "','" + attType + "')" )

      subNum += 1


####################
#  SAVE DOM FACTS  #
####################
def saveDomFacts( childParentAttMap, domNameBase, attDomsMap, posName, pResults, cursor ) :

  print "++++++++++++++++++++++++++++++++++++++++++++++++++"
  print "... running SAVE DOM FACTS from negativeWrites ..."
  print "++++++++++++++++++++++++++++++++++++++++++++++++++"

  #if domNameBase[0:10] == "dom_clock_" :
  #  print "domNameBase = " + domNameBase
  #  print "attDomsMap = " + str( attDomsMap )
  #  #tools.bp( __name__, inspect.stack()[0][3], "stop here" )

  if domNameBase.startswith( "dom_put_" ) :
    print "domNameBase = " + domNameBase
    print "attDomsMap = " + str( attDomsMap )
    #tools.bp( __name__, inspect.stack()[0][3], "stop here" )

  combinedAttMaps = combineAttMaps( childParentAttMap, attDomsMap, posName, pResults )

  newDomNames = []
  for att in combinedAttMaps :
    attID = att
    dom   = combinedAttMaps[ attID ]

    # -------------------------------------------- #
    # insert new fact data
    for data in dom :

      # ............................................ #
      # generate new fact id
      fid = tools.getID()

      # ............................................ #
      # create full fact name
      factName = domNameBase + str( attID ) 

      # ............................................ #
      # all dom facts are true starting at time 1
      timeArg = '1'

      # ............................................ #
      # insert new fact metadata

      #if factName == "bcast" :
      #  print "/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/"
      #  print "  CHECK THIS BCAST INSERT!!!!"

      #print "INSERT INTO Fact VALUES ('" + fid + "','" + factName + "','" + timeArg + "')"
      cursor.execute( "INSERT INTO Fact VALUES ('" + fid + "','" + factName + "','" + timeArg + "')" )

      # ............................................ #
      # set type
      if tools.isInt(data) :
        attType = 'int'
      else :
        attType = 'string'
        data    = '"' + data + '"'

      # ............................................ #
      # perform insertion
      thisID = 0 # contant because domain relations are unary.
      #print "INSERT INTO FactData VALUES ('" + fid + "','" + str(thisID) + "','" + data + "','" + attType + "')"
      cursor.execute( "INSERT INTO FactData VALUES ('" + fid + "','" + str(thisID) + "','" + str( data ) + "','" + attType + "')" )

    # -------------------------------------------- #
    # collect domain subgoal names for convenience
    if not factName in newDomNames :
      newDomNames.append( factName )

  return newDomNames


######################
#  COMBINE ATT MAPS  #
######################
def combineAttMaps( childParentAttMap, attDomsMap, posName, pResults ) :

  finalMap = {}

  print "childParentAttMap = " + str( childParentAttMap )

  for subIndex in childParentAttMap :
    goalIndexList = childParentAttMap[ subIndex ]
    thisRange = []
    for goalIndex in goalIndexList :

      # check if wildcard
      if goalIndex == "_" :
        thisRange.extend( getDomAttRangeFromSubgoalRule( subIndex, posName, pResults ) )

      else :
        thisRange.extend( attDomsMap[ goalIndex ] )

    finalMap[ subIndex ] = thisRange

  return finalMap


#########################################
#  GET DOM ATT RANGE FROM SUBGOAL RULE  #
#########################################
def getDomAttRangeFromSubgoalRule( subIndex, posName, pResults ) :

  domAttRange = []

  results = pResults[ posName ]

  domAttRange = []
  for tup in results :
    domAttRange.append( tup[ subIndex ] )

  return domAttRange

###########################
#  GET ATT DOM NAME BASE  #
###########################
def getAttDomNameBase( name ) :
  return "dom_" + name + "_att"


############################
#  GET PARENT ATT DOMAINS  #
############################
def getParentAttDomains( results ) :

  #print "results = " + str( results )

  if not results == [] :

    # get tuple arity
    arity = len( results[0] )

    attDomsMap = {}
    attID = 0
    for i in range( 0, arity ) :
      col = []
      for tup in results :
        if not tup[i] in col :
          col.append( tup[i] )
      attDomsMap[ i ] = col

    return attDomsMap

  else :
    return {}


#####################
#  SHIFT ARITH OPS  #
#####################
# given list of rids for the IDB rule set to be negated.
# for rules with arithmetic operations in the head,
# rewrite the rules into a series of separate, but sematically
# equivalent rules.
def shiftArithOps( nameRIDs, cursor ) :

  newRIDs = []

  # for each rule, check if goal contains an arithmetic operation
  for rid in nameRIDs :
    cursor.execute( "SELECT attID,attName FROM GoalAtt WHERE rid=='" + rid + "'" )
    attData = cursor.fetchall()
    attData = tools.toAscii_multiList( attData )

    for att in attData :
      attID   = att[0]
      attName = att[1]

      if containsOp( attName ) :

        # compose raw attribute with function call 
        # (only supporting arithmetic ops at the moment)
        decomposedAttName = getOp( attName )  # [ lhs, op, rhs ]
        lhs = decomposedAttName[0]
        op  = decomposedAttName[1]
        rhs = decomposedAttName[2]

        # build substitute goal attribute variable
        newAttName = lhs + "0"

        # replace the goal attribute variable
        replaceGoalAtt( newAttName, attID, rid, cursor )

        # rewrite subgoals containing the universal variable included in the equation
        # with unique subgoals referencing new IDB definitions.
        newArithRuleRIDs = arithOpSubgoalRewrites( rid, newAttName, lhs, attName, cursor )
        newRIDs.extend( newArithRuleRIDs )

  return newRIDs

###############################
#  ARITH OP SUBGOAL REWRITES  #
###############################
# given the id for one of the rules targeted for NegativeWrites,
# the string replacing the arithmetic expression in the goal,
# and the universal attribute appearing in an arithmetic expression
# in the head.
# replace the subgoals containing the universal attribute with new subgoals
# such that the new subgoals have unique names and the new replacement attribute 
# replace the universal attribute in the subgoal.
#
def arithOpSubgoalRewrites( rid, newAttName, oldExprAtt, oldExpr, cursor ) :

  newRIDs = []

  # get subgoal info
  cursor.execute( "SELECT Subgoals.sid,Subgoals.subgoalName,attID FROM Subgoals,SubgoalAtt WHERE Subgoals.rid=='" + rid + "' AND Subgoals.rid==SubgoalAtt.rid AND attName=='" + oldExprAtt + "'" )
  sidData = cursor.fetchall()
  sidData = tools.toAscii_multiList( sidData )

  # ............................................. #
  # remove duplicates
  tmp = []
  for sid in sidData :
    if not sid in tmp :
      tmp.append( sid )
  sidData = tmp
  # ............................................. #

  for data in sidData :
    sid         = data[0]
    subgoalName = data[1]
    attID       = data[2]

    # --------------------------------------------- #
    # replace subgoal name with unique new name 
    # connecting to another set of IDB rule(s)

    # get rule name for this rid
    cursor.execute( "SELECT goalName FROM Rule WHERE rid=='" + rid + "'" )
    ruleName = cursor.fetchone()
    ruleName = tools.toAscii_str( ruleName )

    # generate new unique subgoal name
    newSubgoalName = ruleName + "_" + subgoalName + "_" + tools.getID_4() + "_arithoprewrite"

    cursor.execute( "UPDATE Subgoals SET subgoalName=='" + newSubgoalName + "' WHERE rid=='" + rid + "' AND sid=='" + sid + "'" )

    # --------------------------------------------- #
    # replace universal attribute in subgoals
    cursor.execute( "UPDATE SubgoalAtt SET attName=='" + newAttName + "' WHERE rid=='" + rid + "' AND attID=='" + str( attID ) + "' AND sid=='" + sid + "'" )

    # --------------------------------------------- #
    # build new subgoal IDB rules
    newRID = arithOpSubgoalIDBWrites( rid, sid, newSubgoalName, subgoalName, oldExprAtt, oldExpr, attID, cursor )
    newRIDs.append( newRID )

  return newRIDs


#################################
#  ARITH OP SUBGOAL IDB WRITES  #
#################################
# write the new IDB rules supporting the distribution of equations
# across rule subgoals.
def arithOpSubgoalIDBWrites( oldRID, targetSID, newSubgoalName, oldSubgoalName, oldExprAtt, oldExpr, attID, cursor) :

  # --------------------------------------------- #
  # generate new rule ID                          #
  # --------------------------------------------- #
  newRID = tools.getID()

  # --------------------------------------------- #
  # insert new rule data                          #
  # --------------------------------------------- #
  rid         = newRID
  goalName    = newSubgoalName
  goalTimeArg = ""
  rewritten   = "True"
  cursor.execute( "INSERT INTO Rule (rid, goalName, goalTimeArg, rewritten) VALUES ('" + rid + "','" + goalName + "','" + goalTimeArg + "','" + rewritten + "')" )

  # --------------------------------------------- #
  # insert new rule data                          #
  # --------------------------------------------- #
  # get attribute data from original subgoal
  cursor.execute( "SELECT attID,attName,attType FROM SubgoalAtt WHERE rid=='" + oldRID + "' AND sid=='" + targetSID + "'" )
  data = cursor.fetchall()
  data = tools.toAscii_multiList( data )

  # ............................................. #
  # define the att list for the only subgoal 
  # in the new rule body and replace new goal
  # att str with old goal att str

  subgoalAttData             = data
  subgoalAttData[ attID ][1] = oldExprAtt

  # ............................................. #
  # resolve wildcard attributes to actual 
  # variables.

  subgoalAttData = resolveWildcardAtts( subgoalAttData )

  # ............................................. #
  # define goal att list and 
  # replace old arithmetic expression

  # need this shit to prevent mutating subgoalAttData
  goalAttData = []
  for thing in data :
    thisThing = [ i for i in thing ]
    goalAttData.append( thisThing )
  goalAttData[attID][1] = oldExpr

  # ............................................. #
  # perform inserts

  # goal attributes
  for att in goalAttData :
    attID   = att[0]
    attName = att[1]
    attType = att[2]
    cursor.execute( "INSERT INTO GoalAtt (rid, attID, attName, attType) VALUES ('" + rid + "','" + str( attID ) + "','" + attName + "','" + attType + "')" )

  # subgoal
  sid            = tools.getID()
  subgoalName    = oldSubgoalName
  subgoalTimeArg = ""
  cursor.execute( "INSERT INTO Subgoals (rid, sid, subgoalName, subgoalTimeArg) VALUES ('" + rid + "','" + sid + "','" + subgoalName + "','" + subgoalTimeArg + "')" )

  # subgoal attributes
  for att in subgoalAttData :
    attID   = att[0]
    attName = att[1]
    attType = att[2]
    cursor.execute( "INSERT INTO SubgoalAtt (rid, sid, attID, attName, attType) VALUES ('" + rid + "','" + sid + "','" + str( attID ) + "','" + attName + "','" + attType + "')" )

  # ............................................. #
  # resolve types
  newRule = Rule.Rule( newRID, cursor )
  newRule.setAttTypes()

  #if "log_log_" in newSubgoalName[0:8] and "_log_" in newSubgoalName[12:17] :
  #  tools.bp( __name__, inspect.stack()[0][3], "here" )

  return newRID # means building the rule object twice. kind of redundant...


###########################
#  RESOLVE WILDCARD ATTS  #
###########################
# resolve wildcard attributes to actual variables b/c
# these attributes are copied directly into the goal 
# attribute list of this new rule.
def resolveWildcardAtts( subgoalAttData ) :
  counter = 0
  for data in subgoalAttData :

    if data[1] == "_" :
      data[1] = "B" + str( counter )
      counter += 1

  return subgoalAttData


##########################
#  SHIFT FUNCTION CALLS  #
##########################
# given list of rids for IDB rule set to be negated.
# for rules with function calls in the head, shift 
# the function call to an eqn in the body.
def shiftFunctionCalls( nameRIDs, cursor ) :

  # for each rule, check if goal contains a function call
  for rid in nameRIDs :
    cursor.execute( "SELECT attID,attName FROM GoalAtt WHERE rid=='" + rid + "'" )
    attData = cursor.fetchall()
    attData = tools.toAscii_multiList( attData )

    for att in attData :
      attID   = att[0]
      attName = att[1]

      if containsOp( attName ) :

        # compose raw attribute with function call 
        # (only supporting arithmetic ops at the moment)
        decomposedAttName = getOp( attName )  # [ lhs, op, rhs ]
        lhs = decomposedAttName[0]
        op  = decomposedAttName[1]
        rhs = decomposedAttName[2]

        # build substitute goal attribute variable
        newAttName = lhs + "0"

        # generate appropriate equation using a new variable 
        # for the corresponding goal attribute.
        eqn = generateEqn( newAttName, lhs, op, rhs, rid, cursor )

        # replace the goal attribute variable
        replaceGoalAtt( newAttName, attID, rid, cursor )

        # add equation to rule
        addEqn( eqn, rid, cursor )


##################
#  GENERATE EQN  #
##################
# generate appropriate equation using a new variable 
# for the corresponding goal attribute.
def generateEqn( newAttName, lhs, op, rhs, rid, cursor ) :

  eqn = newAttName + "==" + lhs + op + rhs

  return eqn


######################
#  REPLACE GOAL ATT  #
######################
# replace the goal attribute variable
def replaceGoalAtt( newAttName, attID, rid, cursor ) :

  cursor.execute( "UPDATE GoalAtt SET attName=='" + newAttName + "' WHERE rid=='" + rid + "' AND attID=='" + str( attID ) + "'" )


#############
#  ADD EQN  #
#############
# add equation to rule
def addEqn( eqn, rid, cursor ) :

  # generate new random identifier
  eid = tools.getID()

  # add equation for this rule
  cursor.execute( "INSERT INTO Equation VALUES ('" + rid + "','" + eid + "','" + eqn + "')" )


######################################
#  SET UNIFORM UNIVERSAL ATTRIBUTES  #
######################################
# rewrite original rules with uniform universal attribute variables
def setUniformUniversalAttributes( rids, cursor ) :

  print "===================================================================="
  print "... running SET UNIFORM UNIVERSAL ATTRIBUTES from negativeWrites ..."
  print "===================================================================="

  print "positive rule version rids : " + str( rids )

  # ------------------------------------------------------- #
  # get arity of this IDB                                   #
  # ------------------------------------------------------- #
  arity = None

  #print "rids = " + str( rids )
  #for rid in rids :
  #  print dumpers.reconstructRule( rid, cursor )

  for rid in rids :
    cursor.execute( "SELECT max(attID) FROM GoalAtt WHERE rid=='" + rid + "'" )
    maxID = cursor.fetchone()
    arity = maxID[0]

  # ------------------------------------------------------- #
  # generate list of uniform attribute names of same arity  #
  # ------------------------------------------------------- #
  uniformAttributeList = []

  for i in range(0, arity) :
    uniformAttributeList.append( "A" + str( i ) )

  uniformAttributeList = tuple( uniformAttributeList ) # make immutable. fixes weird list update referencing bug.

  # ------------------------------------------------------- #
  # perform variable substitutions for rules accordingly    #
  # ------------------------------------------------------- #
  for rid in rids :

    uniformList = list( uniformAttributeList ) # make mutable
    variableMap = {}

    print "arity : " + str( arity )
    print "rule : " + dumpers.reconstructRule( rid, cursor )

    for i in range(0, arity) :

      # /////////////////////////// #
      # populate variable map
      cursor.execute( "SELECT attName FROM GoalAtt WHERE rid=='" + rid + "' AND attID=='" + str(i) + "'" )
      attName = cursor.fetchone()
      attName = tools.toAscii_str( attName )

      # handle goal attributes with operators
      if containsOp( attName ) :
        decomposedAttName = getOp( attName )  # [ lhs, op, rhs ]

        lhs = decomposedAttName[0]
        op  = decomposedAttName[1]
        rhs = decomposedAttName[2]

        variableMap[ lhs ] = uniformList[i]
        uniformList[i] = uniformList[i] + op + rhs

      else :
        variableMap[ attName ] = uniformList[i]

      # /////////////////////////// #
      # substitutions in head       #
      # /////////////////////////// #
      cursor.execute( "UPDATE GoalAtt SET attName=='" + uniformList[i] + "' WHERE rid=='" + rid + "' AND attID=='" + str(i) + "'" )

    # /////////////////////////// #
    # substitutions in subgoals   #
    # /////////////////////////// #

    # get sids for this rule
    cursor.execute( "SELECT sid FROM Subgoals WHERE rid=='" + rid + "'" )
    sids = cursor.fetchall()
    sids = tools.toAscii_list( sids )

    for sid in sids :

      # map attIDs to attNames
      attMap = {}
      cursor.execute( "SELECT attID,attName FROM SubgoalAtt WHERE rid=='" + rid + "' AND sid=='" + sid + "'"  )
      attData = cursor.fetchall()
      attData = tools.toAscii_multiList( attData )

      for att in attData :
        attID   = att[0]
        attName = att[1]

        if attName in variableMap :
          cursor.execute( "UPDATE SubgoalAtt SET attName=='" + variableMap[ attName ] + "' WHERE rid=='" + rid + "' AND sid=='" + sid + "' AND attID=='" + str( attID ) + "'" )


    # /////////////////////////// #
    # substitutions in equations  #
    # /////////////////////////// #

    # get eids for this rule
    cursor.execute( "SELECT eid FROM Equation WHERE rid=='" + rid + "'" )
    eids = cursor.fetchall()
    eids = tools.toAscii_list( eids )

    for eid in eids :

      # decompose eqn into components <- assumes structure
      # of the form : <lhsVariable>=<rhsExpression>

      cursor.execute( "SELECT eqn FROM Equation WHERE rid=='" + rid + "' AND eid=='" + eid + "'" )
      eqn = cursor.fetchone()
      eqn = tools.toAscii_str( eqn )

      eqn = eqn.split( "==" )

      lhs_eqn = eqn[0]
      rhs_eqn = eqn[1]

      decomposedAttName = getOp( rhs_eqn )  # [ lhs, op, rhs ]
      lhs_expr = decomposedAttName[0]
      op       = decomposedAttName[1]
      rhs_expr = decomposedAttName[2]

      # check contents of eqn for goal atts
      # save existential vars for later annotation of "__KEEP__" string
      # to prevent wildcard replacement in future stages.
      existentialVarMap = {}
      for var in variableMap :

        # ************************************ #
        # check lhs of eqn is a goal att
        if tools.isInt( lhs_eqn ) : 
          pass
        else :
          if var in lhs_eqn :
            lhs_eqn = variableMap[ var ]

          else : # it's an existential var

            # generate new existential var
            newExistentialVar = generateNewVar( lhs_eqn )

            # save to map
            existentialVarMap[ lhs_eqn ] = newExistentialVar

        # ************************************ #
        # check lhs of rhs expression
        if tools.isInt( lhs_expr ) : 
          pass
        else :
          if var in lhs_expr :
            lhs_expr = variableMap[ var ]
          else : # it's an existential var

            # generate new existential var
            newExistentialVar = generateNewVar( lhs_expr )

            # save to map
            existentialVarMap[ lhs_expr ] = newExistentialVar

        # ************************************ #
        # check rhs of rhs expression
        if tools.isInt( rhs_expr ) : 
          pass
        else :
          if var in rhs_expr :
            rhs_expr = variableMap[ var ]
          else : # it's an existential var

            # generate new existential var
            newExistentialVar = generateNewVar( lhs_eqn )

            # save to map
            existentialVarMap[ rhs_expr ] = newExistentialVar
        # ************************************ #

      # generate new equation using the variable substitutions, if applicable
      if lhs_expr in existentialVarMap :
        lhs_expr = existentialVarMap[ lhs_expr ]
      if rhs_expr in existentialVarMap :
        rhs_expr = existentialVarMap[ rhs_expr ]

      newEqn = lhs_eqn + "==" + lhs_expr + op + rhs_expr

      # replace old equation
      cursor.execute( "UPDATE Equation SET eqn=='" + newEqn + "' WHERE rid=='" + rid + "' AND eid=='" + eid + "'" )


      # ====================================================================== #
      # preserve existential attributes appearing in the eqn across the rule
      # ====================================================================== #

      for sid in sids :

        # get attribs
        cursor.execute( "SELECT attID,attName FROM SubgoalAtt WHERE rid=='" + rid + "' AND sid=='" + sid + "'" )
        attData = cursor.fetchall()
        attData = tools.toAscii_multiList( attData )

        for att in attData :
          attID   = att[0]
          attName = att[1]

          if attName in existentialVarMap :
            newAttName = existentialVarMap[ attName ]
            cursor.execute( "UPDATE SubgoalAtt SET attName=='" + newAttName + "' WHERE rid=='" + rid + "' AND sid=='" + sid + "' AND attID=='" + str( attID ) + "'" )


######################
#  GENERATE NEW VAR  #
######################
def generateNewVar( oldVar ) :
  return oldVar + "__KEEP__" #+ tools.getID_4()


#################
#  CONTAINS OP  #
#################
def containsOp( attName ) :

  flag = False
  for op in arithOps :
    if op in attName :
      flag = True

  return flag


############
#  GET OP  #
############
def getOp( attName ) :

  for op in arithOps :

    if op in attName :
      s = attName.split( op )
      return [ s[0], op, s[1] ]

    else :
      tools.bp( __name__, inspect.stack()[0][3], "FATAL ERROR : attName '" + attName + "' does not contain an arithOp.\nPlease check if universe exploded. Aborting..."  )


#################
#  PRINT RULES  #
#################
def printRules( rids, cursor ) :
  for rid in rids :
    print dumpers.reconstructRule( rid, cursor )


##################
#  GET ALL RIDS  #
##################
# return the list of rids for all rules in the program currently stored in cursor.
def getAllRuleRIDs( cursor ) :
  cursor.execute( "SELECT rid FROM Rule" )
  rids = cursor.fetchall()
  rids = tools.toAscii_list( rids )
  return rids


###############################
#  RULE CONTAINS NEGATED IDB  #
###############################
# check if the given rule contains a negated IDB
def ruleContainsNegatedIDB( rid, cursor ) :

  cursor.execute( "SELECT subgoalName FROM Subgoals WHERE rid='" + rid + "' AND subgoalPolarity=='notin'" )
  negatedSubgoals = cursor.fetchall()
  negatedSubgoals = tools.toAscii_list( negatedSubgoals )

  flag = False

  for subgoalName in negatedSubgoals :

    # skip arith op rewrites for now.
    if "_arithoprewrite" in subgoalName :
      pass

    # skip edb rewrites
    elif "_edbrewrite" in subgoalName :
      pass

    elif isIDB( subgoalName, cursor ) :
      flag = True

  return flag


############
#  IS IDB  #
############
# check if the given string corresponds to the name of a rule in an input program.
# if so, then the string corresponds to an IDB relation
def isIDB( subgoalName, cursor ) :

  cursor.execute( "SELECT rid FROM Rule WHERE goalName='" + subgoalName + "'" )
  rids = cursor.fetchall()
  rids = tools.toAscii_list( rids )

  if len( rids ) > 0 :
    return True
  else :
    return False


#########################
#  REWRITE PARENT RULE  #
#########################
# replace negated subgoals in parent rules with positive counterparts.
# returns name of negated subgoal replaced by positive subgoal and 
# the parent RID.
def rewriteParentRule( rid, cursor ) :

  negatedIDBNames = []

  # .................................................... #
  # get rule name
  cursor.execute( "SELECT goalName FROM Rule WHERE rid='" + rid + "'" )
  goalName = cursor.fetchone()
  goalName = tools.toAscii_str( goalName )

  # .................................................... #
  # get list of negated IDB subgoals
  cursor.execute( "SELECT sid,subgoalName FROM Subgoals WHERE rid='" + rid + "' AND argName=='notin'" )
  negatedSubgoals = cursor.fetchall()
  negatedSubgoals = tools.toAscii_multiList( negatedSubgoals )

  #print "negatedSubgoals = " + str( negatedSubgoals )

  # .................................................... #
  # substitute with appropriate positive counterpart
  for subgoal in negatedSubgoals :
    sid  = subgoal[0]
    name = subgoal[1]

    if "_arithoprewrite" in name :
      pass

    elif isIDB( name, cursor ) :

      positiveName = "not_" + name + "_from_" + goalName
  
      #print "positiveName = " + positiveName
  
      # .................................................... #
      # substitute in positive subgoal name
      cursor.execute( "UPDATE Subgoals SET subgoalName=='" + positiveName + "' WHERE rid=='" + rid + "' AND sid=='" + sid + "'" )
  
      # .................................................... #
      # erase negation on this subgoal
      cursor.execute( "UPDATE Subgoals SET subgoalPolarity=='' WHERE rid=='" + rid + "' AND sid=='" + sid + "'" )
  
      # .................................................... #
      # save for return data
      negatedIDBNames.append( [ name, rid, sid ] )


  # .................................................... #
  # remove duplicates
  #negatedIDBNames = removeDups( rid, negatedIDBNames )

  return negatedIDBNames


#################
#  REMOVE DUPS  #
#################
def removeDups( parentRID, negatedIDBNames ) :

  tmp = []
  for data in negatedIDBNames :
    name = data[0]
    if not name in tmp :
      tmp.append( name )

  return [ [ x, parentRID ] for x in tmp ]


########################
#  GET RIDS FROM NAME  #
########################
# return the list of all rids associated with a particular goal name.
def getRIDsFromName( name, cursor ) :

  cursor.execute( "SELECT rid FROM Rule WHERE goalName='" + name + "'" )
  ridList = cursor.fetchall()
  ridList = tools.toAscii_list( ridList )

  return ridList


#####################
#  APPLY DEMORGANS  #
#####################
# perform the rewrites on the negated IDB rules.
# data for new rules are stored directly in the IR database.
def applyDeMorgans( parentRID, nameRIDs, cursor ) :
  return deMorgans.doDeMorgans( parentRID, nameRIDs, cursor )



##############
#  EVALUATE  #
##############
def evaluate( COUNTER, cursor ) :

  # translate into c4 datalog
  allProgramLines = c4_translator.c4datalog( cursor )

  # run program
  print "call c4 wrapper from negativeWrites"
  results_array = c4_evaluator.runC4_wrapper( allProgramLines )

  #print "FROM evaluate in negativeWrites : results_array :"
  #print results_array

  # ----------------------------------------------------------------- #
  # dump evaluation results locally
  eval_results_dump_dir = os.path.abspath( os.getcwd() ) + "/data/"

  # make sure data dump directory exists
  if not os.path.isdir( eval_results_dump_dir ) :
    print "WARNING : evalulation results file dump destination does not exist at " + eval_results_dump_dir
    print "> creating data directory at : " + eval_results_dump_dir
    os.system( "mkdir " + eval_results_dump_dir )
    if not os.path.isdir( eval_results_dump_dir ) :
      tools.bp( __name__, inspect.stack()[0][3], "FATAL ERROR : unable to create evaluation results dump directory at " + eval_results_dump_dir )
    print "...done."

  # otherwise, data dump directory exists
  eval_results_dump_to_file( COUNTER, results_array, eval_results_dump_dir )

  # ----------------------------------------------------------------- #
  # parse results into a dictionary
  parsedResults = tools.getEvalResults_dict_c4( results_array )

  #print "FROM evaluate in negativeWrites : parsedResults :"
  #print parsedResults

  # ----------------------------------------------------------------- #

  return parsedResults


###############################
#  EVAL RESULTS DUMP TO FILE  #
###############################
def eval_results_dump_to_file( COUNTER, results_array, eval_results_dump_dir ) :

  eval_results_dump_file_path = eval_results_dump_dir + "eval_dump_" + str( COUNTER ) + ".txt"

  # save new contents
  f = open( eval_results_dump_file_path, "w" )

  for line in results_array :

    print line

    # output to file
    f.write( line + "\n" )

  f.close()


#########
#  EOF  #
#########
