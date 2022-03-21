import sys
import time
import argparse
import json
import zenoh
import random
from zenoh import Reliability, SampleKind, SubMode, Sample, KeyExpr, config, queryable, QueryTarget, Target
from zenoh.queryable import STORAGE
import csv


zones = 0   #number of zones
port = 6000
id = 0
getters = 0
cz = []
if len(sys.argv) > 1:
    for i in range(1, len(sys.argv)):
        try:
            if sys.argv[i] == '-z':
                zones = int(sys.argv[i+1])
                
            if sys.argv[i] == "-p":
                port = 32768 + int(sys.argv[i+1])
                id = sys.argv[i+1]
                getters = sys.argv[i+2]
            
        except:
            print("Invalid arguments")
            exit(-1)

print(f"Starting getter")

conf = zenoh.Config.from_json5('{"mode": "peer",\"scouting":{ "multicast":{ "enabled": false}}}')

conf.insert_json5(zenoh.config.LISTEN_KEY, json.dumps([f"tcp/0.0.0.0:{port}"]))
#conf.insert_json5(zenoh.config.CONNECT_KEY, json.dumps(cz))
session = zenoh.open(conf)
zenoh.init_logger()
time.sleep(1*zones)

delay = 1
while True:
    f = open('data.csv', 'a')
    writer = csv.writer(f)
    time.sleep(delay)
    z = random.randint(1,zones)
    s = int(round(time.time() * 1000000))
    replies = session.get(f"/sdn/**/hosts/1")
    
    e = int(round(time.time() * 1000000))
    row = [delay,zones,getters,e-s]
    writer.writerow(row)
    f.close()
        
    
