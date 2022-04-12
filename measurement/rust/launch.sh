#!/bin/bash
#peers,getters,micros,payload,directory

# $1 #getters
# $2 #peers
# $3 micros of delay
# $4 payload size
for (( c=1; c<=$1; c++ ))
do
    RUST_LOG=Warn ./getter/target/release/getter --peers $2 --getters $1 -l tcp/0.0.0.0:$((32769+$c)) --no-multicast-scouting --delay $3 --config conf.json5 --size $4  & 
done
sleep 1
for (( c=1; c<=$2; c++ ))
do
    RUST_LOG=Warn ./peer/target/release/peer --connect $1 --zone $c --no-multicast-scouting --config conf.json5 --size $4 &
done




