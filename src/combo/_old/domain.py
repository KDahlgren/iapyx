import inspect, logging, os, string, sqlite3, sys
import copy
import re

# ------------------------------------------------------ #
# import sibling packages HERE!!!
if not os.path.abspath( __file__ + "/../.." ) in sys.path :
  sys.path.append( os.path.abspath( __file__ + "/../.." ) )
if not os.path.abspath( __file__ + "/../translators" ) in sys.path :
  sys.path.append( os.path.abspath( __file__ + "/../translators" ) )
if not os.path.abspath( __file__ + "/../../negativeWrites" ) in sys.path :
  sys.path.append( os.path.abspath( __file__ + "/../../negativeWrites" ) )

from utils       import dumpers, extractors, globalCounters, tools
from translators import c4_translator, dumpers_c4
from dedt        import Rule, Fact
from evaluators  import c4_evaluator

import goalData


#######################
#  GET ACTIVE DOMAIN  #
#######################
def getActiveDomain(cursor, factMeta, parsedResults):

  ''' Adds in a domain fact for each value in the active domain '''

  str_exists, int_exists = collectAdom(parsedResults)
  newfactMeta = []
  for x in int_exists:
    newfactMeta.append(createDomFact(cursor, "dom_int", [x]))
  for x in str_exists:
    newfactMeta.append(createDomFact(cursor, "dom_str", [x]))
  return factMeta + newfactMeta


##################
#  COLLECT ADOM  #
##################
def collectAdom(parsedResults):
  str_exists = {}
  int_exists = {}
  for x in parsedResults.values():
    for y in x:
      for z in y:
        if is_int(z):
          int_exists[z] = True
        else:
          str_exists[z] = True
  return str_exists.keys(), int_exists.keys()


########################
#  INSERT DOMAIN FACT  #
########################
# rule = tuple of the form ( subgoal name, parent rule name )
def insertDomainFact(cursor, rule, ruleMeta, factMeta, parsedResults):

  '''Insert a Domain Fact into the IR'''

  logging.debug( "  INSERT DOMAIN FACT : rule = "  + str( rule ) )

  checkName = rule[ 1 ]
  m         = re.match( r'^(.*)_(\d*)$', rule[ 1 ] )

  logging.debug( "  INSERT DOMAIN FACT : checkName = "  + str( checkName ) )
  logging.debug( "  INSERT DOMAIN FACT : m         = "  + str( m ) )

  if m :
    checkName = m.group( 1 )

  if goalData.check_for_name( 'dom_'+checkName+'_0', ruleMeta, factMeta ) :
    # if the parents goal already exists
    ruleMeta, factMeta = insertDomainFactOffParDomain( cursor, \
                                                       rule, \
                                                       checkName, \
                                                       ruleMeta, \
                                                       factMeta )
  else:
    # if the parents rule does not exist, basae it off of the results
    ruleMeta, factMeta = insertDomainFactWithoutPar( cursor, \
                                                     rule, \
                                                     ruleMeta, \
                                                     factMeta, \
                                                     parsedResults )
  return ruleMeta, factMeta


#######################################
#  INSERT DOMAIN FACT OFF PAR DOMAIN  #
#######################################
def insertDomainFactOffParDomain(cursor, rule, checkName, ruleMeta, factMeta ):

  logging.debug( "  INSERT DOMAIN FACT OFF PAR DOMAIN : rule      = " + str( rule ) )
  logging.debug( "  INSERT DOMAIN FACT OFF PAR DOMAIN : checkName = " + str( checkName ) )

  parRule, childRule, childVars = collectDomainRuleInfo( cursor, rule , ruleMeta )
  parRule = parRule[0]
  childRule = childRule[0]
  newRules = []
  newFacts = []

  # in this case  we want to base it on the previous iteration of the goal.
  for subgoal in parRule.subgoalListOfDicts:
    if subgoal['subgoalName'] == rule[0]:
      for attIndex in range (0, len(subgoal['subgoalAttList'])):
        att = childRule.goalAttList[attIndex]
        ruleData = createDomRule(rule[0], attIndex, childRule.goalTimeArg, att)

        # add in the adom
        dom_name = "dom_str"
        if childVars[childRule.goalAttList[attIndex]].lower() == 'int':
          dom_name = "dom_int"

        goalDict = createSubgoalDict(dom_name, [att], '', childRule.goalTimeArg)
        ruleData['subgoalListOfDicts'].append(goalDict)
        done = False
        for parAttIndex in range(0, len(parRule.goalAttList)):
          parAtt = parRule.goalAttList[parAttIndex]
          subgoalAtt = subgoal['subgoalAttList'][attIndex]
          if parAtt == subgoalAtt:
            # in here we define the new rule based on this parent index.
            goalDict = createSubgoalDict('dom_'+str(checkName)+'_'+str(parAttIndex),
              [att], '', childRule.goalTimeArg)
            ruleData['subgoalListOfDicts'].append(goalDict)
            domrid = tools.getIDFromCounters( "rid" )
            newRule = Rule.Rule( domrid, ruleData, cursor )
            newRules.append(newRule)
            done = True
            break

        if done:
          done = False
          continue
        # if we get here we need to some sideways information passing 
        # with magic set ish stuff.
        # add in the originial rule!
        goalAttList = []
        for i in range (0, len(childRule.goalAttList)):
          if i == attIndex:
            goalAttList.append(att)
          else:
            goalAttList.append('_')
        goalDict = createSubgoalDict( childRule.relationName, \
                                      goalAttList, \
                                      'notin', \
                                      childRule.goalTimeArg )
        ruleData['subgoalListOfDicts'].append(goalDict)

        domrid = tools.getIDFromCounters( "rid" )
        newRule = Rule.Rule( domrid, ruleData, cursor )
        newRules.append(newRule)
  ruleMeta = ruleMeta + newRules
  factMeta = factMeta + newFacts
  return ruleMeta, factMeta


