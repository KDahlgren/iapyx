#!/usr/bin/env python

import logging, os, string, sys, unittest
import Test_toy2_breaking_example
import log_settings

#####################
#  UNITTEST DRIVER  #
#####################
def unittest_driver() :

  print
  print "*****************************************************"
  print "*   RUNNING TEST SUITE FOR TOY 2 BREAKING EXAMPLE   *"
  print "*****************************************************"
  print

  # make absolutely sure no leftover IR files exist.
  if os.path.exists( "./IR.db" ) :
    os.system( "rm ./IR.db" )
    logging.info( "  UNIT TEST DRIVER : deleted rogue IR.db file." )

  # run Test_toy2_breaking_example tests
  suite = unittest.TestLoader().loadTestsFromTestCase( Test_toy2_breaking_example.Test_toy2_breaking_example )
  unittest.TextTestRunner( verbosity=2, buffer=True ).run( suite )


#########################
#  THREAD OF EXECUTION  #
#########################
unittest_driver()

# make absolutely sure no leftover IR files exist.
if os.path.exists( "./IR.db" ) :
  os.system( "rm ./IR.db" )
  logging.info( "  UNIT TEST DRIVER : deleted rogue IR.db file." )



#########
#  EOF  #
#########
