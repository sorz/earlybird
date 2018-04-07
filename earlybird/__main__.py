#!/usr/bin/env python3
from importlib import import_module
import sys

from .iproute import get_peer_addr
from .pingc import PingHost


def main():
    if len(sys.argv) != 2:
        print(f"Usage: {sys.argv[0]} config", file=sys.stderr)
        sys.exit(1)
    cfg = import_module(sys.argv[1])
    print(cfg.PSK)

if __name__ == '__main__':
    main()
