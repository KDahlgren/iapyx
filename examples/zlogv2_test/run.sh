#!/usr/bin/env bash


cmd="time python ../../src/drivers/iapyx.py -c 0 -n c0,c1,seq0,obj0,obj1,obj2 --EOT 13 -f ./zlogv2_test.ded --evaluator c4"
opt_cmd="cmd"

rm ./IR.db

$cmd

rm ./IR.db
