#!/bin/bash

#$1 number of peers
#$peer number of getters
#$3 path
#PeerArray=("1" "2" "4" "8" "16" "32" "64" "128" "256" "512" "1024")
PeerArray=("1024")
for peer in ${PeerArray[*]}; do
    
    path=$3/${peer}peer
    echo "Starting tests with $1 getter, $peer peers and 32byte payload. Saving in $path"
    mkdir -p $path
    echo "getter,peers,micros,payload,rcv_flag,delay" > $path/1gets.csv
    echo "launch_routeding 1gets"
    ./launch_routed.sh $1 $peer 1000000 32  >> $path/1gets.csv
    sleep 30
    killall peer && killall getter && killall zenohd  
    sleep 3
    echo "getter,peers,micros,payload,rcv_flag,delay" > $path/10gets.csv
    echo "launch_routeding 10gets"
    ./launch_routed.sh $1 $peer 100000 32  >> $path/10gets.csv
    sleep 30
    killall peer && killall getter && killall zenohd  
    sleep 3
    echo "getter,peers,micros,payload,rcv_flag,delay" > $path/100gets.csv
    echo "launch_routeding 100gets"
    ./launch_routed.sh $1 $peer 10000 32  >> $path/100gets.csv
    sleep 30
    killall peer && killall getter && killall zenohd  
    sleep 3
    echo "getter,peers,micros,payload,rcv_flag,delay" > $path/1kgets.csv
    echo "launch_routeding 1kgets"
    ./launch_routed.sh $1 $peer 1000 32  >> $path/1kgets.csv
    sleep 30
    killall peer && killall getter && killall zenohd  
    sleep 3
    echo "getter,peers,micros,payload,rcv_flag,delay" > $path/10kgets.csv
    echo "launch_routeding 10kgets"
    ./launch_routed.sh $1 $peer 100 32  >> $path/10kgets.csv
    sleep 30
    killall peer && killall getter && killall zenohd  
    sleep 3
    echo "getter,peers,micros,payload,rcv_flag,delay" > $path/100kgets.csv
    echo "launch_routeding 100kgets"
    ./launch_routed.sh $1 $peer 10 32 >> $path/100kgets.csv
    sleep 30
    killall peer && killall getter && killall zenohd  
    sleep 3
    echo "getter,peers,micros,payload,rcv_flag,delay" > $path/1Mgets.csv
    echo "launch_routeding 1Mgets"
    ./launch_routed.sh $1 $peer 1 32  >> $path/1Mgets.csv
    sleep 30
    killall peer && killall getter && killall zenohd  
    sleep 3
    echo "getter,peers,micros,payload,rcv_flag,delay" > $path/infgets.csv
    echo "launch_routeding infgets"
    ./launch_routed.sh $1 $peer 0 32  >> $path/infgets.csv
    sleep 10
    killall peer && killall getter && killall zenohd  
    sleep 3
    count=$((count+1))
done
 