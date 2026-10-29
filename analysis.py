import argparse
import csv
import math
from collections import defaultdict


def read_rows(path):
    with open(path, newline="") as f:
        return list(csv.DictReader(f))


def mean(values):
    return sum(values) / len(values) if values else 0.0


def percentile(values, p):
    if not values:
        return 0.0
    values = sorted(values)
    k = (len(values) - 1) * p / 100
    lo, hi = math.floor(k), math.ceil(k)
    if lo == hi:
        return values[lo]
    return values[lo] + (values[hi] - values[lo]) * (k - lo)


def analyze(path):
    rows = read_rows(path)
    groups = defaultdict(list)
    for r in rows:
        groups[r["client_id"]].append(r)

    print("\nNETWORK TIME SYNCHRONIZATION - PERFORMANCE ANALYSIS")
    print("=" * 65)
    print(f"Total synchronization samples: {len(rows)}")
    print(f"Clients: {len(groups)}\n")
    print(f"{'Client':<15}{'Avg RTT(ms)':>14}{'Avg Offset(ms)':>17}{'Before(ms)':>15}{'After(ms)':>13}")
    print("-" * 74)

    all_before, all_after, all_rtt = [], [], []
    for client, data in sorted(groups.items()):
        rtt = [float(x["rtt_ms"]) for x in data]
        off = [abs(float(x["offset_ms"])) for x in data]
        before = [float(x["error_before_ms"]) for x in data]
        after = [float(x["error_after_ms"]) for x in data]
        all_rtt += rtt; all_before += before; all_after += after
        print(f"{client:<15}{mean(rtt):>14.3f}{mean(off):>17.3f}{mean(before):>15.3f}{mean(after):>13.3f}")

    print("\nOverall")
    print(f"Average RTT:              {mean(all_rtt):.3f} ms")
    print(f"Average error before:     {mean(all_before):.3f} ms")
    print(f"Average error after:      {mean(all_after):.3f} ms")
    if all_before:
        improvement = (1 - mean(all_after) / mean(all_before)) * 100 if mean(all_before) else 0
        print(f"Error reduction:          {improvement:.2f}%")
    print(f"95th percentile RTT:      {percentile(all_rtt, 95):.3f} ms")


if __name__ == "__main__":
    p = argparse.ArgumentParser(description="Analyze synchronization results")
    p.add_argument("--file", default="sync_results.csv")
    args = p.parse_args()
    analyze(args.file)
