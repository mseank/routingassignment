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
        #this will be a dictionary of tuples, distance and which neighbor path to use
        #this way, if THAT neighbor's path changes, I know I have to update mine
        self.distance_vectors = {}
        self.distance_vectors[node.hostname] = (0,node.hostname)
        #when it begins, we will set timer to timeout
        self.timer = Sim.scheduler.add(delay=self.timeout, event='broadcast', handler=self.broadcast)
        #also need a dictionary of timers for neighbors
        self.neighbor_timers = {}
        print(self.node.hostname + ': ' + str(self.distance_vectors))

    def receive_packet(self, packet):
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
        #this var is so I know which way I'm going for shortest path
        sending_node = ""
        #not super efficient, but I need to get sending_node before doing the other stuff, 
        # so I'll loop through one initial time
        for k,v in vector_list.items():
            if(int(v[0]) == 0):
                #we know this is the sending node because only the sender can be 0 distance from self
                sending_node = k

        """Now I need to check and see if I have any pathways through this node. Check them all and
        if any of them change, change. If they disappear, delete the path from mine, as well."""
        for k in self.distance_vectors.keys():
            #if it went through this sending_node before, check for a change
            if(self.distance_vectors[k][1] == sending_node):
                #if this previously held distance is still in the sending node, check for a change.
                # if there's no change, don't worry about it.
                if(k in vector_list and int(vector_list[k][0]) != int(self.distance_vectors[k][0])-1):
                    #then set the value to the new value... it'll update later if need be
                    updated_distance = int(vector_list[k][0]+1)
                    dist_tuple = (updated_distance,sending_node)
                    self.distance_vectors[k] = dist_tuple
                    print(self.node.hostname + ': ' + str(self.distance_vectors))
                #if it's no longer in the vector list, delete it, because the path is compromised
                elif(k not in vector_list):
                    del self.distance_vectors[k]

        """For making the 3 time check. Set a timer when received each time, set to run out in
        three self.timeouts. Also when it already exists in the distance_vector dictionary, be sure
        to cancel the previous event timer."""
        for k, v in vector_list.items():
            #check if v == 0, to signify neighbor. if yes, 
            if(int(v[0]) == 0):
                #then go in here and if it already exists, cancel it
                if(k in self.neighbor_timers):
                    if(self.neighbor_timers[k]):
                        Sim.scheduler.cancel(self.neighbor_timers[k])
                    new_timer = Sim.scheduler.add(delay=3*self.timeout, event=k, handler=self.handle_dropped_link)
                    self.neighbor_timers[k] = new_timer
                else:
                    new_timer = Sim.scheduler.add(delay=3*self.timeout, event=k, handler=self.handle_dropped_link)
                    self.neighbor_timers[k] = new_timer
                #then re-add it
            #now we do the adding distance vector stuff
            if k in self.distance_vectors and int(v[0]) <= (int(self.distance_vectors[k][0])-2):
                self.distance_vectors[k] = (int(v[0])+1,sending_node)
                print(self.node.hostname + ': ' + str(self.distance_vectors))
            #I'm worried about count-to-infinity, but if the neighbor is the same, but the distance
            #  changes, then I should change, as well, because this means a change in topology
            #if it's not in it, obviously add it
            elif k not in self.distance_vectors:
                #add the distance vector
                self.distance_vectors[k] = (int(v[0])+1,sending_node)
                print(self.node.hostname + ': ' + str(self.distance_vectors))
                print("")
                #add the neighbor timer nonsense to the neighbor_timer dict
                #if(int(v[0]) == 0):
                    #new_timer = Sim.scheduler.add(delay=3*self.timeout, event=k, handler=self.handle_dropped_link)
                    #self.neighbor_timers[k] = new_timer
        if not self.timer:
            self.timer = Sim.scheduler.add(delay=self.timeout, event='broadcast', handler=self.broadcast)

    def handle_dropped_link(self,event):
        print("timed out on a dropped link!")
        #set the timer to none
        self.neighbor_timers[event] = None
        #I think I should then zero out the distance_vectors. Not sure if this is that efficient,
        # but it seems to be the best way since there's no way of knowing what paths have been affected
        # easily
        self.distance_vectors = {}
        self.distance_vectors[self.node.hostname] = (0,self.node.hostname)

def printstuff(event):
    print("COMING BACK UP")

def main():
    # parameters
    Sim.scheduler.reset()
    Sim.set_debug(True)

    # setup network
    net = Network('../../../networks/experiment2.txt')

    # get nodes
    n1 = net.get_node('n1')
    n2 = net.get_node('n2')
    n3 = net.get_node('n3')
    n4 = net.get_node('n4')
    n5 = net.get_node('n5')
    """n6 = net.get_node('n6')
    n7 = net.get_node('n7')
    n8 = net.get_node('n8')
    n9 = net.get_node('n9')
    n10 = net.get_node('n10')
    n11 = net.get_node('n11')
    n12 = net.get_node('n12')
    n13 = net.get_node('n13')
    n14 = net.get_node('n14')
    n15 = net.get_node('n15')"""

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
    """b6 = BroadcastApp(n6)
    n6.add_protocol(protocol="dvrouting", handler=b6)
    b7 = BroadcastApp(n7)
    n7.add_protocol(protocol="dvrouting", handler=b7)
    b8 = BroadcastApp(n8)
    n8.add_protocol(protocol="dvrouting", handler=b8)
    b9 = BroadcastApp(n9)
    n9.add_protocol(protocol="dvrouting", handler=b9)
    b10 = BroadcastApp(n10)
    n10.add_protocol(protocol="dvrouting", handler=b10)
    b11 = BroadcastApp(n11)
    n11.add_protocol(protocol="dvrouting", handler=b11)
    b12 = BroadcastApp(n12)
    n12.add_protocol(protocol="dvrouting", handler=b12)
    b13 = BroadcastApp(n13)
    n13.add_protocol(protocol="dvrouting", handler=b13)
    b14 = BroadcastApp(n14)
    n14.add_protocol(protocol="dvrouting", handler=b14)
    b15 = BroadcastApp(n15)
    n15.add_protocol(protocol="dvrouting", handler=b15)

    #test taking down a link, experiment 3
    Sim.scheduler.add(delay=360, event=None, handler=n8.get_link('n9').down)
    Sim.scheduler.add(delay=360, event=None, handler=n9.get_link('n8').down)

    #and bring it back up
    Sim.scheduler.add(delay=720, event=None, handler=printstuff)
    Sim.scheduler.add(delay=720, event=None, handler=n8.get_link('n9').up)
    Sim.scheduler.add(delay=720, event=None, handler=n9.get_link('n8').up)"""

    #experiment 2 take down a link
    Sim.scheduler.add(delay=120, event=None, handler=n1.get_link('n2').down)
    Sim.scheduler.add(delay=120, event=None, handler=n2.get_link('n1').down)

    # run the simulation
    Sim.scheduler.run()

if __name__ == '__main__':
    main()

