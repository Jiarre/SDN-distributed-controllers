#!/bin/bash

#$1 number of peers
#$2 number of getters
#$3 path
TestsArray=("1byte"  "2byte"  "4byte"  "8byte"  "16byte"  "32byte" "64byte" "128byte" "256byte" "512byte" "1Kbyte"  "2Kbyte"  "4Kbyte"  "8Kbyte"  "16Kbyte"  "32Kbyte" "64Kbyte" "128Kbyte" "256Kbyte" "512Kbyte" "1Mbyte"  "2Mbyte"  "4Mbyte"  "8Mbyte"  "16Mbyte"  "32Mbyte" "64Mbyte" "128Mbyte" "256Mbyte" "512Mbyte")
count=0
for val in ${TestsArray[*]}; do
    path=$3/$val
 
    echo "Starting tests with $1 peers, $2 getters and $((2**$count)) payload. Saving in $path"
    mkdir -p $path
    echo "getter,peers,micros,payload,rcv_flag,delay" > $path/1gets.csv
    echo "Launching 1gets"
    ./launch.sh $1 $2 1000000 $((2**$count))  >> $path/1gets.csv
    sleep 10
    killall peer && killall getter
    sleep 2
    echo "getter,peers,micros,payload,rcv_flag,delay" > $path/10gets.csv
    echo "Launching 10gets"
    ./launch.sh $1 $2 100000 $((2**$count))  >> $path/10gets.csv
    sleep 5
    killall peer && killall getter
    sleep 2
    echo "getter,peers,micros,payload,rcv_flag,delay" > $path/100gets.csv
    echo "Launching 100gets"
    ./launch.sh $1 $2 10000 $((2**$count))  >> $path/100gets.csv
    sleep 5
    killall peer && killall getter
    sleep 2
    echo "getter,peers,micros,payload,rcv_flag,delay" > $path/1kgets.csv
    echo "Launching 1kgets"
    ./launch.sh $1 $2 1000 $((2**$count))  >> $path/1kgets.csv
    sleep 5
    killall peer && killall getter
    sleep 2
    echo "getter,peers,micros,payload,rcv_flag,delay" > $path/10kgets.csv
    echo "Launching 10kgets"
    ./launch.sh $1 $2 100 $((2**$count))  >> $path/10kgets.csv
    sleep 5
    killall peer && killall getter
    sleep 2
    echo "getter,peers,micros,payload,rcv_flag,delay" > $path/100kgets.csv
    echo "Launching 100kgets"
    ./launch.sh $1 $2 10 $((2**$count)) >> $path/100kgets.csv
    sleep 5
    killall peer && killall getter
    sleep 2
    echo "getter,peers,micros,payload,rcv_flag,delay" > $path/1Mgets.csv
    echo "Launching 1Mgets"
    ./launch.sh $1 $2 1 $((2**$count))  >> $path/1Mgets.csv
    sleep 5
    killall peer && killall getter
    sleep 2
    echo "getter,peers,micros,payload,rcv_flag,delay" > $path/infgets.csv
    echo "Launching infgets"
    ./launch.sh $1 $2 0 $((2**$count))  >> $path/infgets.csv
    sleep 5
    killall peer && killall getter
    sleep 2
    count=$((count+1))
done
 