# Repository Guidelines

## Project Structure & Module Organization

This repository now contains two distinct CTF workspaces sharing one root, not
one cohesive application:

- `problems/<challenge>/` is the archive of solved or partially solved
  challenge folders. The repository root mostly holds shared metadata and
  lightweight entry points such as `pyproject.toml`, `uv.lock`, `main.py`,
  `CLAUDE.md`, and this guide.
- `hcmusctf2026/` is a separate event-preparation workspace for HCMUS-CTF 2026.
  It is mostly long-form operational documentation plus a few standalone solver
  notes, not a packaged program.

The notable trees under `problems/` are:

- `problems/subleq/` for reverse engineering: `chall`, visible and hidden
  SUBLEQ emulators, a Z3 solver, `REVERSING_NOTES.md`, and a writeup.
- `problems/Intro2Pcap/` for forensics: pcap, recovered HTTP objects, SQLite
  artifacts, a quiz transcript, and `solve_quiz.py`.
- `problems/NyankoDaisensou/` for misc/mobile save analysis: solver, README,
  writeup, and a very large vendored `bcsfe/` tree.
- `problems/xv6/` for pwn: `solve_monitor.py`, a writeup, `public/` service
  artifacts, and an `upstream-xv6/` kernel tree.
- `problems/dead_pixel/` for exploit development: solver, writeup, Ghidra
  output, helper scripts, and a `public/` deployment bundle.
- `problems/TARget/` and `problems/PinkBlackVault/` for web: writeups, shipped
  distribution assets, and in `TARget/` a Python solver plus crafted tarballs.
- `problems/rust-in-peace/`, `problems/ModelInversion/`, and
  `problems/morphology-1/` as single-challenge workspaces around Rust, PyTorch,
  and C++/OpenFHE artifacts.

The `hcmusctf2026/` tree currently contains:

- core planning docs: `HCMUS-CTF-2026-RESEARCH.md`,
  `HCMUS-CTF-PATTERNS.md`, `STRATEGY.md`, and `REGISTRATION.md`
- research/support docs: `intel/*.md` and `tools/*.md`
- a host bootstrap script: `setup.sh`
- standalone reference solvers: `solve_CRY1.py`, `solve_falsehood.py`,
  `solve_bootleg_aes.py`, `solve_python_is_safe.py`, and
  `solve_Cute_Quote.sh`
- one large registration PDF and a gitignored secret file:
  `ACCESS.secret.md`

Important mismatch: `hcmusctf2026/CLAUDE.md` refers to `practice/` and
`writeups/` subtrees, but those directories are not present in this checkout.
Do not assume those assets exist locally when editing or testing.

Large or vendored trees deserve path-scoped searches and surgical edits:
`problems/Intro2Pcap/http_objects/`, `problems/NyankoDaisensou/bcsfe/`,
`problems/xv6/upstream-xv6/`, `problems/xv6/public/`,
`problems/dead_pixel/ghidra_out/`, challenge dist folders such as
`Pink_Black_Vault_Heist-dist/` and `TARget-dist/`, plus generated directories
like `__pycache__/` and `__MACOSX/`. The HCMUS docs in `tools/` and `intel/`
are large but handwritten; edit them precisely rather than reformatting them
wholesale.

There is currently no repo-level `tests/` directory. Add tests there only if
logic becomes shared across challenges.

## Build, Test, and Development Commands

Use `uv` for the shared Python environment rooted at `pyproject.toml` and
`uv.lock`:

- `uv sync` installs the shared Python 3.12 dependencies currently tracked at
  the repo root: `capstone`, `pwntools`, and `z3-solver`.
- `uv run python main.py` runs the placeholder root entry point; it is only a
  smoke check, not a challenge dispatcher.
- `uv run python problems/subleq/solve.py` runs visible VM sanity checks.
- `uv run python problems/subleq/solve_real.py` runs hidden VM emulator checks
  against sample inputs.
- `uv run python problems/subleq/solve_z3.py` builds and solves the Z3
  constraints.
- `uv run python problems/TARget/solve.py --help`,
  `uv run python problems/dead_pixel/solve.py --help`,
  `uv run python problems/rust-in-peace/solve.py --help`, and
  `uv run python problems/xv6/solve_monitor.py --help` are safe CLI smoke tests
  for the scripted solvers.
- `make -C problems/morphology-1 server_new` builds the C++ challenge binary
  and requires the OpenFHE headers and libraries referenced by that Makefile.

The HCMUS workspace has different assumptions:

- `bash hcmusctf2026/setup.sh` is an Arch/Manjaro bootstrap script that runs
  `sudo pacman`, uses an AUR helper, and installs `pipx` and Ruby gems. Treat
  it as machine setup, not a routine verification step.
- `bash -n hcmusctf2026/setup.sh` is the safe syntax check after editing that
  script.
- `hcmusctf2026/solve_CRY1.py` needs `numpy`.
- `hcmusctf2026/solve_falsehood.py` needs `sympy` and `pycryptodome`.
- `hcmusctf2026/solve_bootleg_aes.py` needs `pycryptodome` plus files under the
  absent `practice/2023-archive/...` tree.
- `hcmusctf2026/solve_Cute_Quote.sh` is a placeholder curl recipe that still
  targets `http://challenge-host:3000/...`.
- `hcmusctf2026/solve_python_is_safe.py` is a local ctypes demonstration rather
  than a robust CLI harness.

Do not assume the root `uv` environment covers every challenge. For example,
`problems/ModelInversion/run.py` expects `torch` and `Pillow`,
`problems/NyankoDaisensou/solve.py` expects `requests` plus the vendored
`bcsfe/` package, and the HCMUS solvers listed above require extra packages or
missing local assets.

