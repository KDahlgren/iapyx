#/usr/bin/env python

# based on https://github.com/KDahlgren/pyLDFI/blob/master/src/wrappers/c4/C4Wrapper.py

#############
#  IMPORTS  #
#############
# standard python packages
import ConfigParser
import errno, logging, inspect, os, string, sys, time
from ctypes import *
from types  import *

# ------------------------------------------------------ #
# import sibling packages HERE!!!
if not os.path.abspath( __file__ + "/../.." ) in sys.path :
  sys.path.append( os.path.abspath( __file__ + "/../.." ) )

from utils import tools
# ------------------------------------------------------ #


class C4Wrapper( object ) :

  ##########
  #  INIT  #
  ##########
  def __init__( self, argDict ) :

    self.argDict = argDict

    # get the lib file
    dylib_path = os.path.abspath( __file__ + '/../../../lib/c4/build/src/libc4/libc4.dylib' )
    so_path    = os.path.abspath( __file__ + '/../../../lib/c4/build/src/libc4/libc4.so' )

    if os.path.exists( dylib_path ) :
      c4_lib_loc                     = dylib_path
    elif os.path.exists( so_path ) :
      c4_lib_loc                     = so_path
    else :
      raise Exception( "Files not found: '" + dylib_path + "' or '" + so_path + "'. C4Wrapper died. aborting." )

    self.lib                       = cdll.LoadLibrary( c4_lib_loc )
    self.lib.c4_make.restype       = POINTER(c_char)
    self.lib.c4_dump_table.restype = c_char_p   # c4_dump_table returns a char*


  #########################
  #  GET INPUT PROG FILE  #
  #########################
  def getInputProg_file( self, filename ) :
    if DEBUG :
      logging.debug( "Importing program from " + filename )

    try :
      program = []
      fo = open( filename, "r" )
      for line in fo :
        line = line.rstrip()
        program.append( line )
      fo.close()

      return "".join( program )

    except IOError :
      logging.error( "Could not open file " + filename )
      return None


  ########################################################################################
  #  GET INPUT PROG ONE GROUP FOR EVERYTHING BESIDES CLOCKS AND GROUP CLOCKS BY SNDTIME  #
  ########################################################################################
  # this is what molly does.
  def getInputProg_one_group_for_everything_besides_clocks_and_group_clocks_by_sndTime( self, program ) :

    nonClock             = []
    clockStatementGroups = [] # list of strings grouping clock statements by SndTime
    currClockList        = ""
    currTime             = 1

    # ---------------------------------------------------------------------- #
    # only works if clock facts are sorted by increasing SndTime when 
    # appearing in the input c4 line list.
    # also only works if simulations start at time 1.
    for i in range(0 ,len(program)) :

      statement = program[i]
      nextStatement = None
      lastClock     = False

      parsedStatement = statement.split( "(" )

      # ---------------------------------------------------------------------- #
      # CASE : hit a clock fact
      if parsedStatement[0] == "clock" :

        # ---------------------------------------------------------------------- #
        # check if the next statement in the program also declares a clock fact
        try :
          nextStatement    = program[ i+1 ]
          parsedStatement1 = nextStatement.split( "(" )
          assert( parsedStatement1[0] == "clock" )
        except :
          lastClock = True

        parsedClockArgs = parsedStatement[1].split( "," ) # split clock fact arguments into a list

        # ---------------------------------------------------------------------- #
        # check if SndTime is in the current group
        if not lastClock and int( parsedClockArgs[2] ) == currTime :
          currClockList += statement

        # ---------------------------------------------------------------------- #
        # hit a clock fact in the next time group
        elif not lastClock and int( parsedClockArgs[2] ) > currTime :
          clockStatementGroups.append( currClockList ) # save the old clock group
          currClockList  = ""                          # reset the clock group
          currClockList += statement                   # reset the clock group
          currTime       = int( parsedClockArgs[2] )   # reset the curr time

        # ---------------------------------------------------------------------- #
        # hit a clock fact in the next time group and last clock true
        elif lastClock and int( parsedClockArgs[2] ) > currTime :
          clockStatementGroups.append( currClockList ) # save the old clock group
          currClockList  = ""                          # reset the clock group
          currClockList += statement                   # reset the clock group
          currTime       = int( parsedClockArgs[2] )   # reset the curr time
          clockStatementGroups.append( currClockList ) # save the old clock group

        # ---------------------------------------------------------------------- #
        # hit a clock fact in the last time group
        elif lastClock :
          currClockList += statement
          clockStatementGroups.append( currClockList ) # save the old clock group

      # ---------------------------------------------------------------------- #
      # CASE : hit a non clock fact
      else :
        nonClock.append( statement )

    finalProg    = []
    nonClock_str = "".join( nonClock )

    finalProg.append( nonClock_str )          # add all non-clock clock statements
    finalProg.extend( clockStatementGroups )  # add clock statements

    return finalProg


  ##############
  #  RUN PURE  #
  ##############
  # fullprog is a string of concatenated overlog commands.
  def run_pure( self, allProgramData ) :

    allProgramLines = allProgramData[0] # := list of every code line in the generated C4 program.
    tableList       = allProgramData[1] # := list of all tables in generated C4 program.

    # get full program
    fullprog = "".join( allProgramLines )

    # ----------------------------------------- #

    # initialize c4 instance
    self.lib.c4_initialize()
    self.c4_obj = self.lib.c4_make( None, 0 )

    # ---------------------------------------- #
    # load program
    logging.debug( "... loading prog ..." )

    logging.debug( "SUBMITTING SUBPROG : " )
    logging.debug( fullprog )
    c_prog = bytes( fullprog )
    self.lib.c4_install_str( self.c4_obj, c_prog )

    # ---------------------------------------- #
    # dump program results to file
    logging.debug( "... dumping program ..." )

    results_array = self.saveC4Results_toArray( tableList )

    # ---------------------------------------- #
    # close c4 program
    logging.debug( "... closing C4 ..." )

    self.lib.c4_destroy( self.c4_obj )
    self.lib.c4_terminate( )

    try :
      C4_HOME_PATH = tools.getConfig( self.argDict[ "settings" ], "DEFAULT", "C4_HOME_PATH", str )
      try :
        # for safety:
        C4_HOME_PATH = C4_HOME_PATH.replace( "/c4_home", "" )
        C4_HOME_PATH = C4_HOME_PATH.replace( "//", "" )

        assert( os.path.isdir( C4_HOME_PATH ) == True )
        os.system( "rm -rf " + C4_HOME_PATH + "/c4_home/*" )

      except AssertionError :
        raise AssertionError( C4_HOME_PATH + " does not exist." )

    except ConfigParser.NoOptionError as e :
      logging.info( "  FATAL ERROR : option 'C4_HOME_PATH' not set in settings file '" + self.argDict[ "settings" ] + "'. aborting." )
      raise e

    return results_array


  #########
  #  RUN  #
  #########
  # fullprog is a string of concatenated overlog commands.
  def run( self, allProgramData ) :

    allProgramLines = allProgramData[0] # := list of every code line in the generated C4 program.
    tableList       = allProgramData[1] # := list of all tables in generated C4 program.

    # get full program
    fullprog = self.getInputProg_one_group_for_everything_besides_clocks_and_group_clocks_by_sndTime( allProgramLines )

    # ----------------------------------------- #
    # outputs are good

    logging.debug( "PRINTING RAW INPUT PROG" )
    for x in fullprog :
      logging.debug( x )

    logging.debug( "PRINTING LEGIBLE INPUT PROG" )
    for line in fullprog :
      line = line.split( ";" )
      for statement in line :
        statement = statement.rstrip()
        if not statement == "" :
          statement = statement + ";"
          logging.debug( statement )

    if os.path.isdir( self.argDict[ "data_save_path" ] ) :
      filename = self.argDict[ "data_save_path" ] + "/full_program.olg"
      logging.debug( "SAVING TO FILE at path : " + filename )
      fo = open( filename, "w" )
      for line in fullprog :
        line = line.split( ";" )
        for statement in line :
          statement = statement.rstrip()
          if not statement == "" :
            statement = statement + ";"
            fo.write( statement + "\n" )
      fo.close()

    # ----------------------------------------- #
    # initialize c4 instance

    self.lib.c4_initialize()
    self.c4_obj = self.lib.c4_make( None, 0 )

    # ---------------------------------------- #
    # load program

    logging.debug( "... loading prog ..." )

    for subprog in fullprog :
      logging.debug( "SUBMITTING SUBPROG : " )
      logging.debug( subprog )
      c_prog = bytes( subprog )
      logging.debug( "...completed bytes conversion..." )
      self.lib.c4_install_str( self.c4_obj, c_prog )
      logging.debug( "...done installing str." )

    # ---------------------------------------- #
    # dump program results to file

    logging.debug( "... dumping program ..." )

    results_array = self.saveC4Results_toArray( tableList )

    # ---------------------------------------- #
    # close c4 program

    logging.debug( "... closing C4 ..." )

    self.lib.c4_destroy( self.c4_obj )
    self.lib.c4_terminate( )

    try : 
      C4_HOME_PATH = tools.getConfig( self.argDict[ "settings" ], "DEFAULT", "C4_HOME_PATH", str )
      try :
        # for safety:
        C4_HOME_PATH = C4_HOME_PATH.replace( "/c4_home", "" )
        C4_HOME_PATH = C4_HOME_PATH.replace( "//", "" )

        assert( os.path.isdir( C4_HOME_PATH ) == True )
        os.system( "rm -rf " + C4_HOME_PATH + "/c4_home/*" )

      except AssertionError :
        raise AssertionError( C4_HOME_PATH + " does not exist." )
        
    except ConfigParser.NoOptionError as e :
      logging.info( "  FATAL ERROR : option 'C4_HOME_PATH' not set in settings file '" + self.argDict[ "settings" ] + "'. aborting." )
      raise e

    return results_array


  ##############################
  #  SAVE C4 RESULTS TO ARRAY  #
  ##############################
  # save c4 results to array
  def saveC4Results_toArray( self, tableList ) :

    # save new contents
    results_array = []

    for table in tableList :

      # output to stdout
      logging.debug( "---------------------------" )
      logging.debug( table )
      logging.debug( self.lib.c4_dump_table( self.c4_obj, table ) )

      # save in array
      results_array.append( "---------------------------" )
      results_array.append( table )

      table_results_str   = self.lib.c4_dump_table( self.c4_obj, table )
      table_results_array = table_results_str.split( '\n' )
      results_array.extend( table_results_array[:-1] ) # don't add the last empty space

    return results_array


#########################
#  THREAD OF EXECUTION  #
#########################
if __name__ == '__main__' :

  logging.debug( "[ Executing C4 wrapper ]" )
  w = C4Wrapper( ) # initializes c4

  # /////////////////////////////////// #
  rf = open( "./myTest.olg", "r" )
  prog1 = []
  for line in rf :
    line = line.rstrip()
    prog1.append( line )
  rf.close()

  rf = open( "./tableListStr_myTest.data", "r" )
  table_str1 = rf.readline()
  table_str1 = table_str1.rstrip()
  table_str1 = table_str1.split( "," )

  for line in  w.run( [ prog1, table_str1 ] ) :
    print line


#########
#  EOF  #
#########
