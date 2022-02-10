# SDN-distributed-controllers
Traineeship project that revolves around an SDN where controllers are distributed and exchange messages with Zenoh protocol


- controllerz*.py: RYU controller for zone* (currently used for testing on all zones)
- network.py: Mininet topology, involving redundancy and lots of loops
- send_pkt.py: script to send a UDP packet with ethertype 0x1111 (used to trigger actions)
- runcontrollers.sh: script to start controllers for all zones

