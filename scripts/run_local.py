#!/usr/bin/env python3
from __future__ import annotations

import os
from pathlib import Path
import socket
import sys
import webbrowser

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from gre2tor import create_app
from gre2tor.config import load_settings
def _local_ip() -> str | None:
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
            sock.connect(("8.8.8.8", 80))
            return sock.getsockname()[0]
    except OSError:
        return None


def main() -> None:
    host = os.environ.get("GRE2TOR_HOST", "0.0.0.0")
    port = int(os.environ.get("GRE2TOR_PORT", "8765"))
    settings = load_settings()

    settings.INSTANCE_PATH.mkdir(parents=True, exist_ok=True)

    local_url = f"http://127.0.0.1:{port}"
    ip = _local_ip()
    phone_url = f"http://{ip}:{port}" if ip else None

    print("\nGRE2Tor is starting...")
    print(f"Open on this computer: {local_url}")
    if phone_url:
        print(f"Open on a phone/tablet on the same Wi-Fi: {phone_url}")
    print("Press Ctrl+C to stop.\n")

    if os.environ.get("GRE2TOR_NO_BROWSER") != "1":
        webbrowser.open(local_url)

    app = create_app()
    app.run(host=host, port=port, debug=settings.FLASK_DEBUG)


if __name__ == "__main__":
    main()
