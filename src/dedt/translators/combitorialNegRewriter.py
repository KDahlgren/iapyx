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

from utils       import dumpers, extractors, globalCounters, tools, parseCommandLineInput
from translators import c4_translator, dumpers_c4
from dedt        import Rule, Fact
from evaluators  import c4_evaluator

domSubGoals = []

def getDomain(cursor, parsedResults):
  cursor.execute('''
    SELECT fd.data 
    FROM Fact f
    LEFT JOIN FactData fd ON fd.fid = f.fid
    WHERE f.name = "dom"''')
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
    if str(i) in domExists:
      continue
    factData = {}
    factData['relationName'] = 'dom'
    factData['dataList'] = i
    factData["factTimeArg"] = ''
    fid = tools.getIDFromCounters( "fid" )
    Fact.Fact(fid, factData, cursor)
  return ret.keys()

def neg_rewrite(cursor):
  # collect information for domain stuff
  while True:
    original_prog = c4_translator.c4datalog( cursor )
    results_array = c4_evaluator.runC4_wrapper( original_prog )
    parsedResults = tools.getEvalResults_dict_c4( results_array )
    print "running"
    print parsedResults
    #grab all ruleids
    cursor.execute("SELECT rid, goalName FROM Rule")
    ridList = cursor.fetchall()

    rulesToNegate = {}
    for rule in ridList:
      # fetch all subgoals for a given rule.
      cursor.execute('''SELECT s.sid, s.subgoalName, s.subgoalPolarity
        FROM Rule subgoalRule
        LEFT JOIN SubGoals s ON subgoalRule.goalName = s.subgoalName
        LEFT JOIN Rule r ON s.rid = r.rid
        WHERE r.goalName = "''' + rule[1] + '"')
      SubGoals = cursor.fetchall()
      for subGoal in SubGoals:
        if subGoal[2] == 'notin':
          rulesToNegate[str(subGoal[1])] = rule[1]
    rulesToNegateList = rulesToNegate.keys()
    if len(rulesToNegateList) == 0:
      break
    dom = getDomain(cursor, parsedResults)
    negateRules(cursor, rulesToNegate, parsedResults)

  original_prog = c4_translator.c4datalog( cursor )
  results_array = c4_evaluator.runC4_wrapper( original_prog )
  parsedResults = tools.getEvalResults_dict_c4( results_array )
  print "done"
  print parsedResults

def negateRules(cursor, rulesToNegate, parsedResults):
  ''' Negates all rules '''
  for rule in rulesToNegate.iteritems():
    negRules = negateRule(cursor, rule, parsedResults)

def appendDomainArgs(negRule):
  return negRule

def insertDomainFact(cursor, rule, parsedResults):
  if rule[1] in parsedResults.keys():
    # grab parent rule attributes
    cursor.execute("SELECT ga.* From GoalAtt ga LEFT JOIN Rule r ON  r.rid = ga.rid  WHERE r.goalName = '" + rule[1] + "'")
    parGoalAtts = cursor.fetchall()
    # grab all subgoalAttributes
    subGoals = getSubgoalListOfDicts(cursor, parGoalAtts[0][0])
    for subgoal in subGoals:
      if subgoal['subgoalName'] != rule[0]:
        continue
      for i in range (0,len(subgoal['subgoalAttList'])):
        if i >= len(parsedResults[rule[1]][0]):
          break
        for val in parsedResults[rule[1]]:
          factData = {}
          factData['relationName'] = 'dom_'+rule[0]+'_'+str(i)
          factData['dataList'] = val
          factData["factTimeArg"] = ''
          fid = tools.getIDFromCounters( "fid" )
          Fact.Fact(fid, factData, cursor)

