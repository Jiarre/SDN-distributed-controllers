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
from ryu.app.ofctl import api
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
    global session,flows,mode,modes,flag_flows,fast_net,slow_net,boosted,net,paths_cache
    paths_cache = {}
    #session.put(basekey+f"/flows/{zone}/{mode}",json.dumps(flows))
    #mode = modes[1]
    src_zone = zone
    flag_flows = 1
    if mode == modes[0]:
        mode = modes[1]
        fast_net = copy.deepcopy(net)
        slow_net = copy.deepcopy(net)
        b = json.loads(dummy.payload.decode("utf-8"))
        boosted.append(b["src"])
        boosted.append(b["dst"])
    else:
        mode = modes[0]

def known_hosts_update(hosts):
    global known_hosts
    kh = json.loads(hosts.payload.decode("utf-8"))
    for host in kh:
        if kh[host] not in known_hosts:
            known_hosts[host] = kh[host]
    print("C1 Updated kh")
    print(known_hosts)

    

def listener(sample):
    #print(">> [Subscriber1] Received {} ('{}': '{}')".format(sample.kind, sample.key_expr, sample.payload.decode("utf-8")))
    if sample.kind == SampleKind.DELETE:
        store.pop(str(sample.key_expr), None)
    else:
        store[str(sample.key_expr)] = (sample.value, sample.source_info)

def listener_bs(sample):
    #print(">> [Subscriber1] Received {} ('{}': '{}')".format(sample.kind, sample.key_expr, sample.payload.decode("utf-8")))
    if sample.kind == SampleKind.DELETE:
        store_bs.pop(str(sample.key_expr), None)
    else:
        store_bs[str(sample.key_expr)] = (sample.value, sample.source_info)

def query_handler(query):
    #print(">> [Queryable1 ] Received Query '{}'".format(query.selector))
    replies = []
    for stored_name, (data, source_info) in store.items():
        if KeyExpr.intersect(query.key_selector, stored_name):
            flag = 1
            sample = Sample(stored_name, data)
            sample.with_source_info(source_info)
            query.reply(sample)
   
   
def query_handler_bs(query):
    #print(">> [Queryable1 ] Received Query '{}'".format(query.selector))
    replies = []
    flag = 0
    for stored_name, (data, source_info) in store_bs.items():
        if KeyExpr.intersect(query.key_selector, stored_name):
            flag = 1
            sample = Sample(stored_name, data)
            sample.with_source_info(source_info)
            query.reply(sample)
def to_dpid(n):
    return format(n, "d").zfill(16)

def border_retriever(z):
        global session,zone,border_gw,kind,target
        s_latency = int(round(time.time() * 1000))
        while True:
            replies = session.get(f"/sdn/*/BS/{z}",local_routing=False)
            for reply in replies:
                if reply.data.payload.decode("utf-8") != "None":
                    r = json.loads(reply.data.payload.decode("utf-8"))
                    if int(r[0]["from"]) in border_gw:
                        e_latency = int(round(time.time() * 1000))
                        print(f"BR delay: {e_latency - s_latency}ms")
                        return r[0]
                    else:
                        print(f"reaching zone {z} from zone {r['from']}")
                        z = int(r[0]["from"])
                        break

def request_path(net,src,dst,dpid,gsrc,gdst):
    global paths_cache
    path = []
    out_port = 0
    

    path=nx.shortest_path(net,gsrc,gdst,weight='weight')
    
    
   
    if dpid not in path:
        return path,0
    try:
        if (path.index(dpid) == len(path)-1) and (dpid in border_switch):
            return path,0
        else:
            
            next=path[path.index(dpid)+1]
            out_port=net[dpid][next]['port']
        
            
    except ValueError:
        return path,0
    
    return path,out_port

