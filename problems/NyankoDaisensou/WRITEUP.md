# Nyanko Daisensou Writeup

## Summary

This challenge is a Battle Cats save-state checker, not a plain string puzzle.
The checker accepts a real `transfer_code` and `confirmation_code`, downloads
the corresponding save from the official PONOS transfer service, and then checks
for a hacked Cheetah Cat state.

Final flag:

`HCMUS-CTF{=^._.^=|||https://youtu.be/2yJgwwDcgV8?si=QOHkJZq6SsVX7T8H|||=^._.^=}`

## Artifacts

- Checker: `https://nyanko.blackpinker.com/`
- Hint video embedded in the challenge page:
  `https://www.youtube.com/watch?v=mY0DLG19kPI`
- Tutorial linked from that hint video:
  `https://www.youtube.com/watch?v=BL7bhXlz4YI`

The hint video establishes that Cheetah Cat is a cheat-detection / hacked-state
unit, and its description explicitly links to the second tutorial video for the
unlock method.

## Key Findings

1. The checker only accepts real Battle Cats transfer credentials.
2. The cat the checker wants is save cat ID `673`.
3. Unlocking Cheetah alone is not enough.
4. Normal speed-related state does not pass:
   - `Speed Up` item count
   - endless `Speed Up`
   - `dojo_3x_speed`
   - Officers' Club gold pass
   - ordinary cat levels/forms
   - valid `Unit Speed Up` combos
5. The intended route is a hacked per-unit state, matching the GameGuardian
   tutorial hint.

## Winning Condition

The successful save had:

- Cheetah unlocked as cat ID `673`
- An injected talent entry on Cheetah itself:
  - ability ID `27`
  - level `10`

In Battle Cats talent text, this is the `Move Speed Up` talent.

That state is not legitimate for Cheetah, which is exactly why it matches the
challenge theme and checker text:

`You have the Cheetah cat, but it needs a speed boost...`

## Solver

The repo-local solver is:

- [solve.py](/home/larvartar/nhannht-projects/ctf2/problems/NyankoDaisensou/solve.py)

The final file is intentionally minimal. It only builds the winning save state,
uploads it through the official transfer flow, and submits the resulting
transfer credentials to the challenge service.

## Reproduction

1. Get a fresh `cf_clearance` cookie for the checker from your browser.
2. Export it as `CF_CLEARANCE`.
3. Run:

```bash
.venv/bin/python problems/NyankoDaisensou/solve.py
```

Expected checker response:

```json
{
  "flag": "HCMUS-CTF{=^._.^=|||https://youtu.be/2yJgwwDcgV8?si=QOHkJZq6SsVX7T8H|||=^._.^=}",
  "message": "You have the Cheetah cat! Here is your flag:"
}
```

## Notes

- The second tutorial video points to GameGuardian-style memory editing.
- The transferable state that mattered here was not a battle item or global
  speed flag; it was an impossible talent attached to Cheetah in the uploaded
  save.
