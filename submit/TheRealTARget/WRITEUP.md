# The Real TARget

Category: `web`  
Status: `solved`  
Flag: `HCMUS-CTF{CVE-2026-7774_Fr3sh_0ut_0f_th3_0v3n!}`

## Summary

The previous `TARget` intuition was the trap. This version does not shell out to
GNU `tar`, does not reuse a shared extraction directory, and runs on
`python:3.14.5`, where the older `tarfile` traversal bugs were already patched.

The real bug was a newer `tarfile` destination-rewrite issue that survived in
`3.14.5`. By abusing the empty-name symlink chain from `gh-149486`, we could
replace the extraction destination with a path that resolved back to `/app`,
plant a malicious `/app/gzip.py`, then force a later request to import our file
instead of the standard library `gzip` module. That import hook read the flag
and dropped it into Flask’s static directory.

## Artifacts

- Solver: `problems/TheRealTARget/solve.py`
- Local replay harness: `problems/TheRealTARget/harness.py`
- Challenge dist archive: `problems/TheRealTARget/The-Real-TARget-dist.zip`
- Relevant shipped files:
  - `src/app.py`
  - `Dockerfile`
  - `nginx/default.conf`

## Key Observation

The challenge title was literal. `The Real TARget` points at `realpath`-based
`tarfile` filtering, not just “another tar bug.”

That mattered because the obvious archive tricks were already dead on the
shipped runtime:

- no more shared same-second extraction directory
- direct outside symlink writes rejected
- the June 2025 `tarfile` bypass set already patched in `python:3.14.5`

So the correct model was “find the newer bug that still survives after the
`realpath` hardening,” not “reuse the old TARget exploit.”

## Early Wrong Model

The previous `TARget` challenge strongly suggested reusing the old GNU tar /
shared-directory race. That branch died fast on the shipped stack:

- extraction used Python `tarfile`, not GNU `tar`
- each request got a fresh UUID-scoped directory
- the service deleted that tree in `finally`
- the June 2025 traversal tricks were already patched in `python:3.14.5`

That failure mattered because it forced the search onto a newer `tarfile`
destination-rewrite bug instead of squeezing harder on a dead exploit.

## Solve Path

### 1. Confirm the old paths are dead

Shipped source:

```python
with tarfile.open(fileobj=file, mode='r') as tar:
    tar.extractall(path=UPLOAD_FOLDER)
...
finally:
    shutil.rmtree(os.path.join(os.getcwd(), 'uploads', user_id), ignore_errors=True)
```

Important consequences:

- extraction uses Python `tarfile`, not GNU `tar`
- each request gets a fresh `uploads/<uuid>/<uuid>` directory
- the service deletes that tree in `finally`

That immediately rules out the old race from the previous challenge.

Local replay on `python:3.14.5` also killed the obvious direct-symlink writes:

- bare symlink to `/flag` -> rejected
- direct symlink toward `/app/static` -> `LinkOutsideDestinationError`

### 2. Target the newer `tarfile` destination-rewrite bug

The live `3.14.5` image was still vulnerable to the later `gh-149486` issue.
That bug combines two mistakes:

- validation checks the original `member.linkname` with `realpath()`
- extraction writes the normalized `normpath()` result
- empty-name symlink members can replace the extraction destination itself

In this app, that lets us redirect:

```text
/app/uploads/<user>/<upload>
```

back to `/app`.

### 3. Plant a malicious `gzip.py`

Once the extraction destination resolves to `/app`, we can write a file outside
the intended upload tree. The useful target is not a template or config file.
It is `/app/gzip.py`.

Why `gzip`:

- `shutil` has already imported `bz2` and `lzma`
- `gzip` is still a lazy import target
- a later gzipped tar request forces Python to import `gzip`

So the exploit becomes:

1. first archive rewrites the destination and plants `/app/gzip.py`
2. second request sends a gzipped tar stream
3. a worker that has not imported stdlib `gzip` yet imports `/app/gzip.py`
4. malicious `gzip.py` reads `/flag-*` and writes the contents to
   `/app/static/f`

### 4. Read the flag from Flask static files

Once `/app/static/f` exists, the last step is simple:

```text
GET /static/f
```

The challenge does not need code execution inside the request handler itself.
The import side effect is enough.

## Proof

Final live run against `http://chall.blackpinker.com:20528`:

- stage 1 upload returned `200`
- first stage 2 trigger request returned `500`
- flag became readable at `/static/f`

The final flag was then submitted successfully through the platform API and
accepted as `goodFlag`.

## Reproduction

Run the solver:

```bash
uv run python problems/TheRealTARget/solve.py \
  --url http://chall.blackpinker.com:20528
```

Use the harness for local replay on the shipped runtime:

```bash
uv run python problems/TheRealTARget/harness.py
```

The printed solve flow looks like this:

```text
stage1_status=200
stage2_attempt=1 status=500 ...
HCMUS-CTF{CVE-2026-7774_Fr3sh_0ut_0f_th3_0v3n!}
```

## References

- CPython issue: `gh-149486`
- CPython patch: `gh-149487`
- older patched `tarfile` hardening series:
  `gh-135034` / `gh-135037`

## Files

- `problems/TheRealTARget/solve.py`
- `problems/TheRealTARget/harness.py`