def instradate(src,dst,net,datapath):
    global kind,target
    dpid = to_dpid(datapath.id)
    src_zone = zone
    dst_zone = zone
    out_port = 0
    s_src = 0
    e_src = 0
    s_dst = 0
    e_dst = 0
    paths_cache.setdefault(src,{})
    paths_cache.setdefault(dst,{})
    if src in paths_cache and dst in paths_cache[src] and paths_cache[src][dst]!=[]:
        path = paths_cache[src][dst]
        if dpid not in path:
            return path,0
        if (dpid in path) and (path.index(dpid) == len(path)-1) and (dpid in border_switch):
            return path,0
        else:
            
            next=path[path.index(dpid)+1]
            out_port=net[dpid][next]['port']
        return path,out_port
    s_dst = int(round(time.time() * 1000))
    if src not in known_hosts:
        
        replies = session.get(f"/sdn/*/hosts/{src}",local_routing=False)
        for reply in replies:
            if reply.data.payload.decode("utf-8") != "None":
                tmp = json.loads(reply.data.payload.decode("utf-8"))
            
                src_zone = tmp["zone"]
        e_dst = int(round(time.time() * 1000))
        print(f"Host discovery delay = {e_dst - s_dst}ms")
    if dst not in known_hosts:
        s_dst = int(round(time.time() * 1000))
        replies = session.get(f"/sdn/*/hosts/{dst}",local_routing=False)
        for reply in replies:
            if reply.data.payload.decode("utf-8") != "None":
                tmp = json.loads(reply.data.payload.decode("utf-8"))
            
                dst_zone = tmp["zone"]
    e_dst = int(round(time.time() * 1000))
    print(f"Host discovery delay = {e_dst - s_dst}ms")
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
        path,out_port = request_path(net,src,dst,dpid,src,dst)
    elif src not in net and dst in net:
        path,out_port = request_path(net,src,dst,dpid,dpid,dst)
        if src_zone not in border_gw:
            r = border_retriever(src_zone)
            border_gw[src_zone] = border_gw[int(r["from"])]
            session.put(basekey + f"/BS/{src_zone}",json.dumps({"via":border_gw[int(r["from"])],"from":r["from"]}))
    elif src in net and dst not in net:
        if dst_zone not in border_gw:
            r = border_retriever(dst_zone)
            border_gw[dst_zone] = border_gw[int(r["from"])]
            session.put(basekey + f"/BS/{dst_zone}",json.dumps({"via":border_gw[int(r["from"])],"from":r["from"]}))
        path,out_port = request_path(net,src,dst,dpid,src,border_gw[dst_zone])
    elif src not in net and dst not in net:
        if src_zone not in border_gw:
            r = border_retriever(src_zone)
            border_gw[src_zone] = border_gw[int(r["from"])]
            session.put(basekey + f"/BS/{src_zone}",json.dumps({"via":border_gw[int(r["from"])],"from":r["from"]}))
        if dst_zone not in border_gw:
            r = border_retriever(dst_zone)
            border_gw[dst_zone] = border_gw[int(r["from"])]
            session.put(basekey + f"/BS/{dst_zone}",json.dumps({"via":border_gw[int(r["from"])],"from":r["from"]}))
        path,out_port = request_path(net,src,dst,dpid,dpid,border_gw[dst_zone])
    paths_cache[src][dst] = path
    if src not in net:
        path.insert(0,border_gw[src_zone])
    paths_cache[dst][src] = path[::-1] 
    print(f"path {path} \n reverse {path[::-1]}")

    return path,out_port

            
            

conf = zenoh.Config()
basekey = "/sdn/zone1"
zenoh.init_logger()
session = zenoh.open(conf)
zones = ["zone2","zone3"]

sub1 = session.subscribe("/sdn/host-pkt/**",topology_update,reliability=Reliability.Reliable, mode=SubMode.Push)

