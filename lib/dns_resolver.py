#!/usr/bin/env python3

# Source: https://github.com/superstes/python3-resolver
# Copyright (C) 2023  René Pascal Rath
# License: GNU General Public License v3.0

from socket import getaddrinfo, gaierror
from ipaddress import IPv4Address, AddressValueError

DUMMY_PORT = 80


def _is_ipv4_address(i: str) -> bool:
    try:
        IPv4Address(i)
        return True

    except AddressValueError:
        return False


def _sorted(data: list) -> list:
    data.sort()
    return data


def resolve(name: str) -> list:
    try:
        raw = getaddrinfo(name, DUMMY_PORT)
        # pylint: disable=R1718
        return _sorted(list(set([r[4][0] for r in raw])))

    except (gaierror, UnicodeError):
        return []


def resolve_ipv4(name: str) -> list:
    return _sorted([i for i in resolve(name) if _is_ipv4_address(i)])


def resolve_ipv6(name: str) -> list:
    return _sorted([i for i in resolve(name) if not _is_ipv4_address(i)])
