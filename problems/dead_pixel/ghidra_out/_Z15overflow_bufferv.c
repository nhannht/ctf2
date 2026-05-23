// _Z15overflow_bufferv @ 00100996

/* WARNING: Unknown calling convention -- yet parameter storage is locked */
/* overflow_buffer() */

void overflow_buffer(void)

{
  int iVar1;
  ostream *poVar2;
  long lVar3;
  long in_FS_OFFSET;
  char *local_258 [4];
  char *local_238;
  char *local_230;
  undefined *local_228;
  char local_218 [256];
  char local_118 [264];
  long local_10;
  
  local_10 = *(long *)(in_FS_OFFSET + 0x28);
  local_258[0] = "0xDEADBEEF";
  local_258[1] = "heap_spray?";
  local_258[2] = "use-after-free";
  local_258[3] = "double_free";
  local_238 = "rop_chain";
  local_230 = "format_string";
  local_228 = &DAT_00102a8a;
  render_stage = 3;
  if (render_budget < 500) {
    poVar2 = std::operator<<((ostream *)std::cout,">> Insufficient render budget.");
    std::ostream::operator<<
              (poVar2,(_func_ostream_ptr_ostream_ptr *)PTR_endl<char,std_char_traits<char>>_00104fd8
              );
    glitch_out();
  }
  else {
    render_budget = render_budget + -500;
    if (packet_index == 0x10) {
      std::operator<<((ostream *)std::cout,">> Packet log full.\n");
    }
    else {
      std::operator<<((ostream *)std::cout,">> Target address: ");
      read(0,local_218,0xff);
      std::operator<<((ostream *)std::cout,">> Payload: ");
      read(0,local_118,0xff);
      poVar2 = std::operator<<((ostream *)std::cout,"[");
      poVar2 = std::operator<<(poVar2,local_218);
      poVar2 = std::operator<<(poVar2,"]");
      std::ostream::operator<<
                (poVar2,(_func_ostream_ptr_ostream_ptr *)
                        PTR_endl<char,std_char_traits<char>>_00104fd8);
      poVar2 = std::operator<<((ostream *)std::cout,local_118);
      std::ostream::operator<<
                (poVar2,(_func_ostream_ptr_ostream_ptr *)
                        PTR_endl<char,std_char_traits<char>>_00104fd8);
      poVar2 = std::operator<<((ostream *)std::cout,">> Packet injected.");
      std::ostream::operator<<
                (poVar2,(_func_ostream_ptr_ostream_ptr *)
                        PTR_endl<char,std_char_traits<char>>_00104fd8);
      iVar1 = rand();
      if (iVar1 % 10 == 0) {
        poVar2 = std::operator<<((ostream *)std::cout,">> ACK: engine accepted the packet.");
        std::ostream::operator<<
                  (poVar2,(_func_ostream_ptr_ostream_ptr *)
                          PTR_endl<char,std_char_traits<char>>_00104fd8);
        iVar1 = rand();
        lVar3 = (long)packet_index;
        packet_index = packet_index + 1;
        *(char **)(packet_log + lVar3 * 8) = local_258[iVar1 % 6];
      }
      else {
        poVar2 = std::operator<<((ostream *)std::cout,">> No response from engine.");
        std::ostream::operator<<
                  (poVar2,(_func_ostream_ptr_ostream_ptr *)
                          PTR_endl<char,std_char_traits<char>>_00104fd8);
      }
    }
  }
  if (local_10 != *(long *)(in_FS_OFFSET + 0x28)) {
                    /* WARNING: Subroutine does not return */
    __stack_chk_fail();
  }
  return;
}


