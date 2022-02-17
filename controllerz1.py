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
from zenoh import Reliability, SubMode, config, queryable, QueryTarget, Target, Sample, KeyExpr, SampleKind, Sample, KeyExpr
from zenoh.queryable import STORAGE, EVAL
import copy


def topology_update(dummy):
    global session,flows,mode,modes
    session.put(basekey+f"/flows/{zone}/{mode}",json.dumps(flows))
    mode = modes[1]

def known_hosts_update(hosts):
    global known_hosts
    kh = json.loads(hosts.payload.decode("utf-8"))
    for host in kh:
        if kh[host] not in known_hosts:
            known_hosts[host] = kh[host]
    print("C1 Updated kh")
    print(known_hosts)

    

def listener(sample):
    print(">> [Subscriber1] Received {} ('{}': '{}')"
          .format(sample.kind, sample.key_expr, sample.payload.decode("utf-8")))
    if sample.kind == SampleKind.DELETE:
        store.pop(str(sample.key_expr), None)
    else:
        store[str(sample.key_expr)] = (sample.value, sample.source_info)

def listener_bs(sample):
    print(">> [Subscriber1] Received {} ('{}': '{}')"
          .format(sample.kind, sample.key_expr, sample.payload.decode("utf-8")))
    if sample.kind == SampleKind.DELETE:
        store_bs.pop(str(sample.key_expr), None)
    else:
        store_bs[str(sample.key_expr)] = (sample.value, sample.source_info)

def query_handler(query):
    print(">> [Queryable1 ] Received Query '{}'".format(query.selector))
    replies = []
    flag = 0
    for stored_name, (data, source_info) in store.items():
        if KeyExpr.intersect(query.key_selector, stored_name):
            flag = 1
            sample = Sample(stored_name, data)
            sample.with_source_info(source_info)
            query.reply(sample)
    if flag == 0:
        query.reply(Sample(key_expr=query.selector, payload="None".encode()))

def query_handler_bs(query):
    print(">> [Queryable1 ] Received Query '{}'".format(query.selector))
    replies = []
    flag = 0
    for stored_name, (data, source_info) in store_bs.items():
        if KeyExpr.intersect(query.key_selector, stored_name):
            flag = 1
            sample = Sample(stored_name, data)
            sample.with_source_info(source_info)
            query.reply(sample)
    if flag == 0:
        query.reply(Sample(key_expr="sdn/zone1/BS/*", payload="None".encode()))

def to_dpid(n):
    return format(n, "d").zfill(16)

CONTROLLER_NO = 1   

conf = zenoh.Config()
basekey = "sdn/"
zenoh.init_logger()
session = zenoh.open(conf)
zones = ["zone2","zone3"]

sub1 = session.subscribe(basekey+"host-pkt/**",topology_update,reliability=Reliability.Reliable, mode=SubMode.Push)
sub2 = session.subscribe(basekey+"known_hosts",known_hosts_update,reliability=Reliability.Reliable, mode=SubMode.Push)

store = {}
sub = session.subscribe("sdn/zone1/hosts/**", listener, reliability=Reliability.Reliable, mode=SubMode.Push)
queryable = session.queryable("sdn/zone1/hosts/**", STORAGE, query_handler)

store_bs = {}
sub_bs = session.subscribe("sdn/zone1/BS/**", listener_bs, reliability=Reliability.Reliable, mode=SubMode.Push)
queryable_bs = session.queryable("sdn/zone1/BS/**", STORAGE, query_handler_bs)

mac_to_port = {}
modes=["stdnetwork","prioritynetwork"]
mode = modes[0]
net=nx.DiGraph()
nodes = {}
links = {}
switches = {}
no_of_nodes = 0
no_of_links = 0
i=0
zone = 1
fast_links = [(to_dpid(5),to_dpid(1)),(to_dpid(1),to_dpid(5)),("00:00:00:00:00:01",to_dpid(5)),(to_dpid(5),"00:00:00:00:00:01")]
known_hosts = {"00:00:00:00:00:01":{"zone":1, "ip":"10.0.0.1"},"00:00:00:00:00:02":{"zone":1, "ip":"10.0.0.2"}} #mac:zone
border_switch=[1]
session.put("sdn/zone1/BS/2",json.dumps({"via":"1","from":"1"})) #to zone via dpid from zone s
border_gw = {2:1} #to zone %d use dpid %d
flows = {}
flag = 0






