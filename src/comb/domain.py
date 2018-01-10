import inspect, logging, os, string, sqlite3, sys
import copy

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

def getActiveDomain(cursor, parsedResults):
  ''' Adds in a domain fact for each value in the active domain '''
  cursor.execute('''
    SELECT fd.data
    FROM Fact f
    LEFT JOIN FactData fd ON fd.fid = f.fid
    WHERE f.name = "dom_int"
    OR f.name = "dom_str"''')
  domExists = cursor.fetchall()
  domExists =  tools.toAscii_list( domExists )
  ret = {}
  for key, value in parsedResults.iteritems():
    if key == "clock" or key == "crash":
      continue
    for i in value:
      for j in i:
        ret[j] = True
  for i in ret.keys():
    if str(i) in domExists or i == "_":
      continue
    if is_int(i):
      i = int(i)
      rel_name = "dom_int"
    else:
      i = '"' + i + '"'
      rel_name = "dom_str"
    factData = {}
    factData['relationName'] = rel_name
    factData['dataList'] = [i]
    factData["factTimeArg"] = ''
    fid = tools.getIDFromCounters( "fid" )
    Fact.Fact(fid, factData, cursor)
  return ret.keys()

# ruleData = {}
# ruleData['relationName'] = ruleEntry[0]
# ruleData['goalAttList'] = getGoallAtts(cursor, rid)
# ruleData['goalTimeArg'] = ruleEntry[1]
# ruleData['subgoalListOfDicts'] = getSubgoalListOfDicts(cursor, rid)
# ruleData['eqnDict'] = {}

def insertDomainFact(cursor, rule, parsedResults):
  print "*************************************************************"
  print "insertDomainFact called on", rule
  print "*************************************************************"

  cursor.execute("SELECT ga.* From GoalAtt ga LEFT JOIN Rule r ON  r.rid = ga.rid  WHERE r.goalName = '" + rule[1] + "'")
  parGoalAtts = cursor.fetchall()
  if goalData.check_for_id(cursor, 'dom_'+rule[1]+'_0'):
    # in this case  we want to base it on the previous iteration of the goal.
    childRule = goalData.getRuleData(cursor, rule[0])
    parRule = goalData.getRuleData(cursor, rule[1])
    childVars = getAllVarTypes(cursor, childRule[0])
    for subgoal in parRule[0]['subgoalListOfDicts']:
      if subgoal['subgoalName'] == rule[0]:
        for attIndex in range (0, len(subgoal['subgoalAttList'])):
          att = subgoal['subgoalAttList'][attIndex]
          ruleData = {}
          ruleData['relationName'] = 'dom_not_'+rule[0]+'_'+str(attIndex)
          ruleData['goalAttList'] = [att]
          ruleData['goalTimeArg'] = childRule[0]['goalTimeArg']
          ruleData['subgoalListOfDicts'] = []
          ruleData['eqnDict'] = {}

          # add in the adom
          dom_name = "dom_str"
          if childVars[att] == 'int':
            dom_name = "dom_int"

          goalDict = {}
          goalDict['subgoalName'] = dom_name
          goalDict['subgoalAttList'] = [att]
          goalDict['polarity'] = ''
          goalDict['subgoalTimeArg'] = childRule[0]['goalTimeArg']
          ruleData['subgoalListOfDicts'].append(goalDict)
          for parAttIndex in range(0, len(parRule[0]['goalAttList'])):
            parAtt = parRule[0]['goalAttList'][parAttIndex]
            if parAtt == att:
              # in here we define the new rule based on this parent index.
              goalDict = {}
              goalDict['subgoalName'] = 'dom_'+str(parRule[0]['relationName'])+'_'+str(parAttIndex)
              goalDict['subgoalAttList'] = [att]
              goalDict['polarity'] = ''
              goalDict['subgoalTimeArg'] = childRule[0]['goalTimeArg']
              ruleData['subgoalListOfDicts'].append(goalDict)
              print ruleData
              domrid = tools.getIDFromCounters( "rid" )
              newRule = Rule.Rule( domrid, ruleData, cursor )
              done = True
              break

          if done:
            done = False
            continue
          # if we get here we need to some sideways information passing with magic set ish stuff
          # add in the originial rule!
          goalDict = {}
          goalDict['subgoalName'] = childRule[0]['relationName']
          goalDict['subgoalAttList'] = childRule[0]['goalAttList']
          goalDict['polarity'] = 'notin'
          goalDict['subgoalTimeArg'] = childRule[0]['goalTimeArg']
          ruleData['subgoalListOfDicts'].append(goalDict)

          for index in range(0, len(childRule[0]['goalAttList'])):
            if index == attIndex:
              continue
            goalDict = {}
            goalDict['subgoalName'] = 'dom_not_' + rule[0] + '_' + str(index)
            goalDict['subgoalAttList'] = [childRule[0]['goalAttList'][index]]
            goalDict['polarity'] = ''
            goalDict['subgoalTimeArg'] = childRule[0]['goalTimeArg']
            ruleData['subgoalListOfDicts'].append(goalDict)
          print ruleData
          domrid = tools.getIDFromCounters( "rid" )
          newRule = Rule.Rule( domrid, ruleData, cursor )
    return
  # ---------------------------------------------------------------------------------
  # This section is for when we do not have the parent calling function domain. Therefore
  # we must determine the domain based on the parsed results.
  # ---------------------------------------------------------------------------------
  # grab all subgoalAttributes
  subGoals = goalData.getSubgoalListOfDicts(cursor, parGoalAtts[0][0])
  for subgoal in subGoals:
    if subgoal['subgoalName'] != rule[0]:
      continue
    for i in range (0,len(subgoal['subgoalAttList'])):
      if i >= len(parsedResults[rule[1]][0]):
        break
      for val in parsedResults[rule[1]]:
        for i in range(0, len(val)):
          if not is_int(val[i]):
            val[i] = '"' + val[i] + '"'
        factData = {}
        factData['relationName'] = 'dom_not_'+rule[0]+'_'+str(i)
        factData['dataList'] = val
        factData["factTimeArg"] = ''
        fid = tools.getIDFromCounters( "fid" )
        Fact.Fact(fid, factData, cursor)
  # ---------------------------------------------------------------------------------
  print "-----------------------------------------------------------"


