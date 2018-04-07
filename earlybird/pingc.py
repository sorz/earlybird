#!/usr/bin/env python3
from socket import socket, AF_INET, SOCK_DGRAM, SO_BINDTODEVICE, SOL_SOCKET
from struct import pack, unpack
from hashlib import blake2b
from hmac import compare_digest
from statistics import mean, stdev
from collections import namedtuple
import logging
import time


MAX_DELAY_SECS = 10
TIMEOUT = 3

PKT_MAC_LEN = 16
PKT_TYP_PING = 0
PKT_TYP_STAT = 1

TestResult = namedtuple('TestResult', ['loss', 'avg', 'max', 'min', 'stdev'])


class PingHost:
    def __init__(self, psk, dest, dev=None):
        self._sock = socket(AF_INET, SOCK_DGRAM)
        self._sock.settimeout(TIMEOUT)
        self._psk = psk
        self._dest = dest
        self._pings = set()
        if dev is not None:
            self._sock.setsockopt(SOL_SOCKET, SO_BINDTODEVICE, dev.encode())

    def _digest(self, pkt):
        mac = blake2b(key=self._psk, digest_size=PKT_MAC_LEN)
        mac.update(pkt)
        return mac.digest()

    def _send(self, pkt):
        pkt += self._digest(pkt)
        self._sock.sendto(pkt, self._dest)

    def _recv(self):
        pkt = self._sock.recv(2048)
        if len(pkt) < PKT_MAC_LEN + 1:
            raise IOError('packet too short, ignored')
        pkt, mac = pkt[:-PKT_MAC_LEN], pkt[-PKT_MAC_LEN:]
        if not compare_digest(self._digest(pkt), mac):
            raise IOError('wrong auth digest, ignored')
        t, = unpack('!Q', pkt[1:9])
        if time.time() - t / 1000 > MAX_DELAY_SECS:
            raise IOError('delayed packet, ignored')
        return pkt

    def ping(self):
        """Send a ping to remote, return without waiting."""
        t = int(time.time() * 1000)
        pkt = pack('!BQ', PKT_TYP_PING, t)
        self._send(pkt)
        self._pings.add(t % 2**32)

    def perform_test(self, n=5, interval=0.1):
        """Perform `n`-times pings and return (loss %, avg, max, min,
        stdev) in msec.
        """
        for _ in range(n):
            self.ping()
            time.sleep(interval)
        time.sleep(interval)
        n_sent, ts = self.stat()
        loss = (len(ts) - n_sent) / n_sent
        return TestResult(loss, mean(ts), max(ts), min(ts), stdev(ts))

    def stat(self):
        """Request statistics from remote. Return (n, [t1, .., tm]),
        where n is number of pings sent, t is delay in msec, m <= n.
        May raise IOError if remote don't response.
        """
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
    with PingHost('test123', ('192.168.6.65', 3322), 'tun-rpi') as ping:
        print(ping.perform_test(10, 0.01))


if __name__ == '__main__':
    main()
