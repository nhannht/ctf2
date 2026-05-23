// _Z11escape_loopv @ 00100ccf

/* WARNING: Unknown calling convention -- yet parameter storage is locked */
/* escape_loop() */

void escape_loop(void)

{
  long lVar1;
  uint uVar2;
  int iVar3;
  ostream *poVar4;
  long in_FS_OFFSET;
  
  lVar1 = *(long *)(in_FS_OFFSET + 0x28);
  render_stage = 4;
  if (render_budget < 1000000) {
    poVar4 = std::operator<<((ostream *)std::cout,">> Not enough render cycles.");
    std::ostream::operator<<
              (poVar4,(_func_ostream_ptr_ostream_ptr *)PTR_endl<char,std_char_traits<char>>_00104fd8
              );
    glitch_out();
  }
  else {
    render_budget = render_budget + -1000000;
    uVar2 = rand();
    if ((uVar2 & 1) == 0) {
      iVar3 = rand();
      glitch_energy = glitch_energy + iVar3 % 200;
      poVar4 = std::operator<<((ostream *)std::cout,">> Loop boundary weakened!");
      std::ostream::operator<<
                (poVar4,(_func_ostream_ptr_ostream_ptr *)
                        PTR_endl<char,std_char_traits<char>>_00104fd8);
    }
    else {
      iVar3 = rand();
      glitch_energy = glitch_energy - iVar3 % 100;
      poVar4 = std::operator<<((ostream *)std::cout,">> Loop reinforced. Still inside.");
      std::ostream::operator<<
                (poVar4,(_func_ostream_ptr_ostream_ptr *)
                        PTR_endl<char,std_char_traits<char>>_00104fd8);
    }
    if (500 < glitch_energy) {
      memory_cells = memory_cells + glitch_energy + -500;
    }
  }
  if (lVar1 != *(long *)(in_FS_OFFSET + 0x28)) {
                    /* WARNING: Subroutine does not return */
    __stack_chk_fail();
  }
  return;
}


