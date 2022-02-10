# controller z1

from ryu.base import app_manager
#from ryu.base.app_manager import send_event
from ryu.controller import ofp_event
from ryu.controller.handler import CONFIG_DISPATCHER, MAIN_DISPATCHER
from ryu.controller.handler import set_ev_cls
from ryu.ofproto import ofproto_v1_3
from ryu.lib.packet import packet
from ryu.lib.packet import ethernet
from ryu.lib.packet import ether_types
from ryu.topology import event, switches
from ryu.topology.api import get_switch, get_link

from ryu.app.wsgi import ControllerBase

import networkx as nx
import threading
import sys
import time
from datetime import datetime
import argparse
import json
import zenoh
from zenoh import Reliability, SubMode
import copy


def topology_mod_listener(sample):
        time = '(not specified)' if sample.source_info is None or sample.timestamp is None else datetime.fromtimestamp(
            sample.timestamp.time)
        print(">> [Subscriber] Received {} ('{}': '{}')"
            .format(sample.kind, sample.key_expr, sample.payload.decode("utf-8"), time))
        print("mac-to-port: ")
        print(flows)
        
def known_host_listener(hosts):
    
    global known_hosts
    kh = json.loads(hosts.payload.decode("utf-8"))
    for host in kh:
        if kh[host] not in known_hosts:
            known_hosts[host] = kh[host]
    print("C1 Updated kh")
    print(known_hosts)
    

conf = zenoh.Config()
basekey = "sdn/"
zenoh.init_logger()
session = zenoh.open(conf)

sub = session.subscribe(basekey+"host-pkt/**",topology_mod_listener,reliability=Reliability.Reliable, mode=SubMode.Push)
sub = session.subscribe(basekey+"known_hosts/**",known_host_listener,reliability=Reliability.Reliable, mode=SubMode.Push)


mac_to_port = {}
    
net=nx.DiGraph()
nodes = {}
links = {}
switches = {}
no_of_nodes = 0
no_of_links = 0
i=0
known_hosts = {'00:00:00:00:00:01':1,'00:00:00:00:00:02':1}
border_switch=[1]
border_gw = {2:1,3:1} #to zone %d use dpid %d
flows = {}
flag = 0






