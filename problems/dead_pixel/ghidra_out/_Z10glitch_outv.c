// _Z10glitch_outv @ 001005c3

/* WARNING: Globals starting with '_' overlap smaller symbols at the same address */
/* WARNING: Unknown calling convention -- yet parameter storage is locked */
/* glitch_out() */

void glitch_out(void)

{
  ostream *this;
  
  this = std::operator<<((ostream *)std::cout,">> GLITCH: Reality rejected your input.");
  std::ostream::operator<<
            (this,(_func_ostream_ptr_ostream_ptr *)PTR_endl<char,std_char_traits<char>>_00104fd8);
  _DAT_4445414450495845 = 0;
  return;
}


