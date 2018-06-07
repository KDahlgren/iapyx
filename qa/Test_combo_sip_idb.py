#!/usr/bin/env python
  
'''
Test_dm.py
'''

#############
#  IMPORTS  #
#############
# standard python packages
import inspect, logging, os, string, sqlite3, sys, unittest

# ------------------------------------------------------ #
# import sibling packages HERE!!!
if not os.path.abspath( __file__ + "/../../src" ) in sys.path :
  sys.path.append( os.path.abspath( __file__ + "/../../src" ) )

from dedt       import dedt, dedalusParser, Fact, Rule, clockRelation, dedalusRewriter
from utils      import dumpers, globalCounters, tools
from evaluators import c4_evaluator

import dm
import dm_tools

# ------------------------------------------------------ #


##############
#  TEST DM  #
##############
class Test_dm( unittest.TestCase ) :

  logging.basicConfig( format='%(levelname)s:%(message)s', level=logging.DEBUG )
  #logging.basicConfig( format='%(levelname)s:%(message)s', level=logging.INFO )
  #logging.basicConfig( format='%(levelname)s:%(message)s', level=logging.WARNING )

  PRINT_STOP = True

  MOLLY_RUNS = True
  COMBO_RUNS = True
  DM_RUNS    = False


  ###############
  #  PATH LINK  #
  ###############
  def test_path_link( self ) :

    MOLLY_EVAL = False
    COMBO_EVAL = False
    DM_EVAL    = True

    # --------------------------------------------------------------- #

    if self.MOLLY_RUNS :
      test_id        = "path_link"
      test_file_name = "path_link"

      print " >>> RUNNING " + test_id + " <<<"

      test_id                     = "combo_sip_idb_" + "path_link"
      input_file                  = "./molly_progs/" + test_file_name + ".olg"
      argDict                     = self.getArgDict( input_file )
      argDict[ 'data_save_path' ] = "./data/" + test_id + "/"

      eval_molly = self.run_workflow( test_id, argDict, input_file, "molly", MOLLY_EVAL )

    # --------------------------------------------------------------- #

    if self.COMBO_RUNS :
      test_id        = "path_link_combo_sip_idb"
      test_file_name = "path_link"

      print " >>> RUNNING " + test_id + " <<<"

      input_file                  = "./dedalus_drivers/" + test_file_name + ".ded"
      argDict                     = self.getArgDict( input_file )
      argDict[ 'data_save_path' ] = "./data/" + test_id + "/"
      argDict[ 'EOT' ]            = 6
      argDict[ 'nodes' ]          = [ "a", "b", "c" ]
      argDict[ 'settings' ]       = "settings_files/settings_combo_sip_idb.ini"
      argDict[ 'neg_writes' ]     = "combo"

      eval_combo = self.run_workflow( test_id, argDict, input_file, "combo", COMBO_EVAL )

    # --------------------------------------------------------------- #

    if self.DM_RUNS :
      test_id        = "path_link_dm_huge"
      test_file_name = "path_link"

      print " >>> RUNNING " + test_id + " <<<"

      input_file                  = "./dedalus_drivers/" + test_file_name + ".ded"
      argDict                     = self.getArgDict( input_file )
      argDict[ 'data_save_path' ] = "./data/" + test_id + "/"
      argDict[ 'EOT' ]            = 6
      argDict[ 'nodes' ]          = [ "a", "b", "c" ]
      argDict[ 'neg_writes' ]     = "dm"
      argDict[ 'settings' ]       = "settings_files/settings_dm_huge.ini"

      eval_dm = self.run_workflow( test_id, argDict, input_file, "dm", DM_EVAL )

    if self.MOLLY_RUNS and self.DM_RUNS and MOLLY_EVAL and DM_EVAL and COMBO_EVAL :
      self.check_results_alignment( eval_molly, eval_dm, eval_combo )


  #############################
  #  CHECK RESULTS ALIGNMENT  #
  #############################
  def check_results_alignment( self, eval_molly, eval_dm, eval_combo ) :

