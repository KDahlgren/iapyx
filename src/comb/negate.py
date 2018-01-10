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

def negateRule(cursor, rule, parsedResults):
  ''' 
    Takes in a list of rules that all correspond to the same rule,
    performs a form of demorgans in which each negated version of the rule
    is performed and then they are anded together
  '''
  print "***"
  print "Negating", rule
  print "***"

  cursor.execute("select * from Rule where goalName='" + rule[0] + "'")
  f = cursor.fetchone()
  ruleData = goalData.getRuleData(cursor, rule[0])
  if (ruleData is None) or len(ruleData) == 0:
    return []
  domain.insertDomainFact(cursor, rule, parsedResults)
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
    # append the domain information
    negRule = domain.concateDomain(cursor, negRule)
    #insert new rule
    neg_rid = tools.getIDFromCounters( "rid" )
    newRule = Rule.Rule( neg_rid, negRule, cursor )
    # update goalAtts
    goalData.update_goalAtts(cursor, rule, neg_rid)
  print "***"

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
  cursor.execute('''
          UPDATE Subgoals
          SET
            subgoalName = "''' + new_name + '''",
            subgoalPolarity = ''
          WHERE
            rid IN (SELECT rid FROM Rule WHERE goalName NOT LIKE "dom%")
            AND subgoalName = "''' + old_name + '''"
            AND subgoalPolarity = 'notin'
    ''')

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
    if goalData.check_for_rule_id(cursor, neg_name):
      rule['subgoalListOfDicts'][slot]['subgoalName'] = neg_name
    else:
      rule['subgoalListOfDicts'][slot]['polarity'] = 'notin'
    negate_rules[name] = rule['relationName']
  return rule