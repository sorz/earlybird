#!/usr/bin/env python3
from importlib import import_module
from threading import Thread
import logging
import time
import sys

from .iproute import get_peer_addr
from .pingc import PingHost
from .pingd import PingDaemon
from .bird import Bird


def main():
    if len(sys.argv) != 2:
        print(f"Usage: {sys.argv[0]} config", file=sys.stderr)
        sys.exit(1)
    cfg = import_module(sys.argv[1])
    logging.basicConfig(level=cfg.LOGGING_LEVEL)
    if cfg.ENABLE_PINGD:
        pingd = PingDaemon(cfg.PSK, cfg.PINGD_LISTEN)
        pingd_thread = Thread(target=pingd, daemon=True)
        pingd_thread.start()

    bird = Bird(cfg.PINGD_PORT, cfg.INTERFACES, cfg.TEMPLATE_SEARCH_PATHS)
    while True:
        bird.perform_test()
        bird.generate_to(cfg.TEMPLATE, cfg.TEMPLATE_OUTPUT)
        try:
            time.sleep(cfg.TEST_INVERVAL)
        except KeyboardInterrupt:
            logging.info("exit by ^C")
            sys.exit(0)


if __name__ == '__main__':
    main()
