
#!/usr/bin/env python

import copy, os, string, sys, unittest
import Test_dedt

#####################
#  UNITTEST DRIVER  #
#####################
def unittest_driver() :

  print
  print "************************************"
  print "*   RUNNING TEST SUITE FOR IAPYX   *"
  print "************************************"
  print

  suite = unittest.TestLoader().loadTestsFromTestCase( Test_dedt.Test_dedt )
  return unittest.TextTestRunner( verbosity=2, buffer=True ).run( suite )


#########################
#  THREAD OF EXECUTION  #
#########################
unittest_driver()


#########
#  EOF  #
#########
