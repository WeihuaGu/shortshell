#!/usr/bin/env python3
import base64, os, socket, ssl, struct, sys, time
from concurrent.futures import ThreadPoolExecutor
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes

IN_FILE = "open_ips.txt"
OUT_FILE = "ws_ips.txt"
FRONT_SNI = sys.argv[1] if len(sys.argv) > 1 else "cdn5.telesco.pe"
TIMEOUT = 6.0
WORKERS = 64
TRIES = 2            # 每个 IP/DC 组合测几次，必须全部成功才算稳定

ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

BAD_FIRST4 = {b"HEAD", b"POST", b"GET ", b"OPTI",
              b"\xdd\xdd\xdd\xdd", b"\xee\xee\xee\xee", b"\x16\x03\x01\x02"}


def make_obfs(dc):
    """返回 (要发送的64字节init, 加密器, 解密器)"""
    while True:
        b = bytearray(os.urandom(64))
        if b[0] == 0xef or bytes(b[:4]) in BAD_FIRST4 or b[4:8] == b"\0" * 4:
            continue
        break
    b[56:60] = b"\xee\xee\xee\xee"            # intermediate transport
    b[60:62] = struct.pack("<h", dc)          # DC 编号
    raw = bytes(b)
    enc = Cipher(algorithms.AES(raw[8:40]), modes.CTR(raw[40:56])).encryptor()
    rev = raw[::-1]
    dec = Cipher(algorithms.AES(rev[8:40]), modes.CTR(rev[40:56])).decryptor()
    encrypted = enc.update(raw)               # 密钥流推进 64 字节
    return raw[:56] + encrypted[56:64], enc, dec


def ws_frame(data):
    mask = os.urandom(4)
    n = len(data)
    if n < 126:
        hdr = bytes([0x82, 0x80 | n])
    elif n < 65536:
        hdr = bytes([0x82, 0x80 | 126]) + struct.pack(">H", n)
    else:
        hdr = bytes([0x82, 0x80 | 127]) + struct.pack(">Q", n)
    return hdr + mask + bytes(d ^ mask[i % 4] for i, d in enumerate(data))


class Reader:
    def __init__(self, s, buf=b""):
        self.s, self.buf = s, buf

    def exact(self, n):
        while len(self.buf) < n:
            c = self.s.recv(65536)
            if not c:
                raise ConnectionError("closed")
            self.buf += c
        out, self.buf = self.buf[:n], self.buf[n:]
        return out

    def frame(self):
        """返回 (opcode, payload)"""
        b1, b2 = self.exact(2)
        n = b2 & 0x7F
        if n == 126:
            n = struct.unpack(">H", self.exact(2))[0]
        elif n == 127:
            n = struct.unpack(">Q", self.exact(8))[0]
        if b2 & 0x80:
            mask = self.exact(4)
            p = bytes(d ^ mask[i % 4] for i, d in enumerate(self.exact(n)))
        else:
            p = self.exact(n)
        return b1 & 0x0F, p


def probe(ip, dc):
    """完整握手成功返回总耗时(ms)，否则 None"""
    host = f"kws{dc}.web.telegram.org"
    key = base64.b64encode(os.urandom(16)).decode()
    req = (f"GET /apiws HTTP/1.1\r\nHost: {host}\r\n"
           "Upgrade: websocket\r\nConnection: Upgrade\r\n"
           f"Sec-WebSocket-Key: {key}\r\nSec-WebSocket-Version: 13\r\n"
           "Sec-WebSocket-Protocol: binary\r\n"
           "Origin: https://web.telegram.org\r\n\r\n").encode()
    t0 = time.perf_counter()
    try:
        with socket.create_connection((ip, 443), timeout=TIMEOUT) as raw:
            with ctx.wrap_socket(raw, server_hostname=FRONT_SNI) as s:
                s.settimeout(TIMEOUT)
                s.sendall(req)
                head = b""
                while b"\r\n\r\n" not in head:
                    c = s.recv(4096)
                    if not c:
                        return None
                    head += c
                head, rest = head.split(b"\r\n\r\n", 1)
                if b" 101 " not in head.split(b"\r\n")[0] + b" ":
                    return None
                rd = Reader(s, rest)

                init, enc, dec = make_obfs(dc)
                s.sendall(ws_frame(init))

                nonce = os.urandom(16)
                msg_id = int(time.time() * 2**32) & ~3
                body = struct.pack("<I", 0xbe7e8ef1) + nonce      # req_pq_multi
                pkt = (b"\0" * 8 + struct.pack("<Q", msg_id)
                       + struct.pack("<I", len(body)) + body)
                s.sendall(ws_frame(enc.update(struct.pack("<I", len(pkt)) + pkt)))

                plain = b""
                while True:
                    op, p = rd.frame()
                    if op == 0x8:                 # close
                        return None
                    if op in (0x9, 0xA):          # ping/pong
                        continue
                    plain += dec.update(p)
                    if len(plain) >= 4:
                        L = struct.unpack("<I", plain[:4])[0]
                        if not (20 <= L <= 4096):
                            return None           # 例如 4 字节的错误码
                        if len(plain) >= 4 + L:
                            break
                resp = plain[4:4 + L]
        if (len(resp) >= 40 and resp[:8] == b"\0" * 8
                and struct.unpack("<I", resp[20:24])[0] == 0x05162463
                and resp[24:40] == nonce):
            return (time.perf_counter() - t0) * 1000
    except (OSError, ssl.SSLError, ConnectionError, struct.error):
        pass
    return None


def check(ip):
    out = []
    for dc in range(1, 6):
        v = []
        for _ in range(TRIES):
            m = probe(ip, dc)
            if m is None:
                break
            v.append(m)
        if len(v) == TRIES:
            out.append((min(v), dc, ip))
    return out


def main():
    ips = [l.strip() for l in open(IN_FILE) if l.strip()]
    print(f">>> SNI={FRONT_SNI}，完整握手探测 {len(ips)} 个 IP × 5 个 DC ...")
    with ThreadPoolExecutor(max_workers=WORKERS) as ex:
        rows = [r for rs in ex.map(check, ips) for r in rs]
    rows.sort()                                   # 全局按延迟排序

    with open(OUT_FILE, "w") as f:
        for ms, dc, ip in rows:
            f.write(f"{ms:.0f}ms\tDC{dc}\t{ip}\n")

    if not rows:
        print("没有任何 IP 通过完整握手")
        return
    print(f">>> 共 {len(rows)} 个可用组合，已写入 {OUT_FILE}")
    print(">>> 每个 DC 延迟最低的 IP:")
    seen = set()
    for ms, dc, ip in rows:
        if dc not in seen:
            seen.add(dc)
            print(f"  --dc-ip {dc}:{ip}    ({ms:.0f}ms)")


if __name__ == "__main__":
    main()
