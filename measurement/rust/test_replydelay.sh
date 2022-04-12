#!/bin/bash

#$1 number of peers
#$peer number of getters
#$3 path
PeerArray=("1024")
#PeerArray=("1024")
for peer in ${PeerArray[*]}; do
    
    path=$3/${peer}peer
    echo "Starting tests with $1 getter, $peer peers and 32byte payload. Saving in $path"
    #mkdir -p $path
    #echo "getter,peers,micros,payload,rcv_flag,span" > $path.csv
    echo "launch_routeding 1gets"
    ./getter.sh $1 $peer 1000000 32  >> $path.csv
    sleep 10
    killall getter
    sleep 3
    echo "launch_routeding 10gets"
    ./getter.sh $1 $peer 100000 32  >> $path.csv
    sleep 10
    killall getter
    sleep 3
    echo "launch_routeding 100gets"
    ./getter.sh $1 $peer 10000 32  >> $path.csv
    sleep 10
    killall getter
    sleep 3
    echo "launch_routeding 1kgets"
    ./getter.sh $1 $peer 1000 32  >> $path.csv
    sleep 10
    killall getter
    sleep 3
    echo "launch_routeding 10kgets"
    ./getter.sh $1 $peer 100 32  >> $path.csv
    sleep 10
    killall getter
    sleep 3
    echo "launch_routeding 100kgets"
    ./getter.sh $1 $peer 10 32 >> $path.csv
    sleep 10
    killall getter
    sleep 3
    echo "launch_routeding 1Mgets"
    ./getter.sh $1 $peer 1 32  >> $path.csv
    sleep 10
    killall getter
    sleep 3
    echo "launch_routeding infgets"
    ./getter.sh $1 $peer 0 32  >> $path.csv
    sleep 10
    killall getter
    sleep 3
    count=$((count+1))
done
 