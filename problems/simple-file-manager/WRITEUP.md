# simple file manager

## Status

This is an analysis writeup, not a finished solve. The main bug is confirmed,
local reproduction matches the remote runtime model, and there are working heap,
libc, and allocator-control primitives. The missing piece is the final glibc
sink that turns those primitives into a clean flag read or code execution.

## Challenge Setup

The provided deployment is minimal:

- Base image: `ubuntu:22.04`
- Service wrapper: `socat TCP-LISTEN:5000,reuseaddr,fork EXEC:./prob,stderr`
- Runtime user: `pwn`
- Port: `5000`

The copied runtime libc is:

- `glibc 2.35`
- `GNU C Library (Ubuntu GLIBC 2.35-0ubuntu3)`

Local reproduction:

```bash
cd problems/simple-file-manager/public
docker compose up -d --build
```

## Binary Overview

`public/prob` is a 64-bit PIE ELF with NX, stack canary, and full RELRO. It is
not stripped, which makes the first pass much easier.

Useful symbols:

- `main` at `0x1100`
- `xor_chksum` at `0x1300`
- `here` at `0x1360`
- `menu` at `0x13c0`
- `ls_dirs` at `0x1450`
- `get_long` at `0x1510`
- `cd_op` at `0x1570`
- `readn` at `0x1600`
- `write_file` at `0x1670`
- `writen` at `0x1800`
- `read_file` at `0x1880`
- `mkdir_op` at `0x1a20`
- `cwd` at `0x4010`
- `fs` at `0x4060`

Menu actions:

1. write
2. read
3. mkdir
4. cd
5. ls
6. exit

## Recovered Object Model

The program keeps a tiny in-memory filesystem with directory objects and file
objects.

Directory object:

- Allocated with `calloc(1, 0x90)`
- User size `0x90`, heap chunk size `0xa0`
- Layout:
  - `+0x00`: `char name[16]`
  - `+0x10`: `void *entries[16]`

File object:

- Main chunk allocated with `malloc(min(size, 0x1000) + 0x18)`
- A file with logical size `0x78` also lands in the `0xa0` heap chunk class,
  which is the same class used by directory objects
- Layout:
  - `+0x00`: `int mode`
  - `+0x04`: `int checksum`
  - `+0x08`: `size_t total_size`
  - `+0x10`: `void *next`
  - `+0x18`: inline file data

Extra data chunks for files larger than `0x1000`:

- Allocated with `malloc(piece + 8)`
- Layout:
  - `+0x00`: `void *next`
  - `+0x08`: chunk data

`write_file()` fills these objects and computes an XOR checksum over the user
data. `read_file()` prints metadata, writes file content back to the client, and
then frees the backing storage.

## Root Bug

The bug is in `read_file()`.

The function:

1. Looks up a file pointer from the current directory entry table.
2. Prints `mode`, `checksum`, and `size`.
3. Sends the file contents.
4. Frees the main file chunk.
5. Walks the `next` chain and frees extra chunks.
6. Returns without clearing the directory slot.

That leaves a stale pointer in the directory. Any later `read` of the same slot
operates on freed memory. This is a real use-after-free, not just a logic bug.

## Allocator Notes

I reproduced the service locally with the shipped Dockerfile and traced
`malloc`, `calloc`, and `free` using a small preload helper.

Important observation:

- `mkdir` uses `calloc(1, 0x90)`
- small file main chunks use `malloc(...)`
- on glibc 2.35, the `calloc` path did not immediately reuse the freed file
  chunk in the way a naive "free file then overwrite it with a directory" plan
  would expect
- `malloc` reuse was much more relevant than `calloc` reuse

This changed the exploitation direction. The promising path is not "replace the
freed file object with a directory", but "replace it with another `malloc`-backed
object or chunk and let `read_file()` reinterpret it as a file object".

## Confirmed Primitives

### 1. Stale Read After Free

Reading a file once frees it. Reading the same slot again dereferences a stale
pointer and trusts corrupted heap metadata as if it were a live file object.

This already gives a disclosure primitive because:

- `read_file()` trusts the freed object's `size`
- it trusts the freed object's `next`
- it reads from `ptr + 0x18` and then from `next + 8`

### 2. Heap Leak From A Tcache-Freed Small File

If a small file is freed into tcache and then read again from the stale slot,
the first qword in the freed chunk reflects tcache metadata.

On glibc 2.35 this matters because of safe-linking:

- the stored `next` pointer is protected
- if the tcache bin only contains one entry, that protected value corresponds to
  `chunk_addr >> 12`

That leaks the heap page base and confirms that the stale read is useful for
allocator-state recovery.

### 3. Fake File Object Via Extra-Chunk Reuse

This was the first strong controlled primitive.

Setup:

1. Create and free a small file so its main chunk goes into a reusable `malloc`
   size class.
2. Allocate a larger file whose first extra chunk has that same chunk size.
3. The allocator reuses the freed file chunk as that large file's extra chunk.
4. Read the stale slot again.

Result:

- `read_file()` interprets the reused extra chunk as a fresh file object
- bytes inside attacker-controlled file data become fake `size`, fake `next`,
  and fake data fields

One confirmed example:

- free a file with size `0x78`
- allocate a new file with size `0x1088`
- the freed `0xa0`-sized main chunk is reused as the new file's first extra
  chunk on glibc 2.35

With a suitable payload in the large file, the stale read reports a forged file
header and prints controlled bytes. That is a real fake-object read primitive.

### 4. Unsorted-Bin Libc Leak

A larger overlap gives a stable libc disclosure.

The most reliable local pattern was:

1. Free a file of size `0x1500`
2. Reuse one of its `0x508` extra chunks from another large file
3. Reach that reused chunk through the fake-directory path
4. Read unsorted-bin metadata out of the reclaimed region

This leaks `main_arena` pointers under the shipped glibc. The confirmed local
offset was:

- leaked unsorted pointer = `libc_base + 0x219ce0`

## Why The Bug Is Exploitable

The stale file slot gives more than a crash:

- controlled or semi-controlled heap disclosure
- fake file headers
- attacker-chosen `size`
- attacker-chosen `next` pointer traversal
- free operations on pointers recovered from forged chunk headers

That means the bug is already close to the usual heap exploitation chain:

1. use-after-free
2. heap leak
3. libc leak
4. overlap or allocator-metadata control
5. code execution or direct file disclosure

## Corrected Heap Geometry

The early "overwrite a freed file with a directory" idea was too naive. The
important corrected layout facts were:

- directory objects use `calloc(1, 0x90)` and occupy `0xa0` chunks
- the matching small file size is `0x78`, not `0x70`
- file and directory overlap attempts only became stable after switching to the
  `0xa0` class deliberately

One representative local heap layout after the setup phase was:

- heap page base leaked from tcache metadata
- root directory at `heap_page + 0x2a0`
- victim directory at `heap_page + 0x340`
- first small file main chunk at `heap_page + 0x3e0`

Another important correction was pointer interpretation. The fake directory
entries must contain absolute heap pointers, not small offsets. Several earlier
crashes came from accidentally writing values such as `0x3c0` instead of
`heap_page + 0x3c0`.

## Stronger Mid-Chain Primitive

Once the directory overlap was stable, the analysis moved beyond leaks.

Confirmed sequence:

1. Leak the heap page from a stale read on a `0x78` file
2. Free a live directory through the forged file `next` chain
3. Reallocate that freed directory chunk as a file object
4. `cd` into that heap data as if it were a directory

That gives real object confusion: the program treats file-controlled heap bytes
as a live directory entry table. This was confirmed locally by dumping the heap
and by reaching controlled pointers through `cd` and `read`.

## Arbitrary `0xa0`-Bin Allocation And Write

The strongest confirmed primitive is an arbitrary allocation target in the
`0xa0` tcache bin, which becomes an arbitrary `0x78`-byte write.

Representative helper geometry in one stable local run:

- overlapped directory at `dir1 = heap + 0x340`
- fake `0x50` chunk user pointer `P1 = heap + 0x3c0`
- reclaimed extra-chunk pointer `Eptr = heap + 0x34e0`
- reusable real `0xa0` tcache chunk `A = heap + 0x3e0`

