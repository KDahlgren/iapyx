#!/usr/bin/env python

# **************************************** #

#############
#  IMPORTS  #
#############
# standard python packages
import logging, inspect, os, sys

# ------------------------------------------------------ #
# import sibling packages HERE!!!
if not os.path.abspath( __file__ + "/../.." ) in sys.path :
  sys.path.append( os.path.abspath( __file__ + "/../.." ) )

from utils    import tools
from wrappers import C4Wrapper

# **************************************** #


C4_EXEC_PATH = os.path.dirname(os.path.abspath( __file__ )) + "/../../lib/c4/build/src/c4i/c4i"

#####################
#  CLEAN TABLE STR  #
#####################
def cleanTableStr( tableStr ) :

  tableStr = tableStr.split( "," )
  arr = []
  for i in tableStr :
    if not i in arr :
      arr.append( i )
  newStr = ",".join( arr )

  return newStr


################
#  GET TABLES  #
################
# assumes table names are listed in a single string and delimited by one comma only; no spaces.
def getTables( table_path ) :
  tableListStr = ""

  # safety first
  if os.path.exists( table_path ) :
    fo = open( table_path, "r" )
    tableListStr = fo.readline()
    fo.close()
  else :
    sys.exit( "Table list for C4 Overlog input file for pyLDFI program not found at : " + table_path + "\nAborting..." )

  return tableListStr


############
#  RUN C4  #
############
# runs c4 on generated overlog program
# by passing the overlog program to c4 at the command line
# posts the results to standard out while capturing in a file for future processing.
def runC4_directly( c4_file_path, table_path, savepath ) :

  logging.debug( "USING C4 DIRECTLY..." )
  logging.debug( "c4_file_path = " + c4_file_path )
  logging.debug( "table_path   = " + table_path )
  logging.debug( "savepath     = " + savepath )

  # check if executable and input file exist
  if os.path.exists( C4_EXEC_PATH ) :
    if os.path.exists( c4_file_path ) :
      tableListStr = getTables( table_path )

      logging.debug( "tableListStr = " + tableListStr )
      logging.debug( "savepath     = " + savepath )

      # run the program using the modified c4 executable installed during the pyLDFI setup process.
      os.system( C4_EXEC_PATH + " " + c4_file_path + ' "' + tableListStr + '" "' + savepath + '"' )

      # check if dump file is empty.
      if not os.path.exists( savepath ) :
        tools.bp( __name__, inspect.stack()[0][3], "ERROR: c4 file dump does not exist at " + savepath )
      else :
        if not os.path.getsize( savepath ) > 0 :
          tools.bp( __name__, inspect.stack()[0][3], "ERROR: no c4 dump results at " + savepath  )

      return savepath

    else :
      sys.exit( "C4 Overlog input file for pyLDFI program not found at : " + c4_file_path + "\nAborting..." )

  else :
    sys.exit( "C4 executable not found at : " + C4_EXEC_PATH + "\nAborting..." )


####################
#  RUN C4 WRAPPER  #
####################
# runs c4 program on generated overlog program
# by interacting with a C4 wrapper.
# saves the evaluation results to file at c4_results_dump_path.
def runC4_wrapper( allProgramData, argDict ) :

  logging.debug( "USING C4 WRAPPER..." )
  logging.debug( "allProgramLines = " + str( allProgramData[0] ) )
  logging.debug( "tableListArray  = " + str( allProgramData[1] ) )

  # branch on empty generated programs
  if len( allProgramData[0] ) > 1 :

    # branch on empty generated table list arrays
    if allProgramData[1] and not allProgramData[1] == "" :

      # run the program using the c4 wrapper
      w             = C4Wrapper.C4Wrapper( argDict ) # initializes c4 wrapper instance
      results_array = w.run( allProgramData )

      # return c4 evaluation results as an array of strings
      #print "FROM runC4_wrapper : results_array :"
      #print results_array
      return results_array

    else :
      tools.bp( __name__, inspect.stack()[0][3], "FATAL ERROR : generated empty C4 Overlog table list. Aborting..." )

  else :
    tools.bp( __name__, inspect.stack()[0][3], "FATAL ERROR : generated empty C4 Overlog program. Aborting..." )


#########
#  EOF  #
#########
