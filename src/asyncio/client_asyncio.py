"""Asyncio UDP client that measures latency and packet loss.

The client pushes datagrams with a configurable concurrency level so the
transport layer stays busy. Sequence numbers and send timestamps are
embedded in each packet, allowing round-trip latency calculations on reply.
"""
from __future__ import annotations

import argparse
import asyncio
import statistics
import time
from typing import Dict, Optional, Tuple

PayloadMeta = Tuple[int, asyncio.TimerHandle]


class EchoClientProtocol(asyncio.DatagramProtocol):
    def __init__(self, total: int, payload_size: int, timeout: float, concurrency: int):
        if payload_size < 16:
            raise ValueError("payload_size must be at least 16 bytes")

        self.total = total
        self.payload = b"x" * (payload_size - 16)
        self.timeout = timeout
        self.concurrency = concurrency
        self.loop = asyncio.get_running_loop()

        self.transport: Optional[asyncio.DatagramTransport] = None
        self.pending: Dict[int, PayloadMeta] = {}
        self.sent = 0
        self.received = 0
        self.in_flight = 0
        self.rtts = []
        self.done = self.loop.create_future()

    # Lifecycle ---------------------------------------------------------
    def connection_made(self, transport: asyncio.BaseTransport) -> None:
        self.transport = transport  # type: ignore[assignment]
        initial = min(self.concurrency, self.total)
        for _ in range(initial):
            self._send_next()

    def connection_lost(self, exc: Optional[Exception]) -> None:
        if not self.done.done():
            self.done.set_result(None)

    # Sending and receiving --------------------------------------------
    def _send_next(self) -> None:
        if not self.transport:
            return
        if self.sent >= self.total:
            if self.in_flight == 0 and not self.done.done():
                self.done.set_result(None)
            return

        seq = self.sent
        self.sent += 1
        self.in_flight += 1

        t0 = time.perf_counter_ns()
        packet = t0.to_bytes(8, "little") + seq.to_bytes(8, "little") + self.payload
        timer = self.loop.call_later(self.timeout, self._on_timeout, seq)
        self.pending[seq] = (t0, timer)
        self.transport.sendto(packet)

    def _on_timeout(self, seq: int) -> None:
        if seq not in self.pending:
            return
        self.pending.pop(seq, None)
        self.in_flight -= 1
        self._maybe_finish_or_continue()

    def datagram_received(self, data: bytes, addr) -> None:  # type: ignore[override]
        t1 = time.perf_counter_ns()
        if len(data) < 16:
            return
        seq = int.from_bytes(data[8:16], "little")
        pending = self.pending.pop(seq, None)
        if pending is None:
            return
        t0, timer = pending
        timer.cancel()
        self.in_flight -= 1
        self.received += 1
        self.rtts.append((t1 - t0) / 1e6)
        self._maybe_finish_or_continue()

    # Helpers ----------------------------------------------------------
    def _maybe_finish_or_continue(self) -> None:
        if self.sent < self.total:
            self._send_next()
        elif self.in_flight == 0 and not self.done.done():
            self.done.set_result(None)


def run_client(host: str, port: int, n: int, payload_size: int, concurrency: int, timeout: float) -> None:
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    connect = loop.create_datagram_endpoint(
        lambda: EchoClientProtocol(n, payload_size, timeout, concurrency),
        remote_addr=(host, port),
    )

    start_all = time.perf_counter()
    transport: asyncio.DatagramTransport
    protocol: EchoClientProtocol
    try:
        transport, protocol = loop.run_until_complete(connect)
        loop.run_until_complete(protocol.done)
    finally:
        if "transport" in locals():
            transport.close()
        loop.run_until_complete(loop.shutdown_asyncgens())
        loop.close()

    elapsed = time.perf_counter() - start_all
    loss = (protocol.sent - protocol.received) / protocol.sent * 100 if protocol.sent else 0
    print(f"Sent={protocol.sent} Recv={protocol.received} Loss={loss:.2f}%")
    if protocol.rtts:
        print(
            "Latency ms -> "
            f"p50={statistics.median(protocol.rtts):.3f} "
            f"avg={statistics.mean(protocol.rtts):.3f} "
            f"p95={statistics.quantiles(protocol.rtts, n=20)[18]:.3f}"
        )
    print(f"Throughput: {protocol.received/elapsed:.0f} msg/s")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Asyncio UDP benchmark client")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=9999)
    parser.add_argument("--n", type=int, default=5000, help="Number of datagrams to send")
    parser.add_argument("--size", type=int, default=400, help="Payload size in bytes")
    parser.add_argument("--concurrency", type=int, default=50, help="Number of in-flight requests")
    parser.add_argument("--timeout", type=float, default=1.0, help="Per-packet timeout in seconds")
    args = parser.parse_args()
    run_client(args.host, args.port, args.n, args.size, args.concurrency, args.timeout)