def getRuleData(cursor, rule):
  ''' Collects all rule data for a given goalName '''
  cursor.execute("SELECT goalName, goalTimeArg, rid FROM Rule WHERE goalName = '" + rule + "'")
  ruleEntrys = cursor.fetchall()
  rules = []
  for ruleEntry in ruleEntrys:
    if ruleEntry is None:
      # case where the rule wasnt a rule but is a fact
      return
    rid = ruleEntry[2]
    ruleData = {}
    ruleData['relationName'] = ruleEntry[0]
    ruleData['goalAttList'] = getGoallAtts(cursor, rid)
    ruleData['goalTimeArg'] = ruleEntry[1]
    ruleData['subgoalListOfDicts'] = getSubgoalListOfDicts(cursor, rid)
    ruleData['eqnDict'] = {}
    rules.append(ruleData)
  return rules

def update_goalAtts(cursor, rule, neg_rid):
  # grab all goalAtts in the given rule
  cursor.execute(
    '''SELECT ga.attName,
      ga.attType,
      ga.rid
    FROM GoalAtt ga
    LEFT JOIN Rule r
    WHERE r.goalName = "''' + str(rule) + '"')
  goalAtts = cursor.fetchall()
  # make a dict of goalAtt name  to type.
  goalAtt = {}
  for att in goalAtts:
    if att[1] == 'UNDEFINEDTYPE':
      continue
    goalAtt[att[0]] = att[1]
  cursor.execute("SELECT ga.attName, ga.attType FROM GoalAtt ga WHERE ga.rid = '" + str(neg_rid) + "'")
  neg_atts =  cursor.fetchall()
  for neg_att in neg_atts:
    if neg_att[0] not in goalAtt.keys():
      continue
    cursor.execute('''
      UPDATE goalAtt
      SET attType = '%s'
      WHERE attName = '%s'
      AND rid = '%s'
      ''' %(goalAtt[neg_att[0]], neg_att[0], neg_rid))

def getGoallAtts(cursor, rid):
  ''' collects goalAtts '''
  cursor.execute(
    '''SELECT ga.attName,
      ga.attType
    FROM GoalAtt ga
    WHERE ga.rid = "''' + rid + '"')
  goalAtt = cursor.fetchall()
  return tools.toAscii_list( goalAtt )

def getSubgoalListOfDicts(cursor, rid):
  ''' Collects information for the sugboalListofDicts '''
  cursor.execute('''
    SELECT s.sid, s.subgoalName, s.subgoalPolarity, s.subgoalTimeArg
    FROM Subgoals s
    WHERE s.rid = "''' + str(rid) + '"')
  subgoalList = cursor.fetchall()

  subgoalListOfDicts = []
  for subgoal in subgoalList:
    goalDict = {}
    goalDict['subgoalName'] = subgoal[1]
    goalDict['subgoalAttList'] = getSubGoalAttList(cursor, rid, subgoal[0])
    goalDict['polarity'] = subgoal[2]
    goalDict['subgoalTimeArg'] = subgoal[3]
    subgoalListOfDicts.append(goalDict)
  return subgoalListOfDicts

def getSubGoalAttList(cursor, rid, sid):
  ''' Collects infomration to create the subgoalAttList '''
  cursor.execute('''
    SELECT sa.attName
    FROM SubgoalAtt sa
    WHERE sa.rid = "''' + rid + '" AND sid = "' + str(sid) + '"')
  subGoalAtts = cursor.fetchall()
  return tools.toAscii_list( subGoalAtts )

