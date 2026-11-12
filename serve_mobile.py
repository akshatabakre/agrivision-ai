"""Start the AgriVision API for the Android app.

Prints the address to type into the app (Settings -> Server address), then
serves the REST API on all network interfaces, port 8000.

    python serve_mobile.py          (or double-click START_MOBILE_SERVER.bat)
"""
from __future__ import annotations

import socket

import uvicorn

PORT = 8000


def lan_addresses() -> list[str]:
    found = []
    # The interface that would carry outgoing traffic (no packet is actually sent)
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
            s.connect(("10.255.255.255", 1))
            found.append(s.getsockname()[0])
    except OSError:
        pass
    try:
        for info in socket.getaddrinfo(socket.gethostname(), None, socket.AF_INET):
            found.append(info[4][0])
    except OSError:
        pass
    seen, out = set(), []
    for ip in found:
        if ip not in seen and not ip.startswith(("127.", "169.254.")):
            seen.add(ip)
            out.append(ip)
    return out


if __name__ == "__main__":
    ips = lan_addresses()
    print("=" * 62)
    print(" AgriVision AI - server for the Android app")
    print("=" * 62)
    if ips:
        print(" In the app, open Settings and enter:\n")
        print(f"     http://{ips[0]}:{PORT}\n")
        for ip in ips[1:]:
            print(f"   (if that fails, try http://{ip}:{PORT})")
    else:
        print(" No network found - connect the laptop to the phone's hotspot first.")
    print("\n Keep this window open while using the app. Ctrl+C to stop.")
    print("=" * 62, flush=True)
    uvicorn.run("api:app", host="0.0.0.0", port=PORT, log_level="warning")
