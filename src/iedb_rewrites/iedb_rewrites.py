#/usr/bin/env python

'''
iedb_rewrites.py
   Rewrite relations defined as both idb and edb to avoid ambiguity.

   Example:
     ----------------
      t(X) :- m(X) ;
      t(1) ;
      m(2) ;
     ----------------
   ==>
     ----------------
      t(X) :- m(X) ;
      t(X) :- t_edb(X) ;
      t_edb(1) ;
      m(2) ;
     ----------------
'''

import copy, inspect, logging, os, string, sys

# ------------------------------------------------------ #
# import sibling packages HERE!!!
if not os.path.abspath( __file__ + "/../.." ) in sys.path :
  sys.path.append( os.path.abspath( __file__ + "/../.." ) )

from dedt  import Rule
from utils import tools, dumpers, setTypes

# ------------------------------------------------------ #

#############
#  GLOBALS  #
#############

arithOps = [ "+", "-", "*", "/" ]


###################
#  IEDB REWRITES  #
###################
# generate the new set of rules provided by the DM method for negative rewrites.
# factMeta := a list of Fact objects
# ruleMeta := a list of Rule objects
def iedb_rewrites( factMeta, ruleMeta, cursor, settings_path ) :

  logging.debug( "  IEDB REWRITES : running process..." )

  # ----------------------------------------- #
  # generate a dictionary mapping
  # relation names to lists of fact ids.

  cursor.execute( "SELECT goalName FROM Rule" )
  idb_rel_list = cursor.fetchall()
  idb_rel_list = tools.toAscii_list( idb_rel_list )

  logging.debug( "  IEDB REWRITES : idb_rel_list = " + str( idb_rel_list ) )

  # initialize dictionary
  rel_name_to_fact_obj_map = {}
  for rel_name in idb_rel_list :
    rel_name_to_fact_obj_map[ rel_name ] = []

  logging.debug( "  IEDB REWRITES : rel_name_to_fact_obj_map = " + str( rel_name_to_fact_obj_map ) )

  # collect fids
  for f in factMeta :
    if f.relationName in idb_rel_list :
      rel_name_to_fact_obj_map[ f.relationName ].append( f )

  logging.debug( "  IEDB REWRITES : rel_name_to_fact_obj_map = " + str( rel_name_to_fact_obj_map ) )

  # ----------------------------------------- #
  # append "_edb" to all fact names

  for rel_name in rel_name_to_fact_obj_map :

    fact_obj_list = rel_name_to_fact_obj_map[ rel_name ]

    for fact_obj in fact_obj_list :
      fact_obj.relationName += "_edb"
      fact_obj.saveFactInfo()

      cursor.execute( "SELECT name FROM Fact WHERE fid=='" + str( fact_obj.fid ) + "'" )
      name = cursor.fetchone()
      name = tools.toAscii_str( name )
      logging.debug( "  IEBD REWRITES : name = " + str( name ) )

  # ----------------------------------------- #
  # add a new rule with the original goal
  # predicated on the new _edb goal name

  for rel_name in rel_name_to_fact_obj_map :

    logging.debug( "  IEDB REWRITES : rel_name = " + rel_name )
    logging.debug( "  IEDB REWRITEs : len( rel_name_to_fact_obj_map[ " + rel_name + " ] ) = " + \
                      str( len( rel_name_to_fact_obj_map[ rel_name ] ) ) )

    if len( rel_name_to_fact_obj_map[ rel_name ] ) > 0 : 

      new_ruleData                   = {}
      new_ruleData[ "relationName" ] = rel_name
      new_ruleData[ "goalTimeArg" ]  = ""
      new_ruleData[ "eqnDict" ]      = {}
  
      # build the goal attribute list
      new_goalAttList = []
 
      representative_factData = rel_name_to_fact_obj_map[ rel_name ][ 0 ].factData # just pick one
      representative_dataList = representative_factData[ "dataList" ]

      logging.debug( "  representative_factData = " + str( representative_factData ) )
      logging.debug( "  representative_dataList = " + str( representative_dataList ) )

      arity = len( representative_dataList )
      for i in range( 0, arity ) :
        new_goalAttList.append( "A" + str( i ) )
  
      new_ruleData[ "goalAttList" ] = new_goalAttList
  
      # build the subgoal
      new_subgoal_dict = {}
      new_subgoal_dict[ "subgoalName" ]    = rel_name + "_edb"
      new_subgoal_dict[ "subgoalAttList" ] = new_goalAttList
      new_subgoal_dict[ "polarity" ]       = ""
      new_subgoal_dict[ "subgoalTimeArg" ] = ""
  
      new_ruleData[ "subgoalListOfDicts" ] = [ new_subgoal_dict ]
  
      # generate a new rid
      rid = tools.getIDFromCounters( "rid" )
 
      logging.debug( "  IEDB REWRITES : new_ruleData = " + str( new_ruleData ) )
 
      # save the new rule
      new_rule        = copy.deepcopy( Rule.Rule( rid, new_ruleData, cursor ) )
      new_rule.cursor = cursor # need to do this again for some reason???
      ruleMeta.append( new_rule )
  
      # set the types!
      #setTypes.setTypes( cursor, settings_path )

    logging.debug( "  IEDB REWRITES : done on rel_name = " + rel_name )

  # ----------------------------------------- #

  logging.debug( "  IEDB REWRITES : ...done." )
  return factMeta, ruleMeta


#########
#  EOF  #
#########
