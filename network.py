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
        for i in range(8):
            sconfig = {"dpid": "%016x" % (i + 1)}
            self.addSwitch("s%d" % (i + 1), **sconfig)


        #
        

        self.addHost("h1")
        self.addHost("h2")
        self.addHost("h3")
        self.addHost("h4")
        # central zone
        self.addLink("s1","s2",bw=10)
        self.addLink("s2","s3",bw=1000)
        self.addLink("s1","s3",bw=10)
        self.addLink("s1","s4",bw=1000)
        self.addLink("s4","s2",bw=1000)
        self.addLink("s4","s3",bw=10)

        # left zone
        self.addLink("s5","s1",bw=1000)
        self.addLink("s6","s1",bw=10)
        self.addLink("s5","s6",bw=10)

        # right zone
        self.addLink("s7","s3",bw=10)
        self.addLink("s8","s3",bw=1000)
        self.addLink("s7","s8",bw=10)



        # adding hosts

        self.addLink("h1","s5",bw=1000)
        self.addLink("h2","s6",bw=10)
        self.addLink("h3","s7",bw=10)
        self.addLink("h4","s8",bw=1000)




        

        



        


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
    for i in range(1,9):
        net['s1'].cmd(f'sudo ovs-vsctl set bridge s{i} stp-enable=true')
        time.sleep(0.1)
        net['s1'].cmd(f'sudo ovs-ofctl add-flow s{i} dl_type=0x1111,action=CONTROLLER')
        print(f"avviato il tutto su s{i}")
        time.sleep(0.1)
    net['s1'].cmd('ovs-vsctl set-controller s1 tcp:127.0.0.1:6633 tcp:127.0.0.1:6634 && ovs-vsctl set port s1-eth1 other_config:stp-path-cost=10 && ovs-vsctl set port s1-eth2 other_config:stp-path-cost=10 && ovs-vsctl set port s1-eth3 other_config:stp-path-cost=1 && ovs-vsctl set port s1-eth4 other_config:stp-path-cost=1 && ovs-vsctl set port s1-eth5 other_config:stp-path-cost=10')
    time.sleep(0.1)
    net['s2'].cmd('ovs-vsctl set-controller s2 tcp:127.0.0.1:6634 && ovs-vsctl set port s2-eth1 other_config:stp-path-cost=10 && ovs-vsctl set port s2-eth2 other_config:stp-path-cost=1 && ovs-vsctl set port s3-eth3 other_config:stp-path-cost=1')
    time.sleep(0.1)
    net['s3'].cmd('ovs-vsctl set-controller s3 tcp:127.0.0.1:6634 tcp:127.0.0.1:6635 && ovs-vsctl set port s3-eth1 other_config:stp-path-cost=1 && ovs-vsctl set port s3-eth2 other_config:stp-path-cost=10 && ovs-vsctl set port s3-eth3 other_config:stp-path-cost=10 && ovs-vsctl set port s3-eth4 other_config:stp-path-cost=10 && ovs-vsctl set port s3-eth5 other_config:stp-path-cost=1')
    time.sleep(0.1)
    net['s4'].cmd('ovs-vsctl set-controller s4 tcp:127.0.0.1:6634 && ovs-vsctl set port s4-eth1 other_config:stp-path-cost=1 && ovs-vsctl set port s4-eth2 other_config:stp-path-cost=10 && ovs-vsctl set port s4-eth3 other_config:stp-path-cost=10')
    time.sleep(0.1)
    net['s5'].cmd('ovs-vsctl set-controller s5 tcp:127.0.0.1:6633 && ovs-vsctl set port s5-eth1 other_config:stp-path-cost=1 && ovs-vsctl set port s5-eth2 other_config:stp-path-cost=10 && ovs-vsctl set port s5-eth3 other_config:stp-path-cost=1')
    time.sleep(0.1)
    net['s6'].cmd('ovs-vsctl set-controller s6 tcp:127.0.0.1:6633 && ovs-vsctl set port s6-eth1 other_config:stp-path-cost=10 && ovs-vsctl set port s6-eth2 other_config:stp-path-cost=10 && ovs-vsctl set port s6-eth3 other_config:stp-path-cost=10')
    time.sleep(0.1)
    net['s7'].cmd('ovs-vsctl set-controller s7 tcp:127.0.0.1:6635 && ovs-vsctl set port s7-eth1 other_config:stp-path-cost=10 && ovs-vsctl set port s7-eth2 other_config:stp-path-cost=10 && ovs-vsctl set port s7-eth3 other_config:stp-path-cost=10')
    time.sleep(0.1)
    net['s8'].cmd('ovs-vsctl set-controller s8 tcp:127.0.0.1:6635 && ovs-vsctl set port s8-eth1 other_config:stp-path-cost=1 && ovs-vsctl set port s8-eth2 other_config:stp-path-cost=10 && ovs-vsctl set port s8-eth3 other_config:stp-path-cost=1')
    time.sleep(0.1)
    CLI(net)

    net.stop()

if __name__ == '__main__':
    setLogLevel( 'info' )
    runTopo()