####################################
#  INSERT DOMAIN FACT WITHOUT PAR  #
####################################
# what happens if a rule contains two negations?
def insertDomainFactWithoutPar( cursor, rule, ruleMeta, factMeta, parsedResults ):

  logging.debug( "  INSERT DOMAIN FACT WITHOUT PAR : rule = " + str( rule ) )

  # print "not found parent dom"
  parRules, childRule, childVars = collectDomainRuleInfo( cursor, rule, ruleMeta )
  childRule = childRule[0]
  newRules = []
  newFacts = []

  logging.debug( "------------" )
  logging.debug( "  INSERT DOMAIN FACT WITHOUT PAR : parRules :" )
  for i in parRules :
    logging.debug( "     " + dumpers.reconstructRule( i.rid, i.cursor ) )

  logging.debug( "  INSERT DOMAIN FACT WITHOUT PAR : childRule :" )
  logging.debug( "     " + dumpers.reconstructRule( childRule.rid, childRule.cursor ) )
  logging.debug( "------------" )

  for parRule in parRules:
    for subgoal in parRule.subgoalListOfDicts:

      if subgoal['subgoalName'] == childRule.relationName:

        # we found the matching subgoal
        # iterate over the attributes in the subgoal and get the
        # range of values for the attributes, given the eval results.
        for attIndex in range( 0, len( childRule.goalAttList ) ) :
          att = subgoal[ 'subgoalAttList' ][ attIndex ]
          logging.debug( "  INSERT DOMAIN FACT WITHOUT PAR : att = " + att )

          if isConstant( att ) :
            # the attribute is constant in the parent goal therefore add a fact for it
            newFact = createDomFact( cursor, "dom_not_"+rule[0]+"_"+str(attIndex), [att])
            newFacts.append(newFact)
            continue

          found = False
          for parAttIndex in range( 0, len( parRule.goalAttList ) ) :
            parAtt = parRule.goalAttList[ parAttIndex ]
            if parAtt == att :
              found = True

              logging.debug( "  INSERT DOMAIN FACT WITHOUT PAR : ...is a goal att. " )
              logging.debug( "  INSERT DOMAIN FACT WITHOUT PAR : parent results for '" + \
                             rule[1] + "'" )
              for j in parsedResults[ rule[ 1 ] ] :
                logging.debug( "       " + str( j ) )

              # found this attribute in the parent head.
              # therefore can define based off this value in the parents slot
              if len( parsedResults[ rule[ 1 ] ] ) == 0 :

                # nothing exists in the parents domain. 
                # Going to base off of whole active domain.
                if rule[0] in parsedResults.keys():

                  # in this case we can define the domain based off 
                  # its previously fired not domain
                  newFacts = newFacts + createFactsBasedOffParsedResults( cursor, \
                                                                          childVars, \
                                                                          childRule, \
                                                                          attIndex, \
                                                                          parsedResults )
                  continue

                dom_name = 'dom_str'
                if childVars[childRule.goalAttList[attIndex]] == "int":
                  dom_name = 'dom_int'

                logging.debug( "  INSERT DOMAIN FACT WITHOUT PAR : dom_name = " + \
                               dom_name )

                ruleData = createDomRule(rule[0], attIndex, childRule.goalTimeArg, att)
                goalDict = createSubgoalDict( dom_name, [att], '', childRule.goalTimeArg )

                ruleData['subgoalListOfDicts'].append(goalDict)
                domrid = tools.getIDFromCounters( "rid" )
                newRule = Rule.Rule( domrid, ruleData, cursor )
                newRules.append(newRule)

              else :
                dom_name = "dom_not_" + rule[0] + "_" + str(attIndex)
                logging.debug( "  INSERT DOMAIN FACT WITHOUT PAR : dom_name = " + \
                               dom_name )

                usedVals = {}
                logging.debug( "  INSERT DOMAIN FACT WITHOUT PAR : usedVals = " + \
                               str( usedVals ) )
                for val in parsedResults[ rule[ 1 ] ] :
                  # add in a rule into the parsed results
                  data = val[ parAttIndex ]
                  if data in usedVals.keys() :
                    continue
                  usedVals[ data ] = True
                  newFact = createDomFact( cursor, \
                                           dom_name, \
                                           [data] )
                  newFacts.append(newFact)
                break

          if not found:
            logging.debug( "  INSERT DOMAIN FACT WITHOUT PAR : ...is NOT a goal att." )
            if rule[0] in parsedResults.keys():
              newFacts = newFacts + createFactsBasedOffParsedResults( cursor, \
                                                                      childVars, \
                                                                      childRule, \
                                                                      attIndex, \
                                                                      parsedResults )
              continue

            # we have not found it therefore must go off the active domain.
            att = childRule.goalAttList[attIndex]
            dom_name = 'dom_int'
            val = att
            if childVars[att] == 'string':
              dom_name = 'dom_str'

            ruleData = createDomRule(rule[0], attIndex, childRule.goalTimeArg, val)

            # add in the adom
            dom_name = "dom_str"
            if childVars[att].lower() == 'int':
              dom_name = "dom_int"
            goalDict = createSubgoalDict(dom_name, [val], '', childRule.goalTimeArg)
            ruleData['subgoalListOfDicts'].append(goalDict)

            domrid  = tools.getIDFromCounters( "rid" )
            newRule = Rule.Rule( domrid, ruleData, cursor )
            newRules.append(newRule)

  ruleMeta = ruleMeta + newRules
  factMeta = factMeta + newFacts
  return ruleMeta, factMeta


