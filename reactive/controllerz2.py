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
from zenoh import Reliability, SampleKind, SubMode, Sample, KeyExpr
from zenoh.queryable import STORAGE
import copy


def topology_update(sample):
    global session,flows,mode
    #session.put(basekey+f"/flows/{zone}/{mode}",json.dumps(flows))
    print("trigger pkt 2")

def known_hosts_update(hosts):
    
    global known_hosts
    kh = json.loads(hosts.payload.decode("utf-8"))
    
    for host in kh:
        if kh[host] not in known_hosts:
            known_hosts[host] = kh[host]
    print("C2 Updated kh")
    print(known_hosts)

def listener_dispatcher(msg):
    if str(msg.key_expr)=="sdn/host-pkt":
        topology_update(msg)
    elif str(msg.key_expr)=="sdn/known_hosts":
        known_hosts_update(msg)

def listener(sample):
    print(">> [Subscriber2] Received {} ('{}': '{}')"
          .format(sample.kind, sample.key_expr, sample.payload.decode("utf-8")))
    if sample.kind == SampleKind.DELETE:
        store.pop(str(sample.key_expr), None)
    else:
        store[str(sample.key_expr)] = (sample.value, sample.source_info)


def listener_bs(sample):
    print(">> [Subscriber2] Received {} ('{}': '{}')"
          .format(sample.kind, sample.key_expr, sample.payload.decode("utf-8")))
    if sample.kind == SampleKind.DELETE:
        store_bs.pop(str(sample.key_expr), None)
    else:
        store_bs[str(sample.key_expr)] = (sample.value, sample.source_info)

def query_handler(query):
    print(">> [Queryable2 ] Received Query '{}'".format(query.selector))
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
    print(">> [Queryable3 ] Received Query '{}'".format(query.selector))
    replies = []
    flag = 0
    for stored_name, (data, source_info) in store_bs.items():
        if KeyExpr.intersect(query.key_selector, stored_name):
            flag = 1
            sample = Sample(stored_name, data)
            sample.with_source_info(source_info)
            query.reply(sample)
    if flag == 0:
        query.reply(Sample(key_expr=basekey + "/BS/*", payload="None".encode()))
def to_dpid(n):
    return format(n, "d").zfill(16)

def border_retriever(z):
        global session,zone,border_gw
        s_latency = int(round(time.time() * 1000))
        while True:
            replies = session.get(f"sdn/*/BS/{z}",local_routing=False)
            for reply in replies:
                if reply.data.payload.decode("utf-8") != "None":
                    r = json.loads(reply.data.payload.decode("utf-8"))
                    if int(r[0]["from"]) in border_gw:
                        e_latency = int(round(time.time() * 1000))
                        print(f"C2 Border Retriever latency: {e_latency - s_latency}ms")
                        return r[0]
                    else:
                        print(f"reaching zone {z} from zone {r['from']}")
                        z = int(r[0]["from"])
                        break

def instradate(src,dst,net,datapath):
    dpid = to_dpid(datapath.id)
    src_zone = zone
    dst_zone = zone
    out_port = 0
    s_src = 0
    e_src = 0
    s_dst = 0
    e_dst = 0
    if src not in known_hosts:
        s_src = int(round(time.time() * 1000))

        replies = session.get(f"sdn/*/hosts/{src}",local_routing=False)
        for reply in replies:
            if reply.data.payload.decode("utf-8") != "None":
                #known_hosts[str(reply.data.key_expr)[-17:]] = json.loads(reply.data.payload.decode("utf-8"))
                tmp = json.loads(reply.data.payload.decode("utf-8"))
                src_zone = tmp["zone"]
        e_src = int(round(time.time() * 1000))
                    
        
    if dst not in known_hosts:
        s_dst = int(round(time.time() * 1000))
        replies = session.get(f"sdn/*/hosts/{dst}",local_routing=False)
        for reply in replies:
            if reply.data.payload.decode("utf-8") != "None":
                tmp = json.loads(reply.data.payload.decode("utf-8"))
                dst_zone = tmp["zone"]
        e_dst = int(round(time.time() * 1000))
    
    print(f"Controller2 distributed query time {src}->{dst}: \nsrc = {e_src - s_src}ms \ndst = {e_dst - s_dst}ms")
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
        print(f"{src} -> {dst} use path {path}")
        next=path[path.index(dpid)+1]
        out_port=net[dpid][next]['port']
    elif src not in net and dst in net:
        path=nx.shortest_path(net,dpid,dst)
        print(f"{src} -> {dst} use path {path}")
        next=path[path.index(dpid)+1]
        out_port=net[dpid][next]['port']

    elif src in net and dst not in net:
        
        if dst_zone not in border_gw:
            r = border_retriever(dst_zone)
            print(r)
            border_gw[dst_zone] = border_gw[int(r["from"])]
            session.put(basekey + f"/BS/{dst_zone}",json.dumps({"via":border_gw[int(r["from"])],"from":r["from"]}))
            
        path=nx.shortest_path(net,src,border_gw[dst_zone],weight='weight')
        print(f"{src} -> {dst} use path {path}")
        try:
            if(path.index(dpid) == len(path)-1) and (datapath.id in border_switch):
                return 0
            else:
                next=path[path.index(dpid)+1]
                out_port=net[dpid][next]['port']
        except ValueError:
            return
    elif src not in net and dst not in net:
        
        if dst_zone not in border_gw:
            r = border_retriever(dst_zone)
            border_gw[dst_zone] = border_gw[int(r["from"])]
            session.put(basekey + f"/BS/{dst_zone}",json.dumps({"via":border_gw[int(r["from"])],"from":r["from"]}))
        if src_zone not in border_gw:
            r = border_retriever(dst_zone)
            border_gw[dst_zone] = border_gw[int(r["from"])]
            session.put(basekey + f"/BS/{src_zone}",json.dumps({"via":border_gw[int(r["from"])],"from":r["from"]}))
        path=nx.shortest_path(net,dpid,border_gw[dst_zone],weight='weight')
        print(f"{src} -> {dst} use path {path}")
        try:
            if(path.index(dpid) == len(path)-1) and (datapath.id in border_switch):
                return 0
            else:
                next=path[path.index(dpid)+1]
                out_port=net[dpid][next]['port']
        except ValueError:
            return
    return out_port