def negateRule(cursor, rule, parsedResults):
  ''' 
    Takes in a list of rules that all correspond to the same rule,
    performs a form of demorgans in which each negated version of the rule
    is performed and then they are anded together
  '''
  ruleData = getRuleData(cursor, rule[0])
  if (ruleData is None) or len(ruleData) == 0:
    return []
  insertDomainFact(cursor, rule, parsedResults)
  rule = rule[0]
  negated_pieces = []
  old_name = ruleData[0]['relationName']
  new_name = 'not_' + ruleData[0]['relationName']
  for piece in ruleData:
    piece['relationName'] = new_name
    numGoals = len(piece['subgoalListOfDicts'])
    numRules = pow(2, numGoals)
    rules = []
    for i in range (1, numRules):
      for j in range (0, numRules):
        power = pow(2, j)
        if i%power == 0:
          piece = flip_negation(cursor, piece, j, parsedResults)
      rules.append(copy.deepcopy(piece))
    negated_pieces.append(rules)
  negated_pieces = concate_neg_rules(negated_pieces)
  replaceAllNotins(cursor, old_name, new_name)
  for negRule in negated_pieces:
      negRule = concateDomain(negRule)
      # append domain args
      negRule = appendDomainArgs(negRule)
      #insert new rule
      neg_rid = tools.getIDFromCounters( "rid" )
      newRule = Rule.Rule( neg_rid, negRule, cursor )
      # update goalAtts
      update_goalAtts(cursor, rule, neg_rid)

def concateDomain(negRule):
  vars = getAllVars(negRule)
  for var in vars:
    goalDict = {}
    goalDict['subgoalName'] = 'dom'
    goalDict['subgoalAttList'] = [var]
    goalDict['polarity'] = ''
    goalDict['subgoalTimeArg'] = ''
    negRule['subgoalListOfDicts'].append(goalDict)
  return negRule

def getAllVars(rule):
  vars = []
  vars += rule['goalAttList']
  for subgoal in rule['subgoalListOfDicts']:
    vars += subgoal['subgoalAttList']
  return dict((item, True) for item in vars).keys()

def concate_neg_rules(neg_rules):
  ''' Loops through all the negated rules and concatinates them together, performs the and '''
  if len(neg_rules) == 1:
    return neg_rules[0]
  rules = []
  # match each rule with every other rule
  for i in range(0, len(neg_rules)):
    for j in range(0, len(neg_rules)):
      # if they are the same rule skip it
      if i == j:
        break
      for neg_rule in neg_rules[i]:
        # loop through each version of the given rule
        subgoals = neg_rule['subgoalListOfDicts']
        for second_neg_rule in neg_rules[j]:
          # concatinate with each negated version of every other rule
          new_neg_rule = copy.deepcopy(neg_rule)
          new_neg_rule['subgoalListOfDicts'] = subgoals + second_neg_rule['subgoalListOfDicts']
          rules.append(new_neg_rule)
  return rules

def replaceAllNotins(cursor, old_name, new_name):
  ''' Looks for all notins of a given name and replaces them with not_rule'''
  cursor.execute('''UPDATE Subgoals SET
            subgoalName = '%s',
            subgoalPolarity = ''
          WHERE
            subgoalName = '%s'
            AND subgoalPolarity = 'notin'
    ''' %(new_name, old_name))

def flip_negation(cursor, rule, slot,parsedResults):
  ''' 
    Flips a given slot in the subgoal list from negative to positive
    or positive to negative.
  '''
  name  = rule["subgoalListOfDicts"][slot]['subgoalName']
  negate_rules = {}
  if rule['subgoalListOfDicts'][slot]['polarity'] == 'notin':
    # if it was negated, change it to positive
    rule['subgoalListOfDicts'][slot]['polarity'] = ''
  elif rule['subgoalListOfDicts'][slot]['subgoalName'].startswith('not_'):
    # if it was not_ then it was negated, change it to positive
    rule['subgoalListOfDicts'][slot]['polarity'].replace('not_', '')
  else:
    # change it to notin since it was a positive goal. TODO: add it to the
    # inverting rules lists
    neg_name = 'not_' + name
    if check_for_id(cursor, neg_name):
      rule['subgoalListOfDicts'][slot]['subgoalName'] = neg_name
    else:
      rule['subgoalListOfDicts'][slot]['polarity'] = 'notin'
    negate_rules[name] = rule['relationName']
  return rule

def check_for_id(cursor, neg_name):
  '''
    Checks to see if the negated goalName exists in the db.
  '''
  cursor.execute("SELECT * FROM Rule WHERE goalName = '" + neg_name + "'")
  rule = cursor.fetchone()
  return rule != None