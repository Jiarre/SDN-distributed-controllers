import socket
import netifaces


s = socket.socket(socket.AF_PACKET, socket.SOCK_RAW)
if (len(socket.if_nameindex()) > 2):
		for i in socket.if_nameindex():
			print(str(i[0]) + " -> " + i[1])
		idx = int(input("Choose the index of the interface where send the packet: "))
else:
		# Speed up in best case scenarios, excluding loopback interface
		idx = 2
interface = socket.if_indextoname(idx)
dst = input("Provide the complete MAC address: ")
s.bind((interface,0x1111,socket.PACKET_BROADCAST))
eth_type = bytes.fromhex("1111")
mac_dst = bytes.fromhex("F" * 12)
mac_src = s.getsockname()[4]
data = bytes.fromhex(dst.replace(':', ''))


# We're putting together an ethernet frame here, 
# but you could have anything you want instead
# Have a look at the 'struct' module for more 
# flexible packing/unpacking of binary data
# and 'binascii' for 32 bit CRC


pkt = mac_dst + mac_src + eth_type + data
s.send(pkt)
