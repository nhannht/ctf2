// _Z19init_pixel_handlersv @ 001013ae

/* WARNING: Unknown calling convention -- yet parameter storage is locked */
/* init_pixel_handlers() */

void init_pixel_handlers(void)

{
  int local_c;
  
  for (local_c = 0; local_c < 0x100; local_c = local_c + 1) {
    *(code **)(pixel_handlers + (long)local_c * 8) = default_handler;
  }
  pixel_handlers._8_8_ = corrupt_fail;
  pixel_handlers._40_8_ = wall_fail;
  return;
}


