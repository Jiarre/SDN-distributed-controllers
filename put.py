import sys
import time
import argparse
import json
import zenoh
from zenoh import config, Encoding, 

hosts = 4
if len(sys.argv) > 1:
    for i in range(1, len(sys.argv)):
        try:
            
            if sys.argv[i] == '-h':
                hosts = int(sys.argv[i+1])
        except:
            print("Invalid arguments")
            exit(-1)
print("Openning session...")
session = zenoh.open({})
d = math.floor(hosts / 4)
        for i in range(1,hosts+1):
            meta = {"zone":"0"}
            if i in range(d):
                meta["zone"] = 1
                session.put("sdn/zone1/hosts/")
            if i in range(d,2*d):
                self.addLink("s2",f"h{i}",bw=1000)
            if i in range(2*d,3*d):
                self.addLink("s13",f"h{i}",bw=1000)
            if i in range(3*d,hosts+1):
                self.addLink("s14",f"h{i}",bw=1000)



session.put(key, value)


session.close()