###########################################
#  CREATE FACTS BASED OFF PARSED RESULTS  #
###########################################
def createFactsBasedOffParsedResults( cursor, childVars, rule, attIndex, parsedResults ):

  logging.debug( "  CREATE FACTS BASED OFF PARSED RESULTS : childVars = " + \
                 str( childVars ) )
  logging.debug( "  CREATE FACTS BASED OFF PARSED RESULTS : rule = " + \
                 str( rule ) )
  logging.debug( "  CREATE FACTS BASED OFF PARSED RESULTS : attIndex = " + \
                 str( attIndex ) )

  newFacts   = []
  attValues  = [ x [ attIndex ] for x in parsedResults[ rule.relationName ] ]
  strs, ints = collectAdom( parsedResults )
  domName = "dom_not_"+rule.relationName+"_"+str(attIndex)

  logging.debug( "  CREATE FACTS BASED OFF PARSED RESULTS : attValues = " + \
                 str( attValues ) )
  logging.debug( "  CREATE FACTS BASED OFF PARSED RESULTS : strs = " + \
                 str( strs ) )
  logging.debug( "  CREATE FACTS BASED OFF PARSED RESULTS : ints = " + \
                 str( ints ) )
  logging.debug( "  CREATE FACTS BASED OFF PARSED RESULTS : domName = " + \
                 str( domName ) )

  # whoa, is this way too restrictive???
  if childVars[ rule.goalAttList[ attIndex ] ] == "int" :
    for i in ints:
      if i not in attValues:
        newFact = createDomFact( cursor, domName, [ i ] )
        newFacts.append(newFact)

  else:
    for i in strs:
      if i not in attValues:
        newFact = createDomFact( cursor, domName, [i])
        newFacts.append(newFact)


  logging.debug( "  CREATE FACTS NASED OFF PARSED RESULTS : newFacts = " + \
                 str( newFacts ) )
  return newFacts


##############################
#  COLLECT DOMAIN RULE INFO  #
##############################
def collectDomainRuleInfo( cursor, rule, ruleMeta ):

  ''' Returns information about the rule  for inserting Domain facts '''

  parRule = []
  childRule = []
  for r in ruleMeta:
    if r.relationName == rule[1]:
      parRule.append(r)
    if r.relationName == rule[0]:
      childRule.append(r)
  childVars = getAllVarTypes(cursor, childRule[0])
  return parRule, childRule, childVars


