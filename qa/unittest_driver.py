#!/usr/bin/env python

import logging, os, unittest
import Test_comb
import Test_dedt
import Test_dm
import Test_iedb_rewrites
import Test_setTypes
import Test_vs_molly
import Test_molly_ldfi
import Test_wildcard_rewrites

#####################
#  UNITTEST DRIVER  #
#####################
def unittest_driver() :

  print
  print "************************************"
  print "*   RUNNING TEST SUITE FOR IAPYX   *"
  print "************************************"
  print

  # make absolutely sure no leftover IR files exist.
  if os.path.exists( "./IR*.db*" ) :
    os.system( "rm ./IR*.db*" )
    logging.info( "  UNIT TEST DRIVER : deleted rogue IR*.db* file." )

  # run Test_dedt tests
  suite = unittest.TestLoader().loadTestsFromTestCase( Test_dedt.Test_dedt )
  unittest.TextTestRunner( verbosity=2, buffer=True ).run( suite )

  # run Test_vs_molly tests
  suite = unittest.TestLoader().loadTestsFromTestCase( Test_vs_molly.Test_vs_molly )
  unittest.TextTestRunner( verbosity=2, buffer=True ).run( suite )

  # run Test_dm tests
  suite = unittest.TestLoader().loadTestsFromTestCase( Test_dm.Test_dm )
  unittest.TextTestRunner( verbosity=2, buffer=True ).run( suite )

  # run Test_iedb_rewrites tests
  suite = unittest.TestLoader().loadTestsFromTestCase( Test_iedb_rewrites.Test_iedb_rewrites )
  unittest.TextTestRunner( verbosity=2, buffer=True ).run( suite )

  # run Test_wildcard_rewrites tests
  suite = unittest.TestLoader().loadTestsFromTestCase( Test_wildcard_rewrites.Test_wildcard_rewrites )
  unittest.TextTestRunner( verbosity=2, buffer=False ).run( suite )

  # run Test_setTypes tests
  suite = unittest.TestLoader().loadTestsFromTestCase( Test_setTypes.Test_setTypes )
  unittest.TextTestRunner( verbosity=2, buffer=False ).run( suite )

#  # run Test_molly_ldfi tests
#  suite = unittest.TestLoader().loadTestsFromTestCase( Test_molly_ldfi.Test_molly_ldfi )
#  unittest.TextTestRunner( verbosity=2, buffer=False ).run( suite )

  # run Test_comb tests
  suite = unittest.TestLoader().loadTestsFromTestCase( Test_comb.Test_comb )
  unittest.TextTestRunner( verbosity=2, buffer=False ).run( suite )

#########################
#  THREAD OF EXECUTION  #
#########################
unittest_driver()

# make absolutely sure no leftover IR files exist.
if os.path.exists( "./IR*.db*" ) :
  os.system( "rm ./IR*.db*" )
  logging.info( "  UNIT TEST DRIVER : deleted rogue IR*.db* files." )



#########
#  EOF  #
#########
