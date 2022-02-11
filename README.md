# SDN-distributed-controllers
Traineeship project that revolves around an SDN where controllers are distributed and exchange messages with Zenoh protocol


- controllerz*.py: RYU controller for zone* (currently used for testing on all zones)
- network.py: Mininet topology, involving redundancy and lots of loops
- send_pkt.py: script to send a UDP packet with ethertype 0x1111 (used to trigger actions)
- runcontrollers.sh: script to start controllers for all zones

# Topology
The used topology is the one shown in the picture below, it is thinked to add redundancy and to have alternative paths between each pair of hosts or switches

![This is an image](/Topology.png)
# How does it work?
Every controller manage a different group of switches, this group will be called a Zone. Controllers managing their Zones know the topology of their own Zone (through discovery methods) and hosts from all the network. Some switches in a Zone are called "border switches" because they are part of two different Zones, this comes handy when routing packets

# Routing packets
Since it isn't possible to use STP protocol and discover the entire topology of the network without flooding and saturating the network, i opted for a Best-Path approach. 
Every Zone know their topology and all the hosts in the network (and for every hosts their respective zone) so the pseudocode for routing a packet is

```
if src and dst are in the same zone
    bestpath(src,dst)
if src and dst are not in the same zone, but the switch and the dest are
    bestpath(borderswitchdst,dst)
if src and dst are not in the same zone, but the switch and the src are
    bestpath(src,borderswitchsrc)
if neither src or dst are in the same zone as the switch
    bestpath(borderswitchsrc,borderswitchdst)
```
With this implementation routing through zones is transparent for all hosts:

E.G (Following the topology illustration) h1 is in Zone1 and h3 is in Zone3, if h1 tries to ping h3 the controller knows that they are in different zones so it routes the packets to the borderswitch relative to Zone3 (Note that one borderswitch could lead to more than one Zone).
Once the packet is in the borderswitch it will be handled by other zones (like Zone2 for instance) that search for the best path to cross the Zone from one borderswitch to another.
Finally the packet arrives in Zone3 where the controller will calculate the bestpath between the borderswitch and the dst 

# Messages between Controllers
To let the Controllers communicate with eachother I used the Zenoh protocol. Zenoh communication are used for control messages and updates on topology



