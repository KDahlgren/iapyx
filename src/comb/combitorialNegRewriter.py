import inspect, logging, os, string, sqlite3, sys
import copy
import ConfigParser

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
import dm

def neg_rewrite(cursor, argDict, settings_path, ruleMeta, factMeta, parsedResults):
  ''' Performs the negative rewrite of the dedalus program. '''

  # use the aggregate rewrite from the dm module, avoids issues with
  # aggregate rules.

  # determine if we are negating clocks
  logging.debug("COMBO-REWRITE: Begin Combinatorial Rewrite...")
  NEGATE_CLOCKS=True
  try:
    NEGATE_CLOCKS = tools.getConfig( settings_path, "DEFAULT", "NEGATE_CLOCKS", bool )
  except ConfigParser.NoOptionError:
    logging.warning("WARNING : no 'NEGAGTE_CLOCKS' defined in 'DEFAULT' section of settings file ... running with NEGAGTE_CLOCKS=True")

  ruleMeta = dm.aggRewrites( ruleMeta, settings_path )

  # add in active domain facts, this should only be done once in reality.
  factMeta = domain.getActiveDomain(cursor, factMeta, parsedResults)
  setTypes.setTypes( cursor, settings_path )

  while True:
    rulesToNegate = findNegativeRules(cursor, ruleMeta)
    rulesToNegateList = rulesToNegate.keys()

    # if there are no rules to negate, exit
    if len(rulesToNegateList) == 0:
      break

    # Negate the rules in the list
    ruleMeta, factMeta = negateRules(cursor, argDict, settings_path,  ruleMeta, factMeta, rulesToNegate, parsedResults, neg_clocks=NEGATE_CLOCKS)

  logging.debug("COMBO-REWRITE: Ending Combinatorial Rewrite.")
  return ruleMeta, factMeta


def findNegativeRules(cursor, ruleMeta):
  ''' finds all the rules with a 'notin' '''
  rulesToNegate = {}
  for rule in ruleMeta:
    if rule.relationName.startswith('dom') or rule.relationName.startswith('not'):
      continue
    for subgoal in rule.subgoalListOfDicts:
      if subgoal['polarity'] == 'notin':
        if isRule(ruleMeta, subgoal['subgoalName']):
          rulesToNegate[subgoal['subgoalName']] = rule.relationName
  return rulesToNegate

def isRule(ruleMeta, ruleName):
  for rule in ruleMeta:
    if rule.relationName == ruleName:
      return True
  return False

def negateRules(cursor, argDict, settings_path, ruleMeta, factMeta, rulesToNegate, parsedResults, neg_clocks=True):
  ''' Negates all rules '''
  for rule in rulesToNegate.iteritems():
    # for each rule, negate it.
    ruleMeta, factMeta = negateRule(cursor, rule, ruleMeta, factMeta, parsedResults, neg_clocks=neg_clocks)
    original_prog = c4_translator.c4datalog( argDict, cursor )
    setTypes.setTypes( cursor, settings_path )

  return ruleMeta, factMeta