Solver scripts should read local assets with
`Path(__file__).resolve().parent / "filename"` so each problem directory stays
movable. This matters especially in `hcmusctf2026/`, where two scripts still
hardcode paths into a missing `practice/` tree.

HCMUS rCTF API workflow verified on 2026-05-24:

- The browser session token is stored in `localStorage["token"]`, not in a
  cookie.
- Challenge metadata can be fetched with `GET /api/v1/challs` and
  `Authorization: Bearer <token>`.
- Team state and current solves can be fetched with `GET /api/v1/users/me`
  using the same bearer token.
- Flag submission works via
  `POST /api/v1/challs/<challenge-id>/submit` with JSON body
  `{"flag":"HCMUS-CTF{...}"}` and the same bearer token.
- Never commit, log, or paste live bearer tokens or rotated team tokens into
  tracked files. Treat them the same way as `ACCESS.secret.md`.

## Coding Style & Naming Conventions

Most handwritten automation in this repo is Python, but the workspace also
contains C++, Rust, JavaScript, Docker, extracted web assets, upstream vendor
trees, and long-form Markdown research notes. Match the conventions of the
directory you are editing instead of normalizing everything to one style.

Write Python with 4-space indentation and clear, script-local constants for
binary offsets, cell indexes, and limits. Keep constants uppercase, functions
lowercase with underscores, and byte-oriented variables explicit
(`password: bytes`, `flag_bytes`). Prefer `pathlib.Path` for new path handling.
Keep comments focused on reversing facts, invariants, or non-obvious behavior.

For the HCMUS docs, preserve the evidence-first structure: factual headings,
tables where they already exist, and short operational guidance rather than
marketing prose. Avoid broad formatting passes inside extracted or vendored
trees such as `http_objects/`, `bcsfe/`, `upstream-xv6/`, `ghidra_out/`, or
`public/` service bundles unless the task explicitly targets those files.

## Testing Guidelines

No formal repo-wide test framework is configured yet. Verify changes in the
smallest relevant scope before committing:

- Python solver changes: run the touched solver or at least its `--help` or
  local harness path.
- `problems/subleq/`: use the visible, hidden, and Z3 scripts above.
- `problems/morphology-1/`: rebuild with `make`.
- `problems/xv6/`, `problems/TARget/`, `problems/dead_pixel/`, and other
  service-style folders: prefer local helper scripts or documented writeup
  steps over ad hoc remote interaction.
- `hcmusctf2026/` docs: verify referenced paths still exist, and call out any
  intentionally missing prerequisites such as the absent `practice/` tree.
- `hcmusctf2026/setup.sh`: at minimum run `bash -n`.
- `hcmusctf2026` solver edits: confirm required dependencies and local assets
  before claiming a smoke test passed.

When adding tests, use `pytest`, place files under `tests/`, and name them
`test_*.py`. Good initial candidates are reusable emulators, archive builders,
protocol parsers, and other helper code extracted out of a single challenge
directory.

## Solver Approach

Prefer elegant, efficient solutions that match the intended CTF weakness. If a
solve path needs huge CPU time, excessive RAM, or long brute force for an easy
challenge, stop and reassess the model instead of pushing harder. Use bounded
experiments, timeouts, and memory-conscious tools; large resource use is
usually a sign that the abstraction is wrong or an intended shortcut was
missed.

Assume the challenge is designed for a 36-hour CTF and a typical student
laptop or desktop. A suitable solver should run locally with ordinary CPU and
RAM, without cloud hardware, GPU-only assumptions, or overnight unbounded
search. If the approach cannot be explained as the intended weakness and cannot
be validated quickly on local hardware, treat it as the wrong model and refine
the reversing work before scaling.

When working under `hcmusctf2026/`, read `STRATEGY.md` and
`HCMUS-CTF-PATTERNS.md` early. That subtree is optimized around event-time
breadth, pattern-matching, and fast triage rather than deep one-challenge
tunnel vision.

Validate ideas in small contexts before scaling them. Build a tiny harness,
sample, or reduced-dimension version first, confirm the signal is real, and
only then run the full solve. If the small experiment is slow, noisy, or
resource-heavy, fix the approach before increasing the input size.

## Commit & Pull Request Guidelines

This repository has no commit history yet, so no project-specific commit
convention is established. Use concise imperative messages such as
`Add hidden VM emulator` or `Document SUBLEQ memory layout`.

Pull requests should include a short description, the commands run for
verification, and any changed offsets or assumptions. Include relevant excerpts
from `REVERSING_NOTES.md` when solver behavior changes.

## Security & Configuration Tips

Treat challenge binaries, Torch pickles, archives, Docker/service bundles,
recovered artifacts, and the HCMUS registration PDF as untrusted input. Do not
execute shipped binaries directly unless necessary; prefer emulator-based or
source-first analysis where possible.

`hcmusctf2026/ACCESS.secret.md` and any `*.secret.*` files are intentionally
gitignored. Never commit them, rename them into tracked paths, or copy their
contents into tracked documentation.

Avoid committing generated caches, virtual environments, bulky derived
artifacts, or new dumps extracted from the large challenge asset folders unless
they are part of the intended repository state. Do not auto-download missing
practice archives or unrelated media/binary blobs by default. Official
challenge distribution archives, player bundles, and other files needed to
solve the active challenge may be downloaded when the user explicitly
authorizes it or when local source review is clearly required by the task.
Probe live competition infrastructure only when the task explicitly requires
it, and treat every downloaded artifact as untrusted input.
