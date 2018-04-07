#!/usr/bin/env python3
from socket import socket, AF_INET, SOCK_DGRAM
from hashlib import blake2b
from hmac import compare_digest
from struct import pack, unpack
import logging
import time


RECORD_KEEP_MAX_SECS = 6 * 3600
RECORD_KEEP_MAX_NUM = 128
MAX_DELAY_SECS = 10

PKT_MAC_LEN = 16
PKT_TYP_PING = 0
PKT_TYP_STAT = 1
PKT_TYP_RESP = 2

class PingDaemon:
    def __init__(self, psk):
        self._psk = psk
        self._sock = None
        self._host_ping_records = dict()

    def run_forever(self, listen=('0.0.0.0', 3322)):
        self._sock = socket(AF_INET, SOCK_DGRAM)
        self._sock.bind(listen)
        while True:
            pkt, addr = self._sock.recvfrom(1024)
            self._handle_pkt(pkt, addr)

    def _digest(self, pkt):
        mac = blake2b(key=self._psk, digest_size=PKT_MAC_LEN)
        mac.update(pkt)
        return mac.digest()

    def _handle_pkt(self, pkt, addr):
        if len(pkt) < PKT_MAC_LEN + 1:
            logging.debug('packet too short, ignored')
            return
        pkt, mac = pkt[:-PKT_MAC_LEN], pkt[-PKT_MAC_LEN:]
        if not compare_digest(self._digest(pkt), mac):
            logging.warning('wrong auth digest, ignored')
            return
        pkt_type = pkt[0]
        if pkt_type == PKT_TYP_PING:
            self._handle_ping(pkt, addr)
        elif pkt_type == PKT_TYP_STAT:
            self._handle_stat(pkt, addr)
        else:
            logging.warning('unknown packet type, ignored')

    def _clean_records(self):
        now = time.time()
        for host, records in self._host_ping_records.items():
            if now - records[-1][0] > RECORD_KEEP_MAX_SECS:
                del self._host_ping_records[host]
            else:
                self._host_ping_records[host] = _filter_records(records)

    def _handle_stat(self, pkt, addr):
        self._clean_records()
        resp = bytearray([PKT_TYP_RESP])
        resp += pack('!Q', int(time.time() * 1000))
        resp += pkt[1:9]
        lst = self._host_ping_records.get(addr, [])
        for t, delta in lst:
            t = t % (2 ** 32)
            resp += pack('!IH', t, delta)
        resp += self._digest(resp)
        self._sock.sendto(resp, addr)

    def _handle_ping(self, pkt, addr):
        t, = unpack('!Q', pkt[1:9])
        delta = int(round(time.time() * 1000 - t))
        if not 0 < delta < MAX_DELAY_SECS * 1000:
            logging.warning(f'unaccepted delta time {delta}ms, ignored')
            return
        logging.debug('ping from %s: %sms', addr, delta)
        l = self._host_ping_records.get(addr, [])
        l.append((t, delta))
        self._host_ping_records[addr] = _filter_records(l)

def _filter_records(l):
    t = time.time()
    l = [r for r in l if t - r[0] / 1000 < RECORD_KEEP_MAX_SECS]
    return l[:RECORD_KEEP_MAX_NUM]

def main():
    logging.basicConfig(level=logging.DEBUG)
    PingDaemon(b'test123').run_forever()

if __name__ == '__main__':
    main()