#    print
#    print "MOLLY:"
#    for i in eval_molly[ "post" ] :
#      print i
#    print
#    print "DM:"
#    for i in eval_dm[ "post" ] :
#      print i
#    print
#    print "COMBO:"
#    for i in eval_combo[ "post" ] :
#      print i
#    #sys.exit( "blah" )

    print
    print "<><><><><><><><><><><><><><><><><><>"
    print "<>   CHECKING TUPLE ALIGNMENTS    <>"

    if len( eval_molly ) < 1 :
      print "skipping eval comparison b/c no molly results."
      return

    if len( eval_dm ) > 0 :
      # check dm
      logging.debug( "ooooooooooooooooooooooooooooooooooooooooooooooo" )
      logging.debug( "  checking results for dm v. molly:" )
      for rel in eval_molly :
        if "_prov" in rel :
          continue
        else :

          # check for extra molly tups
          extra_molly_tups = []
          for molly_tup in eval_molly[ rel ] :
            if not molly_tup in eval_dm[ rel ] :
              extra_molly_tups.append( molly_tup )

          # check for extra dm tups
          extra_dm_tups = []
          for dm_tup in eval_dm[ rel ] :
            if not dm_tup in eval_molly[ rel ] :
              extra_dm_tups.append( dm_tup )

          if len( extra_molly_tups ) > 0 or len( extra_dm_tups ) > 0 :
            print ">>>> alignment inconsistencies for relation '" + rel + "' :"

          if len( extra_molly_tups ) > 0 :
            print "> tuples found in molly and not in dm for relation '" + rel.upper() + " :"
            for tup in extra_molly_tups :
              print ",".join( tup )
          if len( extra_dm_tups ) > 0 :
            print "> tuples found in dm and not in molly for relation '" + rel.upper() + " :"
            for tup in extra_dm_tups :
              print ",".join( tup )
          if len( extra_molly_tups ) > 0 or len( extra_dm_tups ) > 0 :
            print "<<<<"
    else :
      print "skipping dm comparison b/c no eval results..."

    if len( eval_combo ) > 0 :
      # combo check
      logging.debug( "ooooooooooooooooooooooooooooooooooooooooooooooo" )
      logging.debug( "  checking results for combo v. molly:" )
      for rel in eval_molly :
        if "_prov" in rel :
          continue
        else :

          # check for extra molly tups
          extra_molly_tups = []
          for molly_tup in eval_molly[ rel ] :
            if not molly_tup in eval_combo[ rel ] :
              extra_molly_tups.append( molly_tup )

          # check for extra combo tups
          extra_combo_tups = []
          for combo_tup in eval_combo[ rel ] :
            if not combo_tup in eval_molly[ rel ] :
              extra_combo_tups.append( combo_tup )

          if len( extra_molly_tups ) > 0 or len( extra_combo_tups ) > 0 :
            print ">>>> alignment inconsistencies for relation '" + rel + "' :"

          if len( extra_molly_tups ) > 0 :
            print "> tuples found in molly and not in combo for relation '" + rel.upper() + " :"
            for tup in extra_molly_tups :
              print ",".join( tup )
          if len( extra_combo_tups ) > 0 :
            print "> tuples found in combo and not in molly for relation '" + rel.upper() + " :"
            for tup in extra_combo_tups :
              print ",".join( tup )
          if len( extra_molly_tups ) > 0 or len( extra_combo_tups ) > 0 :
            print "<<<<"
    else :
      print "skipping combo comparison b/c no eval results..."

      print
      print "<><><><><><><><><><><><><><><><><><>"

  ##################
  #  RUN WORKFLOW  #
  ##################
  # generate program (if applicable), run dm program, collect results, analyze results.
  def run_workflow( self, test_id, argDict, input_file, eval_type, RUN_EVAL=True ) :

    # --------------------------------------------------------------- #

    # check if dedalus
    if input_file.endswith( ".ded" ) :
      IS_DED = True
    elif input_file.endswith( ".olg" ) :
      IS_DED = False
    else :
      raise Exception( "INVALID FILE TYPE : make sure the input file is either .ded or .olg" )

    # --------------------------------------------------------------- #

    # make sure data dir exists
    if not os.path.exists( argDict[ "data_save_path" ] ) :
      self.make_data_dir( argDict[ "data_save_path" ], test_id )

    # --------------------------------------------------------------- #

    if not IS_DED :

      # extract program string
      program    = self.extract_program_array( input_file )
      table_list = self.extract_table_list( program )

      program_data = [ program, table_list ]

      # run program with c4 wrapper
      if RUN_EVAL :
        eval_results_dict = self.run_program_c4( program_data, argDict )
      else :
        eval_results_dict = []

    # --------------------------------------------------------------- #

    else :

      # --------------------------------------------------------------- #
      # set up IR data

      test_db = argDict[ "data_save_path" ] + "/IR_" + test_id + ".db"

      if os.path.exists( test_db ) :
        os.remove( test_db )

      IRDB   = sqlite3.connect( test_db )
      cursor = IRDB.cursor()

      dedt.createDedalusIRTables(cursor)
      dedt.globalCounterReset()

      # --------------------------------------------------------------- #

      # run translator
      # grab only the program lines and table list.
      program_data = dedt.translateDedalus( argDict, cursor )[0]

      # run program in c4
      if RUN_EVAL :
        eval_results_dict = self.run_program_c4( program_data, argDict )
      else :
        eval_results_dict = []

    # --------------------------------------------------------------- #

    # run analysis
    analysis_results_dict = self.run_analysis( program_data, eval_results_dict, IS_DED )

    print
    print "======================================"
    print "========== ANALYSIS RESULTS for " + eval_type + " =========="
    print
    for res in analysis_results_dict :
      print res + " => " + str( analysis_results_dict[ res ] )
    print
    print "======================================"
    print

    # --------------------------------------------------------------- #

    # save analysis data to file
    self.save_analysis_data_to_file( analysis_results_dict, test_id, argDict )

    return eval_results_dict


  ################################
  #  SAVE ANALYSIS DATA TO FILE  #
  ################################
  def save_analysis_data_to_file( self, analysis_results_dict, test_id, argDict ) :

    save_file_name = argDict[ "data_save_path" ] + \
                     "/" + test_id + "_analysis_results.txt"

    fo = open( save_file_name, "w" )
    for metric in analysis_results_dict :
      fo.write( metric + "=>" + str( analysis_results_dict[ metric ] ) + "\n" )
    fo.close()


  ##################
  #  RUN ANALYSIS  #
  ##################
  def run_analysis( self, program_data, eval_results_dict, IS_DED ) :

    # --------------------------------------------------------------- #
    # gather data about the programs

    analysis_results_dict = {}
    program_lines         = program_data[0]
    program_tables        = program_data[1]

    analysis_results_dict[ "num_lines_total" ]    = len( program_lines )
    analysis_results_dict[ "num_tables_total" ]   = len( program_tables )
    analysis_results_dict[ "num_idb_rules" ]      = len( [ x for x in program_lines \
                                                             if ":-" in x ] )
    analysis_results_dict[ "num_edb_statements" ] = len( [ x for x in program_lines \
                                                     if not x.startswith( "define(") and \
                                                        not ":-" in x ] )

    subgoal_data = pat.get_subgoal_per_rule_data( program_lines )
    analysis_results_dict[ "avg_num_subgoals_per_rule" ] = subgoal_data[0]
    analysis_results_dict[ "max_num_subgoals_per_rule" ] = subgoal_data[1]
    analysis_results_dict[ "min_num_subgoals_per_rule" ] = subgoal_data[2]

    if len( eval_results_dict ) > 0 :
      assert( len( program_data[1] ) == len( eval_results_dict ) )

    # --------------------------------------------------------------- #
    # gather dm-specific data
    # observe all ded programs run through this process are programs
    # generated via dm or combo.

    if IS_DED :

      analysis_results_dict[ "num_dom_rules" ]     = pat.get_num_rules( program_lines, "dom_" )
      analysis_results_dict[ "num_domcomp_rules" ] = pat.get_num_rules( program_lines, "domcomp_" )
      analysis_results_dict[ "num_dom_rules" ]     = pat.get_num_rules( program_lines, "dom_" )
      analysis_results_dict[ "num_adom_rules" ]    = pat.get_num_rules( program_lines, "adom_" )

    # --------------------------------------------------------------- #
    # gather data about the evaluation results

    if len( eval_results_dict ) > 0 :
      eval_meta_data = pat.get_eval_meta_data( eval_results_dict )
      analysis_results_dict[ "eval_tups_total" ]              = eval_meta_data[0]
      analysis_results_dict[ "eval_tups_total_per_relation" ] = eval_meta_data[1]

    return analysis_results_dict

  ##################
  #  GET ARG DICT  #
  ##################
  def getArgDict( self, inputfile ) :
    argDict = {}
    argDict[ 'file' ]       = inputfile
    argDict[ 'evaluator' ]  = "c4"
    argDict[ 'neg_writes' ] = ""

    # this settings file is fine for running both the dm and molly progs
    # b/c c4 only needs the C4_HOME_PATH option.
    argDict[ 'settings' ] = "./settings_files/settings_program_complexity.ini"

    return argDict


  ####################
  #  RUN PROGRAM C4  #
  ####################
  # return evaluation results dictionary.
  def run_program_c4( self, program_data, argDict ) :

    # run c4 evaluation
    results_array = c4_evaluator.runC4_wrapper( program_data, argDict )
    parsedResults = tools.getEvalResults_dict_c4( results_array )

    return parsedResults


  ########################
  #  EXTRACT TABLE LIST  #
  ########################
  def extract_table_list( self, program_array ) :
    table_list = []
    for line in program_array :
      if not line.startswith( "define(" ) :
        break
      else :
        line        = line.replace( "define(", "" )
        comma_index = line.find( "," )
        table_name  = line[ : comma_index ]
        table_list.append( table_name )
    return table_list


  ###########################
  #  EXTRACT PROGRAM ARRAY  #
  ###########################
  def extract_program_array( self, input_olg_file ) :

    if os.path.exists( input_olg_file ) :
      program_array = []
      fo = open( input_olg_file )
      for line in fo :
        program_array.append( line.rstrip() )
      fo.close()
      return program_array

    else :
      raise Exception( "FILE NOT FOUND : " + input_olg_file )


  ###################
  #  MAKE DATA DIR  #
  ###################
  def make_data_dir( self, data_save_path, test_id ) :
    logging.debug( "  TEST " + test_id.upper() + \
                   " : data save path not found : " + \
                   data_save_path )

    dir_list = data_save_path.split( "/" )
    complete_str = "./"
    for this_dir in dir_list :
      if this_dir == "./" :
        complete_str += this_dir
      else :
        complete_str += this_dir + "/"
        if not os.path.exists( complete_str ) :
          cmd = "mkdir " + complete_str
          logging.debug( "  TEST " + test_id.upper() + " : running cmd = " + cmd )
          os.system( cmd )



##############################
#  MAIN THREAD OF EXECUTION  #
##############################
if __name__ == "__main__" :
  if os.path.exists( "./IR*.db*" ) :
    logging.debug( "removing all ./IR*.db* files." )
    os.remove( "./IR*.db*" )
  unittest.main()
  if os.path.exists( "./IR*.db*" ) :
    logging.debug( "removing all ./IR*.db* files." )
    os.remove( "./IR*.db*" )

#########
#  EOF  #
#########
