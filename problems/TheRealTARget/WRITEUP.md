# The Real TARget

Status: solved.

Flag: `HCMUS-CTF{CVE-2026-7774_Fr3sh_0ut_0f_th3_0v3n!}`

## Challenge framing

- Category: `web`
- Title hint: `The Real TARget`
- Description: `I gib you 1 endpoint, you gib me flag.`
- Live instance observed during analysis: `http://chall.blackpinker.com:20528`
- Dist archive downloaded with explicit user authorization:
  [The-Real-TARget-dist.zip](/home/ubuntu/nhannht-projects/ctf2/problems/TheRealTARget/The-Real-TARget-dist.zip)

The title strongly suggests this is not the previous GNU `tar` race again.
`REAL` is likely pointing at Python's `realpath`-based extraction checks.

## Shipped source analysis

Relevant files:

- [app.py](/home/ubuntu/nhannht-projects/ctf2/problems/TheRealTARget/dist/The-Real-TARget-dist/src/app.py)
- [Dockerfile](/home/ubuntu/nhannht-projects/ctf2/problems/TheRealTARget/dist/The-Real-TARget-dist/Dockerfile)
- [default.conf](/home/ubuntu/nhannht-projects/ctf2/problems/TheRealTARget/dist/The-Real-TARget-dist/nginx/default.conf)

Core app logic:

```python
from flask import Flask, request, jsonify
import os, shutil, uuid, tarfile

app = Flask(__name__)
app.config['MAX_CONTENT_LENGTH'] = 1024

@app.route('/untar', methods=['POST'])
def untar_file():
    if 'file' not in request.files:
        return jsonify({'error': 'No file part'}), 400
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No selected file'}), 400
    if file and (file.filename.endswith('.tar')):
        user_id = uuid.uuid4().hex
        upload_id = uuid.uuid4().hex
        UPLOAD_FOLDER = os.path.join(os.getcwd(), 'uploads', user_id, upload_id)
        try:
            with tarfile.open(fileobj=file, mode='r') as tar:
                tar.extractall(path=UPLOAD_FOLDER)
            return jsonify({'message': 'File untarred successfully'}), 200
        except Exception as e:
            return jsonify({'error': 'File untarred unsuccessfully'}), 500
        finally:
            shutil.rmtree(os.path.join(os.getcwd(), 'uploads', user_id), ignore_errors=True)
    else:
        return jsonify({'error': 'Invalid file type. Only TAR files are allowed.'}), 400
```

Important differences from the previous `TARget`:

- Extraction uses Python `tarfile.extractall()`, not a `subprocess` call to GNU
  `tar`.
- Each request extracts into a fresh random path:
  `uploads/<uuid4>/<uuid4>`.
  This removes the previous same-second shared-directory race.
- Files are deleted in `finally`, so an exploit must create a side effect
  outside `uploads/<uuid4>`.
- The app still has only one interesting route: `POST /untar`.

Container observations:

- Base image in the shipped Dockerfile is `python:3.14.5`.
- `gunicorn` and `flask` are installed directly with `pip`.
- `/app` is `chmod 1775` and owned `root:dat2phit`.
- The service runs as user `dat2phit`.
- There is a front `nginx` proxy, so `/` returning 404 is expected.

## Live endpoint reconnaissance

Observed behavior on the live instance:

- `GET /` returns 404.
- `GET /untar` returns `405 Allow: POST, OPTIONS`.
- `POST /untar` without a file returns `{"error":"No file part"}`.
- `OPTIONS /untar` returns 200.
- The file size limit is real: payloads over about 1 KiB receive
  `413 {"error":"File too large. Max size is 1KB."}`.
- Gzipped tar streams are accepted because `tarfile.open(..., mode='r')`
  autodetects the compression format from the stream.

This means practical exploits need very small archives and should usually use
`w:gz`.

## Early exploit hypotheses and results

### 1. Previous GNU tar race

Rejected.

Reason:

- The old challenge was exploitable because requests that landed in the same
  second shared the same extraction directory.
- This version uses two fresh UUIDs per request, so no shared directory exists.

### 2. Simple traversal or absolute symlink write

Rejected.

Direct tests:

- bare symlink to `/flag` -> server returned 500
- bare symlink to `/` -> server returned 500
- unsafe symlink target like `../tmp/x` -> server returned 500

### 3. Flask custom static route

Not present as a normal file-backed route, but default Flask `/static/...` may
still matter if we ever gain an arbitrary write into `/app/static`.

Observed behavior so far:

- `/static/` returned 404
- `/static/etc/passwd` returned 404

This only proves the files do not exist yet. It does not prove Flask static
serving is disabled.

## Web research that changed the model

The challenge title likely points at the `realpath`-based tarfile filter work
that landed in CPython around June 2025.

The most relevant upstream patch set is:

- CPython PR `gh-135034` / `gh-135037`
- It addresses:
  - `CVE-2024-12718`
  - `CVE-2025-4138`
  - `CVE-2025-4330`
  - `CVE-2025-4517`

Key upstream clue from the patch:

- Python's `tarfile` extraction filter checks paths using `realpath`.
- The challenge title `The Real TARget` is probably a deliberate hint toward
  `realpath`, not just the word `tar`.

Useful upstream artifact:

- `https://patch-diff.githubusercontent.com/raw/python/cpython/pull/135037.patch`

Two important regression tests from that patch:

- `test_exfiltration_via_symlink()` for `CVE-2025-4138`
- `test_realpath_limit_attack()` for `CVE-2025-4517`

## Exact Python 3.14.5 behavior validated locally

I inspected the actual `tarfile` code shipped in the current
`python:3.14.5` image.

The key function is `_get_filtered_attrs()`. Relevant behavior:

- it strips leading `/` from names
- it rejects paths outside the extraction root
- it rejects absolute link targets
- it normalizes link targets with `os.path.normpath`
- it resolves link checks with
  `os.path.realpath(..., strict=os.path.ALLOW_MISSING)`

This is important because it means the current `python:3.14.5` image already
contains the June 2025 hardening, including the `ALLOW_MISSING` change.

That immediately weakens the initial assumption that the live box is trivially
vulnerable to one of the published pre-fix `tarfile` bugs.

## Local harness and reproduced cases

Local helper used for replay:

- [harness.py](/home/ubuntu/nhannht-projects/ctf2/problems/TheRealTARget/harness.py)

Validated on `python:3.14.5` in Docker:

### `exfiltration`

Archive layout:

- `escape -> link/link/../../link-here`
- `link -> ./`

Result on current `python:3.14.5`:

- extraction succeeds
- resulting symlink is normalized to `escape -> link-here`
- no outside effect occurs

This matches the patched behavior from `CVE-2025-4138`.

### `chmod_outside`

Archive layout:

- `a/pwn -> .`
- `a/pwn/` as a directory
- `a/pwn -> x/../`
- `a/x -> ../`

Result on current `python:3.14.5`:

- extraction succeeds
- the final tree remains inside the destination
- no outside chmod/utime side effect was observed

This matches the patched behavior from `CVE-2024-12718`.

### `simple_static_write`

Archive layout:

- `static -> ../../app/static`
- `static/poc.txt`

Result on current `python:3.14.5`:

- extraction fails with `LinkOutsideDestinationError`

This confirms there is no trivial "write into `/app/static` through a direct
symlink" primitive on a patched runtime.

## Solved path

The intended bug is newer than the June 2025 `tarfile` bypass set.
The live `python:3.14.5` image is still vulnerable to `gh-149486`, fixed only
after the `3.14.5` release:

- `tarfile.data_filter()` validates the original `member.linkname` with
  `realpath()`, but writes the normalized `normpath()` value to disk.
- It also mishandles empty-name symlink members and allows replacing the
  extraction destination directory itself with a symlink.

That gives a clean exploit chain on this app:

1. Use the empty-name symlink chain from `gh-149486` to redirect
   `UPLOAD_FOLDER=/app/uploads/<user>/<upload>` back to `/app`.
2. Through that redirected destination, write `/app/gzip.py`.
3. `gzip` is the useful lazy import here:
   `shutil` already imports `bz2` and `lzma` at process start, but not `gzip`.
4. Send a second request containing a gzipped tar stream.
5. A worker that has not yet imported `gzip` loads `/app/gzip.py` instead of
   the stdlib module.
6. Malicious `gzip.py` reads `/flag-*` and writes the contents to
   `/app/static/f`.
7. Read `http://chall.blackpinker.com:<port>/static/f`.

Why the empty-name chain climbs exactly to `/app`:

- The app extracts to `/app/uploads/<user>/<upload>`.
- The symlink chain makes `<upload>` become `a/b`.
- Inside `/app/uploads/<user>`, `a -> ..`.
- Inside `/app/uploads`, `b -> ..`.
- Therefore `/app/uploads/<user>/<upload>` resolves to `/app`.

That is enough to plant a file directly under `/app`.

## Live exploit result

The final live run against `http://chall.blackpinker.com:20528` succeeded with:

- stage 1 upload status `200`
- first stage 2 trigger request status `500`
- flag exposed at `/static/f`

The challenge was then submitted successfully through the authenticated rCTF
API session and accepted as `goodFlag`.

## Automation

Working solver:

- [solve.py](/home/ubuntu/nhannht-projects/ctf2/problems/TheRealTARget/solve.py)

It uses:

- stage 1 as a bzip2-compressed tar to avoid importing `gzip`
- stage 2 as a gzipped tar to trigger `import gzip`
- repeated stage 2 requests to account for Gunicorn worker distribution

## References

- CPython issue `gh-149486`:
  `https://github.com/python/cpython/issues/149486`
- CPython patch `gh-149487`:
  `https://patch-diff.githubusercontent.com/raw/python/cpython/pull/149487.patch`
- CPython patch: `https://patch-diff.githubusercontent.com/raw/python/cpython/pull/135037.patch`
- CPython issue: `https://github.com/python/cpython/issues/135034`
- Flask app source:
  [app.py](/home/ubuntu/nhannht-projects/ctf2/problems/TheRealTARget/dist/The-Real-TARget-dist/src/app.py)
