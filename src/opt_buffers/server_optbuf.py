"""UDP echo server focusing on buffer tuning and batch receive/send.

This variant increases socket buffers and uses ``recvmmsg``/``sendmmsg``
when available to reduce syscall overhead compared to a naive loop.
"""
from __future__ import annotations

import argparse
import socket
import time
from typing import List, Tuple


def _recv_batch(sock: socket.socket, bufsize: int, batch_size: int) -> List[Tuple[bytes, tuple]]:
    """Receive a batch of datagrams with ``recvmmsg`` if available."""
    messages: List[Tuple[bytes, tuple]] = []
    if hasattr(sock, "recvmmsg"):
        mmsg = sock.recvmmsg(batch_size, bufsize)
        for data, ancdata, msg_flags, address in mmsg:
            if msg_flags & socket.MSG_TRUNC:
                # Drop truncated packets to keep echo semantics simple
                continue
            messages.append((bytes(data), address))
    else:  # pragma: no cover - fallback path
        for _ in range(batch_size):
            try:
                data, address = sock.recvfrom(bufsize)
                messages.append((data, address))
            except BlockingIOError:
                break
    return messages


def _send_batch(sock: socket.socket, messages: List[Tuple[bytes, tuple]]) -> None:
    """Send a batch of datagrams with ``sendmmsg`` if available."""
    if not messages:
        return
    if hasattr(sock, "sendmmsg"):
        sock.sendmmsg(messages)
    else:  # pragma: no cover - fallback path
        for data, address in messages:
            sock.sendto(data, address)


def run_server(host: str, port: int, bufsize: int, batch_size: int, rcvbuf: int, sndbuf: int) -> None:
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_RCVBUF, rcvbuf)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_SNDBUF, sndbuf)
    sock.bind((host, port))
    sock.setblocking(False)

    print(
        f"[OPTB] UDP echo listening on {host}:{port} | "
        f"RCVBUF={sock.getsockopt(socket.SOL_SOCKET, socket.SO_RCVBUF)} "
        f"SNDBUF={sock.getsockopt(socket.SOL_SOCKET, socket.SO_SNDBUF)}"
    )

    while True:
        messages = _recv_batch(sock, bufsize, batch_size)
        if not messages:
            time.sleep(0.0005)  # yield CPU
            continue
        _send_batch(sock, messages)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="UDP echo server with buffer optimizations")
    parser.add_argument("--host", default="0.0.0.0")
    parser.add_argument("--port", type=int, default=9999)
    parser.add_argument("--bufsize", type=int, default=2048)
    parser.add_argument("--batch", type=int, default=32, help="Number of packets to read per syscall")
    parser.add_argument("--rcvbuf", type=int, default=4 * 1024 * 1024, help="Receive buffer size")
    parser.add_argument("--sndbuf", type=int, default=4 * 1024 * 1024, help="Send buffer size")
    args = parser.parse_args()
    run_server(args.host, args.port, args.bufsize, args.batch, args.rcvbuf, args.sndbuf)
