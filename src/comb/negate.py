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

import domain
import goalData

def negateRule(cursor, rule, ruleMeta, factMeta,  parsedResults, neg_clocks=True):
  ''' 
    Takes in a list of rules that all correspond to the same rule,
    performs a form of demorgans in which each negated version of the rule
    is performed and then they are anded together
  '''
  logging.debug( "COMBO-REWRITE: Negating" + rule[1] + " from "+ rule[0] )

  # Find the parent rule
  parRule = None
  for r in ruleMeta:
    if r.relationName == rule[0]:
      parRule = r
      break

  if parRule is None:
    logging.warning( "COMBO-REWRITE: parent rule " + rule[0] + " not found." )
    return ruleMeta, factMeta

  # insert domain infomration
  ruleMeta, factMeta = domain.insertDomainFact( cursor, rule, ruleMeta, factMeta, parsedResults )

  # Find the rule to be negated
  rule = rule[0]
  ruleData = []
  for r in ruleMeta:
    if r.relationName == rule:
      ruleData.append(r)
  
  if len(ruleData) == 0:
    logging.warning( "COMBO-REWRITE: rule " + rule + " not found." )
    return ruleMeta, factMeta

  old_rid = ruleData[0].rid
  old_name = ruleData[0].relationName
  new_name = 'not_' + ruleData[0].relationName

  negated_pieces = []
  for piece in ruleData:
    neg_piece = copy.deepcopy( piece )

    # remove clock from things to be negated if neg_clocks is false.
    clk = None
    if not neg_clocks:
      for subgoal in neg_piece.subgoalListOfDicts:
        if subgoal['subgoalName'] == 'clock':
          clk = subgoal
          neg_piece.subgoalListOfDicts.remove(clk)

    neg_piece.relationName = new_name
    neg_piece.ruleData['relationName'] = new_name
    numGoals = len(neg_piece.subgoalListOfDicts)
    numRules = pow(2, numGoals)
    rules = []
    for i in range (1, numRules):
      for j in range (0, numRules):
        power = pow(2, j)
        if i%power == 0:
          neg_piece = flip_negation( cursor, neg_piece, j, parsedResults )
      piece = copy.deepcopy( neg_piece )

      # add back in clocks
      if clk:
        piece.subgoalListOfDicts.append( clk )

      rules.append( copy.deepcopy( piece ) )
    negated_pieces.append( rules )
  headRule, negated_pieces = concate_neg_rules( cursor, negated_pieces )

  if headRule != None:
    headRule = goalData.saveRule( headRule )
    ruleMeta.append( headRule )

  for negRule in negated_pieces:
    # append the domain information
    negRule = domain.concateDomain( cursor, negRule, old_rid, new_name )
    #insert new rule
    neg_rid = tools.getIDFromCounters( "rid" )
    negRule.cursor = cursor
    negRule.rid = neg_rid
    negRule = goalData.saveRule( negRule )
    ruleMeta.append( negRule )

  # if there are facts associated with it, adds in a rule to cover things at the time stamp that dont exist.
  ruleMeta, factMeta = addNegFact( cursor, ruleMeta, factMeta, old_name )

  # flips the notin version of the rules to not_
  ruleMeta = replaceAllNotins( cursor, old_name, new_name, ruleMeta )
  logging.debug("COMBO-REWRITE: Negate of " + old_name + " complete...")
  return ruleMeta, factMeta

def addNegFact(cursor, ruleMeta, factMeta, old_name):
  '''
    If there are any facts associated with the rule, sets up a negated rule that covers all things within the 
    domain that are notin the rule and are at the same timestamp. This covers base facts for recursive rules.
  '''
  for fact in factMeta:
    if fact.relationName == old_name:
      atts = []
      for attIndex in range(0, len(fact.dataListWithTypes)-1):
        atts.append("Att"+str(attIndex))
      atts.append(fact.dataListWithTypes[len(fact.dataListWithTypes)-1][0])
      rule = createRuleData("not_"+old_name,"", atts)
      for attIndex in range (0,len(atts)):
        rule = createSubgoal(rule, ["Att"+str(attIndex)], "dom_not_"+old_name+"_"+str(attIndex))
      rule = createSubgoal(rule, atts, old_name, notin="notin")
      rid = tools.getIDFromCounters( "rid" )
      newRule = Rule.Rule( rid, rule, cursor )
      ruleMeta.append(newRule)
      return ruleMeta, factMeta
  return ruleMeta, factMeta

