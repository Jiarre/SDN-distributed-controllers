#!/bin/bash
# $1 #getters
# $2 #peers
# $3 delay
# $4 size
for (( c=1; c<=$1; c++ ))
do
     RUST_LOG=debug ./getter/target/release/getter --peers $2 --getters $1 -e tcp/0.0.0.0:7447 --no-multicast-scouting --delay $3 --config conf.json5 --size $4 -m client 2> logs/getter.log & 
done