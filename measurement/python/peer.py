import sys
import time
import argparse
import json
import zenoh
import random
from zenoh import Reliability, SampleKind, SubMode, Sample, KeyExpr
from zenoh.queryable import STORAGE

store = {}
zone = 0
ports = []
if len(sys.argv) > 1:
    for i in range(1, len(sys.argv)):
        try:
            if sys.argv[i] == '-z':
                zone = int(sys.argv[i+1])

            if sys.argv[i] == "-p":
                for p in range(1,int(sys.argv[i+1])+1):
                    
                    ports.append(f'tcp/0.0.0.0:{32768+p}')
                    print(f"connect tcp/0.0.0.0:{32768+p} ")
            
        except:
            print("Invalid arguments")
            exit(-1)


def listener(sample):
    if sample.kind == SampleKind.DELETE:
        store.pop(str(sample.key_expr), None)
    else:
        store[str(sample.key_expr)] = (sample.value, sample.source_info)


def query_handler(query):
    #print(">> [peer zone{}] Received Query '{}'".format(zone,query.selector))
    replies = []
    for stored_name, (data, source_info) in store.items():
        if KeyExpr.intersect(query.key_selector, stored_name):
            sample = Sample(stored_name, data)
            sample.with_source_info(source_info)
            query.reply(sample)


# initiate logging
print(f"Starting zone{zone}")

conf = zenoh.Config.from_json5('{"mode": "peer",\"scouting":{ "multicast":{ "enabled": false}}}')

conf.insert_json5(zenoh.config.CONNECT_KEY, json.dumps(ports))
#conf.insert_json5(zenoh.config.LISTEN_KEY, json.dumps([f"tcp/0.0.0.0:{33000+zone}"]))
zenoh.init_logger()

session = zenoh.open(conf)
time.sleep(1)
sub = session.subscribe(f"/sdn/zone{zone}/hosts/**", listener, reliability=Reliability.Reliable, mode=SubMode.Push)

queryable = session.queryable(f"/sdn/zone{zone}/hosts/**", STORAGE, query_handler)
session.put(f"/sdn/zone{zone}/hosts/{zone}",json.dumps({"zone":f"zone{zone}","ip":f"{random.randint(0, 255)}.{random.randint(0, 255)}.{random.randint(0, 255)}.{random.randint(0, 255)}"})) 


c = '\0'
while c != 'q':
    c = sys.stdin.read(1)
    if c == '':
        time.sleep(1)

sub.close()
queryable.close()
session.close()