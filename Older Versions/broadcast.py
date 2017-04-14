from __future__ import print_function

import sys

sys.path.append('../../../')

from src.sim import Sim
from src.packet import Packet

from networks.network import Network


class BroadcastApp(object):
    def __init__(self, node):
        self.node = node
        self.timeout = 30
        self.distance_vectors = {}
        self.distance_vectors[node.hostname] = 0
        #when it begins, we will set timer to timeout
        self.timer = Sim.scheduler.add(delay=self.timeout, event='broadcast', handler=self.broadcast)
        print(self.node.hostname + ': ' + str(self.distance_vectors))

    def receive_packet(self, packet):
        #print(Sim.scheduler.current_time(), self.node.hostname, packet.ident)
        if(packet.protocol == 'dvrouting'):
            self.handle_distance_vector(packet)

    def broadcast(self, event):
        self.timer = Sim.scheduler.add(delay=self.timeout, event='broadcast', handler=self.broadcast)
        p = Packet(
            destination_address=0,
            ttl=1, protocol='dvrouting', body=self.distance_vectors)
        Sim.scheduler.add(delay=0, event=p, handler=self.node.send_packet)

    def handle_distance_vector(self, packet):
    	#step1 - check if sending source has entry in my list of vectors
    	#if yes: check through and see if anything is at least 2 less than what I have
    	#    if any of them are less than 2 of what I have, that means the path is shorter
    	#else: add everything to my list +1
        vector_list = packet.body
        for k, v in vector_list.items():
            if k in self.distance_vectors and int(v) <= (int(self.distance_vectors[k])-2):
            	self.distance_vectors[k] = int(v)+1
            	print(self.node.hostname + ': ' + str(self.distance_vectors))
            elif k not in self.distance_vectors:
            	self.distance_vectors[k] = int(v)+1
            	print(self.node.hostname + ': ' + str(self.distance_vectors))
        if not self.timer:
            self.timer = Sim.scheduler.add(delay=self.timeout, event='broadcast', handler=self.broadcast)

def main():
    # parameters
    Sim.scheduler.reset()
    Sim.set_debug(True)

    # setup network
    net = Network('../../../networks/experiment1.txt')

    # get nodes
    n1 = net.get_node('n1')
    n2 = net.get_node('n2')
    n3 = net.get_node('n3')
    n4 = net.get_node('n4')
    n5 = net.get_node('n5')

    # setup broadcast application
    b1 = BroadcastApp(n1)
    n1.add_protocol(protocol="dvrouting", handler=b1)
    b2 = BroadcastApp(n2)
    n2.add_protocol(protocol="dvrouting", handler=b2)
    b3 = BroadcastApp(n3)
    n3.add_protocol(protocol="dvrouting", handler=b3)
    b4 = BroadcastApp(n4)
    n4.add_protocol(protocol="dvrouting", handler=b4)
    b5 = BroadcastApp(n5)
    n5.add_protocol(protocol="dvrouting", handler=b5)



    # run the simulation
    Sim.scheduler.run()

if __name__ == '__main__':
    main()