class Controllerz1(app_manager.RyuApp):
    
    OFP_VERSIONS = [ofproto_v1_3.OFP_VERSION]    

    def __init__(self, *args, **kwargs):
        super(Controllerz1, self).__init__(*args, **kwargs)
        self.topology_api_app = self
        
        
        
    def discover_topology(self):
        
        time.sleep(10)
        count = 10
        while True:
            time.sleep(5)
            switch_list = get_switch(self.topology_api_app, None)
            tmp_switches=[switch.dp.id for switch in switch_list]
            links_list = get_link(self.topology_api_app, None)
            tmp_links=[(link.src.dpid,link.dst.dpid,{'port':link.src.port_no}) for link in links_list]
            print(tmp_switches)
            print(tmp_links)
            if count==0:
                print("Interrompo thread")
                break
            else:
                self.switches = tmp_switches
                self.links = tmp_links
            count=count-1
            time.sleep(5)


    @set_ev_cls(ofp_event.EventOFPSwitchFeatures, CONFIG_DISPATCHER)
    def switch_features_handler(self, ev):
        datapath = ev.msg.datapath
        ofproto = datapath.ofproto
        parser = datapath.ofproto_parser

        # install table-miss flow entry
        #
        # We specify NO BUFFER to max_len of the output action due to
        # OVS bug. At this moment, if we specify a lesser number, e.g.,
        # 128, OVS will send Packet-In with invalid buffer_id and
        # truncated packet data. In that case, we cannot output packets
        # correctly.  The bug has been fixed in OVS v2.1.0.
        match = parser.OFPMatch()
        actions = [parser.OFPActionOutput(ofproto.OFPP_CONTROLLER,
                                          ofproto.OFPCML_NO_BUFFER)]
        self.add_flow(datapath, 0, match, actions)

    def add_flow(self, datapath, priority, match, actions, buffer_id=None):
        ofproto = datapath.ofproto
        parser = datapath.ofproto_parser

        inst = [parser.OFPInstructionActions(ofproto.OFPIT_APPLY_ACTIONS,
                                             actions)]
        if buffer_id:
            mod = parser.OFPFlowMod(datapath=datapath, buffer_id=buffer_id,
                                    priority=priority, match=match,
                                    instructions=inst)
        else:
            mod = parser.OFPFlowMod(datapath=datapath, priority=priority,
                                    match=match, instructions=inst)
        datapath.send_msg(mod)

    def update_known_hosts(self):
        global session,known_hosts
        session.put(basekey + "known_hosts", json.dumps(known_hosts) )

    def to_dpid(self,dpid):
        return format(dpid, "d").zfill(16)

    @set_ev_cls(ofp_event.EventOFPPacketIn, MAIN_DISPATCHER)
    def _packet_in_handler(self, ev):
        # If you hit this you might want to increase
        # the "miss_send_length" of your switch
        global net
        global known_hosts
        global mac_to_port
        global flows
        global switches
        global border_gw,border_switch,flag

        if flag == 0:
            self.update_known_hosts()
            flag = 1
        
        if ev.msg.msg_len < ev.msg.total_len:
            self.logger.debug("packet truncated: only %s of %s bytes",
                              ev.msg.msg_len, ev.msg.total_len)
        msg = ev.msg
        datapath = msg.datapath
        ofproto = datapath.ofproto
        parser = datapath.ofproto_parser
        in_port = msg.match['in_port']

        pkt = packet.Packet(msg.data)
        eth = pkt.get_protocols(ethernet.ethernet)[0]

        
        
        switch_list = get_switch(self, None)   
        switches=[switch.dp.id for switch in switch_list]
        net.add_nodes_from(switches)
        
        #print "**********List of switches"
        #for switch in switch_list:
        #self.ls(switch)
        #print switch
        #self.nodes[self.no_of_nodes] = switch
        #self.no_of_nodes += 1
    
        links_list = get_link(self, None)
        links=[(format(link.src.dpid, "d").zfill(16),format(link.dst.dpid, "d").zfill(16),{'port':link.src.port_no}) for link in links_list]
        net.add_edges_from(links)
        links=[(format(link.dst.dpid, "d").zfill(16),format(link.src.dpid, "d").zfill(16),{'port':link.dst.port_no}) for link in links_list]
        net.add_edges_from(links)

        
        if eth.ethertype == ether_types.ETH_TYPE_LLDP:
            return
    
        

        #Parser for host-request packet
        if eth.ethertype == 4369:
            global session,basekey
            w = msg.data.hex()[28:40]
            w_dest = w[0:2]+':'+w[2:4] + ':'+w[4:6] + ':'+w[6:8] + ':'+w[8:10] + ':'+w[10:12]
            session.put(basekey + "host-pkt", w_dest )
            return
        #print(net.edges)
        dst = eth.dst
        src = eth.src
        flagl = 0
        flags = 0
        dpid = format(datapath.id, "d").zfill(16)
        flows.setdefault(dpid,[])
        
        #self.logger.info("packet in %s %s %s %s", dpid, src, dst, in_port)
        out_port = 0
        # learn a mac address to avoid FLOOD next time.
        if src not in net:
            net.add_node(src)
            net.add_edge(dpid,src,port=in_port)
            net.add_edge(src,dpid)
        
        if dst in net and src in net:
            print(1)
            path=nx.shortest_path(net,src,dst)
            if dpid not in path:
                return
            next=path[path.index(dpid)+1]
            out_port=net[dpid][next]['port']
        elif src not in net and dst in net:
            if src in known_hosts:
                print(2)
                path=nx.shortest_path(net,dpid,dst)
                next=path[path.index(dpid)+1]
                out_port=net[dpid][next]['port']
            else:
                out_port = ofproto.OFPP_FLOOD
        elif src in net and dst not in net:
            if dst in known_hosts:
                print(3)
                path=nx.shortest_path(net,src,self.to_dpid(border_gw[known_hosts[dst]]))
                print(f"{src} -> {self.to_dpid(border_gw[known_hosts[dst]])} use path {path}")
                print(path)
                try:
                    if(path.index(dpid) == len(path)-1) and (datapath.id in border_switch):
                        return
                    else:
                        next=path[path.index(dpid)+1]
                        out_port=net[dpid][next]['port']
                except ValueError:
                    return
            
        """else:
            print("flood")
            out_port = ofproto.OFPP_FLOOD"""
        #print(f"out nella porta {out_port}")
        actions = [parser.OFPActionOutput(out_port)]

        # install a flow to avoid packet_in next time
        if out_port != ofproto.OFPP_FLOOD and (flagl==0 and flags==0):
            match = parser.OFPMatch(in_port=in_port, eth_dst=dst, eth_src=src)
            # verify if we have a valid buffer_id, if yes avoid to send both
            # flow_mod & packet_out
            if msg.buffer_id != ofproto.OFP_NO_BUFFER:
                self.add_flow(datapath, 1, match, actions, msg.buffer_id)
                return
            else:
                self.add_flow(datapath, 1, match, actions)
                flows[dpid].append([datapath,1,match,actions])
        data = None
        if msg.buffer_id == ofproto.OFP_NO_BUFFER:
            data = msg.data

        out = parser.OFPPacketOut(datapath=datapath, buffer_id=msg.buffer_id,
                                  in_port=in_port, actions=actions, data=data)
        datapath.send_msg(out)

    @set_ev_cls(event.EventSwitchEnter)
    def get_topology_data(self, ev):
        switch_list = get_switch(self, None)   
        switches=[switch.dp.id for switch in switch_list]
        net.add_nodes_from(switches)
        
        #print "**********List of switches"
        #for switch in switch_list:
        #self.ls(switch)
        #print switch
        #self.nodes[self.no_of_nodes] = switch
        #self.no_of_nodes += 1
    
        links_list = get_link(self, None)
        #print links_list

        links=[(format(link.src.dpid, "d").zfill(16),format(link.dst.dpid, "d").zfill(16),{'port':link.src.port_no}) for link in links_list]
        #print links
        net.add_edges_from(links)
        links=[(format(link.dst.dpid, "d").zfill(16),format(link.src.dpid, "d").zfill(16),{'port':link.dst.port_no}) for link in links_list]
        #print links
        net.add_edges_from(links)

    


    


        

    