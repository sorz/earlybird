import logging

LOGGING_LEVEL = logging.DEBUG
PSK = b'tW-VPtR4Sq4M2NR-Jo8FSQ'

ENABLE_PINGD = True
PINGD_LISTEN = ('0.0.0.0', 3322)

TEST_INVERVAL = 600
PINGD_PORT = PINGD_LISTEN[1]
INTERFACES = [
    # must be a peer-to-peer interface (e.g. OpenVPN)
    # have to change the source if not in that case.
    'tun-rpi',
]
TEMPLATE = 'bird.conf'
TEMPLATE_SEARCH_PATHS = ['./', './templates/']
TEMPLATE_OUTPUT = './output.conf'
BIRD_RELOAD_CMD=['/usr/bin/birdc', 'configure']
