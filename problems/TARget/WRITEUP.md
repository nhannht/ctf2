# TARget

## Goal

Challenge prompt:

> I gib you 1 endpoint, you gib me flag.

Solved on 2026-05-24 against the live instanced service:

```text
http://chall.blackpinker.com:20505
```

Flag:

```text
HCMUS-CTF{D1d_y0u_kn0w_th4t_unZ1p_4ls0_h4v3_th1s_1ssu3_but_w0rs3?}
```

## Source Review

The shipped Flask app is tiny:

```python
app.config['MAX_CONTENT_LENGTH'] = 1024

@app.route('/untar', methods=['POST'])
def untar_file():
    ...
    UPLOAD_FOLDER = os.path.join(os.getcwd(), 'uploads', str(int(time.time())))
    ...
    file.save(tar_path)
    subprocess.check_output(['tar', '-xf', tar_path, '-C', UPLOAD_FOLDER])
    ...
    shutil.rmtree(UPLOAD_FOLDER, ignore_errors=True)
```

The Dockerfile matters just as much:

```dockerfile
COPY flag /flag
RUN mv /flag /flag-`cat /proc/sys/kernel/random/uuid`.txt
WORKDIR /app
COPY src/app.py /app/app.py
RUN pip install flask
CMD ["python3", "app.py"]
```

Important consequences:

- uploads are grouped by `uploads/<int(time.time())>`, so requests landing in
  the same second share one extraction directory
- extraction is delegated to GNU `tar`, not Python `tarfile`
- the process runs in `/app`
- the flag is not `/flag`, it is `/flag-<uuid>.txt`
- the code invokes `tar` by bare name, not by absolute path

## Recon

The live instance exposed a default Flask/Werkzeug 404 at `/` and only one
useful route:

```text
GET  /untar -> 405
POST /untar -> untar uploaded .tar
```

The size cap is on the whole multipart request, not only the archive bytes, so
ordinary tarballs are too large. Small handcrafted archives worked, including
single-entry symlink archives.

## Key Observation

The real bug is not simple traversal. It is a race between two untrusted tar
extractions into the same second-based directory.

GNU tar's own manual explicitly warns that extracting multiple untrusted
archives into a shared writable location is unsafe because the first archive can
plant a symlink and the second archive can follow it. That is exactly what this
service does.

## Exploit Chain

### 1. Turn `/static` into arbitrary file read

The first winning primitive was an arbitrary read via Flask's static route.

Flask serves `/static/...` from `/app/static`. That directory did not exist by
default, so a direct attempt to race `static -> /app/static` and then write
through it failed: tar refuses to create `static/file` through a dangling
directory symlink.

The reliable variant was:

1. request A extracts `app -> /app` plus a large zero-filled delay file
2. request B extracts `app/static -> /`
3. if both requests land in the same `uploads/<second>` directory, the second
   extraction follows `app -> /app` and creates `/app/static` as a symlink to
   `/`

After that, Flask's `/static/...` route becomes a read gadget for the entire
filesystem:

```text
GET /static/etc/passwd
```

returned the server's `/etc/passwd`.

To stretch the race window while staying below the 1 KiB multipart cap, the
delay tarball was gzip-compressed and contained a large zero-filled file. A
payload around 750 bytes on the wire expanded to roughly 640 KiB during
extraction, which was enough.

### 2. Turn arbitrary read into code execution

Arbitrary read alone still did not reveal the randomized flag path cheaply, but
the source already exposed a better pivot:

```python
subprocess.check_output(['tar', '-xf', tar_path, '-C', UPLOAD_FOLDER])
```

Because `tar` is not called by absolute path, the app trusts `PATH`.

The second race used the same pattern:

1. request A extracts `usr -> /usr` plus the same large delay file
2. request B extracts `usr/local/bin/tar` as an attacker-controlled shell script
3. a later normal upload triggers `subprocess.check_output(['tar', ...])`
4. the fake `/usr/local/bin/tar` runs instead of the real tar binary

The replacement script was simple:

```sh
#!/bin/sh
cp /flag-* /tmp/flag.txt 2>/dev/null
exit 0
```

Once the hijack landed, any follow-up `/untar` request executed that script.

### 3. Read the copied flag back through `/static`

The first stage had already turned `/app/static` into `/`, so the copied file
was readable immediately:

```text
GET /static/tmp/flag.txt
```

That returned:

```text
HCMUS-CTF{D1d_y0u_kn0w_th4t_unZ1p_4ls0_h4v3_th1s_1ssu3_but_w0rs3?}
```

## Why This Works

The full exploit relies on three independent mistakes:

- extracting attacker-controlled tar archives into a directory name derived from
  `int(time.time())`
- extracting multiple attacker-controlled archives into that same shared
  location
- invoking `tar` via `PATH` instead of `/bin/tar` or `/usr/bin/tar`

Any one of these fixed cleanly would have broken the chain.

## Submission

The browser UI worked for spawning but was flaky for submission, so the final
solve was submitted through rCTF's authenticated API.

On 2026-05-24, the working flow was:

1. read the bearer token from browser `localStorage["token"]`
2. fetch challenge metadata from `GET /api/v1/challs`
3. submit with:

```text
POST /api/v1/challs/<challenge-id>/submit
Authorization: Bearer <token>
Content-Type: application/json

{"flag":"HCMUS-CTF{...}"}
```

For this challenge, the live API returned:

```json
{"kind":"goodFlag","message":"The flag is correct.","data":{"rank":"57"}}
```

## Takeaway

The challenge name is accurate: the bug is really about tar extraction as a
primitive, and the final flag text hints at the broader lesson. Shared
extraction directories plus symlink-following behavior are already enough for
arbitrary file read/write; PATH-based helper execution turns that into full RCE.
