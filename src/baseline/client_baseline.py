import socket, time, statistics, argparse

def run(host, port, n, payload_size):
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    payload = b"x" * (payload_size - 16)
    rtts = []
    sent = 0; received = 0
    start_all = time.perf_counter()

    for i in range(n):
        t0 = time.perf_counter_ns().to_bytes(8, "little")
        seq = i.to_bytes(8, "little")
        sock.sendto(t0 + seq + payload, (host, port))
        sent += 1
        sock.settimeout(1.0)
        try:
            data, _ = sock.recvfrom(65535)
            t1 = time.perf_counter_ns()
            t0_ns = int.from_bytes(data[:8], "little")
            rtts.append((t1*1e9 - t0_ns)/1e6)
            received += 1
        except socket.timeout:
            pass

    elapsed = time.perf_counter() - start_all
    print(f"Sent={sent} Recv={received} Loss={(sent-received)/sent*100:.2f}%")
    if rtts:
        print(f"Latency ms -> p50={statistics.median(rtts):.3f} "
              f"avg={statistics.mean(rtts):.3f} p95={statistics.quantiles(rtts, n=20)[18]:.3f}")
    print(f"Throughput: {received/elapsed:.0f} msg/s")

if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--host", default="127.0.0.1")
    ap.add_argument("--port", type=int, default=9999)
    ap.add_argument("--n", type=int, default=5000)
    ap.add_argument("--size", type=int, default=400)
    args = ap.parse_args()
    run(args.host, args.port, args.n, args.size)
