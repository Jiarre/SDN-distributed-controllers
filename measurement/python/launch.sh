#!/bin/bash
echo "pkts,zones,getter,delay" > data.csv
for (( c=1; c<=$2; c++ ))
do
    sleep 1
    python3 getter.py -z $1 -p $c $2 &
done
sleep 5
for (( c=1; c<=$1; c++ ))
do
    sleep 0.25
    python3 peer.py -z $c -p $2 &
done

