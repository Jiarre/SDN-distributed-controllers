import socket
import netifaces

s = socket.socket(socket.AF_PACKET, socket.SOCK_RAW)
s.bind(("eth0",0x1111,socket.PACKET_BROADCAST))
eth_type = bytes.fromhex("1111")
mac_dst = bytes.fromhex("F" * 12)
mac_src = bytes.fromhex("000000000001")
data = bytes.fromhex("000000000003")


# We're putting together an ethernet frame here, 
# but you could have anything you want instead
# Have a look at the 'struct' module for more 
# flexible packing/unpacking of binary data
# and 'binascii' for 32 bit CRC


pkt = mac_dst + mac_src + eth_type + data
s.send(pkt)
