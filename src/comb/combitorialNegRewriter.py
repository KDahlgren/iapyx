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

from utils       import dumpers, extractors, globalCounters, tools, setTypes
from translators import c4_translator, dumpers_c4
from dedt        import Rule, Fact
from evaluators  import c4_evaluator

import domain
from negate import  negateRule

def neg_rewrite(cursor):
  ''' Performs the negative rewrite of the dedalus program. '''
  original_prog = c4_translator.c4datalog( cursor )
  for section in original_prog:
    for line in section:
      print line
  results_array = c4_evaluator.runC4_wrapper( original_prog )
  parsedResults = tools.getEvalResults_dict_c4( results_array )
  print parsedResults
  while True:
    print "running"
    original_prog = c4_translator.c4datalog( cursor )
    print "----------------------------------------------------------------"
    print "Program"
    print "----------------------------------------------------------------"
    for line in original_prog[0]:
      print line
    for line in original_prog[1]:
      print line
    print "----------------------------------------------------------------"
    results_array = c4_evaluator.runC4_wrapper( original_prog )

    # run the program to get the new domains.
    # TODO: make this unnecessary, can be done if we just take in the 
    # original inputs maybe even better
    rulesToNegate = findNegativeRules(cursor, parsedResults)
    rulesToNegateList = rulesToNegate.keys()

    # if there are no rules to negate, exit
    if len(rulesToNegateList) == 0:
      break

    # add in active domain facts, this should only be done once in reality.
    dom = domain.getActiveDomain(cursor, parsedResults)

    # Negate the rules in the list
    negateRules(cursor, rulesToNegate, parsedResults)
    setTypes.setTypes( cursor )

  # #####
  # THIS IS TESTING CODE REMOVE IT
  # #####
  print "----------------------------------------------------------------"
  print "done"
  print "----------------------------------------------------------------"
  original_prog = c4_translator.c4datalog( cursor )
  results_array = c4_evaluator.runC4_wrapper( original_prog )
  parsedResults = tools.getEvalResults_dict_c4( results_array )
  print parsedResults

def findNegativeRules(cursor, parsedResults):
  ''' finds all the rules with a 'notin' '''

  #grab all ruleids in the program
  cursor.execute("SELECT rid, goalName FROM Rule")
  ridList = cursor.fetchall()

  rulesToNegate = {}
  for rule in ridList:
    if rule[1].startswith('dom'):
      continue
    # fetch all subgoals for a given rule.
    cursor.execute('''SELECT s.sid, s.subgoalName, s.subgoalPolarity
      FROM Rule subgoalRule
      LEFT JOIN SubGoals s ON subgoalRule.goalName = s.subgoalName
      LEFT JOIN Rule r ON s.rid = r.rid
      WHERE r.goalName = "''' + rule[1] + '"')
    SubGoals = cursor.fetchall()

    # loop through all subgoals
    for subGoal in SubGoals:
      if subGoal[2] == 'notin':
        # if the polarity is negative, add it to the list of goals to
        # flip
        rulesToNegate[str(subGoal[1])] = rule[1]

  return rulesToNegate

def negateRules(cursor, rulesToNegate, parsedResults):
  ''' Negates all rules '''
  for rule in rulesToNegate.iteritems():
    # for each rule, negate it.
    negateRule(cursor, rule, parsedResults)