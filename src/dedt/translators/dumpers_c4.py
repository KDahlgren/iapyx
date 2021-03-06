#!/usr/bin/env python

'''
dumpers_c4.py
   Methods for dumping specific contents from the database.
'''

import logging, inspect, os, string, sys

# ------------------------------------------------------ #
# import sibling packages HERE!!!
if not os.path.abspath( __file__ + "/../.." ) in sys.path :
  sys.path.append( os.path.abspath( __file__ + "/../.." ) )

from utils import tools, dumpers
# ------------------------------------------------------ #


#############
#  DUMP IR  #
#############
# dump the contents of an entire IR database
def dumpIR( cursor, db_dump_save_path ) :

  # get facts
  cursor.execute( "SELECT fid FROM Fact" )
  fid_all = cursor.fetchall()
  fid_all = tools.toAscii_list( fid_all )

  full_facts = []
  for fid in fid_all :
    full_facts.append( dumpSingleFact_c4( fid, cursor ) )

  # get rules
  cursor.execute( "SELECT rid FROM Rule" )
  rid_all = cursor.fetchall()
  rid_all = tools.toAscii_list( rid_all )

  full_rules = []
  for rid in rid_all :
    full_rules.append( dumpSingleRule_c4( rid, cursor ) )

  # get clock
  full_clock = dump_clock( cursor )

  if db_dump_save_path :
    logging.debug( "...DUMPING IR...\n" + str( full_facts ) + "\n" + str( full_rules ) + "\n" + str( full_clock ) )

    # save to file
    fo = open( db_dump_save_path, "w" )
    for fact in full_facts : # write facts
      fo.write( fact )
    for rule in full_rules : # write rules
      fo.write( rule )
    for clock in full_clock : # write clock facts
      fo.write( clock )
    fo.close()

    print "IR DUMP SAVED TO : " + db_dump_save_path

  else :
    print "...DUMPING IR..."
    print full_facts
    print full_rules
    print full_clock


#########################
#  DUMP SINGLE FACT C4  #
########################
# input fid and IR db cursor
# output a single fact

def dumpSingleFact_c4( fid, cursor ) :
  fact = ""

  cursor.execute( "SELECT name FROM Fact WHERE fid == '" + fid + "'" ) # get fact name
  factName    = cursor.fetchone()
  factName    = tools.toAscii_str( factName )

  # get list of attribs in fact
  factList    = cursor.execute( "SELECT data FROM FactData WHERE fid == '" + fid + "'" ) # list of fact atts
  factList    = cursor.fetchall()
  factList    = tools.toAscii_list( factList )

  # get fact time arg
  #factTimeArg = ""
  #cursor.execute( "SELECT timeArg FROM Fact WHERE fid == '" + fid + "'" )
  #factTimeArg = cursor.fetchone()
  #factTimeArg = tools.toAscii_str( factTimeArg )

  # convert fact info to pretty string
  fact += factName + "("
  for j in range(0,len(factList)) :
    if j < (len(factList) - 1) :
      fact += factList[j] + ","
    else :
      fact += factList[j]
  #if not factTimeArg == "" :
  #  fact += "," + factTimeArg

  fact += ");" + "\n" # end all facts with a semicolon

  return fact


#########################
#  DUMP SINGLE RULE C4  #
#########################
# input rid and IR db cursor
# output a single rule

