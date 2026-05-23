# TARget

## Goal

Challenge prompt:

> I gib you l endpoint, you gib me flag.

Visible instance:

```text
http://chall.blackpinker.com:20937
```

## Workflow Notes

### 1. Initial service mapping

The root route is a Flask/Werkzeug 404:

```text
GET / -> 404 NOT FOUND
Server: Werkzeug/3.1.8 Python/3.14.5
```

The interesting route is:

```text
GET /untar  -> 405 METHOD NOT ALLOWED, Allow: OPTIONS, POST
POST /untar -> JSON errors
```

Posting without multipart data:

```json
{"error":"No file part"}
```

Posting a normal GNU tar containing one tiny file fails because GNU tar pads the
archive to 10 KiB:

```json
{"error":"File too large. Max size is 1KB."}
```

This makes the likely intended bug a small crafted tar extraction payload.

### 2. Minimal tar payload behavior

Python-generated tar members were stripped of end-of-archive zero blocks. The
server rejects a 1024-byte single-file archive, but accepts one-header archives:

```text
empty zero-byte file, 512 bytes -> 200 {"message":"File untarred successfully"}
symlink flag.txt -> /flag, 512 bytes -> 200 {"message":"File untarred successfully"}
../../tmp/flag.txt -> /flag symlink, 512 bytes -> 500
```

Symlink entries under guessed public locations such as `static/flag.txt`,
`/app/static/...`, `/usr/src/app/static/...`, and `/proc/self/cwd/static/...`
were accepted by the extractor but were not reachable over `GET /static/...`.
That suggests extraction is not directly served from Flask's static route, or
the app runs with a different static layout.

## Current Hypotheses

- Path traversal in tar member names may write outside the extraction directory.
- Symlink or hardlink entries may make the extractor read/write outside the
  extraction directory.
- The phrase "you gib l endpoint" may mean the solve requires creating a server
  endpoint or static file that the checker can request.

## Source Review

The distribution archive was available from the platform:

```text
TARget-dist.zip
```

The relevant source:

```python
app.config['MAX_CONTENT_LENGTH'] = 1024

@app.route('/untar', methods=['POST'])
def untar_file():
    ...
    if file and (file.filename.endswith('.tar')):
        UPLOAD_FOLDER = os.path.join(os.getcwd(), 'uploads', str(int(time.time())))
        ...
        file.save(tar_path)
        subprocess.check_output(['tar', '-xf', tar_path, '-C', UPLOAD_FOLDER])
        ...
        shutil.rmtree(UPLOAD_FOLDER, ignore_errors=True)
```

Dockerfile:

```dockerfile
COPY flag /flag
RUN mv /flag /flag-`cat /proc/sys/kernel/random/uuid`.txt
```

Important consequences:

- The extractor is GNU `tar`, not Python `tarfile`.
- The upload limit applies to the whole HTTP request body, so a 1024-byte tar
  file plus multipart overhead is too large.
- The extraction directory is deleted immediately after `tar` exits.
- The flag filename is randomized as `/flag-<uuid>.txt`, so a fixed symlink to
  `/flag` is not enough.
