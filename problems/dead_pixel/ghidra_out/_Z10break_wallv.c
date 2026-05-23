// _Z10break_wallv @ 00100e75

/* WARNING: Unknown calling convention -- yet parameter storage is locked */
/* break_wall() */

void break_wall(void)

{
  int iVar1;
  ostream *poVar2;
  
  render_stage = 5;
  if (render_budget < 100000) {
    poVar2 = std::operator<<((ostream *)std::cout,">> Not enough budget to breach the fourth wall.")
    ;
    std::ostream::operator<<
              (poVar2,(_func_ostream_ptr_ostream_ptr *)PTR_endl<char,std_char_traits<char>>_00104fd8
              );
    glitch_out();
  }
  else {
    render_budget = render_budget + -100000;
    iVar1 = rand();
    if ((iVar1 % 200000000 == 0) && (100000 < glitch_energy)) {
      poVar2 = std::operator<<((ostream *)std::cout,"BREACH! ");
      poVar2 = (ostream *)std::ostream::operator<<(poVar2,iVar1);
      std::ostream::operator<<
                (poVar2,(_func_ostream_ptr_ostream_ptr *)
                        PTR_endl<char,std_char_traits<char>>_00104fd8);
      escape_reality();
    }
    else {
      poVar2 = std::operator<<((ostream *)std::cout,"-_- ");
      poVar2 = (ostream *)std::ostream::operator<<(poVar2,iVar1);
      std::ostream::operator<<
                (poVar2,(_func_ostream_ptr_ostream_ptr *)
                        PTR_endl<char,std_char_traits<char>>_00104fd8);
      glitch_out();
    }
  }
  return;
}


