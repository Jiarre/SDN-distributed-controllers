#!/bin/bash
echo "getter,peers,micros,payload,delay"
for (( c=1; c<=$2; c++ ))
do
    ./getter/target/release/getter --peers $1 --getters $2 -l tcp/0.0.0.0:$((32769+$c)) --no-multicast-scouting --delay $3 --config conf.json5&
done
sleep 2
for (( c=1; c<=$1; c++ ))
do
    ./peer/target/release/peer --connect $2 --zone $c --no-multicast-scouting --config conf.json5 &
done