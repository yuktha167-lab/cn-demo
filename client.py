import argparse
import csv
import json
import socket
import time
import uuid

RESULT_FILE = "sync_results.csv"


def now_ns():
    return time.time_ns()


def make_socket():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.settimeout(2.0)
    try:
        s.setsockopt(socket.IPPROTO_IP, socket.IP_TOS, 0xB8)
    except OSError:
        pass
    return s


def init_results():
    try:
        with open(RESULT_FILE, "x", newline="") as f:
            csv.writer(f).writerow([
                "timestamp", "client_id", "request_id", "t1_ns", "t2_ns", "t3_ns", "t4_ns",
                "rtt_ms", "offset_ms", "error_before_ms", "error_after_ms"
            ])
    except FileExistsError:
        pass


def synchronize(client_id, server_host, server_port, cycles, interval, skew_ms):
    init_results()
    sock = make_socket()
    print(f"Client {client_id} -> {server_host}:{server_port}")
    print("Press Ctrl+C to stop.\n")

    for _ in range(cycles):
        request_id = uuid.uuid4().hex[:8]
        # t1: client sends request
        t1 = now_ns() + int(skew_ms * 1_000_000)
        request = {"type": "sync", "client_id": client_id, "request_id": request_id}
        sock.sendto(json.dumps(request).encode(), (server_host, server_port))

        try:
            data, _ = sock.recvfrom(4096)
            t4 = now_ns() + int(skew_ms * 1_000_000)
            response = json.loads(data.decode())
            if response.get("type") != "sync_response":
                continue
        except (socket.timeout, json.JSONDecodeError):
            print("Timeout / invalid response")
            continue

        t2 = int(response["t2_ns"])
        t3 = int(response["t3_ns"])

        # NTP-style four-timestamp calculations.
        rtt_ns = (t4 - t1) - (t3 - t2)
        offset_ns = ((t2 - t1) + (t3 - t4)) / 2

        # Since this demo does not change the operating-system clock,
        # show the estimated corrected time instead.
        corrected_time_ns = t4 + int(offset_ns)
        error_before_ms = abs(t4 - t3) / 1_000_000
        error_after_ms = abs(corrected_time_ns - t3) / 1_000_000

        with open(RESULT_FILE, "a", newline="") as f:
            csv.writer(f).writerow([
                time.strftime("%Y-%m-%d %H:%M:%S"), client_id, request_id,
                t1, t2, t3, t4,
                rtt_ns / 1_000_000,
                offset_ns / 1_000_000,
                error_before_ms,
                error_after_ms
            ])

        print(f"[{client_id}] RTT: {rtt_ns/1_000_000:.3f} ms | "
              f"Offset: {offset_ns/1_000_000:.3f} ms | "
              f"Before: {error_before_ms:.3f} ms | After: {error_after_ms:.3f} ms")
        time.sleep(interval)

    sock.close()


if __name__ == "__main__":
    p = argparse.ArgumentParser(description="UDP time synchronization client")
    p.add_argument("--id", default="Client-1")
    p.add_argument("--server", default="127.0.0.1")
    p.add_argument("--port", type=int, default=5000)
    p.add_argument("--cycles", type=int, default=10)
    p.add_argument("--interval", type=float, default=1.0)
    p.add_argument("--skew-ms", type=float, default=0.0,
                   help="Simulated client clock difference; does not change the OS clock")
    args = p.parse_args()
    synchronize(args.id, args.server, args.port, args.cycles, args.interval, args.skew_ms)
