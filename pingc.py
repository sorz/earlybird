#!/usr/bin/env python3
from socket import socket, AF_INET, SOCK_DGRAM, SO_BINDTODEVICE, SOL_SOCKET
from struct import pack, unpack
from hashlib import blake2b
from hmac import compare_digest
import logging
import time


PSK = b'tW-VPtR4Sq4M2NR-Jo8FSQ'
MAX_DELAY_SECS = 10
TIMEOUT = 3

PKT_MAC_LEN = 16
PKT_TYP_PING = 0
PKT_TYP_STAT = 1

def _digest(pkt):
    mac = blake2b(key=PSK, digest_size=PKT_MAC_LEN)
    mac.update(pkt)
    return mac.digest()

class PingHost:
    def __init__(self, dest, dev=None):
        self._sock = socket(AF_INET, SOCK_DGRAM)
        self._sock.settimeout(TIMEOUT)
        self._dest = dest
        self._pings = set()
        if dev is not None:
            self._sock.setsockopt(SOL_SOCKET, SO_BINDTODEVICE, dev.encode())

    def _send(self, pkt):
        mac = blake2b(key=PSK, digest_size=PKT_MAC_LEN)
        mac.update(pkt)
        pkt += mac.digest()
        self._sock.sendto(pkt, self._dest)

    def _recv(self):
        pkt = self._sock.recv(2048)
        if len(pkt) < PKT_MAC_LEN + 1:
            raise IOError('packet too short, ignored')
        pkt, mac = pkt[:-PKT_MAC_LEN], pkt[-PKT_MAC_LEN:]
        if not compare_digest(_digest(pkt), mac):
            raise IOError('wrong auth digest, ignored')
        t, = unpack('!Q', pkt[1:9])
        if time.time() - t / 1000 > MAX_DELAY_SECS:
            raise IOError('delayed packet, ignored')
        return pkt

    def ping(self):
        t = int(time.time() * 1000)
        pkt = pack('!BQ', PKT_TYP_PING, t)
        self._send(pkt)
        self._pings.add(t % 2**32)

    def stat(self):
        t = int(time.time() * 1000)
        request = pack('!BQ', PKT_TYP_STAT, t)
        pkt = None
        for timeout in (0.2, 0.4, 0.8, 1.6):
            self._sock.settimeout(TIMEOUT * timeout)
            self._send(request)
            try:
                pkt = self._recv()
            except IOError as e:
                logging.debug(e)
            else:
                break
        self._sock.settimeout(TIMEOUT)
        if pkt is None:
            raise IOError('no resposne')
        delays = []
        first_t = -1
        for i in range(17, len(pkt), 6):
            t, delay = unpack('!IH', pkt[i:i+6])
            if t in self._pings:
                delays.append(delay)
                first_t = min(first_t, t)
        sent = sum(1 for t in self._pings if t >= first_t)
        return sent, delays

    def clear(self):
        self._pings.clear()

    def close(self):
        self._sock.close()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()


def main():
    logging.basicConfig(level=logging.DEBUG)
    with PingHost(('192.168.6.65', 3322), 'tun-rpi') as ping:
        ping.ping()
        time.sleep(0.01)
        ping.ping()
        time.sleep(0.01)
        ping.ping()
        time.sleep(0.01)
        ping.ping()
        time.sleep(0.01)
        ping.ping()
        time.sleep(0.1)
        print(ping.stat())


if __name__ == '__main__':
    main()
