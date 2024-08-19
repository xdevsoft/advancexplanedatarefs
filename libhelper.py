# -*- coding: utf-8 -*-
#!/usr/bin/env python3

import socket
import struct
import platform


def find_xp(self, wait=3.0):
        """
        Waits for X-Plane to startup, and returns IP (and other) information
        about the first running X-Plane found.

        Parameter:
        wait        - floating point, maximum seconds to wait for beacon.
        """
        # Set up to listen for a multicast beacon
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

        MULTICAST_IP = '239.255.1.1'    # Standard multicast group
        MULTICAST_PORT = 49707          # (MULTICAST_PORT was 49000 for XPlane10)
        
        if platform.system() == 'Windows':
            # Windows doesn't need the IP
            sock.bind(('', MULTICAST_PORT))
        else:
            sock.bind((MULTICAST_IP, MULTICAST_PORT))
        
        mreq = struct.pack("=4sl", socket.inet_aton(MULTICAST_IP), socket.INADDR_ANY)
        sock.setsockopt(socket.IPPROTO_IP, socket.IP_ADD_MEMBERSHIP, mreq)

        if wait > 0:
            # set the socket timeout
            sock.settimeout(wait)

        beacon_data = {}
        while not beacon_data:
            try:
                packet, sender = sock.recvfrom(15000)
                header = packet[0:5]

                if header == b"BECN\x00":
                    # header matches, so looks like the X-Plane beacon
                    # * Data
                    data = packet[5:21]

                    # X-Plane documentation says:
                    # struct becn_struct
                    # {
                    #    uchar beacon_major_version;    // 1 at the time of X-Plane 10.40, 11.55
                    #    uchar beacon_minor_version;    // 1 at the time of X-Plane 10.40, 2 for 11.55
                    #    xint application_host_id;      // 1 for X-Plane, 2 for PlaneMaker
                    #    xint version_number;           // 104014 is X-Plane 10.40b14, 115501 is 11.55r2
                    #    uint role;                     // 1 for master, 2 for extern visual, 3 for IOS
                    #    ushort port;                   // port number X-Plane is listening on
                    #    xchr    computer_name[500];    // the hostname of the computer
                    #    ushort  raknet_port;           // port number the X-Plane Raknet clinet is listening on
                    # };

                    (beacon_major_version, beacon_minor_version, application_host_id,
                    xplane_version_number, role, port) = struct.unpack("<BBiiIH", data)

                    computer_name = packet[21:]  # Python3, these are bytes, not a string
                    computer_name = computer_name.split(b'\x00')[0]  # get name upto, but excluding first null byte
                    (raknet_port, ) = struct.unpack('<H', packet[-2:])

                    if all([beacon_major_version == 1,
                            beacon_minor_version == 2,
                            application_host_id == 1]):
                        beacon_data = {
                            'ip': sender[0],
                            'port': port,
                            'hostname': computer_name.decode('utf-8'),
                            'xplane_version': xplane_version_number,
                            'role': role,
                            'raknet_port': raknet_port
                        }

            except socket.timeout:
                print("Could not find any running xplane instance in network.")

        sock.close()
        return beacon_data


if __name__ == '__main__':
    print(find_xp())