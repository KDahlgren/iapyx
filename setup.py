#!/usr/bin/env python

# based on https://github.com/KDahlgren/pyLDFI/blob/master/setup.py

import os, sys

##########
#  MAIN  #
##########
def main() :
  print "Running iapyx setup with args : \n" + str(sys.argv)

  # clean any existing libs
  os.system( "make clean" )

  # download submodules
  os.system( "make get-submodules" )

  # ---------------------------------------------- #

  os.system( "make c4" )
  os.system( "make molly" )


##############################
#  MAIN THREAD OF EXECUTION  #
##############################
if __name__ == "__main__" :
  main()


#########
#  EOF  #
#########
