#!/usr/bin/env python

'''
clockRelation.py
   Define the functionality for creating clock relations.
'''

import inspect, logging, os, sys
import ConfigParser

# ------------------------------------------------------ #
# import sibling packages HERE!!!
if not os.path.abspath( __file__ + "/../.." ) in sys.path :
  sys.path.append( os.path.abspath( __file__ + "/../.." ) )

from utils import dumpers, parseCommandLineInput, tools
# ------------------------------------------------------ #


#########################
#  INIT CLOCK RELATION  #
#########################
# input IR database cursor and cmdline input
# create initial clock relation
# output nothing
def initClockRelation( cursor, argDict ) :

  COMM_MODEL = tools.getConfig( argDict[ "settings" ], "DEDT", "COMM_MODEL", str )

  # ------------------------------------------------------ #
  # grab the next rule handling method

  try :
    NEXT_RULE_HANDLING = tools.getConfig( argDict[ "settings" ], "DEFAULT", "NEXT_RULE_HANDLING", str )

  except ConfigParser.NoOptionError :
    logging.info( "WARNING : no 'NEXT_RULE_HANDLING' defined in 'DEFAULT' section of settings file." )
    tools.bp( __name__, inspect.stack()[0][3], "FATAL ERROR : NEXT_RULE_HANDLING parameter not specified in DEFAULT section of settings file. use 'USE_AGGS', 'SYNC_ASSUMPTION', or 'USE_NEXT_CLOCK' only." )

  # sanity check next rule handling value
  if NEXT_RULE_HANDLING == "USE_AGGS" or NEXT_RULE_HANDLING == "SYNC_ASSUMPTION" or NEXT_RULE_HANDLING == "USE_NEXT_CLOCK" :
    pass
  else :
    tools.bp( __name__, inspect.stack()[0][3], "FATAL ERROR : unrecognized NEXT_RULE_HANDLING value '" + NEXT_RULE_HANDLING + "'. use 'USE_AGGS', 'SYNC_ASSUMPTION', or 'USE_NEXT_CLOCK' only." )

  # --------------------------------------------------------------------- #

  # check if node topology defined in Fact relation
  nodeFacts = cursor.execute('''SELECT name FROM Fact WHERE Fact.name == "node"''')

  defaultStartSendTime  = '1'
  maxSendTime           = argDict[ "EOT" ]

  # --------------------------------------------------------------------- #
  # prefer cmdline topology
  if argDict[ "nodes" ] :

    logging.debug( "Using node topology from command line: " + str(argDict[ "nodes" ]) )

    nodeSet = argDict[ "nodes" ]

    # synchronous communication model
    if COMM_MODEL == "SYNC" :
      for i in range( int(defaultStartSendTime), int(maxSendTime)+1 ) :
        for n1 in nodeSet :
          for n2 in nodeSet :
            delivTime = str(i + 1)
            #cursor.execute("INSERT OR IGNORE INTO Clock VALUES ('" + n1 + "','" + n2 + "','" + str(i) + "','" + delivTime + "')")
            logging.debug( "INSERT OR IGNORE INTO Clock VALUES ('" + n1 + "','" + n2 + "','" + str(i) + "','" + delivTime + "', 'True')" )
            cursor.execute("INSERT OR IGNORE INTO Clock VALUES ('" + n1 + "','" + n2 + "','" + str(i) + "','" + delivTime + "', 'True')")

            # handle using next_clock relation
            if NEXT_RULE_HANDLING == "USE_NEXT_CLOCK" :
              logging.debug( "INSERT OR IGNORE INTO NextClock VALUES ('" + n1 + "','" + n2 + "','" + str(i) + "','" + delivTime + "', 'True')" )
              cursor.execute("INSERT OR IGNORE INTO NextClock VALUES ('" + n1 + "','" + n2 + "','" + str(i) + "','" + delivTime + "', 'True')")

    # asynchronous communication model
    elif COMM_MODEL == "ASYNC" :
      for i in range( int(defaultStartSendTime), int(maxSendTime)+1 ) :
        for j in range( i, int(maxSendTime)+2 ) :
          for n1 in nodeSet :
            for n2 in nodeSet :
              #cursor.execute("INSERT OR IGNORE INTO Clock VALUES ('" + n1 + "','" + n2 + "','" + str(i) + "','" + delivTime + "')")
              cursor.execute("INSERT OR IGNORE INTO Clock VALUES ('" + n1 + "','" + n2 + "','" + str(i) + "','" + str( j ) + "', 'True')")

              # handle using next_clock relation
              if NEXT_RULE_HANDLING == "USE_NEXT_CLOCK" and j == i + 1 :
                cursor.execute("INSERT OR IGNORE INTO Clock VALUES ('" + n1 + "','" + n2 + "','" + str(i) + "','" + str( j ) + "', 'True')")

    else :
      tools.bp( __name__, inspect.stack()[0][3], "FATAL ERROR : in settings.ini : COMM_MODEL '" + str(COMM_MODEL) + "' not recognized. Aborting." )

  else :
    sys.exit( "ERROR: No node topology specified! Aborting..." )


#########
#  EOF  #
#########
