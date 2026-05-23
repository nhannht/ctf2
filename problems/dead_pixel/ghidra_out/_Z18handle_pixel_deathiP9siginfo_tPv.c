// _Z18handle_pixel_deathiP9siginfo_tPv @ 001012b9

/* handle_pixel_death(int, siginfo_t*, void*) */

void handle_pixel_death(int param_1,siginfo_t *param_2,void *param_3)

{
  if (1 < signal_count) {
                    /* WARNING: Subroutine does not return */
    exit(0xff);
  }
  signal_count = signal_count + 1;
  *(undefined8 *)((long)param_3 + 0xa8) = *(undefined8 *)(pixel_handlers + render_stage * 8);
  return;
}


