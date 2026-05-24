# notebook

## Files

- `prob.cc` is the challenge source.
- `prob` is the shipped PIE binary.
- The menu is:
  - `0`: switch book
  - `1`: write note
  - `2`: read note
  - `3`: erase note
  - `4`: discard book
  - `5`: tag note
  - `6`: exit

## Why the hint matters

The two useful hints are:

- challenge name: `notebook`
- text: `i hate fmstr challenge, heap challenge is good :D`

That rules out the obvious wrong path:

- there is no user-controlled `printf`
- the bug is not a format-string sink
- the real attack surface is the custom heap allocator plus the `book` / `note`
  object layout

So the right model is:

- custom allocator corruption
- object overlap
- heap metadata abuse

## Object layout

The core objects are:

```cpp
typedef struct Note {
    uint64_t size;
    char *data;
} Note;

typedef struct NoteBook {
    Note notes[48];
} NoteBook;
```

Important sizes:

- `sizeof(Note) = 0x10`
- `sizeof(NoteBook) = 48 * 0x10 = 0x300`
- allocator chunk size for a book:
  - `aln(0x300) = 0x310`

The allocator is a custom `Cage` allocator with:

- a randomized `mmap` base
- a `top` chunk
- size-segregated `set<Block*>` bins
- manual coalescing via `priv_size` / `curr_size`

## The allocator bug direction

The allocator keeps a stale `top` model during a bad free sequence.

The first confirmed useful sequence is:

1. create books `0`, `1`, `2`, `3`
2. discard book `2`
3. discard book `1`
4. discard book `3`

With four adjacent book chunks laid out as:

- `A = book0`
- `B = book1`
- `C = book2`
- `D = book3`

the free order `C -> B -> D` causes:

- `B` and `C` to merge into a free `0x620` chunk stored in bins
- `D` free to consolidate with that stale `0x620` chunk and the old top
- `top` to move to `C`
- but the merged `B` chunk remains present in bins as a stale free chunk

So after this sequence, local tracing confirmed:

- a free `0x620` bin chunk still exists at `B`
- allocator `top` also effectively starts at `C`

That is the core allocator inconsistency.

## Proven local overlap primitive

After the bad free sequence, the following allocations are confirmed locally.

### Step 1

From book `0`, allocate note slot `0` with size `0x2f8`.

That requests allocator size `0x310`, and it comes from the stale `0x620`
 chunk at `B`, splitting it into:

- allocated `0x310` at `B`
- remainder `0x310` at `C`

### Step 2

Switch to a fresh book `4`.

Creating book `4` allocates exactly that `0x310` remainder at `C`.

So book `4` now lives inside the region that the allocator also still treats as
 top-derived state.

### Step 3

Go back to book `0`, allocate another note with a slightly smaller size:

- requested note size: `0x2c0`
- allocator chunk size: `0x2d0`

This second note is allocated from the stale top region at `C`.

Because book `4` also lives at `C`, this note overlaps the beginning of the
 `book4->notes[]` array.

### Step 4

The overlap payload must not zero out everything blindly.

One failed attempt used a full `0x2f8` overlap and consumed the entire stale
 top chunk, leaving no room for book `4` to create a real note afterward.

The corrected working version uses `0x2c0`, leaving enough top space for a
 small `0x30` chunk.

### Step 5

From book `4`, create note slot `0` with size `0x18`.

That note is allocated from the remaining small top chunk.

Because the overlapping note from book `0` covers the front of `book4`, reading
 the overlapping note leaks the real metadata of `book4->notes[0]`.

## Confirmed leak

Local trace output from reading the overlapping note showed:

- first qword: `0x18`
- second qword: a real heap pointer, for example:
  - `0x000002816be40900`

That is:

- the `size` field of `book4->notes[0]`
- the `data` pointer of `book4->notes[0]`

So the overlap-to-heap-leak primitive is real and stable locally.

## What is confirmed now

Confirmed:

- this is a heap challenge, not a format-string challenge
- the allocator inconsistency is real
- free order `discard 2 -> discard 1 -> discard 3` is useful
- `book4` can be placed into the stale `C` chunk
- a second book `0` note can overlap `book4`
- that overlap can leak a real heap pointer from `book4->notes[0]`

Not solved yet:

- no PIE leak yet
- no libc leak yet
- no code execution yet
- no flag yet

## Current blocker

The current primitive is a heap-only overlap and heap-only leak.

The next step is to turn the overlapped `book4->notes[]` metadata into a
 stronger primitive, most likely one of:

- arbitrary read through forged `size` / `data`
- controlled free of an arbitrary heap pointer inside the cage allocator
- overlap into a global / PIE pointer-bearing object for a base leak

The challenge is already beyond pure reversing. The remaining work is exploit
 engineering from the confirmed overlap and leak.
