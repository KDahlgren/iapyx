#!/usr/bin/env python

import logging, os, re, string, sys


########################
#  GET EVAL META DATA  #
########################
def get_eval_meta_data( eval_results ) :
  COUNT_TUPS = 0
  rel_to_tups_map = {}
  for rel in eval_results :
    tups_total             = len( eval_results[ rel ] )
    COUNT_TUPS            += tups_total
    rel_to_tups_map[ rel ] = tups_total

  return [ COUNT_TUPS, rel_to_tups_map ]


###################
#  GET NUM RULES  #
###################
def get_num_rules( program_lines, rule_str ) :
  COUNT = 0
  for line in program_lines :
    if not ":-" in line or line.startswith( "define(" ) :
      continue
    else :
      if line.startswith( rule_str ) :
        COUNT += 1
  return COUNT


###############u###
#  GET NUM FACTS  #
###################
def get_num_facts( program_lines, fact_str ) :
  COUNT = 0
  for line in program_lines :
    if ":-" in line or line.startswith( "define(" ) :
      continue
    else :
      if line.startswith( fact_str ) :
        COUNT += 1
  return COUNT


###############################
#  GET SUBGOAL PER RULE DATA  #
###############################
def get_subgoal_per_rule_data( program_lines ) :

  collect_counts   = 0
  rule_count       = 0
  max_num_subgoals = 0
  min_num_subgoals = 999999999999999
  for line in program_lines :
    if not ":-" in line :
      continue
    else :
      rule_count     += 1
      line            = line.translate( None, string.whitespace )
      line            = line.split( ":-" )[1]
      num_subgoals    = len( line.split( ")," ) )
      collect_counts += num_subgoals
      if num_subgoals > max_num_subgoals :
        max_num_subgoals = num_subgoals
      elif num_subgoals < min_num_subgoals :
        min_num_subgoals = num_subgoals

  return [ collect_counts / rule_count, max_num_subgoals, min_num_subgoals ]


#########
#  EOF  #
#########
