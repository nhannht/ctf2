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

Use `uv` for dependency management and execution. Always work through the
project-local `.venv` created by `uv venv`, and prefer `uv run ...` or
`.venv/bin/...` over invoking `python` or `pip` directly:

- `uv venv` creates or refreshes the project-local virtual environment at `.venv`.
- `uv sync` installs Python 3.12 dependencies from `pyproject.toml` and `uv.lock`.
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

Prefer elegant, efficient solutions that match the intended CTF weakness. If a
solve path needs huge CPU time, excessive RAM, or long brute force for an easy
challenge, stop and reassess the model instead of pushing harder. Use bounded
experiments, timeouts, and memory-conscious tools; large resource use is usually
a sign that the abstraction is wrong or an intended shortcut was missed.

Assume the challenge is designed for a 36-hour CTF and a typical student
laptop or desktop. A suitable solver should run locally with ordinary CPU and
RAM, without cloud hardware, GPU-only assumptions, or overnight unbounded
search. If the approach cannot be explained as the intended weakness and cannot
be validated quickly on local hardware, treat it as the wrong model and refine
the reversing work before scaling.

Validate ideas in small contexts before scaling them. Build a tiny harness,
sample, or reduced-dimension version first, confirm the signal is real, and
only then run the full solve. If the small experiment is slow, noisy, or
resource-heavy, fix the approach before increasing the input size.

When web research is useful, search for technical pattern knowledge, prior art,
and general reversing techniques relevant to the challenge's structure. Do not
search for leaked answers, direct writeups, or challenge-specific solves. Use
the web to understand the class of problem better, not to bypass the solve.

## Communication Guidelines

Keep notes, writeups, prompts, code comments, and filenames clearly scoped to
authorized CTF challenge work. Prefer precise challenge terminology such as
`solver`, `payload`, `emulator`, `reversing note`, `primitive`, `kernel read`,
`memory disclosure`, `sandbox`, and `local reproduction` when those terms
accurately describe the work.

Avoid sensational, broad, or real-world operational phrasing when a narrower
CTF description is more accurate. Do not describe work as targeting real
systems, persistence, stealth, credential theft, deployment, or evasion unless
that is explicitly part of an authorized challenge artifact and is necessary to
explain the solution. When discussing remote services, identify them as the
challenge service and include the provided host, port, and protocol rather than
generic real-world attack language.

Generated code should be self-documenting and factual. Comments should explain
challenge assumptions, offsets, invariants, VM behavior, and local validation
steps. Do not add comments or variable names whose purpose is to disguise what
the code does; if a behavior is sensitive or risky, document the CTF context and
the local safety boundary instead.

## Commit & Pull Request Guidelines

This repository has no commit history yet, so no project-specific commit convention is established. Use concise imperative messages such as `Add hidden VM emulator` or `Document SUBLEQ memory layout`.

Pull requests should include a short description, the commands run for verification, and any changed offsets or assumptions. Include relevant excerpts from `REVERSING_NOTES.md` when solver behavior changes.

## Security & Configuration Tips

Treat `chall` as an untrusted binary. Do not execute it directly unless necessary; prefer emulator-based analysis. Avoid committing generated caches, virtual environments, or bulky derived artifacts already covered by `.gitignore`.
