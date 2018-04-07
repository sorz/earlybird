import logging

from .iproute import get_peer_addr
from .pingc import PingHost


class Bird:
    
    def __init__(self, port, ifnames):
        self._ifname_addr = dict()
        self._ifname_stat = dict()
        for ifname in ifnames:
            self.add_interface(ifname, port=port)

    def add_interface(self, ifname, addr=None, port=3322):
        if addr is None:
            addr = get_peer_addr(ifname)
        self._ifname_addr[ifname] = (addr, port)
        logging.debug("interface %s (%s:%s) added", ifname, addr, port)

    def perform_test(self):
        for ifname, (addr, port) in self._ifname_addr.items():
            if addr is None:
                # TODO: update addr
                continue
            with PingHost((addr, port), ifname) as ping:
                try:
                    stat = ping.perform_test()
                    self._ifname_stat[ifname] = stat
                    logging.debug("stat on %s updated: %s", ifname, stat)
                except IOError as err:
                    self._ifname_stat[ifname] = None
                    logging.warning("fail to test %s: %s", ifname, err)
                
    def generate(self, template):
        pass