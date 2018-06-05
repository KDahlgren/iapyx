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

def saveRule(rule):
  rule.saveToRule()
  rule.saveToGoalAtt()
  rule.saveSubgoals()
  rule.saveEquations()
  return rule

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

def check_for_rule_id(cursor, neg_name):
  '''
    Checks to see if the negated goalName exists in the db.
  '''
  cursor.execute("SELECT * FROM Rule WHERE goalName = '" + neg_name + "'")
  rule = cursor.fetchone()
  return rule != None


####################
#  CHECK FOR NAME  #
####################
def check_for_name(relationName, ruleMeta, factMeta):

  '''
    Checks to see if the negated goalName exists in the db.
  '''

  for rule in ruleMeta:
    if rule.relationName == relationName:
      return True

  for fact in factMeta:
    if fact.relationName == relationName:
      return True

  return False


#########
#  EOF  #
#########
