// main @ 0010143f

undefined8 main(void)

{
  ostream *this;
  long in_FS_OFFSET;
  ushort local_ae;
  int local_ac;
  sigaction local_a8;
  long local_10;
  
  local_10 = *(long *)(in_FS_OFFSET + 0x28);
  setvbuf(stdin,(char *)0x0,2,0);
  setvbuf(stdout,(char *)0x0,2,0);
  print_banner();
  alarm(300);
  init_pixel_handlers();
  local_ae = 0;
  local_ac = open("/dev/urandom",0);
  read(local_ac,&local_ae,2);
  close(local_ac);
  srand((uint)local_ae);
  memset(&local_a8,0,0x98);
  local_a8.sa_flags = 4;
  local_a8.__sigaction_handler.sa_handler = handle_pixel_death;
  sigaction(0xb,&local_a8,(sigaction *)0x0);
  memset(&local_a8,0,0x98);
  local_a8.sa_flags = 4;
  local_a8.__sigaction_handler.sa_handler = handle_timeout;
  sigaction(0xe,&local_a8,(sigaction *)0x0);
  this = std::operator<<((ostream *)std::cout,
                         "WARNING: Unauthorized process detected in render pipeline.");
  std::ostream::operator<<
            (this,(_func_ostream_ptr_ostream_ptr *)PTR_endl<char,std_char_traits<char>>_00104fd8);
  run_game();
  if (local_10 != *(long *)(in_FS_OFFSET + 0x28)) {
                    /* WARNING: Subroutine does not return */
    __stack_chk_fail();
  }
  return 0;
}