def concate_neg_rules(cursor, neg_rules):
  ''' Loops through all the negated rules and concatinates them together, performs the and '''
  # This is legacy code, changing the fomualtion of this to support a form of multi level aggrigation
  if len(neg_rules) <= 1:
    return None, neg_rules[0]

  rules = []
  # create the head rule that we will add e ach rule too.
  headRuleData = createRuleData( neg_rules[0][0].relationName, '', neg_rules[0][0].goalAttList )
  # match each rule with every other rule
  for i in range(0, len(neg_rules)):
    # first rename each rule to be 'not_{relationName}_{i}'
    for j in range(0, len(neg_rules[i])):
      new_neg_rule = copy.deepcopy(neg_rules[i][j])
      new_neg_rule.relationName = new_neg_rule.relationName + "_" + str(i)
      new_neg_rule.ruleData['relationName'] = new_neg_rule.relationName
      rules.append(new_neg_rule)
    headRuleData = createSubgoal(headRuleData, headRuleData['goalAttList'], new_neg_rule.relationName)

  head_rid = tools.getIDFromCounters( "rid" )
  newRule = Rule.Rule( head_rid, headRuleData, cursor )
  return newRule, rules


def createRuleData(name, timeargs, atts):
  ruleData = {}
  ruleData['relationName'] = name
  ruleData['goalAttList'] = atts
  ruleData['goalTimeArg'] = timeargs
  ruleData['subgoalListOfDicts'] = []
  ruleData['eqnDict'] = {}
  return ruleData


def createSubgoal(rule, goalAttList, subgoalName, notin=""):
  goalDict = {}
  goalDict['subgoalName'] = subgoalName
  goalDict['subgoalAttList'] = goalAttList
  goalDict['polarity'] = notin
  goalDict['subgoalTimeArg'] = ''
  rule['subgoalListOfDicts'].append(goalDict)
  return rule


def replaceAllNotins(cursor, old_name, new_name, ruleMeta):
  ''' Looks for all notins of a given name and replaces them with not_rule'''
  for rule in ruleMeta:
    if rule.relationName.startswith('dom') or rule.relationName == new_name:
      continue
    for subgoal in rule.subgoalListOfDicts:
      if subgoal['subgoalName'] == old_name and subgoal['polarity'] == 'notin':
        subgoal['subgoalName'] = new_name
        subgoal['polarity'] = ''
    goalData.saveRule(rule)
  return ruleMeta

def flip_negation(cursor, rule, slot, parsedResults):
  ''' 
    Flips a given slot in the subgoal list from negative to positive
    or positive to negative.
  '''
  name  = rule.subgoalListOfDicts[slot]['subgoalName']
  negate_rules = {}
  if rule.subgoalListOfDicts[slot]['polarity'] == 'notin':
    # if it was negated, change it to positive
    rule.subgoalListOfDicts[slot]['polarity'] = ''
  elif rule.subgoalListOfDicts[slot]['subgoalName'].startswith('not_'):
    # if it was not_ then it was negated, change it to positive
    rule.subgoalListOfDicts[slot]['polarity'].replace('not_', '')
  else:
    # change it to notin since it was a positive goal. TODO: add it to the
    # inverting rules lists
    neg_name = 'not_' + name
    if goalData.check_for_rule_id(cursor, neg_name):
      rule.subgoalListOfDicts[slot]['subgoalName'] = neg_name
    else:
      rule.subgoalListOfDicts[slot]['polarity'] = 'notin'
    negate_rules[name] = rule.relationName
  return rule