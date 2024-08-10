#!/usr/bin/env python3

# Source: https://github.com/O-X-L/nftables_addon_dns
# Copyright (C) 2024 Rath Pascal
# License: MIT

from dns_resolver import resolve_ipv4, resolve_ipv6
from util import validate_and_write, load_config, format_var

PROCESS_IPv6 = True

# paths are set in util (shared between addons)
CONFIG_FILE = 'dns.json'
CONFIG_FILE_KEY = 'dns'
OUT_FILE = 'dns.nft'

CONFIG = load_config(file=CONFIG_FILE, key=CONFIG_FILE_KEY)

if CONFIG is None or len(CONFIG) == 0:
    raise SystemExit(f"Config file could not be loaded: '{CONFIG_FILE}'!")

lines = []
for var, hostnames in CONFIG.items():
    if not isinstance(hostnames, list):
        hostnames = [hostnames]

    values_v4 = []
    values_v6 = []

    for hostname in hostnames:
        values_v4.extend(resolve_ipv4(hostname))

        if PROCESS_IPv6:
            values_v6.extend(resolve_ipv6(hostname))

    lines.append(
        format_var(
            name=var,
            data=values_v4,
            version=4,
        )
    )

    if PROCESS_IPv6:
        lines.append(
            format_var(
                name=var,
                data=values_v6,
                version=6,
            )
        )

validate_and_write(lines=lines, file=OUT_FILE, key=CONFIG_FILE_KEY)
