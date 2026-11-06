#!/usr/bin/env python3
import base64, os, socket, ssl, sys, time
from concurrent.futures import ThreadPoolExecutor

IN_FILE = "open_ips.txt"
OUT_FILE = "ws_ips.txt"
FRONT_SNI = sys.argv[1] if len(sys.argv) > 1 else "cdn5.telesco.pe"
TIMEOUT = 5.0
WORKERS = 64

ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE


def ws_probe(ip, n):
    host = f"kws{n}.web.telegram.org"
    key = base64.b64encode(os.urandom(16)).decode()
    req = (f"GET /apiws HTTP/1.1\r\nHost: {host}\r\n"
           "Upgrade: websocket\r\nConnection: Upgrade\r\n"
           f"Sec-WebSocket-Key: {key}\r\nSec-WebSocket-Version: 13\r\n"
           "Sec-WebSocket-Protocol: binary\r\n"
           "Origin: https://web.telegram.org\r\n\r\n").encode()
    t = time.perf_counter()
    try:
        with socket.create_connection((ip, 443), timeout=TIMEOUT) as raw:
            # SNI 用伪装域名，Host 用真实域名
            with ctx.wrap_socket(raw, server_hostname=FRONT_SNI) as s:
                s.settimeout(TIMEOUT)
                s.sendall(req)
                head = s.recv(1024)
        ms = (time.perf_counter() - t) * 1000
        if b" 101 " in head.split(b"\r\n")[0] + b" ":
            return ms
    except (OSError, ssl.SSLError):
        pass
    return None


def check(ip):
    res = []
    for n in range(1, 6):
        v = [m for m in (ws_probe(ip, n) for _ in range(2)) if m is not None]
        if v:
            res.append((n, min(v), ip))
    return res


def main():
    ips = [l.strip() for l in open(IN_FILE) if l.strip()]
    print(f">>> SNI={FRONT_SNI}，探测 {len(ips)} 个 IP ...")
    with ThreadPoolExecutor(max_workers=WORKERS) as ex:
        rows = [r for rs in ex.map(check, ips) for r in rs]
    rows.sort(key=lambda r: (r[0], r[1]))

    with open(OUT_FILE, "w") as f:
        for n, ms, ip in rows:
            f.write(f"{n}\t{ms:.0f}ms\t{ip}\n")

    if not rows:
        print("仍然没有通过的 IP")
        return
    print(">>> 每个 DC 延迟最低的 IP:")
    seen = set()
    for n, ms, ip in rows:
        if n not in seen:
            seen.add(n)
            print(f"  --dc-ip {n}:{ip}    ({ms:.0f}ms)")


if __name__ == "__main__":
    main()