Working fake-directory contents:

- entry `0` points to `P1`
- entry `2` points to `Eptr`
- entry `10` points to `heap + 0x3b0`
- the adjacent data contains the string `cat f*`
- a fake size field of `0x51` is present for the House-of-Spirit step

After a `write_file()` and `cd` sequence, `read_file()` on that fake entry
frees `P1` into tcache. That seeds a later poisoning step against the real
`0xa0` bin.

For a write beginning at `start_addr`, the poisoned allocation target is:

- `target = start_addr - 0x18`

and the tcache pointer written into the freed `A` chunk is:

- `target ^ (A >> 12)`

The important result is not just one poisoned allocation. The helper is
reusable if the temporary allocations are cleaned up after each write:

- free the chunk that popped `A` from the poisoned bin
- free the staging large file whose extra chunk reused `P1`

With that cleanup, two consecutive arbitrary writes to different aligned
addresses succeeded locally in the same process. The alignment constraint is
that `start_addr` must be `0x8 mod 0x10`, because the poisoned return value is
`start_addr - 0x18` and must stay properly aligned.

## Endgame Attempts

### 1. `__free_hook`

This was the first obvious sink to test once arbitrary writes landed.

What worked:

- the poisoned `0xa0` allocation returned `__free_hook - 0x18`
- the write landed
- memory inspection confirmed that `__free_hook` contained `system`

What failed:

- the subsequent free path did not call the hook in a useful way under this
  runtime

So `__free_hook` is a confirmed dead end for this challenge, even though the
write itself is real.

### 2. Split-Write FSOP On Real `stdout`

The next direction was to corrupt the real `stdout` `FILE` object in libc.

This required correcting the structure map first. The useful fields are:

- `_chain` at `stdout + 0x68`
- `_lock` at `stdout + 0x88`
- `_wide_data` at `stdout + 0xa0`
- `_unused2` starts at `stdout + 0xc4`
- vtable at `stdout + 0xd8`

Two separate write layouts were tried:

- an early split across `stdout + 0x68` and `stdout - 0x8`
- a later split centered at `stdout + 0x88` to cover `_lock`, `_wide_data`,
  and the vtable region more cleanly

These attempts did reach libc I/O internals, but they never produced a clean
call to `system()`. One representative crash happened inside `_IO_puts` while
releasing the stream lock. In that core, `stdout->_lock` had been corrupted to
an invalid pointer, so the crash happened before a useful FSOP sink.

### 3. Global `stdout` Pointer Pivot

Instead of partially rewriting the real stream object, a cleaner idea was to:

1. build a complete fake `FILE` object on the heap
2. overwrite the global `stdout` pointer variable in libc
3. let `puts` operate on the fake stream

The overwrite itself worked. Memory inspection confirmed that the global
`stdout` pointer really pointed to the forged heap object afterward.

The missing piece was behavior:

- no call to `system()` was observed
- some attempts appeared to buffer output into heap memory instead
- others failed closed or crashed before reaching a useful virtual call

So the pointer pivot is mechanically valid, but the fake `FILE` state was still
not correct enough to finish the challenge.

## Current Conclusion

The analysis ended with strong primitives but no final sink:

- stable heap leak
- stable libc leak
- stable fake-directory overlap
- stable arbitrary `0xa0`-bin allocation target
- reusable arbitrary `0x78`-byte writes at aligned addresses

What is still missing is the final glibc object or callback that converts those
writes into code execution or a direct flag read under the shipped libc 2.35.

The useful negative results are also worth keeping:

- `__free_hook` writes land but do not solve the challenge
- partial corruption of the real `stdout` object is fragile and crashed on an
  invalid `_lock`
- overwriting the global `stdout` pointer to a fake heap stream is not
  sufficient by itself

So the challenge is definitely a real heap pwn based on the file manager's
object model, and the intended solve is likely close to the arbitrary-write
stage reached here. The unresolved part is choosing the right final sink, not
finding the bug or building the leaks.
