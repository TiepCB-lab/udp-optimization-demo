"""Asyncio-based UDP echo server for demonstration purposes.

The server uses ``asyncio``'s ``DatagramProtocol`` to echo payloads from
clients. It is intentionally lightweight to highlight how asynchronous I/O
can handle many concurrent datagrams without blocking threads.
"""
from __future__ import annotations

import argparse
import asyncio
from typing import Optional


class EchoServerProtocol(asyncio.DatagramProtocol):
    """Minimal datagram protocol that echoes received packets."""

    def __init__(self) -> None:
        self.transport: Optional[asyncio.DatagramTransport] = None

    def connection_made(self, transport: asyncio.BaseTransport) -> None:
        self.transport = transport  # type: ignore[assignment]
        sockname = transport.get_extra_info("sockname")
        print(f"[ASYNC] UDP echo listening on {sockname}")

    def datagram_received(self, data: bytes, addr) -> None:  # type: ignore[override]
        if not self.transport:
            return
        self.transport.sendto(data, addr)

    def error_received(self, exc: Exception) -> None:  # pragma: no cover - debug output only
        print(f"[ASYNC] Error received: {exc}")


def run_server(host: str, port: int, reuse_port: bool = False) -> None:
    """Start an asyncio UDP echo server."""
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    listen = loop.create_datagram_endpoint(
        EchoServerProtocol,
        local_addr=(host, port),
        reuse_port=reuse_port,
    )

    transport: asyncio.DatagramTransport
    protocol: EchoServerProtocol
    try:
        transport, protocol = loop.run_until_complete(listen)
        loop.run_forever()
    except KeyboardInterrupt:
        print("[ASYNC] Shutting down server")
    finally:
        if "transport" in locals():
            transport.close()
        loop.run_until_complete(loop.shutdown_asyncgens())
        loop.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Asyncio UDP echo server")
    parser.add_argument("--host", default="0.0.0.0")
    parser.add_argument("--port", type=int, default=9999)
    parser.add_argument(
        "--reuse-port",
        action="store_true",
        help="Enable SO_REUSEPORT so multiple workers can share the same port",
    )
    args = parser.parse_args()
    run_server(args.host, args.port, args.reuse_port)