store = {}
sub = session.subscribe(basekey + "/hosts/**", listener, reliability=Reliability.Reliable, mode=SubMode.Push)
queryable = session.queryable(basekey + "/hosts/**", STORAGE, query_handler)
store_bs = {}
sub_bs = session.subscribe(basekey + "/BS/**", listener_bs, reliability=Reliability.Reliable, mode=SubMode.Push)
queryable_bs = session.queryable(basekey + "/BS/**", STORAGE, query_handler_bs)
boosted = []
paths_cache = {}
mac_to_port = {}
modes=["stdnetwork","prioritynetwork"]
mode = modes[0]
net=nx.DiGraph()
fast_net = None
slow_net = None
nodes = {}
links = {}
switches = {}
no_of_nodes = 0
no_of_links = 0
i=0
zone = 1
#fast_links = []
fast_links = [(to_dpid(2),to_dpid(4)),(to_dpid(4),to_dpid(2)),(to_dpid(4),to_dpid(1)),(to_dpid(1),to_dpid(4)),("00:00:00:00:00:01",to_dpid(1)),(to_dpid(1),"00:00:00:00:00:01"),("00:00:00:00:00:02",to_dpid(2)),(to_dpid(2),"00:00:00:00:00:01")]
known_hosts = {"00:00:00:00:00:01":{"zone":1, "ip":"10.0.0.1"},"00:00:00:00:00:02":{"zone":1, "ip":"10.0.0.2"}} #mac:zone
border_switch=[3,4]
session.put(basekey + "/BS/2",json.dumps([{"via":"3","from":"1"},{"via":"4","from":"1"}])) #to zone via dpid from zone s
border_gw = {2:'gateway2'} #to zone %d use gw %d
flows = {}
flag = 0
br_delay = 0
zone_delay = 0
flag_flows = 0
target = Target.BestMatching()






