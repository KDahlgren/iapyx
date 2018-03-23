#!/usr/bin/env bash


cmd="time python ../../src/drivers/iapyx.py -c 0 -n a,b --EOT 3 -f ./tcp_handshake.ded --evaluator c4 --data_save_path ./data"
opt_cmd="cmd"

rm ./IR.db
rm ./tmp.txt

$cmd

rm ./IR.db
rm ./tmp.txt