class Controllerz1(app_manager.RyuApp):
    
    OFP_VERSIONS = [ofproto_v1_3.OFP_VERSION]    

    def __init__(self, *args, **kwargs):
        super(Controllerz1, self).__init__(*args, **kwargs)
        self.topology_api_app = self


    @set_ev_cls(ofp_event.EventOFPSwitchFeatures, CONFIG_DISPATCHER)
    def switch_features_handler(self, ev):
        datapath = ev.msg.datapath
        ofproto = datapath.ofproto
        parser = datapath.ofproto_parser
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
        #session.put(basekey + "known_hosts", json.dumps(known_hosts) )
        for mac in known_hosts:
            session.put(f"sdn/zone1/hosts/{mac}",json.dumps(known_hosts[mac]))

    def to_dpid(self,dpid):
        return format(dpid, "d").zfill(16)
    def topo_discovery(self):
        global fast_links
        switch_list = get_switch(self, None)   
        switches=[switch.dp.id for switch in switch_list]
        net.add_nodes_from(switches)
        links_list = get_link(self, None)
        for link in links_list:
            fl = (self.to_dpid(link.src.dpid),self.to_dpid(link.dst.dpid))
            rl = (self.to_dpid(link.dst.dpid),self.to_dpid(link.src.dpid))
            net.add_edge(format(link.src.dpid, "d").zfill(16),format(link.dst.dpid, "d").zfill(16),port=link.src.port_no)
            net.add_edge(format(link.dst.dpid, "d").zfill(16),format(link.src.dpid, "d").zfill(16),port=link.dst.port_no)
            if fl in fast_links or rl in fast_links:
                net[self.to_dpid(link.src.dpid)][self.to_dpid(link.dst.dpid)]['weight'] = 1
                net[self.to_dpid(link.dst.dpid)][self.to_dpid(link.src.dpid)]['weight'] = 1
            else:
                net[self.to_dpid(link.src.dpid)][self.to_dpid(link.dst.dpid)]['weight'] = 10
                net[self.to_dpid(link.dst.dpid)][self.to_dpid(link.src.dpid)]['weight'] = 10
    
    def host_pkt_handler(self,msg):
        global session,basekey
        w = msg.data.hex()[28:40]
        w_dest = w[0:2]+':'+w[2:4] + ':'+w[4:6] + ':'+w[6:8] + ':'+w[8:10] + ':'+w[10:12]
        session.put(basekey + "host-pkt", w_dest )

    def border_retriever(self,z):
        global session,zone,border_gw

        while True:
            replies = session.get_collect(f"sdn/*/BS/{z}",local_routing=False)
            for reply in replies:
                if reply.data.payload.decode("utf-8") != "None":
                    r = json.loads(reply.data.payload.decode("utf-8"))
                    if int(r["from"]) in border_gw:
                        return r
                    else:
                        print(f"reaching zone {z} from zone {r['from']}")
                        z = int(r["from"])
                        break
                    

            
    @set_ev_cls(ofp_event.EventOFPPacketIn, MAIN_DISPATCHER)
    def _packet_in_handler(self, ev):
        global net
        global known_hosts
        global mac_to_port
        global flows
        global switches
        global border_gw,border_switch,flag,zone,zones,fast_links

        msg = ev.msg
        datapath = msg.datapath
        ofproto = datapath.ofproto
        parser = datapath.ofproto_parser
        in_port = msg.match['in_port']

        pkt = packet.Packet(msg.data)
        eth = pkt.get_protocols(ethernet.ethernet)[0]
        dst = eth.dst
        src = eth.src
        flagl = 0
        flags = 0
        dpid = format(datapath.id, "d").zfill(16)
        flows.setdefault(dpid,[])
        out_port = 0

        if flag == 0:
            self.update_known_hosts()
            net.add_node('00:00:00:00:00:01')
            net.add_edge(self.to_dpid(5),'00:00:00:00:00:01',port=3)
            net.add_edge('00:00:00:00:00:01',self.to_dpid(5))

            net.add_node('00:00:00:00:00:02')
            net.add_edge(self.to_dpid(6),'00:00:00:00:00:02',port=3)
            net.add_edge('00:00:00:00:00:02',self.to_dpid(6))

            match = parser.OFPMatch(eth_type=0x1111)
            actions = [parser.OFPActionOutput(ofproto.OFPP_CONTROLLER,
                                          ofproto.OFPCML_NO_BUFFER)]
            self.add_flow(datapath, 0, match, actions)
            flows[dpid].append([datapath,1,match,actions])
            
            
            flag = 1
        
        if ev.msg.msg_len < ev.msg.total_len:
            self.logger.debug("packet truncated: only %s of %s bytes",
                              ev.msg.msg_len, ev.msg.total_len)
        


        self.topo_discovery()
        
        if eth.ethertype == ether_types.ETH_TYPE_LLDP:
            return
        if eth.ethertype == 4369:
            self.host_pkt_handler(msg)
            return
        
        query_src = []
        query_dst = []
        if src not in known_hosts:
            replies = session.get_collect(f"sdn/*/hosts/{src}",local_routing=False)
            for reply in replies:
                if reply.data.payload.decode("utf-8") != "None":
                    known_hosts[str(reply.data.key_expr)[-17:]] = json.loads(reply.data.payload.decode("utf-8"))
                    
        
        if dst not in known_hosts:
            replies = session.get_collect(f"sdn/*/hosts/{dst}",local_routing=False)
            for reply in replies:
                if reply.data.payload.decode("utf-8") != "None":
                    known_hosts[str(reply.data.key_expr)[-17:]] = json.loads(reply.data.payload.decode("utf-8"))
        if src not in net:
            if src in known_hosts and known_hosts[src]==zone:

                net.add_node(src)
                net.add_edge(dpid,src,port=in_port)
                net.add_edge(src,dpid)
                fl = (dpid,src)
                rl = (dpid,src)
                if fl in fast_links or rl in fast_links:
                    net[dpid][src]['weight'] = 1
                    net[src][dpid]['weight'] = 1
                else:
                    net[dpid][src]['weight'] = 10
                    net[src][dpid]['weight'] = 10
        
        if dst in net and src in net:
            
            path=nx.shortest_path(net,src,dst,weight='weight')
            if dpid not in path:
                return
            #print(f"{src} -> {dst} use path {path}")
            next=path[path.index(dpid)+1]
            out_port=net[dpid][next]['port']
        elif src not in net and dst in net:
            if src in known_hosts:
                path=nx.shortest_path(net,dpid,dst)
                #print(f"{src} -> {dst} use path {path}")
                next=path[path.index(dpid)+1]
                out_port=net[dpid][next]['port']
            else:
                out_port = ofproto.OFPP_FLOOD
        elif src in net and dst not in net:
            if dst in known_hosts:
                if known_hosts[dst]["zone"] not in border_gw:
                    r = self.border_retriever(known_hosts[dst]["zone"])
                    border_gw[known_hosts[dst]["zone"]] = border_gw[int(r["from"])]
                    session.put(f"sdn/zone1/BS/{known_hosts[dst]['zone']}",json.dumps({"via":border_gw[int(r["from"])],"from":r["from"]}))
                 
                path=nx.shortest_path(net,src,self.to_dpid(border_gw[known_hosts[dst]["zone"]]),weight='weight')
                #print(f"{src} -> {dst} use path {path}")
                try:
                    if(path.index(dpid) == len(path)-1) and (datapath.id in border_switch):
                        return
                    else:
                        next=path[path.index(dpid)+1]
                        out_port=net[dpid][next]['port']
                except ValueError:
                    return
        elif src not in net and dst not in net:
            if dst in known_hosts and src in known_hosts:
                if known_hosts[dst]["zone"] not in border_gw:
                    r = self.border_retriever(known_hosts[dst]["zone"])
                    border_gw[known_hosts[dst]["zone"]] = border_gw[int(r["from"])]
                    session.put(f"sdn/zone1/BS/{known_hosts[dst]['zone']}",json.dumps({"via":border_gw[int(r["from"])],"from":r["from"]}))
                if known_hosts[src]["zone"] not in border_gw:
                    r = self.border_retriever(known_hosts[dst]["zone"])
                    border_gw[known_hosts[dst]["zone"]] = border_gw[int(r["from"])]
                    session.put(f"sdn/zone1/BS/{known_hosts[dst]['zone']}",json.dumps({"via":border_gw[int(r["from"])],"from":r["from"]}))
                path=nx.shortest_path(net,self.to_dpid(border_gw[known_hosts[src]["zone"]]),self.to_dpid(border_gw[known_hosts[dst]["zone"]]),weight='weight')
                #print(f"{src} -> {dst} use path {path}")
                try:
                    if(path.index(dpid) == len(path)-1) and (datapath.id in border_switch):
                        return
                    else:
                        next=path[path.index(dpid)+1]
                        out_port=net[dpid][next]['port']
                except ValueError:
                    return

        actions = [parser.OFPActionOutput(out_port)]
        if out_port != ofproto.OFPP_FLOOD and (flagl==0 and flags==0):
            match = parser.OFPMatch(in_port=in_port, eth_dst=dst, eth_src=src)
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
        self.topo_discovery()
    


    


        

    