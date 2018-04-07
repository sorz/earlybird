#!/usr/bin/env python3
from pyroute2 import IPRoute


IP = IPRoute()

def get_peer_addr(ifname):
    """Return the peer address of given peer interface.
    None if address not exist or not a peer-to-peer interface.
    """
    for addr in IP.get_addr(label=ifname):
        attrs = dict(addr.get('attrs', []))
        if 'IFA_ADDRESS' in attrs:
            return attrs['IFA_ADDRESS']


if __name__ == '__main__':
    print(get_peer_addr('tun-rpi'))
