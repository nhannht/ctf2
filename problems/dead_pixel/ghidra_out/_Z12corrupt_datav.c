// _Z12corrupt_datav @ 00100606

/* WARNING: Unknown calling convention -- yet parameter storage is locked */
/* corrupt_data() */

void corrupt_data(void)

{
  ostream *poVar1;
  long in_FS_OFFSET;
  int local_24;
  int local_20;
  uint local_1c;
  uint local_18;
  int local_14;
  long local_10;
  
  local_10 = *(long *)(in_FS_OFFSET + 0x28);
  render_stage = 1;
  local_20 = 0;
  while ((local_20 < 0x10 && (*(long *)(packet_log + (long)local_20 * 8) != 0))) {
    poVar1 = (ostream *)std::ostream::operator<<((ostream *)std::cout,local_20);
    poVar1 = std::operator<<(poVar1,". ");
    poVar1 = std::operator<<(poVar1,*(char **)(packet_log + (long)local_20 * 8));
    std::ostream::operator<<
              (poVar1,(_func_ostream_ptr_ostream_ptr *)PTR_endl<char,std_char_traits<char>>_00104fd8
              );
    local_20 = local_20 + 1;
  }
  std::operator<<((ostream *)std::cout,"Select packet: ");
  std::istream::operator>>((istream *)std::cin,&local_24);
  if ((local_20 < local_24) || (*(long *)(packet_log + (long)local_24 * 8) == 0)) {
    glitch_out();
  }
  else {
    local_1c = rand();
    local_18 = rand();
    local_14 = rand();
    render_budget = render_budget - local_14 % 5000;
    if ((local_1c & 1) == 0) {
      memory_cells = memory_cells + (int)local_1c % 10;
      glitch_energy = glitch_energy + (int)local_18 % 10;
      *(ulong *)(corruption_table + (long)local_24 * 8) =
           (ulong)(local_18 & 0xff) + *(long *)(corruption_table + (long)local_24 * 8);
    }
    else {
      memory_cells = memory_cells + (((int)local_1c / 10) * 10 - local_1c);
      glitch_energy = glitch_energy + (((int)local_18 / 10) * 10 - local_18);
      *(ulong *)(corruption_table + (long)local_24 * 8) =
           *(long *)(corruption_table + (long)local_24 * 8) - (ulong)(local_18 & 0xff);
    }
  }
  if (local_10 != *(long *)(in_FS_OFFSET + 0x28)) {
                    /* WARNING: Subroutine does not return */
    __stack_chk_fail();
  }
  return;
}


