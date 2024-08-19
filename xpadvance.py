# -*- coding: utf-8 -*-
#!/usr/bin/env python3
 
import socket
import struct
import time
import threading
from libhelper import find_xp


class XPDataRefs:
    def __init__(self):
        # execute our find_my_plane function which calls find_xp methof inside our libhelper class
        # we need to know where our X-Plane server are running
        self.beacon = self.find_my_xplane()
 
    def find_my_xplane(self, wait=3.0):
        # this will just call our find_xp function inside our libhelper class
        return find_xp(wait)

    def default_handler(self, command, channel, index, value):
        # print('{}, {}: {} - {}'.format(command, index, value, channel))
        pass

    def subscribe(self, command, channel, index, frequency=10):
        '''
        Parameters:
        command = b'RREF'
        frequency = 1                               # number of request/data per seconds
        index = 1                                   # unique identifier per channel
        channel = b'sim/flightmodel/forces/g_axil'

        The string `<4sxii400s` describes how to pack the data:

        `<`				little endian (i.e., least significant byte in the lowest memory position)
        `4s`			a 4-byte object, commonly string, 'RREF', expressed as a bytes: b'RREF'.
        `x`				a null byte, or 0x00. X-Plane is looking for a null-terminated 4-character string & this encodes the null value.
        `i`				a 4-byte integer
        `i`				another 4-byte integer (you could also combine these as `2i`, which consumes two integer arguments)
        `400s`			a 400-byte object. Note that Python pads and zero-fills to fit 400 bytes.
        '''
        # need to create or instantiate our socket
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        # we need to construct our message package before we send it
        msg = struct.pack(
            '<4sxii400s', command, 
            frequency, index, channel
        )
        # we need to pass the IP and PORT from our self.beacon variable that was initialized earlier
        # then send the message
        s.sendto(msg, (self.beacon['ip'], self.beacon['port']))
        return s

    def unsubscribe(self, sock, command, channel, index):
        '''
        Parameters:
        sockt = socket instance that was created
        command = b'RREF'
        index = 1                                   # index that was used
        channel = b'sim/flightmodel/forces/g_axil'

        The message package are the same with our subscribe function
        the only difference is the frequency, we are forcing it to zero (0)
        because we want to tell XPlane to stop sending
        '''
        msg = struct.pack(
            '<4sxii400s', command, 
            0, index, channel
        )
        # we need to pass the IP and PORT from our self.beacon variable that was initialized earlier
        # then send the message
        sock.sendto(msg, (self.beacon['ip'], self.beacon['port']))

    def read_udp(self, channel, index, frequency, callback=None):
        '''
        Parameters:
        frequency = 1                               # number of request/data per seconds
        index = 1                                   # unique identifier per channel
        channel = b'sim/flightmodel/forces/g_axil'
        callback = [optional]

        This function will infinitely receive or read data from the socket
        '''
        command_header = b'RREF'
        sock = self.subscribe(command_header, channel, index, frequency)
        while True:
            data, addr = sock.recvfrom(1024)
            if data:
                header = data[0:4]
                if header == command_header:
                    idx, value = struct.unpack('<if', data[5:13])
                    if callback:
                        # execute the user supplied callback function
                        # we can also run/execute the callback function on another thread if we want it.
                        # for now will just synchronously execute it
                        callback(header, channel, idx, value)
                    else:
                        # else just execute our default callback
                        self.default_handler(header, channel, idx, value)
            else:
                # if we don't received anything, lets give enough time for the CPU
                # to handle other things, the delay should be fast enough so it wont lag
                # when data are already available
                time.sleep(10/1000)     # 10 milliseconds is fast enough


if __name__ == '__main__':
    # This is just a sample callback function
    # you can do whatever you want or need
    def sample_callback(command, channel, index, value):
        '''
        Sample printed messages:    
        ==> b'RREF', 1: 2.2934160369914025e-05 - b'sim/flightmodel/position/local_vx'
        ==> b'RREF', 4: -0.02114936336874962 - b'sim/flightmodel/forces/g_side'
        ==> b'RREF', 5: 4.535009860992432 - b'sim/flightmodel/forces/fside_aero'
        ==> b'RREF', 3: -0.03224347531795502 - b'sim/flightmodel/forces/g_axil'
        ==> b'RREF', 6: -6.190376281738281 - b'sim/flightmodel/forces/fnrml_aero'
        ==> b'RREF', 2: 0.9992488026618958 - b'sim/flightmodel/forces/g_nrml'
        ==> b'RREF', 7: -5.120068073272705 - b'sim/flightmodel/forces/faxil_aero'
        ==> b'RREF', 7: -5.116205215454102 - b'sim/flightmodel/forces/faxil_aero'
        ==> b'RREF', 5: 4.514730453491211 - b'sim/flightmodel/forces/fside_aero'
        ==> b'RREF', 6: -6.212045192718506 - b'sim/flightmodel/forces/fnrml_aero'
        '''
        # for the purpose of this tutorial we will just print them
        print('==> {}, {}: {} - {}'.format(command, index, value, channel))

    # Instantiate our class object XPDataRefs 
    xp = XPDataRefs()

    # let's prepare our subscription channels and parameters
    # XPlane datarefs:
    # https://developer.x-plane.com/datarefs/
    # https://github.com/der-On/X-Plane-Dataref-Search/blob/master/dist/DataRefs.txt
    data_refs = (
        (
            b'sim/flightmodel/position/true_phi',   # channel
            0,                                      # index
            1,                                      # frequency
                                                    # optional [callback], this will use our default callback
        ),
        (
            b'sim/flightmodel/position/local_vx',   # channel
            1,                                      # index
            1,                                      # frequency
            sample_callback                         # optional [callback], this will use our provided callback
        ),
        (
            b'sim/flightmodel/forces/g_nrml',
            2,
            1,
            sample_callback
        ),
        (
            b'sim/flightmodel/forces/g_axil',
            3,
            1,
            sample_callback
        ),
        (
            b'sim/flightmodel/forces/g_side',
            4,
            1,
            sample_callback
        ),
        (
            #Newtons	Aerodynamic forces - sideways - ACF X
            b'sim/flightmodel/forces/fside_aero',   
            5,
            1,
            sample_callback
        ),
        (
            #Newtons	Aerodynamic forces - upward - ACF Y
            b'sim/flightmodel/forces/fnrml_aero',	    
            6,
            1,
            sample_callback
        ),
        (
            #Newtons	Aerodynamic forces - backward - ACF Z
            b'sim/flightmodel/forces/faxil_aero',       
            7,
            1,
            sample_callback
        )
    )

    # Execute all the subscription inside the tuple
    for s in data_refs:
        # this thread will execute read_udp function and pass the parameters to it
        t = threading.Thread(target=xp.read_udp, args=s)
        t.start()

    # We need to block our main script
    # This loop does nothing but give time for the CPU to handle other things
    while True:
        time.sleep(1)
