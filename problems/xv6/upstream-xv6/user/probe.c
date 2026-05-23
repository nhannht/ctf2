#include "kernel/types.h"
#include "kernel/stat.h"
#include "kernel/spinlock.h"
#include "kernel/sleeplock.h"
#include "kernel/fs.h"
#include "kernel/file.h"
#include "kernel/fcntl.h"
#include "kernel/riscv.h"
#include "user/user.h"

static void
say(char *s)
{
  write(1, s, strlen(s));
}

int
main(void)
{
  if(open("console", O_RDWR) < 0){
    mknod("console", CONSOLE, 0);
    open("console", O_RDWR);
  }
  dup(0);
  dup(0);

  say("probe start\n");
  char *p = sbrk(PGSIZE);
  if(p == SBRK_ERROR){
    say("sbrk failed\n");
    exit(1);
  }
  p[0] = 'A';
  say("mapped\n");
  sbrk(-PGSIZE);
  say("freed, touching stale va\n");
  p[0] = 'B';
  say("stale write survived\n");
  exit(0);
}