class Controllerz1(app_manager.RyuApp):
    global session

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
        self.add_flow(datapath, 0, match, actions,0)

    def add_flow(self, datapath, priority, match, actions,cookie, buffer_id=None):
        ofproto = datapath.ofproto
        parser = datapath.ofproto_parser

        inst = [parser.OFPInstructionActions(ofproto.OFPIT_APPLY_ACTIONS,
                                             actions)]
        if buffer_id:
            mod = parser.OFPFlowMod(datapath=datapath, buffer_id=buffer_id,cookie=cookie,
                                    priority=priority, match=match,
                                    instructions=inst)
        else:
            mod = parser.OFPFlowMod(datapath=datapath, priority=priority,cookie=cookie,
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
    
    def remove_flows(self):
        global flows
        for d in flows: 
            for f in flows[d]:
                parser = f[0].ofproto_parser
                ofproto = f[0].ofproto
                match = f[2]
                actions = f[3]
                #self.add_flow(0, datapath, 35000, match, actions)
                mod = parser.OFPFlowMod(datapath=f[0], table_id=0, cookie=1,
                command=f[0].ofproto.OFPFC_DELETE, priority=f[1], match=match, out_port= ofproto.OFPP_ANY, out_group=ofproto.OFPG_ANY)
                f[0].send_msg(mod)
        print("Flows C1 puliti")
        flows = {}

    def host_pkt_handler(self,msg):
        global session,basekey,flows,datapaths
        w = msg.data.hex()[28:40]
        w_dest = w[0:2]+':'+w[2:4] + ':'+w[4:6] + ':'+w[6:8] + ':'+w[8:10] + ':'+w[10:12]
        pkt = packet.Packet(msg.data)
        eth = pkt.get_protocols(ethernet.ethernet)[0]
        dst = eth.dst
        src = eth.src
        tmp = json.dumps({"src": src, "dst": w_dest})
        session.put( "/sdn/host-pkt", tmp)
        

            
    @set_ev_cls(ofp_event.EventOFPPacketIn, MAIN_DISPATCHER)
    def _packet_in_handler(self, ev):
        global net
        global known_hosts
        global mac_to_port
        global flows
        global switches
        global border_gw,border_switch,flag,zone,zones,fast_links,br_delay,zone_delay,flag_flows
        global fast_net,slow_net,boosted,paths_cache
        self.topo_discovery()
        s = int(round(time.time() * 1000))
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
        i
        flows.setdefault(dpid,[])
        out_port = 0
        if flag == 0:
            self.update_known_hosts()
            net.add_node('00:00:00:00:00:01')
            net.add_edge(self.to_dpid(1),'00:00:00:00:00:01',port=4)
            net.add_edge('00:00:00:00:00:01',self.to_dpid(1))

            net.add_node('00:00:00:00:00:02')
            net.add_edge(self.to_dpid(2),'00:00:00:00:00:02',port=4)
            net.add_edge('00:00:00:00:00:02',self.to_dpid(2))

            net.add_node("gateway2")
            net.add_edge(self.to_dpid(3),'gateway2',port=4)
            net.add_edge('gateway2',self.to_dpid(3))
            net[self.to_dpid(3)]['gateway2']['weight'] = 1000
            net['gateway2'][self.to_dpid(3)]['weight'] = 1000
            net.add_edge(self.to_dpid(4),'gateway2',port=4)
            net.add_edge('gateway2',self.to_dpid(4))
            net[self.to_dpid(4)]['gateway2']['weight'] = 900
            net['gateway2'][self.to_dpid(4)]['weight'] = 900

            match = parser.OFPMatch(eth_type=0x1111)
            actions = [parser.OFPActionOutput(ofproto.OFPP_CONTROLLER,
                                          ofproto.OFPCML_NO_BUFFER)]
            self.add_flow(datapath, 0, match, actions,0)
        
            
            
            flag = 1
        if flag_flows == 1:
            self.remove_flows()
            flag_flows = 0
        if ev.msg.msg_len < ev.msg.total_len:
            self.logger.debug("packet truncated: only %s of %s bytes",
                              ev.msg.msg_len, ev.msg.total_len)
        
        if eth.ethertype == ether_types.ETH_TYPE_LLDP:
                return
        if eth.ethertype == 4369:
            self.host_pkt_handler(msg)
            return

        self.topo_discovery()
        path = []
        out_port = 0


            
        if mode == modes[0]:
            path,out_port = instradate(src,dst,net,datapath)


        elif src in boosted and dst in boosted:
            path,out_port = instradate(src,dst,fast_net,datapath)
            #print(f"FAST PATH {src}->{dst} {path}")
            for l in range(1,len(path)-2):
                if slow_net.has_edge(str(path[l]),str(path[l+1])):
                    slow_net.remove_edge(str(path[l]),str(path[l+1]))
                    slow_net.remove_edge(str(path[l+1]),str(path[l]))
        else:
            path,out_port = instradate(src,dst,slow_net,datapath)
            #print(f"SLOW PATH {src}->{dst} {path}")

        
            

        actions = [parser.OFPActionOutput(out_port)]
        if out_port != ofproto.OFPP_FLOOD and (flagl==0 and flags==0) and out_port != 0:
            match = parser.OFPMatch(in_port=in_port, eth_dst=dst, eth_src=src)
            if msg.buffer_id != ofproto.OFP_NO_BUFFER:
                self.add_flow(datapath, 1, match, actions,1, msg.buffer_id)
                
            else:
                self.add_flow(datapath, 1, match, actions,1)
                flows[dpid].append([datapath,1,match,actions])
        data = None
        if msg.buffer_id == ofproto.OFP_NO_BUFFER:
            data = msg.data
        out = parser.OFPPacketOut(datapath=datapath, buffer_id=msg.buffer_id,
                                  in_port=in_port, actions=actions, data=data)
        e = int(round(time.time() * 1000))
        print(f"C1 {dpid} Total pkt handler: {e-s}ms ")
        datapath.send_msg(out)

    @set_ev_cls(event.EventSwitchEnter)
    def get_topology_data(self, ev):
        self.topo_discovery()
    


    


        

    