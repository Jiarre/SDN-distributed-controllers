import os
import shutil
import sys
import time
import math


from mininet.cli import CLI
from mininet.log import setLogLevel
from mininet.net import Mininet
from mininet.topo import Topo
from mininet.node import OVSKernelSwitch, RemoteController, Node, OVSSwitch
from mininet.term import makeTerm
from mininet.link import TCLink
from functools import partial





class Topology(Topo):

    def build(self):
        # adding z2
        for i in range(14):
            sconfig = {"dpid": "%016x" % (i + 1)}
            self.addSwitch("s%d" % (i + 1), **sconfig)


        #
        

        self.addHost("h1")
        self.addHost("h2")
        self.addHost("h3")
        self.addHost("h4")
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
        self.addLink("s3","s4",bw=1000)

        # right zone
        self.addLink("s13","s14",bw=1000)
        self.addLink("s13","s11",bw=1)
        self.addLink("s13","s12",bw=1)
        self.addLink("s14","s11",bw=1)
        self.addLink("s14","s12",bw=1000)
        self.addLink("s12","s11",bw=1000)

        # adding border connections
        self.addLink("s3","s5",bw=1000)
        self.addLink("s4","s6",bw=1000)
        self.addLink("s9","s11",bw=1000)
        self.addLink("s10","s12",bw=1000)


        # adding hosts

        self.addLink("h1","s1",bw=1000)
        self.addLink("h2","s2",bw=1000)
        self.addLink("h3","s13",bw=1000)
        self.addLink("h4","s14",bw=1000)




        

        



        


def runTopo():
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
    net.start()
    """for i in range(1,9):
       net['s1'].cmd(f'sudo ovs-vsctl set bridge s{i} stp-enable=true')
        time.sleep(0.1)
        net['s1'].cmd(f'sudo ovs-ofctl add-flow s{i} dl_type=0x1111,action=CONTROLLER')
        print(f"avviato il tutto su s{i}")
        time.sleep(0.1)"""
    net['s1'].cmd('ovs-vsctl set-controller s1 tcp:127.0.0.1:6633')
    time.sleep(0.1)
    net['s1'].cmd('ovs-vsctl set-controller s2 tcp:127.0.0.1:6633')
    time.sleep(0.1)
    net['s1'].cmd('ovs-vsctl set-controller s3 tcp:127.0.0.1:6633')
    time.sleep(0.1)
    net['s1'].cmd('ovs-vsctl set-controller s4 tcp:127.0.0.1:6633')
    time.sleep(0.1)
    net['s1'].cmd('ovs-vsctl set-controller s5 tcp:127.0.0.1:6634')
    time.sleep(0.1)
    net['s1'].cmd('ovs-vsctl set-controller s6 tcp:127.0.0.1:6634')
    time.sleep(0.1)
    net['s1'].cmd('ovs-vsctl set-controller s7 tcp:127.0.0.1:6634')
    time.sleep(0.1)
    net['s1'].cmd('ovs-vsctl set-controller s8 tcp:127.0.0.1:6634')
    time.sleep(0.1)
    net['s1'].cmd('ovs-vsctl set-controller s9 tcp:127.0.0.1:6634')
    time.sleep(0.1)
    net['s1'].cmd('ovs-vsctl set-controller s10 tcp:127.0.0.1:6634')
    time.sleep(0.1)
    net['s1'].cmd('ovs-vsctl set-controller s11 tcp:127.0.0.1:6635')
    time.sleep(0.1)
    net['s1'].cmd('ovs-vsctl set-controller s12 tcp:127.0.0.1:6635')
    time.sleep(0.1)
    net['s1'].cmd('ovs-vsctl set-controller s13 tcp:127.0.0.1:6635')
    time.sleep(0.1)
    net['s1'].cmd('ovs-vsctl set-controller s14 tcp:127.0.0.1:6635')
    time.sleep(0.1)
    
    CLI(net)

    net.stop()

if __name__ == '__main__':
    setLogLevel( 'info' )
    runTopo()