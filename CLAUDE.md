# Repository Guidelines

## Project Structure & Module Organization

This repository is a small Python CTF workspace. Keep challenge files under
`problems/<challenge-name>/` and reserve the repository root for shared project
metadata such as `pyproject.toml`, `uv.lock`, `.gitignore`, and this guide.

- `problems/subleq/` contains the `chall` binary, SUBLEQ emulators, Z3 solver,
  and `REVERSING_NOTES.md`.
- `problems/100goilays/` contains the original `100goilays.zip` challenge
  archive.

There is currently no `tests/` directory. Add tests there if shared emulator logic is extracted from the scripts.

## Build, Test, and Development Commands

Use `uv` for dependency management and execution:

- `uv sync` installs Python 3.13 dependencies from `pyproject.toml` and `uv.lock`.
- `uv run python main.py` runs the default entry point.
- `uv run python problems/subleq/solve.py` runs visible VM sanity checks.
- `uv run python problems/subleq/solve_real.py` runs hidden VM emulator checks against sample inputs.
- `uv run python problems/subleq/solve_z3.py` builds and solves the Z3 constraints.

Solver scripts should read local assets with `Path(__file__).resolve().parent / "filename"` so each problem directory stays movable.

## Coding Style & Naming Conventions

Write Python with 4-space indentation and clear, script-local constants for binary offsets, cell indexes, and limits. Keep constants uppercase, functions lowercase with underscores, and byte-oriented variables explicit (`password: bytes`, `flag_bytes`). Prefer `pathlib.Path` for new path handling. Keep comments focused on reversing facts, invariants, or non-obvious VM behavior.

## Testing Guidelines

No formal test framework is configured yet. For now, use the script sanity checks above before committing changes. When adding tests, use `pytest`, place files under `tests/`, and name them `test_*.py`. Good initial coverage targets are `load_initial()`, VM halt/error conditions, fixed trace behavior, and known sample input outcomes.

## Solver Approach

### No brute force, no resource-heavy solutions (HARD RULE)

CTF challenges in this repo are designed for a 36-hour student-PC competition.
The intended solve is never cheap to FIND - it demands intelligence, creativity,
careful reading, and a flash of insight from the hunter. But once found, it is
always cheap to RUN: one payload, one script, one query. The difficulty lives in
the recognition, not in the compute.

If your candidate path needs any of the following, the path is wrong - stop and
re-read the source:

- GPU brute force (hashcat, john, cuda kernels, custom CUDA/OpenCL)
- CPU brute force over a keyspace larger than ~2^28
- Multi-hour solver runtimes (Z3/SAT/SMT in the > 10 minute range counts)
- Multi-GB RAM working sets
- Rainbow tables, precomputed dictionaries beyond rockyou-tier
- Distributed compute, cloud GPU rental, or "rent an A100"
- Tens of millions of network requests against the instance
- Asking the user to install hashcat / john / mining-grade tooling

When you find yourself estimating throughput in "H/s", "keys/sec", "guesses/min",
or comparing GPU vs CPU - STOP. That estimation itself is the signal that you
have missed the real bug. Re-read the dist, look for the misuse pattern, the
overlooked endpoint, the prototype quirk, the off-by-one, the algebraic
shortcut, the type-confusion. The intended solve is always a recognition
problem - hard to see, trivial to run once seen. Difficulty is paid in thinking,
not in cycles.

Reason: real example from this repo. Pink Black Vault Heist exposed
`JWT_SECRET = crypto.randomBytes(5)` (40-bit) as bait. The intended solve was
a Cap'n Web prototype-path traversal that returned the flag in one WebSocket
message, no auth, no brute force. Anyone who started running hashcat lost
hours and still would not have finished inside the instance window.

### How to apply

1. Read the dist source end to end before writing any solver.
2. Identify the framework / library being misused. Pull its docs (Context7 or
   the GitHub README) and look for "do not do X" warnings.
3. List the surface that is reachable WITHOUT the obvious auth gate. Methods,
   prototype chain, static vs instance, exposed config endpoints, debug routes.
4. The intended bug is usually in (3), not in the crypto primitive that screams
   "brute me".
5. Only after exhausting (1)-(4) for a full read-through do you bring up
   compute. And even then: present the brute-force estimate to the user with
   wall-clock and dollars, and ask. Never silently install hashcat or kick off
   a long run.

### Solver hygiene

Validate ideas in small contexts before scaling them. Build a tiny harness,
sample, or reduced-dimension version first, confirm the signal is real, and
only then run the full solve. If the small experiment is slow, noisy, or
resource-heavy, fix the approach before increasing the input size.

Use bounded experiments, timeouts, and memory-conscious tools. Cap any solver
at 60 seconds wall clock on first run. If it does not finish, the abstraction
is wrong - do not raise the cap, change the approach.

- BAD: "JWT_SECRET is 5 bytes (40-bit), let me set up hashcat with rockyou
  and the JWT module, ETA 6 hours on this machine."
- GOOD: "JWT_SECRET is 5 bytes - that is bait. What else does this RPC
  surface expose? Reading the class... `getVaultSecret` does not use `this`
  and the RPC library walks the prototype chain. One WebSocket frame solves it."
- BAD: install hashcat / john / gpu drivers without asking.
- GOOD: if compute looks unavoidable, paste the wall-clock estimate and the
  install command into chat, then wait for the user to authorize.

## Commit & Pull Request Guidelines

This repository has no commit history yet, so no project-specific commit convention is established. Use concise imperative messages such as `Add hidden VM emulator` or `Document SUBLEQ memory layout`.

Pull requests should include a short description, the commands run for verification, and any changed offsets or assumptions. Include relevant excerpts from `REVERSING_NOTES.md` when solver behavior changes.

## Security & Configuration Tips

Treat `chall` as an untrusted binary. Do not execute it directly unless necessary; prefer emulator-based analysis. Avoid committing generated caches, virtual environments, or bulky derived artifacts already covered by `.gitignore`.