def dumpSingleRule_c4( rid, cursor ) :

  rule = ""

  # -------------------------------------------------------------- #
  #                           GOAL                                 #

  # get goal name
  cursor.execute( "SELECT goalName FROM Rule WHERE rid == '" + rid + "'" ) # get goal name
  goalName    = cursor.fetchone()
  goalName    = tools.toAscii_str( goalName )

  # get list of attribs in goal
  goalList    = cursor.execute( "SELECT attName FROM GoalAtt WHERE rid == '" + rid + "'" )# list of goal atts
  goalList    = cursor.fetchall()
  goalList    = tools.toAscii_list( goalList )

  # get goal time arg
  goalTimeArg = ""
  cursor.execute( "SELECT goalTimeArg FROM Rule WHERE rid == '" + rid + "'" )
  goalTimeArg = cursor.fetchone()
  goalTimeArg = tools.toAscii_str( goalTimeArg )

  # convert goal info to pretty string
  rule += goalName + "("
  for j in range(0,len(goalList)) :
    if j < (len(goalList) - 1) :
      rule += goalList[j] + ","
    else :
      rule += goalList[j] + ")"
  #KD
  if not goalTimeArg == "" :
    rule += "@" + goalTimeArg + " :- "
    #sys.exit( "ERROR: leftover timeArg in goal: " + rule + "@" + goalTimeArg )
  else :
    rule += " :- "

  # --------------------------------------------------------------- #
  #                         SUBGOALS                                #

  # get list of sids for the subgoals of this rule
  cursor.execute( "SELECT sid FROM Subgoals WHERE rid == '" + str(rid) + "'" ) # get list of sids for this rule
  subIDs = cursor.fetchall()
  subIDs = tools.toAscii_list( subIDs )

  # prioritize dom subgoals first.
  subIDs = prioritizeDoms( rid, subIDs, cursor )

  # prioritize negated subgoals last.
  #subIDs = prioritizeNegatedLast( rid, subIDs, cursor )
  subIDs, clockSubIDs, negSubIDs = prioritizeNegatedLast_2( rid, subIDs, cursor )

  subTimeArg = None
  # iterate over subgoal ids
  for k in range(0,len(subIDs)) :
    newSubgoal = ""

    s = subIDs[k]

    # get subgoal name
    cursor.execute( "SELECT subgoalName FROM Subgoals WHERE rid == '" + str(rid) + "' AND sid == '" + str(s) + "'" )
    subgoalName = cursor.fetchone()

    if not subgoalName == None :
      subgoalName = tools.toAscii_str( subgoalName )

      logging.debug( "subgoalName = " + subgoalName )


      # get subgoal attribute list
      subAtts = cursor.execute( "SELECT attName FROM SubgoalAtt WHERE rid == '" + rid + "' AND sid == '" + s + "'" )
      subAtts = cursor.fetchall()
      subAtts = tools.toAscii_list( subAtts )

      # get subgoal time arg
      cursor.execute( "SELECT subgoalTimeArg FROM Subgoals WHERE rid == '" + rid + "' AND sid == '" + s + "'" )
      subTimeArg = cursor.fetchone() # assume only one time arg
      subTimeArg = tools.toAscii_str( subTimeArg )

      # get subgoal polarity
      cursor.execute( "SELECT subgoalPolarity FROM Subgoals WHERE rid == '" + rid + "' AND sid == '" + s + "'" )
      subPolarity  = cursor.fetchone() # assume only one additional arg
      subPolarity  = tools.toAscii_str( subPolarity )
      if subPolarity == "notin" :
        subPolarity += " "
      newSubgoal  += subPolarity

      # all subgoals have a name and open paren
      newSubgoal += subgoalName + "("

      # add in all attributes
      for j in range(0,len(subAtts)) :

        currAtt = subAtts[j]

        # replace SndTime in subgoal with subTimeArg, if applicable
        if not subTimeArg == "" and "SndTime" in currAtt :
          currAtt = str( subTimeArg )

        if j < (len(subAtts) - 1) :
          newSubgoal += currAtt + ","
        else :
          newSubgoal += currAtt + ")"

      # cap with a comma, if applicable
      if k < len( subIDs ) - 1 :
        newSubgoal += ","

    rule += newSubgoal

  # cap with comma
  if len( subIDs ) > 0 :
    rule += ","

  # --------------------------------------------------------------- #
  #                         EQUATIONS                               #

  # get list of sids for the subgoals of this rule
  cursor.execute( "SELECT eid FROM Equation" ) # get list of eids for this rule
  eqnIDs = cursor.fetchall()
  eqnIDs = tools.toAscii_list( eqnIDs )