def concateDomain(cursor, negRule):
  vars = getAllVars(cursor, negRule)
  for var in vars:
    if var == "_" or var == "NRESERVED":
      continue
    if var[1] == 'int':
      rel_name = "dom_int"
    else:
      rel_name = "dom_str"
    goalDict = {}
    goalDict['subgoalName'] = rel_name
    goalDict['subgoalAttList'] = [var[0]]
    goalDict['polarity'] = ''
    goalDict['subgoalTimeArg'] = ''
    negRule['subgoalListOfDicts'].append(goalDict)
  negRule = appendDomainArgs(negRule)
  return negRule

def appendDomainArgs(negRule):
  ruleName = negRule['relationName']
  for i in  range (0, len(negRule['goalAttList'])):
    domainDict = {}
    domainDict['subgoalName'] = 'dom_'+ruleName+'_'+str(i)
    domainDict['subgoalAttList'] = [negRule['goalAttList'][i]]
    domainDict['polarity'] = ''
    domainDict['subgoalTimeArg'] = ''
    negRule['subgoalListOfDicts'].append(domainDict)
  return negRule

def getAllVars(cursor, rule):
  return getAllVarTypes(cursor, rule).iteritems()

def getAllVarTypes(cursor, rule):
  vars = {}
  for subgoal in rule['subgoalListOfDicts']:
    for att in subgoal['subgoalAttList']:
      cursor.execute('''
        SELECT
          sga.attName,
          sga.attType
        FROM Subgoals sg
        LEFT JOIN Rule r ON sg.rid = r.rid
        LEFT JOIN SubgoalAtt sga ON sga.rid = sg.rid
          AND sga.sid = sg.sid
        WHERE
          sga.attName = "''' + att + '"' + '''
          AND sg.subgoalName = "''' + subgoal['subgoalName'] + '"')
      atts = cursor.fetchall()
      for a in atts:
        if a[1] != "UNDEFINEDTYPE":
          vars[a[0]] = a[1]
  return vars

def is_int(x):
  ''' Returns true if x is an int '''
  try:
    int(x)
    return True
  except:
    return False