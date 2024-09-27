#!/usr/bin/env python3

# Source: https://github.com/O-X-L/nftables_addon_dns
# Copyright (C) 2024  Pascal Rath
# License: GNU General Public License v3.0

from socket import getaddrinfo, gaierror, AF_INET, AF_INET6


def _sorted(data: list) -> list:
    data.sort()
    return data


def resolve(name: str, ip4: bool) -> list:
    try:
        raw = getaddrinfo(name, None, AF_INET if ip4 else AF_INET6)
        # pylint: disable=R1718
        return _sorted(list(set([r[4][0] for r in raw])))

    except (gaierror, UnicodeError):
        return []


def resolve_ipv4(name: str) -> list:
    return resolve(name, True)


def resolve_ipv6(name: str) -> list:
    return resolve(name, False)