#  if   len( subIDs )      > 0 and \
#     ( len( eqnIDs )      > 0 or \
#       len( clockSubIDs ) > 0 or \
#       len( negSubIDs )   > 0 ):
#    rule += ","

  for e in range(0,len(eqnIDs)) :
    currEqnID = eqnIDs[e]
   
    # get associated equation
    if not currEqnID == None :
      cursor.execute( "SELECT eqn FROM Equation WHERE rid == '" + rid + "' AND eid == '" + str(currEqnID) + "'" )
      eqn = cursor.fetchone()
      if not eqn == None :
        eqn = tools.toAscii_str( eqn )

        # convert eqn info to pretty string
        rule += "," + str(eqn)

#  if len( eqnIDs ) > 0 and len( clockSubIDs ) > 0 :
#    rule += ","

  # add SndTime eqn (only works for one subgoal time annotation)
  #if not subTimeArg == None and not subTimeArg == "" :
  #  rule += ",SndTime==" + str( subTimeArg )

  # cap with comma
  if len( eqnIDs ) > 0 :
    rule += ","

  # --------------------------------------------------------------- #

  if len( clockSubIDs ) > 0 :
  
    subTimeArg = None
    # iterate over subgoal ids
    for k in range(0,len(clockSubIDs)) :
      newSubgoal = ""
  
      s = clockSubIDs[k]
  
      # get subgoal name
      cursor.execute( "SELECT subgoalName \
                       FROM   Subgoals \
                       WHERE rid == '" + str(rid) + "' AND \
                             sid == '" + str(s) + "'" )
      subgoalName = cursor.fetchone()
  
      if not subgoalName == None :
        subgoalName = tools.toAscii_str( subgoalName )
  
        logging.debug( "subgoalName = " + subgoalName )
  
  
        # get subgoal attribute list
        subAtts = cursor.execute( "SELECT attName \
                                   FROM   SubgoalAtt \
                                   WHERE rid == '" + rid + "' AND \
                                         sid == '" + s + "'" )
        subAtts = cursor.fetchall()
        subAtts = tools.toAscii_list( subAtts )
  
        # get subgoal time arg
        cursor.execute( "SELECT subgoalTimeArg \
                         FROM   Subgoals \
                         WHERE rid == '" + rid + "' AND \
                               sid == '" + s + "'" )
        subTimeArg = cursor.fetchone() # assume only one time arg
        subTimeArg = tools.toAscii_str( subTimeArg )
  
        # get subgoal polarity
        cursor.execute( "SELECT subgoalPolarity \
                         FROM   Subgoals \
                         WHERE rid == '" + rid + "' AND \
                               sid == '" + s + "'" )
        subPolarity  = cursor.fetchone() # assume only one additional arg
        subPolarity  = tools.toAscii_str( subPolarity )
        subPolarity += " "
        newSubgoal  += subPolarity
  
        # all subgoals have a name and open paren
        newSubgoal += subgoalName + "("
  
        # add in all attributes
        for j in range(0,len(subAtts)) :
  
          currAtt = subAtts[j]
  
          # replace SndTime in subgoal with subTimeArg, if applicable
          if not subTimeArg == "" and "SndTime" in currAtt :
            currAtt = str( subTimeArg )
  
          if j < (len(subAtts) - 1) :
            newSubgoal += currAtt + ","
          else :
            newSubgoal += currAtt + ")"
  
        # cap with a comma, if applicable
        if k < len( clockSubIDs ) - 1 :
          newSubgoal += ","
  
      rule += newSubgoal

  #if len( clockSubIDs ) > 0 and len( negSubIDs ) > 0 :
  #  rule += ","

  # cap with comma
  if len( clockSubIDs ) > 0 :
    rule += ","

  # --------------------------------------------------------------- #

  if len( negSubIDs ) > 0 :
  
    subTimeArg = None
    # iterate over subgoal ids
    for k in range(0,len(negSubIDs)) :
      newSubgoal = ""
  
      s = negSubIDs[k]
  
      # get subgoal name
      cursor.execute( "SELECT subgoalName \
                       FROM   Subgoals \
                       WHERE rid == '" + str(rid) + "' AND \
                             sid == '" + str(s) + "'" )
      subgoalName = cursor.fetchone()
  
      if not subgoalName == None :
        subgoalName = tools.toAscii_str( subgoalName )
  
        logging.debug( "subgoalName = " + subgoalName )
  
  
        # get subgoal attribute list
        subAtts = cursor.execute( "SELECT attName \
                                   FROM   SubgoalAtt \
                                   WHERE rid == '" + rid + "' AND \
                                         sid == '" + s + "'" )
        subAtts = cursor.fetchall()
        subAtts = tools.toAscii_list( subAtts )
  
        # get subgoal time arg
        cursor.execute( "SELECT subgoalTimeArg \
                         FROM   Subgoals \
                         WHERE rid == '" + rid + "' AND \
                               sid == '" + s + "'" )
        subTimeArg = cursor.fetchone() # assume only one time arg
        subTimeArg = tools.toAscii_str( subTimeArg )
  
        # get subgoal polarity
        cursor.execute( "SELECT subgoalPolarity \
                         FROM   Subgoals \
                         WHERE rid == '" + rid + "' AND \
                               sid == '" + s + "'" )
        subPolarity  = cursor.fetchone() # assume only one additional arg
        subPolarity  = tools.toAscii_str( subPolarity )
        subPolarity += " "
        newSubgoal  += subPolarity
  
        # all subgoals have a name and open paren
        newSubgoal += subgoalName + "("
  
        # add in all attributes
        for j in range(0,len(subAtts)) :
  
          currAtt = subAtts[j]
  
          # replace SndTime in subgoal with subTimeArg, if applicable
          if not subTimeArg == "" and "SndTime" in currAtt :
            currAtt = str( subTimeArg )
  
          if j < (len(subAtts) - 1) :
            newSubgoal += currAtt + ","
          else :
            newSubgoal += currAtt + ")"
  
        # cap with a comma, if applicable
        if k < len( negSubIDs ) - 1 :
          newSubgoal += ","
  
      rule += newSubgoal

  # --------------------------------------------------------------- #

  if rule.endswith( "," ) :
    rule = rule[:-1]

  rule += " ;" + "\n" # end all rules with a semicolon
  rule = rule.replace( " ,", "" )
  rule = rule.replace( ",,", "," )
  rule = rule.translate( None, string.whitespace )
  rule = rule.replace( ",;", ";" )
  rule = rule.replace( "notin", "notin " )

  logging.debug( "  >>> rule = " + rule )

  return rule


