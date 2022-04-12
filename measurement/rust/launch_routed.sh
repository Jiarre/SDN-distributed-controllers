#!/bin/bash
#peers,getters,micros,payload,directory

# $1 #getters
# $2 #peers
# $3 micros of delay
# $4 payload size
 /home/federico/zenoh-no-ls/target/release/zenohd -l tcp/0.0.0.0:7447 --config conf.json5  &
sleep 3
for (( c=1; c<=$1; c++ ))
do
     RUST_LOG=Warn ./getter/target/release/getter --peers $2 --getters $1 -e tcp/0.0.0.0:7447 --no-multicast-scouting --delay $3 --config conf.json5 --size $4 -m client & 
done
count=1
for (( c=1; c<=$2; c++ ))
do
   RUST_LOG=Warn ./peer/target/release/peer -e tcp/0.0.0.0:7447 --zone $c --no-multicast-scouting --config conf.json5 --size $4 -m client &
   count=$(($count+1))
done