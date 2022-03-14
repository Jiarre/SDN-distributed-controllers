import os
import shutil
import sys
import time
import math
import getopt
import random


from mininet.cli import CLI
from mininet.log import setLogLevel
from mininet.net import Mininet
from mininet.topo import Topo
from mininet.node import OVSKernelSwitch, RemoteController, Node, OVSSwitch
from mininet.term import makeTerm
from mininet.link import TCLink
from functools import partial

CONTROLLER1 = "192.168.86.15:6633"
CONTROLLER2 = "192.168.86.15:6634"
CONTROLLER3 = "192.168.86.15:6635"
#CONTROLLER1 = "ec2-18-222-86-54.us-east-2.compute.amazonaws.com:6633"
#CONTROLLER3 = "ec2-35-159-37-105.eu-central-1.compute.amazonaws.com:6635"
#CONTROLLER2 = "ec2-18-222-86-54.us-east-2.compute.amazonaws.com:6634"
#CONTROLLER3 = "ec2-18-222-86-54.us-east-2.compute.amazonaws.com:6635"
hosts = 4
if len(sys.argv) > 1:
    for i in range(1, len(sys.argv)):
        try:
            
            if sys.argv[i] == '-h':
                hosts = int(sys.argv[i+1])
        except:
            print("Invalid arguments")
            exit(-1)


class Topology(Topo):

    def build(self):
        global hosts
        # adding z2
        for i in range(14):
            sconfig = {"dpid": "%016x" % (i + 1)}
            self.addSwitch("s%d" % (i + 1), **sconfig)


        #
        if hosts != 4:
            for i in range(1,hosts+1):
                mac = "%02x:%02x:%02x:%02x:%02x:%02x" % (random.randint(0, 255),random.randint(0, 255),random.randint(0, 255),random.randint(0, 255),random.randint(0, 255),random.randint(0, 255))
                self.addHost(f"h{i}",mac=mac)
        else:
            for i in range(1,hosts+1):
                self.addHost(f"h{i}")

    
        # central zone
        self.addLink("s5","s6",bw=1000)
        self.addLink("s5","s7",bw=1)
        self.addLink("s5","s10",bw=1000)
        self.addLink("s6","s8",bw=1)
        self.addLink("s6","s9",bw=1000)
        self.addLink("s8","s10",bw=1)
        self.addLink("s7","s9",bw=1)
        self.addLink("s9","s10",bw=1000)

        # left zone
        self.addLink("s1","s2",bw=1)
        self.addLink("s1","s3",bw=1)
        self.addLink("s1","s4",bw=1000)
        self.addLink("s2","s3",bw=1)
        self.addLink("s2","s4",bw=1000)
        self.addLink("s3","s4",bw=1)

        # right zone
        self.addLink("s13","s14",bw=1000)
        self.addLink("s13","s11",bw=1)
        self.addLink("s13","s12",bw=1)
        self.addLink("s14","s11",bw=1)
        self.addLink("s14","s12",bw=1000)
        self.addLink("s12","s11",bw=1000)

        # adding border connections
        self.addLink("s3","s5",bw=1)
        self.addLink("s4","s6",bw=1000)
        self.addLink("s9","s11",bw=1000)
        self.addLink("s10","s12",bw=1)


        # adding hosts
        if hosts != 4:

            d = math.floor(hosts / 4)
            for i in range(1,hosts+1):

                if i in range(d):
                    self.addLink("s1",f"h{i}",bw=1000)
                if i in range(d,2*d):
                    self.addLink("s2",f"h{i}",bw=1000)
                if i in range(2*d,3*d):
                    self.addLink("s13",f"h{i}",bw=1000)
                if i in range(3*d,hosts+1):
                    self.addLink("s14",f"h{i}",bw=1000)
        else:
            self.addLink("s1",f"h{1}",bw=1000)
            self.addLink("s2",f"h{2}",bw=1000)
            self.addLink("s13",f"h{3}",bw=1000)
            self.addLink("s14",f"h{4}",bw=1000)
        




        

        



        


def runTopo():
    global CONTROLLER2, CONTROLLER1, CONTROLLER3
    topo = Topology()
    OVSSwitch13 = partial( OVSSwitch, protocols='OpenFlow13')
    net = Mininet(
        topo=topo,
        switch=OVSKernelSwitch,
        build=False,
        autoSetMacs=True,
        autoStaticArp=True,
        link=TCLink,
    )
    net.staticArp()
    net.start()
    """for i in range(1,9):
       net['s1'].cmd(f'sudo ovs-vsctl set bridge s{i} stp-enable=true')
        time.sleep(0.1)
        net['s1'].cmd(f'sudo ovs-ofctl add-flow s{i} dl_type=0x1111,action=CONTROLLER')
        print(f"avviato il tutto su s{i}")
        time.sleep(0.1)"""
    
    net['s1'].cmd(f'ovs-vsctl set-controller s1 tcp:{CONTROLLER1}')
    time.sleep(0.1)
    net['s1'].cmd(f'ovs-vsctl set-controller s2 tcp:{CONTROLLER1}')
    time.sleep(0.1)
    net['s1'].cmd(f'ovs-vsctl set-controller s3 tcp:{CONTROLLER1}')
    time.sleep(0.1)
    net['s1'].cmd(f'ovs-vsctl set-controller s4 tcp:{CONTROLLER1}')
    time.sleep(0.1)
    net['s1'].cmd(f'ovs-vsctl set-controller s5 tcp:{CONTROLLER2}')
    time.sleep(0.1)
    net['s1'].cmd(f'ovs-vsctl set-controller s6 tcp:{CONTROLLER2}')
    time.sleep(0.1)
    net['s1'].cmd(f'ovs-vsctl set-controller s7 tcp:{CONTROLLER2}')
    time.sleep(0.1)
    net['s1'].cmd(f'ovs-vsctl set-controller s8 tcp:{CONTROLLER2}')
    time.sleep(0.1)
    net['s1'].cmd(f'ovs-vsctl set-controller s9 tcp:{CONTROLLER2}')
    time.sleep(0.1)
    net['s1'].cmd(f'ovs-vsctl set-controller s10 tcp:{CONTROLLER2}')
    time.sleep(0.1)
    net['s1'].cmd(f'ovs-vsctl set-controller s11 tcp:{CONTROLLER3}')
    time.sleep(0.1)
    net['s1'].cmd(f'ovs-vsctl set-controller s12 tcp:{CONTROLLER3}')
    time.sleep(0.1)
    net['s1'].cmd(f'ovs-vsctl set-controller s13 tcp:{CONTROLLER3}')
    time.sleep(0.1)
    net['s1'].cmd(f'ovs-vsctl set-controller s14 tcp:{CONTROLLER3}')
    time.sleep(0.1)
    
    for i in range(1,hosts+1):
        #net[f'h{i}'].cmd("python3 s.py &")
        time.sleep(0.1)

        print(f"Script avviato in h{i}")
    CLI(net)

    net.stop()

if __name__ == '__main__':
    setLogLevel( 'info' )
    runTopo()