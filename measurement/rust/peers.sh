#!/bin/bash

# $1 #peers
# $2 #size
  RUST_LOG=debug /home/federico/zenoh-no-ls/target/release/zenohd -l tcp/0.0.0.0:7447 --no-multicast-scouting --config conf.json5 2> logs/zenohd.log &
#sleep 3
for (( c=1; c<=$1; c++ ))
do
   echo $count
   RUST_LOG=debug ./peer/target/release/peer -e tcp/0.0.0.0:7447 --zone $c --no-multicast-scouting --config conf.json5 --size $2 -m client 2> logs/peerlog/peer_${c}.log &
   sleep 0.5
   count=$(($count+1))
done