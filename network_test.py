import argparse
import socket
import threading
import time

LOAD_PORT = 5001


def generate_load(host, port, rate, duration, payload_size):
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    payload = b"LOAD" * max(1, payload_size // 4)
    payload = payload[:payload_size]
    interval = 1.0 / max(rate, 1)
    end = time.monotonic() + duration
    sent = 0
    while time.monotonic() < end:
        try:
            sock.sendto(payload, (host, port))
            sent += 1
        except OSError:
            break
        time.sleep(interval)
    sock.close()
    print(f"Load packets sent: {sent}")


def run(host, port, rate, duration):
    print("Controlled network-condition test")
    print(f"Target: {host}:{port} | Rate: {rate} packets/sec | Duration: {duration} sec")
    generate_load(host, port, rate, duration, 256)


if __name__ == "__main__":
    p = argparse.ArgumentParser(description="Generate controlled UDP background load")
    p.add_argument("--host", default="127.0.0.1")
    p.add_argument("--port", type=int, default=LOAD_PORT)
    p.add_argument("--rate", type=int, default=100)
    p.add_argument("--duration", type=float, default=20)
    args = p.parse_args()
    run(args.host, args.port, args.rate, args.duration)
