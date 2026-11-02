#!/usr/bin/env python3
import ipaddress, socket, statistics, sys, time, urllib.request
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor

CIDR_URL = "https://core.telegram.org/resources/cidr.txt"
FALLBACK = [
    "91.108.56.0/22", "91.108.4.0/22", "91.108.8.0/22", "91.108.16.0/22",
    "91.108.12.0/22", "149.154.160.0/20", "91.105.192.0/23",
    "91.108.20.0/22", "185.76.151.0/24",
]
PORT = 443
SCAN_TIMEOUT = 2.0     # 第一轮扫描超时
WORKERS = 400          # 并发数，机房限速的话调小
PROBES = 5             # 对开放 IP 的复测次数
TOP = 20


def load_cidrs():
    try:
        txt = urllib.request.urlopen(CIDR_URL, timeout=8).read().decode()
        res = []
        for tok in txt.split():
            try:
                n = ipaddress.ip_network(tok, strict=False)
                if n.version == 4:
                    res.append(n)
            except ValueError:
                pass
        if res:
            print(f">>> 官方列表: {len(res)} 个 IPv4 网段")
            return res
    except Exception as e:
        print(f">>> 拉取失败({e})，使用内置列表")
    return [ipaddress.ip_network(c) for c in FALLBACK]


def tcp_ms(ip, timeout=SCAN_TIMEOUT):
    t = time.perf_counter()
    try:
        with socket.create_connection((ip, PORT), timeout=timeout):
            return (time.perf_counter() - t) * 1000
    except OSError:
        return None


def probe(ip):
    """多次测量，返回 (最小, 中位, ip)"""
    v = [m for m in (tcp_ms(ip, 3.0) for _ in range(PROBES)) if m is not None]
    return (min(v), statistics.median(v), ip) if v else None


def main():
    nets = load_cidrs()
    all_ips = [str(h) for n in nets for h in n.hosts()]
    print(f">>> 共 {len(all_ips)} 个地址，扫描 TCP {PORT} ...")

    t0 = time.time()
    with ThreadPoolExecutor(max_workers=WORKERS) as ex:
        first = list(ex.map(tcp_ms, all_ips))
    open_ips = [ip for ip, m in zip(all_ips, first) if m is not None]
    print(f">>> 发现 {len(open_ips)} 个开放 IP（耗时 {time.time()-t0:.0f}s）")
    if not open_ips:
        sys.exit("没有开放的 IP")

    print(f">>> 对每个开放 IP 复测 {PROBES} 次 ...")
    with ThreadPoolExecutor(max_workers=64) as ex:
        rank = sorted(r for r in ex.map(probe, open_ips) if r)

    with open("open_ips.txt", "w") as f:
        for mn, md, ip in rank:
            f.write(f"{ip}\n")
    with open("open_ips_latency.txt", "w") as f:
        for mn, md, ip in rank:
            f.write(f"{mn:.0f}ms\tmed={md:.0f}ms\t{ip}\n")

    print(f"\n>>> 延迟最低的前 {TOP} 个 IP:")
    for mn, md, ip in rank[:TOP]:
        print(f"  min {mn:6.0f}ms  med {md:6.0f}ms  {ip}")

    # 按 /24 汇总，看延迟分层
    groups = defaultdict(list)
    for mn, md, ip in rank:
        groups[str(ipaddress.ip_network(ip + "/24", strict=False))].append(mn)
    print("\n>>> 按 /24 汇总（按最低延迟排序）:")
    for g, v in sorted(groups.items(), key=lambda kv: min(kv[1])):
        print(f"  {g:18s} 开放 {len(v):3d} 个  最低 {min(v):6.0f}ms  最高 {max(v):6.0f}ms")


if __name__ == "__main__":
    main()
