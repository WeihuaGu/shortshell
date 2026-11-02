#!/usr/bin/env python3
import os, socket, struct, sys, time
from concurrent.futures import ThreadPoolExecutor

IN_FILE = "open_ips.txt"
OUT_FILE = "dc_ips.txt"
PORT = 443
TIMEOUT = 4.0
TRIES = 3
WORKERS = 64


def recv_exact(s, n):
    buf = b""
    while len(buf) < n:
        chunk = s.recv(n - len(buf))
        if not chunk:
            raise ConnectionError("closed")
        buf += chunk
    return buf


def mtproto_probe(ip):
    """成功返回握手往返耗时(ms)，不是 DC 返回 None"""
    nonce = os.urandom(16)
    msg_id = (int(time.time() * 2**32)) & ~3
    body = struct.pack("<I", 0xbe7e8ef1) + nonce          # req_pq_multi
    payload = (b"\x00" * 8                                 # auth_key_id = 0
               + struct.pack("<Q", msg_id)
               + struct.pack("<I", len(body)) + body)
    try:
        with socket.create_connection((ip, PORT), timeout=TIMEOUT) as s:
            s.settimeout(TIMEOUT)
            s.sendall(b"\xee\xee\xee\xee")                 # intermediate transport
            t = time.perf_counter()
            s.sendall(struct.pack("<I", len(payload)) + payload)
            length = struct.unpack("<I", recv_exact(s, 4))[0]
            if not (20 <= length <= 4096):
                return None
            resp = recv_exact(s, length)
            rtt = (time.perf_counter() - t) * 1000
    except (OSError, ConnectionError):
        return None
    # auth_key_id(8) + msg_id(8) + len(4) + constructor(4) + nonce(16)
    if len(resp) < 40 or resp[:8] != b"\x00" * 8:
        return None
    if struct.unpack("<I", resp[20:24])[0] != 0x05162463:   # resPQ
        return None
    if resp[24:40] != nonce:
        return None
    return rtt


def check(ip):
    v = [m for m in (mtproto_probe(ip) for _ in range(TRIES)) if m is not None]
    return (min(v), ip) if v else None


def main():
    if not os.path.exists(IN_FILE):
        sys.exit(f"找不到 {IN_FILE}，请先运行 find_fast_dc.py")
    ips = [l.strip() for l in open(IN_FILE) if l.strip()]
    print(f">>> 检查 {len(ips)} 个 IP 是否为 MTProto DC 入口 ...")
    with ThreadPoolExecutor(max_workers=WORKERS) as ex:
        ok = sorted(r for r in ex.map(check, ips) if r)

    with open(OUT_FILE, "w") as f:
        for ms, ip in ok:
            f.write(f"{ms:.0f}ms\t{ip}\n")

    print(f">>> 其中 {len(ok)} 个是 DC 入口（已写入 {OUT_FILE}）:")
    for ms, ip in ok:
        print(f"  {ms:6.0f}ms  {ip}")


if __name__ == "__main__":
    main()