###############################
#  PRIORITIZE NEGATED LAST 2  #
###############################
def prioritizeNegatedLast_2( rid, subIDs, cursor ) :

  posSubs   = []
  clockSubs = []
  negSubs   = []

  # check if subgoal is negated
  # branch on result.
  for subID in subIDs :

    cursor.execute( "SELECT subgoalName,subgoalPolarity \
                     FROM   Subgoals \
                     WHERE rid=='" + rid + "' AND \
                           sid=='" + subID + "'" )
    data = cursor.fetchall()
    data = tools.toAscii_multiList( data )
    name = data[0][0]
    sign = data[0][1]

    if name == "clock" :
      clockSubs.append( subID )
    elif not sign == "notin" :
      posSubs.append( subID )
    else :
      negSubs.append( subID )

  return posSubs, clockSubs, negSubs


#############################
#  PRIORITIZE NEGATED LAST  #
#############################
def prioritizeNegatedLast( rid, subIDs, cursor ) :

  posSubs = []
  negSubs = []

  # check if subgoal is negated
  # branch on result.
  for subID in subIDs :

    cursor.execute( "SELECT subgoalPolarity FROM Subgoals WHERE rid=='" + rid + "' AND sid=='" + subID + "'" )
    sign = cursor.fetchone()

    # positive subgoals may have no argName data
    # all instances of negative subgoals WILL have an argName
    if sign :
      sign = tools.toAscii_str( sign )
    else :
      sign = ""

    if not sign == "notin" :
      posSubs.append( subID )
    else :
      negSubs.append( subID )

  return posSubs + negSubs


