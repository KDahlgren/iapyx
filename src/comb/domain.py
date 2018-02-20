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

def getActiveDomain(cursor, factMeta, parsedResults):
  ''' Adds in a domain fact for each value in the active domain '''
  dom_facts = []
  str_exists = {}
  int_exists = {}
  newfactMeta = []
  int_exists[0] = True
  for x in parsedResults.values():
    for y in x:
      for z in y:
        if z=="NULL" or z=="99999999":
          continue
        if z in str_exists.keys():
          continue
        str_exists[z] = True
        if is_int(z):
          newfactMeta.append(createDomFact(cursor, "dom_int", [z]))
          continue
        newfactMeta.append(createDomFact(cursor, "dom_str", [z]))
  return factMeta + newfactMeta

def insertDomainFact(cursor, rule, ruleMeta, factMeta, parsedResults):
  checkName = rule[1]
  m = re.match(r'^(.*)_(\d*)$', rule[1])
  if m:
    checkName = m.group(1)
  if goalData.check_for_name('dom_'+checkName+'_0', ruleMeta, factMeta):
    # if the parents goal already exists
    ruleMeta, factMeta = insertDomainFactOffParDomain( cursor, rule, checkName , ruleMeta, factMeta )
  else:
    # if the parents rule does not exist, basae it off of the results
    ruleMeta, factMeta = insertDomainFactWithoutPar( cursor , rule, ruleMeta, factMeta, parsedResults )
  return ruleMeta, factMeta

def insertDomainFactOffParDomain(cursor, rule, checkName, ruleMeta, factMeta ):
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
        # if we get here we need to some sideways information passing with magic set ish stuff
        # add in the originial rule!
        goalAttList = []
        for i in range (0, len(childRule.goalAttList)):
          if i == attIndex:
            goalAttList.append(att)
          else:
            goalAttList.append('_')
        goalDict = createSubgoalDict(childRule.relationName, goalAttList, 'notin', childRule.goalTimeArg)
        ruleData['subgoalListOfDicts'].append(goalDict)

        domrid = tools.getIDFromCounters( "rid" )
        newRule = Rule.Rule( domrid, ruleData, cursor )
        newRules.append(newRule)
  ruleMeta = ruleMeta + newRules
  factMeta = factMeta + newFacts
  return ruleMeta, factMeta

def insertDomainFactWithoutPar( cursor, rule, ruleMeta, factMeta, parsedResults ):
  # print "not found parent dom"
  parRules, childRule, childVars = collectDomainRuleInfo( cursor, rule, ruleMeta )
  childRule = childRule[0]
  newRules = []
  newFacts = []
  for parRule in parRules:
    for subgoal in parRule.subgoalListOfDicts:
      if subgoal['subgoalName'] == childRule.relationName:
        # we found the matching subgoal
        for attIndex in range(0, len(childRule.goalAttList)):
          att = subgoal['subgoalAttList'][attIndex]
          if isConstant(att):
            # the attribute is constant in the parent goal therefore add a fact for it
            newFact = createDomFact( cursor, "dom_not_"+rule[0]+"_"+str(attIndex), [att])
            newFacts.append(newFact)
            continue

          found = False
          for parAttIndex in range(0, len(parRule.goalAttList)):
            parAtt = parRule.goalAttList[parAttIndex]
            if parAtt == att:
              found = True
              # found this attribute in the parent.
              # therefore can define based off this value in the parents slot
              if len(parsedResults[rule[1]])==0:
                val = '"NULL"'
                if childVars[childRule.goalAttList[attIndex]] == "int":
                  val = 99999999
                factData = {}
                factData['relationName'] = 'dom_not_'+rule[0]+'_'+str(attIndex)
                factData['dataList'] = [val]
                factData["factTimeArg"] = ''
                fid = tools.getIDFromCounters( "fid" )
                newFact = Fact.Fact(fid, factData, cursor)
                newFacts.append(newFact)

              usedVals = {}
              for val in parsedResults[rule[1]]:
                # add in a rule into the parsed results
                data = val[parAttIndex]
                if data in usedVals.keys():
                  continue
                usedVals[data] = True
                newFact = createDomFact(cursor, "dom_not_" + rule[0] + "_" + str(attIndex), [data])
                newFacts.append(newFact)
              break
          if not found:
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

            domrid = tools.getIDFromCounters( "rid" )
            newRule = Rule.Rule( domrid, ruleData, cursor )
            newRules.append(newRule)
  ruleMeta = ruleMeta + newRules
  factMeta = factMeta + newFacts
  return ruleMeta, factMeta

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

def createDomRule(name, index, timeargs, att):
  # print "createDomRule", name
  ruleData = {}
  ruleData['relationName'] = 'dom_not_'+name+'_'+str(index)
  ruleData['goalAttList'] = [att]
  ruleData['goalTimeArg'] = timeargs
  ruleData['subgoalListOfDicts'] = []
  ruleData['eqnDict'] = {}
  return ruleData

def createSubgoalDict(name, attList, polarity, timeargs):
  # print "createSubgoalDict", name
  goalDict = {}
  goalDict['subgoalName'] = name
  goalDict['subgoalAttList'] = attList
  goalDict['polarity'] = polarity
  goalDict['subgoalTimeArg'] = timeargs
  return goalDict

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

def getAllVars(cursor, rule, posRid=None):
  return getAllVarTypes(cursor, rule, posRid=posRid).iteritems()

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


def isConstant(x):
  return is_int(x) or isStringConst(x)

def isStringConst(x):
  ''' Checks if x is a string const '''
  m = re.match(r'".*"', x)
  return not (m==None)

def is_int(x):
  ''' Returns true if x is an int '''
  try:
    int(x)
    return True
  except:
    return False