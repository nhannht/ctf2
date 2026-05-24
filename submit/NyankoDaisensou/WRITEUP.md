# Nyanko Daisensou

Category: `misc`  
Status: `solved`  
Flag: `HCMUS-CTF{=^._.^=|||https://youtu.be/2yJgwwDcgV8?si=QOHkJZq6SsVX7T8H|||=^._.^=}`

Source bundle: `https://github.com/nhannht/ctf2/tree/master/submit/NyankoDaisensou`

## Summary

This was a Battle Cats save-state challenge, not a guessing challenge. The
checker wanted a real `transfer_code` and `confirmation_code`, downloaded the
corresponding save from the official PONOS transfer service, and then looked
for a hacked Cheetah Cat state.

The title and the hint video were the real guide. Cheetah Cat is already a
cheat-themed unit, and the linked tutorial pointed toward GameGuardian-style
memory editing rather than normal in-game progression. The winning state was
not “make the account faster” in a generic way. It was an impossible talent
attached directly to Cheetah.

## Artifacts

- Checker: `https://nyanko.blackpinker.com/`
- Challenge hint video: `https://www.youtube.com/watch?v=mY0DLG19kPI`
- Tutorial linked from the hint: `https://www.youtube.com/watch?v=BL7bhXlz4YI`
- Solver: `problems/NyankoDaisensou/solve.py`
- Supporting notes: `problems/NyankoDaisensou/README.md`

## Key Observation

The checker only accepts real Battle Cats transfer credentials, so the solve
has to produce a valid remote save, not just a locally edited blob. Once that
was clear, the remaining question was what hacked state the checker actually
wanted.

The decisive clue was the tutorial path from the challenge page. It did not
point to ordinary speed-up items or global account boosts. It pointed to
per-unit tampering. In Battle Cats terms, that meant attaching a speed-related
talent directly to Cheetah Cat.

## Early Wrong Model

Before that clue clicked, the natural reading was “make the account faster in
any way the game understands.” We tested the obvious account-wide and
legitimate-state branches first:

- `Speed Up` item count
- infinite `Speed Up`
- `dojo_3x_speed`
- Officers' Club state
- normal unit level / form changes
- valid Unit Speed Up combinations

Those failures mattered because they showed the checker was not rewarding a
generic fast account. It wanted an impossible per-unit talent state.

## Solve Path

### 1. Confirm what the checker validates

The checker accepts a `transfer_code` and `confirmation_code`, fetches the save
behind them, and evaluates that remote state. That immediately rules out fake
credentials and most purely local patching ideas.

### 2. Identify the target unit

The target cat is save cat ID `673`, Cheetah Cat. The challenge text

```text
You have the Cheetah cat, but it needs a speed boost...
```

already hints that merely unlocking the unit is not enough.

### 3. Rule out the obvious speed-state dead ends

These did not satisfy the checker:

- `Speed Up` item count
- endless `Speed Up`
- `dojo_3x_speed`
- Officers' Club gold-pass state
- ordinary cat level or form changes
- valid Unit Speed Up combinations

That is why this challenge was not just “set every speed field to max.”

### 4. Apply the impossible talent state

The winning save state was:

- Cheetah unlocked as cat ID `673`
- one injected talent on Cheetah itself
- talent ability ID `27`
- talent level `10`

In Battle Cats talent text, ability `27` is `Move Speed Up`. That is not a
legitimate talent on Cheetah, which is exactly why it matches the challenge
theme.

The final solver writes that state directly:

```python
cat = save.cats.cats[CHEETAH_ID]
cat.unlocked = 1
cat.talents = [Talent(MOVE_SPEED_UP_TALENT_ID, MOVE_SPEED_UP_TALENT_LEVEL)]
```

### 5. Upload the save and submit the transfer credentials

The solver uses the official transfer flow to create an account, upload the
patched save, recover the resulting transfer codes, and submit them to the
checker.

## Proof

We preserved one exact successful live solver print from the competition run:

```json
{
  "transfer_code": "09ff5c538",
  "confirmation_code": "4065",
  "result": {
    "flag": "HCMUS-CTF{=^._.^=|||https://youtu.be/2yJgwwDcgV8?si=QOHkJZq6SsVX7T8H|||=^._.^=}",
    "message": "You have the Cheetah cat! Here is your flag:"
  }
}
```

## Reproduction

Install the missing save-editor dependency into the project `.venv`:

```bash
uv pip install bcsfe
```

Then run the exact solver entry point:

```bash
CF_CLEARANCE='your_cookie_here' .venv/bin/python problems/NyankoDaisensou/solve.py
```

The solver does four things:

1. create a synthetic Battle Cats account
2. inject `Talent(27, 10)` onto Cheetah `673`
3. upload the patched save through the official transfer flow
4. print the resulting `transfer_code`, `confirmation_code`, and checker result

If the local environment is missing `bcsfe`, the import fails before any of the
game-transfer logic runs. That was an environment issue, not a solver-model
issue.

## Files

- `problems/NyankoDaisensou/solve.py`
- `problems/NyankoDaisensou/README.md`
