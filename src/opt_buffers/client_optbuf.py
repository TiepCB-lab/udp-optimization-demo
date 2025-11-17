"""UDP client using tuned socket buffers and zero-copy memoryviews."""
from __future__ import annotations

import argparse
import socket
import statistics
import time
from typing import List, Tuple


def run(host: str, port: int, n: int, payload_size: int, batch: int, rcvbuf: int, sndbuf: int) -> None:
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_RCVBUF, rcvbuf)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_SNDBUF, sndbuf)
    sock.connect((host, port))
    sock.settimeout(1.0)

    payload = memoryview(b"x" * (payload_size - 16))
    rtts: List[float] = []
    sent = 0
    received = 0

    start_all = time.perf_counter()
    for start in range(0, n, batch):
        window = min(batch, n - start)
        packets: List[Tuple[bytes, tuple]] = []
        for i in range(window):
            seq = start + i
            t0 = time.perf_counter_ns()
            header = t0.to_bytes(8, "little") + seq.to_bytes(8, "little")
            packets.append((header + payload.tobytes(), (host, port)))
        if hasattr(sock, "sendmmsg"):
            sock.sendmmsg(packets)
        else:  # pragma: no cover - fallback path
            for pkt, addr in packets:
                sock.sendto(pkt, addr)
        sent += window

        for _ in range(window):
            try:
                data, _ = sock.recvfrom(65535)
            except socket.timeout:
                continue
            if len(data) < 16:
                continue
            t1 = time.perf_counter_ns()
            t0_ns = int.from_bytes(data[:8], "little")
            rtts.append((t1 - t0_ns) / 1e6)
            received += 1

    elapsed = time.perf_counter() - start_all
    loss = (sent - received) / sent * 100 if sent else 0
    print(
        f"Sent={sent} Recv={received} Loss={loss:.2f}% | "
        f"RCVBUF={sock.getsockopt(socket.SOL_SOCKET, socket.SO_RCVBUF)} "
        f"SNDBUF={sock.getsockopt(socket.SOL_SOCKET, socket.SO_SNDBUF)}"
    )
    if rtts:
        print(
            "Latency ms -> "
            f"p50={statistics.median(rtts):.3f} "
            f"avg={statistics.mean(rtts):.3f} "
            f"p95={statistics.quantiles(rtts, n=20)[18]:.3f}"
        )
    print(f"Throughput: {received/elapsed:.0f} msg/s")


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description="UDP client with buffer/zero-copy optimizations")
    ap.add_argument("--host", default="127.0.0.1")
    ap.add_argument("--port", type=int, default=9999)
    ap.add_argument("--n", type=int, default=5000)
    ap.add_argument("--size", type=int, default=400)
    ap.add_argument("--batch", type=int, default=64, help="Packets per send batch")
    ap.add_argument("--rcvbuf", type=int, default=4 * 1024 * 1024)
    ap.add_argument("--sndbuf", type=int, default=4 * 1024 * 1024)
    args = ap.parse_args()
    run(args.host, args.port, args.n, args.size, args.batch, args.rcvbuf, args.sndbuf)
