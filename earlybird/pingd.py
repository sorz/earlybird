#!/usr/bin/env python3
from socket import socket, AF_INET, SOCK_DGRAM
from hashlib import blake2b
from hmac import compare_digest
from struct import pack, unpack
import logging
import time


LISTEN = ('0.0.0.0', 3322)
PSK = b'tW-VPtR4Sq4M2NR-Jo8FSQ'
RECORD_KEEP_MAX_SECS = 6 * 3600
RECORD_KEEP_MAX_NUM = 128
MAX_DELAY_SECS = 10

PKT_MAC_LEN = 16
PKT_TYP_PING = 0
PKT_TYP_STAT = 1
PKT_TYP_RESP = 2

sock = None
host_ping_records = dict()

def _digest(pkt):
    mac = blake2b(key=PSK, digest_size=PKT_MAC_LEN)
    mac.update(pkt)
    return mac.digest()


def handle_pkt(pkt, addr):
    if len(pkt) < PKT_MAC_LEN + 1:
        logging.debug('packet too short, ignored')
        return
    pkt, mac = pkt[:-PKT_MAC_LEN], pkt[-PKT_MAC_LEN:]
    if not compare_digest(_digest(pkt), mac):
        logging.warning('wrong auth digest, ignored')
        return
    pkt_type = pkt[0]
    if pkt_type == PKT_TYP_PING:
        handle_ping(pkt, addr)
    elif pkt_type == PKT_TYP_STAT:
        handle_stat(pkt, addr)
    else:
        logging.warning('unknown packet type, ignored')


def filter_records(l):
    t = time.time()
    l = [r for r in l if t - r[0] / 1000 < RECORD_KEEP_MAX_SECS]
    return l[:RECORD_KEEP_MAX_NUM]


def clean_records():
    now = time.time()
    for host, records in host_ping_records.items():
        if now - records[-1][0] > RECORD_KEEP_MAX_SECS:
            del host_ping_records[host]
        else:
            host_ping_records[host] = filter_records(records)


def handle_ping(pkt, addr):
    t, = unpack('!Q', pkt[1:9])
    delta = int(round(time.time() * 1000 - t))
    if not 0 < delta < MAX_DELAY_SECS * 1000:
        logging.warning(f'unaccepted delta time {delta}ms, ignored')
        return
    logging.debug('ping from %s: %sms', addr, delta)
    l = host_ping_records.get(addr, [])
    l.append((t, delta))
    host_ping_records[addr] = filter_records(l)


def handle_stat(pkt, addr):
    clean_records()
    resp = bytearray([PKT_TYP_RESP])
    resp += pack('!Q', int(time.time() * 1000))
    resp += pkt[1:9]
    lst = host_ping_records.get(addr, [])
    for t, delta in lst:
        t = t % (2 ** 32)
        resp += pack('!IH', t, delta)
    resp += _digest(resp)
    sock.sendto(resp, addr)


def main():
    global sock
    logging.basicConfig(level=logging.DEBUG)
    sock = socket(AF_INET, SOCK_DGRAM)
    sock.bind(LISTEN)
    while True:
        pkt, addr = sock.recvfrom(1024)
        handle_pkt(pkt, addr)

if __name__ == '__main__':
    main()