#####################
#  PRIORITIZE DOMS  #
#####################
# order domain subgoals first
def prioritizeDoms( rid, subIDs, cursor ) :

  domSubs           = []
  nonDomSubs        = []

  # check if subgoal is a domain subgoal
  # branch on result.
  for subID in subIDs :

    cursor.execute( "SELECT subgoalName FROM Subgoals WHERE rid=='" + rid + "' AND sid=='" + subID + "'" )
    subgoalName = cursor.fetchone()
    subgoalName = tools.toAscii_str( subgoalName )

    if subgoalName.startswith( "dom_" )     or \
       subgoalName.startswith( "domcomp_" ) or \
       subgoalName.startswith( "unidom_" )  or \
       subgoalName.startswith( "exidom_" ) :
      domSubs.append( subID )
    else :
      nonDomSubs.append( subID )

  return domSubs + nonDomSubs


################
#  DUMP CLOCK  #
################
# dump and format all clock facts in c4 overlog
def dump_clock( cursor ) :

  logging.debug( "...running dumpers_c4 dump_clock..." )

  formattedClockFactsList = []

  #cursor.execute( "SELECT * FROM Clock" )
  cursor.execute( "SELECT src, dest, sndTime, delivTime FROM Clock" )
  clockFacts = cursor.fetchall()
  clockFacts = tools.toAscii_multiList( clockFacts )

  logging.debug( "dump_clock: clockFacts = " + str(clockFacts) )

  for c in clockFacts :
    logging.debug( "c = " + str(c) )

    clockF = 'clock('
    for i in range(0,len(c)) :
      currData = c[i]
      if i < 2 :
        clockF += '"' + currData + '",'
      else :
        clockF += str(currData)
        if i < len(c)-1 :
          clockF += ","
    clockF += ");" + "\n" # all clock facts end with a semicolon
    formattedClockFactsList.append( clockF )

  return formattedClockFactsList


################
#  DUMP CRASH  #
################
# dump and format all clock facts in c4 overlog
def dump_crash( cursor ) :

  logging.debug( "...running dumpers_c4 dump_crash..." )

  formattedCrashFactsList = []

  cursor.execute( "SELECT src, dest, sndTime, NRESERVED FROM Crash" )
  crashFacts = cursor.fetchall()
  crashFacts = tools.toAscii_multiList( crashFacts )

  if len( crashFacts ) < 1 :
    #tools.bp( __name__, inspect.stack()[0][3], "FATAL ERROR : crash table is empty." )
    cursor.execute( "INSERT INTO Crash (src,dest,sndTime,NRESERVED) VALUES ('NULL','NULL','99999999','99999999')" )
    cursor.execute( "SELECT src,dest,sndTime,NRESERVED FROM Crash" )
    crashFacts = cursor.fetchall()
    crashFacts = tools.toAscii_multiList( crashFacts )
    logging.debug( "crashFacts = " + str(crashFacts) )

  logging.debug( "dump_crash: crashFacts = " + str(crashFacts) )

  for c in crashFacts :
    logging.debug( "c = " + str(c) )

    crashF = 'crash('
    for i in range(0,len(c)) :
      currData = c[i]
      if i < 2 :
        crashF += '"' + currData + '",'
      else :
        crashF += str(currData)
        if i < len(c)-1 :
          crashF += ","
    crashF += ");" + "\n" # all crash facts end with a semicolon
    formattedCrashFactsList.append( crashF )

  return formattedCrashFactsList


#########
#  EOF  #
######### 
