"""Resolve an address observed by the API, never from a request body.

The public deployment is behind Cloudflare and Nginx. CF-Connecting-IP is
validated as an IP literal; direct callers fall back to the socket peer.
X-Forwarded-For is intentionally ignored because clients can append spoofed
values to that chain.
"""

import ipaddress
from fastapi import Request


def get_observed_client_ip(request: Request) -> str | None:
    candidate = request.headers.get("cf-connecting-ip")
    if candidate:
        try:
            return str(ipaddress.ip_address(candidate.strip()))
        except ValueError:
            pass

    peer = request.client.host if request.client else None
    if not peer:
        return None
    try:
        return str(ipaddress.ip_address(peer.strip()))
    except ValueError:
        return None