conf = zenoh.Config()
basekey = "sdn/zone2"
zenoh.init_logger()
session = zenoh.open(conf)
sub1 = session.subscribe(basekey+"host-pkt/**",topology_update,reliability=Reliability.Reliable, mode=SubMode.Push)
sub2 = session.subscribe(basekey+"known_hosts",known_hosts_update,reliability=Reliability.Reliable, mode=SubMode.Push)

store_bs = {}
sub_bs = session.subscribe(basekey + "/BS/**", listener_bs, reliability=Reliability.Reliable, mode=SubMode.Push)
queryable_bs = session.queryable(basekey + "/BS/**", STORAGE, query_handler_bs)

store = {}
sub = session.subscribe(basekey + "/hosts/**", listener, reliability=Reliability.Reliable, mode=SubMode.Push)
queryable = session.queryable(basekey + "/hosts/**", STORAGE, query_handler_bs)
zones = ["zone1","zone3"]
mac_to_port = {}
mode = "stdnetwork"
net=nx.DiGraph()
nodes = {}
links = {}
switches = {}
no_of_nodes = 0
no_of_links = 0
fast_links = [(to_dpid(1),to_dpid(4)),(to_dpid(4),to_dpid(1)),(to_dpid(4),to_dpid(2)),(to_dpid(2),to_dpid(4)),(to_dpid(2),to_dpid(3)),(to_dpid(3),to_dpid(2))]

i=0
known_hosts = {}
border_switch = [5,6,9,10]
border_gw = {1:'gateway1',3:'gateway3'} #to zone %d use dpid %d
session.put(basekey + "/BS/1",json.dumps([{"via":"5","from":"2"},{"via":"6","from":"2"}]))
session.put(basekey + "/BS/3",json.dumps([{"via":"9","from":"2"},{"via":"10","from":"2"}]))
flows = {}
flag = 0
zone=2





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
            session.put(basekey + f"/hosts/{mac}",json.dumps(known_hosts[mac]))

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
            replies = session.get(f"sdn/*/BS/{z}",local_routing=False)
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
        global border_gw,border_switch,flag,zone,fast_links

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

            match = parser.OFPMatch(eth_type=0x1111)
            actions = [parser.OFPActionOutput(ofproto.OFPP_CONTROLLER,
                                          ofproto.OFPCML_NO_BUFFER)]
            self.add_flow(datapath, 0, match, actions)
            flows[dpid].append([datapath,1,match,actions])
            flag = 1
        
            net.add_node("gateway1")
            net.add_edge(self.to_dpid(5),'gateway1',port=4)
            net.add_edge('gateway1',self.to_dpid(5))

            net.add_edge(self.to_dpid(6),'gateway1',port=4)
            net.add_edge('gateway1',self.to_dpid(6))

            net.add_node("gateway3")
            net.add_edge(self.to_dpid(9),'gateway3',port=4)
            net.add_edge('gateway3',self.to_dpid(9))

            net.add_edge(self.to_dpid(10),'gateway3',port=4)
            net.add_edge('gateway3',self.to_dpid(10))

        if ev.msg.msg_len < ev.msg.total_len:
            self.logger.debug("packet truncated: only %s of %s bytes",
                              ev.msg.msg_len, ev.msg.total_len)
        


        self.topo_discovery()
        
        if eth.ethertype == ether_types.ETH_TYPE_LLDP:
            return
        if eth.ethertype == 4369:
            self.host_pkt_handler(msg)
            return
        
        out_port = instradate(src,dst,net,datapath)
        print(out_port)

        actions = [parser.OFPActionOutput(out_port)]
        if out_port != ofproto.OFPP_FLOOD and (flagl==0 and flags==0) and out_port != 0:
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

    


    


        

    