#####################
#  CREATE DOM FACT  #
#####################
def createDomFact(cursor, name, data):
  # print "createDomFact", name
  for i in range(0, len(data)):
    if not is_int(data[i]):
      if not data[i].startswith('"'):
        data[i] = '"' +  data[i] + '"'
  factData = {}
  factData['relationName'] = name
  factData['dataList'] = data
  factData["factTimeArg"] = ''
  fid = tools.getIDFromCounters( "fid" )
  return Fact.Fact(fid, factData, cursor)


#####################
#  CREATE DOM RULE  #
#####################
def createDomRule(name, index, timeargs, att):
  # print "createDomRule", name
  ruleData = {}
  ruleData['relationName'] = 'dom_not_'+name+'_'+str(index)
  ruleData['goalAttList'] = [att]
  ruleData['goalTimeArg'] = timeargs
  ruleData['subgoalListOfDicts'] = []
  ruleData['eqnDict'] = {}
  return ruleData


#########################
#  CREATE SUBGOAL DICT  #
#########################
def createSubgoalDict(name, attList, polarity, timeargs):
  # print "createSubgoalDict", name
  goalDict = {}
  goalDict['subgoalName'] = name
  goalDict['subgoalAttList'] = attList
  goalDict['polarity'] = polarity
  goalDict['subgoalTimeArg'] = timeargs
  return goalDict


####################
#  CONCATE DOMAIN  #
####################
def concateDomain(cursor, negRule, posRid, ruleName):

  ''' Adds in domain subgoals to negated rules '''

  varss = getAllVars(cursor, negRule, posRid=posRid)
  for var in varss:
    if isStringConst(var[0]) or is_int(var[0]):
      continue
    if var[0] == "_" or '+' in var[0]:
      continue
    if var[1].lower() == 'int':
      rel_name = "dom_int"
    else:
      rel_name = "dom_str"
    goalDict = {}
    goalDict['subgoalName'] = rel_name
    goalDict['subgoalAttList'] = [var[0]]
    goalDict['polarity'] = ''
    goalDict['subgoalTimeArg'] = ''
    negRule.subgoalListOfDicts.append(goalDict)
  negRule = appendDomainArgs(negRule, ruleName)
  return negRule


########################
#  APPEND DOMAIN ARGS  #
########################
def appendDomainArgs(negRule, ruleName):
  ''' adds in domain subgoals specific to the rule '''
  for i in  range (0, len(negRule.goalAttList)):
    att = negRule.goalAttList[i]
    if att == '_' or '+' in att or is_int(att) or isStringConst(att):
      continue
    domainDict = {}
    domainDict['subgoalName'] = 'dom_'+ruleName+'_'+str(i)
    domainDict['subgoalAttList'] = [att]
    domainDict['polarity'] = ''
    domainDict['subgoalTimeArg'] = ''
    negRule.subgoalListOfDicts.append(domainDict)
  return negRule


##################
#  GET ALL VARS  #
##################
def getAllVars(cursor, rule, posRid=None):
  return getAllVarTypes(cursor, rule, posRid=posRid).iteritems()


#######################
#  GET ALL VAR TYPES  #
#######################
def getAllVarTypes(cursor, rule, posRid=None):
  ''' returns a dictionary with key={variable name} val={variable type} for all variables 
      for a given rule
  ''' 
  rid = rule.rid
  if posRid:
    rid = posRid
  atts = dumpers.singleRuleAttDump( str(rule.rid), cursor )
  vars = {}
  for goalAtt in atts['goalAttData']:
    if goalAtt[1] in vars.keys() and goalAtt == 'UNDEFINEDTYPE':
      continue 
    vars[goalAtt[1]] = goalAtt[2]
  for subgoal in atts['subgoalAttData']:
      for subgoalAtt in subgoal[2]:
        if goalAtt[1] in vars.keys() and goalAtt == 'UNDEFINEDTYPE':
          continue 
        vars[subgoalAtt[1]] = subgoalAtt[2]
  return vars


#################
#  IS CONSTANT  #
#################
def isConstant(x):
  return is_int(x) or isStringConst(x)


#####################
#  IS STRING CONST  #
#####################
def isStringConst(x):
  ''' Checks if x is a string const '''
  m = re.match(r'".*"', x)
  return not (m==None)


############
#  IS INT  #
############
def is_int(x):
  ''' Returns true if x is an int '''
  try:
    int(x)
    return True
  except:
    return False
