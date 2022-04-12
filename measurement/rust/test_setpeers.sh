#!/bin/bash

PeerArray=("1024")
for peer in ${PeerArray[*]}; do
    
    path=$3/${peer}peer
    echo "Starting tests with $1 getter, $peer peers and 32byte payload. Saving in $path"
    mkdir -p $path
    echo "getter,peers,micros,payload,rcv_flag,delay" > $path/1gets.csv
    echo "Launching 1gets"
    ./getter.sh $1 $peer 1000000 32  >> $path/1gets.csv
    sleep 20
    killall getter  
    sleep 3
    echo "getter,peers,micros,payload,rcv_flag,delay" > $path/10gets.csv
    echo "Launching 10gets"
    ./getter.sh $1 $peer 100000 32  >> $path/10gets.csv
    sleep 10
    killall getter  
    sleep 3
    echo "getter,peers,micros,payload,rcv_flag,delay" > $path/100gets.csv
    echo "Launching 100gets"
    ./getter.sh $1 $peer 10000 32  >> $path/100gets.csv
    sleep 10
    killall getter  
    sleep 3
    echo "getter,peers,micros,payload,rcv_flag,delay" > $path/1kgets.csv
    echo "Launching 1kgets"
    ./getter.sh $1 $peer 1000 32  >> $path/1kgets.csv
    sleep 10
    killall getter  
    sleep 3
    echo "getter,peers,micros,payload,rcv_flag,delay" > $path/10kgets.csv
    echo "Launching 10kgets"
    ./getter.sh $1 $peer 100 32  >> $path/10kgets.csv
    sleep 10
    killall getter  
    sleep 3
    echo "getter,peers,micros,payload,rcv_flag,delay" > $path/100kgets.csv
    echo "Launching 100kgets"
    ./getter.sh $1 $peer 10 32 >> $path/100kgets.csv
    sleep 10
    killall getter  
    sleep 3
    echo "getter,peers,micros,payload,rcv_flag,delay" > $path/1Mgets.csv
    echo "Launching 1Mgets"
    ./getter.sh $1 $peer 1 32  >> $path/1Mgets.csv
    sleep 10
    killall getter  
    sleep 3
    echo "getter,peers,micros,payload,rcv_flag,delay" > $path/infgets.csv
    echo "Launching infgets"
    ./getter.sh $1 $peer 0 32  >> $path/infgets.csv
    sleep 10
    killall getter  
    sleep 3
done